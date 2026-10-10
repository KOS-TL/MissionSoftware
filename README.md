# MissionSoftware：使命软件工程（Mission Software Engineering）项目仓库

[English summary](README.en.md) · [文档索引](docs/INDEX.md) · [复现手册](docs/REPRODUCE.md) · [架构说明](docs/ARCHITECTURE.md) · [现状与局限](docs/STATUS-AND-LIMITATIONS.md)

本仓库收录「使命软件工程」课题的全部代码、实验数据与文档：一个在 seL4 Microkit 上运行的**使命约束外壳**（mission shell，题目 1 / S1），一套比较传统流程门闩与使命层门闩的**对照实验管线**，以及课题的综合报告、生命周期文档包、实验方案、文献综述和毕业设计任务文档。克隆本仓库并按下文操作，即可在自己的电脑上从源码重建全部镜像、重跑演示与实验矩阵，并在此基础上修改和完善。

课题的核心主张是：一个动作只有同时满足三个条件，才算「在使命之内」——

> **明示托付 ∧ 当前动作仍对准该托付 ∧ 检查可被证伪**
>
> 并且始终坚持 **交付 ≠ 达成**：系统放行一个动作（`ALLOW_SIM`）只说明它通过了检查、被交付执行，不说明使命已经达成。

外壳把这一主张落成两个 Microkit 保护域：门闩 `gatekeeper`（被动 PD，优先级 100）对每个请求依次检查人共签绑定、托付的时间窗/禁区/范围/版本、来源角色和「交付≠达成」，并把每次判决写进 FNV-1a32 哈希链；客户端 `client`（优先级 99）按剧本发出合法与「假使命」请求。对照实验用同一门闩源码的三个编译变体——传统流程基线 B、领域规则强化基线 B+、使命流程 M（及 4 个消融）——在作者自建语料上比较漏检率与误拒率。

> **证据状态（请先读这一段）**
>
> - 本仓库中的实验结果全部是 **环境自测，非确证性**：语料由作者自己编写（作者同时编写规则与语料），真值来自草稿 oracle，只用于确认实验装置工作，**不作为方法有效的证据**（实验方案 H1′）。
> - **语料矩阵在 Windows Docker 上的复现、以及独立标注的留出语料评测，均尚未完成（待办）。**
> - 原始演示 `DEMO_PROFILE=full` 已于 **2026-10-08 在作者的 Windows + Docker 环境中验收通过**：`GATE|CHAIN|tip=80488a97|len=10`。
> - 2026-10-10 在作者的 Linux 沙箱（box，本机交叉编译器 + QEMU，非 Docker）上，用本仓库的脚本重新构建并运行，演示与 43 份矩阵日志均与仓库内的参考结果一致；详见 [docs/verification/box-verification-2026-10-10.md](docs/verification/box-verification-2026-10-10.md)。

## 硬边界（不可越过）

- **非临床**：全部为仿真；不连接任何真实设备，**没有出束、没有厂商设备写使能**接口，也不得添加。
- **K（形式化内核保证）只引用、不宣称**：本项目不证明任何应用层性质，不宣称「seL4 级」应用证明。
- **Microkit 的 MCS 配置**：本仓库使用 Microkit SDK 2.3.1，其内核采用 MCS 配置；该配置的形式化验证仍在进行中，**能编译运行 ≠ 运行的是已验证内核**。
- **共签（cosign）是演示替身**：`GRANT/REVOKE` 报文只是人共签的占位，不是真实的身份认证或签名机制。
- **FNV-1a32 证据链是教学级**：用来演示「判决可追溯、可检出篡改」，不具备密码学强度。
- **`ALLOW_SIM` ≠ 达成**：门闩放行只表示「允许在仿真中交付」，不表示使命达成；「宣称达成」本身会被拒绝。

## 系统架构

![使命约束外壳与对照实验的详细架构](docs/figs/fig-arch-detail.png)

更完整的说明（两个保护域、通道与报文、剖面与变体、判决优先级、证据链、实验管线、目录布局的取舍）见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 仓库地图

