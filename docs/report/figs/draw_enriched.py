# Enriched figures for the integrated report. All experiment numbers from
# microkit-mission-shell/experiment/reports/box-qemu/report.md (setup check).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np, os, math
for p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc","/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    if os.path.exists(p): fm.fontManager.addfont(p)
plt.rcParams["font.family"]=["Noto Sans CJK SC","DejaVu Sans"]
plt.rcParams["axes.unicode_minus"]=False
OUT=os.path.dirname(os.path.abspath(__file__)); DPI=160
BLUE=("#eef4fb","#2b4c7e"); GREEN=("#eaf5ec","#2e7d32"); ORANGE=("#fff6e8","#c9852a"); RED=("#fdecec","#b33a3a"); GRAY=("#f4f4f4","#888888"); WHITE=("#ffffff","#9db4d4")
SETUP="环境自测，非确证性"

def canvas(w,h,W,H):
    fig,ax=plt.subplots(figsize=(w,h)); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis("off")
    fig.subplots_adjust(0.01,0.01,0.99,0.99); return fig,ax
def rbox(ax,x,y,w,h,col,lw=1.4,rs=0.6,z=2):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=0,rounding_size={rs}",fc=col[0],ec=col[1],lw=lw,zorder=z))
def txt(ax,x,y,s,fs=9,bold=False,c="#1d1d1d",ha="center",va="center",z=5):
    ax.text(x,y,s,fontsize=fs,fontweight="bold" if bold else "normal",color=c,ha=ha,va=va,zorder=z,linespacing=1.35)
def arr(ax,x1,y1,x2,y2,c="#333",lw=1.3,ls="-",rad=0.0,ms=13):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=ms,lw=lw,color=c,linestyle=ls,zorder=3,connectionstyle=f"arc3,rad={rad}"))
def save(fig,name):
    fig.savefig(f"{OUT}/{name}",dpi=DPI); plt.close(fig); print("wrote",name)

# ================= Fig 3-1 lifecycle overlay =================
fig,ax=canvas(13.2,8.9,132,89)
txt(ax,66,86.8,"传统软件工程生命周期（完整保留）× 使命叠加（逐阶段可机检）",fs=12,bold=True,c="#2b4c7e")
stages=[("需求","01-SRS",["R1 明示托付 R1.1–R1.7","R2 假使命 R2.1–R2.4","R3 弱成功 ALLOW_SIM","R4 证据链 R4.1–R4.5","R5 负面需求 R5.1–R5.4","R6 剖面 · R7 PD 结构","NFR1–NFR5"]),
        ("设计","02-SDD",["D1 K/A/M/U 分层","D2 共签状态机（默认 OFF）","D3 无 ACHIEVE，仅 ALLOW_SIM","D4 FNV-1a32 链 + tip","D5 DEMO_PROFILE 三档","D6 被动 PD + PPC","D7 日志即契约"]),
        ("实现","03-implementation",["gatekeeper.c","mission_proto.h","scenarios/client_*.c","mission.system","Makefile","docker_build_run.sh","实验：gatekeeper_field.c"]),
        ("测试","04-test-plan / 05-report",["S0 sel4test（仅环境门禁）","S1-B 构建 · S1-I 集成","S1-A 验收（主）· S1-R 回归","TC-FULL-01 … 07","TC-COSIGN-01","TC-FALSE-01","full：len=10 · rc=124 可接受"]),
        ("发布 / 复现","06-release · 08-config",["Docker 复现命令","跑通记录（须含 DEMO_PROFILE=full）","演示口述脚本","CI-SRC … CI-SDK 配置项","重大 / 轻微变更分类","发布检查单 · 回滚","无 profile 旧日志无效"])]
over=["谁托付、何时有效\n何谓“仍是那一件”\n何谓不得宣称达成","人审判通道不可默许\n敏感路径必经门闩\n证据可对质","默认 human_cosign_ok=0\nALLOW_SIM 必附 sim_only\n不实现写使能","假使命必须被拒\nREVOKE 后必须再拒\n通过准则改写","验收看纪律日志\ntip/len 不符即发布失败\n不“调宽”门闩蒙混"]
X0=3; BW=23.2; GAP=2.7
for i,(name,doc,items) in enumerate(stages):
    x=X0+i*(BW+GAP)
    rbox(ax,x,38,BW,41,BLUE,lw=1.6)
    txt(ax,x+BW/2,76.2,name,fs=11.5,bold=True,c="#2b4c7e"); txt(ax,x+BW/2,73.3,doc,fs=8,c="#555")
    rbox(ax,x+1.2,39.5,BW-2.4,31.5,WHITE,lw=1.0)
    for k,it in enumerate(items): txt(ax,x+BW/2,68.3-k*4.1,it,fs=8.1)
    if i<4: arr(ax,x+BW+0.1,58,x+BW+GAP-0.1,58,lw=1.6)
    rbox(ax,x,17,BW,15.5,ORANGE,lw=1.4)
    txt(ax,x+BW/2,30.3,"使命叠加",fs=9,bold=True,c="#8a5a00"); txt(ax,x+BW/2,23.6,over[i],fs=8.2)
    arr(ax,x+BW/2,32.5,x+BW/2,38,c="#c9852a",ls="--",lw=1.3)
