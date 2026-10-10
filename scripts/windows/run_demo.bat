@echo off
REM run_demo.bat [full|cosign_only|false_only] - same docker command the author ran successfully on Windows,
REM but mounting the repo root (which holds mission-shell\ and microkit-sdk-2.3.1\ side by side) as /work.
setlocal
call "%~dp0_env.bat" || exit /b 1
set "PROFILE=%~1"
if "%PROFILE%"=="" set "PROFILE=full"
if not exist "%ROOT%\microkit-sdk-2.3.1\board\qemu_virt_aarch64" (
  echo ERROR: SDK missing. Run scripts\windows\setup_sdk.bat first.
  exit /b 1
)
if not exist "%ROOT%\mission-shell\build_logs" mkdir "%ROOT%\mission-shell\build_logs"
set "LOG=%ROOT%\mission-shell\build_logs\demo_%PROFILE%.log"
docker run --rm -e DEMO_PROFILE=%PROFILE% -v "%WORK%":/work -w /work/mission-shell %IMG% bash /work/mission-shell/docker_build_run.sh > "%LOG%" 2>&1
type "%LOG%"
if /i "%PROFILE%"=="full" docker run --rm -v "%WORK%":/work -w /work %IMG% python3 scripts/check_demo_log.py mission-shell/build_logs/demo_full.log
endlocal
