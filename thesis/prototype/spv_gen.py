#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【示意性原型 / illustrative prototype —— 非实验树的一部分，不参与预注册实验，数字仅为可行性自测】
spv_gen.py：托付记录驱动的单点违反（single-point violation, SPV）语料生成器草案。

思路（拟定）：对每条"当前有效"托付记录 e，先构造一个对 e 合法的名义请求（nominal），
再只改动一个托付要素（时间 / 范围 / 问责 / 版本 / 证据）得到假使命；同时生成边界合法对照。
真值一律由实验树的参考判定器 oracle.evaluate_case 给出（生成器"意图条款"只用于自检）。
输出格式与 experiment/corpus/gen_corpus.py 相同：mission-se-corpus/v1 JSON + corpus_c.corpus_header 头文件。

只读引用实验树（sys.path 导入 corpus_c、oracle；读取 entrustments.json）；不向实验树写任何文件。
用法：python3 spv_gen.py --seed 1 --out out/            # 写 out/spv_<seed>.json/.h
      python3 spv_gen.py --seed 1 --determinism          # 同种子两次生成逐字节比较
"""
import argparse
import json
import os
import random
import sys
sys.dont_write_bytecode = True  # 不在只读引用的实验树内写 __pycache__

EXP = os.environ.get("MISSION_EXP", os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mission-shell", "experiment")))
sys.path.insert(0, os.path.join(EXP, "corpus"))
sys.path.insert(0, os.path.join(EXP, "oracle"))
import corpus_c  # noqa: E402
import oracle  # noqa: E402

GENERATOR = "spv_gen.py v0.1-proto"
CASE_ID_BASE = 5001          # 拟定：避开作者语料 1..320 与留出语料 9001 起
ENT_PATH = os.path.join(EXP, "corpus", "entrustments.json")
OP, ADV = 1, 2


class Gen:
    def __init__(self, seed, book):
        self.rng = random.Random(seed)
        self.book = book
        self.A = book.action_code
        self.nonce = 7000000 + (seed % 1000) * 1000   # 拟定区段；每例内唯一即可

    def ev(self, e, **kw):
        self.nonce += 1
        r = {"op": "EVAL", "kind": "target", "action": self.A["ENABLE_SIM"], "role": OP, "origin": OP,
             "ent": e["id"], "ver": e["ver"], "zone": None, "level": None, "nonce": self.nonce, "u": 1}
        r.update(kw)
        if r["zone"] is None:
            r["zone"] = self.rng.choice(e["allowed_zones"])
        if r["level"] is None:
            r["level"] = self.rng.randint(1, e["sim_level_max"])
        return r

    def nominal_action(self, e):
        for n in ("ENABLE_SIM", "RECOMMEND", "QUERY_STATUS"):
            if n in e["allowed_actions"]:
                return self.A[n]

    def now_in(self, e):
        return self.rng.randint(e["t_start"], e["t_end"])


def G(e):
    return {"op": "GRANT", "ent": e["id"], "ver": e["ver"]}


def RV(e):
    return {"op": "REVOKE", "ent": e["id"], "ver": e["ver"]}


def case(element, rule, intended, e, now, pre, target, note=""):
    return {"element": element, "rule": rule, "intended_clause": intended,
            "ent_ref": "%dv%d" % (e["id"], e["ver"]), "note": note,
            "steps": [{"op": "RESET"}, {"op": "CLOCK", "now": now}] + pre + [target]}


def rules_for(g, e, current, by_id):
    A, out = g.A, []
    na = g.nominal_action(e)
    can_enable = "ENABLE_SIM" in e["allowed_actions"]
    # ---- 时间 ----
    for d in (1, g.rng.randint(2, 50)):
        out.append(case("time", "after_t_end", "S-T1", e, e["t_end"] + d, [G(e)], g.ev(e, action=na), "d=%d" % d))
        if e["t_start"] - d >= 0:
            out.append(case("time", "before_t_start", "S-T2", e, e["t_start"] - d, [G(e)], g.ev(e, action=na), "d=%d" % d))
    out.append(case("time", "LEGAL_at_t_start", "", e, e["t_start"], [G(e)], g.ev(e, action=na)))
    out.append(case("time", "LEGAL_at_t_end", "", e, e["t_end"], [G(e)], g.ev(e, action=na)))
    # ---- 范围 ----
    for z in e["forbidden_zones"]:
        out.append(case("scope", "zone_forbidden", "S-Z1", e, g.now_in(e), [G(e)], g.ev(e, action=na, zone=z), "z=%d" % z))
    outside = [z for z in range(g.book.n_zones) if z not in e["allowed_zones"] and z not in e["forbidden_zones"]]
    for z in sorted(g.rng.sample(outside, min(2, len(outside)))):
        out.append(case("scope", "zone_not_allowed", "S-S1", e, g.now_in(e), [G(e)], g.ev(e, action=na, zone=z), "z=%d" % z))
    lv = sorted({e["sim_level_max"] + 1, g.rng.randint(e["sim_level_max"] + 1, g.book.level_max)})
    for L in lv:
        out.append(case("scope", "level_over_max", "S-S2", e, g.now_in(e), [G(e)], g.ev(e, action=na, level=L), "level=%d" % L))
    out.append(case("scope", "LEGAL_level_eq_max", "", e, g.now_in(e), [G(e)], g.ev(e, action=na, level=e["sim_level_max"])))
    for n in ("ENABLE_SIM", "RECOMMEND", "QUERY_STATUS"):
        if n not in e["allowed_actions"]:
            out.append(case("scope", "action_not_allowed", "S-S3", e, g.now_in(e), [G(e)], g.ev(e, action=A[n]), n))
    # ---- 问责 ----
    if can_enable:
        out.append(case("accountability", "advisor_role_enable", "S-R1", e, g.now_in(e), [G(e)], g.ev(e, role=ADV, origin=ADV)))
        out.append(case("accountability", "advisor_origin_laundered", "S-P1", e, g.now_in(e), [G(e)], g.ev(e, role=OP, origin=ADV)))
    if "RECOMMEND" in e["allowed_actions"]:
        out.append(case("accountability", "LEGAL_advisor_recommend", "", e, g.now_in(e), [G(e)],
                        g.ev(e, action=A["RECOMMEND"], role=ADV, origin=ADV)))
    out.append(case("accountability", "no_cosign", "S-C1", e, g.now_in(e), [], g.ev(e, action=na)))
    out.append(case("accountability", "cosign_revoked", "S-C1", e, g.now_in(e), [G(e), RV(e)], g.ev(e, action=na)))
    other = [x for x in current if x["id"] != e["id"]]
    o = g.rng.choice(other)
    out.append(case("accountability", "cosign_bound_other", "S-C2", e, g.now_in(e), [G(o)], g.ev(e, action=na), "bound=%dv%d" % (o["id"], o["ver"])))
    # ---- 证据（交付≠达成；U 非空） ----
    if can_enable:
        out.append(case("evidence", "enable_u0", "S-U1", e, g.now_in(e), [G(e)], g.ev(e, u=0)))
    out.append(case("evidence", "claim_u0", "S-U1", e, g.now_in(e), [G(e)], g.ev(e, action=A["CLAIM_ACHIEVE"], u=0)))
    out.append(case("evidence", "claim_u_nonzero", "S-U2", e, g.now_in(e), [G(e)],
                    g.ev(e, action=A["CLAIM_ACHIEVE"], u=g.rng.randint(1, 255))))
    # ---- 名义合法 ----
    for _ in range(2):
        out.append(case("legal", "LEGAL_nominal", "", e, g.now_in(e), [G(e)], g.ev(e, action=na)))
    # ---- 版本（仅对存在被取代版本的托付） ----
    for old in sorted(by_id[e["id"]], key=lambda r: r["ver"]):
        if not old["superseded"]:
            continue
        na_o = g.nominal_action(old)
        z = g.rng.choice(sorted(set(old["allowed_zones"]) & set(e["allowed_zones"])) or old["allowed_zones"])
        lvl = g.rng.randint(1, min(old["sim_level_max"], e["sim_level_max"]))
        t = g.rng.randint(max(old["t_start"], e["t_start"]), min(old["t_end"], e["t_end"]))
        out.append(case("version", "stale_bound_old", "S-V1", old, t, [G(old)], g.ev(old, action=na_o, zone=z, level=lvl)))
        out.append(case("version", "bound_current_ref_old", "S-C2", old, t, [G(e)], g.ev(old, action=na_o, zone=z, level=lvl)))
        out.append(case("version", "LEGAL_rebind_current", "", e, t, [G(old), RV(old), G(e)], g.ev(e, action=na, zone=z, level=lvl)))
    return out


def build(seed):
    book = oracle.EntrustmentBook(ENT_PATH)
    recs = book.doc["entrustments"]
    current = [r for r in recs if not r["superseded"]]
    by_id = {}
    for r in recs:
        by_id.setdefault(r["id"], []).append(r)
    g = Gen(seed, book)
    cases = []
    for e in sorted(current, key=lambda r: r["id"]):
        cases += rules_for(g, e, current, by_id)
    selfcheck = {"intended_mismatch": [], "impure": 0}
    for c in cases:
        o = oracle.evaluate_case(dict(c, case_id=0), book)
        c["gt"], c["oracle_clause"], c["oracle_reason"] = o["gt"], o["oracle_clause"], o["oracle_reason"]
        c["oracle_all_clauses"] = o["oracle_all_clauses"]
        c["category"] = ("SPV-" + c["element"]) if c["intended_clause"] else ("LEGAL-" + c["element"])
        c["subtype"] = c["rule"]
        c["name"] = "%s/%s/%s" % (c["category"], c["rule"], c["ent_ref"])
        c["single_point_pure"] = len(o["oracle_all_clauses"]) == (1 if c["intended_clause"] else 0)
        if c["oracle_clause"] != c["intended_clause"]:
            selfcheck["intended_mismatch"].append(c["name"])
        if not c["single_point_pure"]:
            selfcheck["impure"] += 1
    g.rng.shuffle(cases)
    for i, c in enumerate(cases):
        c["case_id"] = CASE_ID_BASE + i
    book_sha = corpus_c.sha256_hex(open(ENT_PATH, "rb").read())
    doc = {"schema": "mission-se-corpus/v1", "corpus_id": "spv-proto-%d" % seed, "corpus_set": "student_spv_proto",
           "seed": seed, "generator": GENERATOR, "entrustments_sha256": book_sha,
           "draft_notice": "示意性原型语料：仅用于可行性自测，非预注册、非独立、不得并入作者语料或留出语料。",
           "selfcheck": selfcheck, "cases": cases}
    return doc


def emit(doc, outdir):
    jb = corpus_c.canonical_json_bytes(doc)
    jsha = corpus_c.sha256_hex(jb)
    hb = corpus_c.corpus_header(doc, jsha)
    os.makedirs(outdir, exist_ok=True)
    base = "spv_%d" % doc["seed"]
    corpus_c.write_bytes(os.path.join(outdir, base + ".json"), jb)
    corpus_c.write_bytes(os.path.join(outdir, base + ".h"), hb)
    return jsha, corpus_c.sha256_hex(hb)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
    ap.add_argument("--determinism", action="store_true")
    a = ap.parse_args(argv)
    d1 = build(a.seed)
    if a.determinism:
        b1 = corpus_c.canonical_json_bytes(d1)
        b2 = corpus_c.canonical_json_bytes(build(a.seed))
        h1 = corpus_c.corpus_header(d1, corpus_c.sha256_hex(b1))
        h2 = corpus_c.corpus_header(build(a.seed), corpus_c.sha256_hex(b2))
        print("determinism seed=%d json_identical=%s header_identical=%s sha=%s" % (
            a.seed, b1 == b2, h1 == h2, corpus_c.sha256_hex(b1)))
        return 0 if (b1 == b2 and h1 == h2) else 1
    js, hs = emit(d1, a.out)
    from collections import Counter
    n_deny = sum(c["gt"] == "MUST_DENY" for c in d1["cases"])
    print("seed=%d cases=%d MUST_DENY=%d MAY_PERMIT=%d json_sha=%s h_sha=%s" % (
        a.seed, len(d1["cases"]), n_deny, len(d1["cases"]) - n_deny, js, hs))
    print("by element:", dict(sorted(Counter(c["category"] for c in d1["cases"]).items())))
    print("selfcheck: intended_mismatch=%d impure=%d" % (len(d1["selfcheck"]["intended_mismatch"]), d1["selfcheck"]["impure"]))
    for n in d1["selfcheck"]["intended_mismatch"][:20]:
        print("  mismatch:", n)
    imp = Counter((c["subtype"], tuple(c["oracle_all_clauses"])) for c in d1["cases"] if not c["single_point_pure"])
    for k, v in sorted(imp.items()):
        print("  impure:", k, v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
