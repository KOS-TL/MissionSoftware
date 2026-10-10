# 架构说明

本文说明仓库中可执行部分的结构：Microkit 系统（演示）、对照实验管线、脚本层，以及目录布局为什么这样安排。概念层面的论证（使命软件工程的定义、与传统软件工程的关系、可证伪性设计）见 [综合报告](report/mission-se-integrated-report.md)。

![详细架构](figs/fig-arch-detail.png)

## 1. Microkit 系统：两个保护域

系统描述文件 `mission-shell/mission.system`：

| 保护域 | 优先级 | 性质 | 程序 |
|---|---|---|---|
| `gatekeeper` | 100 | 被动（`passive="true"`），只在被调用时运行 | `gatekeeper.elf`：演示剖面由 `gatekeeper.c` 编译，实验剖面由 `experiment/gatekeeper_field.c` 编译 |
| `client` | 99 | 主动 | `client.elf`：演示剧本 `scenarios/client_<剖面>.c`，或实验用例驱动 `experiment/client_corpus.c` |

两者之间只有一条通道（id 0），客户端一端 `pp="true"`，即客户端以受保护过程调用（PPC）同步调用门闩。门闩优先级高于客户端，被动 PD 借用调用者的调度上下文运行——这是 Microkit 在 MCS 内核配置下的标准用法。**提醒：MCS 配置的形式化验证仍在进行中，本系统能构建运行不等于运行在已验证内核上。**

### 1.1 报文（`mission_proto.h`）

演示剖面使用简单的请求码：`REQ_LEGAL_ENABLE(1)`、`REQ_EXPIRED_TRUST(2)`、`REQ_FORBIDDEN_ZONE(3)`、`REQ_ADVISOR_ENABLE(4)`、`REQ_EMPTY_U_ACHIEVE(5)`、共签 `GRANT(20)/REVOKE(21)/QUERY(22)`、`REQ_EVIDENCE_TIP(23)`；回复 `ALLOW_SIM(10)`、`DENY(11)`、`OK(12)`、`COSIGN_ON(13)`、`COSIGN_OFF(14)`、`EVIDENCE_TIP(15)`。

实验剖面使用按字段编码的请求（`experiment/proto_fields.h`）：动作、角色、来源、托付编号与版本、区域、强度、nonce、U 声明等字段写入消息寄存器，门闩只依据这些字段、门闩自己持有的托付表（`experiment/gen/entrustments_gen.h`，由 `corpus/entrustments.json` 生成）和逻辑时钟作判决，**不读取任何揭示真值的标签**。

### 1.2 门闩的判决次序

实验变体 `gatekeeper_field.c` 用编译宏选择条件：

| 宏 | 条件 | 检查 |
|---|---|---|
| `GATE_VARIANT_B` | B 传统流程（公平基线） | B-1 枚举、B-2 范围、B-3 工单存在、B-4 角色 ACL、B-5 nonce 去重 |
| `GATE_VARIANT_BPLUS` | B+ 领域规则强化基线 | B + 站点全局时间窗 + 站点禁区 |
| `GATE_VARIANT_M` | M 使命流程 | B-1…B-5 + M-1 共签绑定 (ent_id, ver) → M-2 时间（闭区间）→ M-3 禁区 → M-4 范围（区/强度/动作）→ M-5 版本新鲜 → M-6 来源角色 → M-7 交付≠达成、U 非空 → M-8 证据链 |
| `ABLATE_COSIGN / _ALIGN / _PROV / _U` | M 的消融（至多一个） | 分别去掉 M-1、M-2…M-5、M-6、M-7 |

多条规则同时失败时，按代码中的顺序取第一个失败的理由码，该顺序在 `experiment/prereg.md` §5 中预注册。参考判定器 `experiment/oracle/oracle.py` 以 Python 实现同一规格（`experiment/oracle/rules_spec.md`），用于生成语料真值与核对 M 的理由码。

### 1.3 证据链

