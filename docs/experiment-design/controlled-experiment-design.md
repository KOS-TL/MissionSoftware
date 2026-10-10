# 对照实验方案：使命流程 vs 传统流程

> **仓库化说明（v0.1.0）**：本文为项目过程中的历史文档，按原文收录，仅做去个人化处理：作者本机路径已替换为 `<REPO_ROOT>`（= 本仓库克隆目录，内含 `mission-shell/` 与 `microkit-sdk-2.3.1/`）、`<WORKDIR>`（作者文档目录）或仓库内相对路径；形如 `/workspace/...` 的路径是作者沙箱（box）上的历史路径，在本仓库中分别对应 `mission-shell/`（原 `/workspace/microkit-mission-shell/`）与 `docs/`。文中命令含占位符，**不能直接复制执行**；可直接执行的命令见仓库根目录 `README.md` 与 `docs/REPRODUCE.md`。


> 课题：使命软件工程学（Mission Software Engineering）· 毕设题目1 / S1 延伸
> 作者：chen peng · 文档版本 0.1（预注册草案）· 日期 2026-10-07（Asia/Shanghai）
> 实验对象：Microkit 使命约束外壳（`qemu_virt_aarch64`，Microkit SDK 2.3.1，Docker 镜像 `trustworthysystems/sel4:latest`）
> 源码树：`<REPO_ROOT>\mission-shell`（本机）/ `/workspace/microkit-mission-shell/`（沙箱镜像）
> 生命周期文档包：`docs/lifecycle/`
> 硬约束：**非临床 · 仅仿真 · 无写使能 · 不宣称 seL4 级应用证明 · 交付 ≠ 达成**

---

## 0. 摘要

本方案设计一项**配对对照实验**：同一套带独立真值标签的请求语料，分别送入两个 Microkit 系统映像——

- **B（传统流程）**：门闩只做功能有效性检查（输入格式、取值范围、枚举合法）、角色 ACL 与报文去重，测试按"功能 + 快乐路径"组织；
- **M（使命流程）**：在 B 的全部检查之上叠加使命层——人共签（默认 OFF、绑定托付）、托付对准检查（时间窗、禁区、范围、版本、来源）、U 非空声明、`delivery ≠ achievement` 语义、FNV-1a32 证据链。

主要观测量是**漏检**（应拒却放行）、**误拒**（应放行却拒绝）、**证据篡改检出**与**人工审查效率**。方案的关键设计选择是：作者自建语料上的"使命层全拦截"被预先声明为**低证据权重的操纵检查**；真正的验证性终点放在**由独立标注者在规则冻结后编写的留出语料（hold-out）**与**误拒非劣效检验**上，并给出会被判为"反对本方法"的明确结果。

---

## 1. 研究问题与假设

### 1.1 研究问题

| 编号 | 研究问题 |
|---|---|
| **RQ1 漏检** | 对于"格式合法、角色看似合法、但已不再对准人的托付"的请求（假使命），传统流程的门闩与测试会放行多少？使命层能否把它们拦下？拦截是否推广到作者没有预见的假使命（留出语料）？ |
| **RQ2 误拒 / 代价** | 使命层是否以显著提高误拒（合法请求被拒）为代价？它带来多少代码、需求条目、测试用例与运行时证据开销？ |
| **RQ3 审查与证据可对质性** | 使命流程产出的日志与证据链，是否让（a）机器能检出篡改、（b）人工审查者更快更准地指出"错误放行"并给出可对质的理由？ |
| **RQ4 可迁移性（预览）** | 假使命分类法与检查谓词能否在不改结构的情况下映射到第二个非临床玩具领域？（仅定性预览，不做推断性结论） |

### 1.2 记号

- 语料单元 *c*：一个自包含的请求场景（含前置步骤与一个被评分的目标请求）。
- 真值 `GT(c) ∈ {MUST_DENY, MAY_PERMIT}`，由独立规则规格 `oracle_spec`（§3.5）在运行前给定。
- 判决 `V_X(c) ∈ {PERMIT, DENY, INVALID}`，X ∈ {B, M, B+, M−k}。`PERMIT` 对 B 为 `ALLOW`，对 M 为 `ALLOW_SIM`；`INVALID` 表示日志缺失/不完整，**不得计为 DENY**。
- 漏检率 `FNR_X = P(V_X=PERMIT | GT=MUST_DENY)`；误拒率 `FPR_X = P(V_X=DENY | GT=MAY_PERMIT)`。

### 1.3 假设（零假设以可证伪方式陈述）

所有阈值在 §8 第 1 周写入预注册文件并打 git 标签后**冻结**，之后只可在"偏离记录"中说明修改，不可静默修改。

**H1（漏检，验证性，基于留出语料 H）**
- H1₀：在留出语料的 `MUST_DENY` 单元上，M 与 B 的漏检概率相同，即配对不一致对中 "B 放行而 M 拒绝"（b）与 "B 拒绝而 M 放行"（c）的概率相等（McNemar：P(b) = P(c)）。
- H1₁：b > c（使命层拦截更多）。
- 附加门槛（预注册）：即使 H1₀ 被拒绝，若 `FNR_M(H) ≥ 0.30`，仍判定"使命层推广性不足"（见 §7）。

**H1′（漏检，操纵检查，基于作者语料 A）**
- 预测：`FNR_M(A) = 0`，且在 ≥ 6 个"仅使命可拦"类别上 `FNR_B ≥ 0.9`。
- 说明：因作者同时编写规则与语料，此项近乎同义反复，**只用于确认实验装置工作**，不作为方法有效的证据。若此项失败（M 在自家语料上漏检），说明实现有缺陷，实验先停下修复，不进入主分析。

**H2（误拒 / 非劣效，验证性）**
- H2₀：`FPR_M − FPR_B ≥ Δ`，Δ = 5 个百分点（使命层误拒不可接受地更多）。
- H2₁：`FPR_M − FPR_B < Δ`。
- 判定：配对差的 95% 精确上置信界 < Δ 则拒绝 H2₀。合法语料规模取 n = 120，使得 0/120 时 Clopper–Pearson 双侧 95% 上界约 3.0%（< 5%）。

**H3（审查与证据，部分验证性）**
- H3a₀（机器篡改检出）：在篡改模型 T1–T4（§3.4）上，M 的证据链检出率不高于 B 的普通序号审计日志。
- H3b₀（人工审查）：审查者在 M 日志包上找出"错误放行"的 F1 分数与在 B 日志包上无差异（Wilcoxon 符号秩，双侧）；用时同理。H3b 因样本小，预先声明为**探索性**。

**H4（可迁移性预览）**：不设零假设；只报告分类法覆盖率（第二领域中可直接映射的类别数 / 总类别数）与需要新增的谓词数。

### 1.4 主次终点（防止事后挑选）

| 级别 | 终点 | 检验 |
|---|---|---|
| 主要（验证性） | P1：留出语料 H 上的配对漏检差异 | 精确 McNemar（单侧 α = 0.025） |
| 主要（验证性） | P2：合法语料 L 上的误拒非劣效 | 配对差精确置信区间 vs Δ = 5pp |
| 次要 | S1：作者语料 A 各类别漏检率（操纵检查） | 描述性 + Clopper–Pearson |
| 次要 | S2：篡改检出率 T1–T7 | 描述性 + Fisher 精确 |
| 次要 | S3：消融（M−k）的预测漏检是否出现 | 逐类别描述 |
| 探索性 | E1：人工审查 F1 / 用时 / 步骤 | Wilcoxon、效应量 r |
| 探索性 | E2：代码 / 规格增量成本 | 描述性 |
| 探索性 | E3：第二领域映射（RQ4） | 定性 |

---

## 2. 实验对象与处理条件

### 2.1 现状与必须先承认的问题

