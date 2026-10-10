# 预注册文件 `prereg.md`（冻结版 v1）

> 课题：使命软件工程学 · 对照实验"使命流程 vs 传统流程"（Microkit 使命约束外壳）
> 依据：`controlled-experiment-design.md`（实验方案 v0.1，2026-10-07）
> 冻结日期：2026-10-08（Asia/Shanghai）· 作者：chen peng
> 非临床 · 仅仿真 · 无写使能 · 不宣称 seL4 级应用证明 · 交付 ≠ 达成 · FNV-1a32 证据链为教学级

## 0. 冻结纪律

1. 本文件中的**阈值、假设、主次终点、反证条件、种子**自本版起冻结。冻结后任何修改只能写入 `deviations.md`（含日期、原因、影响），不得静默修改本文件。
2. 建议在把本目录纳入 git 后立即执行：`git add experiment && git commit -m "prereg v1" && git tag prereg-v1`（实验方案 §3.5 第 4 步）。在打标签之前，本文件的"冻结"仅以文件内容与日期为凭。
3. **真值状态**：当前语料真值来自草稿 oracle（`oracle/oracle.py`，草稿·待独立标注人复核；不计入确证性结论）。独立标注人尚未指定。在标注人审阅签字 `oracle/rules_spec.md`、独立重写 `oracle.py`、完成 κ 双标之前，§5 的语料哈希只代表"草稿冻结"，所有基于作者语料的数字都只是**装置自检**。

## 1. 机器可读阈值块（analyze.py 读取；冻结）

```text
# PREREG-THRESHOLDS v1 (frozen)
delta_fpr_pp: 5
holdout_fnr_ceiling: 0.30
bplus_capture_ceiling: 0.80
kappa_min: 0.90
holdout_min_must_deny: 30
holdout_min_may_permit: 10
alpha_primary_one_sided: 0.025
alpha_secondary_two_sided: 0.05
loc_ratio_ceiling: 3.0
l2_subtype_systematic_fpr: 0.50
legal_n_per_seed: 120
seeds: 20261007,20261008,20261009,20261010,20261011
```

| 键 | 含义 |
|---|---|
| `delta_fpr_pp` | 误拒非劣效界值 Δ = 5 个百分点（H2） |
| `holdout_fnr_ceiling` | 留出语料上 M 的漏检率上限 30%；≥ 30% 即判"推广性不足"（X-1） |
| `bplus_capture_ceiling` | B+ 在 F1–F9 上拦截了 M 所拦截用例的比例 ≥ 80% 即触发 X-3 |
| `kappa_min` | 作者手标 vs 独立 oracle 的 Cohen's κ ≥ 0.9（≥ 40 个随机用例） |
| `holdout_min_must_deny` / `holdout_min_may_permit` | 留出语料至少 30 个假使命、10 个合法对照 |
| `alpha_primary_one_sided` | 主终点 P1 精确 McNemar 单侧 α = 0.025 |
| `alpha_secondary_two_sided` | 次要检验双侧 α = 0.05（逐类别再做 Holm 校正） |
| `loc_ratio_ceiling` | X-7 的代码增量门槛（M/B 有效行数比 > 3） |
| `l2_subtype_systematic_fpr` | X-2 中"L2 某边界子型系统性被拒"的操作定义：该子型（5 种子合并）M 误拒率 ≥ 50% |

## 2. 假设（零假设可证伪陈述，摘自方案 §1.3）

- **H1（主，验证性，留出语料 H）**：H1₀ P(b) = P(c)；H1₁ b > c。附加门槛：即使拒绝 H1₀，若 FNR_M(H) ≥ 30%，判"推广性不足"。
- **H1′（操纵检查，作者语料 A）**：预测 FNR_M(A) = 0，且 ≥ 6 个"仅使命可拦"类别（F1、F2、F3、F5、F6、F7、F8、F9）上 FNR_B ≥ 0.9。**不作为方法有效的证据**；失败则先修实现。
- **H2（主，验证性，合法语料 L）**：H2₀ FPR_M − FPR_B ≥ Δ；配对差 95% 精确上界 < Δ 则拒绝 H2₀。
- **H3a（次要）**：T1–T4 上 M 证据链检出率不高于 B 序号日志（Fisher 精确）。
- **H3b（探索性）**：人工审查研究——**本阶段推迟，未实施**。
- **H4（预览）**：不设零假设。

