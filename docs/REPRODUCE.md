# 复现手册

本文给出在三类平台上从零复现演示与对照实验的完整步骤，以及如何判断「复现成功」。所有命令都在**仓库根目录**执行。结果的性质始终是 **环境自测，非确证性**（见 [STATUS-AND-LIMITATIONS.md](STATUS-AND-LIMITATIONS.md)）。

## 0. 复现目标与判据

| 级别 | 内容 | 成功判据 |
|---|---|---|
| A 演示 | `DEMO_PROFILE=full` 构建 + QEMU 运行 | `check_demo_log.py` 输出 `RESULT: PASS`：10 个证据事件顺序正确、链首尾相接、`GATE|CHAIN|tip=80488a97|len=10`、`MISSION_SHELL_DEMO_DONE`；最后 `rc=124`（timeout，正常） |
| B 实验矩阵 | 43 份日志 + 分析报告 | `scripts/compare_runs.sh` 输出 `COMPARE: PASS`（与 `runs/box-qemu/` 归一化后逐字节一致）；`report.md` 的数字表与 `reports/box-qemu/report.md` 一致（只有第 3 行运行环境说明不同） |
| C 主机检查 | 语料确定性、单元测试、hostsim | `CHECK_HOST: PASS`（`check: OK`、`84/84 passed`、`18/18`） |

## 1. Windows 10/11 + Docker Desktop

1. 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)，在 *Settings → General* 中启用 *Use the WSL 2 based engine*；启动后等待 *Engine running*。
2. 安装 Git for Windows。克隆前建议确认 `git config --global core.autocrlf` 的取值；本仓库的 `.gitattributes` 已固定各类文件的换行符，一般无需改动。
3. 选择一个**不含中文和空格**的目录克隆：

   ```bat
   cd /d D:\work
   git clone https://github.com/KOS-TL/MissionSoftware.git
   cd MissionSoftware
   ```

   （`D:\work` 只是示例，换成你自己的目录。）

4. 获取 SDK（`curl.exe` 下载 → `certutil` 校验 SHA-256 → `tar.exe` 解压）：

   ```bat
   scripts\windows\setup_sdk.bat
   ```

5. 预先拉取镜像（约 1.1 GB，可选但推荐）：

   ```bat
   docker pull trustworthysystems/sel4:latest
   docker inspect --format "{{index .RepoDigests 0}}" trustworthysystems/sel4:latest
   ```

   请记下第二条命令输出的 digest，报告结果时附上。

6. 演示、实验、分析、比对、主机检查：

   ```bat
   scripts\windows\run_demo.bat full
   scripts\windows\run_experiment.bat full
   scripts\windows\analyze.bat docker
   scripts\windows\check_host.bat
   ```

   比对脚本是 bash 写的，可在 Git Bash 中运行 `bash scripts/compare_runs.sh docker`，或在镜像中运行：

   ```bat
   docker run --rm -v "%cd%":/work -w /work trustworthysystems/sel4:latest bash scripts/compare_runs.sh docker
   ```

