# 对照实验分支：使命流程（M）vs 传统流程（B）

> Microkit 使命约束外壳 · 实验分支 `exp/controlled-v1` · 依据 `controlled-experiment-design.md`（方案 v0.1）
> 非临床 · 仅仿真 · 无写使能 · 不宣称 seL4 级应用证明 · 交付 ≠ 达成 · FNV-1a32 证据链为教学级

## 0. 当前状态（务必先读）

| 部件 | 状态 |
|---|---|
| 按字段判决的门闩 `gatekeeper_field.c`（B / B+ / M / 消融） | 已实现；box 上真实 QEMU 运行通过 |
| 语料客户端 `client_corpus.c`、语料生成器、Makefile 新剖面、`docker_corpus_run.sh` | 已实现；box 上真实 QEMU 运行通过 |
| 解析 / 篡改 / 统计流水线 | 已实现并端到端跑通 |
| 原 `full / cosign_only / false_only` 剖面 | **未改动**；改 Makefile 后重建，三剖面 ELF 与 `loader.img` 与改动前逐字节一致；`full` 仍得 `GATE|CHAIN|tip=80488a97|len=10` |
| 真值规格 `oracle/rules_spec.md`、参考判定器 `oracle/oracle.py` | **草稿·待独立标注人复核；不计入确证性结论** |
| 留出语料 `corpus/out/holdout_draft.*` | **草稿·待独立标注人复核；不计入确证性结论**（作者手写，仅演示流水线；不得用于判定 X-1，不得用于回改规则） |
| 独立标注人 | **尚未指定** |
| 人工审查小型研究（RQ3b / E1 / X-6） | **推迟，未实施** |
| 预注册 `prereg.md` | 阈值与反证条件已冻结；语料哈希为"草稿冻结"（真值待标注人确认） |

因此，本分支目前产生的所有数字（包括 `reports/` 下的报告）都只是**装置自检（setup check）**。按方案 H1′，作者语料上的"使命层全拦截"近乎同义反复，**不作为方法有效的证据**。

## 1. 目录

```
mission-shell/
├── gatekeeper.c, mission_proto.h, scenarios/, mission.system, docker_build_run.sh   ← 未改动
├── Makefile                 ← 仅新增剖面分支（原三剖面编译命令与产物不变）
├── docker_corpus_run.sh     ← 新增：实验剖面构建 + QEMU + 日志（超时可配，见到 CORPUS_DONE 即结束）
└── experiment/
    ├── README.md            本文件
    ├── prereg.md            预注册（冻结阈值、假设、反证条件、规则优先级、语料哈希）
    ├── proto_fields.h       共用报文布局（标签 30–33、REP_ALLOW=16、MR_* 寄存器、托付记录、语料步骤）
    ├── gatekeeper_field.c   按字段判决的门闩：-DGATE_VARIANT_B | _BPLUS | _M，-DABLATE_COSIGN|ALIGN|PROV|U
    ├── client_corpus.c      语料回放客户端（对所有条件相同；可分片）
    ├── run_matrix.sh        按方案 §5.4 的运行矩阵批量运行（可在 Docker 容器内一次跑完）
    ├── gen/entrustments_gen.h          托付表（由 corpus/entrustments.json 生成；种子无关）
    ├── corpus/
    │   ├── entrustments.json           托付表与站点规则（B+ 用）
    │   ├── gen_corpus.py               作者语料 A 生成器（5 个种子 × 320 用例；确定性）
    │   ├── holdout_draft.py            草稿留出语料（47 例：34 应拒 / 13 可放行，其中 2 例 spec_gap）
    │   ├── corpus_c.py                 JSON → C 头写出器（只写请求字段，不写类别/真值）
    │   └── out/                        corpus_<seed>.{json,h}、holdout_draft.{json,h}、SHA256SUMS
    ├── oracle/
    │   ├── rules_spec.md               真值规则规格（草稿）
    │   ├── oracle.py                   参考判定器（草稿；只读 JSON，不导入门闩代码）
    │   └── kappa.py                    双标一致性（抽样模板 + Cohen's κ）
    ├── tamper/
    │   ├── tamper.py                   T1–T7 篡改变换
    │   ├── run_tamper.py               批量篡改 + 检测
    │   └── expectations.json           预先声明的检出预期（T5 无锚点、T7 在 M 上预期失败，属 U）
    ├── analysis/
    │   ├── parse_serial.py             方案附录 B 接口：parse / verify-chain / verify-seq / tamper / score / determinism
    │   ├── analyze.py                  列联表、精确 McNemar、Wilson 与 Clopper–Pearson 区间、误拒非劣效、Fisher、Holm、反证清单 → Markdown
    │   ├── stats_exact.py              精确统计（仅标准库）
    │   └── loc_count.py                按编译期条件统计门闩有效行数
    ├── hostsim/                        主机模拟（gcc + microkit 桩）。【主机模拟、非 QEMU 实测】
    ├── tests/run_unit_tests.py         B/B+/M 单元测试（28 例 × 3 条件；主机模拟）
    ├── windows/run_all_docker.bat      Windows 一键运行（ASCII 内容，CRLF）
    ├── runs/box-qemu/                  box 上真实 QEMU 运行日志（43 份）
    ├── runs/hostsim/                   主机模拟日志（18 份）
    └── reports/box-qemu/, reports/hostsim/   自动生成的装置自检报告
```

