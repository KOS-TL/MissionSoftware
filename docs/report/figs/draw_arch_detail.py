import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import os
for p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
          "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    if os.path.exists(p): fm.fontManager.addfont(p)
plt.rcParams["font.family"] = ["Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(13.2, 8.4))
ax.set_xlim(0, 132); ax.set_ylim(0, 84); ax.axis("off")
fig.subplots_adjust(0.01, 0.01, 0.99, 0.99)

def rbox(x, y, w, h, fc, ec, lw=1.4, rs=0.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={rs}", fc=fc, ec=ec, lw=lw, zorder=2))
def txt(x, y, s, fs=9, bold=False, c="#1d1d1d", ha="center", va="center"):
    ax.text(x, y, s, fontsize=fs, fontweight="bold" if bold else "normal",
            color=c, ha=ha, va=va, zorder=4, linespacing=1.35)
def arr(x1, y1, x2, y2, c="#333", lw=1.3, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
        mutation_scale=13, lw=lw, color=c, linestyle=ls, zorder=3))

# ---- K layer container ----
rbox(1.5, 4, 129, 76, "#f7f9fc", "#8aa0bf", lw=1.2, rs=0.8)
txt(66, 78.2, "K 层（仅引用，未自证）：seL4 内核  ·  Microkit SDK 2.3.1  ·  板型 qemu_virt_aarch64  ·  配置 debug",
    fs=9, bold=True, c="#2b4c7e")

# ---- client PD ----
rbox(4, 7, 38, 66, "#eef4fb", "#2b4c7e", lw=1.6)
txt(23, 70.2, "PD client", fs=12, bold=True, c="#2b4c7e")
txt(23, 67.2, "优先级 99  ·  主动线程  ·  地址空间独立", fs=8, c="#555")
rbox(6.5, 54, 33, 10.5, "#ffffff", "#9db4d4")
txt(23, 61.5, "场景脚本 / 语料回放", fs=9.5, bold=True)
txt(23, 58.6, "scenarios/client_*.c", fs=8, c="#555")
txt(23, 56.4, "按 DEMO_PROFILE 依次发出请求", fs=8, c="#555")
rbox(6.5, 41, 33, 10.5, "#ffffff", "#9db4d4")
txt(23, 48.5, "DEMO_PROFILE", fs=9.5, bold=True)
txt(23, 45.6, "full ｜ cosign_only ｜ false_only", fs=8, c="#555")
txt(23, 43.4, "实验剖面：mission_corpus + ABLATE", fs=8, c="#555")
rbox(6.5, 28, 33, 10.5, "#fff6e8", "#c9852a")
txt(23, 35.5, "扮演的角色", fs=9.5, bold=True, c="#8a5a00")
txt(23, 32.6, "操作员 / 顾问 / 人共签通道", fs=8, c="#555")
txt(23, 30.4, "全部是模拟，没有真实操作员", fs=8, c="#555")
rbox(6.5, 9.5, 33, 16, "#fdecec", "#b33a3a")
txt(23, 22.5, "不能做的事", fs=9.5, bold=True, c="#b33a3a")
txt(23, 19.4, "不能读写 gatekeeper 的内存", fs=8)
txt(23, 17.2, "没有第二条通道可绕开门闩", fs=8)
txt(23, 15.0, "不能自行修改共签状态或证据链", fs=8)
txt(23, 12.8, "（由 seL4 权能隔离保证，K 层引用）", fs=7.5, c="#888")

# ---- gatekeeper PD ----
rbox(56, 7, 48, 66, "#eef8f1", "#1f7a4d", lw=1.6)
txt(80, 70.2, "PD gatekeeper", fs=12, bold=True, c="#1f7a4d")
txt(80, 67.2, "优先级 100  ·  被动 PD（仅被调用时运行）", fs=8, c="#555")

rbox(58.5, 53, 43, 12, "#ffffff", "#8fbfa6")
txt(80, 62.2, "① 人共签状态机（默认 OFF）", fs=9.5, bold=True)
txt(80, 59.3, "GRANT → ON ｜ REVOKE → OFF ｜ QUERY", fs=8, c="#555")
txt(80, 57.1, "演示替身，不是电子签名", fs=8, c="#a15c00")
txt(80, 55.0, "OFF 时一切使能请求一律 DENY", fs=8, c="#555")

rbox(58.5, 33.5, 43, 17.5, "#ffffff", "#8fbfa6")
txt(80, 48.4, "② 判定（固定优先级，先命中先返回）", fs=9.5, bold=True)
txt(80, 45.6, "无共签 → no_human_cosign", fs=8)
txt(80, 43.4, "托付过期 → expired_entrustment", fs=8)
txt(80, 41.2, "禁区 → forbidden_zone", fs=8)
txt(80, 39.0, "顾问使能 → advisor_cannot_enable", fs=8)
txt(80, 36.8, "空 U 申报达成 → empty_U_no_achieve_tag", fs=8)
txt(80, 34.9, "全部不命中 → ALLOW_SIM（无“达成”返回码）", fs=8, bold=True, c="#1f7a4d")

rbox(58.5, 21, 43, 10.5, "#ffffff", "#8fbfa6")
txt(80, 28.6, "③ 证据链 FNV-1a32（教学级）", fs=9.5, bold=True)
txt(80, 25.8, "EVIDENCE | seq | prev | this | event", fs=8, c="#555")
txt(80, 23.6, "可查询链尾 tip 与长度；非密码学强度", fs=8, c="#a15c00")

rbox(58.5, 9.5, 43, 9.5, "#fff6e8", "#c9852a")
txt(80, 16.4, "每次放行必附注记", fs=9.5, bold=True, c="#8a5a00")
txt(80, 13.6, "sim_only; delivery!=achievement; non-clinical", fs=8)
txt(80, 11.4, "放行 ≠ 使命达成；非临床", fs=8, c="#555")

# ---- serial ----
rbox(109, 30, 19.5, 28, "#fff8ee", "#c9852a", lw=1.4)
txt(118.7, 54.8, "调试串口", fs=10, bold=True, c="#8a5a00")
txt(118.7, 51.6, "关键词契约", fs=8, c="#555")
for i, s in enumerate(["GATE|DENY|…", "GATE|ALLOW_SIM|…", "GATE|NOTE|…", "GATE|COSIGN|…", "EVIDENCE|…", "GATE|CHAIN|tip"]):
    txt(118.7, 47.6 - i * 2.6, s, fs=7.6, c="#444")

# ---- arrows ----
arr(42, 52, 56, 52, c="#2b4c7e")
txt(49, 53.4, "PPC ch0", fs=8, bold=True, c="#2b4c7e")
txt(49, 50.4, "pp=true", fs=7.5, c="#555")
arr(56, 46, 42, 46, c="#1f7a4d")
txt(49, 44.4, "REP_*", fs=8, bold=True, c="#1f7a4d")
arr(104, 44, 109, 44, c="#c9852a", ls="--")
txt(106.5, 45.6, "dbg", fs=7.5, c="#8a5a00")

# ---- caption ----
txt(66, 5.2, "A 层：演示代码，未形式化验证     ·     M 层：共签、对准、证据纪律     ·     U：真签名、真硬件、临床、密码学强度",
    fs=8.5, c="#555")
txt(66, 1.6, "系统描述 mission.system 在构建时静态确定：两个保护域、一条通道，运行中不可新增",
    fs=8, c="#888")
fig.savefig(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "fig-arch-detail.png"), dpi=160)  # v0.1.0: repo-relative
print("saved")
