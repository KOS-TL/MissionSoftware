#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双标一致性工具（实验方案 §3.5 第 3 步）

【草稿·待独立标注人复核；不计入确证性结论】在独立标注人重写 oracle.py 之前，本工具只能用于演练流程。

  kappa.py sample --corpus C.json --n 40 --seed S --out handlabel.csv
      随机抽取 n 个用例，输出**不含真值**的手标模板（作者在 hand_gt 列填 MUST_DENY / MAY_PERMIT）。
  kappa.py score  --corpus C.json --hand handlabel.csv [--kappa-min 0.9]
      用 oracle.py（独立标注人版本）重新判定这些用例，计算 Cohen's κ 并与预注册门槛比较。
"""
import argparse
import csv
import importlib.util
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "analysis"))
import stats_exact  # noqa: E402

ACT = {1: "ENABLE_SIM", 2: "RECOMMEND", 3: "QUERY_STATUS", 4: "CLAIM_ACHIEVE"}
ROLE = {1: "OPERATOR", 2: "ADVISOR"}


def describe(steps):
    out = []
    for s in steps:
        if s["op"] == "RESET":
            continue
        if s["op"] == "CLOCK":
            out.append("now=%d" % s["now"])
        elif s["op"] == "GRANT":
            out.append("GRANT(E%dv%d)" % (s["ent"], s["ver"]))
        elif s["op"] == "REVOKE":
            out.append("REVOKE(%s)" % ("all" if s["ent"] == 0 else "E%dv%d" % (s["ent"], s["ver"])))
        else:
            out.append("[%s] %s role=%s origin=%s ent=E%dv%d zone=%d level=%d nonce=%d U=0x%x" % (
                s["kind"], ACT.get(s["action"], "action=%d" % s["action"]), ROLE.get(s["role"], s["role"]),
                ROLE.get(s["origin"], s["origin"]), s["ent"], s["ver"], s["zone"], s["level"], s["nonce"], s["u"]))
    return "; ".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("sample"); p.add_argument("--corpus", required=True); p.add_argument("--n", type=int, default=40)
    p.add_argument("--seed", type=int, default=1); p.add_argument("--out", required=True)
    p = sp.add_parser("score"); p.add_argument("--corpus", required=True); p.add_argument("--hand", required=True)
    p.add_argument("--kappa-min", type=float, default=0.9)
    a = ap.parse_args(argv)
    corpus = json.load(open(a.corpus, encoding="utf-8"))
    if a.cmd == "sample":
        cs = random.Random(a.seed).sample(corpus["cases"], a.n)
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["case_id", "script", "hand_gt", "hand_clause", "note"])
            for c in sorted(cs, key=lambda c: c["case_id"]):
                w.writerow([c["case_id"], describe(c["steps"]), "", "", ""])
        print("wrote %d blank rows to %s (no ground truth included)" % (a.n, a.out))
        return 0
    spec = importlib.util.spec_from_file_location("oracle", os.path.join(HERE, "oracle.py"))
    om = importlib.util.module_from_spec(spec); spec.loader.exec_module(om)
    book = om.EntrustmentBook()
    byid = {c["case_id"]: c for c in corpus["cases"]}
    hand, orc = [], []
    for row in csv.DictReader(open(a.hand, encoding="utf-8")):
        if not row["hand_gt"].strip():
            continue
        hand.append(row["hand_gt"].strip())
        orc.append(om.evaluate_case(byid[int(row["case_id"])], book)["gt"])
    k = stats_exact.cohen_kappa(hand, orc)
    print("n=%d  Cohen's kappa=%.3f  threshold=%.2f  -> %s" % (len(hand), k, a.kappa_min, "PASS" if k >= a.kappa_min else "FAIL"))
    return 0 if k >= a.kappa_min else 1


if __name__ == "__main__":
    sys.exit(main())
