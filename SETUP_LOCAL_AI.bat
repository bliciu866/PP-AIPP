@echo off
setlocal
cd /d "%~dp0"
echo PP-AIPP Local Free AI Setup
echo This installs a free local image model. First setup downloads several GB.
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3.11 or 3.12 is required. Download it from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
if not exist ".local-ai\Scripts\python.exe" py -3.11 -m venv .local-ai
if errorlevel 1 py -3.12 -m venv .local-ai
if errorlevel 1 goto :failed
call ".local-ai\Scripts\python.exe" -m pip install --upgrade pip
call ".local-ai\Scripts\python.exe" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 (
  echo GPU package unavailable. Installing CPU edition.
  call ".local-ai\Scripts\python.exe" -m pip install torch torchvision
)
call ".local-ai\Scripts\python.exe" -m pip install "diffusers>=0.31" "transformers>=4.44" accelerate safetensors Pillow
if errorlevel 1 goto :failed
echo.
echo SUCCESS. Local Free AI is ready. The model downloads automatically on first generation.
pause
exit /b 0
:failed
echo.
echo SETUP FAILED. Check the messages above and your internet connection.
pause
exit /b 1