```text
MissionSoftware/
├── README.md / README.en.md         本文件 / 英文摘要
├── mission-shell/                   ★ 全部可执行代码（Microkit 系统 + 对照实验）
│   ├── gatekeeper.c client.c mission_proto.h mission.system Makefile
│   ├── scenarios/                   演示剧本：client_full.c / client_cosign_only.c / client_false_only.c
│   ├── docker_build_run.sh          演示：构建 + QEMU 运行（容器内或本机）
│   ├── docker_corpus_run.sh         实验：按变体/语料构建 + QEMU 运行一次
│   ├── docs/                        外壳自带文档（PU 边界、传统 SE 纳入说明、生命周期包索引）
│   └── experiment/                  对照实验：门闩变体、语料生成、oracle、分析、篡改测试、单元测试、hostsim
│       ├── prereg.md deviations.md  预注册（2026-10-08 冻结）与偏离记录
│       ├── corpus/out/              冻结语料（5 个种子）+ SHA256SUMS
│       ├── runs/box-qemu/ reports/box-qemu/   作者沙箱上的参考运行日志与报告
│       └── runs/hostsim/  reports/hostsim/    主机模拟参考日志与报告
├── scripts/                         与位置无关的一键脚本（bash）；scripts/windows/ 为对应的 .bat
├── microkit-sdk-2.3.1/              （不入库）由 scripts/setup_sdk.* 下载并校验的官方 SDK
├── docs/                            文档：架构、复现、扩展、现状、综合报告、生命周期包、实验方案、综述……
├── thesis/                          毕业设计任务文档与示意性原型（prototype/，非实验树）
└── .github/workflows/               GitHub Actions：主机检查（push/PR）与实验性 Docker 演示（手动）
```

## 环境要求

| 平台 | 需要 | 状态 |
|---|---|---|
| **Windows 10/11** | Docker Desktop（WSL 2 后端）、Git for Windows；`curl.exe` 与 `tar.exe`（Windows 10 1803+ 自带） | 原始演示命令已由作者在此环境验收（2026-10-08）；本仓库的 `.bat` 封装**尚未在 Windows 上实际运行**，请反馈 |
| **Linux x86_64** | Docker（推荐），或本机 `aarch64-linux-gnu-gcc` + `qemu-system-aarch64` + `make` + `python3`（`MODE=native`） | 本机工具链模式已在作者 box（Debian，gcc 14.2.0，QEMU 10.0.13）上完整验证；Docker 模式未在 box 上运行（box 无 Docker） |
| **macOS（Apple silicon）** | Docker Desktop | **未测试**。镜像 `trustworthysystems/sel4:latest` 提供 arm64 版本，但默认下载的是 linux-x86-64 SDK；可尝试 `MISSION_IMAGE` 不变并设置 `DOCKER_DEFAULT_PLATFORM=linux/amd64`（仿真运行，较慢），或改用 `SDK_PLATFORM=linux-aarch64`（需自行提供 `SDK_SHA256`） |
| **任意平台（仅主机检查）** | `python3`（3.8+）与 `gcc` | 见快速开始 C；不需要 Docker、QEMU 或 SDK |

镜像体积约 1.1 GB（Docker Hub 记录：amd64 1,092,236,131 字节）；SDK 压缩包 72,548,289 字节。

## 快速开始

先克隆仓库并进入仓库根目录（下文所有命令都在仓库根目录执行）：

```bash
git clone https://github.com/KOS-TL/MissionSoftware.git
cd MissionSoftware
```

然后下载并校验官方 Microkit SDK 2.3.1（脚本核对 SHA-256 `b1b285b8785db7557eba6d0665dd4fbf2f265ea5c0b39d6f91ae3dcc43d2c424`，解压到 `microkit-sdk-2.3.1/`，不会提交进 git）：

```bash
bash scripts/setup_sdk.sh
```

```bat
scripts\windows\setup_sdk.bat
```

> 下文每一步都给出两种写法：**bash**（Linux、macOS、WSL、Git Bash）与 **Windows cmd**。在 PowerShell 中，`.bat` 写作 `.\scripts\windows\run_demo.bat full`。

### A. 演示：`DEMO_PROFILE=full`（约 1–3 分钟，首次拉镜像另计）

