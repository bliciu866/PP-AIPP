@echo off
setlocal
cd /d "%~dp0"
echo [PP-AIPP] Preparing local environment...
python -m venv .venv
if errorlevel 1 goto :error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e ".[desktop]"
if errorlevel 1 goto :error
start "PP-AIPP" .venv\Scripts\pp-aipp-desktop.exe
exit /b 0
:error
echo.
echo Installation failed. Take a photo of this window and send it in ChatGPT.
pause
exit /b 1
