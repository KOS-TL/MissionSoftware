#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
门闩单元测试（实验方案 §2.3 "B 的测试套件" 与 §2.4 "M 的测试" 的最小实现）

- 每条用例给出 B / B+ / M 三个条件各自的预期 (判决, 理由码)；覆盖 B-1…B-5 每条至少一正一反、
  B+ 的两条全局规则、M-1…M-7 各谓词，以及闭区间边界。
- 运行方式：用 hostsim（gcc 本机编译 + microkit 桩）执行。【主机模拟、非 QEMU 实测】
  这些测试只验证判决逻辑与日志格式，不参与语料评分。
用法：python3 tests/run_unit_tests.py
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "corpus"))
import corpus_c  # noqa: E402

A_OK, D = ("ALLOW", "ok"), "DENY"


def ev(kind="target", action=1, role=1, origin=1, ent=1, ver=1, zone=2, level=100, nonce=None, u=1):
    return {"op": "EVAL", "kind": kind, "action": action, "role": role, "origin": origin, "ent": ent,
            "ver": ver, "zone": zone, "level": level, "nonce": nonce, "u": u}


G = lambda e, v=1: {"op": "GRANT", "ent": e, "ver": v}  # noqa: E731
RV = lambda e=0, v=0: {"op": "REVOKE", "ent": e, "ver": v}  # noqa: E731

# (名称, now, 步骤, 预期 {B, Bplus, M})；M 的放行写作 ALLOW，比较时映射为 ALLOW_SIM
UNIT = [
    ("合法名义请求（B-1…B-5 正例）", 150, [G(1), ev()], {"B": A_OK, "Bplus": A_OK, "M": A_OK}),
    ("B-1 反例：动作枚举 9", 150, [G(1), ev(action=9)], {k: (D, "invalid_enum") for k in ("B", "Bplus", "M")}),
    ("B-1 反例：角色 3", 150, [G(1), ev(role=3)], {k: (D, "invalid_enum") for k in ("B", "Bplus", "M")}),
    ("B-2 反例：区 16", 150, [G(1), ev(zone=16)], {k: (D, "invalid_range") for k in ("B", "Bplus", "M")}),
    ("B-2 反例：nonce 0", 150, [G(1), ev(nonce=0)], {k: (D, "invalid_range") for k in ("B", "Bplus", "M")}),
    ("B-2 正例边界：强度 1000（设备上限；超出 E5 托付上限）", 300, [G(5), ev(ent=5, zone=1, level=1000)],
     {"B": A_OK, "Bplus": A_OK, "M": (D, "scope_drift_level")}),
    ("B-3 反例：工单 42 不存在", 150, [G(1), ev(ent=42)], {k: (D, "unknown_ticket") for k in ("B", "Bplus", "M")}),
    ("B-4 反例：顾问直接使能", 150, [G(1), ev(role=2, origin=2)], {k: (D, "role_forbidden") for k in ("B", "Bplus", "M")}),
    ("B-4 正例：顾问 RECOMMEND", 150, [G(1), ev(action=2, role=2, origin=2)], {"B": A_OK, "Bplus": A_OK, "M": A_OK}),
    ("B-5 反例：重复 nonce", 150, [G(1), ev(kind="setup", nonce=4242), ev(nonce=4242)],
     {k: (D, "duplicate_nonce") for k in ("B", "Bplus", "M")}),
    ("M-1 反例：无共签", 150, [ev()], {"B": A_OK, "Bplus": A_OK, "M": (D, "no_human_cosign")}),
    ("M-1 反例：共签绑定另一托付", 200, [G(2), ev()], {"B": A_OK, "Bplus": A_OK, "M": (D, "cosign_binding_mismatch")}),
    ("M-1 正例：撤销不存在的绑定不影响已有共签", 150, [G(1), RV(2, 1), ev()], {"B": A_OK, "Bplus": A_OK, "M": A_OK}),
    ("M-2 反例 / B+ 全局窗反例：E7 过期且越出站点窗", 2001, [G(7), ev(ent=7, zone=13)],
     {"B": A_OK, "Bplus": (D, "global_window_violation"), "M": (D, "expired_entrustment")}),
    ("M-2 反例：E1 过期但在站点窗内（B+ 拦不住）", 201, [G(1), ev()],
     {"B": A_OK, "Bplus": A_OK, "M": (D, "expired_entrustment")}),
    ("M-2 反例：E4 未生效", 499, [G(4), ev(ent=4, zone=9)], {"B": A_OK, "Bplus": A_OK, "M": (D, "entrustment_not_yet_valid")}),
    ("M-3 反例 / B+ 站点禁区反例：区 7", 150, [G(1), ev(zone=7)],
     {"B": A_OK, "Bplus": (D, "global_forbidden_zone"), "M": (D, "forbidden_zone")}),
    ("M-3 反例：托付禁区 8（非站点禁区，B+ 拦不住）", 150, [G(3, 2), ev(ent=3, ver=2, zone=8)],
     {"B": A_OK, "Bplus": A_OK, "M": (D, "forbidden_zone")}),
    ("M-4 反例：区越界", 150, [G(1), ev(zone=5)], {"B": A_OK, "Bplus": A_OK, "M": (D, "scope_drift_zone")}),
    ("M-4 反例：动作越界", 200, [G(2), ev(ent=2, zone=4)], {"B": A_OK, "Bplus": A_OK, "M": (D, "scope_drift_action")}),
    ("M-5 反例：共签与请求都是被取代的 E3v1", 150, [G(3, 1), ev(ent=3, ver=1, zone=1, level=250)],
     {"B": A_OK, "Bplus": A_OK, "M": (D, "stale_entrustment_version")}),
    ("M-6 反例：顾问意见经操作员转述的使能", 150, [G(1), ev(origin=2)], {"B": A_OK, "Bplus": A_OK, "M": (D, "advisor_cannot_enable")}),
    ("M-7 反例：声称达成（U 非空）", 150, [G(1), ev(action=4, u=5)], {"B": A_OK, "Bplus": A_OK, "M": (D, "achievement_not_claimable")}),
    ("M-7 反例：使能且 U 为空", 150, [G(1), ev(u=0)], {"B": A_OK, "Bplus": A_OK, "M": (D, "empty_U_no_achieve_tag")}),
    ("M-7 正例：RECOMMEND 的 U 可为 0", 150, [G(1), ev(action=2, u=0)], {"B": A_OK, "Bplus": A_OK, "M": A_OK}),
    ("闭区间边界：E5 now=t_start=50、区 0、强度=上限", 50, [G(5), ev(ent=5, zone=0, level=600)], {"B": A_OK, "Bplus": A_OK, "M": A_OK}),
    ("闭区间边界：E1 now=t_end=200、区 3、强度=上限", 200, [G(1), ev(zone=3, level=300)], {"B": A_OK, "Bplus": A_OK, "M": A_OK}),
    ("重新托付：撤销 E3v1、改授 E3v2 后按 v2 请求", 150, [G(3, 1), RV(), G(3, 2), ev(ent=3, ver=2, zone=6, level=200)],
     {"B": A_OK, "Bplus": A_OK, "M": A_OK}),
]