```bash
bash scripts/run_demo.sh full
```

```bat
scripts\windows\run_demo.bat full
```

封装脚本执行的就是作者在 Windows 上验收过的那条命令，只是把挂载目录换成了仓库根目录（不用封装脚本时可直接复制）：

```bash
docker run --rm -e DEMO_PROFILE=full -v "$PWD":/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_build_run.sh
```

```bat
docker run --rm -e DEMO_PROFILE=full -v "%cd%":/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_build_run.sh
```

日志保存在 `mission-shell/build_logs/demo_full.log`，脚本随后调用 `scripts/check_demo_log.py` 自动核对。**验收清单**（10 个 `EVIDENCE|seq=…|prev=…|this=…` 证据事件，顺序固定，每个事件的 `prev` 等于上一个事件的 `this`）：

| # | 事件 | 串口中的判决 | 链值 `this` |
|---|---|---|---|
| 1 | `gate_init` | 门闩初始化（共签默认 OFF，哈希链开启） | `24fd4b26` |
| 2 | `no_human_cosign` | 查询得 `STATE=OFF`；无共签时合法请求被 DENY | `dff76c7e` |
| 3 | `cosign_grant` | 人共签 GRANT，`STATE=ON` | `9efeac20` |
| 4 | `legal_path_sim` | 合法请求 `ALLOW_SIM`（附「交付≠达成」NOTE） | `811e41c4` |
| 5 | `expired_entrustment` | 过期托付 DENY | `0720fccb` |
| 6 | `forbidden_zone` | 禁区 DENY | `85fe7af5` |
| 7 | `advisor_cannot_enable` | 顾问不可使能 DENY | `36bc5c58` |
| 8 | `empty_U_no_achieve_tag` | 未声明不确定性 U 而请求「达成」类动作 DENY | `402b2ffd` |
| 9 | `cosign_revoke` | 共签 REVOKE | `6c909283` |
| 10 | `no_human_cosign` | 撤销后合法请求再次 DENY | `80488a97` |

随后应出现 `GATE|CHAIN|tip=80488a97|len=10` 与 `CLIENT|INFO|MISSION_SHELL_DEMO_DONE`，最后一行是 `=== QEMU done rc=124 ===`。**`rc=124` 是正常的**：Microkit 系统不会自行退出，脚本用 `timeout 30s` 结束 QEMU，124 正是 timeout 的返回码。核对脚本的最后一行应为 `RESULT: PASS`。

另外两个剖面：`cosign_only`（只演示共签开关，期望 `tip=4d591f49|len=6`）与 `false_only`（只演示假使命拦截，期望 `tip=dff6c037|len=6`）。这两个期望值来自 2026-10-10 box 上的运行，见验证记录。

### B. 完整对照实验矩阵 + 分析（box 上约 2 分钟；Docker 中预计更久）

```bash
bash scripts/run_experiment.sh full
bash scripts/analyze.sh
```

```bat
scripts\windows\run_experiment.bat full
scripts\windows\analyze.bat
```

矩阵包括：B、M × 5 个预注册种子 × 3 次重复，B+ 与 4 个消融（M-cosign / M-align / M-prov / M-U）× 首个种子，草稿留出语料（B、M、B+），以及原 `full` 剖面回归，共 43 份日志（分析器统计其中 42 份矩阵日志）。日志落在 `mission-shell/experiment/runs/<名称>/`，报告写到 `mission-shell/experiment/reports/<名称>/report.md`；名称在 Docker 模式下默认为 `docker`，本机工具链模式下默认为 `local`。只想快速冒烟时用 `quick`（只跑种子 20261007、每条件 1 次、不跑留出语料与回归）。

**作者沙箱 box 上的参考结果**（`mission-shell/experiment/reports/box-qemu/report.md`；QEMU 10.0.13 + aarch64-linux-gnu-gcc 14.2.0 + SDK 2.3.1，非 Docker）——**环境自测，非确证性**：

