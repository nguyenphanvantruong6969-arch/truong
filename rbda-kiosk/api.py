"""
api.py
======
Lớp API expose cho pywebview — mọi hàm public ở đây có thể được gọi
từ JS qua window.pywebview.api.<ten_ham>(...) và luôn trả về dict
(pywebview tự serialize JSON hai chiều).

Quy ước trả về thống nhất cho mọi hàm:
    { "ok": bool, "data": ..., "errors": [...] }
Để JS chỉ cần check `.ok` là biết thành công hay không, không phải
try/catch riêng lẻ từng hàm.

Mỗi phần tử trong "errors" (và trong các danh sách "warnings" trả về
kèm data khi ok=True) là MỘT trong hai dạng:
  - chuỗi thô (vd traceback) — hiển thị nguyên văn, không dịch.
  - {"code": "...", "params": {...}} — do err() ở i18n_errors.py tạo ra,
    frontend tự dịch sang ngôn ngữ đang chọn (xem ERROR_MESSAGES trong
    app.js, phải khớp với MESSAGES trong i18n_errors.py).
Điều này cho phép app hỗ trợ song ngữ (vi/en) mà không cần Python biết
người dùng đang chọn ngôn ngữ nào.
"""

import csv
import datetime
import io
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rbda_priority_pipeline import (
    init_db,
    load_from_sqlite,
    validate_data_integrity,
    generate_stb_lottery,
    run_rbda,
    sanity_check_result,
    verify_stability,
    export_match_results,
    default_reserve_eligible_fn,
    connect_db,
)
from i18n_errors import err

import sqlite3


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _ok(data=None):
    return {"ok": True, "data": data, "errors": []}


def _fail(errors):
    if isinstance(errors, str):
        errors = [errors]
    elif isinstance(errors, dict) and "code" in errors and "params" in errors:
        errors = [errors]
    return {"ok": False, "data": None, "errors": errors}


