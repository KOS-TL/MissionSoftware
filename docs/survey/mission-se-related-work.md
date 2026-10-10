# 使命软件工程学：相关研究与国内外研究现状

> **仓库化说明（v0.1.0）**：本文为项目过程中的历史文档，按原文收录，仅做去个人化处理：作者本机路径已替换为 `<REPO_ROOT>`（= 本仓库克隆目录，内含 `mission-shell/` 与 `microkit-sdk-2.3.1/`）、`<WORKDIR>`（作者文档目录）或仓库内相对路径；形如 `/workspace/...` 的路径是作者沙箱（box）上的历史路径，在本仓库中分别对应 `mission-shell/`（原 `/workspace/microkit-mission-shell/`）与 `docs/`。文中命令含占位符，**不能直接复制执行**；可直接执行的命令见仓库根目录 `README.md` 与 `docs/REPRODUCE.md`。


> 版本：2026-10-09（Asia/Shanghai）｜范围：与"明示托付 ∧ 仍对准 ∧ 可证伪"合取相关的研究脉络
> 核验标注：【V】已打开页面核验；【S】仅见于检索结果（含所打开页面的参考文献列表）；【M】凭记忆、未核验（本稿未使用）。
> 原则：不杜撰 DOI、页码、统计数字；凡细节不确定处一律省略。

---

## 0. 总览

使命软件工程学（下称"本项目"）给软件生命周期加了一层"使命层"。它的核心判断是：在某一时刻，一个动作获准执行，当且仅当以下三项同时成立：

1. 存在**明示的人类托付**：托付人具名，并写明范围、有效期、版本、禁区，且可撤销；
2. 该动作**仍与托付对准**；
3. 上述检查本身**可证伪**。

对应的工程制品有：托付记录、禁区/未覆盖假设清单（U）、逐动作闸门判决、防篡改证据链。标志性方法是"伪使命测试"：请求格式合法、角色合法，但已不再对准托付的，必须被拒绝。保证模型与 seL4/CompCert 融合，形式化为"条件保证 P + 显式未覆盖 U"。

检索结论：**本项目的单个要素几乎都有成熟的先行研究；但没有找到任何一项工作把这些要素在同一框架内合取起来**，即"具名托付记录 + 逐动作对准闸门 + 伪使命负向测试 + 防篡改证据链 + 形式化验证条件保证（P/U）"，并落在放疗剂量/联锁这类安全关键语境中。

与本项目最接近的是 2025—2026 年的 **AI 智能体授权**研究，见 §7c 和 R73–R77。其中 Zhu & Wang（2026）的"意图证书"已经覆盖了"静态授权合法、但与当前意图不符则拒绝/澄清 + 本地哈希链审计"。所以，**"角色合法但不对准即拒绝"这一思想本身不是本项目首创**。本项目的新意应定位为：

- 把它提升为通用的软件工程学科层（贯穿需求—设计—验证—运行—证据）；
- 把托付人、禁区、版本、U 清单作为一等制品；
- 与经形式化验证的底座做条件保证融合；
- 落到医疗联锁场景。

另外，"使命工程（Mission Engineering）"在美国国防部/INCOSE 与中国国防系统工程界指的是**体系（SoS）的使命设计**，和本项目同名不同义，见 §11。

---

## 1. 对比矩阵

图例：● 明确具备；◐ 部分具备或间接具备；○ 基本不涉及。列含义如下：

- E：托付/委托是否显式
- A：是否在运行时检查对准
- F：是否以负向测试证伪
- T：证据是否防篡改
- V：是否与形式化验证融合
- H：是否有人在回路

| 研究脉络 | E | A | F | T | V | H | 简要理由 |
|---|---|---|---|---|---|---|---|
| 1a 目标导向需求工程（KAOS / i* / Tropos / Secure Tropos） | ◐ | ○ | ◐ | ○ | ◐ | ◐ | 有职责分配；Secure Tropos 显式建模"许可/执行的委托"；KAOS 的障碍分析是一种"反向"思考，并有时序逻辑形式化。但主要在设计期使用。 |
| 1b 需求运行时监控（FLEA、RELAX、Requirements@run.time） | ○ | ● | ○ | ○ | ◐ | ○ | 在运行时监控需求/假设是否被违反；"对准"的对象是需求，而不是人的托付。 |
| 2a 保证案例（GSN / CAE / SACM / Assurance 2.0 / 排除式论证） | ○ | ○ | ◐ | ○ | ◐ | ◐ | 废止因子（defeater）与反案例接近"可证伪"；没有托付人、禁区等概念；属于静态论证。 |
| 2b 动态/条件保证（ConSerts、动态安全案例、ETB、UL 4600 SPI） | ○ | ● | ◐ | ◐ | ◐ | ○ | 在运行时评估保证条件；ETB 用哈希标识证据。不涉及人的托付。 |
| 3 运行时验证与强制（安全自动机、编辑自动机、Simplex/RTA、Shield、ModelPlex） | ○ | ● | ◐ | ○ | ● | ○ | 逐动作拦截/替换，监控器可被验证；所依据的是形式规约，不是托付。 |
| 4a 授权/委托/策略（能力、speaks-for、UCON、XACML、Zanzibar、Macaroons、委托撤销） | ● | ◐ | ◐ | ○ | ◐ | ○ | 委托、caveat、时限、撤销都很成熟；UCON 有"持续授权"；但只检查"有没有权限"，不检查"是否仍对准目的"（基于目的的访问控制是部分例外）。 |
| 4b 人类监督（有意义的人类控制、自动化等级、EU AI Act 第14条） | ◐ | ◐ | ○ | ◐ | ○ | ● | 规范层面要求人能理解、干预、停止，并设双人核验；但缺少可执行的逐动作闸门。 |
| 5 使命工程与使命保证（DoD MEG、SEBoK、CJA、Aerospace MAG、NIST 800-160v2） | ◐ | ◐ | ○ | ○ | ○ | ◐ | 区分"交付"与"使命效果"（MOE 与 MOP）；CJA 把使命映射到资产。对象是体系级任务，不涉及软件动作闸门。 |
| 6a 可信验证（seL4 / CompCert / CakeML / CertiKOS / Cogent / PCC / HACMS / LionsOS） | ○ | ○ | ◐ | ○ | ● | ○ | 提供强隔离与功能正确性的条件保证；HACMS 做过红队对抗。不知道"使命"是什么。 |
| 6b 防篡改证据（Schneier-Kelsey 日志、历史树、CT、in-toto） | ◐ | ◐ | ○ | ● | ○ | ○ | in-toto 的布局由项目所有者签名、规定"谁可执行哪步"，接近托付记录；但针对的是供应链步骤。 |
| 7a 误用/错配测试（误用用例、变异、蜕变、策略变异测试、规约挖掘） | ○ | ○ | ● | ○ | ○ | ○ | 有成熟的负向测试与测试充分性方法；但没有"伪使命"这一类别。 |
| 7b AI 对齐（规约博弈、目标误泛化） | ◐ | ◐ | ◐ | ○ | ○ | ◐ | 揭示"按字面完成 ≠ 达成意图"，与"交付≠达成"同构；缺少工程制品。 |
| 7c AI 智能体授权（委托令牌、CaMeL、Progent、AgentSentry、意图证书） | ● | ● | ◐ | ◐ | ○ | ● | **最接近**：任务/意图范围内的最小权限、到期/撤销，偏离即拒绝，并有审计链。缺 P/U 融合，也不面向安全关键 CPS。 |
| 8 医疗/放疗安全（Therac-25、IEC 62304/60601-2-1/14971、TG-100、Jacky 的 Z 规约） | ◐ | ● | ◐ | ○ | ◐ | ● | 硬件/软件联锁保证"出束状态与处方一致"，处方可看作一种"托付"；FMEA 属于前瞻分析。 |
| 9 中国研究（可信软件计划、自适应/运行时验证、使命工程、有意义人类控制、AgentSentry） | ◐ | ◐ | ◐ | ○ | ◐ | ◐ | 各分支都有工作，但没有找到"使命软件工程"这一合取。 |
| **本项目（目标）** | ● | ● | ● | ● | ● | ● | 目标是六项合取；目前是设计主张，尚待实证。 |

