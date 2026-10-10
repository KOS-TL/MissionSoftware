#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
作者语料 A 生成器 gen_corpus.py（实验方案 §3.2/§3.3/§3.6）

- 确定性：仅使用 random.Random(seed)（Python 标准库）。
- 规模（每种子）：F1–F9 各 20、L1–L5 各 24、M1 10、X1 10，共 320 个用例。
- 每个用例 = 复位 + 时钟设置 + 若干前置步骤 + 唯一的目标请求。
- 生成后用参考判定器 oracle.py（草稿）复核真值与首个违反条款；不一致则丢弃重抽并计数。
- 输出：corpus/out/corpus_<seed>.json（真值）、corpus/out/corpus_<seed>.h（只含请求字段）、
        gen/entrustments_gen.h（托付表，种子无关）、corpus/out/SHA256SUMS。

【提醒】作者语料 A 上的结果只用于"装置自检/操纵检查"，不作为方法有效的证据（方案 H1′）。
真值来自草稿 oracle：草稿·待独立标注人复核；不计入确证性结论。

用法：
  gen_corpus.py --seed 20261007            # 生成单个种子
  gen_corpus.py --all                      # 生成预注册的 5 个种子并更新 SHA256SUMS
  gen_corpus.py --check                    # 重新生成到内存并与 SHA256SUMS 比对（不写文件）
