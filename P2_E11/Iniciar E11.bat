@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Preparando el entorno local E11. La primera instalacion necesita Internet.
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1"
  if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -X utf8 -B -c "import numpy, ifcopenshell, pyvista, matplotlib, pytest"
if errorlevel 1 goto repair
".venv\Scripts\python.exe" -X utf8 -B web\abrir.py "%~1"
if errorlevel 1 goto error
exit /b 0
:repair
echo Faltan dependencias; reparando el entorno local.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1"
if errorlevel 1 goto error
".venv\Scripts\python.exe" -X utf8 -B web\abrir.py "%~1"
if errorlevel 1 goto error
exit /b 0
:error
echo No se pudo abrir E11. Revisa el mensaje anterior.
pause
exit /b 1
