# 示意性原型（illustrative prototype）

**性质声明：** 本目录是指导方案拟定人为评估毕业设计可行性而写的最小原型，**不是**实验树的一部分，**不参与**预注册实验，
其输出数字只是「主机模拟、非 QEMU 实测；作者自建语料、非独立、非确证性」的可行性自测。是否把本原型提供给学生，由指导教师决定；
若提供，学生须在论文中声明，并以本原型为基线说明自己新增的工作。

本原型**只读**引用 `<仓库根>/mission-shell/experiment/`（默认按本目录相对路径定位，可用 `MISSION_EXP` 覆盖）（导入 `corpus_c`、`oracle`、`stats_exact`；编译 `gatekeeper_field.c`、
`client_corpus.c`、`hostsim/hostsim.c`），不向实验树写任何文件（已设置 `PYTHONDONTWRITEBYTECODE`，变异只作用于临时副本）。

| 文件 | 作用 |
|---|---|
| `entrustment_records_v0.example.json` | 托付记录 schema 草案 v0 的示例；被执行字段逐字取自 `experiment/corpus/entrustments.json`，新增字段为示例占位 |
| `er_schema.py` | 草案结构校验 + 降维映射到 `mission-se-entrustments/v1` 记录；核对与实验托付表 11 条记录逐字段相同 |
| `spv_gen.py` | 单点违反生成器草案：输出 `mission-se-corpus/v1` JSON 与 `corpus_c.corpus_header` 头文件；`--determinism` 做同种子逐字节比较 |
| `run_proto_hostsim.sh` | 以 hostsim 方式运行 B / Bplus / M / 4 个消融 / 9 个变异体，并用 `parse_serial.py parse/score` 计分 |
| `summarize.py` | 汇总 FNR、FPR（Wilson 95%）、B vs M 精确 McNemar、按要素漏检、变异体杀死情况 |
| `out/` | 运行产物（`spv_1.json/.h`、`runs/`、`scored/`、`summary.txt`） |

复跑：`python3 er_schema.py && python3 spv_gen.py --seed 1 --determinism && bash run_proto_hostsim.sh`
