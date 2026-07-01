@echo off
setlocal

net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

sc query com.docker.service >nul 2>&1
if errorlevel 1 (
  echo com.docker.service was not found. Install Docker Desktop first.
  pause
  exit /b 1
)

sc config com.docker.service start= auto
sc start com.docker.service >nul 2>&1

set "DOCKER_EXE=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
if not exist "%DOCKER_EXE%" (
  echo Docker Desktop was not found at "%DOCKER_EXE%".
  pause
  exit /b 1
)

schtasks /Create /TN "Start Docker Desktop" /SC ONLOGON /RL HIGHEST /TR "\"%DOCKER_EXE%\"" /F

cd /d "%~dp0.."
start "" "%DOCKER_EXE%"

where docker >nul 2>&1
if errorlevel 1 (
  echo Docker was not found in PATH. Restart Windows and run this .bat again.
  pause
  exit /b 1
)

echo Waiting for Docker Engine...
for /l %%I in (1,1,60) do (
  docker info >nul 2>&1 && goto docker_ready
  timeout /t 2 /nobreak >nul
)

echo Docker Engine did not start in time. Open Docker Desktop and run this .bat again.
pause
exit /b 1

:docker_ready
docker compose up -d
if errorlevel 1 (
  pause
  exit /b 1
)

echo.
echo Done. Docker Desktop will start with Windows and barberia_postgres will start with Docker.
pause
