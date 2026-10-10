# 实现说明与构建指南

> **仓库化说明（v0.1.0）**：本文为项目过程中的历史文档，按原文收录，仅做去个人化处理：作者本机路径已替换为 `<REPO_ROOT>`（= 本仓库克隆目录，内含 `mission-shell/` 与 `microkit-sdk-2.3.1/`）、`<WORKDIR>`（作者文档目录）或仓库内相对路径；形如 `/workspace/...` 的路径是作者沙箱（box）上的历史路径，在本仓库中分别对应 `mission-shell/`（原 `/workspace/microkit-mission-shell/`）与 `docs/`。文中命令含占位符，**不能直接复制执行**；可直接执行的命令见仓库根目录 `README.md` 与 `docs/REPRODUCE.md`。


**版本**：1.0.0  
**日期**：2026-09-23  
**SDK**：Microkit 2.3.1 · **Board**：`qemu_virt_aarch64` · **Config**：`debug`

---

## 1. 源码地图

| 路径 | 角色 |
|---|---|
| `gatekeeper.c` | 门闩、共签、证据链实现 |
| `mission_proto.h` | REQ/REP 常量、`GATE_CH` |
| `mission.system` | 两 PD + channel 组装 |
| `scenarios/client_full.c` | full 场景（主验收） |
| `scenarios/client_cosign_only.c` | 共签剖面 |
| `scenarios/client_false_only.c` | 假使命剖面 |
| `client.c` | 与 full 对齐的阅读副本（非 Makefile 直接依赖，除非 profile 指向） |
| `Makefile` | 交叉编译与 microkit 打包；`DEMO_PROFILE` 选择 CLIENT_SRC |
| `docker_build_run.sh` | 容器内构建 + `timeout 30s` QEMU |
| `run_qemu.sh` | 裸 QEMU 启动辅助 |
| `docs/PU_BOUNDARY.md` | 保证边界 |
| `docs/traditional-SE-embedded-in-mission-shell.md` | 传统 SE 纳入说明 |
| `README.md` | 快速入口 |

构建产物目录：`build/`（`gatekeeper.elf`、`client.elf`、`loader.img`、`report.txt`）。

---

## 2. 关键符号与日志契约

### 2.1 gatekeeper

| 符号 | 契约关键词 |
|---|---|
| `init` | `GATE|INFO|mission shell init…`；`GATE|INFO|K=cited…` |
| `deny(why)` | `GATE|DENY|<why>` |
| `allow_sim(why)` | `GATE|ALLOW_SIM|<why>` + `GATE|NOTE|sim_only; delivery!=achievement; non-clinical` |
| GRANT | `GATE|COSIGN|GRANT (demo stand-in)` |
| REVOKE | `GATE|COSIGN|REVOKE` |
| QUERY | `GATE|COSIGN|STATE=ON|OFF` |
| tip | `GATE|CHAIN|tip=<hex>|len=<n>` |
| `evidence_append` | `EVIDENCE|seq=…|prev=…|this=…|…` |

### 2.2 client

- `CLIENT|REQ|<name>`  
- `CLIENT|REP|ALLOW_SIM|DENY|OK|COSIGN_ON|COSIGN_OFF|EVIDENCE_TIP|OTHER`  
- `CLIENT|INFO|profile=<full|cosign_only|false_only>`  
- `CLIENT|INFO|MISSION_SHELL_DEMO_DONE`

---

## 3. 构建与运行

### 3.1 Docker 验收命令（唯一推荐，Windows）

```bat
docker run --rm -e DEMO_PROFILE=full -v <REPO_ROOT>:/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_build_run.sh
```

等价 PowerShell：

```powershell
docker run --rm -e DEMO_PROFILE=full `
  -v <REPO_ROOT>:/work `
  -w /work/mission-shell `
  trustworthysystems/sel4:latest `
  bash /work/mission-shell/docker_build_run.sh
```

### 3.2 脚本行为摘要（`docker_build_run.sh`）

1. `cd /work/mission-shell`；`SDK=/work/microkit-sdk-2.3.1`  
2. `PROFILE="${DEMO_PROFILE:-full}"` 并 echo  
3. 清空并创建 `build/`  
4. `make … DEMO_PROFILE="$PROFILE" CROSS_PREFIX=aarch64-linux-gnu`  
5. `timeout 30s qemu-system-aarch64 -machine virt,virtualization=on -cpu cortex-a53 -nographic -serial mon:stdio -device loader,file=$BUILD/loader.img,addr=0x70000000,cpu-num=0 -m size=2G`  
6. 打印 `=== QEMU done rc=$? ===`；**脚本以 exit 0 结束**（即使 QEMU 为 124）

### 3.3 其它剖面

```bash
DEMO_PROFILE=cosign_only bash docker_build_run.sh
DEMO_PROFILE=false_only bash docker_build_run.sh
```

### 3.4 挂载约定

宿主 `<REPO_ROOT>` 应同时包含：

- `mission-shell/`（本工程）  
- `microkit-sdk-2.3.1/`（或脚本所期望的相对布局；当前脚本假定 SDK 在 `/work/microkit-sdk-2.3.1`）

若本机将 SDK 置于 `mission-shell/microkit-sdk-2.3.1`，需调整挂载或脚本路径使 `/work/microkit-sdk-2.3.1` 可达（沙箱树内 SDK 在工程子目录；Windows 工作区常见为并列目录——以实际 `docker_build_run.sh` 为准）。

> 实现注记：仓库内 `docker_build_run.sh` 使用 `SDK=/work/microkit-sdk-2.3.1`。请保证 Docker 卷上该路径存在（可将 SDK 放到 `microkit_work/microkit-sdk-2.3.1`，或改脚本指向 `/work/mission-shell/microkit-sdk-2.3.1`）。**改脚本属配置变更，见文档 08。**

---

## 4. Makefile 要点

- 强制 `BUILD_DIR`、`MICROKIT_SDK`、`MICROKIT_BOARD`、`MICROKIT_CONFIG`  
- `DEMO_PROFILE` → `CLIENT_SRC`  
- `CFLAGS`：`-nostdlib -ffreestanding -g -O2 -Wall -Wno-unused-function -Werror`  
- 链接 `-lmicrokit -Tmicrokit.ld`  
- `microkit` 工具生成 `loader.img` 与 `report.txt`

---

## 5. 编码纪律（使命叠加）

1. 默认 `human_cosign_ok = 0`  
2. 先共签与对准，再谈「业务」（本示例业务退化为场景标签）  
3. 关键路径稳定关键词（日志即契约）  
4. `ALLOW_SIM` 必带 sim_only 注释  
5. **不实现**出束/设备写使能  
6. 证据 event 字符串与 DENY why 保持可追溯一致  

---

## 6. 本地阅读副本说明

`client.c` 与 `scenarios/client_full.c` 当前同源。修改场景时优先改 `scenarios/`，并同步 `client.c` 以免文档读者混淆；**构建只认 Makefile 的 CLIENT_SRC**。
