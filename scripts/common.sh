#!/usr/bin/env bash
# scripts/common.sh —— 被其他脚本 source；定位仓库根并给出公共设置。不单独运行。
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHELL_DIR="$REPO_ROOT/mission-shell"
EXP_DIR="$SHELL_DIR/experiment"
SDK_VERSION="2.3.1"
SDK_DIR="$REPO_ROOT/microkit-sdk-$SDK_VERSION"
IMAGE="${MISSION_IMAGE:-trustworthysystems/sel4:latest}"
export PYTHONDONTWRITEBYTECODE=1

# 运行模式：MODE=docker | native | auto（默认 auto：有可用 docker 用 docker，否则本机工具链）
pick_mode() {
  local m="${MODE:-auto}"
  if [ "$m" = "auto" ]; then
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then m=docker
    elif command -v qemu-system-aarch64 >/dev/null 2>&1 && \
         { command -v aarch64-linux-gnu-gcc >/dev/null 2>&1 || command -v aarch64-none-elf-gcc >/dev/null 2>&1; }; then m=native
    else
      echo "ERROR: 既没有可用的 Docker，也没有本机 aarch64 交叉编译器 + qemu-system-aarch64。" >&2
      echo "       请启动 Docker Desktop，或安装工具链后以 MODE=native 运行。" >&2
      return 1
    fi
  fi
  echo "$m"
}

require_sdk() {
  if [ ! -d "$SDK_DIR/board/qemu_virt_aarch64" ]; then
    echo "ERROR: 未找到 Microkit SDK：$SDK_DIR" >&2
    echo "       请先运行：bash scripts/setup_sdk.sh" >&2
    return 1
  fi
}
