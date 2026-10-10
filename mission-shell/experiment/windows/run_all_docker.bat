@echo off
REM run_all_docker.bat - Mission SE controlled experiment, full matrix via Docker (Windows).
REM ASCII-only on purpose (cmd.exe code page). See experiment\README.md section 3.1 for details.
REM Non-clinical; simulation only; delivery != achievement.
setlocal
REM Repository layout (v0.1.0): WORK = repo root (contains mission-shell\ and microkit-sdk-2.3.1\), derived from this file's location.
for %%I in ("%~dp0..\..\..") do set "ROOT=%%~fI"
set "WORK=%ROOT:\=/%"
set IMG=trustworthysystems/sel4:latest
cd /d "%ROOT%\mission-shell" || exit /b 1
set DIGEST=unknown
for /f "delims=" %%i in ('docker inspect --format "{{index .RepoDigests 0}}" %IMG%') do set DIGEST=%%i
echo image digest: %DIGEST%
docker run --rm -e IMAGE_DIGEST=%DIGEST% -e RUNS_DIR=/work/mission-shell/experiment/runs/docker -e QEMU_TIMEOUT=120 -v "%WORK%":/work -w /work/mission-shell %IMG% bash /work/mission-shell/experiment/run_matrix.sh
if errorlevel 1 exit /b 1
docker run --rm -v "%WORK%":/work -w /work/mission-shell %IMG% python3 experiment/analysis/analyze.py --runs-dir experiment/runs/docker --out-dir experiment/reports/docker --env-label "Docker %DIGEST% + QEMU (Windows host)"
echo report: experiment\reports\docker\report.md
endlocal
