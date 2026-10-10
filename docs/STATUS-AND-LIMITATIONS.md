# 现状与局限

> 一句话：**本仓库的实验结果是「环境自测，非确证性」。** 它们说明实验装置按设计工作，不说明使命软件工程方法在独立语料上有效。

## 1. 已完成（附证据位置）

| 事项 | 状态 | 证据 |
|---|---|---|
| S0：sel4test 环境搭建笔记 | 完成（2026-09-23） | [s0-sel4test-guide.md](s0-sel4test-guide.md) |
| S1：使命约束外壳 `full` 演示 | 作者 Windows + Docker 验收通过（2026-10-08），`tip=80488a97 len=10` | [lifecycle/05-test-report-full.md](lifecycle/05-test-report-full.md)、综合报告 |
| 生命周期文档包（SRS/SDD/实现/测试/发布/追溯/配置） | 完成（2026-10-07） | [lifecycle/](lifecycle/00-README.md) |
| 对照实验方案与预注册 | 预注册 v1 于 2026-10-08 冻结；偏离记录目前为空 | [experiment-design/](experiment-design/controlled-experiment-design.md)、`mission-shell/experiment/prereg.md`、`deviations.md` |
| 对照实验矩阵（作者语料 A） | 在作者 box 上运行（2026-10-08，QEMU 10.0.13，非 Docker）：42 份矩阵日志，INVALID 0，12/12 确定性组一致 | `mission-shell/experiment/reports/box-qemu/report.md` |
| hostsim 主机模拟 | 18 份日志 | `mission-shell/experiment/reports/hostsim/` |
| 综合报告 v1.0、文献综述、毕业设计任务文档 | 完成（2026-10-08/09） | [report/](report/mission-se-integrated-report.md)、[survey/](survey/mission-se-related-work.md)、[thesis/](../thesis/graduation-project-spec.md) |
| 仓库化（v0.1.0） | 2026-10-10；box 上重跑演示与 43 份日志，与参考一致 | [verification/box-verification-2026-10-10.md](verification/box-verification-2026-10-10.md) |

## 2. 尚未完成（待办）

1. **对照实验语料矩阵的 Windows Docker 复现**：只有原始 `full` 演示在 Windows Docker 上验收过；语料矩阵尚未在 Windows Docker 上运行。
2. **独立标注的留出语料评测**：仓库中的 `holdout_draft` 是作者手写草稿，只用于演示流水线，**不得**用于判定预注册的确证性假设；尚无独立标注人，oracle 仍是草稿。
3. **人工审查研究**（RQ3b/E1/X-6）：已推迟，未实施。
4. **预注册 git 标签**：综合报告记载「预注册 git 标签未打」；本仓库首次提交时也未打标签，由作者决定是否以及何时补打。
5. 本仓库的 **Windows `.bat` 封装、Docker 模式脚本、GitHub Actions 工作流、macOS** 均未实际运行过（详见验证记录）。
6. **许可证**：代码 MIT，文档与数据 CC BY 4.0（[LICENSES.md](../LICENSES.md)）。

## 3. 硬边界（设计上不做的事）

- 非临床，仅仿真；不提供、也不接受任何出束或厂商设备写使能路径。
- 形式化内核保证（K）只引用、不宣称；不宣称任何应用层的 seL4 级证明。
- Microkit SDK 2.3.1 使用 MCS 内核配置，其验证仍在进行中：**构建成功 ≠ 已验证内核**。
- 共签 `GRANT/REVOKE` 是演示替身，不是身份认证或数字签名。
- FNV-1a32 证据链是教学级，无密钥、非抗碰撞；按预先声明，截尾（T5）与知情重算（T7）在 M 上检不出。
- `ALLOW_SIM` ≠ 达成；「宣称达成」本身会被拒绝。

## 4. 已知局限与风险

| 项 | 说明 |
|---|---|
| 作者语料 | 作者同时编写规则与语料，「M 全拦截」在构造上几乎必然成立，只能作为操纵检查（H1′） |
| 草稿 oracle | 真值由作者编写的参考判定器给出，未经独立复核 |
| 编译器版本 | `image_sha256` 依赖交叉编译器版本；box 参考值来自 gcc 14.2.0。镜像中的编译器版本不同会改变哈希，但不应改变判决 |
| 镜像漂移 | `trustworthysystems/sel4:latest` 会更新。Docker Hub 记录（2026-10-10 查询）：最近更新 2026-10-09 01:39 CST；清单 digest `sha256:00ee29afe8760dbc5e0dd313fa5845c2d73866e0cba565b7012eacbc5b1004f7`；amd64 `sha256:552f280a…9980e`，arm64 `sha256:95e410f0…111f6`。作者 2026-10-08 验收时使用的镜像早于该次更新，digest 未记录。实验脚本会把运行时 digest 写进日志 |
| `MICROKIT_SDK` 环境变量 | 未改动的 `docker_corpus_run.sh` 优先使用该变量；若镜像预设了它，实验会改用镜像内的 SDK |
| 统计实现 | `stats_exact.py` 的 Clopper–Pearson 在单条件用例数超过约 1030 时溢出（见 [EXTENDING.md](EXTENDING.md)）；当前矩阵最大为 1000，不受影响 |
| Apple silicon | 默认 SDK 为 linux-x86-64，与 arm64 镜像不匹配；未测试 |
| 历史文档 | `docs/` 中的历史文档按原文收录，含有作者沙箱路径 `/workspace/...` 与占位符 `<REPO_ROOT>`；其中命令不能直接执行，可执行命令以 README 与 REPRODUCE 为准 |
| PDF/DOCX | 综合报告与毕设文档的 PDF/DOCX 版本未收录（它们嵌入了作者本机路径，且体积较大）；Markdown 是权威版本 |