现有 `gatekeeper.c` 是**按请求标签判决**的：`REQ_EXPIRED_TRUST`（=2）这类标签本身就意味着"这是假使命"，门闩据标签直接 `deny("expired_entrustment")`。这对演示足够，但**不能**作为实验对象——否则"使命层拦住了过期托付"只是"门闩认出了写着'过期'的标签"，是同义反复。

因此实验需要**按字段判决**的新门闩：请求携带结构化字段，门闩根据其持有的托付记录与逻辑时钟进行谓词计算，**不读取任何揭示真值的标签**。两个条件使用**同一请求编码、同一客户端、同一语料**，只替换门闩实现。现有 `full | cosign_only | false_only` 剖面与其验收（`len=10`）保持不动，作为回归基线。

### 2.2 共用请求编码（实验分支新增，提案）

在 `mission_proto.h` 的实验扩展头（建议新文件 `experiment/mission_proto_exp.h`，不改原头文件）中定义：

```c
/* 实验扩展：非临床、仅仿真；不含任何写使能路径 */
#define REQ_CORPUS_EVAL        30u  /* 被评分的目标请求或前置请求 */
#define REQ_HARNESS_RESET      31u  /* 用例间复位共签/nonce 表（证据链不复位，记一条 harness_reset） */
#define REQ_HARNESS_CLOCK_SET  32u  /* 设置门闩逻辑时钟；仅实验剖面存在，并写入证据 */
#define REQ_CORPUS_DONE        33u

#define REP_ALLOW              16u  /* B 的放行（功能性"成功"） */
/* M 仍返回 REP_ALLOW_SIM(10)；两者都返回 REP_DENY(11) 表示拒绝 */

/* 消息寄存器布局（microkit_mr_set / microkit_mr_get） */
enum {
  MR_CASE_ID = 0,   /* 用例数字编号；仅用于日志关联，门闩不得据此判决 */
  MR_STEP_KIND,     /* 0=target（评分）, 1=setup（不评分） */
  MR_ACTION,        /* 1=ENABLE_SIM, 2=RECOMMEND, 3=QUERY_STATUS, 4=CLAIM_ACHIEVE */
  MR_ROLE,          /* 1=OPERATOR, 2=ADVISOR */
  MR_ORIGIN_ROLE,   /* 来源角色（玩具级来源标注；真实来源签名属 U） */
  MR_ENT_ID,        /* 托付编号 */
  MR_ENT_VER,       /* 托付版本 */
  MR_ZONE,          /* 目标区 0..15 */
  MR_SIM_LEVEL,     /* 仿真强度 0..1000（无物理含义） */
  MR_NONCE,         /* 非零 */
  MR_U_DECL,        /* 未覆盖项 U 的位掩码；0 = 声称"无未覆盖" */
  MR_COUNT
};
```

共签消息沿用 `REQ_HUMAN_COSIGN_GRANT/REVOKE/QUERY`（20/21/22），在实验剖面中 GRANT 额外携带 `MR_ENT_ID/MR_ENT_VER`，即**共签绑定到某一版托付**。

门闩内持有一张编译期生成的托付表（由语料生成器输出 `experiment/gen/entrustments_gen.h`）：

```c
typedef struct {
  uint16_t id, ver;
  uint32_t t_start, t_end;      /* 逻辑时间，闭区间 [t_start, t_end] */
  uint16_t allowed_zones;       /* 位掩码 */
  uint16_t forbidden_zones;     /* 位掩码，优先于 allowed */
  uint16_t sim_level_max;       /* 托付上限（≤ 设备范围 1000） */
  uint8_t  allowed_actions;     /* 位掩码 */
  uint8_t  superseded;          /* 1 = 已被更高版本取代 */
} entrustment_t;
```

### 2.3 条件 B：传统流程（公平基线，不是稻草人）

B 的设计原则：**凡是能从接口规格（类型、范围、枚举）与常规访问控制推导出的检查，B 都做；凡是需要"托付记录"才能推导的检查，B 不做。** 这一可操作定义同时给出了"传统"与"使命"的边界（见 §6.4 构念效度）。

`experiment/gatekeeper_baseline.c` 依次执行：

| 编号 | 检查 | 失败原因码 |
|---|---|---|
| B-1 | `MR_ACTION ∈ {1,2,3,4}`、`MR_ROLE ∈ {1,2}`、`MR_ORIGIN_ROLE ∈ {1,2}` | `invalid_enum` |
| B-2 | `MR_ZONE ≤ 15`、`MR_SIM_LEVEL ≤ 1000`、`MR_NONCE ≠ 0` | `invalid_range` |
| B-3 | `MR_ENT_ID` 存在于托付表（"引用了一个存在的工单号"），**不检查版本、时间、范围** | `unknown_ticket` |
| B-4 | 角色 ACL：`ENABLE_SIM` 与 `CLAIM_ACHIEVE` 需 `ROLE=OPERATOR`；`RECOMMEND/QUERY_STATUS` 任意角色 | `role_forbidden` |
| B-5 | nonce 去重（窗口内重复 nonce 拒绝，防精确重放） | `duplicate_nonce` |
| — | 通过以上 → `REP_ALLOW`，打印 `CASE|…|verdict=ALLOW|reason=ok` | — |

B 的日志：普通追加审计行 `AUDIT|seq=<n>|<event>`（有序号、无哈希）。B 对共签消息只记录 `AUDIT|cosign_msg_ignored`（传统系统中不存在"人共签托付"这一概念）。

B 的测试套件（作为"传统流程"的一部分被报告，不参与语料评分）：功能用例 + 快乐路径，约 10–15 条，覆盖 B-1…B-5 每条至少一正一反，即一个**合格的本科工程测试集**。

> 公平性自检：B 会正确拦截格式错误（M1）、顾问直接使能（F4）与精确重放（X1）。若 B 在这些类别上漏检，说明基线实现有缺陷，应先修复——**基线输给使命层的原因必须是缺少托付语义，而不是基线写得差。**

### 2.4 条件 M：使命流程（当前门闩语义的按字段重写）

`experiment/gatekeeper_mission_corpus.c` = B-1…B-5 **全部保留**，之后追加使命层谓词（顺序固定，首个失败即拒绝，原因码沿用并扩展现有命名）：

| 编号 | 使命谓词（对应核心合取式的哪一项） | 失败原因码 |
|---|---|---|
| M-1 | 存在有效共签，且绑定的 `(ent_id, ver)` 与请求一致（**明示托付**） | `no_human_cosign` / `cosign_binding_mismatch` |
| M-2 | `t_start ≤ now ≤ t_end`（**对准：时间**） | `expired_entrustment` / `entrustment_not_yet_valid` |
| M-3 | 目标区不在 `forbidden_zones`（**对准：禁区**） | `forbidden_zone` |
| M-4 | 目标区 ∈ `allowed_zones`、`sim_level ≤ sim_level_max`、动作 ∈ `allowed_actions`（**对准：范围**） | `scope_drift_zone` / `scope_drift_level` / `scope_drift_action` |
| M-5 | 请求版本 = 当前有效版本（`superseded = 0`）（**对准：参数新鲜**） | `stale_entrustment_version` |
| M-6 | 使能类动作的 `ORIGIN_ROLE = OPERATOR`（顾问不可使能，包括经转述） | `advisor_cannot_enable` |
| M-7 | `CLAIM_ACHIEVE` 一律拒绝；`ENABLE_SIM` 要求 `U_DECL ≠ 0`（**交付 ≠ 达成；U 非空**） | `empty_U_no_achieve_tag` / `achievement_not_claimable` |
| M-8 | 每次判决追加 FNV-1a32 证据（**检查可被证伪**） | — |
| — | 全部通过 → `REP_ALLOW_SIM`，并打印 `GATE|NOTE|sim_only; delivery!=achievement; non-clinical` | — |

