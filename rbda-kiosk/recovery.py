"""
recovery.py
===========
js_api RIÊNG cho recovery.html — màn hình chỉ hiện khi PipelineAPI
KHÔNG khởi tạo được (app.db hỏng/mất, xem main.py). Không liên quan gì
tới PipelineAPI/nghiệp vụ pipeline: chỉ có 2 việc —
  1. Cho xem tình trạng lỗi + danh sách bản sao lưu (do PipelineAPI._backup_db
     tạo trước mỗi lần chạy pipeline, xem api.py).
  2. Thử khôi phục: ưu tiên bản sao lưu MỚI NHẤT còn đọc được nguyên vẹn
     (PRAGMA quick_check) — nếu bản đó cũng hỏng thì tự động lùi sang bản
     kế trước, không dừng lại ở bản đầu tiên gặp lỗi (xem
     ke-hoach-mat-du-lieu.html, nhóm C, dòng C2). Nếu không còn bản nào,
     hoặc người dùng chọn bỏ qua, có phương án cuối "bắt đầu mới" — đổi
     tên (KHÔNG xoá) tệp hỏng rồi tạo app.db trống.

main.py chỉ dùng lớp này khi PipelineAPI(db_path) ném exception, vào
đúng lúc đó CHƯA có webview window/API nào khác đang giữ app.db mở —
vì vậy copy/di chuyển file trực tiếp ở đây là an toàn (không rơi vào
tình huống "copy file trong khi tiến trình khác đang ghi" đã ghi nhận
là nguy hiểm với chế độ WAL trong ke hoạch).
"""

import datetime
import os
import shutil
import sqlite3

from i18n_errors import err


def _ok(data=None):
    return {"ok": True, "data": data, "errors": []}


def _fail(errors):
    if isinstance(errors, str):
        errors = [errors]
    elif isinstance(errors, dict) and "code" in errors and "params" in errors:
        errors = [errors]
    return {"ok": False, "data": None, "errors": errors}


def _quick_check_ok(path: str) -> bool:
    """True nếu path là file SQLite hợp lệ và PRAGMA quick_check trả 'ok'."""
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        return False
    try:
        conn = sqlite3.connect(path)
        try:
            row = conn.execute("PRAGMA quick_check").fetchone()
            return bool(row) and row[0] == "ok"
        finally:
            conn.close()
    except sqlite3.Error:
        return False


class RecoveryAPI:
    def __init__(self, db_path: str, init_error: str):
        self.db_path = db_path
        self.init_error = init_error

    def _backup_dir(self) -> str:
        return os.path.dirname(self.db_path) or "."

    def _backup_prefix(self) -> str:
        return f"{os.path.basename(self.db_path)}.bak-"

    def _list_backups(self):
        backup_dir = self._backup_dir()
        prefix = self._backup_prefix()
        if not os.path.isdir(backup_dir):
            return []
        names = sorted(
            (f for f in os.listdir(backup_dir) if f.startswith(prefix)),
            reverse=True,  # ten co timestamp dang so, sort nguoc = moi nhat truoc
        )
        out = []
        for name in names:
            full = os.path.join(backup_dir, name)
            try:
                stat = os.stat(full)
            except OSError:
                continue
            out.append({
                "name": name,
                "size_bytes": stat.st_size,
                "modified_at": datetime.datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat(timespec="seconds"),
            })
        return out

    def get_status(self):
        return _ok({
            "db_path": self.db_path,
            "init_error": self.init_error,
            "backups": self._list_backups(),
        })

    def _move_corrupt_db_aside(self):
        """Đổi tên (KHÔNG xoá) tệp app.db hiện tại nếu nó tồn tại, trả về
        đường dẫn mới hoặc None nếu không có gì để di chuyển/di chuyển
        thất bại."""
        if not os.path.exists(self.db_path):
            return None
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        aside = f"{self.db_path}.corrupt-{ts}"
        try:
            shutil.move(self.db_path, aside)
            return aside
        except OSError:
            return None

    def restore_from_backup(self):
        """Thử bản sao lưu MỚI NHẤT trước; nếu hỏng, tự động lùi sang bản
        kế trước cho tới khi tìm được bản đọc được hoặc hết bản để thử."""
        backups = self._list_backups()
        if not backups:
            return _fail(err("recovery_no_backups"))

        backup_dir = self._backup_dir()
        tried = []
        for b in backups:
            full = os.path.join(backup_dir, b["name"])
            tried.append(b["name"])
            if not _quick_check_ok(full):
                continue

            corrupt_aside = self._move_corrupt_db_aside()
            try:
                shutil.copy2(full, self.db_path)
            except OSError as e:
                # Khoi phuc that bai o buoc copy — tra tep hong ve cho neu
                # da di doi, tranh mat luon ca ban hong (co the con cuu
                # duoc thu cong sau nay).
                if corrupt_aside and os.path.exists(corrupt_aside):
                    try:
                        shutil.move(corrupt_aside, self.db_path)
                    except OSError:
                        pass
                return _fail(err("recovery_restore_failed", detail=str(e)))

            return _ok({
                "restored_from": b["name"],
                "skipped": tried[:-1],
                "detail": err(
                    "recovery_restored_from",
                    backup_name=b["name"],
                    n_skipped=len(tried) - 1,
                ),
            })

        return _fail(err("recovery_all_backups_corrupt", n_tried=len(tried)))

    def start_fresh(self):
        """Phương án cuối, MANG TÍNH PHÁ HUỶ ở mức nhẹ: đổi tên file hỏng
        sang <db>.corrupt-<timestamp> (không xoá) rồi tạo app.db mới
        hoàn toàn trống."""
        from rbda_priority_pipeline import init_db

        self._move_corrupt_db_aside()
        try:
            init_db(self.db_path)
        except Exception as e:
            return _fail(err("recovery_restore_failed", detail=str(e)))
        return _ok({
            "db_path": self.db_path,
            "detail": err("recovery_fresh_created"),
        })
