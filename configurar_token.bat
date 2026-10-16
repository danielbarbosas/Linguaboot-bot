@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "configurar_token.ps1"
echo.
pause
