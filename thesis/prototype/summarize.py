#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【示意性原型】汇总 out/scored/*.csv：漏拒率 FNR、误拒率 FPR（Wilson 95%）、按要素漏拒、B vs M 精确 McNemar、
变异体是否被"杀死"（判决层 / 理由码层，相对未变异 M）。统计函数只读导入 experiment/analysis/stats_exact.py。"""
import csv
import glob
import os
import sys
sys.dont_write_bytecode = True  # 不在只读引用的实验树内写 __pycache__
from collections import defaultdict

EXP = os.environ.get("MISSION_EXP", os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mission-shell", "experiment")))
sys.path.insert(0, os.path.join(EXP, "analysis"))
import stats_exact as st  # noqa: E402


def load(p):
    return {int(r["case_id"]): r for r in csv.DictReader(open(p, encoding="utf-8"))}


def main(scdir, _corpus):
    runs = {os.path.basename(p)[:-4]: load(p) for p in sorted(glob.glob(os.path.join(scdir, "*.csv")))}
    any_run = next(iter(runs.values()))
    n_deny = sum(r["gt"] == "MUST_DENY" for r in any_run.values())
    n_perm = len(any_run) - n_deny
    print("【示意性原型；主机模拟、非 QEMU 实测；作者自建语料、非独立、非确证性】")
    print("cases=%d MUST_DENY=%d MAY_PERMIT=%d" % (len(any_run), n_deny, n_perm))
    print("%-18s %8s %22s %8s %22s %8s %s" % ("condition", "FN", "FNR [Wilson95]", "FP", "FPR [Wilson95]", "INVALID", "reason=oracle"))
    for k in [x for x in runs if not x.startswith("mut-")] + [x for x in runs if x.startswith("mut-")]:
        R = runs[k]
        fn = sum(r["outcome"] == "FN" for r in R.values())
        fp = sum(r["outcome"] == "FP" for r in R.values())
        inv = sum(r["outcome"] == "INVALID" for r in R.values())
        rm = sum(int(r["reason_matches"]) for r in R.values())
        lo, hi = st.wilson(fn, n_deny)
        lo2, hi2 = st.wilson(fp, n_perm)
        print("%-18s %8d %7.1f%% [%4.1f,%5.1f] %8d %7.1f%% [%4.1f,%5.1f] %8d %d/%d" % (
            k, fn, 100.0 * fn / n_deny, 100 * lo, 100 * hi, fp, 100.0 * fp / n_perm, 100 * lo2, 100 * hi2, inv, rm, len(R)))
    if "B" in runs and "M" in runs:
        b = sum(1 for c, r in runs["M"].items() if r["gt"] == "MUST_DENY" and r["verdict"] == "DENY" and runs["B"][c]["verdict"] != "DENY")
        c_ = sum(1 for c, r in runs["M"].items() if r["gt"] == "MUST_DENY" and r["verdict"] != "DENY" and runs["B"][c]["verdict"] == "DENY")
        print("B vs M on MUST_DENY: discordant M-only-deny=%d B-only-deny=%d exact McNemar p=%s" % (b, c_, st.mcnemar_exact(b, c_)))
        per = defaultdict(lambda: [0, 0, 0])
        for c, r in runs["B"].items():
            if r["gt"] == "MUST_DENY":
                per[r["category"]][0] += 1
                per[r["category"]][1] += r["outcome"] == "FN"
                per[r["category"]][2] += runs["M"][c]["outcome"] == "FN"
        print("per element MUST_DENY: n / B-FN / M-FN")
        for k2, v in sorted(per.items()):
            print("   %-22s %3d %3d %3d" % (k2, *v))
    M = runs.get("M")
    for k in [x for x in runs if x.startswith("mut-")]:
        R = runs[k]
        vk = [c for c in R if R[c]["verdict"] != M[c]["verdict"]]
        rk = [c for c in R if R[c]["reason"] != M[c]["reason"]]
        cats = sorted({R[c]["subtype"] for c in vk})
        print("%-18s verdict-kill=%-3s (%3d cases) reason-kill=%-3s (%3d cases) killing subtypes(verdict): %s" % (
            k, "YES" if vk else "no", len(vk), "YES" if rk else "no", len(rk), ",".join(cats[:6])))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