M 的测试：B 的测试集 + 假使命集 + 共签开/关/撤销用例 + 证据链校验（即现有 `full` 剖面纪律的语料化版本）。

### 2.5 次要条件（消融与强化基线，可选但推荐）

| 条件 | 定义 | 目的 |
|---|---|---|
| **B+** | B + 全局（非按托付）时间窗 + 全局禁区表；无共签、无版本、无来源、无 U | 回答"使命层是否只是多写几条领域规则"：B+ 能拦的是**领域规则**，B+ 仍拦不住的才是**托付绑定**的增量 |
| **M−cosign** | M 去掉 M-1 | 预测：F9 漏检上升 |
| **M−align** | M 去掉 M-2…M-5 | 预测：F1/F2/F3/F7/F8 漏检上升 |
| **M−prov** | M 去掉 M-6 的 ORIGIN 部分 | 预测：F5 漏检上升 |
| **M−U** | M 去掉 M-7 | 预测：F6 漏检上升 |

消融用作**构念效度检查**：若去掉某组件后其"预测类别"的漏检**不**上升，说明语料并未真正测到该组件（或另一组件意外兜底），需在报告中如实说明。

### 2.6 控制变量

两条件共享：同一 `client_corpus.c`、同一语料文件（SHA-256 一致）、同一 SDK/板级/`debug` 配置、同一 Docker 镜像 digest、同一 QEMU 参数（`-machine virt,virtualization=on -cpu cortex-a53 -m size=2G`）。唯一自变量：`GATE_SRC`。

---

## 3. 场景语料设计

### 3.1 用例结构

每个用例是一个自包含脚本：

```
HARNESS_RESET
HARNESS_CLOCK_SET(now)
[COSIGN_GRANT(ent_id, ver) | COSIGN_REVOKE]*      ← 前置步骤（setup，不评分）
[CORPUS_EVAL(step_kind=setup, …)]*                ← 例如重放用例的"原始请求"
CORPUS_EVAL(step_kind=target, …)                  ← 唯一被评分的请求
```

用例间复位共签状态与 nonce 表，**证据链不复位**（整个运行一条链，复位本身记为 `harness_reset` 事件），因此用例之间独立，而证据链测试仍覆盖整次运行。

### 3.2 假使命分类法（请求级，9 类）

现有 4 类映射：`expired_entrustment` → F1；`forbidden_zone` → F3；`advisor_cannot_enable` → F4/F5；`empty_U_no_achieve_tag` → F6。

| 类别 | 名称 | 定义（违反核心合取式的哪一项） | 生成维度（变体如何产生） | B 预期 | M 预期 |
|---|---|---|---|---|---|
| **F1** | expired_entrustment | 托付时间窗已过：`now > t_end` | 超出量 1、小、大；托付编号；区/强度在范围内随机 | 放行（漏） | 拒 |
| **F2** | entrustment_not_yet_valid | 托付尚未生效：`now < t_start` | 提前量；同上 | 放行（漏） | 拒 |
| **F3** | forbidden_zone | 目标区在该托付禁区内（区号合法 0..15） | 禁区位置、托付、强度 | 放行（漏） | 拒 |
| **F4** | advisor_direct_enable | `ROLE=ADVISOR` 直接请求 `ENABLE_SIM` | 字段随机 | **拒（B-4 拦截）** | 拒 |
| **F5** | advisor_laundered | `ROLE=OPERATOR` 但 `ORIGIN_ROLE=ADVISOR` 的使能（顾问建议被原样转成操作员请求） | 字段随机 | 放行（漏） | 拒 |
| **F6** | empty_U_achieve | `CLAIM_ACHIEVE`（任何 U），或 `ENABLE_SIM` 且 `U_DECL=0` | 两子型各半 | 放行（漏） | 拒 |
| **F7** | scope_drift | 请求在设备范围内但超出托付范围：区 ∉ allowed（且不在禁区）/ 强度 ∈ (max, 1000] / 动作未被托付 | 三子型均分 | 放行（漏） | 拒 |
| **F8** | stale_parameter_replay | 新 nonce，但参数取自已被取代的托付版本 v1（v2 已生效且共签绑定 v2 或 v1 已撤销） | 版本差、参数差 | 放行（漏） | 拒 |
| **F9** | silent_default_enable | 未经明示共签的使能：从未 GRANT / REVOKE 之后 / 共签绑定的是另一托付 | 三子型均分 | 放行（漏） | 拒 |

### 3.3 对照类别（必须同时存在，否则无法测误拒与基线公平性）

| 类别 | 名称 | 定义 | GT | B 预期 | M 预期 |
|---|---|---|---|---|---|
| **L1** | legal_nominal | 共签绑定当前版本，时间窗内，允许区，强度 ≤ 上限，`U_DECL ≠ 0` | MAY_PERMIT | 放行 | ALLOW_SIM |
| **L2** | legal_boundary | 边界值：`now = t_start` 或 `now = t_end`；强度 = 上限；允许区的最高/最低位 | MAY_PERMIT | 放行 | ALLOW_SIM |
| **L3** | legal_advisor_recommend | 顾问的 `RECOMMEND`（非使能动作），托付内 | MAY_PERMIT | 放行 | ALLOW_SIM |
| **L4** | legal_regrant | REVOKE → 新托付版本 v2 GRANT → 按 v2 参数请求 | MAY_PERMIT | 放行 | ALLOW_SIM |
| **L5** | legal_multi_entrustment | 多托付并存，请求对准其中有效的一个 | MAY_PERMIT | 放行 | ALLOW_SIM |
| **M1** | malformed | 枚举/范围/nonce=0 违例 | MUST_DENY | 拒 | 拒 |
| **X1** | exact_replay | 同一用例内原样重放此前已放行的请求（重复 nonce） | MUST_DENY | 拒（B-5） | 拒 |

L2 是误拒的主要"陷阱"：闭区间写成开区间、`<` 写成 `≤` 这类实现错误只会在边界上暴露。L3 检验 M-6 是否误伤顾问的非使能动作。

### 3.4 证据篡改轨道（离线，T1–T7）

篡改**不在 seL4 内进行**，而是在主机上对已采集的串口日志副本施加变换（`tamper.py`），然后由 `verify-chain`（M）或 `verify-seq`（B）检测。每种篡改每份日志生成 20 个随机位置变体。

| 编号 | 篡改 | 攻击者模型 | B（序号日志）预期 | M（FNV 链）预期 |
|---|---|---|---|---|
| T1 | 修改某条事件文本（如 `DENY`→`ALLOW_SIM` 的原因码） | 朴素 | 不检出 | 检出 |
| T2 | 删除中间一条 | 朴素（不重编号） | 检出（序号缺口） | 检出 |
| T3 | 交换相邻两条 | 朴素 | 检出（序号逆序） | 检出 |
| T4 | 插入一条伪造行（随机哈希） | 朴素 | 视序号而定 | 检出 |
| T5 | 截尾（删除最后 k 条） | 朴素 | 不检出 | **无外部锚点时不检出**；有锚点（tip/len 另存）时检出 |
| T6 | 删除中间一条并**重新编号** | 知情 | 不检出 | 检出 |
| T7 | 修改后**重算整条 FNV 链** | 知情（知道算法；无密钥） | 不检出 | **不检出**（教学级链无密钥，属 U） |

T5/T7 被预先写成"M 预期失败"，这是对 P/U 边界的诚实标注：FNV-1a32 链只提供"顺序追加可复核"的教学语义，不提供密码学抗伪造。外部锚点 = 运行结束时 `REQ_EVIDENCE_TIP` 打印的 `tip/len`，由实验者在采集时另行登记（如写入运行清单并计算其 SHA-256）。

### 3.5 真值标注：独立规则规格先于运行

