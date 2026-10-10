# 毕业设计材料

| 路径 | 内容 |
|---|---|
| [graduation-project-spec.md](graduation-project-spec.md) | 毕业设计任务文档《托付记录驱动的假使命测试生成与对照评测》（Markdown 为权威版本；PDF/DOCX 渲染版未收录，原因见 [../docs/STATUS-AND-LIMITATIONS.md](../docs/STATUS-AND-LIMITATIONS.md)） |
| [figs/](figs/draw_figs.py) | 文档插图（PNG）及其生成脚本 `draw_figs.py` |
| [prototype/](prototype/README.md) | **示意性原型**（illustrative prototype） |

## 关于示意性原型

`prototype/` 是指导方案拟定人为评估毕业设计可行性而写的最小原型：**不属于实验树，不参与预注册实验**，其输出只是「主机模拟、非 QEMU 实测；作者自建语料、非独立、非确证性」的可行性自测。是否把它提供给学生由指导教师决定；若提供，学生须在论文中声明，并以它为基线说明自己新增的工作。

原型只读引用 `../mission-shell/experiment/`（默认按自身位置定位，可用环境变量 `MISSION_EXP` 覆盖），不向实验树写任何文件。复跑：

```bash
cd thesis/prototype
python3 er_schema.py
python3 spv_gen.py --seed 1 --determinism
bash run_proto_hostsim.sh
```

2026-10-10 在 box 上于仓库副本中复跑，`out/` 下的全部产物与仓库内版本逐字节一致（见 [验证记录](../docs/verification/box-verification-2026-10-10.md)）。
