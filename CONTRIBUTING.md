# 参与贡献

感谢你愿意改进本项目。本仓库同时是**可运行的软件**和**一项预注册实验的记录**，因此除了一般的代码规范，还有一条更重要的纪律：不得让实验结论在不知不觉中改变。

## 1. 预注册纪律（涉及 `mission-shell/experiment/` 时必须遵守）

1. **先记偏离，后改代码。** 预注册 `experiment/prereg.md` v1 已于 2026-10-08 冻结。修改阈值、假设、规则规格、门闩判决逻辑、托付表、语料生成器、冻结语料或分析口径之前，先在 `experiment/deviations.md` 追加一行：日期（Asia/Shanghai）、修改内容、原因、对结论的影响、是否需要重跑。
2. **不静默修改 `prereg.md`**，也不改写已发布报告中的结论措辞。需要新的预注册时，另起版本（如 `prereg-v2.md`），并说明与 v1 的关系。
3. **不覆盖冻结语料并沿用旧结论。** `gen_corpus.py --check` 失败就说明你已经偏离；重新冻结（`--all`）后必须全量重跑并重新生成报告。
4. **结果口径不升级。** 作者语料、草稿 oracle、hostsim、草稿留出语料上的任何结果，都只能称为「环境自测 / 装置自检，非确证性」。确证性结论只能来自预注册中规定的独立标注留出语料。
5. **报告每一个数字的来源。** 新增或修改的数字必须能追溯到仓库中的日志或报告文件，并写明运行环境（平台、镜像 digest 或工具链版本）。
6. **硬边界不可放宽**：不得添加出束、真实设备或厂商写使能路径；不得把 `ALLOW_SIM` 写成「达成」；不得宣称 seL4 级应用证明；不得把演示共签或 FNV-1a32 链描述为安全机制。

## 2. 开发流程

```bash
git switch -c <你的分支>
# 修改代码……
bash scripts/check_host.sh                               # 秒级：语料、单元测试、hostsim
bash scripts/run_experiment.sh quick && bash scripts/analyze.sh
bash scripts/verify_repo.sh                              # 仓库卫生
```

- 新规则、新类别的完整步骤见 [docs/EXTENDING.md](docs/EXTENDING.md)。
- `.sh`、`.py`、`.c`、`.h`、`Makefile` 一律 LF；`.bat` 一律 CRLF 且只用 ASCII 字符（`.gitattributes` 已处理，请勿改动）。
- 文件名只用 ASCII 字符。
- 不提交构建产物、`__pycache__`、SDK、压缩包、个人路径、用户名、邮箱或任何凭据（`verify_repo.sh` 会检查）。
- 中文文档力求表述准确、平实；不夸大结论。

## 3. Pull Request

请在描述中说明：改了什么、为什么、是否涉及偏离（附 `deviations.md` 行）、在哪个环境下运行了哪些检查（附 `CHECK_HOST`、`COMPARE`、`VERIFY_REPO` 的结果行）。改变参考结果（`runs/box-qemu/`、`runs/hostsim/`、`reports/*`）的 PR 需同时提交新的日志和报告。

## 4. 报告复现结果

无论成功与否，欢迎在 issue 中报告复现结果，格式见 [docs/REPRODUCE.md](docs/REPRODUCE.md) §6。Windows Docker 上的语料矩阵复现尤其需要。
