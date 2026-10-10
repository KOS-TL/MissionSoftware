@echo off
REM analyze.bat [RUNS_NAME] - run analyze.py inside the image (no local Python needed).
setlocal
call "%~dp0_env.bat" || exit /b 1
set "NAME=%~1"
if "%NAME%"=="" set "NAME=docker"
set DIGEST=unknown
for /f "delims=" %%i in ('docker inspect --format "{{index .RepoDigests 0}}" %IMG%') do set DIGEST=%%i
docker run --rm -v "%WORK%":/work -w /work/mission-shell %IMG% python3 experiment/analysis/analyze.py --runs-dir experiment/runs/%NAME% --out-dir experiment/reports/%NAME% --env-label "Docker %DIGEST% + QEMU (Windows host)"
echo report: mission-shell\experiment\reports\%NAME%\report.md
endlocal
