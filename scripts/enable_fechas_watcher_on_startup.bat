@echo off
setlocal

net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

set "WATCHER=%~dp0watch_fechas_import.ps1"
set "TASK=Watch Fechas Import"

schtasks /Create /TN "%TASK%" /SC ONLOGON /RL HIGHEST /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""%WATCHER%""" /F
if errorlevel 1 (
  pause
  exit /b 1
)

schtasks /Run /TN "%TASK%"

echo.
echo Listo. El watcher de Fechas se ejecutara en segundo plano al iniciar sesion.
pause
