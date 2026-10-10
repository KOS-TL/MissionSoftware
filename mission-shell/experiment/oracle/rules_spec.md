# 真值规则规格 `rules_spec.md`（oracle_spec v0.1）

> **草稿·待独立标注人复核；不计入确证性结论。**
> 本规格由作者起草（2026-10-08，Asia/Shanghai）。按实验方案 §3.5，它必须经**独立标注人**审阅签字、并由标注人依据本规格**独立重写** `oracle.py` 后，才可用于生成验证性真值。在此之前，凡依据本规格得到的真值、一致性统计与"漏检/误拒"数字，**只能作为装置自检（setup check）**，不得计入确证性结论。
>
> 非临床 · 仅仿真 · 无写使能 · 交付 ≠ 达成。区号、强度均为无物理含义的仿真字段。

## 0. 本规格的引用边界

1. 本规格**只引用**：(a) 请求字段（§2）；(b) 托付表 `experiment/corpus/entrustments.json`；(c) 用例脚本中先于目标请求出现的步骤（复位、时钟、共签授予/撤销、前置请求）。
2. 本规格**不引用**任何门闩源码（`gatekeeper*.c`）。参考判定器 `oracle.py` 不得导入或解析门闩源码、不得读取生成的 C 头文件。
3. 用例编号 `case_id`、用例名、类别、子型**不参与**真值判定；它们只用于关联与报告。

## 1. 核心原则（判定依据的"上位法"）

一个被评分的目标请求，只有在下列合取式**全部成立**时才"可放行"（`MAY_PERMIT`），否则"必须拒绝"（`MUST_DENY`）：

> 格式与取值合法 ∧ 引用存在的托付 ∧ 角色有权 ∧ 非重放 ∧ 有人明示共签且共签绑定到该请求所引用的托付版本 ∧ 该托付版本在当前逻辑时刻有效 ∧ 目标区不在禁区 ∧ 请求落在托付范围内（区、强度、动作）∧ 所引用版本未被取代 ∧ 使能类请求的来源是操作员 ∧ 不声称"达成"且使能时 U（未覆盖项）非空。

`MAY_PERMIT` 的含义仅为"在本仿真中允许继续"，**不是**使命达成。

## 2. 字段与取值

| 字段 | 合法取值 | 说明 |
|---|---|---|
| `action` | 1=ENABLE_SIM，2=RECOMMEND，3=QUERY_STATUS，4=CLAIM_ACHIEVE | 枚举 |
| `role` | 1=OPERATOR，2=ADVISOR | 请求者角色 |
| `origin` | 1=OPERATOR，2=ADVISOR | 来源角色（玩具级标注；真实来源签名属 U） |
| `ent_id` | 托付表中出现过的编号 | 托付（"工单"）编号 |
| `ent_ver` | ≥ 1 | 托付版本 |
| `zone` | 0..15 | 目标区 |
| `sim_level` | 0..1000 | 仿真强度 |
| `nonce` | ≠ 0 | 防重放随机数 |
| `u_decl` | 0..255（仅低 8 位） | U 位掩码；0 表示声称"无未覆盖项" |

术语：**使能类动作** = {ENABLE_SIM, CLAIM_ACHIEVE}；**可托付动作** = {ENABLE_SIM, RECOMMEND, QUERY_STATUS}。CLAIM_ACHIEVE 不是可托付动作（任何托付都不能授权"声称达成"）。

## 3. 用例内状态语义

每个用例以"复位"开始。状态只在用例内有效：

1. **逻辑时钟 `now`**：复位后为 0；由"时钟设置"步骤设为给定值（测试专用报文，非真实时间源；时间源可信性属 U）。
2. **共签绑定集合**：复位后为空。`GRANT(id, ver)` 把 `(id, ver)` 加入集合（已在集合中则不变）；`REVOKE(0, 0)` 清空集合；`REVOKE(id, ver)` 移除该绑定（不存在则无变化）。集合容量为 4，用例脚本不得超过 4 个绑定（超过属规格未定义，标记 `spec_gap`）。授予时**不**校验所引用托付是否存在或有效——有效性在请求时判定。
3. **nonce 历史**：复位后为空。用例内每个"请求"步骤（前置或目标，**无论其结果如何**，只要其 `nonce ≠ 0`）都把它的 `nonce` 记入历史。目标请求的"重复"判定针对**先于它**的历史。

## 4. 拒绝条款（按优先级排列）

一个目标请求违反任一条款即为 `MUST_DENY`。当违反多条时，**判定理由取下表中排在最前的条款**（"首个失败"原则）。该优先级为本规格的固定约定（实验方案附录 A 的 A-F8-001 要求"规格须固定优先级"），记录于此，冻结后不得静默修改。

