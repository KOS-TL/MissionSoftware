#!/usr/bin/env bash
# docker_corpus_run.sh —— 实验剖面：构建 + QEMU 运行 + 串口日志输出到 stdout（实验方案 §5.3）
#
# 与 docker_build_run.sh 的差异（后者保持不动）：
#   (1) 校验语料头/JSON 的 SHA-256 与 experiment/corpus/out/SHA256SUMS（冻结清单）一致，不一致即退出；
#       若容器内有 python3，再用生成器重新生成并比对（--check）。
#   (2) QEMU 超时可配置（QEMU_TIMEOUT，默认 120 秒）；见到 CORPUS_DONE 即提前结束。
#   (3) 日志头写入 RUN|profile|seed|image_digest|git_rev|corpus_sha256。
#   (4) 未见 CORPUS_DONE 则在日志尾写 RUN|END|status=INVALID（解析器判为 INVALID，不计为 DENY）。
#
# 环境变量：
#   DEMO_PROFILE   baseline_corpus | mission_corpus | baselineplus_corpus（也接受原三剖面，但不做语料校验）
#   CORPUS_SET     seed（默认）| holdout_draft（草稿留出语料，不计入确证性结论）
#   CORPUS_SEED    默认 20261007
#   ABLATE         空 | cosign | align | prov | U（仅 mission_corpus）
#   CORPUS_SHARD   空 | k/K（分片，例如 0/2）
#   QEMU_TIMEOUT   默认 120（秒）
#   MICROKIT_SDK   默认依次尝试 ../microkit-sdk-2.3.1、./microkit-sdk-2.3.1
#   IMAGE_DIGEST   可选：由宿主传入的镜像 digest（容器内无法自行获取）
#   BUILD_ROOT     默认 ./build_exp
#
# 非临床 · 仅仿真 · 无写使能 · 交付 != 达成。
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

PROFILE="${DEMO_PROFILE:-mission_corpus}"
CSET="${CORPUS_SET:-seed}"
SEED="${CORPUS_SEED:-20261007}"
ABL="${ABLATE:-}"
SHARD="${CORPUS_SHARD:-}"
TMO="${QEMU_TIMEOUT:-120}"
BOARD=qemu_virt_aarch64
CONFIG=debug
if [ -n "${MICROKIT_SDK:-}" ]; then SDK="$MICROKIT_SDK"
elif [ -d "$HERE/../microkit-sdk-2.3.1/board/$BOARD" ]; then SDK="$(cd "$HERE/../microkit-sdk-2.3.1" && pwd)"
else SDK="$HERE/microkit-sdk-2.3.1"; fi
test -d "$SDK/board/$BOARD" || { echo "RUN|ERROR|sdk_not_found|$SDK" >&2; exit 1; }

if command -v aarch64-linux-gnu-gcc >/dev/null 2>&1; then CROSS=aarch64-linux-gnu
elif command -v aarch64-none-elf-gcc >/dev/null 2>&1; then CROSS=aarch64-none-elf
else echo "RUN|ERROR|no_cross_compiler" >&2; exit 1; fi

case "$PROFILE" in
  baseline_corpus) COND=B ;;
  baselineplus_corpus) COND=Bplus ;;
  mission_corpus) COND=M; [ -n "$ABL" ] && COND="M-$ABL" ;;
  *) COND="legacy" ;;
esac
TAG="${PROFILE}${ABL:+_$ABL}_${CSET}${SHARD:+_shard${SHARD%%/*}of${SHARD##*/}}"
[ "$CSET" = "seed" ] && TAG="${TAG}_${SEED}"
BUILD="${BUILD_ROOT:-$HERE/build_exp}/$TAG"

