# -*- coding: utf-8 -*-
"""
语料 → C 头文件写出器（gen_corpus.py 与 holdout_draft.py 共用）。

注意：本模块只做"格式转换"，不含任何判定逻辑；生成的头文件只携带请求字段，
不携带类别、子型、真值或理由码（门闩与客户端都看不到真值）。
"""
import hashlib
import json

STEP_OP = {"RESET": 1, "CLOCK": 2, "GRANT": 3, "REVOKE": 4, "EVAL": 5}
STEP_KIND = {"target": 0, "setup": 1}


def canonical_json_bytes(doc):
    """确定性序列化：排序键、ASCII 转义、LF 换行。SHA-256 基于该字节串。"""
    return (json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii")


def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()


def write_bytes(path, b):
    with open(path, "wb") as f:
        f.write(b)


def corpus_header(doc, json_sha):
    lines = [
        "/* 自动生成，请勿手改。生成器：experiment/corpus/%s */" % doc.get("generator", "?").split()[0],
        "/* 语料：%s；JSON SHA-256：%s */" % (doc["corpus_id"], json_sha),
        "/* 本头文件只含请求字段；不含类别、真值或理由码。非临床·仅仿真。 */",
        "#pragma once",
        '/* 使用前须先包含 proto_fields.h */',
        "",
        '#define CORPUS_ID "%s"' % doc["corpus_id"],
        '#define CORPUS_JSON_SHA256 "%s"' % json_sha,
        "#define CORPUS_N_CASES %du" % len(doc["cases"]),
    ]
    rows = []
    for c in doc["cases"]:
        for s in c["steps"]:
            op = STEP_OP[s["op"]]
            if s["op"] == "EVAL":
                rows.append("  {%du, %d, %d, %d, %d, %d, %du, %du, %du, %du, %du, %du, 0u}," % (
                    c["case_id"], op, STEP_KIND[s["kind"]], s["action"], s["role"], s["origin"],
                    s["ent"], s["ver"], s["zone"], s["level"], s["nonce"], s["u"]))
            elif s["op"] == "CLOCK":
                rows.append("  {%du, %d, 1, 0, 0, 0, 0u, 0u, 0u, 0u, 0u, 0u, %du}," % (c["case_id"], op, s["now"]))
            elif s["op"] in ("GRANT", "REVOKE"):
                rows.append("  {%du, %d, 1, 0, 0, 0, %du, %du, 0u, 0u, 0u, 0u, 0u}," % (
                    c["case_id"], op, s.get("ent", 0), s.get("ver", 0)))
            else:
                rows.append("  {%du, %d, 1, 0, 0, 0, 0u, 0u, 0u, 0u, 0u, 0u, 0u}," % (c["case_id"], op))
    lines.append("#define CORPUS_N_STEPS %du" % len(rows))
    lines.append("")
    lines.append("static const corpus_step_t corpus_steps[CORPUS_N_STEPS] = {")
    lines += rows
    lines.append("};")
    lines.append("")
    return ("\n".join(lines)).encode("utf-8")


def entrustments_header(book_doc, book_sha):
    act = book_doc["actions"]
    w0, w1 = book_doc["site_policy"]["window"]
    t_min = min(r["t_start"] for r in book_doc["entrustments"])
    t_max = max(r["t_end"] for r in book_doc["entrustments"])
    assert (w0, w1) == (t_min, t_max), "site_policy.window 必须等于全表 [min t_start, max t_end]"
    site = book_doc["site_policy"]["forbidden_zones"]
    for r in book_doc["entrustments"]:
        assert set(site) <= set(r["forbidden_zones"]), "站点禁区必须被每条托付禁止"
    site_mask = 0
    for z in site:
        site_mask |= 1 << z
    ids = sorted({r["id"] for r in book_doc["entrustments"]})
    lines = [
        "/* 自动生成，请勿手改。来源：experiment/corpus/entrustments.json（SHA-256：%s） */" % book_sha,
        "/* 托付表（门闩持有）；种子无关。非临床·仅仿真。 */",
        "#pragma once",
        '/* 使用前须先包含 proto_fields.h */',
        "",
        "#define ENT_TABLE_N %du" % len(book_doc["entrustments"]),
        "#define ENT_ID_MAX %du" % max(ids),
        "/* B+ 的全局领域规则（非按托付）：站点运行时间窗与站点禁区 */",
        "#define GLOBAL_T_MIN %du" % w0,
        "#define GLOBAL_T_MAX %du" % w1,
        "#define SITE_FORBIDDEN_MASK 0x%04xu" % site_mask,
        "",
        "static const entrustment_t ent_table[ENT_TABLE_N] = {",
    ]
    for r in book_doc["entrustments"]:
        am = 0
        for a in r["allowed_actions"]:
            am |= 1 << act[a]
        zm = sum(1 << z for z in r["allowed_zones"])
        fm = sum(1 << z for z in r["forbidden_zones"])
        lines.append("  {%du, %du, %du, %du, 0x%04xu, 0x%04xu, %du, 0x%02xu, %du}," % (
            r["id"], r["ver"], r["t_start"], r["t_end"], zm, fm, r["sim_level_max"], am, 1 if r["superseded"] else 0))
    lines.append("};")
    lines.append("")
    return ("\n".join(lines)).encode("utf-8")
