# 测试计划与验收规范

> **仓库化说明（v0.1.0）**：本文为项目过程中的历史文档，按原文收录，仅做去个人化处理：作者本机路径已替换为 `<REPO_ROOT>`（= 本仓库克隆目录，内含 `mission-shell/` 与 `microkit-sdk-2.3.1/`）、`<WORKDIR>`（作者文档目录）或仓库内相对路径；形如 `/workspace/...` 的路径是作者沙箱（box）上的历史路径，在本仓库中分别对应 `mission-shell/`（原 `/workspace/microkit-mission-shell/`）与 `docs/`。文中命令含占位符，**不能直接复制执行**；可直接执行的命令见仓库根目录 `README.md` 与 `docs/REPRODUCE.md`。


**版本**：1.0.0  
**日期**：2026-09-23  
**主验收剖面**：`DEMO_PROFILE=full`

---

## 1. 测试目标

验证 mission-shell 是否满足 SRS R1–R7，尤其是：

- 共签默认 OFF 与 GRANT/REVOKE 行为  
- 假使命四条必须 DENY  
- ALLOW_SIM 弱语义与强制 NOTE  
- 证据链 tip/len  
- 三档 profile 可构建可跑  

**非目标**：临床有效性、密码学强度、seL4 应用证明、性能基准。

---

## 2. 测试级别

| 级别 | 名称 | 范围 | 是否计入应用使命 V&V |
|---|---|---|---|
| S0 | 工具链/底座冒烟 | Docker 内 `sel4test` 等（课题分期） | 否（仅环境门禁） |
| S1-B | 构建冒烟 | 生成 `loader.img` | 是（前置） |
| S1-I | 集成 | QEMU 起至用户态 PD | 是（前置） |
| S1-A | 验收/场景 | 串口关键词契约 | **是（主）** |
| S1-R | 回归 | 同命令复跑对照本报告 | 是 |

---

## 3. 环境与前置

- 镜像：`trustworthysystems/sel4:latest`  
- 挂载：`<REPO_ROOT>:/work`  
- SDK 路径按 `docker_build_run.sh`  
- Board：`qemu_virt_aarch64`  

---

## 4. 通过/失败总则

| 规则 | 说明 |
|---|---|
| 关键词契约优先 | 以串口稳定子串判定，不以「看起来跑起来了」 |
| rc=124 OK | `timeout` 杀死 QEMU 可接受；脚本本身 exit 0 |
| rc 构建失败 | make 非 0 → 失败 |
| 旧日志无效 | 无 `DEMO_PROFILE=` 行的历史记录不得用于现行验收 |
| 负面必测 | 假使命未出现 DENY → 失败 |

---

## 5. 测试用例

### TC-FULL-01 构建与启动（S1-B/I）

- **步骤**：执行第 6 节 Docker 命令  
- **期望**：打印 `DEMO_PROFILE=full`；生成 `loader.img`；出现 `GATE|INFO|mission shell init`  
- **关联**：R7, NFR1

### TC-FULL-02 共签默认 OFF（R1）

- **期望**：`GATE|COSIGN|STATE=OFF`；`CLIENT|REP|COSIGN_OFF`  
- **随后**：`CLIENT|REQ|legal_before_cosign` → `GATE|DENY|no_human_cosign`；`CLIENT|REP|DENY`

### TC-FULL-03 GRANT 与合法弱放行（R1,R3）

- **期望**：`GATE|COSIGN|GRANT (demo stand-in)`；再 QUERY `STATE=ON`  
- **期望**：`GATE|ALLOW_SIM|legal_path_sim`  
- **期望**：`GATE|NOTE|sim_only; delivery!=achievement; non-clinical`  
- **期望**：`CLIENT|REP|ALLOW_SIM`

### TC-FULL-04 假使命集（R2.1–R2.4）

| 步骤 REQ 名 | 期望 DENY 原因 |
|---|---|
| expired_trust | expired_entrustment |
| forbidden_zone | forbidden_zone |
| advisor_enable | advisor_cannot_enable |
| empty_u_achieve | empty_U_no_achieve_tag |

均须 `CLIENT|REP|DENY`。

### TC-FULL-05 REVOKE 后再拒（R1）

- **期望**：`GATE|COSIGN|REVOKE`  
- **期望**：`legal_after_revoke` → `GATE|DENY|no_human_cosign`

### TC-FULL-06 证据 tip（R4）

- **期望**：`GATE|CHAIN|tip=` 后跟 8 位十六进制  
- **期望**：`|len=10`  
- **期望**：存在 `EVIDENCE|seq=1` … 至与判定一致的追加序列  
- **期望**：`CLIENT|REP|EVIDENCE_TIP`

### TC-FULL-07 收尾标记

- **期望**：`CLIENT|INFO|MISSION_SHELL_DEMO_DONE`  
- **期望**：可出现 `=== QEMU done rc=124 ===`（或其它 timeout 码）；**不**因此判失败

### TC-COSIGN-01（profile=cosign_only）

- **命令**：`-e DEMO_PROFILE=cosign_only`  
- **期望**：`CLIENT|INFO|profile=cosign_only`  
- **期望**：无共签时 LEGAL→DENY；GRANT 后 LEGAL→ALLOW_SIM；REVOKE 后再 DENY；DONE  
- **关联**：R1,R3,R6

### TC-FALSE-01（profile=false_only）

- **命令**：`-e DEMO_PROFILE=false_only`  
- **期望**：先 GRANT；四假使命均 DENY；DONE  
- **关联**：R2,R6

---

## 6. 主验收命令（精确）

```bat
docker run --rm -e DEMO_PROFILE=full -v <REPO_ROOT>:/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_build_run.sh
```

---

## 7. 期望串口关键词清单（full，检查用）

按出现先后（允许夹杂其它行）：

1. `DEMO_PROFILE=full`（宿主机脚本 echo）  
2. `GATE|INFO|mission shell init`  
3. `EVIDENCE|seq=1` … `gate_init`  
4. `CLIENT|INFO|profile=full`  
5. `GATE|COSIGN|STATE=OFF`  
6. `GATE|DENY|no_human_cosign`  
7. `GATE|COSIGN|GRANT (demo stand-in)`  
8. `GATE|COSIGN|STATE=ON`  
9. `GATE|ALLOW_SIM|legal_path_sim`  
10. `GATE|NOTE|sim_only; delivery!=achievement; non-clinical`  
11. `GATE|DENY|expired_entrustment`  
12. `GATE|DENY|forbidden_zone`  
13. `GATE|DENY|advisor_cannot_enable`  
14. `GATE|DENY|empty_U_no_achieve_tag`  
15. `GATE|COSIGN|REVOKE`  
16. `GATE|DENY|no_human_cosign`（再次）  
17. `GATE|CHAIN|tip=` … `|len=10`  
18. `CLIENT|INFO|MISSION_SHELL_DEMO_DONE`

---

## 8. 回归策略

- 门闩行为变更（判定分支、默认共签、NOTE 文案、证据混入方式）必须重跑 TC-FULL-01…07 并更新测试报告版本。  
- 仅文档/注释变更：可免跑，但需在变更记录注明。  
- Profile 增删：更新本计划用例表与追溯矩阵。  

---

## 9. 测试交付物

- 本计划  
- `05-测试报告-DEMO_PROFILE-full.md`（及必要时其它剖面报告）  
- 原始串口摘录（附录或跑通记录仓库）  
