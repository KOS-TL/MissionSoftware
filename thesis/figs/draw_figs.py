# 毕业设计文档配图（拟定计划/示意，非实验结果；图 3 的计数来自示意性原型种子 1，主机模拟口径）
import json, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
for p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc","/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    if os.path.exists(p): fm.fontManager.addfont(p)
plt.rcParams["font.family"]=["Noto Sans CJK SC","DejaVu Sans"]
OUT=os.path.dirname(os.path.abspath(__file__)); DPI=160
BLUE=("#eef4fb","#2b4c7e"); GREEN=("#eaf5ec","#2e7d32"); ORANGE=("#fff6e8","#c9852a"); RED=("#fdecec","#b33a3a"); GRAY=("#f4f4f4","#888888"); PURPLE=("#f3eefb","#5b3f8c")

# ---------- 图 1：甘特图 ----------
WPS=[("WP0 环境与 S0/S1 复现",1,2,"Must",5),("WP1 阅读与盲推导记录",1,3,"Must",5),("WP2 托付记录 schema 与映射",3,5,"Must",6),
     ("WP3 单点违反生成器与自检",5,8,"Must",10),("WP4 接入门闩（hostsim→QEMU）",8,10,"Must",6),("WP5 对照评测 B/M 与统计",10,11,"Must",6),
     ("WP5′ B+ 与消融",11,11,"Should",2),("WP6 变异检查",11,12,"Should",5),("WP7 类别对照表",12,12,"Should",2),
     ("May 可选项（Windows 全矩阵 / 第二托付表）",10,13,"May",7),("WP8 论文撰写",12,15,"Must",12),("WP9 答辩准备",16,16,"Must",3)]
col={"Must":"#2b4c7e","Should":"#c9852a","May":"#9a9a9a"}
fig,ax=plt.subplots(figsize=(12.5,5.6)); fig.subplots_adjust(0.26,0.10,0.98,0.82)
for k,(n,a,b,lv,pd) in enumerate(WPS):
    y=len(WPS)-k
    ax.barh(y,b-a+1,left=a-0.5,height=0.58,color=col[lv],alpha=0.88 if lv!="May" else 0.55,hatch="//" if lv=="May" else None,edgecolor="white")
    ax.text(b+0.6,y,"%s · %d 人日"%(lv,pd),va="center",fontsize=8.5,color="#333")
ax.set_yticks(range(len(WPS),0,-1)); ax.set_yticklabels([w[0] for w in WPS],fontsize=9.5)
ax.set_xticks(range(1,17)); ax.set_xticklabels(["第%d周"%i for i in range(1,17)],fontsize=8)
ax.set_xlim(0.4,18.6); ax.grid(axis="x",ls=":",alpha=0.5)
for wk,lab in ((2,"检查点①\nS0/S1 复现"),(8,"检查点②\n中期检查"),(11,"检查点③\n评测冻结"),(15,"检查点④\n论文定稿")):
    ax.axvline(wk+0.5,color="#b33a3a",ls="--",lw=1); ax.text(wk+0.5,len(WPS)+0.95,lab,ha="center",va="bottom",fontsize=8,color="#b33a3a")
ax.set_title("图 1 十六周计划甘特图（拟定；Must 合计 53、Should 9、May 7 人日）",fontsize=11.5,pad=34)
fig.savefig(f"{OUT}/gp-fig1-gantt-v2.png",dpi=DPI); plt.close(fig)

# ---------- 图 2：工具链架构 ----------
fig,ax=plt.subplots(figsize=(13.2,6.6)); ax.set_xlim(0,132); ax.set_ylim(0,66); ax.axis("off"); fig.subplots_adjust(0.01,0.01,0.99,0.99)
def rbox(x,y,w,h,c,lw=1.4,ls="-"):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=0.6",fc=c[0],ec=c[1],lw=lw,ls=ls,zorder=2))
def txt(x,y,s,fs=9,bold=False,c="#1d1d1d"):
    ax.text(x,y,s,fontsize=fs,fontweight="bold" if bold else "normal",color=c,ha="center",va="center",zorder=5,linespacing=1.35)
