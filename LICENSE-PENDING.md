# 许可证：待定

本仓库**尚未选定许可证**。许可证由作者决定，仓库整理者没有替作者选择。

在作者选定并加入 `LICENSE` 文件之前，依照著作权法的默认规则，作者保留全部权利：你可以在 GitHub 上浏览和 fork（GitHub 服务条款允许），但除法律允许的合理使用外，请勿复制、修改或再分发本仓库内容。

## 供作者参考的选项

| 内容 | 建议 | 说明 |
|---|---|---|
| 代码（`mission-shell/`、`scripts/`、`thesis/prototype/`、`.github/`） | **MIT** 或 **Apache-2.0** | 两者都是宽松许可证；Apache-2.0 另含明确的专利授权与终止条款。上游 Microkit SDK 的代码部分为 BSD-2-Clause，与二者均兼容 |
| 文档、插图、幻灯片、实验数据（`docs/`、`thesis/*.md`、`thesis/figs/`、日志与报告） | **CC BY 4.0** | 允许再利用，但须署名 |

选定后：添加 `LICENSE`（代码）与 `LICENSE-docs`（文档，如采用双许可证），在 `README.md`、`README.en.md` 与 `CITATION.cff`（`license:` 字段）中注明，然后删除本文件。

## 第三方组件（不随本仓库分发）

| 组件 | 获取方式 | 上游许可证（据 SDK 2.3.1 自带的 LICENSE.md 与 LICENSES/） |
|---|---|---|
| seL4 Microkit SDK 2.3.1 | `scripts/setup_sdk.*` 从 https://github.com/seL4/microkit/releases/tag/2.3.1 下载 | 代码 BSD-2-Clause，文档 CC-BY-SA-4.0；`LICENSES/` 中另含 GPL-2.0-only 与 seL4 商标声明（LicenseRef-Trademark） |
| Docker 镜像 `trustworthysystems/sel4` | 由 Docker 从 Docker Hub 拉取 | 见镜像及 seL4 基金会的说明 |
| seL4 内核、QEMU、GCC 交叉编译器 | 包含在 SDK / 镜像 / 系统软件包中 | 各自的上游许可证 |

`mission-shell/experiment/hostsim/microkit.h` 是本项目为主机模拟编写的接口桩，不是 SDK 文件的拷贝。