1. **`oracle_spec.md`（规则规格）**：以自然语言 + 判定表写明每条 MUST_DENY 条款（编号 S-1…S-n），**只引用请求字段与托付表**，不引用门闩源码。由作者起草、独立标注者审阅签字。
2. **`oracle.py`（参考判定器）**：由**独立标注者**（同学或指导教师指定人员，非作者）依据 `oracle_spec.md` 编写，不得查看 `gatekeeper_*.c`。输出每个用例的 `GT` 与违反条款号。
3. **双标一致性**：作者对随机抽取的 ≥ 40 个用例独立手标，与 `oracle.py` 计算 Cohen's κ；预注册门槛 κ ≥ 0.9，否则先修订规格再标注。
4. **冻结**：生成语料 → 运行 `oracle.py` 写入 `GT` → 计算 `corpus.json` 的 SHA-256 → 写入预注册文件并 `git tag prereg-v1`。**此后才允许构建与运行实验映像。**
5. **规格缺口记录**：留出语料中若出现规格未覆盖的情形，标注者依据核心原则给出真值并附理由，标记 `spec_gap=true`，在分析中单列，不静默并入。

### 3.6 变体生成与种子

- 生成器 `gen_corpus.py --seed <S> --n-per-cat <N>`，使用 `random.Random(S)`（Python 标准库，确定性）。
- 每个类别有一个**模板**（固定违反条款）与若干**自由维度**（托付编号、区、强度、时间偏移、nonce、U 掩码、子型）；自由维度在"不改变真值"的约束内采样，生成后由 `oracle.py` 复核真值，若复核不一致则丢弃重抽并计数。
- 规模（作者语料 A）：F1–F9 各 N = 20（共 180），L1–L5 各 24（共 120），M1、X1 各 10，合计 320 个用例/种子。
- 种子：预注册 5 个种子 `{20261007, 20261008, 20261009, 20261010, 20261011}`。种子用于**语料重采样**（检验结论是否依赖特定样本），不是运行重复。
- **留出语料 H**：规则冻结后，由独立标注者仅依据"核心合取式 + 非目标清单"（不看分类法表 §3.2 的子型、不看源码）自由编写 ≥ 30 个假使命与 ≥ 10 个合法对照，按同一编码提交。H 只运行一次，结果不得用于回改规则（若回改，必须另造 H′ 重测并在报告中披露）。

---

## 4. 指标

### 4.1 判决类指标（每条件、每类别、每种子）

| 指标 | 定义 | 备注 |
|---|---|---|
| 漏检率 FNR | `#(PERMIT ∧ MUST_DENY) / #MUST_DENY` | 主指标（RQ1） |
| 误拒率 FPR | `#(DENY ∧ MAY_PERMIT) / #MAY_PERMIT` | 主指标（RQ2） |
| 原因码正确率 | M 拒绝时原因码是否对应 `oracle` 给出的违反条款 | 拒得对但理由错，同样削弱"可对质性" |
| 无效率 | `#INVALID / #cases` | 必须为 0，否则该次运行作废重跑并记录 |
| 确定性 | 同条件同种子 R 次运行的 `CASE|` 行逐字节一致 | 预期 100% 一致 |

### 4.2 证据完整性指标（RQ3a）

- 每种篡改 T1–T7 的检出率（检出 = 校验器报告首个不一致位置；位置偏差记录）。
- 漏报（篡改未检出）与误报（未篡改日志被判篡改，期望 0）。
- 回归锚点：用主机重实现的 FNV-1a32 对现有 `full` 剖面计算的预测值为 `tip=80488a97, len=10`（在主机上以 `gatekeeper.c` 同一函数编译验证与 Python 实现一致）；第 3 周用真实串口日志确认该值，作为解析器正确性的 V0 检查。

### 4.3 人工审查小型研究（RQ3b，探索性）

- **参与者**：6–10 名计算机专业学生（非作者、未参与标注），自愿、知情同意，不采集个人敏感信息；全部材料为非临床仿真。如学校要求，先经导师/学院确认是否需伦理备案。
- **材料**：每人两份日志包，各含 20 条判决，其中植入 5 条"错误放行"（来自 B 对 F 类的放行或人为注入）与 1 处篡改段。B 包为 `CASE + AUDIT` 行，M 包为 `CASE + EVIDENCE` 行；两包都附同一份 `oracle_spec.md`。
- **设计**：被试内交叉，AB/BA 平衡；两套不同用例集 S1/S2 与条件做拉丁方配对，避免学习效应与材料效应混淆。
- **任务**：（1）标出所有不应放行的判决并写出违反的规格条款号；（2）判断日志是否被篡改、指出位置。
- **测量**：F1 分数、用时（计时器）、人工步骤数（查规格次数 + 翻日志跳转次数，以有声思维或操作清单计）、主观信心（1–5）。
- **混杂说明**：M 日志的原因码更丰富——这本身就是处理的一部分；但为避免"仅仅是信息量"的指责，B 日志同样带其检查的原因码（`invalid_range` 等）。
- **预演**：1 名试点被试，只用于调整材料，不计入数据。

### 4.4 代码 / 规格增量成本（RQ2 代价）

| 指标 | 采集方式 |
|---|---|
| 门闩 LOC（非空非注释） | `cloc gatekeeper_baseline.c gatekeeper_mission_corpus.c` |
| 需求条目数 | B 的 SRS 条目（B-1…B-5 及非目标） vs M 的条目（再加 M-1…M-8、R1–R5） |
| 测试用例数 | B 测试集 vs M 测试集 |
| ELF 体积 | `aarch64-linux-gnu-size build/gatekeeper.elf` |
| 每请求日志开销 | 每个被评分请求产生的串口字节数（B 的 AUDIT vs M 的 EVIDENCE） |
| 作者工时 | 每个工作包开始/结束登记（自报，精度有限） |

运行时周期开销不作为指标（QEMU 计时不代表真实硬件，属 U）。

---

## 5. 实验流程

### 5.1 目录与新增文件（实验分支 `exp/controlled-v1`，仅新增，不改现有文件语义）

```
mission-shell/
├── gatekeeper.c, mission_proto.h, scenarios/client_*.c, mission.system   ← 不动
├── Makefile                      ← 仅新增剖面分支（见 5.2），原三剖面行为不变
└── experiment/
    ├── prereg.md                 预注册（假设、阈值、种子、语料 SHA-256）
    ├── oracle_spec.md            独立规则规格
    ├── oracle.py                 独立标注者实现的参考判定器
    ├── gen_corpus.py             语料生成器 → corpus/*.json + gen/*.h
    ├── mission_proto_exp.h       §2.2 编码
    ├── gatekeeper_baseline.c     条件 B（及 B+ 通过 -DBASELINE_PLUS）
    ├── gatekeeper_mission_corpus.c  条件 M（消融通过 -DABLATE_COSIGN 等宏）
    ├── scenarios/client_corpus.c 读取 gen/corpus_gen.h 逐用例发起 PPC
    ├── docker_corpus_run.sh      构建 + QEMU + 落盘日志
    ├── parse_serial.py           解析、校验、篡改、评分（见附录 B）
    ├── stats.py                  列联表、精确检验、置信区间
    └── runs/<condition>/<seed>/<rep>.log  + manifest.json
```

`mission.system` 无需修改：PD 名仍为 `gatekeeper`/`client`，只是链接的目标文件不同。

### 5.2 新 DEMO_PROFILE（Makefile 增量，提案）

```make
else ifeq ($(DEMO_PROFILE),baseline_corpus)
  CLIENT_SRC := experiment/scenarios/client_corpus.c
  GATE_SRC   := experiment/gatekeeper_baseline.c
else ifeq ($(DEMO_PROFILE),mission_corpus)
  CLIENT_SRC := experiment/scenarios/client_corpus.c
  GATE_SRC   := experiment/gatekeeper_mission_corpus.c
else ifeq ($(DEMO_PROFILE),baselineplus_corpus)
  CLIENT_SRC := experiment/scenarios/client_corpus.c
  GATE_SRC   := experiment/gatekeeper_baseline.c
  GATE_DEFS  := -DBASELINE_PLUS
# 消融：mission_corpus + ABLATE=cosign|align|prov|U → GATE_DEFS := -DABLATE_$(ABLATE)
```