每个判决事件追加一条 `EVIDENCE|seq=<n>|prev=<上一条>|this=<本条>|<事件名>`，`this` 由 FNV-1a 32 位散列对「上一条 tip + 序号 + 事件名」计算得到；`REQ_EVIDENCE_TIP` 打印 `GATE|CHAIN|tip=<最后一条>|len=<条数>`。离线篡改轨道 T1–T7（`experiment/tamper/`）在主机上对已采集日志的副本做改写、删除、交换、插入、截尾、重编号、重算链等变换，检查链校验能否发现；按预先声明，T5（截尾，无外部锚点）与 T7（知情者重算整条链）在 M 上**预期检不出**。**FNV-1a32 只具教学意义，不具备密码学强度。**

## 2. 剖面（`DEMO_PROFILE`）与构建

`Makefile` 根据 `DEMO_PROFILE` 选择源文件：

| 剖面 | 门闩源 | 客户端源 | 用途 |
|---|---|---|---|
| `full`（默认） | `gatekeeper.c` | `scenarios/client_full.c` | 演示：共签开/关 + 4 类假使命 + 撤销，10 个证据事件 |
| `cosign_only` | `gatekeeper.c` | `scenarios/client_cosign_only.c` | 演示：只看共签开关 |
| `false_only` | `gatekeeper.c` | `scenarios/client_false_only.c` | 演示：只看假使命拦截 |
| `baseline_corpus` | `experiment/gatekeeper_field.c` + `-DGATE_VARIANT_B` | `experiment/client_corpus.c` | 实验条件 B |
| `baselineplus_corpus` | 同上 + `-DGATE_VARIANT_BPLUS` | 同上 | 实验条件 B+ |
| `mission_corpus` | 同上 + `-DGATE_VARIANT_M`（+ `ABLATE`） | 同上 | 实验条件 M 与消融 |

实验剖面另需 `CORPUS_SET=seed|holdout_draft`、`CORPUS_SEED`，语料头 `experiment/corpus/out/corpus_<seed>.h` 被复制为 `$(BUILD_DIR)/corpus_active.h` 编进客户端。构建参数固定：`MICROKIT_BOARD=qemu_virt_aarch64`、`MICROKIT_CONFIG=debug`、`CROSS_PREFIX=aarch64-linux-gnu`。运行：`qemu-system-aarch64 -machine virt,virtualization=on -cpu cortex-a53 -m 2G`，把 `loader.img` 加载到 `0x70000000`。

## 3. 实验管线

```text
corpus/entrustments.json ──► gen_corpus.py ──► corpus/out/corpus_<seed>.{json,h} + SHA256SUMS（冻结）
                                  │  (oracle.py 复核真值)
                                  ▼
docker_corpus_run.sh：校验 SHA256SUMS → make（变体/消融/语料）→ QEMU（见 CORPUS_DONE 即停）→ 串口日志（RUN| / CASE| / EVIDENCE|）
                                  ▼
run_matrix.sh：条件 × 种子 × 重复 → runs/<名称>/<条件>/<语料>/r<k>.log
                                  ▼
analysis/parse_serial.py + analyze.py + stats_exact.py → reports/<名称>/report.md、rates.csv、paired.csv、tamper.csv …
```

- `docker_corpus_run.sh`：一次「构建 + 运行」，把运行元数据写入 `RUN|` 行（剖面、种子、镜像 digest、git 版本、语料哈希、构建出的镜像哈希 `image_sha256`），未见 `CORPUS_DONE` 则记为 `INVALID`。
- `hostsim/`：用本机 `gcc` 把同一门闩源码与 Microkit 桩（`hostsim/microkit.h`）编译成主机程序，按同一语料运行，生成与 QEMU 日志同格式的日志。**主机模拟，不是 QEMU 实测**；用于快速回归与 CI。
- `tests/run_unit_tests.py`：28 个单元用例 × 3 个条件，经 hostsim 执行。
- `tamper/`：篡改检测实验。`oracle/kappa.py`：双标一致性（Cohen's κ）工具，在独立标注人到位之前只用于演练流程。