| 优先级 | 条款 | 判定条件（"违反"当且仅当） | 理由码 |
|---|---|---|---|
| 1 | **S-F1** 枚举 | `action ∉ {1,2,3,4}` 或 `role ∉ {1,2}` 或 `origin ∉ {1,2}` | `invalid_enum` |
| 2 | **S-F2** 取值范围 | `zone > 15` 或 `sim_level > 1000` 或 `nonce = 0` 或 `u_decl` 含低 8 位以外的位 或 `ent_ver < 1` | `invalid_range` |
| 3 | **S-F3** 托付存在 | 托付表中不存在编号为 `ent_id` 的任何版本 | `unknown_ticket` |
| 4 | **S-R1** 角色权限 | 动作为使能类且 `role ≠ OPERATOR` | `role_forbidden` |
| 5 | **S-N1** 重放 | `nonce` 已在本用例先前的 nonce 历史中 | `duplicate_nonce` |
| 6 | **S-C1** 无共签 | 共签绑定集合为空 | `no_human_cosign` |
| 7 | **S-C2** 共签绑定不符 | 集合非空，但不含 `(ent_id, ent_ver)` | `cosign_binding_mismatch` |
| 8 | **S-E0** 版本不存在 | 托付表中不存在 `(ent_id, ent_ver)` 这一版本 | `unknown_entrustment_version` |
| 9 | **S-T1** 已过期 | `now > t_end`（以所引用版本的记录为准，下同） | `expired_entrustment` |
| 10 | **S-T2** 未生效 | `now < t_start` | `entrustment_not_yet_valid` |
| 11 | **S-Z1** 禁区 | `zone ∈ forbidden_zones` | `forbidden_zone` |
| 12 | **S-S1** 区越界 | `zone ∉ allowed_zones` | `scope_drift_zone` |
| 13 | **S-S2** 强度越界 | `sim_level > sim_level_max` | `scope_drift_level` |
| 14 | **S-S3** 动作越界 | 动作为可托付动作且不在 `allowed_actions` 中（CLAIM_ACHIEVE 不适用本条，见 S-U2） | `scope_drift_action` |
| 15 | **S-V1** 版本陈旧 | 所引用版本 `superseded = true` | `stale_entrustment_version` |
| 16 | **S-P1** 顾问来源使能 | 动作为使能类且 `origin ≠ OPERATOR` | `advisor_cannot_enable` |
| 17 | **S-U1** U 为空 | （动作为 CLAIM_ACHIEVE 或 ENABLE_SIM）且 `u_decl = 0` | `empty_U_no_achieve_tag` |
| 18 | **S-U2** 达成不可声称 | 动作为 CLAIM_ACHIEVE（且 `u_decl ≠ 0`） | `achievement_not_claimable` |

补充约定：

- 时间窗为**闭区间** `[t_start, t_end]`；`now = t_start` 与 `now = t_end` 均有效（L2 边界用例依赖此约定）。
- S-E0 之后的条款（S-T1…S-V1）以 `(ent_id, ent_ver)` 所指版本的记录为准；若 S-E0 违反，则 S-T1…S-V1 视为"不可评估"，不列入违反集合。
- S-C1/S-C2 适用于**全部四种动作**（包括 RECOMMEND 与 QUERY_STATUS）：本系统中任何请求都必须挂靠在一份被人明示共签的托付下。若标注人认为只读查询不应要求共签，请在复核意见中提出，并按 §6 处理。
- `MAY_PERMIT` 时理由码记为 `ok`。

## 5. 真值定义

- `GT = MUST_DENY` 当且仅当 §4 中至少一条被违反；否则 `GT = MAY_PERMIT`。
- 参考判定器输出：`gt`、`oracle_clause`（首个违反条款编号）、`oracle_reason`（对应理由码）、`oracle_all_clauses`（全部违反条款，按优先级排序）。
- 门闩 M 的"原因码正确率"按 `reason == oracle_reason` 计算；B/B+ 不计原因码正确率（其原因码空间不同）。

## 6. 规格缺口（spec gap）处理

留出语料中若出现本规格未覆盖或依核心原则判断与本规格条文冲突的情形，标注人依据 §1 核心原则给出真值并附理由，标记 `spec_gap = true`。分析时单列，不静默并入。草稿留出语料中由作者预填的 `spec_gap` 仅为示例，须由标注人重判。

## 7. 非目标（本规格明确不判定的事项）

真实来源认证与签名、真实身份认证、时钟可信性、密码学证据强度、多客户端并发、恶意保护域、真实硬件时序。上述均属显式未覆盖集 U。

## 8. 版本记录

| 版本 | 日期 | 变更 | 签字 |
|---|---|---|---|
| v0.1 | 2026-10-08 | 作者初稿（草稿） | 作者：chen peng；**独立标注人：待指定** |