原有三个剖面默认 `GATE_SRC := gatekeeper.c`；`gatekeeper.o` 规则改为编译 `$(GATE_SRC)` 并依赖 `experiment/gen/*.h`。**回归门禁**：改动后 `DEMO_PROFILE=full` 仍须得到 `GATE|CHAIN|tip=80488a97|len=10`（以真实日志确认后的值为准）与 `MISSION_SHELL_DEMO_DONE`。

`client_corpus.c` 要点：
- 遍历 `corpus_steps[]`，每步 `microkit_mr_set(i, …)` 后 `microkit_ppcall(GATE_CH, microkit_msginfo_new(label, MR_COUNT))`；
- 每个目标请求后打印 `CLIENT|REP|case=<id>|label=<rep>`（客户端侧回执，与门闩侧 `CASE|` 行交叉核对）；
- 结束时发 `REQ_EVIDENCE_TIP`，打印 `CLIENT|INFO|CORPUS_DONE|n=<cases>`。
- 若语料头文件过大导致 PD 内存不足（检查 `build/report.txt`），按 `CORPUS_SHARD=k/K` 分片运行，每片一份日志，分析时合并。

门闩侧每个被评分请求打印一行（解析的唯一判决来源）：

```
CASE|id=<num>|kind=target|verdict=<ALLOW|ALLOW_SIM|DENY>|reason=<code>
```

### 5.3 Docker 命令模式

Windows 主机（与现有 README 一致的挂载方式；以下为 cmd 交互写法，写进 `.bat` 时循环变量需写作 `%%C`/`%%R`）：

```bat
set SEED=20261007
for %C in (baseline_corpus mission_corpus) do (
  for %R in (1 2 3) do (
    docker run --rm -e DEMO_PROFILE=%C -e CORPUS_SEED=%SEED% -e QEMU_TIMEOUT=120 ^
      -v <REPO_ROOT>:/work -w /work/mission-shell ^
      trustworthysystems/sel4:latest bash /work/mission-shell/experiment/docker_corpus_run.sh ^
      > experiment\runs\%C\%SEED%\r%R.log 2>&1
  )
)
```

Linux / 沙箱：

```bash
for C in baseline_corpus mission_corpus; do for S in 20261007 20261008 20261009 20261010 20261011; do for R in 1 2 3; do
  mkdir -p experiment/runs/$C/$S
  docker run --rm -e DEMO_PROFILE=$C -e CORPUS_SEED=$S -e QEMU_TIMEOUT=120 \
    -v "$PWD/..":/work -w /work/mission-shell trustworthysystems/sel4:latest \
    bash /work/mission-shell/experiment/docker_corpus_run.sh > experiment/runs/$C/$S/r$R.log 2>&1
done; done; done
```

`docker_corpus_run.sh` 相对现有 `docker_build_run.sh` 的差异：（1）先运行 `gen_corpus.py --seed $CORPUS_SEED` 并校验 `corpus.json` 的 SHA-256 与 `prereg.md` 一致，不一致即退出；（2）QEMU 超时可配置（默认 120 s）；（3）在日志头写入 `RUN|profile|seed|image_digest|git_rev|corpus_sha256`；（4）`rc=124`（超时收尾）可接受，但必须见到 `CORPUS_DONE`，否则判为 INVALID。

### 5.4 运行矩阵与重复

| 条件 | 种子 | 重复 R | 运行次数 |
|---|---|---|---|
| B、M | 5 | 3 | 30 |
| B+、M−cosign、M−align、M−prov、M−U | 1（首个种子） | 1 | 5 |
| B、M 于留出语料 H | — | 3 | 6 |
| `full` 回归 | — | 1 | 1 |

重复 R 的作用是**确认确定性**（系统无随机源，预期逐字节一致），不是增加统计样本。一旦确认一致，同一 (条件, 种子) 的 R 次运行在分析中只计一次。

### 5.5 解析与分析流水线

```
parse_serial.py parse   → results/<cond>_<seed>.csv（case_id, verdict, reason）
parse_serial.py verify-chain / verify-seq → 证据一致性（未篡改日志必须通过）
parse_serial.py tamper  → 生成 T1–T7 变体并检测
parse_serial.py score   → 与 corpus.json 的 GT 合并，输出混淆矩阵
stats.py                → §6 所述全部表格与检验
```

### 5.6 边界纪律（实验期间）

- 不新增任何写使能、出束、设备写接口；`ALLOW_SIM` 仍是唯一放行形态（M），B 的 `ALLOW` 也只是一行日志，不驱动任何东西。
- 不把任何结果表述为"使命达成"或"应用已被证明"。
- 语料中的"强度""区"均为无物理含义的仿真字段。

---

## 6. 统计分析

### 6.1 分析单元与推断对象

- 系统是确定性的：同一输入必然同一输出。因此**p 值不描述运行噪声**，而描述"从生成器定义的变体总体中抽到这批用例"的抽样不确定性。推断对象 = 生成器 + 规格所定义的用例总体，这一点必须在报告中明说，不得外推到"真实世界的假使命"。
- 同一类别内的变体共享违反条款，高度相关；因此同时报告两个层级：
  - **变体层**（n 大，精度看起来高，但存在聚类）；
  - **类别层**（K 个类别，每类一个"是否被拦截"的汇总判断，更保守）。

### 6.2 列联表

每个类别、每个种子输出配对 2×2 表（行：B 判决；列：M 判决）：

|  | M = DENY | M = PERMIT |
|---|---|---|
| **B = DENY** | a（都拦） | c（只有 B 拦） |
| **B = PERMIT** | b（只有 M 拦） | d（都放） |

对 MUST_DENY 用例，`b` 是使命层的"增量拦截"，`c` 是使命层的"倒退"（预期 0，出现即需逐个解释），`d` 是两者共同漏检。

### 6.3 检验与区间

| 用途 | 方法 | 说明 |
|---|---|---|
| P1：配对漏检差异 | **精确 McNemar**（对 b+c 个不一致对做 Binomial(0.5) 检验） | 配对设计下这是正确检验；Fisher 精确检验假设两组独立，**不适用于同一语料的两条件比较**，仅作对照报告 |
| 不一致对很少时的示例 | b=20,c=0：双侧 p ≈ 1.9×10⁻⁶；b=6,c=0：p ≈ 0.031；b=5,c=0：p ≈ 0.063 | 由此预注册：留出语料至少需 ≥ 30 个 MUST_DENY 用例 |
| 比例置信区间 | **Clopper–Pearson** 精确 95% CI | 0/20 → 上界 16.8%；0/60 → 5.96%；0/120 → 3.03% |
| P2：配对误拒差 | 精确配对差 CI（基于 b、c 的条件二项，或 Tango/Newcombe 配对方法） | 上界 < 5pp 则非劣效成立 |
| 独立组比较 | **Fisher 精确检验** | 用于：M 在 A vs H 上的漏检率比较；篡改检出 B vs M（不同日志格式、按变体独立）；人工研究中不配对的次级比较 |
| 类别层 | 符号检验：K 个"仅使命可拦"类别中 M 胜的个数 | 8 类全胜：p ≈ 0.0078；需 ≥ 6 类全胜方可在双侧 0.05 下显著 |
| 多重比较 | 逐类别检验用 **Holm** 校正 | 主终点 P1、P2 不校正（已预注册且各为一族） |
| 人工研究 | Wilcoxon 符号秩（配对）、效应量 r = Z/√n，报告中位数与 IQR | n ≤ 10，只作探索；同时报告每位被试的原始数据 |
| 一致性 | Cohen's κ（标注一致性） | 门槛 κ ≥ 0.9 |

