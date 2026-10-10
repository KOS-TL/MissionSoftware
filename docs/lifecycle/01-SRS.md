# 软件需求规格说明书（SRS）

> **仓库化说明（v0.1.0）**：本文为项目过程中的历史文档，按原文收录，仅做去个人化处理：作者本机路径已替换为 `<REPO_ROOT>`（= 本仓库克隆目录，内含 `mission-shell/` 与 `microkit-sdk-2.3.1/`）、`<WORKDIR>`（作者文档目录）或仓库内相对路径；形如 `/workspace/...` 的路径是作者沙箱（box）上的历史路径，在本仓库中分别对应 `mission-shell/`（原 `/workspace/microkit-mission-shell/`）与 `docs/`。文中命令含占位符，**不能直接复制执行**；可直接执行的命令见仓库根目录 `README.md` 与 `docs/REPRODUCE.md`。


**系统名称**：基于 seL4 Microkit 的使命约束外壳（mission-shell）  
**文档版本**：1.0.0  
**日期**：2026-09-23  
**对齐行为**：`DEMO_PROFILE=full`（`scenarios/client_full.c`）  
**保证立场**：非临床；K=cited；delivery≠achievement；共签=演示占位；FNV-1a32=教学级

---

## 1. 引言

### 1.1 目的

规定 mission-shell 在仿真环境下的功能、非功能、负面需求及验收准则，使需求、设计、实现与测试可双向追溯，并为「明示托付 ∧ 仍对准 ∧ 可证伪」提供可机检规格。

### 1.2 范围

- **在范围内**：Microkit 用户态两保护域、PPC 协议门闩、人共签状态机、假使命拒绝集、演示级证据链、三档 `DEMO_PROFILE`、Docker+QEMU 复现。  
- **在范围外**：真硬件出束、临床剂量/联锁、密码学强度审计链、电子签名合规、seL4 应用级形式化证明、MRTDS 成品业务。

### 1.3 定义与缩略语

见第 9 节术语表。

### 1.4 参考

- 开题报告：题目1《基于 Microkit 的使命约束外壳》  
- `traditional-SE-embedded-in-mission-shell.md`  
- `docs/PU_BOUNDARY.md`  
- Microkit SDK 2.3.1；board=`qemu_virt_aarch64`

---

## 2. 总体描述

### 2.1 产品透视

在 seL4/Microkit 条件保证之上，构造**可观察的使命门闩**，防止将「内核已验证 / 测试绿 / 仿真放行」误读为「人托付的那件事现仍被正确地做」。

### 2.2 干系人

| 角色 | 关注点 |
|---|---|
| 课题学生（实现与答辩） | 可复现演示、日志可指认、口径不越界 |
| 指导教师 | 需求完整性、负面需求、K/A/M/U 边界 |
| 演示观众 | 共签前后差异、假使命拒绝、证据 tip |
| （非）临床/法规角色 | 本系统**不服务**其验收；明确排除 |

### 2.3 运行环境

- 宿主机：Windows + Docker（镜像 `trustworthysystems/sel4:latest`）  
- 目标：`qemu_virt_aarch64`，Microkit config=`debug`  
- SDK：`microkit-sdk-2.3.1`

### 2.4 约束与假设

- 共签消息由场景客户端发起，**模拟**人审判通道，非真实 UI/签名设备。  
- QEMU `timeout` 导致进程退出码 124 **可接受**，不以进程 rc=0 为通过判据。  
- 串口日志关键词构成验收契约。

---

## 3. 功能需求

### R1 明示托付（人共签通道）

| 子项 | 描述 | 优先级 |
|---|---|---|
| R1.1 | 系统启动后 `human_cosign_ok` 默认为假（OFF） | 必须 |
| R1.2 | 未 GRANT 时，任何需对准检查的使能类请求返回 `REP_DENY`，串口含 `GATE|DENY|no_human_cosign` | 必须 |
| R1.3 | 支持 `REQ_HUMAN_COSIGN_GRANT` → 状态 ON，串口 `GATE|COSIGN|GRANT (demo stand-in)` | 必须 |
| R1.4 | 支持 `REQ_HUMAN_COSIGN_REVOKE` → 状态 OFF，串口 `GATE|COSIGN|REVOKE` | 必须 |
| R1.5 | 支持 `REQ_HUMAN_COSIGN_QUERY` → `REP_COSIGN_ON`/`OFF`，串口 `GATE|COSIGN|STATE=ON|OFF` | 必须 |
| R1.6 | 禁止静默共签（启动即 ON、配置文件隐式 true） | 必须 |
| R1.7 | 需求声明：共签为**演示占位**，不等于电子签名/法规共签 | 必须 |