# traceability band
rbox(ax,3,81,126,3,("#e9eef6","#8aa0bf"),lw=1,rs=0.4)
txt(ax,66,82.5,"07-traceability：Req ↔ 设计 D* ↔ 源文件/符号 ↔ 测试用例 TC-* ↔ 串口关键词（贯穿各阶段）",fs=8.4,c="#2b4c7e",bold=True)
txt(ax,66,14.2,"核心合取式：明示托付 ∧ 当前动作仍对准该托付 ∧ 检查可被证伪　　交付 ≠ 达成",fs=10.5,bold=True,c="#8a5a00")
# KAMU strip
kamu=[("K  seL4 + Microkit：仅引用",BLUE),("A  gatekeeper / client：演示代码，未形式化验证",WHITE),("M  共签 · 对准 · 证据纪律：可测、可日志",GREEN),("U  真签名 · 真硬件 · 临床 · 密码学强度：非空未覆盖",RED)]
for k,(s,c) in enumerate(kamu):
    x=3+k*31.6; rbox(ax,x,3,30.4,8,c,lw=1.2); txt(ax,x+15.2,7,s,fs=8.2,bold=(k!=1))
save(fig,"fig3-1_overlay.png")

# ================= Fig 4-2 cosign state machine (original demo gatekeeper.c) =================
fig,ax=canvas(13.2,7.6,132,76)
txt(ax,66,73.5,"人共签状态机与请求判定（原始演示门闩 gatekeeper.c，按请求标签判定）",fs=12,bold=True,c="#2b4c7e")
from matplotlib.patches import Ellipse
for (cx,lab,sub,col) in [(30,"OFF","human_cosign_ok = 0",RED),(92,"ON","human_cosign_ok = 1",GREEN)]:
    ax.add_patch(Ellipse((cx,46),26,15,fc=col[0],ec=col[1],lw=2,zorder=2)); txt(ax,cx,48,lab,fs=15,bold=True,c=col[1]); txt(ax,cx,43.5,sub,fs=8.5,c="#444")
arr(ax,4,46,16.9,46,lw=1.6); txt(ax,9.5,50.5,"init\n证据 seq=1\ngate_init",fs=7.8,c="#555")
arr(ax,40,52,82,52,rad=-0.25,lw=1.8,c="#2e7d32")
rbox(ax,46,59.5,30,8,GREEN,lw=1.1); txt(ax,61,63.5,"REQ_HUMAN_COSIGN_GRANT (20) → REP_OK\nGATE|COSIGN|GRANT (demo stand-in)\n追加证据 cosign_grant",fs=7.8)
arr(ax,82,40,40,40,rad=-0.25,lw=1.8,c="#b33a3a")
rbox(ax,46,24.5,30,8,RED,lw=1.1); txt(ax,61,28.5,"REQ_HUMAN_COSIGN_REVOKE (21) → REP_OK\nGATE|COSIGN|REVOKE\n追加证据 cosign_revoke",fs=7.8)
# self loops
for cx,col,rep in [(30,RED,"REP_COSIGN_OFF"),(92,GREEN,"REP_COSIGN_ON")]:
    arr(ax,cx-5,53.4,cx+5,53.4,rad=-1.6,lw=1.2,c=col[1],ms=10)
    txt(ax,cx,66.5,f"QUERY (22) → {rep}\nEVIDENCE_TIP (23) → tip/len\n（只读，不追加证据）",fs=7.4,c="#444")