### 6.4 为什么小样本可以接受

1. **预期效应极大**：在仅使命可拦类别上，预测是 B 近 100% 漏检、M 近 0% 漏检；精确检验在 n = 20 时即可给出 p < 10⁻⁵，小样本足以检出这样的效应。
2. **使用精确方法**：Clopper–Pearson、精确 McNemar、Fisher 都不依赖大样本近似，n 小时仍然有效。
3. **误拒用"非劣效 + 上界"表述**：不需要观察到误拒才能下结论；n = 120 时 0 误拒即可把上界压到约 3%。
4. **真正的样本瓶颈是类别数和留出语料**，不是变体数。把 N 从 20 加到 200 只会让变体层 CI 更窄，不会提高外部效度——报告中必须说明这一点，避免"大 N 假精度"。

### 6.5 效度威胁与缓解

**内部效度**

| 威胁 | 缓解 |
|---|---|
| 规则与语料出自同一作者（自证循环） | 真值由独立标注者依据独立规格实现 `oracle.py`；自家语料结果降级为操纵检查；验证性终点放在独立编写的留出语料 H；预注册并打 git 标签 |
| 门闩按标签判决（同义反复） | 按字段判决的新门闩；`MR_CASE_ID` 只用于日志关联，代码审查确认门闩不读取它做判决（`rg MR_CASE_ID experiment/gatekeeper_*.c` 只应出现在打印语句中） |
| 基线写得差（稻草人） | §2.3 的可操作定义；B 必须拦截 M1/F4/X1；B 的测试集由独立同学评审；报告 B+ 条件 |
| 实现缺陷混入结果 | `oracle.py` 与门闩各自独立实现，任何分歧逐条人工裁决并记录 |
| 日志缺失被当作 DENY | INVALID 单列，非零即作废重跑 |
| 研究者自由度（事后改阈值/挑类别） | 主次终点、阈值、种子、语料哈希预注册；偏离写入 `deviations.md` |

**构念效度**

| 威胁 | 缓解 |
|---|---|
| "漏检"其实是"基线缺需求"——这是否只是在比较两份需求文档？ | 承认并明确主张：使命 SE 的作用正是**系统性地诱导出**托付相关需求；实验测的是这一纪律的后果，而非某种运行时魔法。B+ 进一步把"多写领域规则"与"绑定托付"分开 |
| 玩具字段（`ORIGIN_ROLE`、`U_DECL`）是自报的，真实攻击者可伪造 | 明确为 U：真实来源签名、真实身份认证不在本实验范围；实验只测"若这些字段可信，检查是否到位" |
| 共签为演示占位 | 同上，属 U；不宣称电子签名/法规共签 |
| FNV-1a32 不是密码学哈希 | T7 被预先写成预期失败，结果单列为 U 的佐证 |
| 消融未出现预测漏检 | 如实报告为"语料未测到该组件"，不解释成"组件不必要" |

**外部效度**

| 威胁 | 缓解 |
|---|---|
| 玩具领域、两 PD、单客户端 | 结论措辞限定于"在此类显式托付的门闩场景中"；RQ4 第二领域仅作定性预览 |
| QEMU 而非真硬件 | 判决逻辑与硬件无关；性能/时序不作结论 |
| 参与者为学生 | 人工研究只作探索性 |

**结论效度**：确定性系统 + 精确检验；避免把变体层 p 值当作对真实世界的推断。

---

## 7. 预期结果与可证伪条件

### 7.1 预期结果（预注册预测）

| 类别 | B 漏检率 | B+ 漏检率 | M 漏检率 |
|---|---|---|---|
| F1、F2 | ≈ 100% | ≈ 0–100%（取决于全局窗是否覆盖） | 0% |
| F3 | ≈ 100% | 部分（仅全局禁区覆盖的部分） | 0% |
| F4 | 0% | 0% | 0% |
| F5、F6、F7、F8、F9 | ≈ 100% | ≈ 100% | 0% |
| M1、X1 | 0% | 0% | 0% |
| L1–L5（误拒率） | 0% | 0% | 0%（L2 边界最敏感） |
| 留出语料 H | 高 | 高 | 低，但**不预测为 0**（预期会出现 `spec_gap`） |
| 篡改 T1–T4、T6 | 部分 | — | 100% |
| 篡改 T5（无锚点）、T7 | 0% | — | 0%（预期失败，属 U） |

### 7.2 会被判为"反对本方法"的结果（预注册，任一成立即在结论中如实写明）

| 编号 | 条件 | 含义 |
|---|---|---|
| **X-1** | 留出语料 H 上 McNemar 不显著（单侧 α = 0.025），或 `FNR_M(H) ≥ 30%` | 使命层只拦住了作者预见到的假使命，**不推广**；方法主张至多是"作者自己的检查清单" |
| **X-2** | 误拒非劣效不成立：`FPR_M − FPR_B` 的 95% 上界 ≥ 5pp，或 L2 某一边界子型系统性被拒 | 使命层以可用性为代价换安全，"不增加误拒"的主张失败 |
| **X-3** | B+ 在 F1–F9 上拦截了 M 所拦截的 ≥ 80% | 增量主要来自"多写几条领域规则"，而非托付绑定/共签/U 等使命结构；方法的独特性主张被削弱 |
| **X-4** | M 出现 `c > 0`（B 拦住而 M 放行） | 使命层引入了回退，实现或方法存在结构问题 |
| **X-5** | 证据链在 T1–T4 上检出率不高于序号日志（Fisher 不显著） | "检查可被证伪"在证据层未落地 |
| **X-6** | 人工研究中 M 日志的 F1 中位数不高于 B，且用时更长 | 证据可对质性在人这一侧没有收益（探索性，作为弱反证据报告） |
| **X-7** | 代码增量 > 3 倍基线 LOC，而 X-1 同时成立 | 代价高且收益不推广 |

明确声明：**作者语料 A 上 M 全拦截不计为支持方法的证据**；若只有 A 上的结果为正、而 X-1 成立，结论应写为"使命层在本玩具中未显示推广收益"。

---

## 8. 实施计划（约 6 周，对接毕设题目1）

| 周 | 工作包 | 交付物 | 门禁 |
|---|---|---|---|
| W1 | 规格与预注册：`oracle_spec.md`、请求编码、B/M 判定表、假设与阈值；确定独立标注者 | `prereg.md` 草案、`oracle_spec.md` v1（标注者签字） | 导师审阅 |
| W2 | 生成器 + 独立 `oracle.py`；κ 双标；语料冻结；`git tag prereg-v1` | `corpus/seed-*.json`、语料 SHA-256、κ 报告 | κ ≥ 0.9；标签已打 |
| W3 | 实现 `gatekeeper_baseline.c`、`gatekeeper_mission_corpus.c`、`client_corpus.c`、Makefile 剖面、`docker_corpus_run.sh`、`parse_serial.py`；B/M 各自测试集 | 可运行映像；V0：`full` 回归 tip/len 与主机预测一致 | `full` 回归通过；B 拦截 M1/F4/X1 |
| W4 | 主运行矩阵（30 次）+ 确定性检查 + 消融/B+（5 次）+ 篡改轨道；独立标注者编写留出语料 H 并运行（6 次） | `runs/`、`results/*.csv`、混淆矩阵 | INVALID = 0 |
| W5 | 人工审查研究（试点 1 人 + 正式 6–10 人）；成本指标采集 | 匿名化原始数据、计时表 | 知情同意齐全 |
| W6 | 统计分析、反证条件逐条判定、论文实验章、复现包 | `stats.py` 输出、实验报告、`deviations.md`、复现包（镜像 digest + 命令 + 哈希） | 导师审阅 |

