@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\install.ps1"
if not exist ".venv\Scripts\python.exe" exit /b 1
".venv\Scripts\python.exe" -X utf8 -B "web\abrir.py" %*