txt(ax,30,36.5,"重复 REVOKE：仍为 OFF，仍追加证据",fs=7.4,c="#777"); txt(ax,92,36.5,"重复 GRANT：仍为 ON，仍追加证据",fs=7.4,c="#777")
# decision panels
rbox(ax,3,3,58,19,RED,lw=1.4); txt(ax,32,19.5,"OFF 时：其余任何请求（含合法、假使命、未知标签）",fs=8.6,bold=True,c="#b33a3a")
txt(ax,32,11,"→ DENY  no_human_cosign（追加证据）\n先判共签，再看标签：顺序不可颠倒\n例：full 剖面 seq=2（共签前）与 seq=10（撤销后）",fs=8.2)
rbox(ax,66,3,63,19,GREEN,lw=1.4); txt(ax,97.5,19.5,"ON 时：按请求标签分支（每次判定追加证据）",fs=8.6,bold=True,c="#2e7d32")
txt(ax,97.5,10.8,"REQ_LEGAL_ENABLE (1) → ALLOW_SIM legal_path_sim + NOTE sim_only\nREQ_EXPIRED_TRUST (2) → DENY expired_entrustment\nREQ_FORBIDDEN_ZONE (3) → DENY forbidden_zone\nREQ_ADVISOR_ENABLE (4) → DENY advisor_cannot_enable\nREQ_EMPTY_U_ACHIEVE (5) → DENY empty_U_no_achieve_tag　其他 → DENY unknown_request",fs=7.8)
save(fig,"fig4-2_cosign.png")

# ================= Fig 4-3 evidence chain (full profile) =================
fig,ax=canvas(13.2,6.9,132,69)
txt(ax,66,66.5,"DEMO_PROFILE=full 证据链：10 个事件（FNV-1a32 教学级，this = H(prev ‖ seq ‖ event)）",fs=12,bold=True,c="#2b4c7e")
ev=[("gate_init","gatekeeper init","24fd4b26",BLUE),("no_human_cosign","legal_before_cosign","dff76c7e",RED),("cosign_grant","GRANT","9efeac20",BLUE),
    ("legal_path_sim","legal_sim → ALLOW_SIM","811e41c4",GREEN),("expired_entrustment","expired_trust","0720fccb",RED),("forbidden_zone","forbidden_zone","85fe7af5",RED),
    ("advisor_cannot_enable","advisor_enable","36bc5c58",RED),("empty_U_no_achieve_tag","empty_u_achieve","402b2ffd",RED),("cosign_revoke","REVOKE","6c909283",BLUE),("no_human_cosign","legal_after_revoke","80488a97",RED)]
prev="00000000"; W=23; G=2.5
for k,(e,trig,h,col) in enumerate(ev):
    r=k//5; c=k%5; x=3+c*(W+G); y=38 if r==0 else 13
    rbox(ax,x,y,W,20,col,lw=1.5)
    txt(ax,x+W/2,y+17,f"seq = {k+1}",fs=9,bold=True,c=col[1]); txt(ax,x+W/2,y+13,e,fs=8.3,bold=True)
    txt(ax,x+W/2,y+9.6,f"触发：{trig}",fs=7.5,c="#555"); txt(ax,x+W/2,y+5.6,f"prev = {prev}",fs=7.8,c="#555"); txt(ax,x+W/2,y+2.6,f"this = {h}",fs=8.4,bold=True)
    if c<4: arr(ax,x+W+0.1,y+10,x+W+G-0.1,y+10,lw=1.4)
    prev=h
arr(ax,3+4*(W+G)+W/2,37.6,3+W/2,33.4,ls="--",c="#777",rad=0.0)
rbox(ax,3,1.5,126,8.5,ORANGE,lw=1.3)
txt(ax,66,7.6,"末端：GATE|CHAIN|tip=80488a97|len=10　·　QUERY 与 EVIDENCE_TIP 只读、不计入长度　·　非密码学强度：无密钥、非抗碰撞（U）",fs=8.4,bold=True,c="#8a5a00")
txt(ax,66,3.8,"Windows + Docker trustworthysystems/sel4:latest（2026-10-08，作者报告）：tip=80488a97 len=10，rc=124，MISSION_SHELL_DEMO_DONE；逐条哈希与沙箱 QEMU 回归日志一致",fs=7.9)
save(fig,"fig4-3_evidence_chain.png")

