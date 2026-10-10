#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参考判定器 oracle.py（oracle_spec v0.1 的草稿实现）

【草稿·待独立标注人复核；不计入确证性结论】
  - 本文件由作者依据 rules_spec.md 起草，仅用于装置自检与生成器复核。
  - 按实验方案 §3.5，验证性真值必须由独立标注人依据 rules_spec.md **独立重写**本文件。
  - 独立性约束：本文件只读取语料 JSON 与 entrustments.json；不导入、不解析任何门闩源码
    （gatekeeper*.c）或生成的 C 头文件，与门闩实现无共享逻辑。

非临床 · 仅仿真 · 交付 != 达成。

用法：
  oracle.py label   --corpus C.json [--entrustments E.json] [--out labels.csv]
  oracle.py compare --corpus C.json --results results_M.csv [--out disagreements.md]
  oracle.py selftest
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ENT = os.path.join(HERE, "..", "corpus", "entrustments.json")

# 条款优先级表：(条款号, 理由码)。顺序即 rules_spec.md §4 的优先级，冻结后不得静默修改。
CLAUSE_ORDER = [
    ("S-F1", "invalid_enum"),
    ("S-F2", "invalid_range"),
    ("S-F3", "unknown_ticket"),
    ("S-R1", "role_forbidden"),
    ("S-N1", "duplicate_nonce"),
    ("S-C1", "no_human_cosign"),
    ("S-C2", "cosign_binding_mismatch"),
    ("S-E0", "unknown_entrustment_version"),
    ("S-T1", "expired_entrustment"),
    ("S-T2", "entrustment_not_yet_valid"),
    ("S-Z1", "forbidden_zone"),
    ("S-S1", "scope_drift_zone"),
    ("S-S2", "scope_drift_level"),
    ("S-S3", "scope_drift_action"),
    ("S-V1", "stale_entrustment_version"),
    ("S-P1", "advisor_cannot_enable"),
    ("S-U1", "empty_U_no_achieve_tag"),
    ("S-U2", "achievement_not_claimable"),
]
REASON_OF = dict(CLAUSE_ORDER)


class EntrustmentBook:
    """托付表的只读视图（来自 entrustments.json）。"""

    def __init__(self, path=DEFAULT_ENT):
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        self.doc = doc
        self.action_code = doc["actions"]                      # 名称 -> 编号
        self.action_name = {v: k for k, v in doc["actions"].items()}
        self.n_zones = doc["zones"]
        self.level_max = doc["sim_level_device_max"]
        self.u_valid = doc["u_mask_valid"]
        self.ver_min = doc["ent_ver_min"]
        self.records = {}
        self.ids = set()
        for r in doc["entrustments"]:
            self.records[(r["id"], r["ver"])] = r
            self.ids.add(r["id"])

    def get(self, ent_id, ver):
        return self.records.get((ent_id, ver))


class CaseState:
    """用例内状态：逻辑时钟、共签绑定集合、nonce 历史（rules_spec.md §3）。"""

    CAPACITY = 4

    def __init__(self):
        self.now = 0
        self.bindings = []      # 保持插入顺序的 (id, ver) 列表
        self.nonces = []
        self.spec_gap_notes = []

    def apply(self, step):
        op = step["op"]
        if op == "RESET":
            self.__init__()
        elif op == "CLOCK":
            self.now = int(step["now"])
        elif op == "GRANT":
            key = (int(step["ent"]), int(step["ver"]))
            if key not in self.bindings:
                if len(self.bindings) >= self.CAPACITY:
                    self.spec_gap_notes.append("cosign_capacity_exceeded")
                else:
                    self.bindings.append(key)
        elif op == "REVOKE":
            key = (int(step.get("ent", 0)), int(step.get("ver", 0)))
            if key == (0, 0):
                self.bindings = []
            elif key in self.bindings:
                self.bindings.remove(key)
        elif op == "EVAL":
            pass  # 请求步骤由调用方单独评估
        else:
            raise ValueError("unknown step op: %r" % op)