## 3. 主次终点

| 级别 | 终点 | 检验 |
|---|---|---|
| 主要 | P1 留出语料 H 上配对漏检差异 | 精确 McNemar，单侧 α = 0.025 |
| 主要 | P2 合法语料 L 上误拒非劣效 | 配对差保守精确上界（b/n 的 Clopper–Pearson 双侧 95% 上界，因 (b−c)/n ≤ b/n）vs Δ |
| 次要 | S1 作者语料各类别漏检率 | 描述 + Wilson / Clopper–Pearson |
| 次要 | S2 篡改检出 T1–T7 | 描述 + Fisher 精确 |
| 次要 | S3 消融预测漏检是否出现 | 逐类别描述 |
| 探索性 | E1 人工审查（推迟）、E2 代码/证据成本、E3 第二领域 | — |

## 4. 反证条件（任一成立即在结论中如实写明；摘自方案 §7.2，操作化如下）

| 编号 | 条件（操作化） |
|---|---|
| X-1 | 留出语料 H（独立标注人编写，非 spec_gap 部分）上精确 McNemar 单侧 p ≥ 0.025，或 FNR_M(H) ≥ 30% |
| X-2 | 任一种子或 5 种子合并的误拒差保守上界 ≥ 5pp，或任一 L2 子型 M 误拒率 ≥ 50% |
| X-3 | 首个种子上，F1–F9 中 M 拦截的用例里 B+ 也拦截的比例 ≥ 80%（预注册口径；"增量口径"仅作补充报告） |
| X-4 | 任一 MUST_DENY 类别出现 c > 0（B 拦而 M 放） |
| X-5 | T1–T4 合并，M 检出率高于 B 的 Fisher 精确单侧 p ≥ 0.05 |
| X-6 | 人工研究中 M 的 F1 中位数不高于 B 且用时更长（推迟；当前不判定） |
| X-7 | M/B 门闩有效行数比 > 3 且 X-1 成立 |

明确声明：**作者语料 A 上 M 全拦截不计为支持方法的证据**；若只有 A 上结果为正而 X-1 成立，结论写为"使命层在本玩具中未显示推广收益"。

## 5. 规则优先级（多条规则同时违反时的判定理由）

采用实验方案 §2.4 的顺序，细化后固定为（详见 `oracle/rules_spec.md` §4）：

`S-F1 枚举 → S-F2 范围 → S-F3 工单存在 → S-R1 角色 → S-N1 重放 → S-C1 无共签 → S-C2 共签绑定不符 → S-E0 版本不存在 → S-T1 过期 → S-T2 未生效 → S-Z1 禁区 → S-S1 区越界 → S-S2 强度越界 → S-S3 动作越界 → S-V1 版本陈旧 → S-P1 顾问来源使能 → S-U1 U 为空 → S-U2 达成不可声称`

由此，方案附录 A 中 A-F8-001（共签绑定 v2、请求 v1）的理由码固定为 `cosign_binding_mismatch`；A-F8-002（撤销后改授 v2、按 v1 请求）同样为 `cosign_binding_mismatch`；只有"共签仍绑定旧版本 v1 且按 v1 请求"时理由码为 `stale_entrustment_version`。

## 6. 时间模型与设计决定

