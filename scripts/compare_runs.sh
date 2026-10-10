#!/usr/bin/env bash
# scripts/compare_runs.sh [RUNS_NAME] [REF_NAME] —— 把 experiment/runs/<RUNS_NAME>/ 中的日志与参考 experiment/runs/<REF_NAME>/ 逐份比较。
#   默认 RUNS_NAME=docker（若不存在则 local），REF_NAME=box-qemu。
#   比较前把与环境有关、与判决无关的字段归一化：QEMU 被 timeout 结束时打印的 pid、RUN|END 的 elapsed_s、
#   RUN| 行中的 image=（镜像 digest）与 git=（仓库版本）。其余每一行（含 CASE|、EVIDENCE|、image_sha256、corpus_sha256）必须逐字节一致。
#   另外单独统计只比较 CASE| 行时的一致数。参考中有、本次运行中没有的日志（例如 quick 子集）计为 missing，不算失败。
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
NAME="${1:-}"; REF="${2:-box-qemu}"
if [ -z "$NAME" ]; then if [ -d "$EXP_DIR/runs/docker" ]; then NAME=docker; else NAME=local; fi; fi
A="$EXP_DIR/runs/$REF"; B="$EXP_DIR/runs/$NAME"
[ -d "$B" ] || { echo "ERROR: 没有 $B；先运行 scripts/run_experiment.sh" >&2; exit 2; }
norm() { tr -d '\r' < "$1" | sed -E 's/from pid [0-9]+/from pid N/; s/elapsed_s=[0-9]+/elapsed_s=N/; s/\|image=[^|]*/|image=X/; s/\|git=[^|]*/|git=X/'; }
n=0; same=0; case_same=0; missing=0
while IFS= read -r ref; do
  rel="${ref#"$A/"}"; n=$((n+1))
  if [ ! -f "$B/$rel" ]; then missing=$((missing+1)); continue; fi
  if cmp -s <(norm "$ref") <(norm "$B/$rel"); then same=$((same+1)); else echo "DIFF    $rel"; diff <(norm "$ref") <(norm "$B/$rel") | head -6 | sed 's/^/        /'; fi
  cmp -s <(grep '^CASE|' "$ref" | tr -d '\r') <(grep '^CASE|' "$B/$rel" | tr -d '\r') && case_same=$((case_same+1))
done < <(find "$A" -name 'r*.log' | sort)
echo "compared $n logs ($REF vs $NAME): normalised-identical $same/$n; CASE|-identical $case_same/$n; missing $missing"
present=$((n-missing))
if [ "$present" -gt 0 ] && [ "$same" = "$present" ]; then
  if [ "$missing" = 0 ]; then echo "COMPARE: PASS"; else echo "COMPARE: PASS (partial: $present of $n reference logs present, e.g. after 'run_experiment quick')"; fi
  exit 0
fi
echo "COMPARE: FAIL"; exit 1
