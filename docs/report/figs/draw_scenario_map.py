# Fig 1-1: hypothetical scenarios -> failed conjunction term -> MR -> false missions. Conceptual, no experiment numbers.
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os
for p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc","/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    if os.path.exists(p): fm.fontManager.addfont(p)
plt.rcParams["font.family"]=["Noto Sans CJK SC","DejaVu Sans"]
OUT=os.path.dirname(os.path.abspath(__file__)); DPI=160
BLUE=("#eef4fb","#2b4c7e"); GREEN=("#eaf5ec","#2e7d32"); ORANGE=("#fff6e8","#c9852a"); RED=("#fdecec","#b33a3a"); GRAY=("#f4f4f4","#888888")
fig,ax=plt.subplots(figsize=(13.2,7.4)); ax.set_xlim(0,132); ax.set_ylim(0,74); ax.axis("off"); fig.subplots_adjust(0.01,0.01,0.99,0.99)
def rbox(x,y,w,h,col,lw=1.4):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=0.6",fc=col[0],ec=col[1],lw=lw,zorder=2))
def txt(x,y,s,fs=9,bold=False,c="#1d1d1d"):
    ax.text(x,y,s,fontsize=fs,fontweight="bold" if bold else "normal",color=c,ha="center",va="center",zorder=5,linespacing=1.35)
def arr(x1,y1,x2,y2,c="#333"):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=12,lw=1.3,color=c,zorder=3))
txt(66,71.3,"假设情境 → 失败的合取项 → 使命需求 MR → 证伪用的假使命（及合法对照）",fs=12,bold=True,c="#2b4c7e")
cols=[(3,24,"假设情境",BLUE),(31,28,"失败的合取项",ORANGE),(63,34,"导出的使命需求",GREEN),(101,28,"假使命 / 合法对照",RED)]
for x,w,h,c in cols: txt(x+w/2,66.5,h,fs=10,bold=True,c=c[1])
rows=[("情境一\n托付过期\n（时间）","第二项：仍对准\n（有效期）","MR-1 托付作为一等对象\nMR-2 逐动作核对有效期，默认拒绝\nMR-3 拒绝写入证据链","F1 过期 · F2 尚未生效\n对照 L2（窗口端点）"),
      ("情境二\n建议变使能\n（问责·范围·版本）","第一项：明示判断\n第二项：来源·范围·版本","MR-4 来源可追溯\nMR-5 明示共签（绑定版本）\nMR-6 托付范围检查\nMR-7 版本对准","F4 · F5 · F7 · F8 · F9\n对照 L3、L4"),
      ("情境三\n空 U 贴达成\n（证据）","第三项：可被证伪\n＋ 交付 ≠ 达成","MR-8 无达成成功码，仅 ALLOW_SIM\nMR-9 U 非空声明\nMR-10 结论按 K/P/U 分层","F6（U 为空 / 声称达成）\n对照 L1")]
ys=[48,29,10]; H=15
for y,r in zip(ys,rows):
    for (x,w,_,c),s in zip(cols,r):
        rbox(x,y,w,H,c); txt(x+w/2,y+H/2,s,fs=10)
    for k in range(3):
        x,w=cols[k][0],cols[k][1]; arr(x+w+0.2,y+H/2,cols[k+1][0]-0.2,y+H/2)
txt(66,5.2,"剩余 U：时间源可信性 · 托付记录是否反映审批意图（假绿灯）· 来源字段须如实填写 · 共签是否伴随审议 · U 内容的正确与完整 · 下游对 ALLOW_SIM 的误读",fs=8.6,c="#b33a3a")
txt(66,1.8,"假设情境，示意图；不含实验数据",fs=8,c="#666")
fig.savefig(f"{OUT}/fig1-1_scenario_map.png",dpi=DPI); print("ok")