PowerShell 用户：`.bat` 前加 `.\`，例如 `.\scripts\windows\run_demo.bat full`；手写 docker 命令时把 `"%cd%"` 换成 `"${PWD}"`：

```powershell
docker run --rm -e DEMO_PROFILE=full -v "${PWD}:/work" -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_build_run.sh
```

> **状态说明**：上面这条 docker 命令（挂载目录不同）由作者于 2026-10-08 在 Windows + Docker 上验收通过；`scripts\windows\*.bat` 封装与 Windows 上的语料矩阵**尚未实际运行**。`run_experiment.bat` 与原先的 `mission-shell\experiment\windows\run_all_docker.bat` 等价，后者也只改了路径推导方式。

## 2. Linux x86_64

### 2.1 Docker 模式（推荐）

```bash
git clone https://github.com/KOS-TL/MissionSoftware.git && cd MissionSoftware
bash scripts/setup_sdk.sh
docker pull trustworthysystems/sel4:latest
bash scripts/run_demo.sh full
bash scripts/run_experiment.sh full
bash scripts/analyze.sh docker
bash scripts/compare_runs.sh docker
bash scripts/check_host.sh
```

当前用户需要能运行 `docker`（加入 `docker` 组或使用 rootless Docker）。Docker 模式**未在作者的 box 上运行**（box 没有 Docker），但所用命令与 Windows 上验收过的命令同构。

### 2.2 本机工具链模式（`MODE=native`，已在 box 上完整验证）

Debian/Ubuntu 示例：

```bash
sudo apt-get install -y gcc-aarch64-linux-gnu qemu-system-arm make python3 gcc curl
MODE=native bash scripts/run_demo.sh full
MODE=native bash scripts/run_experiment.sh full
bash scripts/analyze.sh local
bash scripts/compare_runs.sh local
```

box 上的版本：aarch64-linux-gnu-gcc 14.2.0（Debian 14.2.0-19）、QEMU 10.0.13、GNU Make 4.4.1、Python 3.13.5。其他版本的编译器可能生成不同的 `image_sha256`，但判决（`CASE|` 行）应当不变；若出现差异，请连同版本一起报告。

## 3. macOS

**未测试。** Apple silicon 上 Docker 默认拉取 arm64 镜像，而 `setup_sdk.sh` 默认下载 linux-x86-64 SDK，二者不匹配。可尝试的两条路线（均未验证）：

```bash
# 路线 1：以 amd64 仿真运行镜像（慢）
export DOCKER_DEFAULT_PLATFORM=linux/amd64
bash scripts/setup_sdk.sh && bash scripts/run_demo.sh full

# 路线 2：arm64 镜像 + linux-aarch64 SDK（需自行核对并提供 SHA-256）
SDK_PLATFORM=linux-aarch64 SDK_SHA256=<你核对过的哈希> bash scripts/setup_sdk.sh
```

官方 2.3.1 发布页同时提供 `linux-aarch64` 与 `macos-aarch64` 压缩包（链接已确认可访问），但本仓库只记录了 linux-x86-64 的哈希。Intel Mac 与 Linux Docker 模式应当相同，同样未测试。

## 4. 结果比对细节

- **日志**：`scripts/compare_runs.sh <名称>` 对每份日志做归一化后与 `runs/box-qemu/` 比较。被归一化的只有：QEMU 被 timeout 结束时打印的进程号、`RUN|END|elapsed_s`、`RUN|` 行中的 `image=`（镜像 digest，box 上为 `unknown`）与 `git=`（box 参考日志为 `nogit`）。`image_sha256`（构建出的系统镜像哈希）**不**被归一化：使用相同 SDK 与相同版本的编译器时应当一致。
- **报告**：`diff mission-shell/experiment/reports/box-qemu/report.md mission-shell/experiment/reports/<名称>/report.md` 应只有第 3 行（运行环境说明）不同；`falsification_checklist.md` 同理；各 CSV 文件应完全一致。
- **演示**：除 `check_demo_log.py` 外，也可直接 `grep "GATE|CHAIN" mission-shell/build_logs/demo_full.log`。

## 5. 只跑一部分

| 需求 | 命令（bash；Windows 用对应 `.bat`） |
|---|---|
| 冒烟：种子 20261007、各条件 1 次 | `bash scripts/run_experiment.sh quick` |
| 单个条件 | `DEMO_PROFILE=mission_corpus CORPUS_SEED=20261007 bash mission-shell/docker_corpus_run.sh > m.log`（本机模式；Docker 写法见 `mission-shell/experiment/README.md` §3.1） |
| 只要某个消融 | 上式加 `ABLATE=cosign`（或 `align`、`prov`、`U`） |
| 调整重复次数 / 种子 | `REPS=1 SEEDS="20261007 20261008" bash mission-shell/experiment/run_matrix.sh`（本机模式）（另可设 `SKIP_ABLATIONS=1`、`SKIP_HOLDOUT=1`、`SKIP_LEGACY=1`、`RUNS_DIR=…`） |
| 示意性原型（毕业设计） | `cd thesis/prototype && python3 er_schema.py && python3 spv_gen.py --seed 1 --determinism && bash run_proto_hostsim.sh` |

## 6. 报告你的复现结果

请在 issue 中附上：操作系统与版本、Docker Desktop 版本、镜像 digest、`check_demo_log.py` 的输出、`compare_runs.sh` 的最后两行，以及（若有差异）第一处差异的上下文。复现成功同样欢迎报告——Windows 上的语料矩阵复现正是本项目目前缺少的证据。