| 条件 | 种子数 | MUST_DENY 漏检（FNR） | 合法请求误拒（FPR） |
|---|---|---|---|
| B 传统流程 | 5 | 800/1000 = 80.0% | 0/600 = 0.0% |
| B+ 领域规则强化 | 1 | 128/200 = 64.0% | 0/120 = 0.0% |
| **M 使命流程** | 5 | **0/1000 = 0.0%** | 0/600 = 0.0% |
| M-cosign（去共签） | 1 | 20/200 = 10.0% | 0/120 = 0.0% |
| M-align（去对准） | 1 | 93/200 = 46.5% | 0/120 = 0.0% |
| M-prov（去来源） | 1 | 20/200 = 10.0% | 0/120 = 0.0% |
| M-U（去交付≠达成） | 1 | 20/200 = 10.0% | 0/120 = 0.0% |

运行完整性：INVALID 0；12/12 个重复组的 `CASE|` 行逐字节一致；回归门禁 `tip=80488a97|len=10` 通过。这些数字只说明**装置按设计工作**（作者语料上「仅使命可拦」的类别 B 拦不住、M 能拦），不能外推为方法在独立语料上的效果。你的运行结果应与之逐行一致（运行耗时、进程号等字段除外）；如何比较见 [docs/REPRODUCE.md](docs/REPRODUCE.md)。

### C. 仅主机检查（无需 Docker / QEMU / SDK，约 5 秒）

```bash
bash scripts/check_host.sh
```

```bat
scripts\windows\check_host.bat
```

依次运行：`gen_corpus.py --check`（重新生成 5 个种子的语料并与冻结的 `SHA256SUMS` 比对）、门闩单元测试（28 例 × 3 个变体 = 84 项）、hostsim 主机模拟（18 份日志与参考逐字节比较）。期望输出 `check: OK`、`84/84 passed`、`18/18`、`CHECK_HOST: PASS`。Windows 封装在镜像内执行同一脚本（未在 Windows 上实测）；本机装有 Python 3 与 gcc 时也可在 Git Bash/WSL 中直接运行 bash 版本。**hostsim 是主机模拟，不是 QEMU 实测。**

## 修改与扩展

- 改门闩规则：`mission-shell/experiment/gatekeeper_field.c`（实验变体）或 `mission-shell/gatekeeper.c`（演示）；同步修改参考判定器 `experiment/oracle/oracle.py` 并在 `experiment/tests/run_unit_tests.py` 中加用例。
- 加语料类别：`experiment/corpus/gen_corpus.py`；**冻结语料不得静默覆盖**，改动须先记入 `experiment/deviations.md`。
- 加演示剧本：`mission-shell/scenarios/client_<名称>.c`，以 `DEMO_PROFILE=<名称>` 构建。

完整的「新增一条规则 + 单元测试 + 语料类别」示例见 [docs/EXTENDING.md](docs/EXTENDING.md)。

**推荐的开发循环**：改代码 → `bash scripts/check_host.sh`（秒级）→ `bash scripts/run_experiment.sh quick` → `bash scripts/analyze.sh` → 确认无误后再跑 `full`。提交前运行 `bash scripts/verify_repo.sh`（仓库卫生检查）。

## 如何阅读结果

- 串口日志的行格式：`GATE|...` 是门闩输出，`EVIDENCE|seq=|prev=|this=|<事件>` 是证据链条目，`CLIENT|...` 是客户端输出，`CASE|...` 是实验用例的判决，`RUN|...` 是运行元数据（构建哈希 `image_sha256`、语料哈希 `corpus_sha256`、镜像 digest）。
- `report.md` 依次给出：运行完整性 → 作者语料上的 FNR/FPR（含 Wilson 与 Clopper–Pearson 区间）→ B vs M 配对 McNemar 检验 → 消融 → 篡改检测 → 草稿留出语料 → 可证伪性清单。
- 报告中凡是「作者语料」「草稿真值」「hostsim」的结果都**不是确证性证据**；预注册的确证性检验需要独立标注的留出语料，目前尚未进行。

## 常见问题