# ================= Fig 6-1 pipeline =================
fig,ax=canvas(13.2,8.2,132,82)
txt(ax,66,79.5,"对照实验流水线（实验分支 experiment/）　·　判决只依据请求字段 + 托付表 + 逻辑时钟",fs=12,bold=True,c="#2b4c7e")
cols=[("① 语料与托付",BLUE,["corpus/entrustments.json","→ gen/entrustments_gen.h","gen_corpus.py：5 种子","20261007 … 20261011","每种子 320 例","F1–F9×20 · L1–L5×24","M1×10 · X1×10","holdout_draft.py：47 例（草稿）"]),
      ("② 真值与冻结",ORANGE,["rules_spec.md：S-F1 … S-U2","共 18 条，固定优先级","oracle.py 只读 JSON","生成器复核真值","（5 种子重抽 0 次）","prereg.md §7 SHA-256","草稿冻结，标注人未定","git tag 未打"]),
      ("③ C 头与构建",GREEN,["corpus_c.py：仅请求字段","case_id 不含类别","gatekeeper_field.c","编译期宏：B / B+ / M","ABLATE=cosign|align|prov|U","client_corpus.c（各条件相同）","构建前哈希校验","不一致即退出"]),
      ("④ 运行",BLUE,["run_matrix.sh","box 真实 QEMU：42 份语料日志","+ 1 份 full 回归日志","B、M：5 种子 × 3 次","B+ 与 4 消融：首种子 × 1","草稿留出：B、M × 3，B+ × 1","hostsim：18 组（主机模拟）","Windows Docker：待复现"]),
      ("⑤ 解析与校验",GREEN,["parse_serial.py","parse / score","verify-chain（M）","verify-seq（B / B+）","determinism：12/12 一致","INVALID = 0（退出码 2）","链/序号失败 = 0（退出码 3）","hostsim 与 QEMU 逐字节一致"]),
      ("⑥ 统计与报告",BLUE,["analyze.py · stats_exact.py","精确 McNemar · Holm","Wilson / Clopper–Pearson","误拒非劣效 Δ = 5pp","Fisher（篡改 T1–T4）","oracle compare：0 不一致","reports/box-qemu/report.md","falsification_checklist.md"])]
BW=19.6; G=2.2
for i,(t,col,items) in enumerate(cols):
    x=2+i*(BW+G); rbox(ax,x,22,BW,52,col,lw=1.6); txt(ax,x+BW/2,71,t,fs=10,bold=True,c=col[1])
    rbox(ax,x+1,23.5,BW-2,44.5,WHITE,lw=0.9)
    for k,it in enumerate(items): txt(ax,x+BW/2,64.5-k*5.2,it,fs=7.5)
    if i<5: arr(ax,x+BW+0.1,48,x+BW+G-0.1,48,lw=1.6)
rbox(ax,68,3,62,15,RED,lw=1.4); txt(ax,99,15.2,"篡改轨道 T1–T7（离线，对日志副本；每种 20 个随机位置）",fs=8.8,bold=True,c="#b33a3a")
txt(ax,99,9,"tamper.py / run_tamper.py → verify-chain / verify-seq\nexpectations.json 预先声明：T5 无锚点、T7 在 M 上预期不检出（U）",fs=8)
arr(ax,2+4*(BW+G)+BW/2,22,90,18.1,c="#b33a3a",ls="--")
rbox(ax,2,3,62,15,ORANGE,lw=1.4); txt(ax,33,15.2,"回归与确定性门禁",fs=8.8,bold=True,c="#8a5a00")
txt(ax,33,8.6,"原 full / cosign_only / false_only：ELF 与 loader.img 逐字节不变\nfull 回归：GATE|CHAIN|tip=80488a97|len=10 · DEMO_DONE\n偏离只能写入 deviations.md（当前为空）",fs=7.9)
txt(ax,66,0.9,SETUP,fs=8,c="#b33a3a",bold=True)
save(fig,"fig6-2_pipeline.png")