"""
import argparse
import importlib.util
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import corpus_c  # noqa: E402

PREREG_SEEDS = [20261007, 20261008, 20261009, 20261010, 20261011]
GENERATOR = "gen_corpus.py v1.0"
ENT_PATH = os.path.join(HERE, "entrustments.json")
OUT_DIR = os.path.join(HERE, "out")
GEN_DIR = os.path.join(EXP, "gen")

ENABLE, RECOMMEND, QUERY, CLAIM = 1, 2, 3, 4
OPERATOR, ADVISOR = 1, 2

F_CATS = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"]
L_CATS = ["L1", "L2", "L3", "L4", "L5"]


def load_oracle():
    """以文件路径加载草稿 oracle（生成器可以使用 oracle；门闩不得使用）。"""
    p = os.path.join(EXP, "oracle", "oracle.py")
    spec = importlib.util.spec_from_file_location("oracle_draft", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Gen:
    def __init__(self, seed, book_doc):
        self.r = random.Random(seed)
        self.doc = book_doc
        self.act = book_doc["actions"]
        self.recs = book_doc["entrustments"]
        self.cur = [e for e in self.recs if not e["superseded"]]
        self.enable_cur = [e for e in self.cur if "ENABLE_SIM" in e["allowed_actions"]]
        self.rec_cur = [e for e in self.cur if "RECOMMEND" in e["allowed_actions"]]
        self.used = set()

    # ---------- 基本采样 ----------
    def nonce(self):
        while True:
            n = self.r.randint(1, 2 ** 31 - 1)
            if n not in self.used:
                self.used.add(n)
                return n

    def u_nz(self):
        return self.r.randint(1, 255)

    def actions_of(self, e):
        return [self.act[a] for a in e["allowed_actions"]]

    def pick_action(self, e, p_enable=0.6):
        acts = self.actions_of(e)
        if ENABLE in acts and self.r.random() < p_enable:
            return ENABLE
        return self.r.choice(acts)

    def legal_zones(self, e):
        return sorted(set(e["allowed_zones"]) - set(e["forbidden_zones"]))

    def now_in(self, e, interior=False):
        if interior:
            return self.r.randint(e["t_start"] + 1, e["t_end"] - 1)
        return self.r.randint(e["t_start"], e["t_end"])

    def req(self, e, action=None, role=OPERATOR, origin=OPERATOR, zone=None, level=None,
            u=None, kind="target", ver=None, ent=None):
        if action is None:
            action = self.pick_action(e)
        if zone is None:
            zone = self.r.choice(self.legal_zones(e))
        if level is None:
            level = self.r.randint(0, e["sim_level_max"])
        if u is None:
            # 使能类必须 U 非空；非使能动作的 U 可为 0（检验 S-U1 不被过度适用）
            u = self.u_nz() if action in (ENABLE, CLAIM) or self.r.random() < 0.75 else 0
        return {"op": "EVAL", "kind": kind, "action": action, "role": role, "origin": origin,
                "ent": e["id"] if ent is None else ent, "ver": e["ver"] if ver is None else ver,
                "zone": zone, "level": level, "nonce": self.nonce(), "u": u}

    @staticmethod
    def grant(e):
        return {"op": "GRANT", "ent": e["id"], "ver": e["ver"]}

    @staticmethod
    def revoke(e=None):
        if e is None:
            return {"op": "REVOKE", "ent": 0, "ver": 0}
        return {"op": "REVOKE", "ent": e["id"], "ver": e["ver"]}

    @staticmethod
    def case(now, pre, tgt):
        return [{"op": "RESET"}, {"op": "CLOCK", "now": now}] + pre + [tgt]

    def versions(self, ent_id):
        return [e for e in self.recs if e["id"] == ent_id]

    # ---------- 假使命 F1–F9（返回 steps, 子型, 预期首个条款） ----------
    def F1(self, i):
        sub = ["over_by_1", "over_small", "over_large"][i % 3]
        e = self.r.choice(self.cur)
        d = {"over_by_1": 1, "over_small": self.r.randint(2, 20), "over_large": self.r.randint(500, 5000)}[sub]
        return self.case(e["t_end"] + d, [self.grant(e)], self.req(e)), sub, "S-T1"

    def F2(self, i):
        sub = ["early_by_1", "early_small", "early_large"][i % 3]
        e = self.r.choice(self.cur)
        d = {"early_by_1": 1, "early_small": self.r.randint(2, 20),
             "early_large": self.r.randint(21, e["t_start"])}[sub]
        return self.case(e["t_start"] - d, [self.grant(e)], self.req(e)), sub, "S-T2"

    def F3(self, i):
        e = self.r.choice(self.cur)
        z = self.r.choice(e["forbidden_zones"])
        site = z in self.doc["site_policy"]["forbidden_zones"]
        sub = "site_forbidden" if site else "entrustment_forbidden"
        return self.case(self.now_in(e), [self.grant(e)], self.req(e, zone=z)), sub, "S-Z1"

    def F4(self, i):
        e = self.r.choice(self.enable_cur)
        origin = self.r.choice([ADVISOR, OPERATOR])
        sub = "origin_advisor" if origin == ADVISOR else "origin_operator"
        return self.case(self.now_in(e), [self.grant(e)],
                         self.req(e, action=ENABLE, role=ADVISOR, origin=origin)), sub, "S-R1"

    def F5(self, i):
        e = self.r.choice(self.enable_cur)
        return self.case(self.now_in(e), [self.grant(e)],
                         self.req(e, action=ENABLE, role=OPERATOR, origin=ADVISOR)), "laundered", "S-P1"

    def F6(self, i):
        if i % 2 == 0:
            e = self.r.choice(self.cur)
            u = 0 if self.r.random() < 0.5 else self.u_nz()
            sub = "claim_u0" if u == 0 else "claim_u_nonzero"
            clause = "S-U1" if u == 0 else "S-U2"
            return self.case(self.now_in(e), [self.grant(e)], self.req(e, action=CLAIM, u=u)), sub, clause
        e = self.r.choice(self.enable_cur)
        return self.case(self.now_in(e), [self.grant(e)], self.req(e, action=ENABLE, u=0)), "enable_u0", "S-U1"

    def F7(self, i):
        sub = ["zone", "level", "action"][i % 3]
        if sub == "zone":
            cands = [e for e in self.cur if set(range(16)) - set(e["allowed_zones"]) - set(e["forbidden_zones"])]
            e = self.r.choice(cands)
            z = self.r.choice(sorted(set(range(16)) - set(e["allowed_zones"]) - set(e["forbidden_zones"])))
            return self.case(self.now_in(e), [self.grant(e)], self.req(e, zone=z)), "zone", "S-S1"
        if sub == "level":
            e = self.r.choice(self.cur)
            lv = self.r.randint(e["sim_level_max"] + 1, self.doc["sim_level_device_max"])
            return self.case(self.now_in(e), [self.grant(e)], self.req(e, level=lv)), "level", "S-S2"
        cands = [e for e in self.cur if {ENABLE, RECOMMEND, QUERY} - set(self.actions_of(e))]
        e = self.r.choice(cands)
        a = self.r.choice(sorted({ENABLE, RECOMMEND, QUERY} - set(self.actions_of(e))))
        return self.case(self.now_in(e), [self.grant(e)], self.req(e, action=a)), "action", "S-S3"

    def F8(self, i):
        sub = ["stale_bound", "bound_current", "both_bound"][i % 3]
        eid = self.r.choice([3, 6])
        vs = self.versions(eid)
        old = self.r.choice([v for v in vs if v["superseded"]])
        curv = [v for v in vs if not v["superseded"]][0]
        # 参数取自旧版本；一半用例刻意取"旧版允许、新版不允许"的强度（参数差）
        level = None
        if self.r.random() < 0.5 and old["sim_level_max"] > curv["sim_level_max"]:
            level = self.r.randint(curv["sim_level_max"] + 1, old["sim_level_max"])
        tgt = self.req(old, level=level)
        if sub == "stale_bound":
            pre, clause = [self.grant(old)], "S-V1"
        elif sub == "bound_current":
            pre, clause = [self.grant(curv)], "S-C2"
        else:
            pre = [self.grant(old), self.grant(curv)]
            self.r.shuffle(pre)
            clause = "S-V1"
        return self.case(self.now_in(old), pre, tgt), sub, clause

    def F9(self, i):
        sub = ["never_granted", "after_revoke", "bound_other"][i % 3]
        e = self.r.choice(self.enable_cur)
        if sub == "never_granted":
            pre, clause = [], "S-C1"
        elif sub == "after_revoke":
            pre = [self.grant(e), self.revoke(e if self.r.random() < 0.5 else None)]
            clause = "S-C1"
        else:
            other = self.r.choice([x for x in self.cur if x["id"] != e["id"]])
            pre, clause = [self.grant(other)], "S-C2"
        return self.case(self.now_in(e), pre, self.req(e, action=ENABLE)), sub, clause

    # ---------- 合法对照 L1–L5 ----------
    def L1(self, i):
        e = self.r.choice(self.cur)
        tgt = self.req(e, level=self.r.randint(0, e["sim_level_max"] - 1))
        return self.case(self.now_in(e, interior=True), [self.grant(e)], tgt), "nominal", ""

    def L2(self, i):
        sub = ["t_start", "t_end", "level_max", "level_zero", "zone_min", "zone_max"][i % 6]
        e = self.r.choice(self.cur)
        now = {"t_start": e["t_start"], "t_end": e["t_end"]}.get(sub, self.now_in(e))
        kw = {}
        if sub == "level_max":
            kw["level"] = e["sim_level_max"]
        elif sub == "level_zero":
            kw["level"] = 0
        elif sub == "zone_min":
            kw["zone"] = min(self.legal_zones(e))
        elif sub == "zone_max":
            kw["zone"] = max(self.legal_zones(e))
        return self.case(now, [self.grant(e)], self.req(e, **kw)), sub, ""

    def L3(self, i):
        e = self.r.choice(self.rec_cur)
        u = 0 if i % 3 == 0 else None
        tgt = self.req(e, action=RECOMMEND, role=ADVISOR, origin=ADVISOR, u=u)
        return self.case(self.now_in(e), [self.grant(e)], tgt), ("u0" if u == 0 else "u_any"), ""

    def L4(self, i):
        eid = self.r.choice([3, 6])
        vs = self.versions(eid)
        old = self.r.choice([v for v in vs if v["superseded"]])
        curv = [v for v in vs if not v["superseded"]][0]
        specific = self.r.random() < 0.5
        pre = [self.grant(old), self.revoke(old if specific else None), self.grant(curv)]
        sub = "revoke_specific" if specific else "revoke_all"
        return self.case(self.now_in(curv), pre, self.req(curv)), sub, ""

    def L5(self, i):
        tgt_e = self.r.choice(self.cur)
        others = [x for x in self.cur if x["id"] != tgt_e["id"]]
        k = self.r.choice([1, 2])
        chosen = self.r.sample(others, k)
        pre = [self.grant(x) for x in chosen + [tgt_e]]
        self.r.shuffle(pre)
        return self.case(self.now_in(tgt_e), pre, self.req(tgt_e)), "grants_%d" % (k + 1), ""

    # ---------- M1 格式错、X1 精确重放 ----------
    M1_SUBS = ["bad_action", "bad_role", "bad_origin", "zone_out", "level_out",
               "nonce_zero", "u_out_of_mask", "ver_zero", "unknown_ticket"]

    def M1(self, i):
        sub = self.M1_SUBS[i % len(self.M1_SUBS)]
        e = self.r.choice(self.enable_cur)
        t = self.req(e, action=ENABLE)
        clause = "S-F2"
        if sub == "bad_action":
            t["action"] = self.r.choice([0, 5, 9, 200]); clause = "S-F1"
        elif sub == "bad_role":
            t["role"] = self.r.choice([0, 3, 7]); clause = "S-F1"
        elif sub == "bad_origin":
            t["origin"] = self.r.choice([0, 3, 9]); clause = "S-F1"
        elif sub == "zone_out":
            t["zone"] = self.r.randint(16, 255)
        elif sub == "level_out":
            t["level"] = self.r.randint(1001, 60000)
        elif sub == "nonce_zero":
            t["nonce"] = 0
        elif sub == "u_out_of_mask":
            t["u"] = self.r.randint(256, 0xFFFF)
        elif sub == "ver_zero":
            t["ver"] = 0
        elif sub == "unknown_ticket":
            t["ent"] = self.r.choice([0] + list(range(9, 100))); clause = "S-F3"
        return self.case(self.now_in(e), [self.grant(e)], t), sub, clause

    def X1(self, i):
        e = self.r.choice(self.cur)
        s = self.req(e, kind="setup")
        t = dict(s)
        t["kind"] = "target"
        return self.case(self.now_in(e), [self.grant(e), s], t), "exact_replay", "S-N1"


def build(seed, oracle, book_doc, n_f=20, n_l=24, n_m1=10, n_x1=10):
    book = oracle.EntrustmentBook(ENT_PATH)
    g = Gen(seed, book_doc)
    plan = [(c, n_f) for c in F_CATS] + [(c, n_l) for c in L_CATS] + [("M1", n_m1), ("X1", n_x1)]
    cases, redraws = [], {}
    for cat, n in plan:
        fn = getattr(g, cat)
        want_gt = "MAY_PERMIT" if cat.startswith("L") else "MUST_DENY"
        for i in range(n):
            for attempt in range(200):
                steps, sub, clause = fn(i)
                c = {"steps": steps}
                o = oracle.evaluate_case(dict(c, case_id=0), book)
                ok = o["gt"] == want_gt and o["oracle_clause"] == clause
                if cat == "X1":
                    ok = ok and o["setup_expected"] == ["MAY_PERMIT"]
                if ok:
                    break
                redraws[cat] = redraws.get(cat, 0) + 1
            else:
                raise RuntimeError("cannot generate %s #%d" % (cat, i))
            cases.append({"name": "A-%s-%03d" % (cat, i + 1), "category": cat, "subtype": sub,
                          "intended_clause": clause, "steps": steps,
                          "gt": o["gt"], "oracle_clause": o["oracle_clause"],
                          "oracle_reason": o["oracle_reason"],
                          "oracle_all_clauses": o["oracle_all_clauses"]})
    g.r.shuffle(cases)  # 打乱顺序：用例编号不携带类别信息
    for k, c in enumerate(cases, 1):
        c["case_id"] = k
    book_sha = corpus_c.sha256_hex(open(ENT_PATH, "rb").read())
    return {
        "schema": "mission-se-corpus/v1",
        "corpus_id": "seed-%d" % seed,
        "corpus_set": "author_A",
        "seed": seed,
        "generator": GENERATOR,
        "entrustments_sha256": book_sha,
        "draft_notice": "GT from DRAFT oracle (pending independent labeller review); author corpus A = setup/manipulation check only; not confirmatory.",
        "plan": {c: n for c, n in plan},
        "redraws": redraws,
        "cases": cases,
    }


def emit(doc, write=True):
    jb = corpus_c.canonical_json_bytes(doc)
    jsha = corpus_c.sha256_hex(jb)
    hb = corpus_c.corpus_header(doc, jsha)
    base = "corpus_%d" % doc["seed"] if doc.get("seed") else doc["corpus_id"]
    if write:
        os.makedirs(OUT_DIR, exist_ok=True)
        corpus_c.write_bytes(os.path.join(OUT_DIR, base + ".json"), jb)
        corpus_c.write_bytes(os.path.join(OUT_DIR, base + ".h"), hb)
    return {base + ".json": jsha, base + ".h": corpus_c.sha256_hex(hb)}


def emit_entrustments(write=True):
    raw = open(ENT_PATH, "rb").read()
    hb = corpus_c.entrustments_header(json.loads(raw.decode("utf-8")), corpus_c.sha256_hex(raw))
    if write:
        os.makedirs(GEN_DIR, exist_ok=True)
        corpus_c.write_bytes(os.path.join(GEN_DIR, "entrustments_gen.h"), hb)
    return {"../../gen/entrustments_gen.h": corpus_c.sha256_hex(hb),
            "../entrustments.json": corpus_c.sha256_hex(raw)}


def read_sums():
    p = os.path.join(OUT_DIR, "SHA256SUMS")
    d = {}
    if os.path.exists(p):
        for line in open(p, encoding="ascii"):
            if line.strip():
                h, name = line.split()
                d[name] = h
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description="作者语料 A 生成器（确定性）")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true", help="生成预注册的 5 个种子并重写 SHA256SUMS")
    ap.add_argument("--check", action="store_true", help="内存中重新生成并与 SHA256SUMS 比对")
    ap.add_argument("--n-f", type=int, default=20)
    ap.add_argument("--n-l", type=int, default=24)
    ap.add_argument("--n-m1", type=int, default=10)
    ap.add_argument("--n-x1", type=int, default=10)
    a = ap.parse_args(argv)
    oracle = load_oracle()
    book_doc = json.load(open(ENT_PATH, encoding="utf-8"))
    seeds = PREREG_SEEDS if (a.all or a.check) else [a.seed]
    if seeds == [None]:
        ap.error("需要 --seed、--all 或 --check")
    write = not a.check
    sums = dict(emit_entrustments(write))
    for s in seeds:
        doc = build(s, oracle, book_doc, a.n_f, a.n_l, a.n_m1, a.n_x1)
        sums.update(emit(doc, write))
        print("seed %d: %d cases, redraws=%s" % (s, len(doc["cases"]), doc["redraws"]))
    if a.check:
        old = read_sums()
        bad = [k for k, v in sums.items() if old.get(k) != v]
        for k in bad:
            print("MISMATCH %s: frozen=%s regenerated=%s" % (k, old.get(k), sums[k]))
        print("check: %s" % ("OK" if not bad else "FAILED"))
        return 1 if bad else 0
    if a.all:
        old = read_sums()
        old.update(sums)
        with open(os.path.join(OUT_DIR, "SHA256SUMS"), "w", encoding="ascii", newline="\n") as f:
            for k in sorted(old):
                f.write("%s  %s\n" % (old[k], k))
    return 0


if __name__ == "__main__":
    sys.exit(main())
