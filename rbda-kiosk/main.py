"""
main.py
=======
Điểm khởi động ứng dụng kiosk. Tạo cửa sổ pywebview, gắn PipelineAPI
làm js_api để index.html/app.js gọi qua window.pywebview.api.*

Cách chạy:
    python3 main.py                    # dùng app.db cùng thư mục main.py
    python3 main.py /duong/dan/khac.db # chỉ định DB khác
"""

import os
import sys
import traceback

import browser_host
from api import PipelineAPI
from recovery import RecoveryAPI

APP_TITLE = "Phân bổ Câu lạc bộ — RB-DA"

# QUAN TRỌNG khi đóng gói bằng PyInstaller: __file__ của main.py KHÔNG
# trỏ tới thư mục chứa file .exe thật — nó trỏ vào thư mục tài nguyên
# tạm (_internal/ ở chế độ onedir, hoặc thư mục giải nén tạm ở chế độ
# onefile). Nếu dùng __file__ để tính đường dẫn app.db, DB sẽ bị ghi
# nhầm vào bên trong _internal/ (đã tự phát hiện bug này bằng cách
# build thật và chạy thử — xem PACKAGING_HUONGDAN.md).
#
#   BASE_DIR      -> nơi ĐẶT app.db (phải là thư mục chứa .exe thật,
#                     để dữ liệu không bị mất khi build lại/cập nhật app)
#   RESOURCE_DIR  -> nơi ĐỌC tài nguyên đã đóng gói (index.html,
#                     style.css, app.js, assets/fonts/) — ở chế độ đóng
#                     gói, đây là _internal/ (hoặc thư mục tạm), khác
#                     với BASE_DIR; ở chế độ chạy thường (python3
#                     main.py), cả hai trùng nhau.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = BASE_DIR


def resolve_db_path() -> str:
    if len(sys.argv) > 1:
        return os.path.abspath(sys.argv[1])
    return os.path.join(BASE_DIR, "app.db")


def _show_ui(title: str, page: str, js_api, width: int, height: int,
             min_size: tuple) -> None:
    """
    Hiện giao diện `page` với backend `js_api`, THỬ HAI CÁCH theo thứ tự:

      1. Cửa sổ pywebview (ưu tiên — cửa sổ gốc của hệ điều hành).
      2. NẾU pywebview hỏng: máy chủ cục bộ + một CỬA SỔ RIÊNG của trình
         duyệt nhân Chromium (Edge/Chrome), mở bằng cờ `--app=` nên KHÔNG
         có thanh địa chỉ, KHÔNG có tab — nhìn và dùng như ứng dụng
         desktop. Chỉ khi máy không có trình duyệt Chromium nào thì mới
         đành mở tab thường (xem browser_host.py).

    VÌ SAO CẦN CÁCH 2: trên Windows, pywebview bắt buộc đi qua
    pythonnet -> .NET Framework, và mắt xích này đã hỏng thật trên máy
    người dùng sau khi đóng gói bằng PyInstaller:

        RuntimeError: Failed to resolve Python.Runtime.Loader.Initialize
        from ...\\_internal\\pythonnet\\runtime\\Python.Runtime.dll

    Trước đây lỗi đó làm cả tiến trình chết kèm hộp thoại khó hiểu, app
    hoàn toàn không dùng được. Giờ nó chỉ khiến app đổi cách vẽ cửa sổ —
    TOÀN BỘ tính năng giữ nguyên, vì app.js/recovery.js vẫn gọi backend
    qua đúng `window.pywebview.api.*` như cũ (browser_host dựng sẵn cầu
    nối giả lập). Với cờ `--app=`, người dùng vẫn thấy MỘT CỬA SỔ ỨNG
    DỤNG RIÊNG, không phải một tab lẫn trong trình duyệt.
    """
    try:
        import webview

        window = webview.create_window(
            title, os.path.join(RESOURCE_DIR, page), js_api=js_api,
            width=width, height=height, min_size=min_size,
        )
        if hasattr(js_api, "set_window"):
            # Cho phép các tính năng dùng hộp thoại gốc của hệ điều hành
            # sau này (hiện chưa tính năng nào bắt buộc phải có window ref).
            js_api.set_window(window)
        webview.start()
        return
    except BaseException:
        # Nuot MOI loai loi (ke ca khong phai Exception) roi thu cach 2 —
        # con mot duong chay duoc van hon la chet kem stack trace.
        sys.stderr.write(
            "pywebview khong khoi dong duoc, chuyen sang che do trinh duyet:\n"
            + traceback.format_exc()
        )

    browser_host.serve(js_api, RESOURCE_DIR, page, width=width, height=height)


def main() -> None:
    db_path = resolve_db_path()

    # KHÔNG BAO GIỜ được chết ngầm: nếu app.db hỏng/mất, PipelineAPI(...)
    # (gọi init_db bên trong) ném exception NGAY TẠI ĐÂY — TRƯỚC khi có
    # bất kỳ cửa sổ nào được tạo. Không bọc try/except thì tiến trình
    # thoát với exit code 1 và KHÔNG cửa sổ nào hiện ra — đặc biệt
    # nghiêm trọng trên bản build Windows console=False (kiosk), nơi
    # không có terminal nào để người vận hành thấy lỗi (xem
    # ke-hoach-mat-du-lieu.html, nhóm B). Thay vào đó: mở màn hình PHỤC HỒI
    # (recovery.html/recovery.py) cho phép khôi phục từ bản sao lưu tự
    # động (xem PipelineAPI._backup_db trong api.py) hoặc bắt đầu lại
    # với DB trống.
    try:
        api = PipelineAPI(db_path)
    except Exception as e:
        _show_ui(
            APP_TITLE + " — Phục hồi dữ liệu",
            "recovery.html",
            RecoveryAPI(db_path, f"{e}\n\n{traceback.format_exc()}"),
            width=900, height=700, min_size=(700, 560),
        )
        return

    _show_ui(
        APP_TITLE, "index.html", api,
        width=1280, height=800, min_size=(1024, 640),
    )


if __name__ == "__main__":
    main()