---

## 2. 脉络一：目标/义务导向需求工程（1a、1b）

**做什么。**
- KAOS 把目标逐层精化为可分配给代理的需求与期望 [R15, R16]。障碍分析系统地寻找使目标失效的条件 [R17]。
- i*/Tropos 以"行动者—依赖"建模社会意图 [R18, R19]。
- Secure Tropos 显式区分所有权、许可与执行的**委托**，并检查信任链 [R20]。
- 需求监控（FLEA）在运行时检测假设是否被违反 [R21, R22]。
- RELAX 和 Requirements reflection 让需求成为运行时对象 [R23, R24]。
- 需求可追溯性问题见 [R25]。

**与本项目的共性。**
- "障碍"约等于本项目的"未覆盖假设 U"。
- Secure Tropos 的"许可委托"约等于本项目的"托付"。
- 需求监控约等于"运行时仍对准"。

**精确差距。**
- 托付在这些方法中是**设计期模型元素**，不是运行时带版本、有效期、禁区和撤销的记录。
- 没有逐动作闸门，也没有"伪使命"负向测试集。
- 没有与形式化验证底座做 P/U 条件保证融合。

**接近度：部分重叠**（Secure Tropos 与 KAOS 障碍 + 需求监控是本项目在需求工程中的直接祖先）。

## 3. 脉络二：保证案例及其维护（2a、2b）

**做什么。**
- GSN [R26, R27]、CAE [R28]、OMG SACM [R29] 提供结构化论证。
- Assurance 2.0 [R30]【V】强调废止因子、反案例与"可辩驳性"。
- 排除式论证 [R31, R32] 以"排除怀疑"度量置信度。
- 动态安全案例 [R34]【V】主张在运行期更新论证。
- ConSerts [R33] 在运行时按条件合成认证。
- Sorokin 等 [R35]【V】基于 Evidential Tool Bus 实现持续保证。
- AMLAS [R36]、UL 4600 [R37]、SOTIF [R38] 把保证扩展到机器学习与自主系统。
- STPA [R39] 的"不安全控制动作"包括"在错误情境下提供本应正确的动作"，这与"伪使命"高度同构。

**共性。**
- "条件保证 P + 显式 U"与 Assurance 2.0 的"假设/废止因子显式化"以及 ConSerts 的"条件化保证"思想一致。
- 动态安全案例与"证据链随运行更新"一致。

**差距。**
- 保证案例论证的是"系统是否安全/可信"，**不论证"此刻这一动作是否仍在人的托付之内"**。
- 证据大多没有防篡改要求（ETB 只用哈希做标识）。
- 没有托付人和撤销语义。

**接近度：部分重叠**（ConSerts/动态安全案例/Assurance 2.0 是 P/U 表述最直接的参照）。

## 4. 脉络三：运行时验证与运行时强制（3）

**做什么。**
- 运行时验证综述 [R40, R41]（Leucker & Schallhart 刊于 JLAP 78(5)，卷期为 2009 年，2008 年在线发表）。
- 运行时强制框架 [R42]。
- 安全自动机 [R43]：截断违规执行。
- 编辑自动机 [R44]：插入/抑制动作。
- Simplex [R45] 与 ASTM F3269 运行时保证 [R46]：用经验证的安全控制器兜底未验证组件。
- Shield [R47]：为强化学习拦截不安全动作。
- ModelPlex [R48]：把经验证模型编译为运行时监控器。

**共性。** 本项目的"逐动作闸门"本质上是运行时强制。Simplex/RTA 的"验证组件约束未验证组件"结构，与 seL4 上 Microkit 约束壳的设计同构。

**差距。** 监控依据的是**形式规约/安全包络**，不是带托付人、有效期、禁区、版本的托付记录。规约本身是否仍对准人的意图，不在其考察范围内。

**接近度：部分重叠**（技术机制几乎可直接复用；语义对象不同）。

## 5. 脉络四：授权、委托、策略与人类监督（4a、4b）

**4a 做什么。**
- 能力（capability）[R49]、保护原则 [R50]。
- 混淆代理人问题 [R51]：即"合法权限被用于非本意目的"，是"角色合法但不对准"的经典安全版本。
- 能力安全再审视 [R52]。
- speaks-for 委托逻辑 [R53]。
- UCON 的持续授权与义务 [R54]。
- XACML 义务 [R55]、Zanzibar [R56]。
- Macaroons 的可衰减 caveat [R57]。
- 委托与撤销 [R58]。
- 基于目的的访问控制 [R59]：最接近"对准"，按"访问目的"授权。

**4b 做什么。**
- 有意义的人类控制，其"追踪/追溯"条件 [R60]。
- 自动化等级 [R61]。
- EU AI Act 第14条 [R62]【V】：要求高风险 AI 系统能被自然人有效监督；监督者能够理解局限、意识到自动化偏见、正确解读输出、决定不使用或推翻输出、通过"停止"按钮等手段中断系统；对特定生物识别系统，结果须经至少两名具备能力的自然人分别核验确认。

