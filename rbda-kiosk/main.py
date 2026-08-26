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

import webview

from api import PipelineAPI

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


def main() -> None:
    db_path = resolve_db_path()
    api = PipelineAPI(db_path)

    index_path = os.path.join(RESOURCE_DIR, "index.html")
    window = webview.create_window(
        APP_TITLE,
        index_path,
        js_api=api,
        width=1280,
        height=800,
        min_size=(1024, 640),
    )
    # Cho phép các tính năng dùng hộp thoại gốc của hệ điều hành sau này
    # (hiện tại không tính năng nào bắt buộc phải có window ref).
    api.set_window(window)

    webview.start()


if __name__ == "__main__":
    main()