# ================= Fig 6-2 field gatekeeper decision flow =================
fig,ax=canvas(13.2,10.0,132,100)
txt(ax,66,97.5,"按字段判决门闩 gatekeeper_field.c：decide() 检查顺序（首个失败即拒绝）",fs=12,bold=True,c="#2b4c7e")
rbox(ax,4,86.5,60,6.5,GRAY,lw=1.1); txt(ax,34,89.7,"handle_eval：读取 9 个字段；先判 nonce 是否已在历史；\n未重复且非 0 则记入历史（无论本请求结果）",fs=7.8)
arr(ax,34,86.4,34,84.6,lw=1.1,ms=9)
steps=[("B-1 枚举 action/role/origin","invalid_enum",BLUE,""),("B-2 取值范围 zone/level/nonce/u_decl/ver","invalid_range",BLUE,""),("B-3 工单存在（不查版本/时间/范围）","unknown_ticket",BLUE,""),
       ("B-4 角色 ACL：使能类须 OPERATOR","role_forbidden",BLUE,""),("B-5 nonce 去重","duplicate_nonce",BLUE,""),
       ("B+ 全局运行窗 [50, 2000]","global_window_violation",ORANGE,"仅 B+"),("B+ 站点禁区 {7, 15}","global_forbidden_zone",ORANGE,"仅 B+"),
       ("M-1 共签集合非空","no_human_cosign",GREEN,"ABLATE_COSIGN 去掉"),("M-1 共签绑定 (ent_id, ver)","cosign_binding_mismatch",GREEN,"ABLATE_COSIGN 去掉"),
       ("版本存在 (ent_id, ver)","unknown_entrustment_version",GREEN,"ABLATE_ALIGN 去掉"),("M-2 时间 now > t_end / now < t_start","expired_entrustment / entrustment_not_yet_valid",GREEN,"ABLATE_ALIGN 去掉"),
       ("M-3 禁区（优先于 allowed）","forbidden_zone",GREEN,"ABLATE_ALIGN 去掉"),("M-4 范围：区 / 强度 / 动作","scope_drift_zone / _level / _action",GREEN,"ABLATE_ALIGN 去掉"),
       ("M-5 版本未被取代","stale_entrustment_version",GREEN,"ABLATE_ALIGN 去掉"),("M-6 使能类来源须 OPERATOR","advisor_cannot_enable",GREEN,"ABLATE_PROV 去掉"),
       ("M-7 CLAIM_ACHIEVE 一律拒；ENABLE_SIM 须 U≠0","empty_U_no_achieve_tag / achievement_not_claimable",GREEN,"ABLATE_U 去掉")]
y=84.5; H=3.9; S=0.75
for k,(chk,why,col,tag) in enumerate(steps):
    yy=y-k*(H+S)
    rbox(ax,4,yy-H,60,H,col,lw=1.2,rs=0.4); txt(ax,6,yy-H/2,chk,fs=8,ha="left")
    if tag: txt(ax,62.5,yy-H/2,tag,fs=6.9,c="#777",ha="right")
    arr(ax,64.2,yy-H/2,74.8,yy-H/2,c="#b33a3a",lw=1.1,ms=10)
    rbox(ax,75,yy-H,53,H,RED,lw=1.0,rs=0.4); txt(ax,77,yy-H/2,"DENY  "+why,fs=7.8,ha="left",c="#7a1f1f")
    if k<len(steps)-1: arr(ax,34,yy-H-0.05,34,yy-H-S+0.05,lw=1.0,ms=8)
yl=y-len(steps)*(H+S)
arr(ax,34,yl+S,34,yl-0.6,lw=1.2)
rbox(ax,4,yl-7.5,28,6.4,BLUE,lw=1.3); txt(ax,18,yl-4.3,"B / B+：ALLOW（REP_ALLOW=16）\n普通序号审计 AUDIT|seq=",fs=7.8)
rbox(ax,36,yl-7.5,28,6.4,GREEN,lw=1.3); txt(ax,50,yl-4.3,"M：ALLOW_SIM + NOTE\nsim_only; delivery!=achievement",fs=7.8)
rbox(ax,75,yl-7.5,53,6.4,ORANGE,lw=1.2); txt(ax,101.5,yl-4.3,"每次判决写 CASE|id|kind|verdict|reason；M 另追加 FNV-1a32 证据\nMR_CASE_ID 只在 log_verdict() 中读取，不参与判决",fs=7.6)
save(fig,"fig6-1_field_decision.png")