## 2. 条件定义

| 条件 | 构建 | 检查 |
|---|---|---|
| **B** 传统流程（公平基线） | `DEMO_PROFILE=baseline_corpus` | B-1 枚举、B-2 范围、B-3 工单存在（不查版本/时间/范围）、B-4 角色 ACL、B-5 nonce 去重；普通序号审计日志 `AUDIT|seq=` |
| **B+** 领域规则强化基线 | `DEMO_PROFILE=baselineplus_corpus` | B + 站点运行窗 [50, 2000] + 站点禁区 {7, 15}；无共签、无版本、无来源、无 U |
| **M** 使命流程 | `DEMO_PROFILE=mission_corpus` | B-1…B-5 + M-1 共签绑定 (ent_id, ver) + M-2 时间 + M-3 禁区 + M-4 范围 + M-5 版本新鲜 + M-6 来源 + M-7 交付≠达成/U 非空 + M-8 FNV-1a32 证据链 |
| **M−k** 消融 | `DEMO_PROFILE=mission_corpus ABLATE=cosign\|align\|prov\|U` | 去掉对应组件 |

判决只依据请求字段、门闩持有的托付表与逻辑时钟（测试专用报文 `REQ_HARNESS_CLOCK_SET` 设置），不读任何揭示真值的标签；`MR_CASE_ID` 只在打印函数中出现（`rg MR_CASE_ID experiment/gatekeeper_field.c` 可核对）。多条规则同时失败时的理由码按 `prereg.md` §5 的固定优先级。

## 3. 构建与运行

### 3.1 Windows + Docker（与现有 README 相同的挂载方式）