**论文对接**：本实验构成题目1"基于 Microkit 的使命约束外壳"的评价章节——在原有"可跑通的约束外壳 + 生命周期文档包"之上，补上"与传统流程相比，它究竟多拦住了什么、代价多少、哪些拦不住"的定量证据。时间紧时的裁剪顺序：先砍 RQ4 → 再砍消融（保留 B+）→ 再把人工研究降为 3 人试点；**留出语料 H 与误拒非劣效不可砍**，否则实验失去验证性。

---

## 9. 边界声明

1. **非临床**：语料、字段、判决均为仿真；不出束、无厂商写使能、无注册材料、无真实剂量或联锁逻辑。
2. **不宣称 seL4 级应用证明**：seL4/Microkit 属 K 层，仅引用其已有保证；门闩与客户端属 A 层，为演示代码，**未经形式化验证**。形式化方法在本课题中只被当作条件保证 P，并伴随显式未覆盖集 U。
3. **交付 ≠ 达成**：`ALLOW_SIM` 只表示"在本仿真中允许继续"，任何结果都不得表述为使命达成。
4. **共签为演示占位**：不是电子签名或法规意义上的共签系统。
5. **证据链为教学级**：FNV-1a32 无密钥、非抗碰撞；T7 预期失败已写入 U。
6. **结论范围**：结论只适用于"由本生成器与规格定义的用例总体"及类似的显式托付门闩场景，不外推到真实系统的假使命发生率。
7. **显式未覆盖集 U（本实验）**：真实来源认证与签名、真实时钟与时间源可信性、密码学强度的证据、真硬件与时序、多客户端并发、恶意 PD、人在真实压力下的审查行为、第二领域的定量结论。
8. **源码纪律**：本方案不修改现有 `gatekeeper.c`、`mission_proto.h`、`scenarios/client_*.c`、`mission.system` 的语义；所有实验代码均在 `experiment/` 下新增，并以 `full` 剖面回归作为门禁。

---

## 附录 A：具体场景表（作者语料 A 的代表性用例 + 留出语料示例）

记号：托付 E1 v1 = `{t:[100,200], allowed_zones:{1,2,3}, forbidden_zones:{7}, sim_level_max:300, actions:{ENABLE_SIM, RECOMMEND, QUERY_STATUS}}`；E1 v2 = 同 E1 但 `sim_level_max:200`，生效后 v1 标记为 superseded；E2 v1 = `{t:[150,400], allowed_zones:{4,5}, forbidden_zones:{7}, sim_level_max:500, actions:{RECOMMEND}}`。"GRANT(E1v1)"表示共签绑定 E1 v1。未注明时 `ROLE=ORIGIN=OPERATOR`、`U_DECL=0b0001`、`now=150`、nonce 新。B 列中"放行"即漏检（对 MUST_DENY）。

| ID | 类别 | 描述（前置 → 目标请求） | 真值 | B 预期 | M 预期（原因码） |
|---|---|---|---|---|---|
| A-F1-001 | F1 过期托付 | GRANT(E1v1)；now=201；ENABLE_SIM zone=2 level=100 | MUST_DENY | ALLOW（漏） | DENY `expired_entrustment` |
| A-F1-002 | F1 | GRANT(E1v1)；now=5000；同上 | MUST_DENY | ALLOW（漏） | DENY `expired_entrustment` |
| A-F2-001 | F2 未生效 | GRANT(E1v1)；now=99；ENABLE_SIM zone=1 | MUST_DENY | ALLOW（漏） | DENY `entrustment_not_yet_valid` |
| A-F3-001 | F3 禁区 | GRANT(E1v1)；ENABLE_SIM zone=7 level=50 | MUST_DENY | ALLOW（漏） | DENY `forbidden_zone` |
| A-F4-001 | F4 顾问直接使能 | GRANT(E1v1)；ROLE=ADVISOR ENABLE_SIM zone=1 | MUST_DENY | DENY `role_forbidden` | DENY `role_forbidden` |
| A-F5-001 | F5 顾问转述 | GRANT(E1v1)；ROLE=OPERATOR ORIGIN=ADVISOR ENABLE_SIM zone=1 | MUST_DENY | ALLOW（漏） | DENY `advisor_cannot_enable` |
| A-F6-001 | F6 空 U 声称达成 | GRANT(E1v1)；CLAIM_ACHIEVE U_DECL=0 | MUST_DENY | ALLOW（漏） | DENY `empty_U_no_achieve_tag` |
| A-F6-002 | F6 达成不可声称 | GRANT(E1v1)；CLAIM_ACHIEVE U_DECL=0b0011 | MUST_DENY | ALLOW（漏） | DENY `achievement_not_claimable` |
| A-F6-003 | F6 使能时声称 U 为空 | GRANT(E1v1)；ENABLE_SIM zone=1 U_DECL=0 | MUST_DENY | ALLOW（漏） | DENY `empty_U_no_achieve_tag` |
| A-F7-001 | F7 范围漂移：区 | GRANT(E1v1)；ENABLE_SIM zone=5（合法区号、不在禁区、不在 allowed） | MUST_DENY | ALLOW（漏） | DENY `scope_drift_zone` |
| A-F7-002 | F7 范围漂移：强度 | GRANT(E1v1)；ENABLE_SIM zone=1 level=301（≤1000） | MUST_DENY | ALLOW（漏） | DENY `scope_drift_level` |
| A-F7-003 | F7 范围漂移：动作 | GRANT(E2v1)；ENABLE_SIM zone=4（E2 只托付 RECOMMEND） | MUST_DENY | ALLOW（漏） | DENY `scope_drift_action` |
| A-F8-001 | F8 过期参数重放 | E1v2 生效；GRANT(E1v2)；ENABLE_SIM ent=E1 ver=1 level=280（新 nonce） | MUST_DENY | ALLOW（漏） | DENY `cosign_binding_mismatch` 或 `stale_entrustment_version`（规格须固定优先级） |
| A-F8-002 | F8 | GRANT(E1v1)；REVOKE；E1v2 生效；GRANT(E1v2)；按 v1 参数且 ver=1 请求 | MUST_DENY | ALLOW（漏） | DENY `stale_entrustment_version` |
| A-F9-001 | F9 从未共签 | （无 GRANT）ENABLE_SIM zone=1 | MUST_DENY | ALLOW（漏） | DENY `no_human_cosign` |
| A-F9-002 | F9 撤销后 | GRANT(E1v1)；REVOKE；ENABLE_SIM zone=1 | MUST_DENY | ALLOW（漏） | DENY `no_human_cosign` |
| A-F9-003 | F9 共签张冠李戴 | GRANT(E2v1)；ENABLE_SIM ent=E1 zone=1 | MUST_DENY | ALLOW（漏） | DENY `cosign_binding_mismatch` |
| A-L1-001 | L1 合法 | GRANT(E1v1)；ENABLE_SIM zone=2 level=100 | MAY_PERMIT | ALLOW | ALLOW_SIM（附 sim_only 注记） |
| A-L2-001 | L2 边界：窗口末 | GRANT(E1v1)；now=200；ENABLE_SIM zone=3 level=300 | MAY_PERMIT | ALLOW | ALLOW_SIM |
| A-L2-002 | L2 边界：窗口首 | GRANT(E1v1)；now=100；ENABLE_SIM zone=1 level=0 | MAY_PERMIT | ALLOW | ALLOW_SIM |
| A-L3-001 | L3 顾问建议 | GRANT(E1v1)；ROLE=ADVISOR ORIGIN=ADVISOR RECOMMEND zone=2 | MAY_PERMIT | ALLOW | ALLOW_SIM |
| A-L4-001 | L4 重新托付 | GRANT(E1v1)；REVOKE；E1v2 生效；GRANT(E1v2)；ENABLE_SIM ver=2 level=200 | MAY_PERMIT | ALLOW | ALLOW_SIM |
| A-L5-001 | L5 多托付 | GRANT(E2v1)；now=300；ROLE=OPERATOR RECOMMEND ent=E2 zone=4 | MAY_PERMIT | ALLOW | ALLOW_SIM |
| A-M1-001 | M1 格式错 | ENABLE_SIM zone=16 | MUST_DENY | DENY `invalid_range` | DENY `invalid_range` |
| A-M1-002 | M1 格式错 | ACTION=9 | MUST_DENY | DENY `invalid_enum` | DENY `invalid_enum` |
| A-X1-001 | X1 精确重放 | GRANT(E1v1)；[setup] ENABLE_SIM nonce=77；[target] 原样再发 nonce=77 | MUST_DENY | DENY `duplicate_nonce` | DENY `duplicate_nonce` |
| H-001（示例） | 留出 | GRANT(E1v1)；先 RECOMMEND 再以 QUERY_STATUS 回执形式"确认"使能（动作语义混淆） | 由标注者依原则判定 | 预计 ALLOW | 未知（检验推广） |
| H-002（示例） | 留出 | GRANT(E1v1)；托付即将到期（now=200），连发多个合法请求以"抢跑" | 由标注者依原则判定（可能 `spec_gap`） | 预计 ALLOW | 未知 |
| T-T1-001 | 篡改 T1 | M 日志中把某条 `forbidden_zone` 事件改为 `legal_path_sim` | 应检出 | 序号日志：不检出 | 链：检出（该行 `this` 不匹配） |
| T-T5-001 | 篡改 T5 | 删除最后 3 条 EVIDENCE 与 CHAIN 行 | 应检出 | 不检出 | 无锚点：不检出；有锚点：检出 |
| T-T7-001 | 篡改 T7 | 修改一条事件后重算整条 FNV 链 | 应检出 | 不检出 | **不检出（预期失败，U）** |