**验收（full）**：先 QUERY→OFF；`legal_before_cosign`→DENY；GRANT 后再 QUERY→ON。

### R2 仍对准托付（假使命拒绝集）

在共签 **ON** 之后，下列请求仍必须 DENY（假使命，非可选）：

| ID | 请求标签（协议） | 期望串口原因 | 协议常量 |
|---|---|---|---|
| R2.1 | expired_trust | `GATE|DENY|expired_entrustment` | `REQ_EXPIRED_TRUST` (2) |
| R2.2 | forbidden_zone | `GATE|DENY|forbidden_zone` | `REQ_FORBIDDEN_ZONE` (3) |
| R2.3 | advisor_enable | `GATE|DENY|advisor_cannot_enable` | `REQ_ADVISOR_ENABLE` (4) |
| R2.4 | empty_u_achieve | `GATE|DENY|empty_U_no_achieve_tag` | `REQ_EMPTY_U_ACHIEVE` (5) |

**使命叠加**：即使「功能上想放行」，对准失败也不得以成功码掩盖。

### R3 合法路径的弱成功语义（ALLOW_SIM）

| 子项 | 描述 |
|---|---|
| R3.1 | 共签 ON 且请求为 `REQ_LEGAL_ENABLE` 时，返回 `REP_ALLOW_SIM`，串口 `GATE|ALLOW_SIM|legal_path_sim` |
| R3.2 | 必须伴随 `GATE|NOTE|sim_only; delivery!=achievement; non-clinical` |
| R3.3 | 需求与验收中**禁止**将 `ALLOW_SIM` 表述为「使命达成」 |
| R3.4 | 本系统不提供 `ACHIEVE` 类成功码 |

### R4 检查可证伪（证据链）

| 子项 | 描述 |
|---|---|
| R4.1 | 关键判定与共签变更追加证据事件；算法为 FNV-1a 32-bit 演示链 |
| R4.2 | 每条日志形如 `EVIDENCE|seq=…|prev=…|this=…|<event>` |
| R4.3 | `REQ_EVIDENCE_TIP` 打印 `GATE|CHAIN|tip=<hex>|len=<n>` |
| R4.4 | `DEMO_PROFILE=full` 期望 `len=10`（见测试报告事件表） |
| R4.5 | 需求声明：教学用顺序联结，**不作**密码学抗碰撞/抗伪造保证 |

### R5 负面需求（Negative requirements）

| ID | 禁止项 |
|---|---|
| R5.1 | 不出束、无厂商写使能接口、无注册材料路径 |
| R5.2 | 不重做 seL4 证明；不宣称应用级 seL4/CompCert 保证 |
| R5.3 | 不实现真实临床剂量/联锁业务（外壳≠MRTDS 成品） |
| R5.4 | 未知请求标签 → `DENY|unknown_request`（不得默许） |

### R6 场景剖面可切换（可测试性需求）

| ID | 描述 |
|---|---|
| R6.1 | 构建变量 `DEMO_PROFILE∈{full, cosign_only, false_only}` 选择不同 client 场景源 |
| R6.2 | 默认 `full`；未知 profile 构建失败 |
| R6.3 | 各剖面结束须打印 `CLIENT|INFO|MISSION_SHELL_DEMO_DONE` |

### R7 保护域与通道结构

| ID | 描述 |
|---|---|
| R7.1 | 存在被动 PD `gatekeeper`（priority 100, passive）与主动 PD `client`（priority 99） |
| R7.2 | 二者经 channel id=0 通信；client 端 `pp=true`（PPC） |
| R7.3 | 门闩逻辑仅在 gatekeeper 的 `protected` 入口实施 |

---

## 4. 非功能需求

| ID | 类别 | 描述 |
|---|---|---|
| NFR1 | 可复现性 | 同一 Docker 命令在约定挂载下可复现串口关键词序列 |
| NFR2 | 可观察性 | 关键路径稳定英文关键词；便于脚本 grep 与答辩指认 |
| NFR3 | 构建确定性 | 交叉编译 freestanding；`-Wall -Werror` |
| NFR4 | 超时策略 | `timeout 30s` QEMU；rc=124 不单独构成失败 |
| NFR5 | 文档一致性 | 日志契约与 SRS/追溯矩阵同步维护 |

