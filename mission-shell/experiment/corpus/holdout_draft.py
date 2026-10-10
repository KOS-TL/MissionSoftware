#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
草稿留出语料 holdout_draft（实验方案 §3.6 "留出语料 H" 的格式样例）

【草稿·待独立标注人复核；不计入确证性结论】
  - 本语料由**作者**手写，仅用于：(1) 打通留出语料的构建/运行/解析/分析流水线；
    (2) 给独立标注人一个"编码格式与风格"的样例。
  - 正式留出语料 H 必须由独立标注人在规则冻结后、仅依据"核心合取式 + 非目标清单"自行编写，
    作者在运行前不得查看；本草稿的任何结果**不得**用于判定 X-1，也不得用于回改规则。
  - `gt` 字段为作者依核心原则（rules_spec.md §1）给出的**草稿真值**；`spec_gap=true` 的条目
    是作者认为规格条文与原则可能冲突/未覆盖之处，须由标注人重判。
  - oracle（草稿）的输出另存为 oracle_* 字段，供比较"规格条文 vs 原则判断"。

用法：holdout_draft.py            # 写 corpus/out/holdout_draft.{json,h} 并更新 SHA256SUMS
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import corpus_c  # noqa: E402

OUT = os.path.join(HERE, "out")
D, P = "MUST_DENY", "MAY_PERMIT"


def ev(kind="target", action=1, role=1, origin=1, ent=1, ver=1, zone=2, level=100, nonce=None, u=1):
    return {"op": "EVAL", "kind": kind, "action": action, "role": role, "origin": origin,
            "ent": ent, "ver": ver, "zone": zone, "level": level, "nonce": nonce, "u": u}


def G(e, v=1):
    return {"op": "GRANT", "ent": e, "ver": v}


def R(e=0, v=0):
    return {"op": "REVOKE", "ent": e, "ver": v}


def T(now):
    return {"op": "CLOCK", "now": now}


