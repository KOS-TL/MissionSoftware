@echo off
REM run_experiment.bat [full|quick] - controlled-experiment matrix in Docker (replaces the old experiment\windows\run_all_docker.bat paths).
REM full: B,M x 5 seeds x 3 + B+ + 4 ablations + draft holdout + full regression; quick: seed 20261007 only, 1 rep, no holdout/regression.
setlocal
call "%~dp0_env.bat" || exit /b 1
set "SUBSET=%~1"
if "%SUBSET%"=="" set "SUBSET=full"
set "EXTRA="
if /i "%SUBSET%"=="quick" set "EXTRA=-e SEEDS=20261007 -e REPS=1 -e SKIP_HOLDOUT=1 -e SKIP_LEGACY=1"
if "%RUNS_NAME%"=="" set "RUNS_NAME=docker"
set DIGEST=unknown
for /f "delims=" %%i in ('docker inspect --format "{{index .RepoDigests 0}}" %IMG%') do set DIGEST=%%i
echo image digest: %DIGEST%
docker run --rm -e IMAGE_DIGEST=%DIGEST% -e RUNS_DIR=/work/mission-shell/experiment/runs/%RUNS_NAME% -e QEMU_TIMEOUT=120 %EXTRA% -v "%WORK%":/work -w /work/mission-shell %IMG% bash /work/mission-shell/experiment/run_matrix.sh
if errorlevel 1 exit /b 1
echo Next: scripts\windows\analyze.bat %RUNS_NAME%
endlocal
