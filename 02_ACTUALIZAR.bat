@echo off
cd /d "%~dp0"
.venv\Scripts\python scripts\actualizar.py
if errorlevel 1 exit /b 1
.venv\Scripts\python scripts\vincular_318_554.py
if errorlevel 1 (
 echo No se pudo actualizar la vinculacion 318/554. Se conservan las copias disponibles.
)
.venv\Scripts\python scripts\validar.py
pause
