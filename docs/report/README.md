# 综合报告

- [mission-se-integrated-report.md](mission-se-integrated-report.md)：《使命软件工程：一种可证伪的工程方法及其在 seL4 Microkit 使命约束外壳上的实验管线验证——项目与实验综合报告（v1.0）》。Markdown 为权威版本；PDF/DOCX 渲染版因嵌入作者本机路径且体积较大而未收录。
- `figs/*.png`：报告插图（权威版本）。`figs/draw_*.py` 与 `make_figs.py` 是生成脚本，保留以便追溯；其中 `make_figs.py` 是较早的一版，会写出部分已被替换的图（如 `fig4-1_arch.png`、`fig6-1_pipeline.png`）并覆盖同名 PNG，重新运行前请先备份。生成脚本需要 `matplotlib` 与 `numpy`。