## 4. 脚本层（`scripts/`）

| 脚本 | 作用 | 模式 |
|---|---|---|
| `setup_sdk.sh` / `windows\setup_sdk.bat` | 下载官方 Microkit SDK 2.3.1，核对 SHA-256，解压到仓库根的 `microkit-sdk-2.3.1/` | — |
| `run_demo.sh [剖面]` / `run_demo.bat` | 演示构建 + 运行；`full` 剖面自动调用 `check_demo_log.py` | docker / native |
| `run_experiment.sh [full\|quick]` / `run_experiment.bat` | 调用 `experiment/run_matrix.sh` | docker / native |
| `analyze.sh [名称]` / `analyze.bat` | 调用 `experiment/analysis/analyze.py` | 本机 python3（bat 版在镜像内运行） |
| `check_host.sh` / `check_host.bat` | 语料 `--check` + 单元测试 + hostsim 比对 | 本机 python3 + gcc（bat 版在镜像内运行） |
| `verify_repo.sh` / `check_links.py` | 仓库卫生检查 / Markdown 相对链接检查 | — |

`MODE=auto`（默认）在 Docker 可用时使用 Docker，否则使用本机 `aarch64-linux-gnu-gcc` + `qemu-system-aarch64`；也可显式指定 `MODE=docker` 或 `MODE=native`。镜像可用 `MISSION_IMAGE` 覆盖（默认 `trustworthysystems/sel4:latest`）。

## 5. 目录布局的取舍

作者原先的工作目录是一个名为 `microkit_work` 的文件夹，其中并列放着 `mission-shell/` 与 `microkit-sdk-2.3.1/`，Docker 命令把这个文件夹挂载为 `/work`：

```text
-v <microkit_work>:/work -w /work/mission-shell ... bash /work/mission-shell/docker_build_run.sh
```

`docker_build_run.sh` 中写死了 `/work/mission-shell`、`/work/microkit-sdk-2.3.1`、`/work/mission-shell/build` 三个路径；`docker_corpus_run.sh` 默认在 `../microkit-sdk-2.3.1` 寻找 SDK。为了让**已经验收过的命令几乎原样可用、且脚本行为不变**，本仓库把**仓库根目录本身当作 `microkit_work`**：

- 代码保持在 `mission-shell/` 下，不改名、不搬动；
- SDK 由 `setup_sdk.*` 下载到仓库根的 `microkit-sdk-2.3.1/`（已列入 `.gitignore`，不提交）；
- 于是 `-v <仓库根>:/work -w /work/mission-shell` 与原命令完全同构，`docker_build_run.sh` 的默认路径与 `docker_corpus_run.sh` 的 `../microkit-sdk-2.3.1` 查找规则都直接成立。

任务说明中曾建议把 SDK 放在 `third_party/`。我们没有这样做：那样就必须修改两个实验脚本的 SDK 查找逻辑或每次传入额外变量，改动了已验收的行为面。目前的做法对 `docker_build_run.sh` 只做了最小改动——三个路径改为可由 `MISSION_SHELL_DIR`、`MISSION_MICROKIT_SDK`、`MISSION_BUILD_DIR` 覆盖，默认值与原脚本逐字相同（使用带 `MISSION_` 前缀的变量名，是为了避免镜像中可能预设的 `MICROKIT_SDK` 意外改变行为）。这一改动只为本机工具链模式服务；box 上的验证表明，改动前后在同一路径下构建出的 `loader.img` 与 ELF 逐字节相同（见[验证记录](verification/box-verification-2026-10-10.md)）。

> 注意：`docker_corpus_run.sh`（未改动）会优先使用环境变量 `MICROKIT_SDK`。如果你使用的镜像预设了该变量，实验运行会改用镜像中的 SDK。日志的 `RUN|build_ok` 行记录了构建出的 `image_sha256`，可据此判断是否与参考一致。