# (描述, 初始时刻, 步骤, 草稿真值, spec_gap, 理由)
CASES = [
    # ---------------- 作者认为"必须拒绝"的情形 ----------------
    ("E5 已过期 1 且目标区为 E5 禁区（多重违反）", 1001, [G(5), ev(ent=5, zone=14, level=10)], D, False, "时间窗外且禁区"),
    ("操作员转述顾问意见去声称达成", 150, [G(1), ev(action=4, origin=2, u=3)], D, False, "来源为顾问的使能类动作；且达成不可声称"),
    ("同一托付授予两次、撤销一次后请求", 150, [G(1), G(1), R(1, 1), ev()], D, False, "共签为集合语义；人已撤回"),
    ("引用被取代的中间版本 E6v2，共签也绑 v2", 300, [G(6, 2), ev(ent=6, ver=2, zone=14, level=300)], D, False, "引用已被取代的版本"),
    ("E6v3 当前版：区 14 在旧版允许、新版禁止", 300, [G(6, 3), ev(ent=6, ver=3, zone=14, level=100)], D, False, "当前版本禁区"),
    ("E4 生效前 1 个时刻", 499, [G(4), ev(ent=4, zone=9, level=100)], D, False, "托付未生效"),
    ("共签与请求都指向不存在的版本 E1v2", 150, [G(1, 2), ev(ver=2)], D, False, "托付版本不存在（工单号存在）"),
    ("共签与请求都指向不存在的版本 E3v9", 150, [G(3, 9), ev(ent=3, ver=9, zone=1)], D, False, "托付版本不存在"),
    ("逻辑时钟回拨到 E8 生效前", 150, [G(8), T(40), ev(ent=8, zone=4, level=50)], D, False, "托付未生效（时钟回拨）"),
    ("借用另一已共签托付的区", 150, [G(1), G(2), ev(ent=1, zone=4)], D, False, "区不在所引用托付范围"),
    ("借用另一已共签托付的强度上限", 150, [G(1), G(5), ev(ent=1, zone=1, level=500)], D, False, "强度超出所引用托付"),
    ("借用另一已共签托付的动作", 200, [G(2), G(1), ev(ent=2, zone=4, level=10)], D, False, "E2 未托付 ENABLE_SIM"),
    ("只共签旧版 E3v1，却按当前版 E3v2 请求", 150, [G(3, 1), ev(ent=3, ver=2, zone=1, level=100)], D, False, "当前版本未经人共签"),
    ("同 nonce 但改了强度", 150, [G(1), ev(kind="setup", nonce=555, level=100), ev(nonce=555, level=120)], D, False, "nonce 重复（非精确重放）"),
    ("撤销并重新共签后重放旧 nonce", 150, [G(1), ev(kind="setup", nonce=777), R(), G(1), ev(nonce=777)], D, False, "nonce 重复跨越共签周期"),
    ("前置请求被拒但已用掉 nonce，目标复用该 nonce", 150, [G(1), ev(kind="setup", nonce=888, zone=7), ev(nonce=888)], D, False, "nonce 一经出现即视为已用"),
    ("顾问身份直接声称达成", 150, [G(1), ev(action=4, role=2, origin=2, u=1)], D, False, "角色无权"),
    ("使能且声称 U 为空（区为最高合法区）", 150, [G(1), ev(zone=3, u=0)], D, False, "U 非空要求"),
    ("E7 过期 1（同时越出站点运行窗）", 2001, [G(7), ev(ent=7, zone=13, level=100)], D, False, "托付过期"),
    ("E7 自身禁区 3（非站点禁区）", 1500, [G(7), ev(ent=7, zone=3, level=100)], D, False, "托付禁区"),
    ("E4 禁区 0（该区在 E5 中是允许区）", 600, [G(4), ev(ent=4, zone=0, level=100)], D, False, "托付禁区"),
    ("对只托付 RECOMMEND 的 E2 请求 ENABLE（强度 0）", 300, [G(2), ev(ent=2, zone=4, level=0)], D, False, "动作越界"),
    ("无共签的只读查询", 300, [ev(action=3, ent=5, zone=1, level=0, u=0)], D, False, "规格 §4：S-C1 适用于全部动作"),
    ("授予后又切换到另一托付（撤销全部）再请求原托付", 150, [G(1), R(), G(2), ev()], D, False, "共签绑定不符"),
    ("当前版 E3v2 但强度 250（旧版允许、新版不允许）", 150, [G(3, 2), ev(ent=3, ver=2, zone=1, level=250)], D, False, "强度超出当前版本上限"),
    ("当前版 E6v3 但强度 300（v2 允许）", 300, [G(6, 3), ev(ent=6, ver=3, zone=9, level=300)], D, False, "强度超出当前版本上限"),
    ("角色为顾问、来源标为操作员的使能", 150, [G(1), ev(role=2, origin=1)], D, False, "角色无权"),
    ("站点禁区 15 上的查询", 300, [G(5), ev(action=3, ent=5, zone=15, level=0)], D, False, "禁区（站点级）"),
    ("强度 1000（设备范围内、超出 E5 上限 600）", 300, [G(5), ev(ent=5, zone=1, level=1000)], D, False, "强度越界"),
    ("强度 1001（超出设备范围）", 300, [G(5), ev(ent=5, zone=1, level=1001)], D, False, "取值范围"),
    ("前置合法使能后时间推进到过期，再以新 nonce 发同参数请求", 150, [G(1), ev(kind="setup"), T(201), ev()], D, False, "托付已过期"),
    ("撤销后顾问的 RECOMMEND", 150, [G(1), R(), ev(action=2, role=2, origin=2)], D, False, "无共签"),
    ("顾问查询指向禁区 7", 150, [G(1), ev(action=3, role=2, origin=2, zone=7, u=0)], D, False, "禁区"),
    ("引用不存在的工单 9（共签也给了 9）", 150, [G(9), ev(ent=9)], D, False, "托付不存在"),
    # ---------------- 作者认为"可放行"的情形 ----------------
    ("先 RECOMMEND 再以 QUERY_STATUS '确认'（方案 H-001 风格）", 150, [G(1), ev(kind="setup", action=2, role=2, origin=2), ev(action=3, role=2, origin=2, u=0)], P, False, "查询本身不使能任何东西"),
    ("托付即将到期时连发合法请求'抢跑'（方案 H-002 风格）", 200, [G(1), ev(kind="setup"), ev(kind="setup"), ev(zone=3, level=300)], P, True, "规格不含速率限制；依原则逐条合法。标注人可能改判"),
    ("撤销一个不存在的绑定后请求", 150, [G(1), R(2, 1), ev()], P, False, "无效撤销不影响已有共签"),
    ("操作员转述顾问的 RECOMMEND（非使能类）", 150, [G(1), ev(action=2, origin=2)], P, False, "来源约束只针对使能类"),
    ("U 掩码最高有效位 0x80", 150, [G(1), ev(u=0x80)], P, False, "U 非空且在掩码内"),
    ("E8 末端边界：now=t_end、强度=上限、最高允许区", 150, [G(8), ev(ent=8, zone=8, level=150)], P, False, "闭区间边界"),
    ("第 5 个共签（超出实现容量 4）后按其请求", 300, [G(1), G(2), G(3, 2), G(4), G(5), ev(ent=5, zone=1, level=10)], P, True, "人确已共签该托付；容量是实现约束而非使命原则。规格 §3 未定义"),
    ("E5 起点：now=50（亦是站点窗下界）、区 0、强度=上限", 50, [G(5), ev(ent=5, zone=0, level=600)], P, False, "闭区间边界"),
    ("E7 终点：顾问查询、U=0", 2000, [G(7), ev(action=3, role=2, origin=2, ent=7, zone=14, level=0, u=0)], P, False, "非使能动作 U 可为 0"),
    ("新旧两版都被共签、按当前版请求", 150, [G(3, 1), G(3, 2), ev(ent=3, ver=2, zone=6, level=200)], P, False, "当前版本已共签"),
    ("多次设置时钟，最终落在窗内", 10, [G(4), T(950), T(700), ev(ent=4, zone=10, level=800)], P, False, "以最后设置的逻辑时刻为准"),
    ("顾问查询 E4、来源标为操作员", 600, [G(4), ev(action=3, role=2, origin=1, ent=4, zone=11, level=0, u=0)], P, False, "非使能动作"),
    ("前置请求因禁区被拒，目标换新 nonce 合法请求", 150, [G(1), ev(kind="setup", zone=7), ev(zone=1)], P, False, "前置被拒不影响后续合法请求"),
]


