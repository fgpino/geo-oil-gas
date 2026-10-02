@echo off
rem Publica los cambios locales con las mismas verificaciones que la primera carga.
call "%~dp004_PUBLICAR_GITHUB.bat"
exit /b %errorlevel%