**共性。** 委托、时限、caveat、撤销、"理解—干预—停止"都与托付记录的字段直接对应。

**差距。**
- 访问控制只判断"主体是否有权"，不判断"此动作是否仍服务于托付目的"（基于目的的访问控制只做到部分，且目的是声明值，不可证伪）。
- AI Act 是**法律义务**，不提供可执行的逐动作闸门或证伪测试。

**接近度：部分重叠**（4a 的 Macaroons/UCON 与 4b 的第14条是托付记录字段设计的直接依据）。

## 6. 脉络五：使命工程与使命保证（5）

**做什么。**
- DoD 使命工程指南 MEG 2.0 [R1, R2]。
- SEBoK"Mission Engineering"条目 [R3]【V】：主笔 Judith Dahmann；"使命本身成为关注系统"，在体系层分析"能否达成预期效果"。
- Dahmann & Parasidis 综述 [R4]。
- mKAOS 面向体系使命建模 [R5, R6]。
- MITRE 皇冠宝石分析（使命→资产映射）[R7]。
- Aerospace 使命保证指南 [R8]、NASA 软件保证标准 [R9]。
- NIST 800-160v2 网络弹性"保障使命" [R10]。
- 可信性分类学 [R11]。

**共性。** "交付≠达成"与 MOE/MOP 之分、"使命效果"评估完全同向。

**差距。**
- 使命工程关注的是**体系能力组合与作战线程**，不涉及软件逐动作授权。
- "使命"由组织/作战需求给出，没有托付人、禁区、撤销的记录语义。
- 也没有与形式化验证融合。

**接近度：背景**（但有严重的命名碰撞，见 §11）。

## 7. 脉络六：可信验证融合（6a、6b）

**6a 做什么。**
- seL4 功能正确性证明 [R79, R80]、CompCert [R81]、CakeML [R82]、CertiKOS [R83]、Cogent [R84]、PCC [R88]、DeepSpec [R89]、验证软件大挑战 VSI [R90]。
- LionsOS [R85]：基于 seL4/Microkit 的操作系统。
- HACMS [R87]：在无人机等平台上以 seL4 隔离未验证组件，并经受红队检验。
- 鸿蒙内核 HongMeng [R91]：提供工业级参照。

**一个与 P/U 直接相关的关键事实（已核验）。** Microkit 手册 [R86]【V】写明：Microkit 总是使用 seL4 的 **MCS 配置**，而该配置"仍在验证中，计划 2026 年完成 RISC-V、2027 年完成 AArch64"。因此，**基于 Microkit 构建的发布版并不意味着所用内核已经过验证**。本项目的条件保证 P 必须把这一点显式写入 U 清单。

**6b 做什么。**
- 安全审计日志 [R92]、可防篡改历史树 [R93]、证书透明 RFC 6962 [R94]。
- in-toto [R95]：所有者签名的布局规定"由谁执行哪一步"，并逐步验证链接元数据。

**共性。** "已验证底座 + 显式假设"正是 seL4 证明的表述方式（证明依赖于对硬件、引导与汇编等的假设）。防篡改证据链可直接复用 6b 的技术。

**差距。** 已验证底座保证的是"隔离与实现符合规约"，**不涉及规约是否仍对准人的托付**。in-toto 的"授权步骤"限于供应链场景。

**接近度：背景（6a）／部分重叠（6b）**。

## 8. 脉络七：针对"错配/不对准"的测试（7a、7b、7c）

**7a。**
- 误用用例 [R63]、变异测试 [R64]、蜕变测试 [R65]。
- XACML 策略变异测试 [R66]：通过变异策略检验测试集能否区分"应拒"与"应允"，是与"伪使命测试"最接近的经典技术。
- 规约挖掘 [R67]。

**7b。** AI 安全具体问题 [R68]、规约博弈 [R69]、目标误泛化 [R70, R71]：都在论证"满足字面目标 ≠ 达成意图"。

**7c（最接近的一组）。**
- Greshake 等 [R72] 揭示了间接提示注入：智能体执行"格式合法但非用户本意"的动作。
- South 等 [R73]【V】：认证委托框架。用户签发委托令牌，包含范围、到期/撤销端点与审计地址，并支持人在回路审查。
- CaMeL [R74]【V】：以能力与数据流策略隔离不可信数据。在 AgentDojo 上，可证安全完成的任务为 77%，无防护时为 84%。
- Progent [R75]：为智能体工具调用提供可编程权限策略。
- AgentSentry [R76]【V】（北京大学团队）：按任务生成临时的默认拒绝策略，任务结束即撤销。
- Zhu & Wang [R77]【V】：意图证书，包含请求哈希、主体绑定、动作类别、资源/效应界、置信度、到期与撤销。当工具调用"静态被允许但与当前意图不符"或出现意图漂移时，执行拒绝/澄清；同时维护防篡改的本地审计哈希序列，并给出"不扩权"性质的形式命题。报告的实验中，198 份被接受的草案里有 40 份不安全，执行数为 0。
- 任务漂移检测 [R78]。

**共性。** 7c 几乎逐项对应本项目的托付记录、逐动作闸门与证据链；对抗基准相当于"伪使命测试"的雏形。

**差距。**
- 7c 的托付来自**用户的自然语言请求**，没有具名托付人的禁区、版本与 U 清单。
- 没有与形式化验证底座做条件保证融合。
- 面向 LLM 工具调用，而不是安全关键 CPS。
- 负向测试以注入攻击为主，不是系统化的"角色合法但已失效/越界托付"测试类别。
- 7a 有成熟的充分性理论，但没有"使命"语义。

**接近度：7c 非常接近；7a 部分重叠；7b 背景。**

## 9. 脉络八：医疗与放疗安全（8）

**做什么。**
- Therac-25 事故调查 [R96]：软件联锁失效、复用旧代码中的假设失效。
- IEC 62304 软件生命周期 [R97]、IEC 60601-2-1 电子加速器专用安全标准 [R98]、ISO 14971 风险管理 [R99]。
- IAEA SRS 17 放疗事故教训 [R100]、AAPM TG-100 基于 FMEA 的前瞻风险管理 [R101]、IAEA SAFRON 事件学习系统 [R102]。
- Jacky 等对中子治疗机控制软件的 Z 形式规约 [R103]：核心不变式为"出束时机器设置须与处方一致"（仅见于检索结果，原页面访问超时）。
- 闭环医疗 CPS [R104]。

