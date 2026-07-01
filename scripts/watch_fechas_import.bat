@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0watch_fechas_import.ps1"
pause