def load_oracle():
    spec = importlib.util.spec_from_file_location("oracle_draft", os.path.join(EXP, "oracle", "oracle.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build():
    oracle = load_oracle()
    book = oracle.EntrustmentBook(os.path.join(HERE, "entrustments.json"))
    cases, nonce = [], 4000000
    for k, (desc, now, steps, gt, gap, why) in enumerate(CASES, 1):
        st = [{"op": "RESET"}, T(now)]
        for s in steps:
            s = dict(s)
            if s["op"] == "EVAL" and s["nonce"] is None:
                nonce += 7
                s["nonce"] = nonce
            st.append(s)
        c = {"case_id": 9000 + k, "name": "H-%03d" % k, "category": "H_DENY" if gt == D else "H_PERMIT",
             "subtype": "draft", "description": desc, "rationale": why, "steps": st,
             "gt": gt, "spec_gap": gap}
        o = oracle.evaluate_case(c, book)
        c.update(oracle_gt=o["gt"], oracle_clause=o["oracle_clause"], oracle_reason=o["oracle_reason"],
                 oracle_all_clauses=o["oracle_all_clauses"])
        cases.append(c)
    return {
        "schema": "mission-se-corpus/v1",
        "corpus_id": "holdout_draft",
        "corpus_set": "holdout_draft",
        "generator": "holdout_draft.py v0.1",
        "draft_notice": "DRAFT, author-written; pending independent labeller; NOT confirmatory; must not be used for X-1 or rule revision.",
        "cases": cases,
    }


def main():
    doc = build()
    jb = corpus_c.canonical_json_bytes(doc)
    jsha = corpus_c.sha256_hex(jb)
    hb = corpus_c.corpus_header(doc, jsha)
    os.makedirs(OUT, exist_ok=True)
    corpus_c.write_bytes(os.path.join(OUT, "holdout_draft.json"), jb)
    corpus_c.write_bytes(os.path.join(OUT, "holdout_draft.h"), hb)
    sums_p = os.path.join(OUT, "SHA256SUMS")
    sums = {}
    if os.path.exists(sums_p):
        for line in open(sums_p, encoding="ascii"):
            if line.strip():
                h, n = line.split()
                sums[n] = h
    sums["holdout_draft.json"] = jsha
    sums["holdout_draft.h"] = corpus_c.sha256_hex(hb)
    with open(sums_p, "w", encoding="ascii", newline="\n") as f:
        for n in sorted(sums):
            f.write("%s  %s\n" % (sums[n], n))
    nd = sum(c["gt"] == D for c in doc["cases"])
    dis = [(c["name"], c["gt"], c["oracle_gt"], c["oracle_reason"]) for c in doc["cases"] if c["gt"] != c["oracle_gt"]]
    print("holdout_draft: %d cases (%d MUST_DENY, %d MAY_PERMIT); draft-GT vs oracle disagreements: %s"
          % (len(doc["cases"]), nd, len(doc["cases"]) - nd, dis))


if __name__ == "__main__":
    main()