**共性。** 处方 ≈ 托付记录（具名开具者、范围、版本），联锁 ≈ 逐动作闸门。Therac-25 正是"未覆盖假设 U"失效的典型。

**差距。**
- 标准要求风险控制与可追溯性，但**没有把"处方/授权是否仍有效、是否被撤销、是否越出禁区"作为可证伪的运行时一等制品**。
- 形式规约案例很少与已验证内核融合。

**接近度：部分重叠**（领域语境与监管锚点）。

## 10. 脉络九：中国研究（9）

- **可信软件**：国家自然科学基金"可信软件基础研究"重大研究计划 [R112]，结题综述见何积丰等 [R111]（原 PDF 访问超时）；王怀民等关于网络化可信软件协同开发 [R113]。
- **运行时验证/智能系统**：
  - 陈泽众、邓玉欣《软件学报》2024 [R105]【V】；
  - 徐家乐等《软件学报》2025 [R106]【V】；
  - 卜磊、董威、单云霄《前瞻科技》2023 [R107]【V】：智能系统可信验证，讨论运行时监控与 Simplex 类结构。
- **自适应软件**：金芝团队（北京大学）长期从事需求驱动自适应 [R118]（仅核到主页信息，具体论文未逐篇核验，故不列）。
- **使命工程（国防系统工程，同名不同义）**：
  - 王林尧《使命工程研究综述》2024 [R108]【V】；
  - 王林尧、蒙涛、孙书剑、李任飞《系统工程与电子技术》2026 [R109]【V】：基于 MBSE 的使命工程；
  - 丛林虎等 2024 [R110]：多层级使命任务线程。
- **人类监督伦理**：刘成科、葛燕《走向"有意义的人类控制"》[R114]【V】。
- **医疗器械标准**：YY/T 0664-2020（等同 IEC 62304）[R115]、GB 9706.201-2020（等同 IEC 60601-2-1）[R116]。
- **智能体授权**：AgentSentry [R76]（北大）。
- 结论：**没有检索到使用"使命软件工程"作为学术术语的中文文献**，也没有检索到与本项目合取一致的中文工作。另外，c2.org.cn 上的《智能体安全风险综述》为英文综述的中文译介，不计为原创研究。

**接近度：背景至部分重叠**（AgentSentry 为部分重叠）。

---

## 11. 空白陈述（Gap Statement）

1. **个别要素都有先例**：托付/委托（4a、7c、Secure Tropos）、运行时对准检查（1b、3、7c）、负向/变异测试（7a）、防篡改日志（6b）、形式化条件保证（6a、2b）、人在回路（4b、8）。
2. **"角色合法但不对准即拒绝"已出现于 2025—2026 年的智能体授权研究**（R76、R77，以及 R51 的混淆代理人问题），本项目不能声称首创这一思想。
3. **未检索到的合取**：同一框架同时具备以下各项，且落在放疗联锁场景：
   - (a) 具名托付人，带范围、有效期、版本、禁区、可撤销的托付记录；
   - (b) 逐动作对准闸门；
   - (c) 系统化"伪使命测试"作为验收必要条件；
   - (d) 防篡改证据链；
   - (e) 与 seL4/CompCert 融合的"条件保证 P + 显式未覆盖 U"；
   - (f) "交付≠达成"作为生命周期层贯穿各阶段。
4. **诚实的新意定位**：新意在于**组合与学科化**（把上述要素提炼为软件工程的覆盖层与制品体系）以及**安全关键领域的落地**，而不在单项机制。本项目尚缺实证，需要用"伪使命测试"的检出率、误拒率、闸门开销，以及 Microkit/MCS 未验证状态下 U 的完整性来证明价值。
5. **需优先回应的近作**：Zhu & Wang 2026 [R77]、AgentSentry [R76]、South 等 [R73]、CaMeL [R74]；以及 Assurance 2.0 [R30] 与 ConSerts [R33] 的条件保证思路。

## 12. 命名碰撞说明

- **Mission Engineering / 使命工程**：DoD OUSD(R&E) 的 MEG 2.0 [R1]、SEBoK [R3]、国内 [R108–R110] 中均指**体系（SoS）层的使命分析与设计**，包括使命线程、MOE、体系架构。它与本项目"软件动作须对准人的托付"在对象和方法上都不同。
- **"mission software engineer"**：仅作为工业界**岗位名称**出现（如 Anduril [R12]、Varda [R13]），指航天/防务"任务软件"（飞控、地面段）的工程师，不是学科名。
- **"mission-oriented software engineering"**：见于美国 EPA 合同"MOSES"与 ERT 公司的服务名 [R14]，属商业/合同用语；mKAOS [R5, R6] 中的 "mission-oriented" 指体系使命建模。没有找到作为学术方法论的用法。
- **"使命软件工程"**：中文学术检索中**未发现**这一术语。
- **建议**：首次出现时注明"不同于 DoD/INCOSE 使命工程"。英文可考虑 "Mission Software Engineering (entrustment-aligned)"，或改为 "Entrustment-Aligned Software Engineering" 以避免检索混淆。是否更名由作者决定。

## 13. 检索困难（如实说明）

- 未直接访问 CNKI、万方数据库。中文文献依赖通用检索与期刊官网（jos.org.cn、sys-ele.com、castjournals 等），可能遗漏学位论文与会议论文。
- 以下页面访问超时或被拒，相关条目只能标【S】：
  - ictp.caict.ac.cn：一篇中文智能体授权论文，未纳入；
  - cssjj：eVTOL 运行时保证论文，未纳入；
  - sciengine：何积丰等结题综述 PDF；
  - PMC：HACMS 论文（403）；
  - Jacky 中子治疗规约页面。
- nsfc.gov.cn 返回了无关内容。
- IEC/ISO/ASTM/UL 标准正文需付费，只核到产品页或检索摘要。
- 绝大多数经典文献（如 KAOS、GSN、seL4 2009）只核到检索结果，未逐一打开原文；年份/卷期以检索结果为准。Leveson 专著按 MIT Press 页面信息记为 2012 年（亦常见 2011 年的引用）。

---

## 14. 参考文献

状态：【V】已打开页面核验｜【S】仅见于检索结果（含所打开页面的参考文献列表）

