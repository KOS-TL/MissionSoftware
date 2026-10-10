import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np, os
for p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc","/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    if os.path.exists(p): fm.fontManager.addfont(p)
plt.rcParams["font.family"]=["Noto Sans CJK SC","DejaVu Sans"]
plt.rcParams["axes.unicode_minus"]=False
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs")  # v0.1.0: repo-relative (was the author's box path)

def box(ax,x,y,w,h,txt,fc="#eef3fb",ec="#2b4c7e",fs=10,bold=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02,rounding_size=0.08",fc=fc,ec=ec,lw=1.3))
    ax.text(x+w/2,y+h/2,txt,ha="center",va="center",fontsize=fs,fontweight="bold" if bold else "normal",wrap=True)
def arrow(ax,x1,y1,x2,y2,style="-|>",ls="-",c="#333"):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle=style,mutation_scale=14,lw=1.2,color=c,linestyle=ls))

# Fig 3-1 lifecycle overlay
fig,ax=plt.subplots(figsize=(10,4.6)); ax.set_xlim(0,10); ax.set_ylim(0,4.6); ax.axis("off")
stages=["需求\nSRS R1–R7","设计\nSDD D1–D7","实现\ngatekeeper / client","测试\nS0 门禁 · S1 full","发布 / 复现\nDocker · 跑通记录"]
over=["谁托付、何时有效\n何谓不得宣称达成","共签不可默许\n敏感路径必经门闩","默认拒绝；ALLOW_SIM\n必附 sim_only 注记","假使命必须被拒\n通过准则改写","验收看纪律日志\n不看功能成功感"]
for i,(s,o) in enumerate(zip(stages,over)):
    x=0.2+i*1.95
    box(ax,x,2.85,1.7,1.1,s,fs=10,bold=True)
    box(ax,x,0.75,1.7,1.25,o,fc="#fff4e5",ec="#b86e00",fs=8.8)
    arrow(ax,x+0.85,2.0,x+0.85,2.85,style="-|>",ls="--",c="#b86e00")
    if i<4: arrow(ax,x+1.7,3.4,x+1.95,3.4)
ax.text(5,4.3,"传统软件工程生命周期（保持完整）",ha="center",fontsize=11,fontweight="bold",color="#2b4c7e")
ax.text(5,0.3,"使命叠加：明示托付 ∧ 当前动作仍对准该托付 ∧ 检查可被证伪（逐阶段可机检）",ha="center",fontsize=10.5,fontweight="bold",color="#b86e00")
fig.tight_layout(); fig.savefig(f"{OUT}/fig3-1_overlay.png",dpi=200); plt.close(fig)

# Fig 4-1 architecture
fig,ax=plt.subplots(figsize=(9,4.2)); ax.set_xlim(0,9); ax.set_ylim(0,4.2); ax.axis("off")
ax.add_patch(FancyBboxPatch((0.2,0.9),6.2,3.0,boxstyle="round,pad=0.02",fc="#f7f7f7",ec="#666",lw=1,ls="--"))
ax.text(0.4,3.65,"seL4 + Microkit（K 层：仅引用）· qemu_virt_aarch64 · Microkit SDK 2.3.1 · config=debug",fontsize=8.8,color="#444")
box(ax,0.6,1.3,2.2,1.9,"PD client\npriority 99（主动）\n场景脚本 / 语料回放\nscenarios/client_*.c",fs=9)
box(ax,3.9,1.3,2.2,1.9,"PD gatekeeper\npriority 100（passive）\n共签状态机 · 判定\n证据链 FNV-1a32",fs=9,fc="#e8f5e9",ec="#2e7d32")
arrow(ax,2.8,2.45,3.9,2.45); ax.text(3.35,2.6,"PPC ch0\npp=true",ha="center",fontsize=8)
arrow(ax,3.9,1.95,2.8,1.95); ax.text(3.35,1.6,"REP_*",ha="center",fontsize=8)
box(ax,7.0,1.6,1.8,1.4,"调试串口\n关键词契约\nGATE| / EVIDENCE|\nCLIENT|",fs=8.5,fc="#fff4e5",ec="#b86e00")
arrow(ax,6.1,2.3,7.0,2.3)
ax.text(4.5,0.45,"A 层：演示代码，未形式化验证；M 层：共签·对准·证据纪律；U：真签名、真硬件、临床、密码学强度",ha="center",fontsize=8.6)
fig.tight_layout(); fig.savefig(f"{OUT}/fig4-1_arch.png",dpi=200); plt.close(fig)