# ================= Fig 7-1 FNR + FPR with Wilson CI =================
def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return max(0,c-h),min(1,c+h)
cats=["F1","F2","F3","F4","F5","F6","F7","F8","F9","M1","X1"]
Bk=[100,100,100,0,100,100,100,100,100,0,0]; Bn=[100]*9+[50,50]
Pk=[12,12,4,0,20,20,20,20,20,0,0]; Pn=[20]*9+[10,10]
Mk=[0]*11; Mn=[100]*9+[50,50]
fig=plt.figure(figsize=(13.2,8.0)); gs=fig.add_gridspec(2,1,height_ratios=[2.2,1],hspace=0.55)
ax=fig.add_subplot(gs[0]); x=np.arange(11); w=0.27
for off,k,n,lab,col in [(-w,Bk,Bn,"B 公平基线（5 种子合并）","#5b7bb0"),(0,Pk,Pn,"B+ 领域规则强化（首种子）","#d9a441"),(w,Mk,Mn,"M 使命流程（5 种子合并）","#2e7d32")]:
    r=[a/b*100 for a,b in zip(k,n)]; lo=[wilson(a,b)[0]*100 for a,b in zip(k,n)]; hi=[wilson(a,b)[1]*100 for a,b in zip(k,n)]
    ax.bar(x+off,r,w,color=col,label=lab,edgecolor="white",zorder=2)
    ax.errorbar(x+off,r,yerr=[np.maximum(0,np.array(r)-np.array(lo)),np.maximum(0,np.array(hi)-np.array(r))],fmt="none",ecolor="#333",capsize=2.5,lw=0.9,zorder=3)
    ax.scatter([xx+off for xx,rr in zip(x,r) if rr==0],[0.8]*sum(1 for rr in r if rr==0),marker="s",s=14,color=col,zorder=4)
    for xi,(a,b,rr,hh) in enumerate(zip(k,n,r,hi)): ax.text(xi+off,hh+2,f"{a}/{b}",ha="center",va="bottom",fontsize=6.4,rotation=90,color="#333")
ax.axvspan(-0.5,2.5,color="#e9eef6",zorder=0); ax.axvspan(3.5,8.5,color="#e9eef6",zorder=0)
ax.set_xticks(x); ax.set_xticklabels(cats); ax.set_ylim(0,135); ax.set_yticks([0,20,40,60,80,100]); ax.set_ylabel("漏检率 FNR（%）")
ax.grid(axis="y",alpha=0.3,zorder=1); ax.legend(fontsize=8.5,loc="upper center",bbox_to_anchor=(0.5,-0.09),ncol=3,frameon=False)
ax.set_title(f"(a) 应拒用例漏检（误差线：Wilson 95% 区间；阴影 = 仅使命可拦类别）　·　{SETUP}",fontsize=10.5)
ax.text(10.45,128,"合计：B 800/1000 = 80.0%　B+ 128/200 = 64.0%　M 0/1000 = 0.0%",ha="right",fontsize=8.5,color="#2b4c7e",fontweight="bold")
ax2=fig.add_subplot(gs[1]); L=["L1","L2","L3","L4","L5"]; x=np.arange(5)
for off,n,lab,col in [(-w,120,"B（5 种子，每类 n=120）","#5b7bb0"),(0,24,"B+（首种子，每类 n=24）","#d9a441"),(w,120,"M（5 种子，每类 n=120）","#2e7d32")]:
    hi=wilson(0,n)[1]*100
    ax2.bar(x+off,[0.25]*5,w,color=col,label=lab,zorder=2); ax2.scatter(x+off,[0.25]*5,marker="s",s=14,color=col,zorder=4)
    ax2.errorbar(x+off,[0]*5,yerr=[[0]*5,[hi]*5],fmt="none",ecolor=col,capsize=3,lw=1.2,zorder=3)
    for xi in x: ax2.text(xi+off,hi+0.6,f"0/{n}",ha="center",fontsize=7,color="#333")
ax2.set_xticks(x); ax2.set_xticklabels(L); ax2.set_ylim(0,19); ax2.set_ylabel("误拒率 FPR（%）"); ax2.axhline(5,ls="--",color="#b33a3a",lw=1)
ax2.text(4.55,5.4,"Δ = 5pp（非劣效界值）",ha="right",fontsize=7.8,color="#b33a3a")
ax2.grid(axis="y",alpha=0.3,zorder=1); ax2.legend(fontsize=8,loc="upper left",ncol=3,frameon=False)
ax2.set_title("(b) 合法用例误拒：全部为 0；线段为 Wilson 95% 上界　·　M 合并 0/600，保守上界 0.6%",fontsize=10)
fig.subplots_adjust(left=0.07,right=0.98,top=0.95,bottom=0.06); save(fig,"fig7-1_fnr.png")

