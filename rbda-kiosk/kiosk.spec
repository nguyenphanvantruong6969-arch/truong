# -*- mode: python ; coding: utf-8 -*-
"""
kiosk.spec
==========
Đóng gói ứng dụng kiosk thành 1 file thực thi độc lập bằng PyInstaller.

QUAN TRỌNG: PyInstaller đóng gói CHO ĐÚNG HỆ ĐIỀU HÀNH ĐANG CHẠY LỆNH.
Muốn có file .exe cho Windows, LỆNH `pyinstaller kiosk.spec` PHẢI CHẠY
TRÊN MÁY WINDOWS (hoặc máy ảo/CI chạy Windows) — không build chéo được
từ Linux/macOS ra .exe.

Cách dùng (trên Windows, đã cài Python 3.10+ và requirements.txt):
    pip install -r requirements.txt
    pyinstaller kiosk.spec
    # -> dist/PhanBoCauLacBo/PhanBoCauLacBo.exe

Cách dùng (trên Linux/macOS — build ra file thực thi cho CHÍNH hệ đó,
hữu ích để tự kiểm tra cấu hình đóng gói không lỗi trước khi build
Windows thật):
    pyinstaller kiosk.spec
"""

import sys

block_cipher = None

datas = [
    ("index.html", "."),
    ("style.css", "."),
    ("app.js", "."),
    ("assets/fonts", "assets/fonts"),
]

hiddenimports = ["webview"]

# pywebview chọn backend GUI khác nhau theo hệ điều hành. Khai báo rõ để
# PyInstaller không bỏ sót khi phân tích tĩnh (static analysis đôi khi
# không thấy import động bên trong thư viện webview).
if sys.platform.startswith("win"):
    hiddenimports += ["webview.platforms.edgechromium", "webview.platforms.winforms", "clr"]
elif sys.platform == "darwin":
    hiddenimports += ["webview.platforms.cocoa"]
else:
    hiddenimports += ["webview.platforms.gtk", "webview.platforms.qt"]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PhanBoCauLacBo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # False = khong hien cua so console den phia sau kiosk
    icon=None,       # co the thay bang duong dan .ico neu truong co logo
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PhanBoCauLacBo",
)
