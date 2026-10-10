# Microkit 使命约束外壳 —— 软件工程生命周期文档包

> **仓库化说明（v0.1.0）**：本文为项目过程中的历史文档，按原文收录，仅做去个人化处理：作者本机路径已替换为 `<REPO_ROOT>`（= 本仓库克隆目录，内含 `mission-shell/` 与 `microkit-sdk-2.3.1/`）、`<WORKDIR>`（作者文档目录）或仓库内相对路径；形如 `/workspace/...` 的路径是作者沙箱（box）上的历史路径，在本仓库中分别对应 `mission-shell/`（原 `/workspace/microkit-mission-shell/`）与 `docs/`。文中命令含占位符，**不能直接复制执行**；可直接执行的命令见仓库根目录 `README.md` 与 `docs/REPRODUCE.md`。


| 项 | 内容 |
|---|---|
| 版本 | 1.0.0 |
| 日期 | 2026-09-23（Asia/Shanghai） |
| 工程代号 | mission-shell（毕设题目1 / S1） |
| 源码树 | `<REPO_ROOT>\mission-shell`（本机） / `/workspace/microkit-mission-shell`（沙箱镜像） |
| 文档包路径 | 本目录；同步目标 `docs/lifecycle/` |

---

## 1. 包的目的

本包把题目1示例从「可跑的实现尖刺」补全为**传统软件工程全流程**产物集：需求（SRS）→ 设计（SDD）→ 实现与构建 → 测试计划/报告 → 发布与复现 → 追溯与变更 → 总览。  
使命纪律不另起平行生命周期，而是在每一阶段叠加可机检约束：

> **明示托付 ∧ 当前动作仍对准该托付 ∧ 判定可被证伪**

## 2. 阅读顺序（推荐）

1. `09-生命周期总览.md` — 先建立 REQ→RELEASE 一条故事线  
2. `00-README.md`（本文）— 范围与非目标  
3. `01-SRS-软件需求规格说明书.md` — R1–R5 与验收口径  
4. `02-SDD-软件设计说明书.md` — D1–D5 与架构  
5. `07-需求追溯矩阵.md` — Req ↔ 设计 ↔ 源码 ↔ 测试  
6. `03-实现说明与构建指南.md`  
7. `04-测试计划与验收规范.md` → `05-测试报告-DEMO_PROFILE-full.md`  
8. `06-发布与复现手册.md`、`08-配置与变更管理.md`

ASCII 同源副本（便于工具链）：`01-SRS.md` … `09-lifecycle-overview.md`（与中文主文件内容一致）。

## 3. 与开题报告、纳入文档的关系

| 既有文档 | 本包关系 |
|---|---|
| `开题报告-题目1-基于Microkit的使命约束外壳.md` | 立项与 S0→S1 分期；本包是其「工程化落地」的正式生命周期附件 |
| `traditional-SE-embedded-in-mission-shell.md` | 立场与总表来源；本包将其中 R*/D* 展开为可归档的 SRS/SDD/测试/追溯正式件 |
| `docs/PU_BOUNDARY.md` / `microkit-PU-BOUNDARY.md` | K/A/M/U 保证边界；本包各文件均引用且不越界 |

## 4. 范围（Goals）

- 在 Microkit `qemu_virt_aarch64` 上两保护域（`gatekeeper` + `client`）的**演示级**使命约束外壳  
- `DEMO_PROFILE=full|cosign_only|false_only` 场景可切换  
- Docker 可复现构建与串口关键词验收  

## 5. 非目标（Non-goals）——全文硬约束

- **非临床**：无出束、无厂商写使能、无注册材料  
- **不宣称 seL4 级应用证明**：K 层仅引用；应用 A 为演示、未形式化验证  
- **delivery ≠ achievement**：`ALLOW_SIM` ≠ 使命达成  
- **共签为演示占位**：非电子签名/法规共签系统  
- **FNV-1a32 证据链为教学级**：非密码学抗碰撞保证  

## 6. 验收一句口径

唯一推荐验收：`DEMO_PROFILE=full` 串口出现完整共签 OFF→DENY→GRANT→ALLOW_SIM→四假使命 DENY→REVOKE→DENY→`GATE|CHAIN|…|len=10`→`MISSION_SHELL_DEMO_DONE`。  
无 `DEMO_PROFILE` 的旧日志**不得**作为现行验收依据。

## 7. 文件清单

| 文件 | 说明 |
|---|---|
| `00-README.md` | 索引（本文） |
| `01-SRS-软件需求规格说明书.md` / `01-SRS.md` | 软件需求规格 |
| `02-SDD-软件设计说明书.md` / `02-SDD.md` | 软件设计说明 |
| `03-实现说明与构建指南.md` / `03-implementation.md` | 实现与构建 |
| `04-测试计划与验收规范.md` / `04-test-plan.md` | 测试计划 |
| `05-测试报告-DEMO_PROFILE-full.md` / `05-test-report-full.md` | full 剖面测试报告 |
| `06-发布与复现手册.md` / `06-release-repro.md` | 发布与复现 |
| `07-需求追溯矩阵.md` / `07-traceability.md` | 追溯矩阵 |
| `08-配置与变更管理.md` / `08-config-change.md` | 配置与变更 |
| `09-生命周期总览.md` / `09-lifecycle-overview.md` | 总览叙事 |

## 8. 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| 1.0.0 | 2026-09-23 | 初版：对照源码 `gatekeeper.c` / `mission_proto.h` / `scenarios/*` / `docker_build_run.sh` 定稿 |

---

*文档包仅描述与归档；不修改生产门闩行为。*