# ================= Fig 7-2 ablation heatmap =================
rows=["B（5 种子）","B+（首种子）","M（5 种子）","M−cosign","M−align","M−prov","M−U"]
cc=["F1","F2","F3","F4","F5","F6","F7","F8","F9","M1","X1"]
K=[[100,100,100,0,100,100,100,100,100,0,0],[12,12,4,0,20,20,20,20,20,0,0],[0]*11,[0,0,0,0,0,0,0,0,20,0,0],[20,20,20,0,0,0,20,13,0,0,0],[0,0,0,0,20,0,0,0,0,0,0],[0,0,0,0,0,20,0,0,0,0,0]]
N=[[100]*9+[50,50],[20]*9+[10,10],[100]*9+[50,50]]+[[20]*9+[10,10]]*4
tot=["800/1000\n80.0%","128/200\n64.0%","0/1000\n0.0%","20/200\n10.0%","93/200\n46.5%","20/200\n10.0%","20/200\n10.0%"]
pred={3:[8],4:[0,1,2,6,7],5:[4],6:[5]}
R=np.array([[k/n*100 for k,n in zip(a,b)] for a,b in zip(K,N)])
fig,ax=plt.subplots(figsize=(13.2,6.6)); fig.subplots_adjust(left=0.11,right=0.86,top=0.86,bottom=0.17)
im=ax.imshow(R,cmap="Reds",vmin=0,vmax=100,aspect="auto")
ax.set_xticks(range(11)); ax.set_xticklabels(cc); ax.set_yticks(range(7)); ax.set_yticklabels(rows)
for i in range(7):
    for j in range(11):
        v=R[i,j]; ax.text(j,i,f"{K[i][j]}/{N[i][j]}",ha="center",va="center",fontsize=8,color="white" if v>55 else "#222")
for i,js in pred.items():
    for j in js: ax.add_patch(Rectangle((j-0.5,i-0.5),1,1,fill=False,ec="#2b4c7e",lw=2.2))
ax.axhline(2.5,color="#2b4c7e",lw=1.5); ax.axhline(1.5,color="#999",lw=0.8)
for i,t in enumerate(tot): ax.text(11.0,i,t,ha="left",va="center",fontsize=8,color="#2b4c7e",fontweight="bold")
ax.text(11.0,6.95,"全部应拒漏检",ha="left",va="top",fontsize=8,fontweight="bold")
cb=fig.colorbar(im,ax=ax,fraction=0.025,pad=0.11); cb.set_label("漏检率（%）")
ax.set_title(f"各变体 × 类别漏检（蓝框 = 消融预注册的预测上升类别；L1–L5 误拒全部为 0）　·　{SETUP}",fontsize=10.5)
fig.text(0.11,0.05,"F8 在 M−align 下 13/20 漏检：其余 7 例被 M-1 cosign_binding_mismatch 拦截（共签绑定与版本对准重叠）。消融预测全部出现，其他类别无变化。",fontsize=8.5,color="#8a5a00")
save(fig,"fig7-2_ablation.png")

# ================= Fig 7-3 tamper matrix =================
fig,ax=canvas(13.2,7.6,132,76)
txt(ax,66,73.5,f"证据篡改轨道 T1–T7：检出矩阵（每格 20 个随机位置变体）　·　{SETUP}",fs=12,bold=True,c="#2b4c7e")
T=[("T1","改事件文本，不动序号/哈希","朴素","0/20","20/20","—"),("T2","删中间一条，不重编号","朴素","20/20","20/20","—"),("T3","交换相邻两条","朴素","20/20","20/20","—"),
   ("T4","插入伪造行（B 序号=前+1，不重编号）","朴素","20/20","20/20","—"),("T5","截尾最后 k 条（k∈[1,5]）","朴素","0/20","0/20","20/20"),
   ("T6","删一条并重编号、更新长度","知情","0/20","20/20","—"),("T7","改一条后重算整条 FNV 链","知情·无密钥","0/20","0/20","—")]
hx=[3,12,52,66,88,110]; hw=[9,40,14,22,22,20]
heads=["篡改","变换","攻击者","B 序号日志","M FNV 链（无锚点）","M + 外部锚点"]
for x,w_,h in zip(hx,hw,heads): rbox(ax,x,63.5,w_-0.6,6,BLUE,lw=1.1,rs=0.4); txt(ax,x+(w_-0.6)/2,66.5,h,fs=8.6,bold=True,c="#2b4c7e")
U={("T5",4),("T7",4)}
for r,row in enumerate(T):
    y=56-r*6.95
    for c,(x,w_) in enumerate(zip(hx,hw)):
        v=row[c]
        if c<3: col=WHITE
        elif v=="—": col=GRAY
        elif v.startswith("20"): col=GREEN
        else: col=RED
        rbox(ax,x,y,w_-0.6,6.1,col,lw=1.0,rs=0.4)
        lab=v if c<3 else ("未单独报告" if v=="—" else (v+"  检出" if v.startswith("20") else v+"  未检出"))
        txt(ax,x+(w_-0.6)/2,y+3.2,lab,fs=8.2 if c!=1 else 7.6,bold=(c>=3 and v!="—"),c="#1d1d1d" if v!="—" else "#888")
        if (row[0],c) in U:
            ax.add_patch(Rectangle((x+0.3,y+0.3),w_-1.2,5.8,fill=False,hatch="///",ec="#b33a3a",lw=0,zorder=4))
            txt(ax,x+w_-2.2,y+3.2,"U",fs=9,bold=True,c="#b33a3a",ha="right")
