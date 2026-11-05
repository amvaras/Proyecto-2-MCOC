@echo off
cd /d "%~dp0"
set "PY_E08=..\.venv-e08\Scripts\python.exe"
if not exist "%PY_E08%" set "PY_E08=.venv\Scripts\python.exe"
if not exist "%PY_E08%" (
  echo Instala primero el entorno segun README.md.
  pause
  exit /b 1
)
"%PY_E08%" -X utf8 -B web\abrir.py
if errorlevel 1 pause
