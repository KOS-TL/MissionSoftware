# 文档索引

## 入门

| 文档 | 内容 |
|---|---|
| [../README.md](../README.md) | 项目介绍、证据状态、硬边界、快速开始（中文，权威） |
| [../README.en.md](../README.en.md) | 英文摘要 |
| [REPRODUCE.md](REPRODUCE.md) | 分平台完整复现步骤与结果比对 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 两个保护域、报文、判决次序、证据链、实验管线、脚本层、目录布局取舍 |
| [EXTENDING.md](EXTENDING.md) | 新增规则 / 单元测试 / 语料类别的完整示例（附补丁 [examples/m9-zero-level-enable.patch](examples/m9-zero-level-enable.patch)） |
| [STATUS-AND-LIMITATIONS.md](STATUS-AND-LIMITATIONS.md) | 已完成、待办、硬边界、已知局限 |
| [verification/box-verification-2026-10-10.md](verification/box-verification-2026-10-10.md) | 仓库化后在 box 上的验证记录（已验证 vs 需用户 Docker 运行） |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | 贡献流程与预注册纪律 |
| [../CHANGELOG.md](../CHANGELOG.md) | 版本历史 |

## 课题文档（历史文档，按原文收录并去个人化）

| 文档 | 内容 |
|---|---|
| [report/mission-se-integrated-report.md](report/mission-se-integrated-report.md) | 项目与实验综合报告 v1.0（插图在 `report/figs/`，生成脚本为 `report/make_figs.py` 与 `report/figs/draw_*.py`，PNG 为权威版本） |
| [experiment-design/controlled-experiment-design.md](experiment-design/controlled-experiment-design.md) | 对照实验方案 |
| [survey/mission-se-related-work.md](survey/mission-se-related-work.md) | 文献综述（117 条有效条目，带核验状态） |
| [traditional-se-embedded.md](traditional-se-embedded.md) | 传统软件工程如何嵌入使命外壳（与 `mission-shell/docs/` 中同名文档内容相同） |
| [pu-boundary.md](pu-boundary.md) | 保证边界：K（内核，仅引用）/ A（应用，演示）/ M（使命层，可观察）/ U（未覆盖项，必须非空）；`mission-shell/docs/PU_BOUNDARY.md` 是外壳树内的另一版本 |
| [s0-sel4test-guide.md](s0-sel4test-guide.md) | S0：seL4 半天跑通（Windows + Docker，sel4test） |
| [defense-topic1-microkit-mission-shell.pptx](defense-topic1-microkit-mission-shell.pptx) | 题目 1 答辩幻灯片（11 页） |

### 生命周期文档包（`lifecycle/`）

| 文档 | 内容 |
|---|---|
| [lifecycle/00-README.md](lifecycle/00-README.md) | 文档包说明 |
| [lifecycle/01-SRS.md](lifecycle/01-SRS.md) | 软件需求规格说明书 |
| [lifecycle/02-SDD.md](lifecycle/02-SDD.md) | 软件设计说明书 |
| [lifecycle/03-implementation.md](lifecycle/03-implementation.md) | 实现说明与构建指南 |
| [lifecycle/04-test-plan.md](lifecycle/04-test-plan.md) | 测试计划与验收规范 |
| [lifecycle/05-test-report-full.md](lifecycle/05-test-report-full.md) | 测试报告（`DEMO_PROFILE=full`） |
| [lifecycle/06-release-repro.md](lifecycle/06-release-repro.md) | 发布与复现手册（历史版；当前以 [REPRODUCE.md](REPRODUCE.md) 为准） |
| [lifecycle/07-traceability.md](lifecycle/07-traceability.md) | 需求追溯矩阵 |
| [lifecycle/08-config-change.md](lifecycle/08-config-change.md) | 配置与变更管理 |
| [lifecycle/09-lifecycle-overview.md](lifecycle/09-lifecycle-overview.md) | 生命周期总览 |

## 代码树中的文档

| 文档 | 内容 |
|---|---|
| [../mission-shell/README.md](../mission-shell/README.md) | 外壳演示简介 |
| [../mission-shell/experiment/README.md](../mission-shell/experiment/README.md) | 对照实验详细说明（条件、构建、运行、分析） |
| [../mission-shell/experiment/prereg.md](../mission-shell/experiment/prereg.md) | 预注册 v1（2026-10-08 冻结） |
| [../mission-shell/experiment/deviations.md](../mission-shell/experiment/deviations.md) | 偏离记录 |
| [../mission-shell/experiment/oracle/rules_spec.md](../mission-shell/experiment/oracle/rules_spec.md) | 判定规则规格 |
| [../mission-shell/experiment/reports/box-qemu/report.md](../mission-shell/experiment/reports/box-qemu/report.md) | 参考实验报告（作者 box） |
| [../mission-shell/docs/](../mission-shell/docs/PU_BOUNDARY.md) | 外壳自带文档（PU 边界、传统 SE 纳入说明、生命周期包索引） |

## 毕业设计

| 文档 | 内容 |
|---|---|
| [../thesis/README.md](../thesis/README.md) | 目录说明 |
| [../thesis/graduation-project-spec.md](../thesis/graduation-project-spec.md) | 毕业设计任务文档：托付记录驱动的假使命测试生成与对照评测 |
| [../thesis/prototype/README.md](../thesis/prototype/README.md) | 示意性原型（非实验树、不参与预注册） |
