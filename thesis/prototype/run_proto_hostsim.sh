#!/usr/bin/env bash
# 【示意性原型；主机模拟、非 QEMU 实测】把 spv_gen.py 生成的语料头文件接到实验树的门闩源码上（只读引用），
# 按 hostsim 的同一编译方式运行 B / Bplus / M / M 消融，以及若干"规则缺陷"变异体（变异只作用于临时副本）。
# 输出：out/runs/<condition>/spv_<seed>/r1.log 与 out/scored/<condition>.csv
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1  # 不在实验树内写 __pycache__
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXP="${MISSION_EXP:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../mission-shell/experiment" && pwd)}"
SEED="${SEED:-1}"
OUT="$HERE/out"; RUNS="$OUT/runs"; SC="$OUT/scored"
mkdir -p "$RUNS" "$SC"
python3 "$HERE/spv_gen.py" --seed "$SEED" --out "$OUT" >/dev/null
H="$OUT/spv_$SEED.h"; J="$OUT/spv_$SEED.json"; CORP="spv_$SEED"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
CF="-O2 -Wall -Werror -Wno-unused-function -I$EXP/hostsim -I$EXP"

run_one() { # $1=cond $2=defs $3=gatekeeper source
  local d="$TMP/$1"; mkdir -p "$d" "$RUNS/$1/$CORP"
  cp "$H" "$d/corpus_active.h"
  gcc $CF $2 -Dinit=gk_init -Dnotified=gk_notified -Dprotected=gk_protected -c "$3" -o "$d/g.o"
  gcc $CF -I"$d" -Dinit=client_init -Dnotified=client_notified -c "$EXP/client_corpus.c" -o "$d/c.o"
  gcc $CF -c "$EXP/hostsim/hostsim.c" -o "$d/h.o"
  gcc "$d/g.o" "$d/c.o" "$d/h.o" -o "$d/sim"
  { echo "RUN|profile=hostsim|condition=$1|corpus=$CORP|env=hostsim_NOT_QEMU (illustrative prototype)"
    "$d/sim"; echo "RUN|END|status=done|elapsed_s=0"; } > "$RUNS/$1/$CORP/r1.log"
  python3 "$EXP/analysis/parse_serial.py" parse --log "$RUNS/$1/$CORP/r1.log" --corpus "$J" --out "$d/res.csv" >/dev/null
  python3 "$EXP/analysis/parse_serial.py" score --results "$d/res.csv" --corpus "$J" --out "$SC/$1.csv"
}

GK="$EXP/gatekeeper_field.c"
run_one B "-DGATE_VARIANT_B" "$GK"
run_one Bplus "-DGATE_VARIANT_BPLUS" "$GK"
run_one M "-DGATE_VARIANT_M" "$GK"
for A in cosign align prov U; do
  run_one "M-$A" "-DGATE_VARIANT_M -DABLATE_$(echo $A | tr a-z A-Z)" "$GK"
done

# ---- 变异检查（拟定的最小变异算子；只改临时副本） ----
mut() { # $1=name $2=sed-expr
  local m="$TMP/mut_$1"; mkdir -p "$m/gen"
  cp "$EXP/gen/entrustments_gen.h" "$m/gen/"
  sed "$2" "$GK" > "$m/gatekeeper_field.c"
  if cmp -s "$GK" "$m/gatekeeper_field.c"; then echo "MUTANT $1 NOT APPLIED" >&2; exit 1; fi
  run_one "mut-$1" "-DGATE_VARIANT_M" "$m/gatekeeper_field.c"
}
mut t_end_open      's/if (logical_now > e->t_end) {/if (logical_now >= e->t_end) {/'
mut t_start_open    's/if (logical_now < e->t_start) {/if (logical_now <= e->t_start) {/'
mut level_ge        's/if (q->level > e->sim_level_max) {/if (q->level >= e->sim_level_max) {/'
mut no_forbidden    's/if (e->forbidden_zones \& BIT(q->zone)) {/if (0) {/'
mut no_superseded   's/if (e->superseded) {/if (0) {/'
mut no_binding      's/if (!is_bound((uint32_t)q->ent_id, (uint32_t)q->ent_ver)) {/if (0) {/'
mut no_origin       's/if (enable_class \&\& q->origin != ROLE_OPERATOR) {/if (0) {/'
mut enable_u_skip   's/if (q->action == ACT_ENABLE_SIM \&\& q->u_decl == 0) {/if (0) {/'
mut action_scope    's/if (q->action != ACT_CLAIM_ACHIEVE \&\& !(e->allowed_actions \& BIT(q->action))) {/if (0) {/'
python3 "$HERE/summarize.py" "$SC" "$J" > "$OUT/summary.txt"
cat "$OUT/summary.txt"
