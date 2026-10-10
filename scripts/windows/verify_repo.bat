@echo off
REM verify_repo.bat - repository hygiene checks, run inside the image via bash.
setlocal
call "%~dp0_env.bat" || exit /b 1
docker run --rm -v "%WORK%":/work -w /work %IMG% bash scripts/verify_repo.sh
endlocal