# ---- (1) 语料冻结校验 ----
CORPUS_SHA="n/a"
if [ "$COND" != "legacy" ]; then
  OUT=experiment/corpus/out
  if [ "$CSET" = "seed" ]; then BASE="corpus_${SEED}"; else BASE="holdout_draft"; fi
  for f in "$BASE.json" "$BASE.h"; do
    want="$(awk -v n="$f" '$2==n{print $1}' "$OUT/SHA256SUMS")"
    got="$(sha256sum "$OUT/$f" | cut -d' ' -f1)"
    if [ -z "$want" ] || [ "$want" != "$got" ]; then
      echo "RUN|ERROR|corpus_hash_mismatch|file=$f|frozen=${want:-none}|actual=$got"; exit 1
    fi
  done
  CORPUS_SHA="$(sha256sum "$OUT/$BASE.json" | cut -d' ' -f1)"
  if command -v python3 >/dev/null 2>&1 && [ "$CSET" = "seed" ]; then
    python3 experiment/corpus/gen_corpus.py --check >/dev/null || { echo "RUN|ERROR|generator_check_failed"; exit 1; }
    REGEN=verified
  else
    REGEN=skipped
  fi
fi

GIT_REV="$(git -C "$HERE" rev-parse --short HEAD 2>/dev/null || echo nogit)"
HDR_SET="$CSET"; HDR_SEED="$SEED"
[ "$COND" = "legacy" ] && { HDR_SET="n/a"; HDR_SEED="n/a"; }
[ "$CSET" = "holdout_draft" ] && HDR_SEED="n/a"
echo "RUN|profile=$PROFILE|condition=$COND|corpus_set=$HDR_SET|seed=$HDR_SEED|ablate=${ABL:-none}|shard=${SHARD:-all}|image=${IMAGE_DIGEST:-unknown}|git=$GIT_REV|corpus_sha256=$CORPUS_SHA|regen=${REGEN:-n/a}|qemu_timeout=$TMO"

# ---- 构建（输出到 stderr，避免污染串口日志） ----
rm -rf "$BUILD"; mkdir -p "$BUILD"
make -C "$HERE" BUILD_DIR="$BUILD" MICROKIT_SDK="$SDK" MICROKIT_BOARD="$BOARD" MICROKIT_CONFIG="$CONFIG" \
  CROSS_PREFIX="$CROSS" DEMO_PROFILE="$PROFILE" CORPUS_SET="$CSET" CORPUS_SEED="$SEED" \
  ABLATE="$ABL" CORPUS_SHARD="$SHARD" 1>&2
GSZ="$("$CROSS-size" "$BUILD/gatekeeper.elf" 2>/dev/null | awk 'NR==2{print "text="$1",data="$2",bss="$3}')"
CSZ="$("$CROSS-size" "$BUILD/client.elf" 2>/dev/null | awk 'NR==2{print "text="$1",data="$2",bss="$3}')"
echo "RUN|build_ok|gatekeeper_elf=${GSZ:-?}|client_elf=${CSZ:-?}|image_sha256=$(sha256sum "$BUILD/loader.img" | cut -d' ' -f1)"

# ---- (2) QEMU：见到 CORPUS_DONE / MISSION_SHELL_DEMO_DONE 即结束 ----
QLOG="$BUILD/serial.log"
: > "$QLOG"
qemu-system-aarch64 -machine virt,virtualization=on -cpu cortex-a53 -nographic -serial mon:stdio \
  -device loader,file="$BUILD/loader.img",addr=0x70000000,cpu-num=0 -m size=2G \
  < /dev/null > "$QLOG" 2>&1 &
QPID=$!
T0=$(date +%s)
STATUS=timeout
while kill -0 "$QPID" 2>/dev/null; do
  if grep -a -q -E "CLIENT\|INFO\|(CORPUS_DONE|MISSION_SHELL_DEMO_DONE)" "$QLOG"; then STATUS=done; sleep 1; break; fi
  if [ $(( $(date +%s) - T0 )) -ge "$TMO" ]; then break; fi
  sleep 1
done
kill "$QPID" 2>/dev/null || true
wait "$QPID" 2>/dev/null || true
ELAPSED=$(( $(date +%s) - T0 ))
tr -d '\r' < "$QLOG"
if [ "$STATUS" = "done" ]; then
  echo "RUN|END|status=done|elapsed_s=$ELAPSED"
else
  echo "RUN|END|status=INVALID|reason=no_CORPUS_DONE_within_${TMO}s|elapsed_s=$ELAPSED"
fi
exit 0