def violated_clauses(req, st, book):
    """返回目标请求违反的全部条款（按优先级排序）。只读取请求字段、托付表与用例状态。"""
    a, role, origin = req["action"], req["role"], req["origin"]
    eid, ver = req["ent"], req["ver"]
    zone, level, nonce, u = req["zone"], req["level"], req["nonce"], req["u"]

    ENABLE = book.action_code["ENABLE_SIM"]
    CLAIM = book.action_code["CLAIM_ACHIEVE"]
    is_enable_class = a in (ENABLE, CLAIM)
    delegable = {book.action_code[n] for n in ("ENABLE_SIM", "RECOMMEND", "QUERY_STATUS")}

    bad = set()
    if a not in book.action_name or role not in (1, 2) or origin not in (1, 2):
        bad.add("S-F1")
    if (zone >= book.n_zones or level > book.level_max or nonce == 0
            or (u & ~book.u_valid) != 0 or ver < book.ver_min):
        bad.add("S-F2")
    if eid not in book.ids:
        bad.add("S-F3")
    if is_enable_class and role != 1:
        bad.add("S-R1")
    if nonce != 0 and nonce in st.nonces:
        bad.add("S-N1")
    if not st.bindings:
        bad.add("S-C1")
    elif (eid, ver) not in st.bindings:
        bad.add("S-C2")
    rec = book.get(eid, ver)
    if rec is None:
        bad.add("S-E0")
    else:
        if st.now > rec["t_end"]:
            bad.add("S-T1")
        if st.now < rec["t_start"]:
            bad.add("S-T2")
        if zone in rec["forbidden_zones"]:
            bad.add("S-Z1")
        if zone not in rec["allowed_zones"]:
            bad.add("S-S1")
        if level > rec["sim_level_max"]:
            bad.add("S-S2")
        allowed = {book.action_code[n] for n in rec["allowed_actions"]}
        if a in delegable and a not in allowed:
            bad.add("S-S3")
        if rec["superseded"]:
            bad.add("S-V1")
    if is_enable_class and origin != 1:
        bad.add("S-P1")
    if a in (ENABLE, CLAIM) and u == 0:
        bad.add("S-U1")
    if a == CLAIM and u != 0:
        bad.add("S-U2")
    return [c for c, _ in CLAUSE_ORDER if c in bad]


def evaluate_case(case, book):
    """回放用例脚本；返回目标请求的真值字典。前置请求的预期结果一并给出（不评分）。"""
    st = CaseState()
    setup_outcomes = []
    target = None
    for step in case["steps"]:
        if step["op"] != "EVAL":
            st.apply(step)
            continue
        clauses = violated_clauses(step, st, book)
        outcome = {
            "gt": "MUST_DENY" if clauses else "MAY_PERMIT",
            "oracle_clause": clauses[0] if clauses else "",
            "oracle_reason": REASON_OF[clauses[0]] if clauses else "ok",
            "oracle_all_clauses": clauses,
        }
        if step["nonce"] != 0:
            st.nonces.append(step["nonce"])
        if step["kind"] == "target":
            if target is not None:
                raise ValueError("case %s has more than one target" % case.get("case_id"))
            target = outcome
        else:
            setup_outcomes.append(outcome["gt"])
    if target is None:
        raise ValueError("case %s has no target step" % case.get("case_id"))
    target["setup_expected"] = setup_outcomes
    target["spec_gap_auto"] = bool(st.spec_gap_notes)
    return target


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cmd_label(args):
    book = EntrustmentBook(args.entrustments)
    corpus = load_json(args.corpus)
    out = open(args.out, "w", newline="", encoding="utf-8") if args.out else sys.stdout
    w = csv.writer(out)
    w.writerow(["case_id", "name", "gt", "oracle_clause", "oracle_reason", "oracle_all_clauses"])
    for c in corpus["cases"]:
        r = evaluate_case(c, book)
        w.writerow([c["case_id"], c.get("name", ""), r["gt"], r["oracle_clause"],
                    r["oracle_reason"], ";".join(r["oracle_all_clauses"])])
    if args.out:
        out.close()
    return 0


