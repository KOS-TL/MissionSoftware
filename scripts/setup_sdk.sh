#!/usr/bin/env bash
# scripts/setup_sdk.sh —— 下载并校验官方 Microkit SDK 2.3.1，解压到 <仓库根>/microkit-sdk-2.3.1（已被 .gitignore 忽略）。
# 用法：bash scripts/setup_sdk.sh            # 默认 linux-x86-64（Docker 镜像内使用的就是这一版）
#       SDK_PLATFORM=linux-aarch64 SDK_SHA256=<hash> bash scripts/setup_sdk.sh
# 来源：https://github.com/seL4/microkit/releases/tag/2.3.1 （第三方发布物，不随本仓库再分发）
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
PLAT="${SDK_PLATFORM:-linux-x86-64}"
TARBALL="microkit-sdk-$SDK_VERSION-$PLAT.tar.gz"
URL="https://github.com/seL4/microkit/releases/download/$SDK_VERSION/$TARBALL"
# 已核实的哈希（2026-10-10 在构建机上下载核对；解压内容与作者实验所用 SDK 逐文件一致）
PINNED_linux_x86_64="b1b285b8785db7557eba6d0665dd4fbf2f265ea5c0b39d6f91ae3dcc43d2c424"
want="${SDK_SHA256:-}"
if [ -z "$want" ] && [ "$PLAT" = "linux-x86-64" ]; then want="$PINNED_linux_x86_64"; fi

if [ -f "$SDK_DIR/VERSION" ] && [ "$(cat "$SDK_DIR/VERSION")" = "$SDK_VERSION" ] && [ -d "$SDK_DIR/board/qemu_virt_aarch64" ]; then
  echo "SDK 已存在：$SDK_DIR（VERSION=$SDK_VERSION），跳过下载。如需重装请先删除该目录。"
  exit 0
fi
CACHE="$REPO_ROOT/.cache"; mkdir -p "$CACHE"
if [ ! -f "$CACHE/$TARBALL" ]; then
  echo "下载 $URL"
  if command -v curl >/dev/null 2>&1; then curl -fL --retry 3 -o "$CACHE/$TARBALL.part" "$URL"
  else wget -O "$CACHE/$TARBALL.part" "$URL"; fi
  mv "$CACHE/$TARBALL.part" "$CACHE/$TARBALL"
fi
if command -v sha256sum >/dev/null 2>&1; then got="$(sha256sum "$CACHE/$TARBALL" | cut -d' ' -f1)"
else got="$(shasum -a 256 "$CACHE/$TARBALL" | cut -d' ' -f1)"; fi
echo "SHA-256：$got"
if [ -n "$want" ]; then
  [ "$got" = "$want" ] || { echo "ERROR: SHA-256 不符（期望 $want）。已保留文件 $CACHE/$TARBALL 供检查。" >&2; exit 1; }
  echo "SHA-256 校验通过。"
else
  echo "WARNING: 平台 $PLAT 没有预置哈希；请自行核对上面的 SHA-256（可设置 SDK_SHA256 强制校验）。"
fi
tar xzf "$CACHE/$TARBALL" -C "$REPO_ROOT"
test -d "$SDK_DIR/board/qemu_virt_aarch64" && echo "SDK 就绪：$SDK_DIR"