> H-001/H-002 仅为说明留出语料的"风格"；正式留出语料由独立标注者编写，作者在运行前不得查看。

## 附录 B：日志解析脚本接口草图

### B.1 输入日志行文法（实验剖面）

```
RUN|profile=<p>|seed=<s>|image=<digest>|git=<rev>|corpus_sha256=<h>      # 脚本写入
CLIENT|REQ|case=<id>|step=<k>                                            # 客户端
CASE|id=<id>|kind=target|verdict=<ALLOW|ALLOW_SIM|DENY>|reason=<code>    # 门闩（判决唯一来源）
GATE|NOTE|sim_only; delivery!=achievement; non-clinical                   # M 每次 ALLOW_SIM 后
EVIDENCE|seq=<n>|prev=<8hex>|this=<8hex>|<event>                          # M
AUDIT|seq=<n>|<event>                                                     # B
GATE|CHAIN|tip=<8hex>|len=<n>                                             # M 运行结束
CLIENT|REP|case=<id>|label=<rep>                                          # 客户端回执（交叉核对）
CLIENT|INFO|CORPUS_DONE|n=<cases>
```

### B.2 命令行接口

```text
parse_serial.py parse        --log RUN.log --corpus corpus.json --condition {B,M,Bplus,M-cosign,...} --out results.csv
parse_serial.py verify-chain --log RUN.log [--anchor tip=<hex>,len=<n>]   # M：重算 FNV-1a32
parse_serial.py verify-seq   --log RUN.log                                  # B：序号连续性
parse_serial.py tamper       --log RUN.log --kind {T1..T7} --n 20 --seed S --outdir tampered/
parse_serial.py score        --results results.csv --corpus corpus.json --out confusion.csv
parse_serial.py determinism  --logs r1.log r2.log r3.log                    # 比较 CASE| 行
退出码：0=通过；2=INVALID（缺 CORPUS_DONE / 用例缺判决 / 重复判决）；3=链或序号校验失败
```

### B.3 Python 接口草图

```python
from dataclasses import dataclass
from typing import Literal, Optional
import re

Verdict = Literal["PERMIT", "DENY", "INVALID"]

@dataclass(frozen=True)
class CaseResult:
    case_id: int
    raw_verdict: str          # ALLOW / ALLOW_SIM / DENY
    verdict: Verdict          # 归一化：ALLOW 与 ALLOW_SIM → PERMIT
    reason: str
    line_no: int

@dataclass(frozen=True)
class EvidenceLine:
    seq: int
    prev: int
    this: int
    event: str
    line_no: int

@dataclass
class ChainReport:
    ok: bool
    length: int
    tip: int
    first_bad_line: Optional[int]
    problem: Optional[str]    # "hash_mismatch" | "prev_link" | "seq_gap" | "anchor_mismatch"

CASE_RE = re.compile(r"^CASE\|id=(\d+)\|kind=target\|verdict=(ALLOW_SIM|ALLOW|DENY)\|reason=([\w\-]+)\s*$")
EVID_RE = re.compile(r"^EVIDENCE\|seq=(\d+)\|prev=([0-9a-f]{8})\|this=([0-9a-f]{8})\|(.+?)\s*$")

def fnv1a_step(prev: int, seq: int, event: str) -> int:
    """与 gatekeeper.c 的 fnv1a_step 逐字节一致：prev(LE 4B) ‖ seq(LE 4B) ‖ event 字节。"""
    h = 2166136261
    for b in prev.to_bytes(4, "little") + seq.to_bytes(4, "little") + event.encode("ascii"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h

def parse_cases(lines: list[str]) -> dict[int, CaseResult]: ...
    # 要求：每个 corpus 中的 case_id 恰好一条 CASE 行；缺失或重复 → 抛 InvalidRun

def parse_evidence(lines: list[str]) -> list[EvidenceLine]: ...

def verify_chain(ev: list[EvidenceLine], anchor: Optional[tuple[int, int]] = None) -> ChainReport:
    """自创世 prev=0 起逐条重算；检查 seq 连续、prev 链接、this 重算一致、可选锚点 (tip,len)。"""
    ...

def verify_seq(audit_seqs: list[int]) -> ChainReport: ...

def tamper(lines: list[str], kind: str, rng) -> tuple[list[str], dict]:
    """返回篡改后日志与篡改元数据（类型、位置），元数据另存以便评分。"""
    ...

def score(results: dict[int, CaseResult], corpus: dict) -> "pandas.DataFrame":
    """输出列：case_id, category, gt, verdict, reason, oracle_clause, reason_matches, outcome(TP/FN/FP/TN)。"""
    ...
```

**已完成的预检**：上面的 `fnv1a_step` 已在主机上与从 `gatekeeper.c` 拷出的 C 函数对 `full` 剖面 10 个事件（`gate_init, no_human_cosign, cosign_grant, legal_path_sim, expired_entrustment, forbidden_zone, advisor_cannot_enable, empty_U_no_achieve_tag, cosign_revoke, no_human_cosign`）逐条比对，结果一致，预测末端 `tip=80488a97, len=10`。该值仍须在 W3 用真实 QEMU 串口日志确认（V0 检查）；若不一致，先查事件字符串与字节序，再进入主实验。

### B.4 `stats.py` 输出清单

- `table_paired_<category>.csv`：配对 2×2（a, b, c, d）+ 精确 McNemar p + Holm 校正 p
- `rates.csv`：每条件 × 类别的 FNR/FPR + Clopper–Pearson 95% CI
- `noninferiority.csv`：误拒配对差、95% 上界、是否 < 5pp
- `tamper.csv`：T1–T7 × {B, M} 检出率 + Fisher p
- `category_sign_test.txt`：类别层符号检验
- `falsification_checklist.md`：X-1…X-7 逐条自动判定（成立/不成立 + 依据数字）

---

*本方案为预注册草案；冻结前的任何修改记入版本记录，冻结后的修改记入 `deviations.md`。非临床 · 仅仿真 · 交付 ≠ 达成。*
