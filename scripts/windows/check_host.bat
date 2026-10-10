@echo off
REM check_host.bat - host-only checks (corpus --check, unit tests, hostsim) run inside the image via bash.
setlocal
call "%~dp0_env.bat" || exit /b 1
docker run --rm -v "%WORK%":/work -w /work %IMG% bash scripts/check_host.sh
endlocal
