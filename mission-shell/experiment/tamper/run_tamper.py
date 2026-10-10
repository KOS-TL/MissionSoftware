#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
篡改轨道批量运行：对一份 B（或 B+）日志与一份 M 日志，各施加 T1–T7 每种 n 个随机位置变体，
用 parse_serial.py 的 verify-seq / verify-chain 检测，输出 tamper_results.json 与 tamper.csv。

T5 对 M 分两种口径：无外部锚点（只看日志自身）与有外部锚点（采集时另行登记的 tip/len，
此处取原始未篡改日志中的 GATE|CHAIN 行模拟"另行登记"）。

用法：run_tamper.py --log-b B.log --log-m M.log [--n 20] [--seed 20261007] --out-dir DIR
"""
import argparse
import csv
import importlib.util
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ps = _load("parse_serial", "../analysis/parse_serial.py")
tm = _load("tamper_mod", "tamper.py")


def detect(lines, fmt, external_anchor=None):
    if fmt == "M":
        rep = ps.verify_chain(ps.parse_evidence(lines), external_anchor, ps.internal_anchor(lines))
    else:
        rep = ps.verify_seq_lines(lines)
    return (not rep.ok), rep.problem


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-b", required=True)
    ap.add_argument("--log-m", required=True)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261007)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    logs = {"B": ps.read_lines(a.log_b), "M": ps.read_lines(a.log_m)}
    ext_anchor = ps.internal_anchor(logs["M"])
    res = {"false_alarm": {}, "rows": [], "summary": {}}
    for fmt, lines in logs.items():
        res["false_alarm"][fmt] = detect(lines, fmt, ext_anchor if fmt == "M" else None)[0]
    for kind in ["T%d" % i for i in range(1, 8)]:
        for fmt in ("B", "M"):
            rng = random.Random("%d-%s-%s" % (a.seed, kind, fmt))
            modes = ["no_anchor", "external_anchor"] if (fmt == "M" and kind == "T5") else ["default"]
            for mode in modes:
                det = 0
                for i in range(a.n):
                    t_lines, info = tm.tamper(logs[fmt], kind, rng)
                    d, prob = detect(t_lines, fmt, ext_anchor if mode == "external_anchor" else None)
                    det += d
                    res["rows"].append({"kind": kind, "format": fmt, "mode": mode, "variant": i,
                                        "detected": int(d), "problem": prob or "", "pos_seq": info.get("pos_seq", "")})
                key = "%s|%s|%s" % (kind, fmt, mode)
                res["summary"][key] = {"detected": det, "n": a.n}
    with open(os.path.join(a.out_dir, "tamper_results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    with open(os.path.join(a.out_dir, "tamper.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(res["rows"][0].keys()))
        w.writeheader()
        w.writerows(res["rows"])
    for k, v in res["summary"].items():
        print("%-28s %2d/%d" % (k, v["detected"], v["n"]))
    print("false alarms on untampered logs:", res["false_alarm"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
