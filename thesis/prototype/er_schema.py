#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【示意性原型 / illustrative prototype —— 非实验树的一部分，不参与预注册实验】
托付记录 schema 草案 "mission-se-entrustment-record/v0-draft"（拟定）与向实验托付表
experiment/corpus/entrustments.json（schema "mission-se-entrustments/v1"）的降维映射。

只读引用实验树：<仓库根>/mission-shell/experiment（可用环境变量 MISSION_EXP 覆盖）（不写入任何文件）。
"""
import json
import os
import sys
sys.dont_write_bytecode = True  # 不在只读引用的实验树内写 __pycache__

EXP = os.environ.get("MISSION_EXP", os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mission-shell", "experiment")))
EXP_ENT = os.path.join(EXP, "corpus", "entrustments.json")

# v0 草案中被门闩逐条执行的字段 -> entrustments.json 字段（一一对应）
ENFORCED_MAP = {
    ("id",): "id",
    ("version", "ver"): "ver",
    ("version", "superseded"): "superseded",
    ("validity", "t_start"): "t_start",
    ("validity", "t_end"): "t_end",
    ("scope", "allowed_zones"): "allowed_zones",
    ("scope", "forbidden_zones"): "forbidden_zones",
    ("scope", "sim_level_max"): "sim_level_max",
    ("scope", "allowed_actions"): "allowed_actions",
}
# v0 草案中门闩不按记录执行、只作文档/追溯用途的字段（进入显式未覆盖集 U）
NOT_ENFORCED = [("entrustor",), ("trustee",), ("purpose",), ("version", "supersedes"),
                ("accountability",), ("evidence",)]


def _get(d, path):
    for k in path:
        d = d[k]
    return d


def to_v1_record(rec):
    out = {}
    for path, key in ENFORCED_MAP.items():
        out[key] = _get(rec, path)
    return out


def validate(doc):
    """最小结构校验（拟定规则）。返回错误列表。"""
    errs = []
    seen = set()
    for r in doc["records"]:
        k = (r["id"], r["version"]["ver"])
        if k in seen:
            errs.append("duplicate %s" % (k,))
        seen.add(k)
        v, s = r["validity"], r["scope"]
        if v["t_start"] > v["t_end"]:
            errs.append("%s: t_start > t_end" % (k,))
        if set(s["allowed_zones"]) & set(s["forbidden_zones"]):
            errs.append("%s: allowed ∩ forbidden ≠ ∅（禁区优先，但草案要求显式不相交）" % (k,))
        if not all(0 <= z < 16 for z in s["allowed_zones"] + s["forbidden_zones"]):
            errs.append("%s: zone out of 0..15" % (k,))
        if "CLAIM_ACHIEVE" in s["allowed_actions"]:
            errs.append("%s: CLAIM_ACHIEVE 不可托付（交付≠达成）" % (k,))
        if r["accountability"].get("enable_requires_origin") != "OPERATOR":
            errs.append("%s: 使能来源必须为 OPERATOR（全局规则 S-P1）" % (k,))
    return errs


def to_v1_entrustments(doc):
    return [to_v1_record(r) for r in doc["records"]]


def main(argv):
    path = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(__file__), "entrustment_records_v0.example.json")
    doc = json.load(open(path, encoding="utf-8"))
    errs = validate(doc)
    print("validate: %d error(s)" % len(errs))
    for e in errs:
        print("  ", e)
    exp = json.load(open(EXP_ENT, encoding="utf-8"))["entrustments"]
    mine = to_v1_entrustments(doc)
    norm = lambda L: sorted(json.dumps(x, sort_keys=True) for x in L)  # noqa: E731
    same = norm(mine) == norm(exp)
    print("mapped %d records; identical to experiment entrustments.json records: %s" % (len(mine), same))
    return 0 if (not errs and same) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
