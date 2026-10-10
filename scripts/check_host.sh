#!/usr/bin/env bash
# scripts/check_host.sh —— 只需 python3 + gcc 的主机检查（不需要 Docker / QEMU / 交叉编译器 / SDK）：
#   1) 语料确定性：gen_corpus.py --check（重新生成并与冻结的 SHA256SUMS 比对）
#   2) 门闩单元测试：tests/run_unit_tests.py（28 例 × 3 条件，经 hostsim 编译运行）
#   3) 主机模拟 hostsim：18 组（条件, 语料）日志写入 experiment/runs/hostsim-check/，并与仓库内参考日志 runs/hostsim/ 逐字节比较
# 【主机模拟、非 QEMU 实测】
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
cd "$SHELL_DIR"
fail=0
echo "== 1/3 gen_corpus.py --check"
python3 experiment/corpus/gen_corpus.py --check || fail=1
echo "== 2/3 run_unit_tests.py"
python3 experiment/tests/run_unit_tests.py || fail=1
echo "== 3/3 hostsim"
OUT="$EXP_DIR/runs/hostsim-check"
rm -rf "$OUT"
RUNS_DIR="$OUT" bash experiment/hostsim/run_hostsim.sh 2>/dev/null || fail=1
n=0; bad=0
while IFS= read -r ref; do
  rel="${ref#"$EXP_DIR/runs/hostsim/"}"
  n=$((n+1))
  if ! cmp -s "$ref" "$OUT/$rel"; then echo "DIFF: $rel"; bad=$((bad+1)); fi
done < <(find "$EXP_DIR/runs/hostsim" -name 'r1.log' | sort)
echo "hostsim: $((n-bad))/$n 份日志与参考逐字节一致"
[ "$bad" = 0 ] && [ "$n" -gt 0 ] || fail=1
if [ "$fail" = 0 ]; then echo "CHECK_HOST: PASS"; else echo "CHECK_HOST: FAIL"; exit 1; fi
