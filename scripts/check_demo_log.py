#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/check_demo_log.py LOG —— 按 SRS §6.2 关键词合取核对 DEMO_PROFILE=full 的串口日志。
退出码 0 = PASS，1 = FAIL。rc=124（timeout 终止 QEMU）是预期收工方式，不判失败。"""
import re
import sys

EXPECTED_EVENTS = ["gate_init", "no_human_cosign", "cosign_grant", "legal_path_sim", "expired_entrustment",
                   "forbidden_zone", "advisor_cannot_enable", "empty_U_no_achieve_tag", "cosign_revoke",
                   "no_human_cosign"]
EXPECTED_TIP, EXPECTED_LEN = "80488a97", 10


def main(path):
    text = open(path, encoding="utf-8", errors="replace").read().replace("\r", "")
    lines = text.split("\n")
    checks = []
    checks.append(("剖面声明 DEMO_PROFILE=full", any(l.strip() == "DEMO_PROFILE=full" for l in lines) or "profile=full" in text))
    checks.append(("GATE|COSIGN|STATE=OFF", "GATE|COSIGN|STATE=OFF" in text))
    checks.append(("GATE|COSIGN|GRANT", "GATE|COSIGN|GRANT" in text))
    checks.append(("GATE|COSIGN|STATE=ON", "GATE|COSIGN|STATE=ON" in text))
    checks.append(("GATE|ALLOW_SIM|legal_path_sim + NOTE", "GATE|ALLOW_SIM|legal_path_sim" in text and "GATE|NOTE|" in text))
    for r in ("expired_entrustment", "forbidden_zone", "advisor_cannot_enable", "empty_U_no_achieve_tag"):
        checks.append(("GATE|DENY|" + r, "GATE|DENY|" + r in text))
    checks.append(("GATE|COSIGN|REVOKE", "GATE|COSIGN|REVOKE" in text))
    ev = [m.groups() for m in re.finditer(r"^EVIDENCE\|seq=(\d+)\|prev=([0-9a-f]{8})\|this=([0-9a-f]{8})\|(\S+)$", text, re.M)]
    names = [e[3] for e in ev]
    checks.append(("10 个证据事件且顺序正确", names == EXPECTED_EVENTS))
    chained = all(ev[i][1] == (ev[i - 1][2] if i else "00000000") for i in range(len(ev)))
    checks.append(("证据链 prev/this 首尾相接", bool(ev) and chained))
    checks.append(("GATE|CHAIN|tip=%s|len=%d" % (EXPECTED_TIP, EXPECTED_LEN),
                   "GATE|CHAIN|tip=%s|len=%d" % (EXPECTED_TIP, EXPECTED_LEN) in text))
    checks.append(("CLIENT|INFO|MISSION_SHELL_DEMO_DONE", "CLIENT|INFO|MISSION_SHELL_DEMO_DONE" in text))
    ok = True
    for name, res in checks:
        print("%-4s %s" % ("PASS" if res else "FAIL", name))
        ok &= bool(res)
    m = re.search(r"=== QEMU done rc=(\d+) ===", text)
    if m:
        print("INFO QEMU rc=%s%s" % (m.group(1), "（timeout 终止，属预期）" if m.group(1) == "124" else ""))
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
