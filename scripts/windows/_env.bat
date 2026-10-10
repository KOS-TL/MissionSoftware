@echo off
REM _env.bat - called by the other .bat files; sets ROOT (repo root, backslashes) and WORK (forward slashes for docker -v).
REM ASCII-only on purpose (cmd.exe code page).
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
set "WORK=%ROOT:\=/%"
if "%MISSION_IMAGE%"=="" (set "IMG=trustworthysystems/sel4:latest") else (set "IMG=%MISSION_IMAGE%")
docker info >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker is not running. Start Docker Desktop and wait until it reports "Engine running".
  exit /b 1
)
exit /b 0