VARIANT_DEFS = {"B": "-DGATE_VARIANT_B", "Bplus": "-DGATE_VARIANT_BPLUS", "M": "-DGATE_VARIANT_M"}


def build_doc():
    cases, nonce = [], 7000000
    for k, (name, now, steps, exp) in enumerate(UNIT, 1):
        st = [{"op": "RESET"}, {"op": "CLOCK", "now": now}]
        for s in steps:
            s = dict(s)
            if s["op"] == "EVAL" and s["nonce"] is None:
                nonce += 3
                s["nonce"] = nonce
            st.append(s)
        cases.append({"case_id": 100 + k, "name": name, "steps": st})
    return {"corpus_id": "unit_tests", "generator": "run_unit_tests.py", "cases": cases}


def main():
    doc = build_doc()
    hb = corpus_c.corpus_header(doc, corpus_c.sha256_hex(corpus_c.canonical_json_bytes(doc)))
    fails = total = 0
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "corpus_active.h"), "wb").write(hb)
        cf = ["-O2", "-Wall", "-Werror", "-Wno-unused-function", "-I" + os.path.join(EXP, "hostsim"), "-I" + EXP]
        for var, d in VARIANT_DEFS.items():
            exe = os.path.join(td, "sim_" + var)
            subprocess.check_call(["gcc"] + cf + [d, "-Dinit=gk_init", "-Dnotified=gk_notified", "-Dprotected=gk_protected",
                                                  "-c", os.path.join(EXP, "gatekeeper_field.c"), "-o", exe + "_g.o"])
            subprocess.check_call(["gcc"] + cf + ["-I" + td, "-Dinit=client_init", "-Dnotified=client_notified",
                                                  "-c", os.path.join(EXP, "client_corpus.c"), "-o", exe + "_c.o"])
            subprocess.check_call(["gcc"] + cf + ["-c", os.path.join(EXP, "hostsim", "hostsim.c"), "-o", exe + "_h.o"])
            subprocess.check_call(["gcc", exe + "_g.o", exe + "_c.o", exe + "_h.o", "-o", exe])
            out = subprocess.check_output([exe]).decode()
            got = {int(m.group(1)): (m.group(2), m.group(3))
                   for m in re.finditer(r"^CASE\|id=(\d+)\|kind=target\|verdict=(\w+)\|reason=([\w\-]+)$", out, re.M)}
            for k, (name, _, _, exp) in enumerate(UNIT, 1):
                want = exp[var]
                if var == "M" and want[0] == "ALLOW":
                    want = ("ALLOW_SIM", want[1])
                total += 1
                if got.get(100 + k) != want:
                    fails += 1
                    print("FAIL [%s] %s: got %s want %s" % (var, name, got.get(100 + k), want))
    print("unit tests（主机模拟、非 QEMU 实测）: %d/%d passed (%d cases x 3 variants)" % (total - fails, total, len(UNIT)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
