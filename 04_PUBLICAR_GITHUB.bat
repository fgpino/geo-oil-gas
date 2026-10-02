@echo off
setlocal
cd /d "%~dp0"
where git >nul 2>nul
if errorlevel 1 goto setup
where gh >nul 2>nul
if errorlevel 1 goto setup
gh auth status >nul 2>nul
if errorlevel 1 goto setup
if exist .venv\Scripts\python.exe (
 .venv\Scripts\python.exe scripts\validar.py
) else (
 py scripts\validar.py
)
if errorlevel 1 goto failed
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\publicar.ps1"
if errorlevel 1 goto failed
pause
exit /b 0
:setup
echo Ejecute primero 00_PREPARAR_GITHUB.bat.
pause
exit /b 1
:failed
echo Publicacion detenida. Revise el mensaje anterior.
pause
exit /b 1
