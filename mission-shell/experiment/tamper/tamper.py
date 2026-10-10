#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
离线证据篡改轨道 T1–T7（实验方案 §3.4）

篡改**不在 seL4 内进行**：在主机上对已采集串口日志的**副本**施加变换，再由
verify-chain（M：FNV-1a32 链）或 verify-seq（B/B+：普通序号审计日志）检测。

| 编号 | 篡改 | 攻击者模型 |
|---|---|---|
| T1 | 修改某条事件文本（DENY:<理由> → 放行:ok），不动序号/哈希 | 朴素 |
| T2 | 删除中间一条，不重编号 | 朴素 |
| T3 | 交换相邻两条 | 朴素 |
| T4 | 在中间插入一条伪造行（M：随机哈希；B：序号取前一条+1，后续不重编号） | 朴素 |
| T5 | 截尾：删除最后 k 条（k∈[1,5]）及 GATE|CHAIN / GATE|AUDIT_END 行 | 朴素 |
| T6 | 删除中间一条并重新编号后续序号，同步更新日志内长度 | 知情 |
| T7 | 修改一条事件后重算其后整条 FNV 链并更新日志内 tip（B：仅修改文本） | 知情（知道算法；无密钥） |

预先声明（见 expectations.json 与 prereg.md）：T5（无外部锚点）与 T7 在 M 上**预期不检出**——
教学级 FNV-1a32 链无密钥、非抗碰撞，只提供"顺序追加可复核"语义；这是 U（未覆盖项）的佐证，不是缺陷修复对象。
"""
import re

EVID_RE = re.compile(r"^EVIDENCE\|seq=(\d+)\|prev=([0-9a-f]{8})\|this=([0-9a-f]{8})\|(.+?)\s*$")
AUDIT_RE = re.compile(r"^AUDIT\|seq=(\d+)\|(.+?)\s*$")
CHAIN_RE = re.compile(r"^GATE\|CHAIN\|tip=([0-9a-f]{8})\|len=(\d+)\s*$")
AUDIT_END_RE = re.compile(r"^GATE\|AUDIT_END\|len=(\d+)\s*$")


def fnv1a_step(prev, seq, event):
    h = 2166136261
    for b in prev.to_bytes(4, "little") + (seq & 0xFFFFFFFF).to_bytes(4, "little") + event.encode("ascii", "replace"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _fmt_m(seq, prev, this, event):
    return "EVIDENCE|seq=%d|prev=%08x|this=%08x|%s" % (seq, prev, this, event)


def _fmt_b(seq, event):
    return "AUDIT|seq=%d|%s" % (seq, event)


def _index(lines):
    """返回 (格式, 证据行下标列表, 解析结果列表)。"""
    ev_m = [(i, EVID_RE.match(l)) for i, l in enumerate(lines)]
    ev_m = [(i, m) for i, m in ev_m if m]
    if ev_m:
        return "M", [i for i, _ in ev_m], [(int(m.group(1)), int(m.group(2), 16), int(m.group(3), 16), m.group(4)) for _, m in ev_m]
    ev_b = [(i, AUDIT_RE.match(l)) for i, l in enumerate(lines)]
    ev_b = [(i, m) for i, m in ev_b if m]
    return "B", [i for i, _ in ev_b], [(int(m.group(1)), None, None, m.group(2)) for _, m in ev_b]


def _forge_event(event, fmt):
    """把一条拒绝事件改写为放行事件；若不是拒绝事件则改写理由码末字符。"""
    permit = "ALLOW_SIM" if fmt == "M" else "ALLOW"
    m = re.match(r"^(c\d+:\w+:)DENY:[\w\-]+$", event)
    if m:
        return m.group(1) + permit + ":ok"
    return event[:-1] + ("x" if event[-1] != "x" else "y")


def _pick_deny(rng, parsed, lo, hi):
    cands = [k for k in range(lo, hi) if ":DENY:" in parsed[k][3]]
    return rng.choice(cands) if cands else rng.randrange(lo, hi)


def _set_len_lines(lines, new_len, new_tip=None):
    out = []
    for l in lines:
        m = CHAIN_RE.match(l)
        if m:
            tip = int(m.group(1), 16) if new_tip is None else new_tip
            out.append("GATE|CHAIN|tip=%08x|len=%d" % (tip, new_len))
            continue
        if AUDIT_END_RE.match(l):
            out.append("GATE|AUDIT_END|len=%d" % new_len)
            continue
        out.append(l)
    return out


def tamper(lines, kind, rng):
    """返回 (篡改后日志行列表, 元数据)。不修改输入。"""
    lines = list(lines)
    fmt, idx, parsed = _index(lines)
    n = len(idx)
    if n < 6:
        raise ValueError("too few evidence lines to tamper")
    info = {"kind": kind, "format": fmt}

    if kind == "T1":
        k = _pick_deny(rng, parsed, 1, n - 1)
        seq, prev, this, ev = parsed[k]
        new_ev = _forge_event(ev, fmt)
        lines[idx[k]] = _fmt_m(seq, prev, this, new_ev) if fmt == "M" else _fmt_b(seq, new_ev)
        info.update(pos_seq=seq, before=ev, after=new_ev)

    elif kind == "T2":
        k = rng.randrange(1, n - 1)
        info.update(pos_seq=parsed[k][0], deleted=lines[idx[k]])
        del lines[idx[k]]

    elif kind == "T3":
        k = rng.randrange(1, n - 2)
        a, b = idx[k], idx[k + 1]
        lines[a], lines[b] = lines[b], lines[a]
        info.update(pos_seq=parsed[k][0])

    elif kind == "T4":
        k = rng.randrange(1, n - 1)
        seq, prev, this, ev = parsed[k]
        forged_ev = "c%d:target:%s:ok" % (rng.randint(1, 9999), "ALLOW_SIM" if fmt == "M" else "ALLOW")
        if fmt == "M":
            forged = _fmt_m(seq + 1, this, rng.getrandbits(32), forged_ev)
        else:
            forged = _fmt_b(seq + 1, forged_ev)
        lines.insert(idx[k] + 1, forged)
        info.update(pos_seq=seq + 1, inserted=forged)

    elif kind == "T5":
        kk = rng.randint(1, 5)
        drop = set(idx[n - kk:])
        lines = [l for i, l in enumerate(lines)
                 if i not in drop and not CHAIN_RE.match(l) and not AUDIT_END_RE.match(l)]
        info.update(truncated=kk)

    elif kind == "T6":
        k = rng.randrange(1, n - 1)
        info.update(pos_seq=parsed[k][0])
        for j in range(k + 1, n):
            seq, prev, this, ev = parsed[j]
            lines[idx[j]] = _fmt_m(seq - 1, prev, this, ev) if fmt == "M" else _fmt_b(seq - 1, ev)
        del lines[idx[k]]
        lines = _set_len_lines(lines, n - 1)

    elif kind == "T7":
        k = _pick_deny(rng, parsed, 1, n - 1)
        seq, prev, this, ev = parsed[k]
        new_ev = _forge_event(ev, fmt)
        info.update(pos_seq=seq, before=ev, after=new_ev)
        if fmt == "B":
            lines[idx[k]] = _fmt_b(seq, new_ev)
        else:
            tip = prev
            for j in range(k, n):
                s, _, _, e = parsed[j]
                e = new_ev if j == k else e
                h = fnv1a_step(tip, s, e)
                lines[idx[j]] = _fmt_m(s, tip, h, e)
                tip = h
            lines = _set_len_lines(lines, n, new_tip=tip)
    else:
        raise ValueError(kind)
    return lines, info
