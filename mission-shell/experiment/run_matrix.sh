#!/usr/bin/env bash
# run_matrix.sh —— 按实验方案 §5.4 运行矩阵批量调用 ../docker_corpus_run.sh，日志落盘到 $RUNS_DIR。
#
# 可在 Docker 容器内一次跑完（Windows 用户只需一条 docker run），也可在装有交叉编译器与
# qemu-system-aarch64 的 Linux 主机上直接运行。
#
# 环境变量：
#   RUNS_DIR   默认 experiment/runs/local
#   REPS       每个 (条件, 种子) 的重复次数，默认 3（只用于确认确定性，不增加统计样本）
#   SEEDS      默认 "20261007 20261008 20261009 20261010 20261011"
#   QEMU_TIMEOUT 默认 120
#   SKIP_ABLATIONS=1 / SKIP_HOLDOUT=1 / SKIP_LEGACY=1  可跳过相应部分
#
# 输出布局：$RUNS_DIR/<condition>/<corpus>/r<k>.log ，corpus = 种子号或 holdout_draft；
#           $RUNS_DIR/legacy_full/r1.log（full 剖面回归）。
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
RUNS_DIR="${RUNS_DIR:-$HERE/runs/local}"
REPS="${REPS:-3}"
SEEDS="${SEEDS:-20261007 20261008 20261009 20261010 20261011}"
FIRST_SEED="${SEEDS%% *}"
export QEMU_TIMEOUT="${QEMU_TIMEOUT:-120}"
mkdir -p "$RUNS_DIR"

one() { # $1=condition-dir $2=corpus-dir $3=rep ; 其余环境变量由调用方 export
  local d="$RUNS_DIR/$1/$2"; mkdir -p "$d"
  echo "[run_matrix] $1 / $2 / r$3" >&2
  bash "$ROOT/docker_corpus_run.sh" > "$d/r$3.log" 2> "$d/build_r$3.txt" || echo "[run_matrix] FAILED $1/$2/r$3" >&2
}

# 主矩阵：B、M × 5 种子 × REPS
for S in $SEEDS; do
  for R in $(seq 1 "$REPS"); do
    DEMO_PROFILE=baseline_corpus CORPUS_SET=seed CORPUS_SEED=$S ABLATE= one B "$S" "$R"
    DEMO_PROFILE=mission_corpus  CORPUS_SET=seed CORPUS_SEED=$S ABLATE= one M "$S" "$R"
  done
done
export DEMO_PROFILE CORPUS_SET CORPUS_SEED ABLATE
# 次要条件：B+ 与消融 × 首个种子 × 1
if [ "${SKIP_ABLATIONS:-0}" != "1" ]; then
  DEMO_PROFILE=baselineplus_corpus CORPUS_SET=seed CORPUS_SEED=$FIRST_SEED ABLATE= one Bplus "$FIRST_SEED" 1
  for A in cosign align prov U; do
    DEMO_PROFILE=mission_corpus CORPUS_SET=seed CORPUS_SEED=$FIRST_SEED ABLATE=$A one "M-$A" "$FIRST_SEED" 1
  done
fi
# 草稿留出语料（不计入确证性结论）：B、M、B+
if [ "${SKIP_HOLDOUT:-0}" != "1" ]; then
  for R in $(seq 1 "$REPS"); do
    DEMO_PROFILE=baseline_corpus CORPUS_SET=holdout_draft ABLATE= one B holdout_draft "$R"
    DEMO_PROFILE=mission_corpus  CORPUS_SET=holdout_draft ABLATE= one M holdout_draft "$R"
  done
  DEMO_PROFILE=baselineplus_corpus CORPUS_SET=holdout_draft ABLATE= one Bplus holdout_draft 1
fi
# 回归门禁：原 full 剖面
if [ "${SKIP_LEGACY:-0}" != "1" ]; then
  mkdir -p "$RUNS_DIR/legacy_full"
  DEMO_PROFILE=full CORPUS_SET= ABLATE= bash "$ROOT/docker_corpus_run.sh" > "$RUNS_DIR/legacy_full/r1.log" 2> "$RUNS_DIR/legacy_full/build_r1.txt"
fi
echo "[run_matrix] done -> $RUNS_DIR" >&2
