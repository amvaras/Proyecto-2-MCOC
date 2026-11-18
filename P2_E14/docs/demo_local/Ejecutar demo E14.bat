@echo off
setlocal
cd /d "%~dp0..\.."
if not exist ".venv\Scripts\python.exe" (
  echo Primero abre Iniciar E14.bat para instalar el entorno de esta copia.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -X utf8 -B "docs\demo_local\ejecutar.py" --abrir %*
if errorlevel 1 (
  echo La ejecucion no termino correctamente. Revisa el mensaje anterior.
  pause
  exit /b 1
)
pause
