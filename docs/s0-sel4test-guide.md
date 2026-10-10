# seL4 半天跑通清单（Windows + Docker）

> **文档性质**：本科/演示环境搭建笔记，服务「使命软件工程」分期中的 **S0→S1**。  
> **非目标**：不宣称达到 seL4 形式化验证级保证；不做临床/出束；不把「测试绿 / QEMU 跑通」写成「使命达成」。  
> **日期**：2026-09-23  
> **仓库化说明（v0.1.0）**：`<WORKDIR>` 指你自选的、不含中文与空格的 Windows 工作目录（例如 `D:\work`），`<WORKDIR_WSL>` 是它在 WSL 中的对应路径（例如 `/mnt/d/work`）。本文是 S0（sel4test）环境笔记，与本仓库的 S1 演示相互独立；S1 复现请看仓库根目录 `README.md` 与 `docs/REPRODUCE.md`。  

---

## 0. 你要得到什么

半天结束时，应同时具备：

1. 本机 Docker 里能 **编译** `sel4test`；
2. QEMU 里能 **跑完** 测试，看到 `All is well in the universe`；
3. 书面分清三层：
   - **K**：seL4 内核（他人已验证的底座，本课题一般不改、不重证）；
   - **A**：你的用户态应用 / CAmkES 或 Microkit 保护域（毕设主战场）；
   - **M**：使命外壳（托付 · 禁区 · 证据 · 人审判）——挂在 A 上，**不是**内核证明的自动推论。

对应毕设 **题目 1**：基于 seL4 用户态服务的使命约束外壳设计与演示。

---

## 1. 前置检查（15 分钟）

### 1.1 硬件与软件

| 项 | 建议 |
|----|------|
| OS | Windows 10/11 |
| 内存 | ≥16 GB（Docker 分配 ≥8 GB） |
| 磁盘 | 空余 ≥40 GB（源码+镜像+构建） |
| 软件 | Docker Desktop（已装且 **Running**） |
| 可选 | WSL2 后端；Git for Windows |

Docker Desktop → Settings → Resources：Memory **≥ 8 GB**，Disk 足够。QEMU 在容器里内存不够会莫名失败。

### 1.2 网络

需能访问 GitHub（`github.com/seL4/...`）。若公司网拦截，改用可用镜像或代理后再 `repo sync`。

### 1.3 成功判据（本阶段）

- [ ] `docker version` 正常  
- [ ] 进入官方 seL4 构建容器  
- [ ] `sel4test` 配置 `-DSIMULATION=TRUE` 后 `ninja` 成功  
- [ ] `./simulate` 跑完并出现成功句  
- [ ] 笔记中写明：本阶段证明的是 **工具链+仿真**，不是使命达成  

---

## 2. 推荐路径：官方 Docker（少踩依赖坑）

官方说明：

- Dockerfiles：https://docs.sel4.systems/projects/dockerfiles/  
- 机器依赖：https://docs.sel4.systems/projects/buildsystem/host-dependencies.html  
- sel4test：https://docs.sel4.systems/projects/sel4test/  
- 教程 Setup：https://docs.sel4.systems/Tutorials/setting-up  

### 2.1 拉取 Docker 环境（约 20–40 分钟，视网速）

在 **PowerShell** 或 **Ubuntu (WSL)** 中：

```powershell
cd <WORKDIR>
git clone https://github.com/seL4/seL4-CAmkES-L4v-dockerfiles.git
cd seL4-CAmkES-L4v-dockerfiles
# 若 make 不可用，在「Ubuntu WSL」里执行下列命令
```

在 WSL/Git Bash（有 `make`）中：

```bash
cd <WORKDIR_WSL>/seL4-CAmkES-L4v-dockerfiles
make user
```

第一次会拉较大镜像。成功后你在**容器 shell**里，提示符会变化。

> 工作习惯（官方建议）：  
> - **终端 A（宿主机）**：git、编辑代码  
> - **终端 B（容器）**：只做编译与 `./simulate`

### 2.2 获取 sel4test 源码（约 15–30 分钟）

**在宿主机**（路径选你文档区，避免中文空格）：

```bash
# WSL 示例
sudo apt-get update
sudo apt-get install -y repo curl git python3

mkdir -p <WORKDIR_WSL>/sel4test
cd <WORKDIR_WSL>/sel4test
repo init -u https://github.com/seL4/sel4test-manifest.git
repo sync
```

Windows 原生若无 `repo`，用 WSL 做这一步最省事。

### 2.3 在容器内配置、编译、仿真（约 30–60 分钟）

进入容器后挂载到源码目录（按你实际的 `container` / `make user` 别名调整；常见是在源码目录执行官方文档中的 `container` 别名）。

```bash
cd /host/sel4test          # 路径以容器内实际挂载为准
mkdir -p build-x86 && cd build-x86
../init-build.sh -DPLATFORM=x86_64 -DSIMULATION=TRUE
ninja
./simulate
```

