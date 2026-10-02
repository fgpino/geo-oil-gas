@echo off
setlocal
cd /d "%~dp0"
where git >nul 2>nul
if errorlevel 1 goto missing
where gh >nul 2>nul
if errorlevel 1 goto missing
gh auth status >nul 2>nul
if errorlevel 1 (
 gh auth login --hostname github.com --git-protocol https --web
 if errorlevel 1 goto failed
)
gh auth setup-git
if errorlevel 1 goto failed
echo GitHub preparado. Puede ejecutar 04_PUBLICAR_GITHUB.bat.
pause
exit /b 0
:missing
echo Instale Git y GitHub CLI y vuelva a abrir este archivo.
echo Git: https://git-scm.com/download/win
echo GitHub CLI: https://cli.github.com/
pause
exit /b 1
:failed
echo No se pudo preparar GitHub. Revise el mensaje anterior.
pause
exit /b 1
