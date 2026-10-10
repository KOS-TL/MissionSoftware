# 许可证说明 / Licensing

本仓库采用双许可证 / This repository is dual-licensed:

| 内容 / Content | 许可证 / License | 文件 / File |
|---|---|---|
| 代码：`mission-shell/`、`scripts/`、`thesis/prototype/`、`.github/` | MIT | [`LICENSE`](LICENSE) |
| 文档、插图、幻灯片、实验数据与报告：`docs/`、`thesis/` 中的文档与插图、`mission-shell/experiment/` 下的日志与报告 | CC BY 4.0 | [`LICENSE-docs`](LICENSE-docs) |

版权所有 / Copyright (c) 2026 Chen Peng。转载或改编文档时请署名并注明出处。

## 第三方组件（不随本仓库分发）

| 组件 | 获取方式 | 上游许可证（据 SDK 2.3.1 自带的 LICENSE.md 与 LICENSES/） |
|---|---|---|
| seL4 Microkit SDK 2.3.1 | `scripts/setup_sdk.*` 从 <https://github.com/seL4/microkit/releases/tag/2.3.1> 下载 | 代码 BSD-2-Clause，文档 CC-BY-SA-4.0；`LICENSES/` 中另含 GPL-2.0-only 与 seL4 商标声明（LicenseRef-Trademark） |
| Docker 镜像 `trustworthysystems/sel4` | 由 Docker 从 Docker Hub 拉取 | 见镜像及 seL4 基金会的说明 |
| seL4 内核、QEMU、GCC 交叉编译器 | 包含在 SDK / 镜像 / 系统软件包中 | 各自的上游许可证 |

`mission-shell/experiment/hostsim/microkit.h` 是本项目为主机模拟编写的接口桩，不是 SDK 文件的拷贝。
