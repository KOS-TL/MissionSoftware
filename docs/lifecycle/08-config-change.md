# 配置与变更管理

> **仓库化说明（v0.1.0）**：本文为项目过程中的历史文档，按原文收录，仅做去个人化处理：作者本机路径已替换为 `<REPO_ROOT>`（= 本仓库克隆目录，内含 `mission-shell/` 与 `microkit-sdk-2.3.1/`）、`<WORKDIR>`（作者文档目录）或仓库内相对路径；形如 `/workspace/...` 的路径是作者沙箱（box）上的历史路径，在本仓库中分别对应 `mission-shell/`（原 `/workspace/microkit-mission-shell/`）与 `docs/`。文中命令含占位符，**不能直接复制执行**；可直接执行的命令见仓库根目录 `README.md` 与 `docs/REPRODUCE.md`。


**版本**：1.0.0  
**日期**：2026-09-23

---

## 1. 配置项识别

| CI 标识 | 内容 | 基线敏感度 |
|---|---|---|
| CI-SRC | `gatekeeper.c` 等源与 `mission_proto.h` | **高**（门闩行为） |
| CI-SYS | `mission.system` | 高 |
| CI-SCEN | `scenarios/client_*.c` | 高（验收序列） |
| CI-BUILD | `Makefile` / `docker_build_run.sh` | 中高 |
| CI-PROF | `DEMO_PROFILE` 取值集合 | 高 |
| CI-DOC | 本生命周期包、开题、PU_BOUNDARY | 中（口径） |
| CI-SDK | Microkit SDK 2.3.1 | 高（工具链） |

---

## 2. 何谓基线（Baseline）

**应用验收基线（S1-full）** 同时满足：

1. 源码可构建出 `loader.img`  
2. `-e DEMO_PROFILE=full` 串口满足测试计划关键词合取  
3. 文档包版本与追溯矩阵指向该源码符号  
4. PU 边界声明未被削弱  

仅有「曾经跑通但无 DEMO_PROFILE 声明」的日志 **不构成** 现行基线证据。

---

## 3. DEMO_PROFILE 版本化

| 取值 | 状态 | 说明 |
|---|---|---|
| `full` | **受控主验收** | 默认；变更场景步必须重跑 TC-FULL-* |
| `cosign_only` | 受控对照 | 变更共签相关时重跑 |
| `false_only` | 受控对照 | 变更假使命集时重跑 |
| 其它 | 禁止 | Makefile 应报错 |

新增 profile：变更请求 → 更新 Makefile、SRS R6、测试计划、追溯矩阵 → 评审 → 合入。

---

## 4. 门闩行为变更控制

下列变更视为**重大**（必须变更请求 + 全量 full 验收 + 更新 05 报告）：

- 默认 `human_cosign_ok` 初值  
- DENY/ALLOW 分支条件或原因字符串  
- `allow_sim` 是否打印 NOTE  
- 证据算法或混入字段  
- 删除/放宽任一假使命  
- 引入 ACHIEVE 或写使能类接口（默认**拒绝合入**，与 R5 冲突）

下列为**轻微**：

- 注释、文档、答辩稿  
- 超时秒数在合理范围调整（需注明）  
- 日志增加非契约调试行（不得破坏既有关键词）

---

## 5. 变更流程（本科尺度最小集）

1. 陈述动机与影响需求 ID  
2. 改代码/文档  
3. 跑 Docker full（及受影响 profile）  
4. 更新追溯矩阵与测试报告版本  
5. 在开题/论文中若不改结论可只附录；若改口径须指导教师知悉  

---

## 6. 配置审计问题清单

- 当前验收是否使用 `DEMO_PROFILE=full`？  
- tip/len 是否仍为 10？事件表是否仍匹配？  
- 是否有人把 ALLOW_SIM 写成达成？  
- SDK 小版本是否漂移？  

---

## 7. 命名与发布标签建议

- 文档包：`mission-shell-lifecycle-1.0.0`  
- 源码 tag 示例：`s1-full-baseline-2026-09-23`  
- 产物包：`mission-shell-lifecycle.tgz`