# Fig 4-2 cosign state machine
fig,ax=plt.subplots(figsize=(8,3.4)); ax.set_xlim(0,8); ax.set_ylim(0,3.4); ax.axis("off")
from matplotlib.patches import Circle
for (x,t,fc) in [(2,"OFF\n(human_cosign_ok=0)","#fdecea"),(6,"ON","#e8f5e9")]:
    ax.add_patch(Circle((x,1.7),0.75,fc=fc,ec="#333",lw=1.3)); ax.text(x,1.7,t,ha="center",va="center",fontsize=9.5)
arrow(ax,0.4,1.7,1.25,1.7); ax.text(0.5,1.95,"init",fontsize=9)
ax.add_patch(FancyArrowPatch((2.6,2.2),(5.4,2.2),connectionstyle="arc3,rad=-0.3",arrowstyle="-|>",mutation_scale=14,lw=1.2))
ax.text(4,3.0,"REQ_HUMAN_COSIGN_GRANT (20)",ha="center",fontsize=9)
ax.add_patch(FancyArrowPatch((5.4,1.2),(2.6,1.2),connectionstyle="arc3,rad=-0.3",arrowstyle="-|>",mutation_scale=14,lw=1.2))
ax.text(4,0.35,"REQ_HUMAN_COSIGN_REVOKE (21)",ha="center",fontsize=9)
ax.text(2,0.65,"QUERY→REP_COSIGN_OFF\n使能类请求→DENY no_human_cosign",ha="center",fontsize=8)
ax.text(6,0.65,"QUERY→REP_COSIGN_ON\n再经对准检查",ha="center",fontsize=8)
fig.tight_layout(); fig.savefig(f"{OUT}/fig4-2_cosign.png",dpi=200); plt.close(fig)

# Fig 6-1 pipeline
fig,ax=plt.subplots(figsize=(10,3.6)); ax.set_xlim(0,10); ax.set_ylim(0,3.6); ax.axis("off")
items=[("语料生成\ngen_corpus.py\n5 种子×320","#eef3fb"),("草稿 oracle\nrules_spec.md\noracle.py","#fff4e5"),("C 头\ncorpus_c.py\n仅请求字段","#eef3fb"),("构建\nB / B+ / M / M−k\ngatekeeper_field.c","#e8f5e9"),("QEMU 运行\nrun_matrix.sh\n串口日志","#eef3fb"),("解析与统计\nparse_serial.py\nanalyze.py","#eef3fb")]
for i,(t,fc) in enumerate(items):
    x=0.15+i*1.65; box(ax,x,1.4,1.4,1.5,t,fc=fc,fs=8.5)
    if i<5: arrow(ax,x+1.4,2.15,x+1.65,2.15)
box(ax,6.75,0.1,3.0,0.9,"篡改轨道 T1–T7（离线，对日志副本）\ntamper.py / run_tamper.py",fc="#fdecea",ec="#a33",fs=8.3)
arrow(ax,7.35,1.4,7.6,1.0,ls="--")
ax.text(1.0,0.55,"SHA-256 哈希校验（prereg §7）\n不一致即退出",fontsize=8.3)
ax.text(5,3.35,"判决只依据请求字段 + 托付表 + 逻辑时钟；MR_CASE_ID 仅用于日志关联",ha="center",fontsize=9.5,fontweight="bold")
fig.tight_layout(); fig.savefig(f"{OUT}/fig6-1_pipeline.png",dpi=200); plt.close(fig)

