# 测试报告：DEMO_PROFILE=full

> **仓库化说明（v0.1.0）**：本文为项目过程中的历史文档，按原文收录，仅做去个人化处理：作者本机路径已替换为 `<REPO_ROOT>`（= 本仓库克隆目录，内含 `mission-shell/` 与 `microkit-sdk-2.3.1/`）、`<WORKDIR>`（作者文档目录）或仓库内相对路径；形如 `/workspace/...` 的路径是作者沙箱（box）上的历史路径，在本仓库中分别对应 `mission-shell/`（原 `/workspace/microkit-mission-shell/`）与 `docs/`。文中命令含占位符，**不能直接复制执行**；可直接执行的命令见仓库根目录 `README.md` 与 `docs/REPRODUCE.md`。


**版本**：1.0.0  
**日期**：2026-09-23  
**对应计划**：`04-测试计划与验收规范.md`  
**结论**：在已知成功 full 跑通口径下，**通过**（关键词契约满足；QEMU timeout rc=124 可接受）

---

## 1. 测试标识

| 项 | 值 |
|---|---|
| 剖面 | `DEMO_PROFILE=full` |
| 客户端源 | `scenarios/client_full.c` |
| 门闩源 | `gatekeeper.c` |
| Board / SDK | `qemu_virt_aarch64` / Microkit 2.3.1 |
| 镜像 | `trustworthysystems/sel4:latest` |

## 2. 执行命令

```bat
docker run --rm -e DEMO_PROFILE=full -v <REPO_ROOT>:/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_build_run.sh
```

## 3. 环境声明

- 必须出现脚本输出行：`DEMO_PROFILE=full`  
- **无效对照**：任何未设置 `DEMO_PROFILE`（或未打印该行）的旧日志，**不得**作为本报告的验收附件。

## 4. 用例结果摘要

| 用例 | 结果 | 备注 |
|---|---|---|
| TC-FULL-01 构建启动 | PASS | loader 生成；GATE init |
| TC-FULL-02 共签 OFF + 先拒 | PASS | STATE=OFF；DENY no_human_cosign |
| TC-FULL-03 GRANT + ALLOW_SIM | PASS | NOTE sim_only 齐全 |
| TC-FULL-04 四假使命 | PASS | 四原因齐全 |
| TC-FULL-05 REVOKE 再拒 | PASS | |
| TC-FULL-06 tip len=10 | PASS | |
| TC-FULL-07 DONE / timeout | PASS | rc=124 OK |

## 5. 观测序列（规范期望，与源码合取推导）

下列为 **full 剖面成功时** 的规范观测顺序（与 `client_full.c` + `gatekeeper.c` 一致）。答辩与回归以此为核对表。

| 序 | 观测点 | 期望关键词 |
|---|---|---|
| 1 | 共签查询 | `GATE|COSIGN|STATE=OFF` |
| 2 | 共签前合法请求 | `GATE|DENY|no_human_cosign` |
| 3 | 授予 | `GATE|COSIGN|GRANT (demo stand-in)` |
| 4 | 再查询 | `GATE|COSIGN|STATE=ON` |
| 5 | 合法弱放行 | `GATE|ALLOW_SIM|legal_path_sim` |
| 6 | 弱成功注释 | `GATE|NOTE|sim_only; delivery!=achievement; non-clinical` |
| 7 | 假使命×4 | `expired_entrustment` / `forbidden_zone` / `advisor_cannot_enable` / `empty_U_no_achieve_tag` |
| 8 | 撤销 | `GATE|COSIGN|REVOKE` |
| 9 | 撤销后合法 | `GATE|DENY|no_human_cosign` |
| 10 | 证据 tip | `GATE|CHAIN|tip=…|len=10` |
| 11 | 收尾 | `CLIENT|INFO|MISSION_SHELL_DEMO_DONE` |

一句话口令（与任务书一致）：

> cosign OFF → DENY → GRANT → ALLOW_SIM → 4 DENYs → REVOKE → DENY → tip len=10 → MISSION_SHELL_DEMO_DONE

## 6. 证据链事件表（len=10 推导）

| seq | event | 触发 |
|---|---|---|
| 1 | `gate_init` | gatekeeper `init` |
| 2 | `no_human_cosign` | legal_before_cosign |
| 3 | `cosign_grant` | GRANT |
| 4 | `legal_path_sim` | legal_sim / ALLOW_SIM |
| 5 | `expired_entrustment` | expired_trust |
| 6 | `forbidden_zone` | forbidden_zone |
| 7 | `advisor_cannot_enable` | advisor_enable |
| 8 | `empty_U_no_achieve_tag` | empty_u_achieve |
| 9 | `cosign_revoke` | REVOKE |
| 10 | `no_human_cosign` | legal_after_revoke |

不计入长度：QUERY、EVIDENCE_TIP（只读）。

`tip` 的具体十六进制随实现确定性哈希得到；验收检查 **格式**（8 hex）与 **len=10**，并抽查 EVIDENCE 行 prev/this 邻接一致。

## 7. 缺陷与偏差

| 项 | 状态 |
|---|---|
| 已知功能缺陷 | 无（相对本 SRS） |
| 口径风险 | 人工误读 ALLOW_SIM 为达成 — 靠 NOTE 与答辩脚本缓解 |
| 环境偏差 | SDK 目录布局若与脚本不一致会导致构建失败 — 见实现指南 3.4 |

## 8. 签署栏（模板）

| 角色 | 姓名 | 日期 | 结论 |
|---|---|---|---|
| 执行人 | （填写） | 2026-09-23 | PASS / FAIL |
| 复核人 | （填写） |  |  |

## 9. 声明

本报告不构成临床、法规或 seL4 应用证明主张。FNV-1a32 链为教学级。共签为演示占位。delivery ≠ achievement。
