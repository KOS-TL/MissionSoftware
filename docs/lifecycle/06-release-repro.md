# 发布与复现手册

> **仓库化说明（v0.1.0）**：本文为项目过程中的历史文档，按原文收录，仅做去个人化处理：作者本机路径已替换为 `<REPO_ROOT>`（= 本仓库克隆目录，内含 `mission-shell/` 与 `microkit-sdk-2.3.1/`）、`<WORKDIR>`（作者文档目录）或仓库内相对路径；形如 `/workspace/...` 的路径是作者沙箱（box）上的历史路径，在本仓库中分别对应 `mission-shell/`（原 `/workspace/microkit-mission-shell/`）与 `docs/`。文中命令含占位符，**不能直接复制执行**；可直接执行的命令见仓库根目录 `README.md` 与 `docs/REPRODUCE.md`。


**版本**：1.0.0  
**日期**：2026-09-23

---

## 1. 交付物清单

| 交付物 | 位置（典型） | 说明 |
|---|---|---|
| 源码树 | `<REPO_ROOT>\mission-shell` | gatekeeper/client/协议/脚本 |
| Microkit SDK 2.3.1 | `…\microkit_work\microkit-sdk-2.3.1` 或工程内 | 按 docker 脚本路径 |
| 本生命周期文档包 | `docs/lifecycle/` | SRS/SDD/测试/追溯等 |
| 开题报告 | `<WORKDIR>\` 下题目1开题 | 立项 |
| 传统 SE 纳入说明 | `traditional-SE-embedded-in-mission-shell.md` | 立场 |
| PU 边界 | `docs/PU_BOUNDARY.md` | K/A/M/U |
| 跑通记录 | 课题「跑通记录」目录/文件 | 须含 DEMO_PROFILE=full |
| 答辩 PPT | 题目1演示稿 | 口述配合日志 |

**非交付**：临床数据、写使能固件、应用级形式化证明物件。

---

## 2. 复现步骤（从零到验收）

1. 确认 Docker 可用；拉取或已有 `trustworthysystems/sel4:latest`。  
2. 确认目录：`<REPO_ROOT>\mission-shell` 含本仓库文件；SDK 路径满足 `docker_build_run.sh`。  
3. **必须**设置环境变量：

```bat
docker run --rm -e DEMO_PROFILE=full -v <REPO_ROOT>:/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_build_run.sh
```

4. 保存完整终端输出为跑通记录；核对 `04`/`05` 关键词表。  
5. 可选：再跑 `cosign_only`、`false_only` 作对照实验。

---

## 3. 演示口述脚本（约 2–3 分钟）

建议顺序指串口，口播四点：

1. **托付（明示）**  
   「系统启动共签是 OFF。没有人侧 GRANT 之前，合法仿真请求也被拒绝——日志里是 `no_human_cosign`。这不是功能坏了，而是明示托付没成立。」

2. **人审判**  
   「接下来 GRANT——注意括号写着 demo stand-in，这是演示占位，不是电子签名产品。查询变为 ON 之后，合法路径才出现 `ALLOW_SIM`。」

3. **禁区 / 假使命**  
   「共签开了也不等于什么都能做：过期托付、禁区、顾问妄图使能、空 U 贴达成——四条全部 DENY。对准失败就不能放行。」

4. **证据与弱成功**  
   「每次关键判定进 FNV-1a32 教学链；最后 tip 长度 10。`ALLOW_SIM` 下面有一行 NOTE：`sim_only; delivery!=achievement; non-clinical`。交付或仿真放行，不等于使命达成。我们也不宣称 seL4 应用证明。」

收尾：「DONE 标记出现；QEMU 被 timeout 杀掉返回 124 是预期收工方式。」

---

## 4. 已知陷阱（Pitfalls）

| 陷阱 | 表现 | 处理 |
|---|---|---|
| 未设 `DEMO_PROFILE=full` | 可能默认为 full，但旧记录缺失声明 → **验收无效** | 命令行显式 `-e DEMO_PROFILE=full` |
| Windows 路径 / 卷挂载 | Docker 找不到 `/work/mission-shell` | 使用 `D:/…` 正斜杠挂载 |
| 中文路径打 tar | 某些工具损坏文件名 | 文档包同时提供 ASCII 文件名副本；tar 用 UTF-8 |
| NTFS junction / subst | 卷内容不是预期树 | 避免对 SDK 用断裂 junction |
| 把 rc=124 当失败 | 误判验收 | 以关键词为准 |
| 把 ALLOW_SIM 写成达成 | 口径越界 | 对照 SRS R3 与口述稿 |
| SDK 路径不一致 | make 找不到 board | 对齐 `/work/microkit-sdk-2.3.1` |
| 修改 gatekeeper 后不改追溯 | 文档漂移 | 走变更管理（文档 08） |

---

## 5. 发布检查单（Checklist）

- [ ] Docker full 命令跑通且关键词齐全  
- [ ] 跑通记录含 `DEMO_PROFILE=full`  
- [ ] SRS/SDD/追溯与源码符号一致  
- [ ] PU 边界与非目标未削弱  
- [ ] PPT/口述不含临床或 seL4 应用证明表述  

---

## 6. 回滚

若现场演示失败：不要「调宽」门闩蒙混；记录失败关键词，改回上次基线 tag/提交后重跑。门闩放宽属重大变更，须重验收。