class PipelineAPI:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.window = None  # gán qua set_window() sau khi main.py tạo cửa sổ pywebview
        init_db(self.db_path)

    def set_window(self, window) -> None:
        """
        Gọi từ main.py sau webview.create_window(...):
            api = PipelineAPI(db_path)
            window = webview.create_window("...", "index.html", js_api=api)
            api.set_window(window)
        Không bắt buộc — nếu không gọi, mọi tính năng vẫn hoạt động,
        chỉ riêng import CSV sẽ nhận nội dung file qua FileReader ở JS
        (đã dùng theo mặc định) thay vì hộp thoại chọn file gốc của hệ điều hành.
        """
        self.window = window

    # -----------------------------------------------------------------
    # TAB "VẬN HÀNH PIPELINE"
    # -----------------------------------------------------------------

    def get_last_run_info(self):
        """Thông tin lần chạy pipeline gần nhất — để hiện ở sidebar/dashboard."""
        try:
            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            row = cur.execute("SELECT * FROM run_meta WHERE id = 1").fetchone()
            conn.close()
            return _ok(dict(row) if row else None)
        except Exception as e:
            return _fail(err("error_reading_last_run", detail=str(e)))

    def get_dashboard_status(self):
        """Số liệu tổng quan để hiển thị ngay khi mở tab Pipeline."""
        try:
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            n_students = cur.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            n_clubs = cur.execute("SELECT COUNT(*) FROM clubs").fetchone()[0]
            n_prefs = cur.execute(
                "SELECT COUNT(DISTINCT student_id) FROM preferences"
            ).fetchone()[0]
            n_matched = cur.execute(
                "SELECT COUNT(*) FROM match_results WHERE club_id IS NOT NULL"
            ).fetchone()[0]
            has_results = cur.execute(
                "SELECT COUNT(*) FROM match_results"
            ).fetchone()[0] > 0
            conn.close()
            return _ok({
                "n_students": n_students,
                "n_clubs": n_clubs,
                "n_students_with_preferences": n_prefs,
                "n_matched": n_matched,
                "has_results": has_results,
            })
        except Exception as e:
            return _fail(err("error_reading_dashboard", detail=str(e)))

    def check_data_integrity(self):
        """Nút 'Kiểm tra dữ liệu' — chỉ validate, KHÔNG chạy pipeline."""
        try:
            students, clubs, tested_scores, applicants, preferences, _ = (
                load_from_sqlite(self.db_path)
            )
            errors = validate_data_integrity(students, clubs, preferences, applicants)
            if errors:
                return _fail(errors)
            return _ok({
                "message": "Du lieu hop le.",
                "n_students": len(students),
                "n_clubs": len(clubs),
            })
        except Exception as e:
            return _fail([err("error_checking_integrity", detail=str(e)), traceback.format_exc()])

    # -----------------------------------------------------------------
    # KIỂM TRA SỨC KHOẺ DỮ LIỆU (pre-flight)
    #
    # validate_data_integrity() chỉ bắt dữ liệu KHÔNG HỢP LỆ (club không
    # tồn tại, capacity <= 0, nguyện vọng trùng…). Nhưng có cả một nhóm
    # tình huống mà dữ liệu VẪN HỢP LỆ, pipeline VẪN CHẠY, kết quả VẪN
    # trông bình thường — trong khi ai được vào club đã bị thay đổi bởi
    # một thiếu sót mà người vận hành không hề thấy. Ví dụ nguy hiểm nhất:
    # giáo viên mới chấm được một nửa danh sách, nửa còn lại lập tức bị
    # xếp dưới TOÀN BỘ các em đã có điểm — kể cả em thấp điểm nhất.
    #
    # Hàm này liệt kê đúng nhóm đó dưới dạng CẢNH BÁO (không phải lỗi):
    # không chặn chạy pipeline, nhưng bắt buộc phải hiện ra trước mắt
    # người vận hành để họ tự quyết định.
    # -----------------------------------------------------------------

    _HEALTH_SAMPLE_LIMIT = 5

    def get_data_health_report(self):
        """
        Rà soát các thiếu sót dữ liệu ÂM THẦM LÀM ĐỔI KẾT QUẢ.
        Trả về {"warnings": [...], "n_warnings": int, "n_high": int} —
        mỗi cảnh báo là {code, params, severity} với severity là
        "high" (gần như chắc chắn làm sai kết quả) hoặc "medium"/"info".
        """
        try:
            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            warnings = []

            def warn(severity, code, **params):
                entry = err(code, **params)
                entry["severity"] = severity
                warnings.append(entry)

            # --- 1. Chấm điểm thiếu / chưa chấm ---------------------------
            for row in cur.execute("""
                SELECT c.club_id,
                       COUNT(DISTINCT t.student_id) AS n_applicants,
                       COUNT(DISTINCT sc.student_id) AS n_scored
                FROM clubs c
                JOIN club_test_selection t ON t.club_id = c.club_id
                LEFT JOIN club_scores sc
                       ON sc.club_id = c.club_id AND sc.student_id = t.student_id
                GROUP BY c.club_id
                ORDER BY c.club_id
            """).fetchall():
                n_app, n_scored = row["n_applicants"], row["n_scored"]
                if n_app == 0:
                    continue
                if n_scored == 0:
                    warn("high", "health_scoring_none",
                         club_id=row["club_id"], n_applicants=n_app)
                elif n_scored < n_app:
                    warn("high", "health_scoring_partial",
                         club_id=row["club_id"], n_applicants=n_app,
                         n_scored=n_scored, n_missing=n_app - n_scored)

            # --- 2. Đăng ký thi nhưng không xếp nguyện vọng club đó -------
            wasted = cur.execute("""
                SELECT t.student_id, t.club_id
                FROM club_test_selection t
                LEFT JOIN preferences p
                       ON p.student_id = t.student_id AND p.club_id = t.club_id
                WHERE p.student_id IS NULL
                ORDER BY t.student_id, t.club_id
            """).fetchall()
            if wasted:
                sample = ", ".join(
                    f"{r['student_id']}→{r['club_id']}"
                    for r in wasted[:self._HEALTH_SAMPLE_LIMIT]
                )
                warn("high", "health_tested_not_ranked",
                     n=len(wasted), sample=sample)

            # --- 3. Học sinh chưa xếp nguyện vọng nào ---------------------
            no_pref = cur.execute("""
                SELECT s.student_id FROM students s
                LEFT JOIN preferences p ON p.student_id = s.student_id
                WHERE p.student_id IS NULL
                ORDER BY s.student_id
            """).fetchall()
            if no_pref:
                warn("medium", "health_student_no_preferences",
                     n=len(no_pref),
                     sample=", ".join(r["student_id"] for r in no_pref[:self._HEALTH_SAMPLE_LIMIT]))

            # --- 4. Nhãn dự trữ của học sinh mà không club nào dùng -------
            for row in cur.execute("""
                SELECT s.reserve_group AS g, COUNT(*) AS n
                FROM students s
                WHERE s.reserve_group IS NOT NULL AND TRIM(s.reserve_group) <> ''
                  AND s.reserve_group NOT IN (
                      SELECT reserve_group FROM clubs
                      WHERE reserve_group IS NOT NULL AND TRIM(reserve_group) <> ''
                  )
                GROUP BY s.reserve_group ORDER BY s.reserve_group
            """).fetchall():
                warn("high", "health_orphan_student_group",
                     reserve_group=row["g"], n=row["n"])

            # --- 5. Club có suất dự trữ nhưng chưa đặt nhãn ---------------
            for row in cur.execute("""
                SELECT club_id, reserve_capacity FROM clubs
                WHERE reserve_capacity > 0
                  AND (reserve_group IS NULL OR TRIM(reserve_group) = '')
                ORDER BY club_id
            """).fetchall():
                warn("high", "health_club_reserve_no_group",
                     club_id=row["club_id"], reserve_capacity=row["reserve_capacity"])

            # --- 6. Club dành suất cho nhãn chưa học sinh nào mang --------
            for row in cur.execute("""
                SELECT club_id, reserve_group, reserve_capacity FROM clubs
                WHERE reserve_capacity > 0
                  AND reserve_group IS NOT NULL AND TRIM(reserve_group) <> ''
                  AND reserve_group NOT IN (
                      SELECT reserve_group FROM students
                      WHERE reserve_group IS NOT NULL AND TRIM(reserve_group) <> ''
                  )
                ORDER BY club_id
            """).fetchall():
                warn("medium", "health_club_group_no_students",
                     club_id=row["club_id"], reserve_group=row["reserve_group"],
                     reserve_capacity=row["reserve_capacity"])

            # --- 7. Tổng chỗ ít hơn số học sinh đã nộp nguyện vọng --------
            n_seats = cur.execute(
                "SELECT COALESCE(SUM(capacity), 0) FROM clubs"
            ).fetchone()[0]
            n_with_prefs = cur.execute(
                "SELECT COUNT(DISTINCT student_id) FROM preferences"
            ).fetchone()[0]
            if n_with_prefs > n_seats:
                warn("info", "health_oversubscribed",
                     n_seats=n_seats, n_students=n_with_prefs,
                     n_short=n_with_prefs - n_seats)

            conn.close()
            return _ok({
                "warnings": warnings,
                "n_warnings": len(warnings),
                "n_high": sum(1 for w in warnings if w["severity"] == "high"),
            })
        except Exception as e:
            return _fail(err("error_checking_integrity", detail=str(e)))

    def get_pipeline_run_warning(self):
        """
        Gọi TRƯỚC khi hiện hộp xác nhận 'Chạy pipeline' (bước 1 trong xác
        nhận 2 bước). Cho UI biết: (a) đã có kết quả cũ sẽ bị ghi đè chưa,
        (b) STB đã bị khoá chưa (nếu khoá, chạy bình thường sẽ TÁI SỬ DỤNG
        STB cũ chứ không vẽ lại — chỉ vẽ lại nếu force_redraw_stb=True).
        """
        try:
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            has_results = cur.execute(
                "SELECT COUNT(*) FROM match_results"
            ).fetchone()[0] > 0
            lock_row = cur.execute(
                "SELECT is_locked, locked_at FROM stb_lock WHERE id = 1"
            ).fetchone()
            last_run = cur.execute(
                "SELECT run_at, seed FROM run_meta WHERE id = 1"
            ).fetchone()
            conn.close()
            return _ok({
                "has_existing_results": has_results,
                "stb_locked": bool(lock_row[0]) if lock_row else False,
                "stb_locked_at": lock_row[1] if lock_row else None,
                "last_run_at": last_run[0] if last_run else None,
                "last_run_seed": last_run[1] if last_run else None,
            })
        except Exception as e:
            return _fail(err("error_checking_run_warning", detail=str(e)))

    def get_stb_lock_status(self):
        try:
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            row = cur.execute(
                "SELECT is_locked, locked_at, unlocked_at FROM stb_lock WHERE id = 1"
            ).fetchone()
            conn.close()
            if not row:
                return _ok({"is_locked": False, "locked_at": None, "unlocked_at": None})
            return _ok({
                "is_locked": bool(row[0]),
                "locked_at": row[1],
                "unlocked_at": row[2],
            })
        except Exception as e:
            return _fail(err("error_reading_stb_lock", detail=str(e)))

    def get_run_history(self, limit: int = 20):
        """Nhật ký toàn bộ các lần chạy pipeline, mới nhất trước — phục vụ kiểm toán."""
        try:
            limit = max(1, min(int(limit), 200))
            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT run_id, seed, run_at, rounds_run, n_matched, n_total, stb_redrawn "
                "FROM run_history ORDER BY run_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            conn.close()
            return _ok([dict(r) for r in rows])
        except Exception as e:
            return _fail(err("error_reading_run_history", detail=str(e)))

    _MAX_BACKUPS = 10

    def _backup_db(self) -> str:
        """
        Sao lưu app.db bằng SQLite Backup API (connection.backup(), KHÔNG
        phải copy file thô) ngay TRƯỚC khi pipeline bắt đầu ghi gì —
        an toàn kể cả khi có tiến trình khác đang mở file cùng lúc, khác
        với copy file trực tiếp vốn có thể chụp phải trạng thái nửa-ghi
        (xem ke-hoach-mat-du-lieu.html). Giữ lại tối đa _MAX_BACKUPS bản
        gần nhất, tự xoá bản cũ hơn. Trả về đường dẫn bản sao lưu.
        """
        backup_dir = os.path.dirname(self.db_path) or "."
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"{os.path.basename(self.db_path)}.bak-{ts}"
        backup_path = os.path.join(backup_dir, backup_name)

        src = connect_db(self.db_path)
        try:
            dst = sqlite3.connect(backup_path)
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()

        prefix = f"{os.path.basename(self.db_path)}.bak-"
        existing = sorted(f for f in os.listdir(backup_dir) if f.startswith(prefix))
        for stale in existing[: -self._MAX_BACKUPS] if len(existing) > self._MAX_BACKUPS else []:
            try:
                os.remove(os.path.join(backup_dir, stale))
            except OSError:
                pass
        return backup_path

    def run_pipeline(self, seed: int = 42, force_redraw_stb: bool = False):
        """
        Nút 'Chạy pipeline' — chạy trọn 5 bước, trả về log từng bước
        để UI hiển thị lên stepper theo thời gian thực (từng bước một,
        không phải chỉ kết quả cuối).

        Quy tắc khoá STB (giải quyết #3 ghi đè âm thầm + #4 khoá STB):
          - Nếu STB CHƯA khoá (lần chạy đầu tiên, hoặc sau khi người
            dùng chủ động mở khoá): vẽ STB cho MỌI học sinh, rồi tự
            động khoá lại ngay sau khi vẽ xong.
          - Nếu STB ĐÃ khoá và force_redraw_stb=False (mặc định): KHÔNG
            vẽ lại — chỉ vẽ bổ sung cho học sinh MỚI (stb_number NULL,
            vd học sinh vừa được thêm qua kiosk sau khi đã khoá), số đã
            có giữ nguyên. Đây là hành vi mặc định khi bấm 'Chạy lại'.
          - Nếu STB đã khoá và force_redraw_stb=True (người dùng xác
            nhận 2 bước trên UI để "vẽ lại"): vẽ lại TOÀN BỘ, ghi log
            unlocked_at của lần khoá cũ rồi khoá lại với thời điểm mới.
          - Mọi lần chạy (kể cả tái sử dụng STB) đều được append vào
            run_history — không bao giờ mất dấu vết lần chạy nào.

        Tính nguyên tử (giải quyết #1 trong ke-hoach-mat-du-lieu.html):
          - Vẽ/khoá STB, ghi match_results, ghi run_meta/run_history đều
            diễn ra trong MỘT connection/transaction duy nhất. Nếu bất kỳ
            bước nào ở giữa ném lỗi (kể cả crash tiến trình được bắt
            bằng try/except ở đây), TOÀN BỘ transaction rollback — kể cả
            số STB vừa vẽ ("full rollback", phương án đã chốt: mọi lần
            gọi lại run_pipeline() sau một crash bắt đầu từ trạng thái
            sạch, không có "khoá STB mồ côi" không đi kèm kết quả nào).
          - Xuất CSV chỉ thực hiện SAU KHI transaction đã commit thành
            công — CSV là sản phẩm phụ, lỗi ghi file không được phép
            khiến DB rơi vào trạng thái dở dang.
        """
        steps_log = []
        conn = None
        try:
            try:
                backup_path = self._backup_db()
                steps_log.append({
                    "step": "backup", "status": "done",
                    "detail": err("db_backed_up", backup_name=os.path.basename(backup_path)),
                })
            except Exception as e:
                # Sao luu la luoi an toan, KHONG phai dieu kien tien quyet —
                # loi sao luu khong duoc chan pipeline chay.
                steps_log.append({
                    "step": "backup", "status": "error",
                    "detail": err("db_backup_failed", detail=str(e)),
                })

            steps_log.append({"step": "validate", "status": "running"})
            students, clubs, tested_scores, applicants, preferences, _ = (
                load_from_sqlite(self.db_path)
            )
            errors = validate_data_integrity(students, clubs, preferences, applicants)
            if errors:
                steps_log.append({"step": "validate", "status": "error", "detail": errors})
                return _fail({"steps": steps_log, "errors": errors})
            steps_log.append({"step": "validate", "status": "done"})

            steps_log.append({"step": "stb_lottery", "status": "running"})
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            lock_row = cur.execute(
                "SELECT is_locked FROM stb_lock WHERE id = 1"
            ).fetchone()
            already_locked = bool(lock_row[0]) if lock_row else False
            stb_redrawn = False

            if not already_locked or force_redraw_stb:
                # Ve lai TOAN BO
                stb_lottery_new = generate_stb_lottery(list(students.keys()), seed=seed)
                conn.executemany(
                    "UPDATE students SET stb_number = ? WHERE student_id = ?",
                    [(v, k) for k, v in stb_lottery_new.items()],
                )
                if already_locked and force_redraw_stb:
                    cur.execute(
                        "UPDATE stb_lock SET unlocked_at = ? WHERE id = 1", (_now(),)
                    )
                cur.execute(
                    "UPDATE stb_lock SET is_locked = 1, locked_at = ? WHERE id = 1",
                    (_now(),),
                )
                stb_redrawn = True
                stb_step_detail = err("stb_redrawn_and_locked", n=len(stb_lottery_new))
                for sid, v in stb_lottery_new.items():
                    students[sid]["stb"] = v
            else:
                # Da khoa: chi ve bo sung cho hoc sinh moi (stb_number con NULL)
                missing = [
                    sid for sid, info in students.items() if info.get("stb") is None
                ]
                if missing:
                    supplement = generate_stb_lottery(missing, seed=seed)
                    # danh so tiep noi sau STB lon nhat hien co, tranh trung
                    existing_max_row = cur.execute(
                        "SELECT MAX(stb_number) FROM students"
                    ).fetchone()
                    offset = (existing_max_row[0] + 1) if existing_max_row[0] is not None else 0
                    conn.executemany(
                        "UPDATE students SET stb_number = ? WHERE student_id = ?",
                        [(v + offset, k) for k, v in supplement.items()],
                    )
                    stb_step_detail = err("stb_supplemented", n=len(missing))
                    for sid, v in supplement.items():
                        students[sid]["stb"] = v + offset
                else:
                    stb_step_detail = err("stb_reused")
            steps_log.append({"step": "stb_lottery", "status": "done", "detail": stb_step_detail})

            # Khong mo connection moi de doc lai stb_number: cac thay doi
            # o tren CHUA commit, mot connection khac se khong thay duoc
            # (va se pha vo tinh nguyen tu). Cap nhat truc tiep vao dict
            # students trong bo nho (da lam o hai nhanh phia tren) roi
            # dung lai cho RB-DA — tuong duong voi doc lai tu DB nhung
            # van nam trong CUNG MOT transaction.
            stb_lottery = {sid: info["stb"] for sid, info in students.items()}

            steps_log.append({"step": "rbda_cascade", "status": "running"})
            reserve_fn = default_reserve_eligible_fn(students, clubs)
            result = run_rbda(
                students, clubs, tested_scores, applicants, preferences,
                stb_lottery, is_reserve_eligible_fn=reserve_fn,
            )
            sanity_problems = sanity_check_result(result, clubs, preferences)
            stability_problems = verify_stability(result, clubs, preferences, reserve_fn)
            if sanity_problems or stability_problems:
                steps_log.append({
                    "step": "rbda_cascade", "status": "error",
                    "detail": sanity_problems + stability_problems,
                })
                conn.rollback()
                conn.close()
                conn = None
                steps_log.append({"step": "rollback", "status": "done", "detail": err("pipeline_rolled_back")})
                return _fail({"steps": steps_log, "errors": sanity_problems + stability_problems})
            steps_log.append({
                "step": "rbda_cascade", "status": "done",
                "detail": err("rbda_done", rounds=result.rounds_run),
            })

            steps_log.append({"step": "write_results", "status": "running"})
            cur.execute("DELETE FROM match_results")
            cur.executemany(
                "INSERT INTO match_results (student_id, club_id, round_num, matched_tier, rank_in_student_pref) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        sid, cid, result.rounds_run,
                        result.matched_tier.get(sid),
                        result.rank_in_student_pref.get(sid),
                    )
                    for sid, cid in result.assignment.items()
                ],
            )
            steps_log.append({"step": "write_results", "status": "done"})

            n_matched = sum(1 for v in result.assignment.values() if v)
            run_at = _now()

            cur.execute(
                "INSERT INTO run_meta (id, seed, run_at, rounds_run, n_matched, n_total) "
                "VALUES (1, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET seed=excluded.seed, run_at=excluded.run_at, "
                "rounds_run=excluded.rounds_run, n_matched=excluded.n_matched, n_total=excluded.n_total",
                (seed, run_at, result.rounds_run, n_matched, len(result.assignment)),
            )
            # run_history: KHONG BAO GIO ghi de — moi lan chay them 1 dong moi,
            # de nguoi dung luon xem lai duoc lich su chay pipeline (giai quyet #3).
            cur.execute(
                "INSERT INTO run_history (seed, run_at, rounds_run, n_matched, n_total, stb_redrawn) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (seed, run_at, result.rounds_run, n_matched, len(result.assignment),
                 1 if stb_redrawn else 0),
            )

            # Diem commit DUY NHAT cua toan bo pipeline: neu bat ky dong
            # nao o tren (ve STB, ghi ket qua, ghi run_meta/run_history)
            # nem exception, khoi except ben duoi se rollback() thay vi
            # chay den day — STB vua ve cung bi huy theo (full rollback).
            conn.commit()
            conn.close()
            conn = None

            # Xuat CSV CHI xay ra SAU KHI DB da commit thanh cong.
            steps_log.append({"step": "export", "status": "running"})
            export_path = os.path.join(os.path.dirname(self.db_path), "match_results.csv")
            try:
                export_match_results(result, export_path)
                steps_log.append({"step": "export", "status": "done", "detail": export_path})
            except Exception as e:
                steps_log.append({
                    "step": "export", "status": "error",
                    "detail": err("error_exporting_csv", detail=str(e)),
                })
                export_path = None

            return _ok({
                "steps": steps_log,
                "n_matched": n_matched,
                "n_total": len(result.assignment),
                "rounds_run": result.rounds_run,
                "export_path": export_path,
                "stb_redrawn": stb_redrawn,
            })
        except BaseException as e:
            # BaseException (khong chi Exception): KeyboardInterrupt/
            # SystemExit KHONG ke thua tu Exception, nhung mot "crash
            # giua chung" phai duoc rollback du no la loai nao — full
            # rollback (Option A) khong duoc phep chi ap dung cho mot
            # so loai loi. Sau khi don dep xong, neu day la tin hieu
            # dieu khien tien trinh (Ctrl+C, thoat) thi PHAI nem lai
            # (raise) thay vi nuot thanh {ok: False} nhu mot loi
            # nghiep vu binh thuong.
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
                conn.close()
                steps_log.append({"step": "rollback", "status": "done", "detail": err("pipeline_rolled_back")})
            if not isinstance(e, Exception):
                raise
            error_entry = err("error_running_pipeline", detail=str(e))
            steps_log.append({"step": "unknown", "status": "error", "detail": error_entry})
            return _fail({"steps": steps_log, "errors": [error_entry, traceback.format_exc()]})

    # -----------------------------------------------------------------
    # NHẬP DỮ LIỆU TỪ MICROSOFT FORMS (CSV đã chuẩn hoá bởi
    # 06_ms_forms_transform.py) — trước đây KHÔNG có đường nào để CSV
    # này vào app.db, đây là mảnh còn thiếu duy nhất trong luồng dữ liệu.
    #
    # JS đọc file bằng FileReader.readAsText() ở phía trình duyệt rồi
    # gửi NGUYÊN VĂN nội dung CSV (chuỗi text) qua đây — không cần
    # main.py hỗ trợ thêm gì, không phụ thuộc hộp thoại chọn file gốc
    # của hệ điều hành (vốn không ổn định trong mọi bản pywebview).
    #
    # Hỗ trợ 2 định dạng cho MỖI loại CSV — tự nhận diện theo header,
    # không cần người dùng chọn định dạng:
    #   (a) "dài" (long) — đúng 1-1 với cấu trúc bảng DB, do
    #       06_ms_forms_transform.py xuất ra:
    #         nguyện vọng:      student_id,name,club_id,rank
    #         chọn club thi:    student_id,club_id
    #   (b) "rộng" (wide) — 1 dòng/học sinh, tiện đọc bằng mắt:
    #         nguyện vọng:      student_id,name,pref_1,pref_2,...,pref_10
    #         chọn club thi:    student_id,name,test_club_1,test_club_2,...
    # -----------------------------------------------------------------

    @staticmethod
    def _parse_csv_rows(csv_text: str):
        """Tự nhận diện dấu phân cách (, hoặc ;) và trả về (fieldnames, rows)."""
        sample = csv_text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(io.StringIO(csv_text), dialect=dialect)
        fieldnames = [ (f or "").strip().lower() for f in (reader.fieldnames or []) ]
        rows = []
        for raw_row in reader:
            row = { (k or "").strip().lower(): (v.strip() if isinstance(v, str) else v)
                    for k, v in raw_row.items() if k is not None }
            rows.append(row)
        return fieldnames, rows

    def preview_import_csv(self, csv_text: str, kind: str):
        """
        Xem trước trước khi nhập thật (không ghi DB) — cho UI hiện
        'phát hiện định dạng X, Y dòng, Z học sinh sẽ được tạo mới'
        trước khi người dùng bấm xác nhận nhập.
        kind: "preferences" hoặc "test_selection"
        """
        try:
            fieldnames, rows = self._parse_csv_rows(csv_text)
            if not rows:
                return _fail(err("csv_empty"))

            is_wide = any(f.startswith("pref_") or f.startswith("test_club_") for f in fieldnames)
            fmt = "wide" if is_wide else "long"

            conn = connect_db(self.db_path)
            existing_ids = {r[0] for r in conn.execute("SELECT student_id FROM students")}
            conn.close()

            row_student_ids = {r.get("student_id", "") for r in rows if r.get("student_id")}
            new_students = [sid for sid in row_student_ids if sid not in existing_ids]

            return _ok({
                "format": fmt,
                "kind": kind,
                "fieldnames": fieldnames,
                "n_rows": len(rows),
                "n_students_detected": len(row_student_ids),
                "n_new_students": len(new_students),
                "sample_row": rows[0] if rows else None,
            })
        except Exception as e:
            return _fail(err("error_reading_csv_preview", detail=str(e)))

    def import_preferences_csv(self, csv_text: str, create_missing_students: bool = True):
        """
        Nhập CSV nguyện vọng (Bước 2 — xếp hạng) từ Microsoft Forms.
        Ghi đè TOÀN BỘ nguyện vọng cũ của TỪNG học sinh xuất hiện trong
        file (giống hành vi submit_preferences ở kiosk) — không đụng
        tới học sinh không có trong file.
        """
        try:
            fieldnames, rows = self._parse_csv_rows(csv_text)
            if not rows:
                return _fail(err("csv_empty"))

            is_wide = any(f.startswith("pref_") for f in fieldnames)

            # Gom thanh { student_id: (name, [club_id_theo_thu_tu]) }
            grouped: dict = {}
            if is_wide:
                pref_cols = sorted(
                    [f for f in fieldnames if f.startswith("pref_")],
                    key=lambda f: int(f.split("_")[1]) if f.split("_")[1].isdigit() else 999,
                )
                for row in rows:
                    sid = row.get("student_id")
                    if not sid:
                        continue
                    ordered = [row[c] for c in pref_cols if row.get(c)]
                    grouped[sid] = (row.get("name", ""), ordered)
            else:
                if "student_id" not in fieldnames or "club_id" not in fieldnames:
                    return _fail(err("csv_missing_columns", fieldnames=fieldnames))
                has_rank = "rank" in fieldnames
                by_sid_rows: dict = {}
                for row in rows:
                    sid = row.get("student_id")
                    if not sid or not row.get("club_id"):
                        continue
                    by_sid_rows.setdefault(sid, []).append(row)
                for sid, sid_rows in by_sid_rows.items():
                    if has_rank:
                        sid_rows.sort(key=lambda r: int(r["rank"]) if r.get("rank", "").isdigit() else 999)
                    name = next((r.get("name") for r in sid_rows if r.get("name")), "")
                    grouped[sid] = (name, [r["club_id"] for r in sid_rows])

            conn = connect_db(self.db_path)
            cur = conn.cursor()
            valid_club_ids = {r[0] for r in cur.execute("SELECT club_id FROM clubs")}
            existing_students = {r[0] for r in cur.execute("SELECT student_id FROM students")}

            n_created, n_updated, n_skipped = 0, 0, 0
            row_errors = []

            for sid, (name, ordered_clubs) in grouped.items():
                # loai bo trung lap giu thu tu xuat hien dau tien
                seen = set()
                deduped = []
                for cid in ordered_clubs:
                    if cid not in seen:
                        seen.add(cid)
                        deduped.append(cid)
                if len(deduped) != len(ordered_clubs):
                    row_errors.append(err("csv_pref_duplicate_deduped", student_id=sid))

                if len(deduped) > 10:
                    row_errors.append(err("csv_pref_too_many_skipped", student_id=sid, count=len(deduped)))
                    n_skipped += 1
                    continue

                invalid_clubs = [c for c in deduped if c not in valid_club_ids]
                if invalid_clubs:
                    row_errors.append(err("csv_unknown_clubs_skipped", student_id=sid, club_ids=invalid_clubs))
                    n_skipped += 1
                    continue

                if sid not in existing_students:
                    if not create_missing_students:
                        row_errors.append(err("csv_student_missing_skipped", student_id=sid))
                        n_skipped += 1
                        continue
                    cur.execute(
                        "INSERT INTO students (student_id, name, stb_number, reserve_group) "
                        "VALUES (?, ?, NULL, NULL)",
                        (sid, name or sid),
                    )
                    existing_students.add(sid)
                    n_created += 1
                elif name:
                    cur.execute(
                        "UPDATE students SET name = ? WHERE student_id = ? AND (name IS NULL OR name = '')",
                        (name, sid),
                    )

                cur.execute("DELETE FROM preferences WHERE student_id = ?", (sid,))
                cur.executemany(
                    "INSERT INTO preferences (student_id, club_id, rank) VALUES (?, ?, ?)",
                    [(sid, cid, i + 1) for i, cid in enumerate(deduped)],
                )
                n_updated += 1

            conn.commit()
            conn.close()

            return _ok({
                "n_students_created": n_created,
                "n_students_with_preferences_written": n_updated,
                "n_students_skipped": n_skipped,
                "warnings": row_errors,
            })
        except Exception as e:
            return _fail([err("error_importing_preferences_csv", detail=str(e)), traceback.format_exc()])

    def import_test_selection_csv(self, csv_text: str, create_missing_students: bool = True):
        """
        Nhập CSV chọn club muốn thi/xét (Bước 1 — tick-box) từ
        Microsoft Forms. Ghi đè toàn bộ lựa chọn thi cũ của từng học
        sinh xuất hiện trong file, giống hành vi submit_test_selection.
        """
        try:
            fieldnames, rows = self._parse_csv_rows(csv_text)
            if not rows:
                return _fail(err("csv_empty"))

            is_wide = any(f.startswith("test_club_") for f in fieldnames)

            grouped: dict = {}
            if is_wide:
                test_cols = [f for f in fieldnames if f.startswith("test_club_")]
                for row in rows:
                    sid = row.get("student_id")
                    if not sid:
                        continue
                    selected = [row[c] for c in test_cols if row.get(c)]
                    grouped[sid] = (row.get("name", ""), selected)
            else:
                if "student_id" not in fieldnames or "club_id" not in fieldnames:
                    return _fail(err("csv_missing_columns", fieldnames=fieldnames))
                for row in rows:
                    sid = row.get("student_id")
                    if not sid or not row.get("club_id"):
                        continue
                    name, clubs_list = grouped.get(sid, ("", []))
                    grouped[sid] = (row.get("name") or name, clubs_list + [row["club_id"]])

            conn = connect_db(self.db_path)
            cur = conn.cursor()
            valid_club_ids = {r[0] for r in cur.execute("SELECT club_id FROM clubs")}
            existing_students = {r[0] for r in cur.execute("SELECT student_id FROM students")}

            n_created, n_updated, n_skipped = 0, 0, 0
            row_errors = []

            for sid, (name, club_ids) in grouped.items():
                deduped = sorted(set(club_ids), key=club_ids.index)
                invalid_clubs = [c for c in deduped if c not in valid_club_ids]
                if invalid_clubs:
                    row_errors.append(err("csv_unknown_clubs_skipped", student_id=sid, club_ids=invalid_clubs))
                    n_skipped += 1
                    continue

                if sid not in existing_students:
                    if not create_missing_students:
                        row_errors.append(err("csv_student_missing_skipped", student_id=sid))
                        n_skipped += 1
                        continue
                    cur.execute(
                        "INSERT INTO students (student_id, name, stb_number, reserve_group) "
                        "VALUES (?, ?, NULL, NULL)",
                        (sid, name or sid),
                    )
                    existing_students.add(sid)
                    n_created += 1
                elif name:
                    cur.execute(
                        "UPDATE students SET name = ? WHERE student_id = ? AND (name IS NULL OR name = '')",
                        (name, sid),
                    )

                cur.execute("DELETE FROM club_test_selection WHERE student_id = ?", (sid,))
                cur.executemany(
                    "INSERT INTO club_test_selection (student_id, club_id) VALUES (?, ?)",
                    [(sid, cid) for cid in deduped],
                )
                n_updated += 1

            conn.commit()
            conn.close()

            return _ok({
                "n_students_created": n_created,
                "n_students_with_selection_written": n_updated,
                "n_students_skipped": n_skipped,
                "warnings": row_errors,
            })
        except Exception as e:
            return _fail([err("error_importing_test_selection_csv", detail=str(e)), traceback.format_exc()])

    # -----------------------------------------------------------------
    # CHẤM ĐIỂM MÙ (blind scoring) — trước đây club_scores chỉ được
    # điền qua seed_sample_data(), KHÔNG có màn hình cho giáo viên chấm
    # thật. Yêu cầu thiết kế cốt lõi "chấm mù" (grader không thấy STB,
    # không thấy thứ hạng nguyện vọng của học sinh) được ĐẢM BẢO Ở ĐÂY
    # bằng cách chỉ trả về student_id + tên — KHÔNG BAO GIỜ trả stb_number
    # hay preferences trong bất kỳ hàm nào của mục này.
    # -----------------------------------------------------------------

    def get_scoring_overview(self):
        """Tổng quan tiến độ chấm điểm theo từng club — cho màn hình chọn club để chấm."""
        try:
            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute("""
                SELECT c.club_id, c.name,
                       COUNT(DISTINCT t.student_id) AS n_applicants,
                       COUNT(DISTINCT sc.student_id) AS n_scored
                FROM clubs c
                LEFT JOIN club_test_selection t ON t.club_id = c.club_id
                LEFT JOIN club_scores sc ON sc.club_id = c.club_id AND sc.student_id = t.student_id
                GROUP BY c.club_id
                ORDER BY c.club_id
            """).fetchall()
            conn.close()
            return _ok([dict(r) for r in rows])
        except Exception as e:
            return _fail(err("error_reading_scoring_overview", detail=str(e)))

    def get_club_applicants_for_scoring(self, club_id: str):
        """
        Danh sách học sinh cần chấm cho 1 club — CHỈ mã số, tên, và
        điểm đã chấm trước đó (nếu có, để sửa). KHÔNG kèm STB, KHÔNG
        kèm thứ hạng nguyện vọng — đúng yêu cầu chấm mù (blind scoring).
        """
        try:
            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            club = cur.execute(
                "SELECT club_id, name FROM clubs WHERE club_id = ?", (club_id,)
            ).fetchone()
            if not club:
                conn.close()
                return _fail(err("club_not_found", club_id=club_id))
            rows = cur.execute("""
                SELECT s.student_id, s.name, sc.score
                FROM club_test_selection t
                JOIN students s ON s.student_id = t.student_id
                LEFT JOIN club_scores sc ON sc.student_id = t.student_id AND sc.club_id = t.club_id
                WHERE t.club_id = ?
                ORDER BY s.student_id
            """, (club_id,)).fetchall()
            conn.close()
            return _ok({
                "club_id": club["club_id"],
                "club_name": club["name"],
                "applicants": [dict(r) for r in rows],
            })
        except Exception as e:
            return _fail(err("error_reading_scoring_list", detail=str(e)))

    def submit_club_scores(self, club_id: str, scores: list):
        """
        Lưu điểm chấm cho 1 club. scores: [{"student_id": "...", "score": 8.5}, ...]
        Chỉ cho điểm học sinh THỰC SỰ có trong club_test_selection của
        club này (không thể chấm 'khống' cho học sinh không thi/xét).
        """
        try:
            if not isinstance(scores, list) or not scores:
                return _fail(err("scores_must_be_nonempty_list"))

            conn = connect_db(self.db_path)
            cur = conn.cursor()
            club_exists = cur.execute(
                "SELECT 1 FROM clubs WHERE club_id = ?", (club_id,)
            ).fetchone()
            if not club_exists:
                conn.close()
                return _fail(err("club_not_found", club_id=club_id))

            valid_applicants = {
                r[0] for r in cur.execute(
                    "SELECT student_id FROM club_test_selection WHERE club_id = ?",
                    (club_id,),
                ).fetchall()
            }

            n_saved, skipped = 0, []
            for entry in scores:
                sid = entry.get("student_id")
                score = entry.get("score")
                if sid not in valid_applicants:
                    skipped.append(err("score_not_applicant", student_id=sid))
                    continue
                if score is None or score == "":
                    # cho phep xoa diem (bo trong o) bang cach xoa ban ghi
                    cur.execute(
                        "DELETE FROM club_scores WHERE student_id = ? AND club_id = ?",
                        (sid, club_id),
                    )
                    continue
                try:
                    score = float(score)
                except (TypeError, ValueError):
                    skipped.append(err("score_not_a_number", student_id=sid, score=score))
                    continue
                cur.execute(
                    "INSERT INTO club_scores (student_id, club_id, score) VALUES (?, ?, ?) "
                    "ON CONFLICT(student_id, club_id) DO UPDATE SET score = excluded.score",
                    (sid, club_id, score),
                )
                n_saved += 1

            conn.commit()
            conn.close()
            return _ok({"club_id": club_id, "n_saved": n_saved, "warnings": skipped})
        except Exception as e:
            return _fail(err("error_saving_scores", detail=str(e)))

    # -----------------------------------------------------------------
    # TAB "KẾT QUẢ"
    # -----------------------------------------------------------------

    def get_match_results(self, search: str = ""):
        """Bảng kết quả, lọc theo student_id/name nếu search có giá trị."""
        try:
            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            query = """
                SELECT m.student_id, s.name, m.club_id, c.name as club_name,
                       m.matched_tier, m.rank_in_student_pref
                FROM match_results m
                JOIN students s ON s.student_id = m.student_id
                LEFT JOIN clubs c ON c.club_id = m.club_id
            """
            params = ()
            if search:
                query += " WHERE m.student_id LIKE ? OR s.name LIKE ?"
                params = (f"%{search}%", f"%{search}%")
            query += " ORDER BY m.student_id"
            rows = cur.execute(query, params).fetchall()
            conn.close()
            return _ok([dict(r) for r in rows])
        except Exception as e:
            return _fail(err("error_reading_results", detail=str(e)))

    def get_club_fill_stats(self):
        """Tỉ lệ lấp đầy mỗi club — dùng vẽ thanh progress bar."""
        try:
            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute("""
                SELECT c.club_id, c.name, c.capacity, c.reserve_capacity,
                       COUNT(m.student_id) as matched
                FROM clubs c
                LEFT JOIN match_results m ON m.club_id = c.club_id
                GROUP BY c.club_id
                ORDER BY c.club_id
            """).fetchall()
            conn.close()
            return _ok([dict(r) for r in rows])
        except Exception as e:
            return _fail(err("error_reading_club_stats", detail=str(e)))

    def export_csv(self, output_path: str):
        try:
            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute("SELECT student_id, club_id FROM match_results ORDER BY student_id").fetchall()
            conn.close()
            import csv
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["student_id", "club_id"])
                for r in rows:
                    w.writerow([r["student_id"], r["club_id"] or ""])
            return _ok({"path": output_path, "n_rows": len(rows)})
        except Exception as e:
            return _fail(err("error_exporting_csv", detail=str(e)))

    # -----------------------------------------------------------------
    # TAB "QUẢN LÝ CLUB & DỰ TRỮ" (admin thao tác trực tiếp — trường tự quyết)
    # -----------------------------------------------------------------

    def list_clubs_admin(self):
        """Giống list_clubs nhưng bao gồm cả reserve_group, dùng cho form sửa."""
        return self.list_clubs()

    def create_or_update_club(
        self, club_id: str, name: str, capacity: int,
        reserve_capacity: int = 0, reserve_group: str = "",
    ):
        """
        Tạo mới hoặc cập nhật 1 club (UPSERT theo club_id).
        reserve_group: chuỗi tự do do trường tự đặt (vd 'chinh_sach',
        'khoi10', hoặc để trống '' nếu club không có dự trữ).
        """
        try:
            capacity = int(capacity)
            reserve_capacity = int(reserve_capacity)
            if capacity <= 0:
                return _fail(err("capacity_must_be_positive"))
            if reserve_capacity > capacity:
                return _fail(err("reserve_capacity_exceeds_capacity"))
            if not club_id.strip():
                return _fail(err("club_id_required"))

            reserve_group_value = reserve_group.strip() or None

            conn = connect_db(self.db_path)
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO clubs (club_id, name, capacity, reserve_capacity, reserve_group)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(club_id) DO UPDATE SET
                    name=excluded.name,
                    capacity=excluded.capacity,
                    reserve_capacity=excluded.reserve_capacity,
                    reserve_group=excluded.reserve_group
                """,
                (club_id.strip(), name.strip(), capacity, reserve_capacity, reserve_group_value),
            )
            conn.commit()
            conn.close()
            return _ok({"club_id": club_id, "action": "upserted"})
        except Exception as e:
            return _fail(err("error_saving_club", detail=str(e)))

    def delete_club(self, club_id: str):
        """
        Xoá club — CHẶN nếu đã có preferences/match_results tham chiếu
        tới club này, để tránh mất dữ liệu học sinh đã nộp.
        """
        try:
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            n_prefs = cur.execute(
                "SELECT COUNT(*) FROM preferences WHERE club_id = ?", (club_id,)
            ).fetchone()[0]
            n_matches = cur.execute(
                "SELECT COUNT(*) FROM match_results WHERE club_id = ?", (club_id,)
            ).fetchone()[0]
            if n_prefs > 0 or n_matches > 0:
                conn.close()
                return _fail(err(
                    "cannot_delete_club_referenced",
                    club_id=club_id, n_prefs=n_prefs, n_matches=n_matches,
                ))
            cur.execute("DELETE FROM clubs WHERE club_id = ?", (club_id,))
            cur.execute("DELETE FROM club_test_selection WHERE club_id = ?", (club_id,))
            cur.execute("DELETE FROM club_scores WHERE club_id = ?", (club_id,))
            conn.commit()
            conn.close()
            return _ok({"club_id": club_id, "deleted": True})
        except Exception as e:
            return _fail(err("error_deleting_club", detail=str(e)))

    def list_reserve_groups_in_use(self):
        """Danh sách các reserve_group đang được dùng (để gợi ý trong form, tránh gõ sai chính tả)."""
        try:
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT DISTINCT reserve_group FROM clubs WHERE reserve_group IS NOT NULL "
                "UNION "
                "SELECT DISTINCT reserve_group FROM students WHERE reserve_group IS NOT NULL"
            ).fetchall()
            conn.close()
            return _ok(sorted(r[0] for r in rows if r[0]))
        except Exception as e:
            return _fail(err("error_reading_reserve_groups", detail=str(e)))

    def set_student_reserve_group(self, student_id: str, reserve_group: str):
        """Gán (hoặc gỡ, nếu reserve_group='') diện dự trữ cho 1 học sinh."""
        try:
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            exists = cur.execute(
                "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if not exists:
                conn.close()
                return _fail(err("student_not_found", student_id=student_id))
            value = reserve_group.strip() or None
            cur.execute(
                "UPDATE students SET reserve_group = ? WHERE student_id = ?",
                (value, student_id),
            )
            conn.commit()
            conn.close()
            return _ok({"student_id": student_id, "reserve_group": value})
        except Exception as e:
            return _fail(err("error_assigning_reserve_group", detail=str(e)))

    def bulk_set_reserve_group(self, student_ids: list, reserve_group: str):
        """Gán hàng loạt — dùng khi trường có sẵn danh sách (vd cả 1 khối lớp)."""
        try:
            if not isinstance(student_ids, list) or not student_ids:
                return _fail(err("student_ids_must_be_nonempty_list"))
            value = reserve_group.strip() or None
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            existing_ids = {
                r[0] for r in cur.execute("SELECT student_id FROM students").fetchall()
            }
            missing = [sid for sid in student_ids if sid not in existing_ids]
            valid_ids = [sid for sid in student_ids if sid in existing_ids]
            cur.executemany(
                "UPDATE students SET reserve_group = ? WHERE student_id = ?",
                [(value, sid) for sid in valid_ids],
            )
            conn.commit()
            conn.close()
            return _ok({"n_updated": len(valid_ids), "not_found": missing})
        except Exception as e:
            return _fail(err("error_bulk_assigning", detail=str(e)))

    def list_students_admin(self, search: str = "", page: int = 1, page_size: int = 100):
        """
        Danh sách học sinh kèm reserve_group hiện tại, cho tab quản lý.
        CÓ PHÂN TRANG (trước đây LIMIT 100 cứng khiến trường >100 học
        sinh bị ẩn âm thầm không báo). Trả kèm total/total_pages để UI
        vẽ nút điều hướng trang.
        """
        try:
            page = max(1, int(page))
            page_size = max(1, min(int(page_size), 500))
            offset = (page - 1) * page_size

            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            where_clause = ""
            params: tuple = ()
            if search:
                where_clause = " WHERE student_id LIKE ? OR name LIKE ?"
                params = (f"%{search}%", f"%{search}%")

            total = cur.execute(
                f"SELECT COUNT(*) FROM students{where_clause}", params
            ).fetchone()[0]

            rows = cur.execute(
                f"SELECT student_id, name, reserve_group FROM students{where_clause} "
                "ORDER BY student_id LIMIT ? OFFSET ?",
                params + (page_size, offset),
            ).fetchall()
            conn.close()

            total_pages = max(1, (total + page_size - 1) // page_size)
            return _ok({
                "rows": [dict(r) for r in rows],
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            })
        except Exception as e:
            return _fail(err("error_reading_student_list", detail=str(e)))

    # -----------------------------------------------------------------
    # TAB "NHẬP DỰ PHÒNG" (kiosk fallback entry)
    # -----------------------------------------------------------------

    def list_clubs(self):
        try:
            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT club_id, name, capacity, reserve_capacity FROM clubs ORDER BY club_id"
            ).fetchall()
            conn.close()
            return _ok([dict(r) for r in rows])
        except Exception as e:
            return _fail(err("error_reading_club_list", detail=str(e)))

    def search_students(self, query: str):
        try:
            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT student_id, name FROM students "
                "WHERE student_id LIKE ? OR name LIKE ? LIMIT 20",
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
            conn.close()
            return _ok([dict(r) for r in rows])
        except Exception as e:
            return _fail(err("error_searching_students", detail=str(e)))

    def get_student_entry_state(self, student_id: str):
        """
        Trạng thái nhập liệu hiện tại của 1 học sinh — dùng để tab
        'Nhập dự phòng' hiển thị lại nếu học sinh quay lại kiosk.
        """
        try:
            conn = connect_db(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            student = cur.execute(
                "SELECT student_id, name FROM students WHERE student_id = ?",
                (student_id,),
            ).fetchone()
            if not student:
                conn.close()
                return _fail(err("student_not_found", student_id=student_id))

            tested = [
                r["club_id"]
                for r in cur.execute(
                    "SELECT club_id FROM club_test_selection WHERE student_id = ?",
                    (student_id,),
                ).fetchall()
            ]
            prefs = [
                r["club_id"]
                for r in cur.execute(
                    "SELECT club_id FROM preferences WHERE student_id = ? ORDER BY rank",
                    (student_id,),
                ).fetchall()
            ]
            conn.close()
            return _ok({
                "student_id": student["student_id"],
                "name": student["name"],
                "tested_clubs": tested,
                "ranked_clubs": prefs,
            })
        except Exception as e:
            return _fail(err("error_reading_student_state", detail=str(e)))

    def submit_test_selection(self, student_id: str, club_ids: list):
        """
        BƯỚC 1 (độc lập với xếp hạng) — tick-box club muốn thi/xét.
        Ghi đè toàn bộ lựa chọn cũ của học sinh này.
        """
        try:
            if not isinstance(club_ids, list):
                return _fail(err("club_ids_must_be_list"))
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            exists = cur.execute(
                "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if not exists:
                conn.close()
                return _fail(err("student_not_found", student_id=student_id))

            invalid = [
                cid for cid in club_ids
                if not cur.execute(
                    "SELECT 1 FROM clubs WHERE club_id = ?", (cid,)
                ).fetchone()
            ]
            if invalid:
                conn.close()
                return _fail(err("unknown_clubs", club_ids=invalid))

            cur.execute(
                "DELETE FROM club_test_selection WHERE student_id = ?", (student_id,)
            )
            cur.executemany(
                "INSERT INTO club_test_selection (student_id, club_id) VALUES (?, ?)",
                [(student_id, cid) for cid in club_ids],
            )
            conn.commit()
            conn.close()
            return _ok({"student_id": student_id, "n_selected": len(club_ids)})
        except Exception as e:
            return _fail(err("error_saving_test_selection", detail=str(e)))

    def submit_preferences(self, student_id: str, ordered_club_ids: list):
        """
        BƯỚC 2 (độc lập với tick-box thi) — xếp hạng nguyện vọng,
        tối đa 10 club (giới hạn Microsoft Forms Ranking, giữ đồng
        bộ với luồng nhập chính).
        """
        try:
            if not isinstance(ordered_club_ids, list):
                return _fail(err("ordered_club_ids_must_be_list"))
            if len(ordered_club_ids) == 0:
                return _fail(err("must_rank_at_least_one"))
            if len(ordered_club_ids) > 10:
                return _fail(err("max_10_preferences"))
            if len(ordered_club_ids) != len(set(ordered_club_ids)):
                return _fail(err("duplicate_preference_in_list"))

            conn = connect_db(self.db_path)
            cur = conn.cursor()
            exists = cur.execute(
                "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if not exists:
                conn.close()
                return _fail(err("student_not_found", student_id=student_id))

            invalid = [
                cid for cid in ordered_club_ids
                if not cur.execute(
                    "SELECT 1 FROM clubs WHERE club_id = ?", (cid,)
                ).fetchone()
            ]
            if invalid:
                conn.close()
                return _fail(err("unknown_clubs", club_ids=invalid))

            cur.execute("DELETE FROM preferences WHERE student_id = ?", (student_id,))
            cur.executemany(
                "INSERT INTO preferences (student_id, club_id, rank) VALUES (?, ?, ?)",
                [(student_id, cid, i + 1) for i, cid in enumerate(ordered_club_ids)],
            )
            conn.commit()
            conn.close()
            return _ok({"student_id": student_id, "n_ranked": len(ordered_club_ids)})
        except Exception as e:
            return _fail(err("error_saving_preferences", detail=str(e)))

    def create_student_if_missing(self, student_id: str, name: str):
        """Kiosk fallback: nếu học sinh chưa có trong students, tạo mới (chưa có STB)."""
        try:
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            exists = cur.execute(
                "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if not exists:
                cur.execute(
                    "INSERT INTO students (student_id, name, stb_number, reserve_group) "
                    "VALUES (?, ?, NULL, NULL)",
                    (student_id, name),
                )
                conn.commit()
            conn.close()
            return _ok({"student_id": student_id, "created": not exists})
        except Exception as e:
            return _fail(err("error_creating_student", detail=str(e)))

    def reset_student_entry(self, student_id: str):
        """
        Nút 'Sửa lại từ đầu' — xoá lựa chọn thi (Bước 1) và nguyện vọng
        (Bước 2) hiện tại của học sinh để nhập lại từ đầu tại kiosk.
        KHÔNG xoá bản ghi học sinh (giữ nguyên student_id/tên/STB/reserve_group).
        """
        try:
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            exists = cur.execute(
                "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if not exists:
                conn.close()
                return _fail(err("student_not_found", student_id=student_id))
            cur.execute("DELETE FROM club_test_selection WHERE student_id = ?", (student_id,))
            cur.execute("DELETE FROM preferences WHERE student_id = ?", (student_id,))
            conn.commit()
            conn.close()
            return _ok({"student_id": student_id, "reset": True})
        except Exception as e:
            return _fail(err("error_resetting_student_entry", detail=str(e)))

    def delete_student(self, student_id: str):
        """
        Nút 'Xoá học sinh' — xoá hẳn học sinh khỏi hệ thống (dùng khi
        tạo nhầm mã / trùng học sinh tại kiosk). CHẶN nếu học sinh đã
        có mặt trong match_results (đã qua lần chạy pipeline gần nhất)
        để tránh làm lệch thống kê lấp đầy club và mất dấu kiểm toán —
        phải chạy lại pipeline (hoặc xử lý ở tab Quản lý) trước.
        """
        try:
            conn = connect_db(self.db_path)
            cur = conn.cursor()
            exists = cur.execute(
                "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if not exists:
                conn.close()
                return _fail(err("student_not_found", student_id=student_id))
            n_matches = cur.execute(
                "SELECT COUNT(*) FROM match_results WHERE student_id = ?", (student_id,)
            ).fetchone()[0]
            if n_matches > 0:
                conn.close()
                return _fail(err("cannot_delete_student_matched", student_id=student_id))
            cur.execute("DELETE FROM club_test_selection WHERE student_id = ?", (student_id,))
            cur.execute("DELETE FROM preferences WHERE student_id = ?", (student_id,))
            cur.execute("DELETE FROM club_scores WHERE student_id = ?", (student_id,))
            cur.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
            conn.commit()
            conn.close()
            return _ok({"student_id": student_id, "deleted": True})
        except Exception as e:
            return _fail(err("error_deleting_student", detail=str(e)))
