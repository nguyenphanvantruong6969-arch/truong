@echo off
REM build_windows.bat — chay tren May Windows co Python 3.10+
REM Ket qua: dist\PhanBoCauLacBo\PhanBoCauLacBo.exe

python -m venv .venv_build
call .venv_build\Scripts\activate.bat

pip install -r requirements.txt

pyinstaller kiosk.spec --noconfirm

echo.
echo ============================================================
echo  XONG. File chay duoc nam o:
echo  dist\PhanBoCauLacBo\PhanBoCauLacBo.exe
echo  (phai copy CA THU MUC PhanBoCauLacBo, khong chi rieng .exe,
echo   vi no can thu muc _internal di kem)
echo ============================================================
pause