def cmd_compare(args):
    """比较 oracle 与某次门闩运行（parse_serial.py parse 的输出）的判决与理由码。"""
    book = EntrustmentBook(args.entrustments)
    corpus = load_json(args.corpus)
    res = {}
    with open(args.results, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            res[int(row["case_id"])] = row
    n = agree_v = agree_r = 0
    rows = []
    for c in corpus["cases"]:
        cid = c["case_id"]
        r = evaluate_case(c, book)
        g = res.get(cid)
        n += 1
        if g is None:
            rows.append((cid, c.get("name", ""), c.get("category", ""), r["gt"], "MISSING", r["oracle_reason"], "-"))
            continue
        gv = "MAY_PERMIT" if g["verdict"] == "PERMIT" else ("MUST_DENY" if g["verdict"] == "DENY" else "INVALID")
        ok_v = gv == r["gt"]
        ok_r = g["reason"] == r["oracle_reason"]
        agree_v += ok_v
        agree_r += ok_v and ok_r
        if not (ok_v and ok_r):
            rows.append((cid, c.get("name", ""), c.get("category", ""), r["gt"], g["verdict"], r["oracle_reason"], g["reason"]))
    lines = ["# oracle（草稿）与门闩判决比对", "",
             "> 草稿·待独立标注人复核；不计入确证性结论。", "",
             "- 用例数：%d" % n,
             "- 判决一致：%d（%.2f%%）" % (agree_v, 100.0 * agree_v / max(n, 1)),
             "- 判决与理由码均一致：%d（%.2f%%）" % (agree_r, 100.0 * agree_r / max(n, 1)),
             "- 不一致条目：%d" % len(rows), ""]
    if rows:
        lines += ["| case_id | 名称 | 类别 | oracle 真值 | 门闩判决 | oracle 理由 | 门闩理由 |", "|---|---|---|---|---|---|---|"]
        lines += ["| %s | %s | %s | %s | %s | %s | %s |" % r for r in rows]
    text = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    return 0 if not rows else 1


def cmd_selftest(args):
    """用实验方案附录 A 的若干代表性用例做最小自检（以本表中的 E1/E2/E3 对应）。"""
    book = EntrustmentBook(args.entrustments)

    def ev(**kw):
        d = dict(op="EVAL", kind="target", action=1, role=1, origin=1, ent=1, ver=1,
                 zone=2, level=100, nonce=11, u=1)
        d.update(kw)
        return d

    def case(now, pre, tgt):
        return {"case_id": 0, "steps": [{"op": "RESET"}, {"op": "CLOCK", "now": now}] + pre + [tgt]}

    g = {"op": "GRANT", "ent": 1, "ver": 1}
    checks = [
        (case(150, [g], ev()), "MAY_PERMIT", "ok"),
        (case(201, [g], ev()), "MUST_DENY", "expired_entrustment"),
        (case(200, [g], ev(zone=3, level=300)), "MAY_PERMIT", "ok"),
        (case(100, [g], ev(zone=1, level=0)), "MAY_PERMIT", "ok"),
        (case(99, [g], ev(zone=1)), "MUST_DENY", "entrustment_not_yet_valid"),
        (case(150, [g], ev(zone=7, level=50)), "MUST_DENY", "forbidden_zone"),
        (case(150, [g], ev(role=2, origin=2)), "MUST_DENY", "role_forbidden"),
        (case(150, [g], ev(origin=2)), "MUST_DENY", "advisor_cannot_enable"),
        (case(150, [g], ev(action=4, u=0)), "MUST_DENY", "empty_U_no_achieve_tag"),
        (case(150, [g], ev(action=4, u=3)), "MUST_DENY", "achievement_not_claimable"),
        (case(150, [g], ev(u=0)), "MUST_DENY", "empty_U_no_achieve_tag"),
        (case(150, [g], ev(zone=5)), "MUST_DENY", "scope_drift_zone"),
        (case(150, [g], ev(level=301)), "MUST_DENY", "scope_drift_level"),
        (case(150, [{"op": "GRANT", "ent": 2, "ver": 1}], ev(ent=2, zone=4)), "MUST_DENY", "scope_drift_action"),
        (case(150, [{"op": "GRANT", "ent": 3, "ver": 2}], ev(ent=3, ver=1, level=280)), "MUST_DENY", "cosign_binding_mismatch"),
        (case(150, [{"op": "GRANT", "ent": 3, "ver": 1}], ev(ent=3, ver=1, level=280)), "MUST_DENY", "stale_entrustment_version"),
        (case(150, [], ev()), "MUST_DENY", "no_human_cosign"),
        (case(150, [g, {"op": "REVOKE", "ent": 0, "ver": 0}], ev()), "MUST_DENY", "no_human_cosign"),
        (case(150, [{"op": "GRANT", "ent": 2, "ver": 1}], ev()), "MUST_DENY", "cosign_binding_mismatch"),
        (case(150, [g], ev(role=2, origin=2, action=2)), "MAY_PERMIT", "ok"),
        (case(150, [g], ev(zone=16)), "MUST_DENY", "invalid_range"),
        (case(150, [g], ev(action=9)), "MUST_DENY", "invalid_enum"),
        (case(150, [g, ev(kind="setup", nonce=77)], ev(nonce=77)), "MUST_DENY", "duplicate_nonce"),
    ]
    fails = 0
    for i, (c, gt, reason) in enumerate(checks):
        r = evaluate_case(c, book)
        if r["gt"] != gt or r["oracle_reason"] != reason:
            fails += 1
            print("selftest #%d FAIL: got %s/%s want %s/%s" % (i, r["gt"], r["oracle_reason"], gt, reason))
    print("oracle selftest: %d/%d passed" % (len(checks) - fails, len(checks)))
    return 1 if fails else 0


def main(argv=None):
    p = argparse.ArgumentParser(description="参考判定器（草稿·待独立标注人复核）")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("label", "compare", "selftest"):
        sp = sub.add_parser(name)
        sp.add_argument("--entrustments", default=DEFAULT_ENT)
        if name in ("label", "compare"):
            sp.add_argument("--corpus", required=True)
            sp.add_argument("--out")
        if name == "compare":
            sp.add_argument("--results", required=True)
    args = p.parse_args(argv)
    return {"label": cmd_label, "compare": cmd_compare, "selftest": cmd_selftest}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