> 仓库化（v0.1.0）：以下命令均在 **cmd** 中、于**仓库根目录**（含 `mission-shell\` 与 `microkit-sdk-2.3.1\`）执行，`%cd%` 即挂载为 `/work` 的目录；PowerShell 把 `"%cd%"` 换成 `"${PWD}"`，bash 换成 `"$PWD"`。更简便的封装见仓库根目录 `scripts/windows/*.bat` 与 `docs/REPRODUCE.md`。

单个剖面（日志写到文件；构建输出留在控制台）：

```bat
cd /d <仓库克隆目录>
mkdir mission-shell\experiment\runs\docker 2>nul
docker run --rm -e DEMO_PROFILE=mission_corpus -e CORPUS_SEED=20261007 -e QEMU_TIMEOUT=120 -v "%cd%":/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_corpus_run.sh > mission-shell\experiment\runs\docker\M_20261007_r1.log
docker run --rm -e DEMO_PROFILE=baseline_corpus -e CORPUS_SEED=20261007 -e QEMU_TIMEOUT=120 -v "%cd%":/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_corpus_run.sh > mission-shell\experiment\runs\docker\B_20261007_r1.log
docker run --rm -e DEMO_PROFILE=baselineplus_corpus -e CORPUS_SEED=20261007 -e QEMU_TIMEOUT=120 -v "%cd%":/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_corpus_run.sh > mission-shell\experiment\runs\docker\Bplus_20261007_r1.log
docker run --rm -e DEMO_PROFILE=mission_corpus -e ABLATE=cosign -e CORPUS_SEED=20261007 -e QEMU_TIMEOUT=120 -v "%cd%":/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_corpus_run.sh > mission-shell\experiment\runs\docker\M-cosign_20261007_r1.log
docker run --rm -e DEMO_PROFILE=mission_corpus -e CORPUS_SET=holdout_draft -e QEMU_TIMEOUT=120 -v "%cd%":/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_corpus_run.sh > mission-shell\experiment\runs\docker\M_holdout_draft_r1.log
```

`ABLATE` 可取 `cosign | align | prov | U`；`CORPUS_SEED` 取 5 个预注册种子之一；分片：`-e CORPUS_SHARD=0/2` 与 `-e CORPUS_SHARD=1/2` 各跑一次，解析时传两个 `--log`。

**完整运行矩阵（推荐，一条命令）**：B、M × 5 种子 × 3 次重复 + B+ + 4 个消融 + 草稿留出语料 + full 回归，日志按 `runs/docker/<条件>/<语料>/r<k>.log` 落盘：

```bat
docker run --rm -e RUNS_DIR=/work/mission-shell/experiment/runs/docker -e QEMU_TIMEOUT=120 -v "%cd%":/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/experiment/run_matrix.sh
```

分析（容器内 python3；若本机装有 Python 3.8+ 也可直接在 Windows 上运行同一 `python` 命令）：

```bat
docker run --rm -v "%cd%":/work -w /work/mission-shell trustworthysystems/sel4:latest python3 experiment/analysis/analyze.py --runs-dir experiment/runs/docker --out-dir experiment/reports/docker --env-label "Docker trustworthysystems/sel4 + QEMU (Windows host)"
```

`windows/run_all_docker.bat` 把上面三步（含记录镜像 digest）串在一起。

> 原有剖面照旧：`docker run ... -e DEMO_PROFILE=full ... bash /work/mission-shell/docker_build_run.sh`（v0.1.0 仅把脚本中三处路径改为可由环境变量覆盖，默认值与行为不变）。

### 3.2 Linux / 沙箱（已装交叉编译器与 QEMU）

```bash
DEMO_PROFILE=mission_corpus CORPUS_SEED=20261007 ./docker_corpus_run.sh > m.log
RUNS_DIR=$PWD/experiment/runs/local ./experiment/run_matrix.sh
python3 experiment/analysis/analyze.py --runs-dir experiment/runs/local --out-dir experiment/reports/local --env-label "..."
```

### 3.3 无 Docker / 无 QEMU 时：主机模拟

```bash
bash experiment/hostsim/run_hostsim.sh          # 【主机模拟、非 QEMU 实测】
python3 experiment/tests/run_unit_tests.py      # 28 例 × 3 条件
```

主机模拟只验证判决逻辑与日志格式；任何由它得到的数字都必须标注"主机模拟、非 QEMU 实测"。在 box 上已核对：18 组（条件, 语料）的门闩/客户端输出行与真实 QEMU 日志**逐字节一致**。

## 4. 解析与分析

```bash
P=experiment/analysis/parse_serial.py
python3 $P parse --log run.log --corpus experiment/corpus/out/corpus_20261007.json --condition M --out res.csv
python3 $P verify-chain --log run.log [--anchor tip=80488a97,len=10 | --anchor-from-log original.log]
python3 $P verify-seq --log b_run.log
python3 $P tamper --log run.log --kind T6 --n 20 --seed 20261007 --outdir tampered/
python3 $P score --results res.csv --corpus experiment/corpus/out/corpus_20261007.json --out confusion.csv
python3 $P determinism --logs r1.log r2.log r3.log
python3 experiment/oracle/oracle.py compare --corpus experiment/corpus/out/corpus_20261007.json --results res.csv
python3 experiment/tamper/run_tamper.py --log-b b.log --log-m m.log --out-dir tamper_out/
```

退出码：0 通过；2 INVALID（缺 `CORPUS_DONE`、用例缺判决、重复判决、客户端回执不一致）；3 链或序号校验失败。INVALID **不计为 DENY**。

日志行文法（门闩为判决唯一来源）：

```
RUN|profile=…|condition=…|corpus_set=…|seed=…|image=…|git=…|corpus_sha256=…    # 脚本写入
CASE|id=<id>|kind=target|verdict=<ALLOW|ALLOW_SIM|DENY>|reason=<code>          # 门闩，被评分请求
SETUP|id=<id>|kind=setup|verdict=…|reason=…                                     # 门闩，前置请求（不评分）
GATE|NOTE|sim_only; delivery!=achievement; non-clinical                         # M 每次 ALLOW_SIM 后
EVIDENCE|seq=<n>|prev=<8hex>|this=<8hex>|<event>                                # M
AUDIT|seq=<n>|<event>                                                           # B / B+
GATE|CHAIN|tip=<8hex>|len=<n>   或   GATE|AUDIT_END|len=<n>                     # 运行结束
CLIENT|REP|case=<id>|label=<rep>                                                # 客户端回执（交叉核对）
CLIENT|INFO|CORPUS_DONE|n=<cases>
```

## 5. 语料

- 作者语料 A：`python3 experiment/corpus/gen_corpus.py --all`（重写 5 个种子与 `SHA256SUMS`）；`--check` 只比对不写文件。每种子：F1–F9 各 20、L1–L5 各 24、M1 10、X1 10，共 320；用例顺序打乱，`case_id` 不携带类别信息；C 头只含请求字段。
- 生成器用草稿 oracle 复核每个用例的真值与首个违反条款，不一致即重抽（当前 5 个种子重抽次数均为 0）。
- 托付表在 `corpus/entrustments.json`，与 `gen/entrustments_gen.h` 同步生成；**修改托付表或生成器会改变哈希，属于偏离，须记入 `deviations.md`**。
- 草稿留出语料：`python3 experiment/corpus/holdout_draft.py`。正式留出语料须由独立标注人按同一 JSON 格式编写（`case_id` 建议从 9001 起），再用 `corpus_c.py` 生成头文件、写入 `SHA256SUMS`。

## 6. 独立标注人接手清单

1. 审阅 `oracle/rules_spec.md`，在版本记录中签字或提出修改（含 S-C1/S-C2 是否适用于只读查询、nonce 消耗语义、共签容量）。
2. **不看** `gatekeeper_field.c`，仅依据规格重写 `oracle/oracle.py`（保持 `evaluate_case(case, book)` 接口，以便生成器与分析脚本复用）。
3. 作者用 `oracle/kappa.py sample` 抽 ≥ 40 例盲标，`kappa.py score` 计算 κ（门槛 0.9）。
4. 标注人仅依据"核心合取式 + 非目标清单"编写留出语料 H（≥ 30 应拒、≥ 10 可放行），H 只运行一次。
5. 以上完成后重新生成语料、更新 `prereg.md` §7 哈希并打 `git tag prereg-v1`，然后才运行确证性矩阵。

## 7. 边界声明

1. 非临床：字段、语料、判决均为仿真；无出束、无厂商写使能、无设备写接口；`ALLOW` / `ALLOW_SIM` 都只是一行日志。
2. 门闩与客户端属 A 层演示代码，未经形式化验证；seL4/Microkit 属 K 层，仅引用其已有保证。不宣称 seL4 级应用证明。
3. 交付 ≠ 达成：任何结果不得表述为"使命达成"。
4. 共签为演示占位，不是电子签名或法规意义上的共签。
5. FNV-1a32 证据链无密钥、非抗碰撞；T5（无外部锚点）与 T7 预期不检出，属 U。
6. 结论范围仅限"本生成器与规格定义的用例总体"及类似的显式托付门闩场景。
