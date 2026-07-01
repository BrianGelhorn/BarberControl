@echo off
setlocal

net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

where winget >nul 2>&1
if errorlevel 1 (
  echo winget no esta instalado. Instala "App Installer" desde Microsoft Store y vuelve a ejecutar este .bat.
  pause
  exit /b 1
)

winget source update

winget install --id Docker.DockerDesktop --exact --accept-package-agreements --accept-source-agreements
winget install --id Python.Python.3.12 --exact --accept-package-agreements --accept-source-agreements
winget install --id PostgreSQL.PostgreSQL.17 --exact --accept-package-agreements --accept-source-agreements --override "--mode unattended --superpassword postgres"
winget install --id PostgreSQL.psqlODBC --exact --accept-package-agreements --accept-source-agreements

echo.
echo Instalacion terminada.
echo PostgreSQL queda instalado con usuario postgres y password postgres.
pause
