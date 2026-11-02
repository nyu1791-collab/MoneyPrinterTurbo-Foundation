@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
if not exist ".venv\Scripts\python.exe" (
  echo Run uv sync --locked first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe tools\use_youtube_en.py
if errorlevel 1 (
  pause
  exit /b 1
)
if /i "%~1"=="--configure-only" exit /b 0
call webui.bat
exit /b %errorlevel%