### 使命工程与使命保证
- R1 OUSD(R&E). *Mission Engineering Guide*, Version 2.0. U.S. DoD, 2023. https://ac.cto.mil/wp-content/uploads/2023/11/MEG_2_Oct2023.pdf 【S】
- R2 OUSD(R&E). Mission Engineering（官方页面）. https://ac.cto.mil/mission-engineering/ 【S】
- R3 Dahmann, J.（主笔）等. "Mission Engineering". *SEBoK* (Guide to the Systems Engineering Body of Knowledge), 2026 年在线版. https://sebokwiki.org/wiki/Mission_Engineering 【V】
- R4 Dahmann, J.; Parasidis, G. "Mission Engineering: A Technical Perspective". *ITEA Journal of Test and Evaluation* 45(3), 2024. https://itea.org/journals/volume-45-3/mission-engineering/ 【S】
- R5 Silva, E.; Batista, T.; Oquendo, F. 等. mKAOS 相关工作（SESoS 研讨会），2015. https://dl.acm.org/doi/10.5555/2821418.2821426 【S】
- R6 "Formal modeling systems-of-systems missions with mKAOS". ACM SAC 2018. https://dl.acm.org/doi/10.1145/3167132.3167311 【S】
- R7 MITRE. Crown Jewels Analysis. https://www.mitre.org/our-impact/intellectual-property/crown-jewels-analysis 【S】
- R8 The Aerospace Corporation. *Mission Assurance Guide*, TOR-2007(8546)-6018 Rev. B, 2012. https://everyspec.com/USAF/TORs/TOR-2007-8546-6018_REV-B_53310/ 【S】
- R9 NASA. NASA-STD-8739.8B *Software Assurance and Software Safety Standard*. https://standards.nasa.gov/standard/nasa/nasa-std-87398 【S】
- R10 NIST. SP 800-160 Vol. 2 Rev. 1 *Developing Cyber-Resilient Systems*, 2021. https://csrc.nist.gov/pubs/sp/800/160/v2/r1/final 【S】
- R11 Avizienis, A.; Laprie, J.-C.; Randell, B.; Landwehr, C. "Basic Concepts and Taxonomy of Dependable and Secure Computing". *IEEE TDSC* 1(1), 2004. https://dl.acm.org/doi/abs/10.1109/TDSC.2004.2 【S】
- R12 Anduril Industries. "Mission Software Engineer" 招聘页, 2026. https://boards.greenhouse.io/andurilindustries/jobs/5226925007 【S】
- R13 Varda Space Industries. "Mission Software Engineer" 招聘页, 2026. https://job-boards.greenhouse.io/vardaspace/jobs/7846477003 【S】
- R14 ERT. "Mission-Oriented Software Engineering Services". https://www.environmental-expert.com/services/mission-oriented-software-engineering-services-256304 【S】

### 目标/义务导向需求工程
- R15 Dardenne, A.; van Lamsweerde, A.; Fickas, S. "Goal-directed requirements acquisition". *Science of Computer Programming* 20, 1993. https://www.sciencedirect.com/science/article/pii/016764239390021G 【S】
- R16 van Lamsweerde, A. "Goal-Oriented Requirements Engineering: A Guided Tour". RE 2001. https://webperso.info.ucl.ac.be/~avl/files/RE01.pdf 【S】
- R17 van Lamsweerde, A.; Letier, E. "Handling Obstacles in Goal-Oriented Requirements Engineering". *IEEE TSE* 26(10), 2000. https://dl.acm.org/doi/10.1109/32.879820 【S】
- R18 Yu, E. "Towards Modelling and Reasoning Support for Early-Phase Requirements Engineering". RE 1997. https://www.cs.toronto.edu/pub/eric/RE97.pdf 【S】
- R19 Bresciani, P.; Perini, A.; Giorgini, P.; Giunchiglia, F.; Mylopoulos, J. "Tropos: An Agent-Oriented Software Development Methodology". *JAAMAS* 8, 2004. https://dl.acm.org/doi/abs/10.1023/B:AGNT.0000018806.20944.EF 【S】
- R20 Giorgini, P.; Massacci, F.; Mylopoulos, J.; Zannone, N. "Modeling Security Requirements Through Ownership, Permission and Delegation". RE 2005. http://www.dit.unitn.it/~massacci/Publications/GIOR-MASS-MYLO-ZANN-05-RE-Paper.pdf 【S】
- R21 Fickas, S.; Feather, M. S. "Requirements Monitoring in Dynamic Environments". RE 1995. https://researchr.org/publication/FickasF95 【S】
- R22 Feather, M. S.; Fickas, S.; van Lamsweerde, A.; Ponsard, C. "Reconciling System Requirements and Runtime Behavior". IWSSD 1998. https://researchr.org/publication/FeatherFLP98 【S】
- R23 Whittle, J.; Sawyer, P.; Bencomo, N.; Cheng, B. H. C.; Bruel, J.-M. "RELAX: Incorporating Uncertainty into the Specification of Self-Adaptive Systems". RE 2009. https://cse.msu.edu/~mckinley/Pubs/files/Whittle.RELAX.2009.pdf 【S】
- R24 Bencomo, N.; Whittle, J.; Sawyer, P.; Finkelstein, A.; Letier, E. "Requirements reflection: requirements as runtime entities". ICSE 2010. https://dl.acm.org/doi/10.1145/1810295.1810329 【S】
- R25 Gotel, O.; Finkelstein, A. "An Analysis of the Requirements Traceability Problem". ICRE 1994. http://www0.cs.ucl.ac.uk/staff/A.Finkelstein/papers/rtprob.pdf 【S】

