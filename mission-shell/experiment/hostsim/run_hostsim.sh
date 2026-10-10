#!/usr/bin/env bash
# run_hostsim.sh —— 主机模拟运行（gcc 本机编译；不需要交叉编译器、SDK 或 QEMU）。
# 【主机模拟、非 QEMU 实测】输出布局与 run_matrix.sh 相同：$RUNS_DIR/<condition>/<corpus>/r1.log
# 用途：(1) 无 Docker/QEMU 时打通"判决逻辑 → 日志 → 解析 → 分析"；(2) 与 QEMU 日志逐字节对照门闩输出。
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXP="$(cd "$HERE/.." && pwd)"
RUNS_DIR="${RUNS_DIR:-$EXP/runs/hostsim}"
SEEDS="${SEEDS:-20261007 20261008 20261009 20261010 20261011}"
CC="${HOST_CC:-gcc}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CF="-O2 -Wall -Werror -Wno-unused-function -I$HERE -I$EXP"

run_one() { # $1=cond $2=defs $3=corpus-name $4=corpus-header
  local out="$RUNS_DIR/$1/$3"; mkdir -p "$out" "$TMP/$1_$3"
  cp "$4" "$TMP/$1_$3/corpus_active.h"
  $CC $CF $2 -Dinit=gk_init -Dnotified=gk_notified -Dprotected=gk_protected -c "$EXP/gatekeeper_field.c" -o "$TMP/$1_$3/g.o"
  $CC $CF -I"$TMP/$1_$3" -Dinit=client_init -Dnotified=client_notified -c "$EXP/client_corpus.c" -o "$TMP/$1_$3/c.o"
  $CC $CF -c "$HERE/hostsim.c" -o "$TMP/$1_$3/h.o"
  $CC "$TMP/$1_$3/g.o" "$TMP/$1_$3/c.o" "$TMP/$1_$3/h.o" -o "$TMP/$1_$3/sim"
  { echo "RUN|profile=hostsim|condition=$1|corpus=$3|env=hostsim_NOT_QEMU (host simulation, not QEMU measurement)"
    "$TMP/$1_$3/sim"
    echo "RUN|END|status=done|elapsed_s=0"; } > "$out/r1.log"
  echo "[hostsim] $1 / $3 -> $out/r1.log" >&2
}

for S in $SEEDS; do
  H="$EXP/corpus/out/corpus_$S.h"
  run_one B "-DGATE_VARIANT_B" "$S" "$H"
  run_one M "-DGATE_VARIANT_M" "$S" "$H"
done
FIRST="${SEEDS%% *}"
H="$EXP/corpus/out/corpus_$FIRST.h"
run_one Bplus "-DGATE_VARIANT_BPLUS" "$FIRST" "$H"
for A in cosign align prov U; do
  run_one "M-$A" "-DGATE_VARIANT_M -DABLATE_$(echo $A | tr a-z A-Z)" "$FIRST" "$H"
done
H="$EXP/corpus/out/holdout_draft.h"
run_one B "-DGATE_VARIANT_B" holdout_draft "$H"
run_one M "-DGATE_VARIANT_M" holdout_draft "$H"
run_one Bplus "-DGATE_VARIANT_BPLUS" holdout_draft "$H"
