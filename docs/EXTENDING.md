# 扩展指南：新增规则、单元测试与语料类别

本文用一个完整的**示例**说明如何在实验门闩中加一条新规则，并同步更新参考判定器、单元测试、语料生成器和分析脚本。示例规则不是课题的组成部分，也**没有**合入主线代码；它的全部改动以补丁形式放在 [examples/m9-zero-level-enable.patch](examples/m9-zero-level-enable.patch)，下文给出的数字来自 2026-10-10 在 box 上把补丁应用到一份临时副本后的实际运行（hostsim，主机模拟、非 QEMU 实测）。

## 0. 先守纪律：预注册与偏离记录

`mission-shell/experiment/prereg.md` 已于 2026-10-08 冻结。任何改动规则、语料、生成器、托付表、阈值或分析口径的工作，都要**先**在 `mission-shell/experiment/deviations.md` 中追加一行（日期、修改内容、原因、对结论的影响、是否需要重跑），**后**改代码；不得静默修改 `prereg.md`，不得覆盖冻结语料并沿用旧结论。详见 [CONTRIBUTING.md](../CONTRIBUTING.md)。

## 1. 示例规则 M-9：强度为 0 的使能请求没有可交付内容

> M-9（示例）：若动作是 `ENABLE_SIM` 且强度 `level == 0`，拒绝，理由码 `zero_level_enable`。

需要改动的位置有五处，彼此必须保持一致：

| # | 文件 | 改动 |
|---|---|---|
| 1 | `experiment/gatekeeper_field.c` | 在 `GATE_VARIANT_M` 分支末尾（M-7 之后）加入检查，返回 `"zero_level_enable"` |
| 2 | `experiment/oracle/oracle.py` | `CLAUSE_ORDER` 末尾追加 `("S-L0", "zero_level_enable")`；`violated_clauses()` 中加入同一谓词。**条款顺序必须与 C 代码中的检查顺序一致**，否则理由码比对会失败 |
| 3 | `experiment/tests/run_unit_tests.py` | 在 `UNIT` 中加一条反例（强度 0：B、B+ 放行，M 拒绝）和一条正例（强度 1：三者都放行） |
| 4 | `experiment/corpus/gen_corpus.py` | `F_CATS` 增加 `"F10"`，新增生成方法 `F10()`：取一条允许使能的当前托付，先共签，再发出强度为 0 的使能请求，预期首个违反条款 `S-L0` |
| 5 | `experiment/analysis/analyze.py` | 把 `F_CATS` 的范围从 F1–F9 扩到 F1–F10 |

C 代码的核心改动：

```c
    /* M-9（示例规则）：强度为 0 的使能请求没有可交付内容，拒绝 */
    if (q->action == ACT_ENABLE_SIM && q->level == 0) {
        return "zero_level_enable";
    }
```

示例把检查放在消融宏之外，因此 4 个消融变体同样带有 M-9；如果希望某个消融连同 M-9 一起去掉，需要把它放进相应的 `#if !defined(ABLATE_…)` 块。这类选择本身就要写进偏离记录。

## 2. 应用补丁并逐步验证

```bash
git switch -c example/m9                      # 在新分支上试验
git apply docs/examples/m9-zero-level-enable.patch
python3 mission-shell/experiment/tests/run_unit_tests.py
python3 mission-shell/experiment/corpus/gen_corpus.py --check
```

box 上的实际结果：

1. 单元测试：`90/90 passed (30 cases x 3 variants)`（原为 84/84，新增 2 例 × 3 个变体）。
2. `gen_corpus.py --check`：**失败**（`MISMATCH … check: FAILED`）。这是预期的：生成器变了，冻结语料不再能由它重新生成。这一步就是在提醒你「已经偏离预注册」。
3. 确认偏离已记录后，才重新生成语料：

   ```bash
   python3 mission-shell/experiment/corpus/gen_corpus.py --all
   python3 mission-shell/experiment/corpus/gen_corpus.py --check
   ```

   每个种子变为 340 个用例（原 320），`--check` 恢复为 `OK`。值得注意的是生成器日志中出现了 `redraws={'L2': …}`（各种子 3–7 次）：原本会随机抽到「强度 0 的合法使能」的 L2 用例，在新规则下不再合法，被丢弃重抽。也就是说，**加一条规则会改变既有合法对照类的构成**，这正是需要重新冻结、重新跑全部条件的原因。
4. 用 hostsim 快速看效果（秒级）：

   ```bash
   RUNS_DIR=$PWD/mission-shell/experiment/runs/hostsim-m9 bash mission-shell/experiment/hostsim/run_hostsim.sh
   ```

   在种子 20261007 上，F10 一列为：B 20/20 漏检，B+ 20/20 漏检，M 0/20；各条件的 L 类误拒仍为 0。M-cosign、M-prov、M-U 的 F10 也是 0/20，与「M-9 不受消融宏控制」一致。
5. 最后再用 QEMU 跑矩阵（`bash scripts/run_experiment.sh quick`，然后 `full`），并用 `bash scripts/analyze.sh` 生成报告。示例只在 hostsim 上验证过，QEMU 一步留给你。

> **已知局限**：`analysis/stats_exact.py` 的 Clopper–Pearson 区间直接用 `math.comb` 计算二项分布，单个条件的用例数超过约 1030 时会抛出 `OverflowError`。原矩阵中 B、M 汇总 5 个种子正好是 1000 个 MUST_DENY 用例，不受影响；示例把每个种子的 MUST_DENY 用例增加到 220，5 个种子汇总为 1100，`analyze.py` 在全量 hostsim 结果上会因此失败（上面的数字是只对种子 20261007 运行分析得到的）。若要扩大语料，请先把该函数改为对数空间或正则化不完全 Beta 函数实现，并记入偏离记录。

## 3. 新增一个演示剧本

1. 复制 `mission-shell/scenarios/client_full.c` 为 `client_<名称>.c`，修改请求序列；
2. 在 `mission-shell/Makefile` 的剖面列表中加入 `else ifeq ($(DEMO_PROFILE),<名称>)` 分支；
3. `bash scripts/run_demo.sh <名称>`（自动核对只对 `full` 生效；新剧本请自行写出期望的证据事件与链值，并在文档中注明其来源）。

注意：`full` 剖面是回归门禁（`tip=80488a97|len=10`），修改 `gatekeeper.c` 的任何判决或证据链逻辑都会改变它；这类修改须同时更新 `scripts/check_demo_log.py` 的期望值并在偏离记录与 CHANGELOG 中说明。

## 4. 新增一个实验条件或消融

- 在 `gatekeeper_field.c` 顶部的宏检查中登记新宏，在 `Makefile` 的 `ABLATE` 分支中加入映射；
- 在 `experiment/run_matrix.sh` 中加入运行项，在 `analysis/analyze.py` 中加入条件名；
- 按「先登记偏离、再改代码、重新冻结、全量重跑」的顺序进行。

## 5. 提交前检查清单

```bash
bash scripts/check_host.sh          # 语料 --check、单元测试、hostsim 比对（改了语料/规则时会按预期失败，需同步更新参考）
bash scripts/run_experiment.sh quick && bash scripts/analyze.sh
bash scripts/verify_repo.sh         # 仓库卫生：个人路径、换行符、文件名、体积、链接
```

若你的改动有意改变了参考结果（`runs/box-qemu/`、`runs/hostsim/`、`reports/*`），请在同一个提交中更新它们，并在提交说明里写明运行环境与偏离记录编号。
