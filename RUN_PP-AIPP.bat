@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\pp-aipp-desktop.exe (
  echo PP-AIPP is not installed yet. Run INSTALL_AND_RUN.bat first.
  pause
  exit /b 1
)
start "PP-AIPP" .venv\Scripts\pp-aipp-desktop.exe