### 保证案例与动态保证
- R26 Kelly, T.; Weaver, R. "The Goal Structuring Notation – A Safety Argument Notation". DSN 2004 Workshop on Assurance Cases. https://www-users.cs.york.ac.uk/tpk/dsn2004.pdf 【S】
- R27 SCSC Assurance Case Working Group. *GSN Community Standard* Version 3, 2021. https://scsc.uk/gsn 【S】
- R28 Bishop, P.; Bloomfield, R. "A Methodology for Safety Case Development". Safety-Critical Systems Symposium 1998. https://openaccess.city.ac.uk/549/ 【S】
- R29 OMG. *Structured Assurance Case Metamodel (SACM)* 2.2. https://www.omg.org/spec/SACM/2.2/ 【S】
- R30 Bloomfield, R.; Rushby, J. "Assurance 2.0: A Manifesto". arXiv:2004.10474, 2020. https://arxiv.org/abs/2004.10474 【V】
- R31 Goodenough, J. B.; Weinstock, C. B.; Klein, A. Z. "Eliminative induction: A basis for arguing system confidence". ICSE 2013 (NIER). https://dl.acm.org/doi/abs/10.5555/2486788.2486950 【S】
- R32 Goodenough, J. B.; Weinstock, C. B.; Klein, A. Z. *Eliminative Argumentation: A Basis for Arguing Confidence in System Properties*. CMU/SEI 技术报告, 2015. https://www.sei.cmu.edu/library/eliminative-argumentation-a-basis-for-arguing-confidence-in-system-properties/ 【S】
- R33 Schneider, D.; Trapp, M. "Conditional Safety Certification of Open Adaptive Systems". *ACM TAAS* 8(2), 2013. https://dl.acm.org/doi/abs/10.1145/2491465.2491467 【S】
- R34 Denney, E.; Pai, G.; Habli, I. "Dynamic Safety Cases for Through-Life Safety Assurance". ICSE 2015 (NIER). https://ntrs.nasa.gov/citations/20150011054 【V】
- R35 Sorokin, L.; Bouchekir, R.; Beyene, T. A.; Liao, B.; Molin, A. "Towards Continuous Assurance Case Creation for ADS with the Evidential Tool Bus". arXiv:2403.01918, 2024. https://arxiv.org/abs/2403.01918 【V】
- R36 Hawkins, R. 等. *Guidance on the Assurance of Machine Learning in Autonomous Systems (AMLAS)*. University of York, 2021. https://www.york.ac.uk/assuring-autonomy/guidance/amlas/ 【S】
- R37 UL. UL 4600 *Standard for Evaluation of Autonomous Products*（第3版 2023）; Koopman, P. 相关解读, 2023. https://users.ece.cmu.edu/~koopman/pubs/Koopman2023_UL4600_Safety_Case.pdf 【S】
- R38 ISO 21448:2022 *Road vehicles — Safety of the intended functionality*. https://www.iso.org/standard/77490.html 【S】
- R39 Leveson, N. G. *Engineering a Safer World*. MIT Press, 2012. https://mitpress.mit.edu/9780262297301/engineering-a-safer-world/ 【S】

### 运行时验证与强制
- R40 Leucker, M.; Schallhart, C. "A brief account of runtime verification". *J. Logic and Algebraic Programming* 78(5), 2009. https://www.sciencedirect.com/science/article/pii/S1567832608000775 【S】
- R41 Bartocci, E.; Falcone, Y. (eds.). *Lectures on Runtime Verification*. Springer LNCS 10457, 2018. https://link.springer.com/book/10.1007/978-3-319-75632-5 【S】
- R42 Falcone, Y.; Fernandez, J.-C.; Mounier, L. "What can you verify and enforce at runtime?". *STTT*, 2012（Crossref 记录 2011 年在线）. https://link.springer.com/article/10.1007/s10009-011-0196-8 【S】
- R43 Schneider, F. B. "Enforceable Security Policies". *ACM TISSEC* 3(1), 2000. https://dl.acm.org/doi/10.1145/353323.353382 【S】
- R44 Ligatti, J.; Bauer, L.; Walker, D. "Edit automata: enforcement mechanisms for run-time security policies". *Int. J. Information Security* 4, 2005. https://link.springer.com/article/10.1007/s10207-004-0046-8 【S】
- R45 Sha, L. "Using Simplicity to Control Complexity". *IEEE Software* 18(4), 2001. https://doi.org/10.1109/MS.2001.936213 【S】
- R46 ASTM F3269-21 *Standard Practice for Methods to Safely Bound Behavior of Aircraft Systems Containing Complex Functions Using Run-Time Assurance*. https://store.astm.org/f3269-21.html 【S】
- R47 Alshiekh, M.; Bloem, R.; Ehlers, R.; Könighofer, B.; Niekum, S.; Topcu, U. "Safe Reinforcement Learning via Shielding". AAAI 2018. https://ojs.aaai.org/index.php/AAAI/article/view/11797 【S】
- R48 Mitsch, S.; Platzer, A. "ModelPlex: verified runtime validation of verified cyber-physical system models". *Formal Methods in System Design* 49, 2016. https://link.springer.com/article/10.1007/s10703-016-0241-z 【S】

### 授权、委托、策略
- R49 Dennis, J. B.; Van Horn, E. C. "Programming Semantics for Multiprogrammed Computations". *CACM* 9(3), 1966. https://dl.acm.org/doi/10.1145/365230.365252 【S】
- R50 Saltzer, J. H.; Schroeder, M. D. "The Protection of Information in Computer Systems". *Proc. IEEE* 63(9), 1975. https://www.cs.virginia.edu/~evans/cs551/saltzer/ 【S】
- R51 Hardy, N. "The Confused Deputy". *ACM SIGOPS OSR* 22(4), 1988. https://dl.acm.org/doi/10.1145/54289.871709 【S】
- R52 Miller, M. S.; Yee, K.-P.; Shapiro, J. *Capability Myths Demolished*. Tech. Report SRL2003-02, JHU, 2003. http://srl.cs.jhu.edu/pubs/SRL2003-02.pdf 【S】
- R53 Lampson, B.; Abadi, M.; Burrows, M.; Wobber, E. "Authentication in Distributed Systems: Theory and Practice". *ACM TOCS* 10(4), 1992. https://dl.acm.org/doi/10.1145/138873.138874 【S】
- R54 Park, J.; Sandhu, R. "The UCON_ABC Usage Control Model". *ACM TISSEC* 7(1), 2004. https://dl.acm.org/doi/10.1145/984334.984339 【S】
- R55 OASIS. *eXtensible Access Control Markup Language (XACML) Version 3.0*, 2013. https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html 【S】
- R56 Pang, R. 等. "Zanzibar: Google's Consistent, Global Authorization System". USENIX ATC 2019. https://www.usenix.org/conference/atc19/presentation/pang 【S】
- R57 Birgisson, A.; Politz, J. G.; Erlingsson, Ú.; Taly, A.; Vrable, M.; Lentczner, M. "Macaroons: Cookies with Contextual Caveats for Decentralized Authorization in the Cloud". NDSS 2014. https://www.ndss-symposium.org/ndss2014/programme/macaroons-cookies-contextual-caveats-decentralized-authorization-cloud/ 【S】
- R58 Crampton, J.; Khambhammettu, H. "Delegation in Role-Based Access Control". ESORICS 2006. https://doi.org/10.1007/11863908_12 【S】
- R59 Byun, J.-W.; Li, N. "Purpose based access control for privacy protection in relational database systems". *VLDB Journal*（Crossref 记录 2006 年在线发表）. https://doi.org/10.1007/s00778-006-0023-0 【S】

