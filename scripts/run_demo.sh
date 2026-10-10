#!/usr/bin/env bash
# scripts/run_demo.sh [full|cosign_only|false_only] —— 构建并运行 S1 演示，日志写入 mission-shell/build_logs/demo_<profile>.log
# MODE=docker（默认在 docker 可用时）等价于作者在 Windows 上成功运行过的命令：
#   docker run --rm -e DEMO_PROFILE=full -v <仓库根>:/work -w /work/mission-shell trustworthysystems/sel4:latest \
#     bash /work/mission-shell/docker_build_run.sh
# MODE=native：在装有 aarch64 交叉编译器与 qemu-system-aarch64 的 Linux 上直接运行同一脚本。
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
PROFILE="${1:-full}"
require_sdk
M="$(pick_mode)"
mkdir -p "$SHELL_DIR/build_logs"
LOG="$SHELL_DIR/build_logs/demo_${PROFILE}.log"
echo "[run_demo] mode=$M profile=$PROFILE log=$LOG" >&2
if [ "$M" = docker ]; then
  docker run --rm -e DEMO_PROFILE="$PROFILE" -v "$REPO_ROOT":/work -w /work/mission-shell "$IMAGE" \
    bash /work/mission-shell/docker_build_run.sh 2>&1 | tr -d '\r' | tee "$LOG"
else
  DEMO_PROFILE="$PROFILE" MISSION_SHELL_DIR="$SHELL_DIR" MISSION_MICROKIT_SDK="$SDK_DIR" \
    MISSION_BUILD_DIR="$SHELL_DIR/build" bash "$SHELL_DIR/docker_build_run.sh" 2>&1 | tr -d '\r' | tee "$LOG"
fi
if [ "$PROFILE" = full ]; then
  python3 "$REPO_ROOT/scripts/check_demo_log.py" "$LOG"
fi
