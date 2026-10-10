#!/usr/bin/env bash
# scripts/analyze.sh [RUNS_NAME] —— 解析 experiment/runs/<RUNS_NAME> 并生成 experiment/reports/<RUNS_NAME>/report.md
# 只需 python3（标准库）；不需要 Docker 或 QEMU。
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
NAME="${1:-local}"
LABEL="${ENV_LABEL:-runs/$NAME on $(uname -s) $(uname -m)}"
cd "$SHELL_DIR"
python3 experiment/analysis/analyze.py --runs-dir "experiment/runs/$NAME" --out-dir "experiment/reports/$NAME" --env-label "$LABEL"
echo "报告：mission-shell/experiment/reports/$NAME/report.md（与 experiment/reports/box-qemu/report.md 对照）"