def arr(x1,y1,x2,y2,c="#333",ls="-"):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=12,lw=1.3,color=c,ls=ls,zorder=3))
txt(66,63.5,"图 2 学生工具链与既有实验装置的接口（拟定；虚线框 = 学生新增，实线框 = 只读复用的既有组件）",fs=11.5,bold=True,c="#2b4c7e")
rbox(2,40,22,16,PURPLE,ls="--"); txt(13,48,"托付记录 v0（拟定）\nentrustor / trustee / purpose\nvalidity / scope / version\naccountability / evidence",9)
rbox(30,40,22,16,PURPLE,ls="--"); txt(41,48,"schema 校验与降维映射\n（er_schema）\n→ entrustments.json 字段",9)
rbox(58,40,24,16,PURPLE,ls="--"); txt(70,48,"单点违反生成器（spv_gen）\n名义请求 + 只改一个要素\n+ 边界合法对照；种子确定",9)
rbox(88,40,20,16,BLUE); txt(98,48,"参考判定器\noracle.evaluate_case\n（只读导入，给真值）",9)
rbox(112,40,18,16,BLUE); txt(121,48,"corpus_c\ncanonical JSON\n+ C 头文件",9)
for a,b in ((24,30),(52,58),(82,88),(108,112)): arr(a+0.2,48,b-0.2,48)
rbox(2,14,28,18,BLUE); txt(16,23,"entrustments.json\n→ gen/entrustments_gen.h\n（门闩持有的托付表；\nMust 级不改动）",9)
rbox(36,14,30,18,BLUE); txt(51,23,"gatekeeper_field.c\nB / B+ / M / M−消融\n+ 变异体（仅临时副本）",9)
rbox(72,14,26,18,GREEN); txt(85,23,"运行载体\nhostsim（主机模拟）\n或 学生分支 QEMU\n（CORPUS_SET=student）",9)
rbox(104,14,26,18,BLUE); txt(117,23,"parse_serial parse/score\nstats_exact\n（Wilson / McNemar）",9)
arr(121,40,58,32.2); arr(30.2,23,35.8,23); arr(66.2,23,71.8,23); arr(98.2,23,103.8,23)
arr(13,40,13,32.2,c="#5b3f8c",ls="--"); txt(20.5,36,"字段须一致",8,c="#5b3f8c")
rbox(2,2,128,8,GRAY); txt(66,6,"输出：语料 JSON/头文件（含 SHA-256）· 日志 · 计分 CSV · 统计表 · 变异杀死表 —— 一律标注「环境自测，非确证性」；学生语料不并入作者语料或留出语料 H",9.5)
fig.savefig(f"{OUT}/gp-fig2-toolchain.png",dpi=DPI); plt.close(fig)

# ---------- 图 3：单点违反矩阵（原型种子 1 的实际计数） ----------
J=json.load(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "prototype", "out", "spv_1.json")))  # v0.1.0: repo-relative
rules=[]; seen=set()
order_el=["time","scope","accountability","version","evidence","legal"]
for el in order_el:
    for c in sorted(J["cases"],key=lambda c:c["rule"]):
        if c["element"]==el and c["rule"] not in seen: seen.add(c["rule"]); rules.append((el,c["rule"]))
clauses=["S-R1","S-C1","S-C2","S-T1","S-T2","S-Z1","S-S1","S-S2","S-S3","S-V1","S-P1","S-U1","S-U2","(无)"]
M=[[0]*len(clauses) for _ in rules]; N=[0]*len(rules)
for c in J["cases"]:
    i=rules.index((c["element"],c["rule"])); N[i]+=1
    cl=c["oracle_all_clauses"] or ["(无)"]
    for x in cl: M[i][clauses.index(x)]+=1
fig,ax=plt.subplots(figsize=(12.5,7.4)); fig.subplots_adjust(0.30,0.08,0.97,0.90)
import numpy as np
A=np.array([[M[i][j]/N[i] for j in range(len(clauses))] for i in range(len(rules))])
ax.imshow(A,cmap="Blues",vmin=0,vmax=1.4,aspect="auto")
EL={"time":"时间","scope":"范围","accountability":"问责","version":"版本","evidence":"证据","legal":"名义合法"}
ax.set_yticks(range(len(rules))); ax.set_yticklabels(["%s｜%s（n=%d）"%(EL[e],r,N[k]) for k,(e,r) in enumerate(rules)],fontsize=8.5)
ax.set_xticks(range(len(clauses))); ax.set_xticklabels(clauses,fontsize=8.5)
for i in range(len(rules)):
    for j in range(len(clauses)):
        if M[i][j]: ax.text(j,i,str(M[i][j]),ha="center",va="center",fontsize=7.5,color="#0b2545" if A[i,j]<0.8 else "white")
    nimp=sum(1 for c in J["cases"] if (c["element"],c["rule"])==rules[i] and not c["single_point_pure"])
    if nimp: ax.text(len(clauses)-0.45,i,"  非单点 %d"%nimp,va="center",fontsize=7.5,color="#b33a3a")
ax.set_xlim(-0.5,len(clauses)+0.9)
ax.set_title("图 3 单点违反规则 × 参考判定器违反条款（示意性原型，种子 1，210 例；格内为该条款被违反的用例数）",fontsize=10.5,pad=10)
ax.set_xlabel("rules_spec.md §4 条款（按 oracle 实际判定；一例可违反多条）",fontsize=9)
fig.savefig(f"{OUT}/gp-fig3-spv-matrix.png",dpi=DPI); plt.close(fig)
print("ok")
