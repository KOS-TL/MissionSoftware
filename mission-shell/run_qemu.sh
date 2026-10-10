#!/usr/bin/env bash
set -euo pipefail
IMG="${1:?loader.img path}"
exec qemu-system-aarch64 \
  -machine virt,virtualization=on \
  -cpu cortex-a53 \
  -nographic \
  -serial mon:stdio \
  -device loader,file="${IMG}",addr=0x70000000,cpu-num=0 \
  -m size=2G
