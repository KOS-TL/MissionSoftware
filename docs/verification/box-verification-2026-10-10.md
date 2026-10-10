# 仓库化验证记录（box，2026-10-10）

本记录说明 v0.1.0 仓库在作者沙箱（box）上实际验证了什么、结果如何，以及哪些部分**只能由用户在自己的 Docker 环境中验证**。所有数字均来自本次实际运行；时间为 Asia/Shanghai（CST）。结果性质：**环境自测，非确证性**。

## 1. 验证环境

| 项 | 值 |
|---|---|
| 主机 | Linux 6.12.94+ x86_64（Debian），**无 Docker** |
| 交叉编译器 | aarch64-linux-gnu-gcc (Debian 14.2.0-19) 14.2.0 |
| QEMU | QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1) |
| 其他 | GNU Make 4.4.1，Python 3.13.5，git 2.47.3 |
| 运行模式 | `MODE=native`（脚本自动选择：无 Docker 时使用本机工具链） |
| Microkit SDK | 2.3.1 linux-x86-64，由 `scripts/setup_sdk.sh` 从官方发布页下载 |

## 2. 已在 box 上验证

### 2.1 SDK 下载脚本

- `curl -I -L` 官方链接 `https://github.com/seL4/microkit/releases/download/2.3.1/microkit-sdk-2.3.1-linux-x86-64.tar.gz`：`302 → 200`，`content-length: 72548289`（2026-10-10 10:39 CST 复查）。
- `bash scripts/setup_sdk.sh`：下载 72,548,289 字节，SHA-256 = `b1b285b8785db7557eba6d0665dd4fbf2f265ea5c0b39d6f91ae3dcc43d2c424`，校验通过并解压；再次运行时检测到已有 SDK 并跳过。
- 解压所得目录与作者此前使用的 SDK 目录 `diff -rq` 无差异。

### 2.2 演示 `DEMO_PROFILE=full`（要求 a）

`bash scripts/run_demo.sh full` → `scripts/check_demo_log.py`：`RESULT: PASS`。10 个证据事件依次为 `gate_init`(24fd4b26) → `no_human_cosign`(dff76c7e) → `cosign_grant`(9efeac20) → `legal_path_sim`(811e41c4) → `expired_entrustment`(0720fccb) → `forbidden_zone`(85fe7af5) → `advisor_cannot_enable`(36bc5c58) → `empty_U_no_achieve_tag`(402b2ffd) → `cosign_revoke`(6c909283) → `no_human_cosign`(80488a97)，链首尾相接；`GATE|CHAIN|tip=80488a97|len=10`；`CLIENT|INFO|MISSION_SHELL_DEMO_DONE`；`=== QEMU done rc=124 ===`。

核对脚本的反例自检：把 `tip=80488a97` 改成 `tip=deadbeef` 后核对失败（退出码 1）；对 `cosign_only` 日志运行同样报告 `RESULT: FAIL`。

另外两个剖面：`cosign_only` → `GATE|CHAIN|tip=4d591f49|len=6`；`false_only` → `GATE|CHAIN|tip=dff6c037|len=6`。

### 2.3 构建产物逐字节一致（要求 b）

把原始源码树（改动前）与本仓库分别放在同一路径 `/work` 下（box 上临时建立的符号链接，验证后删除），各自用**未修改的原脚本**与**仓库中修改后的** `docker_build_run.sh` 构建三个剖面，比较 `loader.img`、`gatekeeper.elf`、`client.elf`（含调试信息，未剥离）：

| 剖面 | loader.img | gatekeeper.elf | client.elf |
|---|---|---|---|
| full | 一致 `c22776e11008adf51df3c9805d310ce8025d67795ce9cc0207ad79ee58184dc3` | 一致 `fd47dc5e301b7f66…` | 一致 `80d1a8e7610f92ef…` |
| cosign_only | 一致 `852a0f43794dd13563bfff262aee9817926de8269714dcf05e34657447aeb552` | 一致 `fd47dc5e301b7f66…` | 一致 `7843f198914d9218…` |
| false_only | 一致 `dbaa0b85c2d7d45d9c80afea9cfe176ac571224f6f814c63dcb61649cec05fdd` | 一致 `fd47dc5e301b7f66…` | 一致 `681d429071faa803…` |

此外：仓库路径下（非 `/work`）以本机模式构建出的三个 `loader.img` 与上表相同；`full` 的 `loader.img` 哈希与参考日志 `runs/box-qemu/legacy_full/r1.log` 中记录的 `image_sha256=c22776e1…dc3` 相同。ELF 含 `-g` 调试信息，只有在相同构建路径下才逐字节一致；剥离调试信息后（`objcopy --strip-debug`）的比较在不同路径下同样一致。

### 2.4 主机检查（要求 c）

`bash scripts/check_host.sh`：

- `gen_corpus.py --check`：5 个种子各 320 个用例，`check: OK`；
- 单元测试：`84/84 passed (28 cases x 3 variants)`；
- hostsim：`18/18` 份日志与 `runs/hostsim/` 参考逐字节一致；
- `CHECK_HOST: PASS`，耗时约 4 秒。

### 2.5 完整实验矩阵（要求 d：完成了全量 43 份，而不只是 B、M 各一）

`bash scripts/run_experiment.sh full`（本机模式，耗时 1 分 45 秒）→ `bash scripts/analyze.sh local` → `bash scripts/compare_runs.sh local`：

