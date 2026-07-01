@echo off
setlocal

net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

set "POSTGRES_USER=barberia"
set "POSTGRES_PASSWORD=barberia_local"
set "POSTGRES_HOST=localhost"
set "POSTGRES_PORT=5433"
set "POSTGRES_PROD_DB=barberia_prod"
set "POSTGRES_DB="
set "DSN_NAME=BarberiaPostgres"

if exist "%~dp0..\.env" (
  for /f "usebackq tokens=1,* delims==" %%A in ("%~dp0..\.env") do (
    if /i "%%A"=="POSTGRES_USER" set "POSTGRES_USER=%%B"
    if /i "%%A"=="POSTGRES_PASSWORD" set "POSTGRES_PASSWORD=%%B"
    if /i "%%A"=="POSTGRES_HOST" set "POSTGRES_HOST=%%B"
    if /i "%%A"=="POSTGRES_PORT" set "POSTGRES_PORT=%%B"
    if /i "%%A"=="POSTGRES_PROD_DB" set "POSTGRES_PROD_DB=%%B"
    if /i "%%A"=="POSTGRES_DB" set "POSTGRES_DB=%%B"
  )
)

set "ODBC_DB=%POSTGRES_PROD_DB%"
if defined POSTGRES_DB set "ODBC_DB=%POSTGRES_DB%"

set "ATTRS=DSN=%DSN_NAME%|SERVER=%POSTGRES_HOST%|PORT=%POSTGRES_PORT%|DATABASE=%ODBC_DB%|UID=%POSTGRES_USER%|PWD=%POSTGRES_PASSWORD%|SSLmode=disable"

"%SystemRoot%\System32\odbcconf.exe" /A {CONFIGSYSDSN "PostgreSQL Unicode(x64)" "%ATTRS%"}
if errorlevel 1 (
  "%SystemRoot%\System32\odbcconf.exe" /A {CONFIGSYSDSN "PostgreSQL Unicode" "%ATTRS%"}
)
if errorlevel 1 (
  echo No pude crear el DSN. Instala el driver ODBC de PostgreSQL y vuelve a ejecutar este .bat.
  pause
  exit /b 1
)

echo.
echo DSN ODBC creado: %DSN_NAME%
echo Host: %POSTGRES_HOST%
echo Puerto: %POSTGRES_PORT%
echo Base: %ODBC_DB%
echo Usuario: %POSTGRES_USER%
pause
