#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze.py —— 从运行目录生成实验报告（Markdown + CSV）。

输入布局（run_matrix.sh 的输出）：<runs-dir>/<condition>/<corpus>/r<k>.log ，corpus = 种子号或 holdout_draft；
可选 <runs-dir>/legacy_full/r1.log（full 剖面回归）。
输出：<out-dir>/report.md、rates.csv、paired.csv、noninferiority.csv、tamper.csv、falsification_checklist.md、
      oracle_vs_M.md、results/<cond>_<corpus>.csv、confusion/<cond>_<corpus>.csv

统计口径（实验方案 §6）：
  - 漏检率 FNR = P(PERMIT | MUST_DENY)；误拒率 FPR = P(DENY | MAY_PERMIT)；INVALID 单列、不计为 DENY。
  - 比例区间：Wilson 95% 与 Clopper–Pearson 95%（精确）同时给出。
  - 配对比较：精确 McNemar（不一致对 b、c 上的 Binomial(0.5)）；逐类别 Holm 校正。
  - 误拒非劣效：配对差 FPR_M − FPR_B = (b − c)/n ≤ b/n，取 b/n 的 Clopper–Pearson 双侧 95% 上界
    作为差值的保守精确上界；上界 < Δ 则非劣效成立。
  - 阈值从 prereg.md 的 PREREG-THRESHOLDS 块读取（冻结值）。

用法：analyze.py --runs-dir DIR --out-dir DIR --env-label "运行环境说明" [--corpus-dir corpus/out] [--prereg prereg.md]
"""
import argparse
import csv
import glob
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import stats_exact as st  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ps = _load("parse_serial", os.path.join(HERE, "parse_serial.py"))
tm = _load("tamper_mod", os.path.join(EXP, "tamper", "tamper.py"))
loc = _load("loc_count", os.path.join(HERE, "loc_count.py"))

F_CATS = ["F%d" % i for i in range(1, 10)]
L_CATS = ["L%d" % i for i in range(1, 6)]
D_CATS = F_CATS + ["M1", "X1"]
MISSION_ONLY = ["F1", "F2", "F3", "F5", "F6", "F7", "F8", "F9"]
ABLATION_PRED = {"M-cosign": ["F9"], "M-align": ["F1", "F2", "F3", "F7", "F8"], "M-prov": ["F5"], "M-U": ["F6"]}
COND_ORDER = ["B", "Bplus", "M", "M-cosign", "M-align", "M-prov", "M-U"]


def read_prereg(path):
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"# PREREG-THRESHOLDS v1 \(frozen\)\n(.*?)```", txt, re.S)
    if not m:
        raise SystemExit("prereg.md 中未找到 PREREG-THRESHOLDS 块")
    d = {}
    for line in m.group(1).strip().splitlines():
        k, v = [x.strip() for x in line.split(":", 1)]
        d[k] = v
    return {
        "delta": float(d["delta_fpr_pp"]) / 100.0,
        "h_fnr_ceiling": float(d["holdout_fnr_ceiling"]),
        "bplus_ceiling": float(d["bplus_capture_ceiling"]),
        "kappa_min": float(d["kappa_min"]),
        "h_min_deny": int(d["holdout_min_must_deny"]),
        "h_min_permit": int(d["holdout_min_may_permit"]),
        "alpha1": float(d["alpha_primary_one_sided"]),
        "alpha2": float(d["alpha_secondary_two_sided"]),
        "loc_ratio": float(d["loc_ratio_ceiling"]),
        "l2_systematic": float(d["l2_subtype_systematic_fpr"]),
        "seeds": [int(s) for s in d["seeds"].split(",")],
    }


def pct(x):
    return "%.1f%%" % (100 * x)


def ci_str(x, n):
    w = st.wilson(x, n)
    c = st.clopper_pearson(x, n)
    return "%s [W %s–%s; CP %s–%s]" % (pct(x / n) if n else "n/a", pct(w[0]), pct(w[1]), pct(c[0]), pct(c[1]))


def pfmt(p):
    return "%.3g" % p


# ---------------------------------------------------------------- 读取运行
def load_runs(runs_dir, corpus_dir):
    runs, corpora, integrity = {}, {}, []
    for cond_dir in sorted(glob.glob(os.path.join(runs_dir, "*"))):
        cond = os.path.basename(cond_dir)
        if cond == "legacy_full" or not os.path.isdir(cond_dir):
            continue
        for corp_dir in sorted(glob.glob(os.path.join(cond_dir, "*"))):
            corp = os.path.basename(corp_dir)
            cpath = os.path.join(corpus_dir, ("corpus_%s.json" % corp) if corp.isdigit() else "%s.json" % corp)
            if corp not in corpora:
                corpora[corp] = ps.load_corpus(cpath)
            want = {c["case_id"] for c in corpora[corp]["cases"]}
            logs = sorted(glob.glob(os.path.join(corp_dir, "r[0-9]*.log")))
            parsed, case_lines = [], []
            for p in logs:
                lines = ps.read_lines(p)
                rec = {"log": os.path.relpath(p, runs_dir), "status": "ok", "detail": "", "bytes": os.path.getsize(p)}
                try:
                    cases = ps.parse_cases(lines)
                    ps.check_completeness(lines, cases)
                    c = ps.condition_from_log(lines)
                    if c != cond:
                        raise ps.InvalidRun("condition in log %s != dir %s" % (c, cond))
                    if set(cases) != want:
                        raise ps.InvalidRun("case set mismatch")
                except ps.InvalidRun as e:
                    rec.update(status="INVALID", detail=str(e))
                    cases = None
                if cond.startswith("M"):
                    rep = ps.verify_chain(ps.parse_evidence(lines), None, ps.internal_anchor(lines))
                    rec["integrity"] = "chain ok len=%d tip=%08x" % (rep.length, rep.tip) if rep.ok else "chain FAIL %s" % rep.problem
                else:
                    rep = ps.verify_seq_lines(lines)
                    rec["integrity"] = "seq ok len=%d" % rep.length if rep.ok else "seq FAIL %s" % rep.problem
                rec["integrity_ok"] = rep.ok
                m = [l for l in lines if l.startswith("RUN|build_ok")]
                rec["build"] = m[0] if m else ""
                integrity.append(dict(rec, cond=cond, corpus=corp))
                parsed.append((p, lines, cases))
                case_lines.append([l for l in lines if l.startswith("CASE|")])
            det = all(cl == case_lines[0] for cl in case_lines) if case_lines else False
            valid = [x for x in parsed if x[2] is not None]
            runs[(cond, corp)] = {"cases": valid[0][2] if valid else None, "lines": valid[0][1] if valid else None,
                                  "n_reps": len(parsed), "n_valid": len(valid), "deterministic": det,
                                  "log": valid[0][0] if valid else None}
    return runs, corpora, integrity


def verdicts(run):
    return {cid: r.verdict for cid, r in run["cases"].items()} if run and run["cases"] else None


# ---------------------------------------------------------------- 指标
def cat_rates(run, corpus, cats_key="category"):
    """返回 {category: (k, n)}：对 MUST_DENY 类别 k=#PERMIT；对 MAY_PERMIT 类别 k=#DENY。"""
    v = verdicts(run)
    out = {}
    for c in corpus["cases"]:
        cat = c[cats_key]
        k, n = out.get(cat, (0, 0))
        bad = (v[c["case_id"]] == "PERMIT") if c["gt"] == "MUST_DENY" else (v[c["case_id"]] == "DENY")
        out[cat] = (k + int(bad), n + 1)
    return out