- 日志集合与 `runs/box-qemu/` 完全相同（43 份：B、M × 5 种子 × 3 次，B+ 与 4 个消融 × 种子 20261007，草稿留出语料 B×3、M×3、B+×1，`legacy_full`）；
- 归一化后（只归一化 QEMU 被终止时打印的进程号与 `RUN|END|elapsed_s`）**43/43 逐字节一致**，`CASE|` 行 43/43 一致；未归一化时 43 份都只在这两个字段上不同；
- 例：`M/20261007/r1.log` 的 `image_sha256=eb001f320a827f0a1054432a2ef89b3272d12276b8a918f94bc47369f9453dc6` 与参考相同；
- 生成的 `reports/local/` 与 `reports/box-qemu/` 相比，只有 `report.md` 与 `falsification_checklist.md` 第 3 行的运行环境说明不同，其余文件（CSV、混淆矩阵、`oracle_vs_M.md` 等）完全一致。因此 README 中的数字表（B 800/1000，M 0/1000，B+ 128/200，M-cosign 20/200，M-align 93/200，M-prov 20/200，M-U 20/200，误拒全为 0，12/12 确定性组）在本次运行中得到原样复现。

旁证：hostsim 的 18 份日志与 QEMU 参考中对应的 18 份日志相比，`CASE|` 行完全一致（`compare_runs.sh hostsim` 报告 `CASE|-identical 18/43; missing 25`；hostsim 日志的其他行格式不同，因此该命令按设计报告 FAIL）。

### 2.6 干净克隆复跑

从本地 git 仓库克隆到临时目录（不含任何被忽略的文件），依次运行：`gen_corpus.py --check`（OK）、`run_unit_tests.py`（84/84）、`check_host.sh`（PASS）、`setup_sdk.sh`（重新下载并校验）、`run_demo.sh full`（PASS）、`run_experiment.sh full` + `analyze.sh` + `compare_runs.sh`（43/43，`COMPARE: PASS`）、`run_experiment.sh quick`（7 份日志，`COMPARE: PASS (partial: 7 of 43 …)`）。运行后 `git status` 干净，即所有生成物都被 `.gitignore` 覆盖。克隆中的日志 `RUN|` 行记录了 `git=<提交号>`（参考日志为 `nogit`），比对脚本对该字段做了归一化。

GitHub Actions 工作流 `host-checks.yml` 中的命令（`gen_corpus.py --check`、`run_unit_tests.py`、`check_host.sh`、`verify_repo.sh`）即在该干净克隆中验证；工作流文件本身未在 GitHub 上运行。

### 2.7 示意性原型与扩展示例

- `thesis/prototype/`：在仓库副本中运行 `er_schema.py`（`validate: 0 error(s)`，11 条记录与实验托付表一致）、`spv_gen.py --seed 1 --determinism`（`json_identical=True header_identical=True`）、`run_proto_hostsim.sh`（rc=0）；`out/` 与仓库版本 `diff -r` 无差异；实验树未被写入。
- `docs/EXTENDING.md` 的示例补丁在临时副本上应用：单元测试 90/90；`--check` 按预期失败；重新冻结后每种子 340 个用例；hostsim 上种子 20261007 的 F10：B 20/20、B+ 20/20 漏检，M 0/20。同时发现 `stats_exact.py` 在单条件用例数超过约 1030 时溢出（已记入现状文档）。

### 2.8 仓库卫生

`bash scripts/verify_repo.sh`：必需文件齐全；无构建产物、缓存、SDK 二进制或压缩包；文件名全部为 ASCII；无作者用户名、Windows 用户目录、主机名或作者本机路径（检查模式见脚本本身）；无邮箱（`noreply@example.invalid` 除外）；无疑似密钥；代码与脚本中无 `/workspace/` 绝对路径；`.sh/.py/.c/.h/Makefile/.md` 为 LF，`.bat` 为 CRLF；Markdown 相对链接全部有效；结果为 `VERIFY_REPO: PASS`（检查 361 个文件（含 MANIFEST.sha256），合计约 14.2 MiB，Markdown 相对链接 108 条）。

## 3. 未在 box 上验证、需要用户在 Docker 环境中运行

| 项 | 原因 | 建议的验证命令 |
|---|---|---|
| Docker 模式的 `run_demo.sh` / `run_experiment.sh` / `analyze.sh` | box 无 Docker | Linux：`bash scripts/run_demo.sh full`、`bash scripts/run_experiment.sh full`、`bash scripts/compare_runs.sh docker` |
| 全部 `scripts/windows/*.bat`（含 `setup_sdk.bat` 的 `certutil` 解析、`%~dp0` 路径推导、`"%cd%"` 挂载） | 无 Windows 环境 | `scripts\windows\setup_sdk.bat`，然后 `run_demo.bat full`、`run_experiment.bat full`、`analyze.bat docker` |
| 修改后的 `mission-shell/experiment/windows/run_all_docker.bat` | 同上 | 直接双击或在 cmd 中运行 |
| 镜像中的编译器是否生成相同 `image_sha256` | 镜像版本未知 | 对比日志 `RUN|build_ok` 行 |
| 镜像是否预设 `MICROKIT_SDK` 环境变量 | 无法在 box 上检查镜像 | `docker run --rm trustworthysystems/sel4:latest env` |
| GitHub Actions 两个工作流 | 未推送 | 推送后在 Actions 页面查看；`docker-demo` 需手动触发 |
| macOS（Apple silicon / Intel） | 无设备 | 见 `docs/REPRODUCE.md` §3 |
| Windows 上 SDK 解压后的可执行位 | 无 Windows 环境 | 若报 `Permission denied`，见 README「常见问题」 |

作者 2026-10-08 在 Windows + Docker 上验收的是**原目录布局**下的同一条 docker 命令；本仓库只改变了挂载的目录（仓库根目录代替 `microkit_work`），容器内看到的 `/work` 布局相同。