# Fig 7-1 FNR per category
cats=["F1","F2","F3","F4","F5","F6","F7","F8","F9","M1","X1"]
B=[100,100,100,0,100,100,100,100,100,0,0]
Bp=[60,60,20,0,100,100,100,100,100,0,0]
M=[0]*11
x=np.arange(len(cats)); w=0.27
fig,ax=plt.subplots(figsize=(10,5))
ax.bar(x-w,B,w,label="B（5 种子合并，每类 n=100 / M1、X1 n=50）",color="#7a8ca8")
ax.bar(x,Bp,w,label="B+（首个种子，每类 n=20 / M1、X1 n=10）",color="#d9a441")
ax.bar(x+w,M,w,label="M（5 种子合并）",color="#2e7d32")
for i,v in enumerate(M): ax.text(x[i]+w,1.5,"0",ha="center",fontsize=7.5,color="#2e7d32")
ax.set_xticks(x); ax.set_xticklabels(cats); ax.set_ylabel("漏检率 FNR（%）"); ax.set_ylim(0,112)
ax.legend(fontsize=8.5,loc="upper center",bbox_to_anchor=(0.5,-0.12),ncol=1,frameon=False); ax.grid(axis="y",alpha=0.3)
ax.set_title("作者语料 A 上各类别漏检率（装置自检，非确证性）",fontsize=11)
fig.tight_layout(); fig.savefig(f"{OUT}/fig7-1_fnr.png",dpi=200); plt.close(fig)

# Fig 7-2 ablation heatmap
rows=["M","M−cosign","M−align","M−prov","M−U"]
cc=["F1","F2","F3","F4","F5","F6","F7","F8","F9"]
data=np.array([[0]*9,[0,0,0,0,0,0,0,0,20],[20,20,20,0,0,0,20,13,0],[0,0,0,0,20,0,0,0,0],[0,0,0,0,0,20,0,0,0]])
fig,ax=plt.subplots(figsize=(8,3.3))
im=ax.imshow(data,cmap="Reds",vmin=0,vmax=20,aspect="auto")
ax.set_xticks(range(9)); ax.set_xticklabels(cc); ax.set_yticks(range(5)); ax.set_yticklabels(rows)
for i in range(5):
    for j in range(9): ax.text(j,i,f"{data[i,j]}/20",ha="center",va="center",fontsize=8,color="white" if data[i,j]>10 else "#222")
ax.set_title("消融：各类别漏检数（首个种子 20261007）",fontsize=11)
fig.colorbar(im,ax=ax,fraction=0.03); fig.tight_layout(); fig.savefig(f"{OUT}/fig7-2_ablation.png",dpi=200); plt.close(fig)

# Fig 7-3 tamper
T=["T1","T2","T3","T4","T5\n无锚点","T5\n外部锚点","T6","T7"]
Bd=[0,20,20,20,0,np.nan,0,0]; Md=[20,20,20,20,0,20,20,0]
x=np.arange(len(T)); w=0.36
fig,ax=plt.subplots(figsize=(9,3.6))
ax.bar(x-w/2,[0 if np.isnan(v) else v for v in Bd],w,label="B 序号日志",color="#7a8ca8")
ax.bar(x+w/2,Md,w,label="M FNV-1a32 链",color="#2e7d32")
ax.text(x[5]-w/2,0.6,"—",ha="center")
ax.set_xticks(x); ax.set_xticklabels(T,fontsize=9); ax.set_ylabel("检出数（/20）"); ax.set_ylim(0,23)
ax.legend(fontsize=9); ax.grid(axis="y",alpha=0.3)
ax.set_title("证据篡改轨道检出（T5 无锚点与 T7 在 M 上不检出为预先声明的 U）",fontsize=10.5)
fig.tight_layout(); fig.savefig(f"{OUT}/fig7-3_tamper.png",dpi=200); plt.close(fig)
print("ok")