### 人类监督
- R60 Santoni de Sio, F.; van den Hoven, J. "Meaningful Human Control over Autonomous Systems: A Philosophical Account". *Frontiers in Robotics and AI* 5, 2018. https://www.frontiersin.org/articles/10.3389/frobt.2018.00015/full 【S】
- R61 Parasuraman, R.; Sheridan, T. B.; Wickens, C. D. "A model for types and levels of human interaction with automation". *IEEE Trans. SMC-A* 30(3), 2000. https://ieeexplore.ieee.org/document/844354 【S】
- R62 European Union. Regulation (EU) 2024/1689 (AI Act), Article 14 "Human oversight"（AI Act Service Desk 汇编文本）. https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-14 【V】

### 测试（误用/变异/蜕变/策略）
- R63 Sindre, G.; Opdahl, A. L. "Eliciting security requirements with misuse cases". *Requirements Engineering* 10, 2005（2004 年在线）. https://link.springer.com/article/10.1007/s00766-004-0194-4 【S】
- R64 Jia, Y.; Harman, M. "An Analysis and Survey of the Development of Mutation Testing". *IEEE TSE* 37(5), 2011. https://ieeexplore.ieee.org/document/5487526 【S】
- R65 Chen, T. Y. 等. "Metamorphic Testing: A Review of Challenges and Opportunities". *ACM Computing Surveys* 51(1), 2018. https://dl.acm.org/doi/10.1145/3143561 【S】
- R66 Martin, E.; Xie, T.; Yu, T. "Defining and Measuring Policy Coverage in Testing Access Control Policies". ICICS 2006. https://link.springer.com/chapter/10.1007/11935308_11 【S】
- R67 Ammons, G.; Bodík, R.; Larus, J. R. "Mining Specifications". POPL 2002. https://dl.acm.org/doi/10.1145/503272.503275 【S】

### AI 对齐与智能体授权
- R68 Amodei, D. 等. "Concrete Problems in AI Safety". arXiv:1606.06565, 2016. https://arxiv.org/abs/1606.06565 【S】
- R69 Krakovna, V. 等. "Specification gaming: the flip side of AI ingenuity". DeepMind Blog, 2020. https://deepmind.google/discover/blog/specification-gaming-the-flip-side-of-ai-ingenuity/ 【S】
- R70 Langosco, L. 等. "Goal Misgeneralization in Deep Reinforcement Learning". ICML 2022. https://proceedings.mlr.press/v162/langosco22a.html 【S】
- R71 Shah, R. 等. "Goal Misgeneralization: Why Correct Specifications Aren't Enough For Correct Goals". arXiv:2210.01790, 2022. https://arxiv.org/abs/2210.01790 【S】
- R72 Greshake, K. 等. "Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection". AISec 2023. https://arxiv.org/abs/2302.12173 【S】
- R73 South, T. 等. "Authenticated Delegation and Authorized AI Agents". arXiv:2501.09674, 2025. https://arxiv.org/abs/2501.09674 【V】
- R74 Debenedetti, E. 等. "Defeating Prompt Injections by Design"（CaMeL）. arXiv:2503.18813, 2025. https://arxiv.org/abs/2503.18813 【V】
- R75 Shi, T. 等. "Progent: Securing AI Agents with Privilege Control"（arXiv 现行标题）. arXiv:2504.11703, 2025. https://arxiv.org/abs/2504.11703 【S】
- R76 Cai, R. 等（北京大学）. "AgentSentry: ... task-centric access control for computer-use agents". SaTS 2025, DOI 10.1145/3733824.3764872; arXiv:2510.26212. https://arxiv.org/abs/2510.26212 【V】
- R77 Zhu; Wang（Accentrust）. "Intent-Governed Tool Authorization for AI Agents". arXiv:2606.22916, 2026. https://arxiv.org/abs/2606.22916 【V】
- R78 Abdelnabi, S. 等. "Get my drift? Catching LLM Task Drift with Activation Deltas"（TaskTracker）. arXiv:2406.00799, 2024. https://arxiv.org/abs/2406.00799 【S】

### 可信验证（seL4 生态等）
- R79 Klein, G. 等. "seL4: Formal Verification of an OS Kernel". SOSP 2009. https://dl.acm.org/doi/10.1145/1629575.1629596 【S】
- R80 Klein, G. 等. "Comprehensive Formal Verification of an OS Microkernel". *ACM TOCS* 32(1), 2014. https://dl.acm.org/doi/10.1145/2560537 【S】
- R81 Leroy, X. "Formal verification of a realistic compiler". *CACM* 52(7), 2009. https://dl.acm.org/doi/10.1145/1538788.1538814 【S】
- R82 Kumar, R.; Myreen, M. O.; Norrish, M.; Owens, S. "CakeML: A Verified Implementation of ML". POPL 2014. https://dl.acm.org/doi/10.1145/2535838.2535841 【S】
- R83 Gu, R. 等. "CertiKOS: An Extensible Architecture for Building Certified Concurrent OS Kernels". OSDI 2016. https://www.usenix.org/conference/osdi16/technical-sessions/presentation/gu 【S】
- R84 Amani, S. 等. "Cogent: Verifying High-Assurance File System Implementations". ASPLOS 2016. https://dl.acm.org/doi/10.1145/2872362.2872404 【S】
- R85 Heiser, G. 等. "Fast, Secure, Adaptable: LionsOS Design, Implementation and Performance". arXiv:2501.06234, 2025. https://arxiv.org/abs/2501.06234 【S】
- R86 seL4 Foundation. *seL4 Microkit Manual*（v2.3.1, latest）. https://docs.sel4.systems/projects/microkit/manual/latest/ 【V】
- R87 Fisher, K.; Launchbury, J.; Richards, R. "The HACMS program: using formal methods to eliminate exploitable bugs". *Phil. Trans. R. Soc. A* 375, 2017. https://pmc.ncbi.nlm.nih.gov/articles/PMC5597724/ 【S】（访问返回 403）
- R88 Necula, G. C. "Proof-Carrying Code". POPL 1997. https://dl.acm.org/doi/10.1145/263699.263712 【S】
- R89 Appel, A. W. 等. "Position paper: the science of deep specification". *Phil. Trans. R. Soc. A* 375, 2017. https://royalsocietypublishing.org/doi/10.1098/rsta.2016.0331 【S】
- R90 Hoare, C. A. R.; Misra, J.; Leavens, G. T.; Shankar, N. "The Verified Software Initiative: A Manifesto". *ACM Computing Surveys* 41(4), 2009. https://dl.acm.org/doi/10.1145/1592434.1592439 【S】
- R91 Chen, H. 等. "Microkernel Goes General: Performance and Compatibility in the HongMeng Production Microkernel". OSDI 2024. https://www.usenix.org/conference/osdi24/presentation/chen-haibo 【S】

