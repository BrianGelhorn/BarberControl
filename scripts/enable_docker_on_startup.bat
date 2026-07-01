@echo off
setlocal

net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

sc query com.docker.service >nul 2>&1
if errorlevel 1 (
  echo No encuentro com.docker.service. Instala Docker Desktop primero.
  pause
  exit /b 1
)

sc config com.docker.service start= auto
sc start com.docker.service >nul 2>&1

set "DOCKER_EXE=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
if not exist "%DOCKER_EXE%" (
  echo No encuentro Docker Desktop en "%DOCKER_EXE%".
  pause
  exit /b 1
)

schtasks /Create /TN "Start Docker Desktop" /SC ONLOGON /RL HIGHEST /TR "\"%DOCKER_EXE%\"" /F

cd /d "%~dp0.."
start "" "%DOCKER_EXE%"

where docker >nul 2>&1
if errorlevel 1 (
  echo No encuentro Docker en PATH. Reinicia Windows y vuelve a ejecutar este .bat.
  pause
  exit /b 1
)

echo Esperando Docker Engine...
for /l %%I in (1,1,60) do (
  docker info >nul 2>&1 && goto docker_ready
  timeout /t 2 /nobreak >nul
)

echo Docker Engine no levanto a tiempo. Abre Docker Desktop y ejecuta este .bat otra vez.
pause
exit /b 1

:docker_ready
docker compose up -d
if errorlevel 1 (
  pause
  exit /b 1
)

echo.
echo Finalizado. Docker Desktop se iniciara con Windows y barberia_postgres se levantara con Docker.
pause
