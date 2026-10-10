# 变更记录

本文件记录仓库的版本变化。日期为 Asia/Shanghai。仓库化之前的条目根据各文档自带的日期整理，用来说明 v0.1.0 收录的内容从何而来。

## [0.1.0] — 2026-10-10

首次以独立仓库形式整理发布（尚未推送）。

### 收录
- `mission-shell/`：Microkit 使命约束外壳（门闩 + 客户端两个保护域、3 个演示剖面）与对照实验管线（B / B+ / M、4 个消融、语料生成、草稿 oracle、分析、篡改轨道、单元测试、hostsim），连同冻结语料、作者 box 上的参考日志与报告。
- `docs/`：综合报告 v1.0（Markdown + 插图）、生命周期文档包、对照实验方案、文献综述、传统 SE 纳入说明、保证边界、S0 环境笔记、答辩幻灯片。
- `thesis/`：毕业设计任务文档（Markdown）与示意性原型。

### 新增
- `scripts/`：与位置无关的 `setup_sdk`、`run_demo`、`run_experiment`、`analyze`、`check_host`、`compare_runs`、`verify_repo`、`check_links`、`check_demo_log`；`scripts/windows/` 下对应的 `.bat`。
- 入门与工程文档：`README.md`、`README.en.md`、`docs/INDEX.md`、`ARCHITECTURE.md`、`REPRODUCE.md`、`EXTENDING.md`（附示例补丁）、`STATUS-AND-LIMITATIONS.md`、`docs/verification/box-verification-2026-10-10.md`、`CONTRIBUTING.md`、`CITATION.cff`、`LICENSE`（MIT）、`LICENSE-docs`（CC BY 4.0）、`LICENSES.md`。
- `.gitattributes`、`.gitignore`、`.github/workflows/host-checks.yml`、`.github/workflows/docker-demo.yml`（手动触发、实验性）。

### 修改（行为不变）
- `mission-shell/docker_build_run.sh`：三处写死的路径改为可由 `MISSION_SHELL_DIR`、`MISSION_MICROKIT_SDK`、`MISSION_BUILD_DIR` 覆盖，默认值不变；在相同路径下构建出的 `loader.img` 与 ELF 与改动前逐字节相同。
- `mission-shell/experiment/windows/run_all_docker.bat`：仓库路径改为由脚本自身位置推导。
- 原型与绘图脚本中的作者沙箱绝对路径改为相对于脚本自身的路径（可用 `MISSION_EXP` 覆盖）。
- 文档去个人化：作者本机路径替换为 `<REPO_ROOT>`、`<WORKDIR>` 或仓库内相对路径，并在每份历史文档顶部加注说明；`mission-shell/README.md` 与 `experiment/README.md` 中的命令改为可直接复制执行的形式。答辩幻灯片中的路径同样替换。

### 未收录
- Microkit SDK（由脚本从官方发布页下载并校验）、构建产物、PDF/DOCX 渲染版本（嵌入作者本机路径且体积较大）。

## 仓库化之前的历史

- **2026-10-09**：综合报告定稿（v1.0，第 6 轮修订）；毕业设计任务文档与示意性原型完成；文献综述更新。
- **2026-10-08**：S1 原始演示 `DEMO_PROFILE=full` 在作者 Windows + Docker 环境验收通过（`tip=80488a97`，`len=10`）。对照实验预注册 v1 冻结；在作者 box（QEMU 10.0.13，非 Docker）上运行完整矩阵，生成参考日志与报告；hostsim 18 份日志。
- **2026-10-07**：对照实验方案、生命周期文档包、传统 SE 纳入说明、保证边界文档、题目 1 答辩幻灯片完成。
- **2026-09-23**：S0 环境笔记（seL4 半天跑通，Windows + Docker）。