### 防篡改证据
- R92 Schneier, B.; Kelsey, J. "Secure Audit Logs to Support Computer Forensics". *ACM TISSEC* 2(2), 1999. https://dl.acm.org/doi/10.1145/317087.317089 【S】
- R93 Crosby, S. A.; Wallach, D. S. "Efficient Data Structures for Tamper-Evident Logging". USENIX Security 2009. https://www.usenix.org/legacy/event/sec09/tech/full_papers/crosby.pdf 【S】
- R94 Laurie, B.; Langley, A.; Kasper, E. RFC 6962 *Certificate Transparency*, 2013. https://www.rfc-editor.org/rfc/rfc6962 【S】
- R95 Torres-Arias, S. 等. "in-toto: Providing farm-to-table guarantees for bits and bytes". USENIX Security 2019. https://www.usenix.org/conference/usenixsecurity19/presentation/torres-arias 【S】

### 医疗与放疗安全
- R96 Leveson, N. G.; Turner, C. S. "An Investigation of the Therac-25 Accidents". *IEEE Computer* 26(7), 1993. https://doi.org/10.1109/MC.1993.274940 【S】
- R97 IEC 62304:2006+AMD1:2015 *Medical device software — Software life cycle processes*. https://webstore.iec.ch/en/publication/22794 【S】
- R98 IEC 60601-2-1:2020 *Particular requirements for basic safety and essential performance of electron accelerators*. https://webstore.iec.ch/ （具体产品页链接失效，需在 IEC Webstore 检索） 【S】
- R99 ISO 14971:2019 *Medical devices — Application of risk management*. https://www.iso.org/standard/72704.html 【S】
- R100 IAEA. Safety Reports Series No. 17 *Lessons Learned from Accidental Exposures in Radiotherapy*, 2000. https://www.iaea.org/publications/5980/lessons-learned-from-accidental-exposures-in-radiotherapy 【S】
- R101 Huq, M. S. 等. "The report of Task Group 100 of the AAPM: Application of risk analysis methods to radiation therapy quality management". *Medical Physics* 43(7), 2016. https://pmc.ncbi.nlm.nih.gov/articles/PMC4985013/ 【S】
- R102 IAEA. SAFRON (Safety in Radiation Oncology). https://www.iaea.org/resources/rpop/resources/databases-and-learning-systems/safron 【S】
- R103 Jacky, J.; Patrick, M.; Unger, J. 中子治疗机控制软件的 Z 形式规约（Clinical Neutron Therapy System 相关报告/论文，1990 年代）. https://staff.washington.edu/jon/cnts/iccr.html 【S】（原页面超时）
- R104 Arney, D.; Pajic, M.; Goldman, J. M.; Lee, I.; Mangharam, R.; Sokolsky, O. "Toward patient safety in closed-loop medical device systems". ICCPS 2010. https://dl.acm.org/doi/10.1145/1795194.1795214 【S】

### 中国研究
- R105 陈泽众, 邓玉欣. 运行时验证相关论文. 《软件学报》, 2024. https://www.jos.org.cn/josen/article/abstract/7126 【V】
- R106 徐家乐 等. 智能系统运行时验证/监控相关论文. 《软件学报》, 2025. https://www.jos.org.cn/josen/article/abstract/7351 【V】
- R107 卜磊, 董威, 单云霄. 智能系统可信验证相关综述. 《前瞻科技》, 2023. https://www.castjournals.com/ 【V】
- R108 王林尧. 《使命工程研究综述》. 体系工程学术会议论文, 2024. https://www.aconf.cn/ 【V】
- R109 王林尧, 蒙涛, 孙书剑, 李任飞. 基于 MBSE 的使命工程方法. 《系统工程与电子技术》, 2026. https://www.sys-ele.com/ 【V】
- R110 丛林虎 等. 多层级使命任务线程相关研究. 《系统工程与电子技术》, 2024（见 R109 参考文献）. https://www.sys-ele.com/ 【S】
- R111 何积丰 等. "可信软件基础研究"重大研究计划结题综述. 《中国科学基金》, 2018. https://www.sciengine.com/ 【S】（PDF 访问超时）
- R112 国家自然科学基金委员会. "可信软件基础研究"重大研究计划. https://www.nsfc.gov.cn/ 【S】
- R113 王怀民 等. 基于网络的可信软件大规模协同开发与演化. 《中国科学：信息科学》, 2014. https://www.trustie.net/ 【S】
- R114 刘成科, 葛燕. 《走向"有意义的人类控制"》. 期刊 ISSN 1008-7699, 2023 年第 1 期, DOI 10.16452/j.cnki.sdkjsk.2023.01.006. https://doi.org/10.16452/j.cnki.sdkjsk.2023.01.006 【V】
- R115 YY/T 0664-2020《医疗器械软件 软件生存周期过程》. https://std.samr.gov.cn/ 【S】
- R116 GB 9706.201-2020《医用电气设备 第2-1部分：能量为 1 MeV 至 50 MeV 电子加速器的基本安全和基本性能专用要求》. https://std.samr.gov.cn/ 【S】
- R117 （空号，原拟收录条目已合并入 R76）
- R118 金芝（北京大学）个人主页（需求驱动自适应系统研究方向）. https://cs.pku.edu.cn/ 【S】

**DOI 核对**：R6, R11, R15, R17, R19, R24, R33, R40, R42, R43, R44, R45, R47, R48, R49, R51, R53, R54, R57, R58, R59, R60, R61, R63, R64, R65, R66, R67, R79, R80, R81, R82, R84, R88, R89, R90, R92, R96, R101, R104 共 40 条的 DOI，已于 2026-10-09 经 Crossref 元数据 API 核对标题与年份一致（ACM/IEEE/出版社页面对抓取返回 403，故状态仍记为【S】）；其中 R58、R59、R96、R45 的链接已按 Crossref 结果更正。R68、R71、R72、R75、R78、R85 的 arXiv 编号与标题已经 arXiv API 核对。

**统计**：有效条目 117 条（R117 为空号）。【V】16 条：R3, R30, R34, R35, R62, R73, R74, R76, R77, R86, R105–R109, R114；【S】101 条；【M】0 条。
注：部分【S】条目的 URL 是按检索结果中出现的出版方/机构页面记录的，作者列表中的"等"表示未逐一核实其余作者。