- 逻辑时钟：门闩持有逻辑时刻 `now`，只能由测试专用报文 `REQ_HARNESS_CLOCK_SET`（32）设置并写入证据/审计；用例复位时归零。时钟可信性属 U。
- 托付表编译期固化（`corpus/entrustments.json` → `gen/entrustments_gen.h`），种子无关。
- B+ 的全局规则：站点运行窗 = 全表 [min t_start, max t_end] = [50, 2000]；站点禁区 = 每条托付都禁止的区 {7, 15}。
- 共签为集合语义（容量 4），GRANT/REVOKE 携带 (ent_id, ver)；REVOKE(0,0) 撤销全部。
- nonce 一经出现即记入用例内历史（无论该请求结果）。

## 7. 种子与语料哈希（草稿冻结；SHA-256）

种子：20261007、20261008、20261009、20261010、20261011（用于语料重采样，不是运行重复）。规模：每种子 F1–F9 各 20、L1–L5 各 24、M1 10、X1 10，共 320。

```text
c74a562b0d84898df51c7f64ad7060e44ba785470839272e29ad2e2f4331574c  ../../gen/entrustments_gen.h
1412203e37bd798dacb83d07deca7e6adf865cd191a1d851c2fc6ea19e2cf502  ../entrustments.json
b53268fc3f5b09989414cf5941ebbd22a062d154c52801acda4403044fc9dba2  corpus_20261007.h
7cf3a6807a0e29aee5dc480ff929531348086e32d72393ec410a45ad40696555  corpus_20261007.json
33ebc6fcec0c33d29bdb6515a751dd580418e8aab0abef47d181e18522e89061  corpus_20261008.h
bdd8e521f72521b922ce4c2cbf44488f9346a70ff09ef1171eb99f9e76d51cba  corpus_20261008.json
a39e4dd7de9e43db5819cffb8882a2edd366dfb02990320ae024a7fe00a38931  corpus_20261009.h
ea7f767c4285b869ee94f0b7fde7901278c0be77408bfc36909dcd80095c0eed  corpus_20261009.json
3e5ee7a1fa2843452c91cf3ec5bcf403346af855c89c7ae7b2818a4e7c63a372  corpus_20261010.h
72a1db5157c5b0b323a529d9c7244dd43c6a8054c892f3035f6859a642746d1b  corpus_20261010.json
cbdfab94000a4bc3989db769a057005280b7612587ab012a3a0f30859945d1df  corpus_20261011.h
389140c3c1b09bff778226df3b9463d57d2a0137c583c4a7693498634ab623ed  corpus_20261011.json
db1cac91fa80722762acfbcd58023700b907309179f4f3eb480deea819ba1dab  holdout_draft.h
7bf427a3eddaa90890fedda7da0f36ec5ec9bc46b8bd0121037c285a24cd0fed  holdout_draft.json
```

`docker_corpus_run.sh` 在构建前校验上述哈希，不一致即退出；容器内有 python3 时还会重新生成并比对。

## 8. 篡改轨道预期（预先声明为 U 的失败）

T5（无外部锚点）与 T7 在 M 上**预期不检出**：FNV-1a32 无密钥、非抗碰撞，只提供"顺序追加可复核"的教学语义；外部锚点 = 运行结束时 `GATE|CHAIN|tip|len`，由实验者另行登记。完整预期见 `tamper/expectations.json`。

## 9. 运行矩阵（方案 §5.4）

| 条件 | 种子 | 重复 | 次数 |
|---|---|---|---|
| B、M | 5 | 3 | 30 |
| B+、M−cosign、M−align、M−prov、M−U | 首个种子 | 1 | 5 |
| B、M 于留出语料 H（待独立标注人提供；当前只有草稿） | — | 3 | 6 |
| full 回归 | — | 1 | 1 |

重复只用于确认确定性；同一 (条件, 种子) 的重复在分析中只计一次。

## 10. 未实施 / 推迟事项

- 人工审查小型研究（RQ3b/E1/X-6）：**推迟**。
- 独立标注人：**未指定**；规格、oracle、留出语料均为草稿。
- RQ4 第二领域：未实施。
