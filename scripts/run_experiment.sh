#!/usr/bin/env bash
# scripts/run_experiment.sh [full|quick] —— 运行对照实验矩阵（mission-shell/experiment/run_matrix.sh）。
#   full （默认）：B、M × 5 种子 × 3 次 + B+ + 4 个消融 + 草稿留出语料（B/B+/M）+ full 回归（分析器计 42 份矩阵日志，另加 1 份 legacy_full 回归日志）
#   quick：只跑首个种子 20261007、每条件 1 次，并跳过留出语料与 full 回归（约为完整矩阵的 1/4 时间；仅作冒烟）
# 输出：mission-shell/experiment/runs/<RUNS_NAME>/（默认 RUNS_NAME=local；docker 模式默认 docker）
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
SUBSET="${1:-full}"
require_sdk
M="$(pick_mode)"
RUNS_NAME="${RUNS_NAME:-$([ "$M" = docker ] && echo docker || echo local)}"
ENVS=(-e QEMU_TIMEOUT="${QEMU_TIMEOUT:-120}")
case "$SUBSET" in
  full) ;;
  quick) ENVS+=(-e SEEDS=20261007 -e REPS=1 -e SKIP_HOLDOUT=1 -e SKIP_LEGACY=1) ;;
  *) echo "用法：$0 [full|quick]" >&2; exit 2 ;;
esac
echo "[run_experiment] mode=$M subset=$SUBSET runs=experiment/runs/$RUNS_NAME" >&2
if [ "$M" = docker ]; then
  DIGEST="$(docker inspect --format '{{index .RepoDigests 0}}' "$IMAGE" 2>/dev/null || echo unknown)"
  docker run --rm -e IMAGE_DIGEST="$DIGEST" -e RUNS_DIR=/work/mission-shell/experiment/runs/"$RUNS_NAME" "${ENVS[@]}" \
    -v "$REPO_ROOT":/work -w /work/mission-shell "$IMAGE" bash /work/mission-shell/experiment/run_matrix.sh
else
  env_args=()
  for kv in "${ENVS[@]}"; do [ "$kv" = "-e" ] || env_args+=("$kv"); done
  env "${env_args[@]}" RUNS_DIR="$EXP_DIR/runs/$RUNS_NAME" bash "$EXP_DIR/run_matrix.sh"
fi
echo "[run_experiment] 完成。下一步：bash scripts/analyze.sh $RUNS_NAME" >&2
