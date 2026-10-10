#!/usr/bin/env bash
set -euo pipefail
# 仓库化改动（v0.1.0）：以下三处路径可由环境变量覆盖；默认值与原脚本完全相同，
# 因此在容器内以 -v <仓库根>:/work -w /work/mission-shell 运行时行为不变。
#   MISSION_SHELL_DIR    默认 /work/mission-shell
#   MISSION_MICROKIT_SDK 默认 /work/microkit-sdk-2.3.1
#   MISSION_BUILD_DIR    默认 /work/mission-shell/build
cd "${MISSION_SHELL_DIR:-/work/mission-shell}"
SDK="${MISSION_MICROKIT_SDK:-/work/microkit-sdk-2.3.1}"
BOARD=qemu_virt_aarch64
CONFIG=debug
BUILD="${MISSION_BUILD_DIR:-/work/mission-shell/build}"
PROFILE="${DEMO_PROFILE:-full}"
echo "DEMO_PROFILE=$PROFILE"
test -d "$SDK/board/$BOARD"
rm -rf "$BUILD"; mkdir -p "$BUILD"
make BUILD_DIR="$BUILD" MICROKIT_SDK="$SDK" MICROKIT_BOARD="$BOARD" MICROKIT_CONFIG="$CONFIG" \
  CROSS_PREFIX=aarch64-linux-gnu DEMO_PROFILE="$PROFILE"
ls -la "$BUILD"
echo "=== QEMU ==="
set +e
timeout 30s qemu-system-aarch64 \
  -machine virt,virtualization=on \
  -cpu cortex-a53 \
  -nographic \
  -serial mon:stdio \
  -device loader,file="$BUILD/loader.img",addr=0x70000000,cpu-num=0 \
  -m size=2G
echo "=== QEMU done rc=$? ==="
exit 0