**期望：**

- 大量测试输出（DEBUG 下会有**故意失败**的负向测试日志，属正常）；  
- 结尾：`All is well in the universe`；  
- 退出 QEMU：先 `Ctrl-a`，再按 `x`。

**备选平台**（若 x86_64 有问题）：

```bash
../init-build.sh -DPLATFORM=ia32 -DSIMULATION=TRUE
# 或 ARM 示例（见官方 host-dependencies）：
# ../init-build.sh -DSIMULATION=TRUE -DAARCH32=TRUE -DPLATFORM=sabre
```

### 2.4 常见失败与处置

| 现象 | 处置 |
|------|------|
| QEMU 立刻挂 / 无输出 | Docker 内存调到 ≥8GB 后重建容器 |
| `repo sync` 失败 | 检查代理/GitHub 访问；重试 |
| `ninja` 缺工具 | 确认命令在**官方容器内**执行，勿在裸 Windows 编 |
| 路径在 `/mnt/d` 极慢 | 把源码放到 WSL 家目录 `~/sel4test` 再挂载 |
| 误把测试错误当失败 | 看结尾是否有成功句；读 sel4test 文档说明 |

---

## 3. 跑通之后：接到毕设题目 1 的切入点

不要停在「内核测通」。题目 1 的主线是 **用户态使命外壳**。

### 3.1 建议的最小增量（下一周）

1. **选定载体**（二选一，优先 B 给本科）：  
   - A. CAmkES 组件  
   - B. **Microkit** 保护域（SDK + QEMU virt，文档更利落）  
     - https://docs.sel4.systems/projects/microkit/tutorial/part0.html  
2. **实现一个「伪设备」用户态服务**（例如：仿真「放行门闩」状态机，**无**真硬件）。  
3. **挂上使命四件**：  
   - 托付文书（谁签发、时效、范围）；  
   - 禁区表（明确拒绝的请求类型）；  
   - 证据追加（请求/拒绝/哈希）；  
   - 人审判占位（共签前拒绝贴「达成」）。  
4. **假使命用例至少 3 个**：过期托付、越权角色、建议通道妄图使能。  

### 3.2 保证分级表（开题/答辩必贴）

| 层级 | 内容 | 本毕设是否声称「已证明」 |
|------|------|-------------------------|
| K seL4 内核 | 隔离/能力等（上游证明） | **引用，不重做** |
| A 用户态服务 | 你的代码正确性 | 测试 + 可选轻量模型；**非** CompCert/seL4 级 |
| M 使命外壳 | 托付·禁区·证据·人审判纪律 | 可机检门禁 + 用例；**交付≠达成** |
| U 未覆盖 | 真硬件、侧信道、规范错误、共签缺失… | **必须非空列出** |

### 3.3 与「理念剧场 / MRTDS」的关系

- MRTDS Docker 理念剧场：讲清**方法纪律**（可继续用）。  
- 本清单：换到底座 **seL4+QEMU**，证明「形式化验证生态上可挂使命外壳」。  
- **禁止混写**：seL4test 绿灯 ≠ 放射联锁可用；Microkit 演示 ≠ 注册资料。

---

## 4. 半天时间盒（建议日程）

| 时段 | 任务 |
|------|------|
| 0:00–0:15 | Docker 资源、目录 `<WORKDIR>` |
| 0:15–1:00 | clone dockerfiles，`make user` 进容器 |
| 1:00–1:45 | `repo init/sync` sel4test |
| 1:45–3:00 | `init-build` + `ninja` + `./simulate` |
| 3:00–3:30 | 记录日志截图、写 P/U 表草稿 |
| 3:30–4:00 | 浏览 Microkit tutorial part0，定题目 1 下周任务 |

超时未跑通：优先保「容器能编」，仿真放到第二天；不要同时开 CAmkES+验证全栈。

---

## 5. 验收清单（可直接贴任务书）

- [ ] 附：一次完整 `./simulate` 尾部日志（含成功句）  
- [ ] 附：`init-build.sh` 完整参数行  
- [ ] 书面声明：本阶段仅验证 **S0 工具链与仿真**  
- [ ] 列出题目 1 的 A/M 边界与至少 3 条 \(U\)  
- [ ] 明确非目标：临床、出束写使能、等同 seL4 证明、注册材料  

---

## 6. 参考链接（精简）

1. https://docs.sel4.systems/Tutorials/setting-up  
2. https://docs.sel4.systems/projects/dockerfiles/  
3. https://docs.sel4.systems/projects/sel4test/  
4. https://docs.sel4.systems/projects/buildsystem/host-dependencies.html  
5. https://docs.sel4.systems/Hardware/X64.html（PC99 / 仿真）  
6. https://docs.sel4.systems/projects/microkit/tutorial/part0.html  

---

*圆心复述：明示托付 ∧ 仍在执行这一件 ∧ 检查可被证伪。人立法、划界、审判；模型不签发托付、不使能。*