def paired(vb, vm, cases):
    a = b = c = d = 0
    for x in cases:
        B, M = vb[x["case_id"]], vm[x["case_id"]]
        if B == "DENY" and M == "DENY":
            a += 1
        elif B == "PERMIT" and M == "DENY":
            b += 1
        elif B == "DENY" and M == "PERMIT":
            c += 1
        else:
            d += 1
    return a, b, c, d


def oracle_vs(run, corpus, gt_field="gt", reason_field="oracle_reason"):
    rows, agree = [], 0
    for c in corpus["cases"]:
        r = run["cases"][c["case_id"]]
        og = c.get("oracle_gt", c["gt"]) if gt_field == "oracle_gt" else c["gt"]
        gv = "MUST_DENY" if r.verdict == "DENY" else "MAY_PERMIT"
        ok = gv == og and r.reason == c[reason_field]
        agree += ok
        if not ok:
            rows.append((c["case_id"], c.get("name", ""), c.get("category", ""), og, r.raw_verdict, c[reason_field], r.reason))
    return agree, rows


# ---------------------------------------------------------------- 主流程
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--corpus-dir", default=os.path.join(EXP, "corpus", "out"))
    ap.add_argument("--prereg", default=os.path.join(EXP, "prereg.md"))
    ap.add_argument("--env-label", required=True)
    ap.add_argument("--tamper-n", type=int, default=20)
    a = ap.parse_args(argv)
    T = read_prereg(a.prereg)
    os.makedirs(os.path.join(a.out_dir, "results"), exist_ok=True)
    os.makedirs(os.path.join(a.out_dir, "confusion"), exist_ok=True)
    runs, corpora, integrity = load_runs(a.runs_dir, a.corpus_dir)
    seeds = [s for s in T["seeds"] if ("B", str(s)) in runs and ("M", str(s)) in runs]
    first = str(seeds[0]) if seeds else None
    R = []  # 报告行
    w = R.append

    # ---- 落盘每次运行的 results / confusion
    for (cond, corp), run in runs.items():
        if not run["cases"]:
            continue
        with open(os.path.join(a.out_dir, "results", "%s_%s.csv" % (cond, corp)), "w", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            wr.writerow(["case_id", "raw_verdict", "verdict", "reason", "line_no", "condition"])
            for cid in sorted(run["cases"]):
                r = run["cases"][cid]
                wr.writerow([cid, r.raw_verdict, r.verdict, r.reason, r.line_no, cond])
        rows = ps.score(run["cases"], corpora[corp])
        with open(os.path.join(a.out_dir, "confusion", "%s_%s.csv" % (cond, corp)), "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            wr.writeheader()
            wr.writerows(rows)

    w("# 对照实验装置自检报告（setup check）")
    w("")
    w("> **运行环境：%s**" % a.env_label)
    w(">")
    w("> **性质声明**：本报告基于作者语料 A（作者同时编写规则与语料）与草稿 oracle 真值（草稿·待独立标注人复核；不计入确证性结论）。")
    w("> 按实验方案 H1′，作者语料上的\"使命层全拦截\"只用于确认实验装置工作，**不作为方法有效的证据**。")
    w("> 留出语料部分为**作者手写草稿**，仅演示流水线，不得用于判定 X-1。人工审查研究（RQ3b/E1/X-6）已推迟，未实施。")
    w("> 非临床 · 仅仿真 · 无写使能 · 不宣称 seL4 级应用证明 · 交付 ≠ 达成 · FNV-1a32 链为教学级。")
    w("")

    # ---- 1. 运行完整性
    w("## 1. 运行完整性")
    w("")
    n_inv = sum(1 for r in integrity if r["status"] != "ok")
    n_int_fail = sum(1 for r in integrity if not r["integrity_ok"])
    w("- 日志总数：%d；INVALID：%d（预注册要求为 0）；未篡改日志的链/序号校验失败：%d（期望 0）" % (len(integrity), n_inv, n_int_fail))
    nondet = [k for k, v in runs.items() if v["n_reps"] > 1 and not v["deterministic"]]
    reps = [k for k, v in runs.items() if v["n_reps"] > 1]
    w("- 确定性：%d 个（条件, 语料）组有多次重复，CASE| 行逐字节一致的组：%d/%d" % (len(reps), len(reps) - len(nondet), len(reps)))
    leg = os.path.join(a.runs_dir, "legacy_full", "r1.log")
    if os.path.exists(leg):
        ll = ps.read_lines(leg)
        ch = [l for l in ll if l.startswith("GATE|CHAIN")]
        done = any("MISSION_SHELL_DEMO_DONE" in l for l in ll)
        ok = bool(ch) and ch[-1].strip() == "GATE|CHAIN|tip=80488a97|len=10" and done
        w("- 回归门禁（原 full 剖面，同一运行环境）：`%s`，DEMO_DONE=%s → **%s**" % (ch[-1] if ch else "无 CHAIN 行", done, "通过" if ok else "未通过"))
    w("")
    if n_inv:
        w("| 日志 | 状态 | 说明 |")
        w("|---|---|---|")
        for r in integrity:
            if r["status"] != "ok":
                w("| %s | %s | %s |" % (r["log"], r["status"], r["detail"]))
        w("")

    # ---- 2. 作者语料 A：各条件 × 类别
    w("## 2. 作者语料 A：漏检率 / 误拒率（装置自检，非确证性）")
    w("")
    w("F*/M1/X1 列为漏检率 FNR（应拒却放行）；L* 列为误拒率 FPR（应放行却拒绝）。B 与 M 汇总 %d 个种子；B+ 与消融仅首个种子 %s。" % (len(seeds), first))
    w("")
    rate_rows = []
    hdr = D_CATS + L_CATS
    w("| 条件 | 种子数 | " + " | ".join(hdr) + " | 全部 MUST_DENY FNR | 全部 L FPR |")
    w("|---" * (len(hdr) + 4) + "|")
    for cond in COND_ORDER:
        corps = [str(s) for s in seeds if (cond, str(s)) in runs and runs[(cond, str(s))]["cases"]]
        if not corps:
            continue
        agg = {}
        for corp in corps:
            for cat, (k, n) in cat_rates(runs[(cond, corp)], corpora[corp]).items():
                K, N = agg.get(cat, (0, 0))
                agg[cat] = (K + k, N + n)
                rate_rows.append({"condition": cond, "corpus": corp, "category": cat, "bad": k, "n": n,
                                  "metric": "FNR" if cat in D_CATS else "FPR"})
        dk = sum(agg[c][0] for c in D_CATS if c in agg); dn = sum(agg[c][1] for c in D_CATS if c in agg)
        lk = sum(agg[c][0] for c in L_CATS if c in agg); ln = sum(agg[c][1] for c in L_CATS if c in agg)
        cells = ["%d/%d" % agg[c] if c in agg else "-" for c in hdr]
        w("| %s | %d | %s | %s | %s |" % (cond, len(corps), " | ".join(cells), ci_str(dk, dn), ci_str(lk, ln)))
    w("")
    with open(os.path.join(a.out_dir, "rates.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["condition", "corpus", "category", "metric", "bad", "n"])
        wr.writeheader()
        wr.writerows(rate_rows)

    # 每种子 B / M 概要
    w("每种子概要（B / M）：")
    w("")
    w("| 种子 | B FNR(MUST_DENY) | M FNR(MUST_DENY) | B FPR(L) | M FPR(L) | M 原因码与 oracle 一致 |")
    w("|---|---|---|---|---|---|")
    for s in seeds:
        corp = str(s)
        out = []
        for cond in ("B", "M"):
            r = cat_rates(runs[(cond, corp)], corpora[corp])
            out.append((sum(r[c][0] for c in D_CATS), sum(r[c][1] for c in D_CATS), sum(r[c][0] for c in L_CATS), sum(r[c][1] for c in L_CATS)))
        agree, _ = oracle_vs(runs[("M", corp)], corpora[corp])
        w("| %s | %d/%d (%s) | %d/%d (%s) | %d/%d (%s) | %d/%d (%s) | %d/%d |" % (
            corp, out[0][0], out[0][1], pct(out[0][0] / out[0][1]), out[1][0], out[1][1], pct(out[1][0] / out[1][1]),
            out[0][2], out[0][3], pct(out[0][2] / out[0][3]), out[1][2], out[1][3], pct(out[1][2] / out[1][3]),
            agree, len(corpora[corp]["cases"])))
    w("")

    # H1′ 操纵检查
    agg_b, agg_m = {}, {}
    for s in seeds:
        for cond, agg in (("B", agg_b), ("M", agg_m)):
            for cat, (k, n) in cat_rates(runs[(cond, str(s))], corpora[str(s)]).items():
                K, N = agg.get(cat, (0, 0)); agg[cat] = (K + k, N + n)
    fnr_m_zero = all(agg_m[c][0] == 0 for c in D_CATS)
    b_high = [c for c in MISSION_ONLY if agg_b[c][0] / agg_b[c][1] >= 0.9]
    fair = all(agg_b[c][0] == 0 for c in ("F4", "M1", "X1"))
    w("**H1′ 操纵检查**：FNR_M(A)=0 → %s；FNR_B ≥ 0.9 的\"仅使命可拦\"类别 = %d 个（%s；预测 ≥ 6）→ %s。" % (
        "成立" if fnr_m_zero else "不成立", len(b_high), ",".join(b_high), "成立" if len(b_high) >= 6 else "不成立"))
    w("**基线公平性自检**（B 必须拦截 F4/M1/X1）：%s（F4 %d/%d，M1 %d/%d，X1 %d/%d 漏检）。" % (
        "通过" if fair else "未通过", agg_b["F4"][0], agg_b["F4"][1], agg_b["M1"][0], agg_b["M1"][1], agg_b["X1"][0], agg_b["X1"][1]))
    w("")

    # ---- 3. 配对 B vs M
    w("## 3. 配对比较 B vs M（MUST_DENY 用例，%d 个种子汇总；变体层，存在类别内聚类）" % len(seeds))
    w("")
    w("a=都拦，b=只有 M 拦，c=只有 B 拦（使命层回退，预期 0），d=都放。精确 McNemar 双侧 p；Holm 校正跨 %d 个 F/M1/X1 类别。" % len(D_CATS))
    w("")
    praw, prow = {}, {}
    for cat in D_CATS:
        A = B_ = C = D = 0
        for s in seeds:
            cs = [c for c in corpora[str(s)]["cases"] if c["category"] == cat]
            x = paired(verdicts(runs[("B", str(s))]), verdicts(runs[("M", str(s))]), cs)
            A += x[0]; B_ += x[1]; C += x[2]; D += x[3]
        p2, p1 = st.mcnemar_exact(B_, C)
        praw[cat] = p2
        prow[cat] = (A, B_, C, D, p2, p1)
    padj = st.holm(praw)
    w("| 类别 | a | b | c | d | McNemar p（双侧） | Holm p |")
    w("|---|---|---|---|---|---|---|")
    with open(os.path.join(a.out_dir, "paired.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["category", "a", "b", "c", "d", "mcnemar_p_two_sided", "mcnemar_p_one_sided", "holm_p"])
        for cat in D_CATS:
            A, B_, C, D, p2, p1 = prow[cat]
            wr.writerow([cat, A, B_, C, D, p2, p1, padj[cat]])
            w("| %s | %d | %d | %d | %d | %s | %s |" % (cat, A, B_, C, D, pfmt(p2), pfmt(padj[cat])))
    wins = sum(1 for c in MISSION_ONLY if prow[c][1] > prow[c][2])
    loss = sum(1 for c in MISSION_ONLY if prow[c][1] < prow[c][2])
    w("")
    w("类别层符号检验（%d 个仅使命可拦类别）：M 胜 %d、负 %d，双侧 p = %s。" % (len(MISSION_ONLY), wins, loss, pfmt(st.sign_test(wins, loss))))
    c_total = sum(prow[c][2] for c in D_CATS)
    w("")

    # ---- 4. 误拒非劣效
    w("## 4. 误拒非劣效（L1–L5，Δ = %.0f 个百分点；草稿真值，装置自检）" % (100 * T["delta"]))
    w("")
    w("配对差 FPR_M − FPR_B = (b − c)/n ≤ b/n；以 b/n 的 Clopper–Pearson 双侧 95% 上界为保守精确上界。")
    w("")
    w("| 语料 | n | b（仅 M 拒） | c（仅 B 拒） | 差值 | 95% 保守上界 | < Δ ? |")
    w("|---|---|---|---|---|---|---|")
    ni_rows = []
    tb = tc = tn = 0
    for s in seeds:
        cs = [c for c in corpora[str(s)]["cases"] if c["category"] in L_CATS]
        _, b2, c2, _ = paired(verdicts(runs[("B", str(s))]), verdicts(runs[("M", str(s))]),
                              cs)  # 注意：此处 b2 = B PERMIT ∧ M DENY（仅 M 拒）
        n = len(cs)
        ub = st.clopper_pearson(b2, n)[1]
        ni_rows.append((str(s), n, b2, c2, (b2 - c2) / n, ub, ub < T["delta"]))
        tb += b2; tc += c2; tn += n
    ub = st.clopper_pearson(tb, tn)[1] if tn else 1.0
    ni_rows.append(("pooled", tn, tb, tc, (tb - tc) / tn if tn else 0, ub, ub < T["delta"]))
    with open(os.path.join(a.out_dir, "noninferiority.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["corpus", "n", "b_M_only_deny", "c_B_only_deny", "diff", "upper95_conservative", "noninferior"])
        for r in ni_rows:
            wr.writerow(r)
            w("| %s | %d | %d | %d | %s | %s | %s |" % (r[0], r[1], r[2], r[3], pct(r[4]), pct(r[5]), "是" if r[6] else "否"))
    # L2 子型
    l2 = {}
    for s in seeds:
        v = verdicts(runs[("M", str(s))])
        for c in corpora[str(s)]["cases"]:
            if c["category"] == "L2":
                k, n = l2.get(c["subtype"], (0, 0))
                l2[c["subtype"]] = (k + int(v[c["case_id"]] == "DENY"), n + 1)
    l2_bad = [k for k, (x, n) in l2.items() if n and x / n >= T["l2_systematic"]]
    w("")
    w("L2 边界子型（M 误拒）：" + "；".join("%s %d/%d" % (k, x, n) for k, (x, n) in sorted(l2.items())))
    w("")

    # ---- 5. B+
    x3 = None
    if first and ("Bplus", first) in runs and runs[("Bplus", first)]["cases"]:
        w("## 5. B+（领域规则强化基线，首个种子 %s）" % first)
        w("")
        vb, vm, vp = verdicts(runs[("B", first)]), verdicts(runs[("M", first)]), verdicts(runs[("Bplus", first)])
        fcases = [c for c in corpora[first]["cases"] if c["category"] in F_CATS]
        m_deny = [c for c in fcases if vm[c["case_id"]] == "DENY"]
        both = [c for c in m_deny if vp[c["case_id"]] == "DENY"]
        incr = [c for c in m_deny if vb[c["case_id"]] == "PERMIT"]
        incr_p = [c for c in incr if vp[c["case_id"]] == "DENY"]
        x3 = len(both) / len(m_deny) if m_deny else 0
        w("- X-3 口径（预注册）：F1–F9 中 M 拦截的用例里 B+ 也拦截的比例 = %d/%d = **%s**（门槛 %s）" % (
            len(both), len(m_deny), pct(x3), pct(T["bplus_ceiling"])))
        w("- 补充（增量口径，不用于判定）：M 拦而 B 放的用例里 B+ 拦截的比例 = %d/%d = %s" % (
            len(incr_p), len(incr), pct(len(incr_p) / len(incr)) if incr else "n/a"))
        per = {}
        for c in fcases:
            k, n = per.get(c["category"], (0, 0))
            per[c["category"]] = (k + int(vp[c["case_id"]] == "DENY"), n + 1)
        w("- B+ 各类别拦截数：" + "；".join("%s %d/%d" % (k, x, n) for k, (x, n) in sorted(per.items())))
        lp = [c for c in corpora[first]["cases"] if c["category"] in L_CATS]
        w("- B+ 误拒（L1–L5）：%d/%d" % (sum(vp[c["case_id"]] == "DENY" for c in lp), len(lp)))
        w("")

    # ---- 6. 消融
    abl = [c for c in ABLATION_PRED if first and (c, first) in runs and runs[(c, first)]["cases"]]
    if abl:
        w("## 6. 消融（构念效度检查，首个种子 %s）" % first)
        w("")
        w("| 条件 | 预测上升类别 | 预测类别漏检（M → M−k） | 其他 F 类别漏检变化 | L 误拒 | 预测是否出现 |")
        w("|---|---|---|---|---|---|")
        base = cat_rates(runs[("M", first)], corpora[first])
        for cnd in abl:
            r = cat_rates(runs[(cnd, first)], corpora[first])
            pred = ABLATION_PRED[cnd]
            ptxt = "；".join("%s %d→%d/%d" % (c, base[c][0], r[c][0], r[c][1]) for c in pred)
            others = [c for c in F_CATS if c not in pred and r[c][0] != base[c][0]]
            otxt = "；".join("%s %d→%d" % (c, base[c][0], r[c][0]) for c in others) or "无"
            lfp = sum(r[c][0] for c in L_CATS)
            ok = all(r[c][0] > base[c][0] for c in pred)
            w("| %s | %s | %s | %s | %d | %s |" % (cnd, ",".join(pred), ptxt, otxt, lfp, "是" if ok else "**否**（逐个说明）"))
        w("")

    # ---- 7. 篡改轨道
    x5 = None
    if first and runs.get(("B", first), {}).get("lines") and runs.get(("M", first), {}).get("lines"):
        w("## 7. 证据篡改轨道 T1–T7（离线，主机上对日志副本施加变换；每种 %d 个随机位置变体）" % a.tamper_n)
        w("")
        import random
        ext = ps.internal_anchor(runs[("M", first)]["lines"])
        trows, summ = [], {}
        for kind in ["T%d" % i for i in range(1, 8)]:
            for fmt, cond in (("B", "B"), ("M", "M")):
                modes = ["no_anchor", "external_anchor"] if (fmt == "M" and kind == "T5") else ["default"]
                for mode in modes:
                    rng = random.Random("%s-%s-%s" % (first, kind, fmt))
                    det = 0
                    for i in range(a.tamper_n):
                        tl, info = tm.tamper(runs[(cond, first)]["lines"], kind, rng)
                        if fmt == "M":
                            rep = ps.verify_chain(ps.parse_evidence(tl), ext if mode == "external_anchor" else None, ps.internal_anchor(tl))
                        else:
                            rep = ps.verify_seq_lines(tl)
                        det += int(not rep.ok)
                        trows.append([kind, fmt, mode, i, int(not rep.ok), rep.problem or "", info.get("pos_seq", "")])
                    summ[(kind, fmt, mode)] = det
        with open(os.path.join(a.out_dir, "tamper.csv"), "w", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            wr.writerow(["kind", "format", "mode", "variant", "detected", "problem", "pos_seq"])
            wr.writerows(trows)
        exp = json.load(open(os.path.join(EXP, "tamper", "expectations.json"), encoding="utf-8"))["expected"]
        n = a.tamper_n
        w("| 篡改 | B 序号日志检出 | M FNV 链检出 | 预注册预期（B / M） |")
        w("|---|---|---|---|")
        for kind in ["T%d" % i for i in range(1, 8)]:
            if kind == "T5":
                mtxt = "无锚点 %d/%d；外部锚点 %d/%d" % (summ[(kind, "M", "no_anchor")], n, summ[(kind, "M", "external_anchor")], n)
                etxt = "%s / 无锚点 %s，有锚点 %s" % (exp[kind]["B"], exp[kind]["M_no_anchor"], exp[kind]["M_external_anchor"])
            else:
                mtxt = "%d/%d" % (summ[(kind, "M", "default")], n)
                etxt = "%s / %s" % (exp[kind]["B"], exp[kind]["M"])
            w("| %s | %d/%d | %s | %s |" % (kind, summ[(kind, "B", "default")], n, mtxt, etxt))
        mb = sum(summ[("T%d" % i, "B", "default")] for i in range(1, 5))
        mm = sum(summ[("T%d" % i, "M", "default")] for i in range(1, 5))
        p2, p1 = st.fisher_exact(mm, 4 * n - mm, mb, 4 * n - mb)
        x5 = p1
        w("")
        w("T1–T4 合并：M %d/%d vs B %d/%d，Fisher 精确单侧 p（M 更高）= %s；双侧 p = %s。" % (mm, 4 * n, mb, 4 * n, pfmt(p1), pfmt(p2)))
        w("T5（无锚点）与 T7 在 M 上不检出是**预先声明的预期失败**，属 U（教学级 FNV-1a32 无密钥、无外部锚点不能防截尾），不是待修复缺陷。")
        w("")

    # ---- 8. 草稿留出语料
    h1 = None
    if ("B", "holdout_draft") in runs and ("M", "holdout_draft") in runs and runs[("M", "holdout_draft")]["cases"]:
        hc = corpora["holdout_draft"]
        w("## 8. 草稿留出语料（作者手写；草稿·待独立标注人复核；**不计入确证性结论，不得用于判定 X-1**）")
        w("")
        core = [c for c in hc["cases"] if not c.get("spec_gap")]
        gaps = [c for c in hc["cases"] if c.get("spec_gap")]
        w("用例 %d 个（MUST_DENY %d，MAY_PERMIT %d；其中 spec_gap 单列 %d 个）。真值 = 作者依核心原则的草稿判断。" % (
            len(hc["cases"]), sum(c["gt"] == "MUST_DENY" for c in hc["cases"]), sum(c["gt"] == "MAY_PERMIT" for c in hc["cases"]), len(gaps)))
        w("")
        w("| 条件 | FNR（非 spec_gap 的 MUST_DENY） | FPR（非 spec_gap 的 MAY_PERMIT） |")
        w("|---|---|---|")
        for cond in ("B", "Bplus", "M"):
            if (cond, "holdout_draft") not in runs or not runs[(cond, "holdout_draft")]["cases"]:
                continue
            v = verdicts(runs[(cond, "holdout_draft")])
            dd = [c for c in core if c["gt"] == "MUST_DENY"]
            pp = [c for c in core if c["gt"] == "MAY_PERMIT"]
            fk = sum(v[c["case_id"]] == "PERMIT" for c in dd)
            pk = sum(v[c["case_id"]] == "DENY" for c in pp)
            w("| %s | %d/%d = %s | %d/%d = %s |" % (cond, fk, len(dd), ci_str(fk, len(dd)), pk, len(pp), ci_str(pk, len(pp))))
        vb, vm = verdicts(runs[("B", "holdout_draft")]), verdicts(runs[("M", "holdout_draft")])
        dd = [c for c in core if c["gt"] == "MUST_DENY"]
        A, B_, C, D = paired(vb, vm, dd)
        p2, p1 = st.mcnemar_exact(B_, C)
        fnr_m = sum(vm[c["case_id"]] == "PERMIT" for c in dd) / len(dd) if dd else 1
        h1 = (p1, fnr_m, len(dd))
        w("")
        w("配对（MUST_DENY）：a=%d b=%d c=%d d=%d；精确 McNemar 单侧 p = %s（仅演示计算路径）。" % (A, B_, C, D, pfmt(p1)))
        if gaps:
            w("")
            w("spec_gap 条目（单列，不并入上表）：")
            w("")
            w("| 用例 | 草稿真值 | oracle 条文判定 | B | B+ | M（理由） | 说明 |")
            w("|---|---|---|---|---|---|---|")
            vp = verdicts(runs[("Bplus", "holdout_draft")]) if ("Bplus", "holdout_draft") in runs else {}
            for c in gaps:
                r = runs[("M", "holdout_draft")]["cases"][c["case_id"]]
                w("| %s %s | %s | %s/%s | %s | %s | %s（%s） | %s |" % (c["name"], c["description"], c["gt"], c["oracle_gt"], c["oracle_reason"],
                                                                vb[c["case_id"]], vp.get(c["case_id"], "-"), r.verdict, r.reason, c["rationale"]))
        w("")

    # ---- 9. oracle vs M
    w("## 9. 草稿 oracle 与门闩 M 的一致性")
    w("")
    ov_lines = ["# 草稿 oracle 与门闩 M 判决/理由码比对", "", "> 草稿·待独立标注人复核；不计入确证性结论。oracle 与门闩代码无共享逻辑（oracle 只读 JSON）。", ""]
    w("| 语料 | 用例 | 判决与理由码均一致 | 不一致 |")
    w("|---|---|---|---|")
    all_dis = []
    for corp in [str(s) for s in seeds] + (["holdout_draft"] if ("M", "holdout_draft") in runs else []):
        run = runs.get(("M", corp))
        if not run or not run["cases"]:
            continue
        gtf = "oracle_gt" if corp == "holdout_draft" else "gt"
        agree, dis = oracle_vs(run, corpora[corp], gt_field=gtf)
        w("| %s | %d | %d | %d |" % (corp, len(corpora[corp]["cases"]), agree, len(dis)))
        all_dis += [(corp,) + d for d in dis]
    w("")
    if all_dis:
        w("不一致条目（逐条人工裁决前不得静默处理）：")
        w("")
        w("| 语料 | case_id | 名称 | 类别 | oracle 真值 | M 判决 | oracle 理由 | M 理由 |")
        w("|---|---|---|---|---|---|---|---|")
        for d in all_dis:
            w("| %s | %s | %s | %s | %s | %s | %s | %s |" % d)
        w("")
    else:
        w("在全部作者语料种子%s上，M 与草稿 oracle 的判决与理由码**逐条一致**（0 条不一致）。注意：二者出自同一作者、依据同一份规格，一致只说明实现与规格条文相符，不说明规格本身正确。" % ("与草稿留出语料（按 oracle 条文真值）" if ("M", "holdout_draft") in runs else ""))
        w("")
    ov_lines += ["共 %d 条不一致。" % len(all_dis)] + ["| %s | %s | %s | %s | %s | %s | %s | %s |" % d for d in all_dis]
    open(os.path.join(a.out_dir, "oracle_vs_M.md"), "w", encoding="utf-8").write("\n".join(ov_lines) + "\n")

    # ---- 10. 成本
    w("## 10. 代码 / 证据增量成本（E2，探索性）")
    w("")
    locs = {k: loc.count(os.path.join(EXP, "gatekeeper_field.c"), v) for k, v in loc.VARIANTS.items()}
    ratio = locs["M"] / locs["B"]
    w("- 门闩有效行数（gatekeeper_field.c 按编译期条件展开；非空非注释，含预处理指令行）：" + "，".join("%s=%d" % kv for kv in locs.items()))
    w("- LOC 比 M/B = %.2f（X-7 门槛 %.1f）" % (ratio, T["loc_ratio"]))
    for cond in ("B", "Bplus", "M"):
        if first and (cond, first) in runs and runs[(cond, first)]["log"]:
            p = runs[(cond, first)]["log"]
            bl = [l for l in runs[(cond, first)]["lines"] if l.startswith("RUN|build_ok")]
            body = sum(len(l) + 1 for l in runs[(cond, first)]["lines"]
                       if l.startswith(("CASE|", "SETUP|", "EVIDENCE|", "AUDIT|", "GATE|NOTE")))
            w("- %s：门闩相关串口字节/被评分请求 = %.1f；%s" % (cond, body / len(corpora[first]["cases"]), bl[0] if bl else ""))
    w("")

    # ---- 11. 反证条件清单
    fc = ["# 反证条件逐条判定（X-1…X-7）", "",
          "> 运行环境：%s。作者语料 + 草稿真值 → 下列判定均为**装置自检口径**，不是确证性结论。" % a.env_label, "",
          "| 编号 | 条件 | 当前状态 | 依据 |", "|---|---|---|---|"]
    fc.append("| X-1 | 留出语料 H 上 McNemar 不显著或 FNR_M(H) ≥ %s | **未判定**（尚无独立标注人编写的留出语料） | 草稿留出语料仅演示：%s |" % (
        pct(T["h_fnr_ceiling"]), ("单侧 p=%s，FNR_M=%s，n_deny=%d（不计入）" % (pfmt(h1[0]), pct(h1[1]), h1[2])) if h1 else "未运行"))
    x2 = any(not r[6] for r in ni_rows) or bool(l2_bad)
    fc.append("| X-2 | 误拒非劣效不成立或 L2 子型系统性被拒（子型 FPR ≥ %s） | %s（装置自检） | 合并上界 %s；L2 系统性被拒子型：%s |" % (
        pct(T["l2_systematic"]), "成立" if x2 else "不成立", pct(ni_rows[-1][5]), ",".join(l2_bad) or "无"))
    fc.append("| X-3 | B+ 拦截 M 所拦 F1–F9 的 ≥ %s | %s（装置自检） | %s |" % (
        pct(T["bplus_ceiling"]), ("成立" if x3 >= T["bplus_ceiling"] else "不成立") if x3 is not None else "未运行", pct(x3) if x3 is not None else "-"))
    fc.append("| X-4 | M 出现 c > 0（B 拦而 M 放） | %s | 全部 MUST_DENY 类别 c 合计 = %d |" % ("成立" if c_total > 0 else "不成立", c_total))
    fc.append("| X-5 | T1–T4 上链检出率不高于序号日志（Fisher 不显著） | %s | Fisher 单侧 p = %s |" % (
        ("成立" if x5 >= T["alpha2"] else "不成立") if x5 is not None else "未运行", pfmt(x5) if x5 is not None else "-"))
    fc.append("| X-6 | 人工研究 M 的 F1 中位数不高于 B 且更慢 | **未判定**（人工审查研究已推迟） | — |")
    fc.append("| X-7 | LOC > %.0f 倍基线且 X-1 成立 | %s | LOC 比 %.2f |" % (
        T["loc_ratio"], "不成立（LOC 比未超门槛，与 X-1 无关）" if ratio <= T["loc_ratio"] else "待 X-1", ratio))
    open(os.path.join(a.out_dir, "falsification_checklist.md"), "w", encoding="utf-8").write("\n".join(fc) + "\n")
    w("## 11. 反证条件清单（装置自检口径）")
    w("")
    R.extend(fc[4:])
    w("")
    w("---")
    w("*本报告由 experiment/analysis/analyze.py 自动生成。非临床 · 仅仿真 · 交付 ≠ 达成。*")
    open(os.path.join(a.out_dir, "report.md"), "w", encoding="utf-8").write("\n".join(R) + "\n")
    print("report -> %s" % os.path.join(a.out_dir, "report.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