rbox(ax,3,1.5,126,9,ORANGE,lw=1.3)
txt(ax,66,7.6,"全部 7 行观察结果与 tamper/expectations.json 预注册预期一致　·　T1–T4 合并：M 80/80 vs B 60/80，Fisher 单侧 p = 2.46×10⁻⁷（X-5 未触发）",fs=8.4,bold=True,c="#8a5a00")
txt(ax,66,3.9,"斜线 U = 预先声明的预期失败：FNV-1a32 无密钥、非抗碰撞，无外部锚点不能防截尾；不是待修复缺陷。T4 对 B 的检出依赖“不重编号”的攻击者模型（待复核）",fs=7.9)
save(fig,"fig7-3_tamper.png")

# ================= Fig 7-4 falsification status =================
fig,ax=canvas(13.2,6.6,132,66)
txt(ax,66,63.5,f"可证伪条件 X-1 … X-7 的当前状态　·　{SETUP}",fs=12,bold=True,c="#2b4c7e")
X=[("X-1","留出语料 H 上 McNemar 不显著或 FNR_M(H) ≥ 30%","未判定","尚无独立标注人编写的 H（草稿 47 例仅演示，不计入）",None),
   ("X-2","误拒差保守上界 ≥ 5pp 或 L2 子型 FPR ≥ 50%","未触发","合并上界 0.6%（门槛 5pp）",(0.6,5,"%")),
   ("X-3","B+ 覆盖 M 所拦 F1–F9 用例 ≥ 80%","未触发","52/180 = 28.9%（门槛 80%）",(28.9,80,"%")),
   ("X-4","任一应拒类别 c > 0（B 拦而 M 放）","未触发","c 合计 = 0",None),
   ("X-5","T1–T4 链检出不高于序号日志（Fisher p ≥ 0.05）","未触发","Fisher 单侧 p = 2.46×10⁻⁷",None),
   ("X-6","人工研究 M 的 F1 中位数不高于 B 且更慢","未判定","人工审查研究推迟，未实施",None),
   ("X-7","M/B LOC 比 > 3 且 X-1 成立","未触发","403/247 = 1.63（门槛 3.0；X-1 未判定）",(1.63,3.0,"×"))]
for r,(k,cond,st,ev,g) in enumerate(X):
    y=54-r*7.4
    col=GREEN if st=="未触发" else ORANGE
    rbox(ax,3,y,8,6.2,BLUE,lw=1.1,rs=0.4); txt(ax,7,y+3.1,k,fs=9.5,bold=True,c="#2b4c7e")
    rbox(ax,12,y,46,6.2,WHITE,lw=0.9,rs=0.4); txt(ax,14,y+3.1,cond,fs=7.9,ha="left")
    rbox(ax,59,y,12,6.2,col,lw=1.3,rs=0.4); txt(ax,65,y+3.1,st,fs=9,bold=True,c=col[1])
    rbox(ax,72,y,57,6.2,WHITE,lw=0.9,rs=0.4); txt(ax,74,y+4.2 if g else y+3.1,ev,fs=7.8,ha="left")
    if g:
        v,t,u=g; x0=74; L_=40; mx=t*1.25
        ax.add_patch(Rectangle((x0,y+0.9),L_,1.4,fc="#eeeeee",ec="none",zorder=4))
        ax.add_patch(Rectangle((x0,y+0.9),L_*v/mx,1.4,fc="#2e7d32",ec="none",zorder=5))
        ax.plot([x0+L_*t/mx]*2,[y+0.5,y+2.7],color="#b33a3a",lw=1.6,zorder=6)
        txt(ax,x0+L_+1,y+1.6,f"门槛 {t}{u}",fs=7,c="#b33a3a",ha="left")
txt(ax,66,1.8,"“未触发”仅在装置自检口径下成立（作者语料 + 草稿真值）；承担验证性负荷的 X-1、X-6 均未判定",fs=8.4,bold=True,c="#8a5a00")
save(fig,"fig7-4_falsification.png")