---

## 5. 接口需求（逻辑）

### 5.1 请求标签（`mission_proto.h`）

| 符号 | 值 | 含义 |
|---|---|---|
| `REQ_LEGAL_ENABLE` | 1 | 合法仿真使能请求 |
| `REQ_EXPIRED_TRUST` | 2 | 过期托付 |
| `REQ_FORBIDDEN_ZONE` | 3 | 禁区 |
| `REQ_ADVISOR_ENABLE` | 4 | 顾问妄图使能 |
| `REQ_EMPTY_U_ACHIEVE` | 5 | 空 U 贴达成 |
| `REQ_HUMAN_COSIGN_GRANT` | 20 | 共签授予 |
| `REQ_HUMAN_COSIGN_REVOKE` | 21 | 共签撤销 |
| `REQ_HUMAN_COSIGN_QUERY` | 22 | 共签查询 |
| `REQ_EVIDENCE_TIP` | 23 | 证据 tip 查询 |

### 5.2 应答标签

| 符号 | 值 |
|---|---|
| `REP_ALLOW_SIM` | 10 |
| `REP_DENY` | 11 |
| `REP_OK` | 12 |
| `REP_COSIGN_ON` | 13 |
| `REP_COSIGN_OFF` | 14 |
| `REP_EVIDENCE_TIP` | 15 |

---

## 6. 验收准则（Acceptance）

### 6.1 命令（唯一推荐）

```bat
docker run --rm -e DEMO_PROFILE=full -v <REPO_ROOT>:/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_build_run.sh
```

### 6.2 full 剖面通过条件（合取）

1. 出现 `GATE|COSIGN|STATE=OFF` 与随后 `GATE|DENY|no_human_cosign`  
2. 出现 `GATE|COSIGN|GRANT` 与 `STATE=ON`  
3. 出现 `GATE|ALLOW_SIM|legal_path_sim` 与 `GATE|NOTE|sim_only; delivery!=achievement; non-clinical`  
4. 四条假使命 DENY 原因齐全（R2.1–R2.4）  
5. 出现 `GATE|COSIGN|REVOKE` 与再次 `no_human_cosign`  
6. 出现 `GATE|CHAIN|tip=…|len=10`  
7. 出现 `CLIENT|INFO|MISSION_SHELL_DEMO_DONE`  
8. **无效依据**：缺少 `DEMO_PROFILE=full` 声明的旧跑通日志  

### 6.3 失败条件（示例）

- 假使命变为 ALLOW_SIM  
- REVOKE 后合法路径仍 ALLOW_SIM  
- tip/len 与事件数不符  
- 将 ALLOW_SIM 在报告中写成「达成」

---

## 7. 需求优先级与依赖

R1、R2、R3、R4、R5 为关键路径必须；R6、R7 支撑可测试性与结构。R2 依赖 R1（共签 ON）；R3 依赖 R1；R4 横贯 R1–R3。

---

## 8. 追溯钩子

每条 R* 在 `07-需求追溯矩阵.md` 中映射到设计决策 D*、源文件/符号、测试用例 ID、串口关键词。

---

## 9. 术语表

| 术语 | 含义 |
|---|---|
| 明示托付 | 人侧共签通道显式 GRANT，默认 OFF |
| 仍对准 | 当前请求未落入过期/禁区/顾问使能/空U达成等假使命 |
| 可证伪 | 判定写入可查询证据链与稳定日志 |
| ALLOW_SIM | 仿真弱放行；≠成就 |
| K/A/M/U | 引用内核 / 应用演示 / 使命纪律 / 未覆盖域 |
| PPC | Protected Procedure Call（Microkit pp 通道） |
| PD | Protection Domain |
| DEMO_PROFILE | 构建期场景选择器 |

---

## 10. 附录：full 剖面客户端请求序列（需求视角）

1. query_cosign  
2. legal_before_cosign  
3. cosign_grant  
4. query_cosign  
5. legal_sim  
6. expired_trust / forbidden_zone / advisor_enable / empty_u_achieve  
7. cosign_revoke  
8. legal_after_revoke  
9. evidence_tip  
10. `MISSION_SHELL_DEMO_DONE`

（对应实现见 `scenarios/client_full.c`。）
