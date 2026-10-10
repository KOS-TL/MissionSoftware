# 需求追溯矩阵

> **仓库化说明（v0.1.0）**：本文为项目过程中的历史文档，按原文收录，仅做去个人化处理：作者本机路径已替换为 `<REPO_ROOT>`（= 本仓库克隆目录，内含 `mission-shell/` 与 `microkit-sdk-2.3.1/`）、`<WORKDIR>`（作者文档目录）或仓库内相对路径；形如 `/workspace/...` 的路径是作者沙箱（box）上的历史路径，在本仓库中分别对应 `mission-shell/`（原 `/workspace/microkit-mission-shell/`）与 `docs/`。文中命令含占位符，**不能直接复制执行**；可直接执行的命令见仓库根目录 `README.md` 与 `docs/REPRODUCE.md`。


**版本**：1.0.0  
**日期**：2026-09-23  
**源码基线**：`/workspace/microkit-mission-shell`（对齐用户机 `…\mission-shell`）

说明：一需求可对应多设计/多测试；串口关键词为验收锚定。

---

## 1. 主矩阵

| Req | 设计 | 源文件 / 符号 | 测试用例 | 串口关键词（关键） |
|---|---|---|---|---|
| R1.1 共签默认 OFF | D2 | `gatekeeper.c`:`human_cosign_ok=0`；`init` | TC-FULL-02 | `STATE=OFF` |
| R1.2 无共签则拒 | D2,D3 | `protected` 中 `if (!human_cosign_ok) deny("no_human_cosign")` | TC-FULL-02,05 | `GATE|DENY|no_human_cosign` |
| R1.3 GRANT | D2 | `REQ_HUMAN_COSIGN_GRANT` 分支 | TC-FULL-03 | `GATE|COSIGN|GRANT (demo stand-in)` |
| R1.4 REVOKE | D2 | `REQ_HUMAN_COSIGN_REVOKE` | TC-FULL-05 | `GATE|COSIGN|REVOKE` |
| R1.5 QUERY | D2 | `REQ_HUMAN_COSIGN_QUERY` → `REP_COSIGN_ON/OFF` | TC-FULL-02,03 | `STATE=ON` / `OFF` |
| R1.6 禁静默共签 | D2,D6 | 无启动置位；仅显式消息 | TC-FULL-02 | 启动后首查必 OFF |
| R1.7 演示占位声明 | D2 | 日志文案 `demo stand-in`；文档 | 文档评审 | `demo stand-in` |
| R2.1 过期托付 | D3 | `REQ_EXPIRED_TRUST` → `deny("expired_entrustment")` | TC-FULL-04, TC-FALSE-01 | `DENY|expired_entrustment` |
| R2.2 禁区 | D3 | `REQ_FORBIDDEN_ZONE` → `forbidden_zone` | 同上 | `DENY|forbidden_zone` |
| R2.3 顾问使能 | D3 | `REQ_ADVISOR_ENABLE` → `advisor_cannot_enable` | 同上 | `DENY|advisor_cannot_enable` |
| R2.4 空U达成 | D3 | `REQ_EMPTY_U_ACHIEVE` → `empty_U_no_achieve_tag` | 同上 | `DENY|empty_U_no_achieve_tag` |
| R3.1 ALLOW_SIM | D3 | `REQ_LEGAL_ENABLE` → `allow_sim("legal_path_sim")` | TC-FULL-03 | `GATE|ALLOW_SIM|legal_path_sim` |
| R3.2 NOTE 强制 | D3 | `allow_sim` 内 `GATE|NOTE|sim_only;…` | TC-FULL-03 | `sim_only; delivery!=achievement; non-clinical` |
| R3.3 禁止称达成 | D3,D1 | 无 ACHIEVE 码；文档口径 | 文档评审+测试报告声明 | — |
| R3.4 无 ACHIEVE | D3 | `mission_proto.h` 无达成 REP | 代码检查 | — |
| R4.1–4.3 证据链 | D4 | `fnv1a_step` / `evidence_append` / `REQ_EVIDENCE_TIP` | TC-FULL-06 | `EVIDENCE|seq=`；`GATE|CHAIN|` |
| R4.4 full len=10 | D4 | 事件表见测试报告 §6 | TC-FULL-06 | `len=10` |
| R4.5 非密码学声明 | D4,D1 | 文件头注释；PU_BOUNDARY | 文档评审 | `chain=FNV-1a32 demo` |
| R5.1 无写使能 | D1,D7 | 工程无出束/写接口 | 代码扫描 | 无相关符号 |
| R5.2 不宣称应用证明 | D1 | K=cited 日志与文档 | 文档评审 | `K=cited` |
| R5.3 非临床业务 | D1 | 范围排除 | 文档评审 | `non-clinical` |
| R5.4 未知请求拒绝 | D3 | `default: deny("unknown_request")` | 可选负测 | `unknown_request` |
| R6.1–6.3 Profile | D5 | `Makefile` `DEMO_PROFILE`；`scenarios/*` | TC-COSIGN-01, TC-FALSE-01, TC-FULL-* | `CLIENT|INFO|profile=`；`MISSION_SHELL_DEMO_DONE` |
| R7.1–7.3 两 PD+PPC | D6 | `mission.system`；`microkit_ppcall` / `protected` | TC-FULL-01 | 系统可跑；PPC 往返 |
| NFR1 可复现 | — | `docker_build_run.sh` | 回归 S1-R | 同命令复现 |
| NFR2 可观察 | D7 | 全路径 `dbg_puts` | 全部 TC | 稳定关键词 |
| NFR4 timeout | — | `timeout 30s`；脚本 `exit 0` | TC-FULL-07 | `rc=124` 可接受 |

---

## 2. 协议常量速查

| 常量 | 值 | 关联 Req |
|---|---|---|
| REQ_LEGAL_ENABLE | 1 | R3 |
| REQ_EXPIRED_TRUST | 2 | R2.1 |
| REQ_FORBIDDEN_ZONE | 3 | R2.2 |
| REQ_ADVISOR_ENABLE | 4 | R2.3 |
| REQ_EMPTY_U_ACHIEVE | 5 | R2.4 |
| REQ_HUMAN_COSIGN_GRANT | 20 | R1.3 |
| REQ_HUMAN_COSIGN_REVOKE | 21 | R1.4 |
| REQ_HUMAN_COSIGN_QUERY | 22 | R1.5 |
| REQ_EVIDENCE_TIP | 23 | R4 |
| REP_ALLOW_SIM | 10 | R3 |
| REP_DENY | 11 | R1/R2 |
| REP_OK | 12 | R1 GRANT/REVOKE |
| REP_COSIGN_ON / OFF | 13 / 14 | R1.5 |
| REP_EVIDENCE_TIP | 15 | R4 |

---

## 3. 维护规则

变更 REQ 常量、DENY 字符串、NOTE 文案、证据混入或默认共签时：同提交更新本表与测试报告，并升变更单（见 08）。