| 现象 | 原因与处理 |
|---|---|
| `error during connect` / `Docker is not running` | Docker Desktop 未启动。启动后等待状态变为 *Engine running* 再重试；Windows 需启用 WSL 2 后端。 |
| `$'\r': command not found`、`bad interpreter` | 脚本被转换成了 CRLF。本仓库的 `.gitattributes` 强制 `*.sh *.py *.c *.h Makefile` 为 LF、`*.bat` 为 CRLF；若曾设置 `core.autocrlf=true` 并在加入 `.gitattributes` 前检出，请执行 `git rm --cached -r . && git reset --hard`（会丢弃未提交修改）。不要用会改换行符的编辑器保存 `.sh` 文件。 |
| 最后一行是 `rc=124` | 正常，见快速开始 A。只有在 `MISSION_SHELL_DEMO_DONE` 缺失时才需要排查。 |
| Windows 路径/引号问题 | 在 cmd 中用 `-v "%cd%":/work`，在 PowerShell 中用 `-v "${PWD}:/work"`；仓库路径尽量不含中文与空格。不要把 cmd 的 `^` 续行和 PowerShell 的 `` ` `` 续行混用。 |
| `docker pull` 很慢或超时 | 镜像约 1.1 GB；可先单独执行 `docker pull trustworthysystems/sel4:latest`，或在 Docker Desktop 中配置镜像加速。 |
| `ERROR: 未找到 Microkit SDK` | 先运行 `scripts/setup_sdk.sh` 或 `scripts\windows\setup_sdk.bat`；SDK 必须位于仓库根目录下的 `microkit-sdk-2.3.1/`。 |
| `microkit: Permission denied`（Windows） | 在 Windows 上解压的 SDK 没有可执行位。Docker Desktop 的绑定挂载通常会把文件显示为可执行；若仍报错，可改在 WSL 中运行 `bash scripts/setup_sdk.sh`，或在镜像内解压：`docker run --rm -v "%cd%":/work -w /work trustworthysystems/sel4:latest tar -xzf .cache/microkit-sdk-2.3.1-linux-x86-64.tar.gz`（未在 Windows 上实测）。 |
| SHA-256 校验失败 | 删除 `.cache/` 中的压缩包后重试；仍失败请勿继续，提 issue 说明。 |
| 镜像版本不同导致结果不一致 | `latest` 标签会更新（Docker Hub 记录的最近更新为 2026-10-09 01:39 CST）。实验脚本把镜像 digest 写进每份日志的 `RUN|` 行；比较结果时请一并报告 digest。 |

## 参与贡献

欢迎提 issue 与 pull request。实验相关的修改必须遵守预注册纪律（先记偏离、后改代码、不覆盖冻结语料、不改写已有结论的口径），详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

代码采用 **MIT** 许可证（[LICENSE](LICENSE)）；文档、插图与实验数据采用 **CC BY 4.0**（[LICENSE-docs](LICENSE-docs)），详见 [LICENSES.md](LICENSES.md)。第三方组件（Microkit SDK、seL4、Docker 镜像）不随本仓库分发，各自遵循其原许可证。

## 引用

见 [CITATION.cff](CITATION.cff)（GitHub 页面右侧的 “Cite this repository” 会据此生成引用格式）。

## 文档索引

| 文档 | 内容 |
|---|---|
| [docs/INDEX.md](docs/INDEX.md) | 全部文档的导航 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系统与实验管线架构、目录布局取舍 |
| [docs/REPRODUCE.md](docs/REPRODUCE.md) | 分平台的完整复现步骤与结果比对 |
| [docs/EXTENDING.md](docs/EXTENDING.md) | 新增规则 / 测试 / 语料类别的示例 |
| [docs/STATUS-AND-LIMITATIONS.md](docs/STATUS-AND-LIMITATIONS.md) | 已完成、未完成与已知局限 |
| [docs/report/mission-se-integrated-report.md](docs/report/mission-se-integrated-report.md) | 项目与实验综合报告 |
| [docs/verification/box-verification-2026-10-10.md](docs/verification/box-verification-2026-10-10.md) | 本仓库在 box 上的验证记录 |
| [mission-shell/experiment/README.md](mission-shell/experiment/README.md) | 对照实验的详细说明 |
| [thesis/graduation-project-spec.md](thesis/graduation-project-spec.md) | 毕业设计任务文档 |
