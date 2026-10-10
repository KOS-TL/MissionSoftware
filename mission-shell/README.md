# Microkit 使命外壳演示（题目 1 / S1）

非临床 · 仅仿真 · 不宣称 seL4 级应用证明 · 交付≠达成 · 人共签默认关闭。

## 快速跑（Docker）

在**仓库根目录**（含 `mission-shell/` 与 `microkit-sdk-2.3.1/`；SDK 用 `scripts/setup_sdk.sh` 或 `scripts\windows\setup_sdk.bat` 获取）执行：

```bash
# bash（Linux / macOS / WSL / Git Bash）
docker run --rm -e DEMO_PROFILE=full -v "$PWD":/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_build_run.sh
```

```bat
REM Windows cmd
docker run --rm -e DEMO_PROFILE=full -v "%cd%":/work -w /work/mission-shell trustworthysystems/sel4:latest bash /work/mission-shell/docker_build_run.sh
```

或直接用封装脚本：`bash scripts/run_demo.sh full`、`scripts\windows\run_demo.bat full`（见仓库根 `README.md`）。

可选：`cosign_only` / `false_only`。

## 期望串口（full）

1. 共签查询 OFF → 合法请求 DENY(`no_human_cosign`)  
2. GRANT → 合法 ALLOW_SIM  
3. 假使命 DENY  
4. REVOKE → 合法再 DENY  
5. `MISSION_SHELL_DEMO_DONE`

详见 `docs/PU_BOUNDARY.md`（原文还引用了一份未随仓库发布的内部任务书《毕设任务书-题目1-S0S1》）。
