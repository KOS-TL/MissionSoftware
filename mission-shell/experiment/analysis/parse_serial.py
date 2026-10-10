#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
串口日志解析 / 校验 / 篡改 / 评分（实验方案附录 B 的接口实现）

子命令：
  parse        --log RUN.log [--log SHARD2.log ...] --corpus corpus.json [--condition C] --out results.csv
  verify-chain --log RUN.log [--anchor tip=<hex>,len=<n> | --anchor-from-log ORIG.log]   # M：重算 FNV-1a32
  verify-seq   --log RUN.log                                                             # B/B+：序号连续性
  tamper       --log RUN.log --kind {T1..T7} --n 20 --seed S --outdir tampered/
  score        --results results.csv --corpus corpus.json --out confusion.csv
  determinism  --logs r1.log r2.log [r3.log ...]                                          # 比较 CASE| 行
退出码：0=通过；2=INVALID（缺 CORPUS_DONE / 用例缺判决 / 重复判决 / 回执不一致）；3=链或序号校验失败

只使用 Python 标准库。非临床 · 仅仿真 · 交付 != 达成。
"""
import argparse
import csv
import importlib.util
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Literal, Optional, Tuple

Verdict = Literal["PERMIT", "DENY", "INVALID"]

CASE_RE = re.compile(r"^CASE\|id=(\d+)\|kind=target\|verdict=(ALLOW_SIM|ALLOW|DENY)\|reason=([\w\-]+)\s*$")
EVID_RE = re.compile(r"^EVIDENCE\|seq=(\d+)\|prev=([0-9a-f]{8})\|this=([0-9a-f]{8})\|(.+?)\s*$")
AUDIT_RE = re.compile(r"^AUDIT\|seq=(\d+)\|(.+?)\s*$")
CHAIN_RE = re.compile(r"^GATE\|CHAIN\|tip=([0-9a-f]{8})\|len=(\d+)\s*$")
AUDIT_END_RE = re.compile(r"^GATE\|AUDIT_END\|len=(\d+)\s*$")
REP_RE = re.compile(r"^CLIENT\|REP\|case=(\d+)\|label=(\w+)\s*$")
DONE_RE = re.compile(r"^CLIENT\|INFO\|CORPUS_DONE\|n=(\d+)\s*$")
VARIANT_RE = re.compile(r"^GATE\|INFO\|field gatekeeper variant=(\w+)\|ablate=(\w+)\s*$")
RUN_END_RE = re.compile(r"^RUN\|END\|status=(\w+)")

EXIT_OK, EXIT_INVALID, EXIT_CHAIN = 0, 2, 3


class InvalidRun(Exception):
    pass


@dataclass(frozen=True)
class CaseResult:
    case_id: int
    raw_verdict: str          # ALLOW / ALLOW_SIM / DENY
    verdict: Verdict          # 归一化：ALLOW 与 ALLOW_SIM → PERMIT
    reason: str
    line_no: int


@dataclass(frozen=True)
class EvidenceLine:
    seq: int
    prev: int
    this: int
    event: str
    line_no: int


@dataclass
class ChainReport:
    ok: bool
    length: int
    tip: int
    first_bad_line: Optional[int]
    problem: Optional[str]    # "hash_mismatch" | "prev_link" | "seq_gap" | "anchor_mismatch" | "empty"


def read_lines(path) -> List[str]:
    with open(path, "rb") as f:
        raw = f.read().decode("utf-8", errors="replace")
    return [ln.rstrip("\r\n").replace("\r", "") for ln in raw.split("\n")]


def fnv1a_step(prev: int, seq: int, event: str) -> int:
    """与 gatekeeper.c / gatekeeper_field.c 的 fnv1a_step 逐字节一致：prev(LE 4B) ‖ seq(LE 4B) ‖ event 字节。"""
    h = 2166136261
    for b in prev.to_bytes(4, "little") + (seq & 0xFFFFFFFF).to_bytes(4, "little") + event.encode("ascii", "replace"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def condition_from_log(lines) -> Optional[str]:
    for ln in lines:
        m = VARIANT_RE.match(ln)
        if m:
            v, a = m.group(1), m.group(2)
            return v if a == "none" else "%s-%s" % (v, a)
    return None


def parse_cases(lines: List[str]) -> Dict[int, CaseResult]:
    """每个 case_id 恰好一条 CASE 行；重复 → InvalidRun。"""
    out: Dict[int, CaseResult] = {}
    for i, ln in enumerate(lines, 1):
        m = CASE_RE.match(ln)
        if not m:
            continue
        cid, raw, reason = int(m.group(1)), m.group(2), m.group(3)
        if cid in out:
            raise InvalidRun("duplicate CASE line for id=%d (line %d)" % (cid, i))
        out[cid] = CaseResult(cid, raw, "DENY" if raw == "DENY" else "PERMIT", reason, i)
    return out


def check_completeness(lines: List[str], cases: Dict[int, CaseResult]):
    """必须见到 CORPUS_DONE；RUN|END 若存在必须为 done；客户端回执须与门闩判决一致。"""
    done = [DONE_RE.match(ln) for ln in lines]
    done = [m for m in done if m]
    if not done:
        raise InvalidRun("missing CLIENT|INFO|CORPUS_DONE")
    for ln in lines:
        m = RUN_END_RE.match(ln)
        if m and m.group(1) != "done":
            raise InvalidRun("RUN|END status=%s" % m.group(1))
    n_done = int(done[-1].group(1))
    if n_done != len(cases):
        raise InvalidRun("CORPUS_DONE n=%d but %d CASE lines" % (n_done, len(cases)))
    reps = {}
    for ln in lines:
        m = REP_RE.match(ln)
        if m:
            reps[int(m.group(1))] = m.group(2)
    for cid, c in cases.items():
        if reps.get(cid) != c.raw_verdict:
            raise InvalidRun("client receipt mismatch for case %d: gate=%s client=%s" % (cid, c.raw_verdict, reps.get(cid)))


def parse_evidence(lines: List[str]) -> List[EvidenceLine]:
    ev = []
    for i, ln in enumerate(lines, 1):
        m = EVID_RE.match(ln)
        if m:
            ev.append(EvidenceLine(int(m.group(1)), int(m.group(2), 16), int(m.group(3), 16), m.group(4), i))
    return ev


def internal_anchor(lines) -> Optional[Tuple[int, int]]:
    for ln in reversed(lines):
        m = CHAIN_RE.match(ln)
        if m:
            return int(m.group(1), 16), int(m.group(2))
    return None


def verify_chain(ev: List[EvidenceLine], anchor: Optional[Tuple[int, int]] = None,
                 log_anchor: Optional[Tuple[int, int]] = None) -> ChainReport:
    """自创世 prev=0 起逐条重算；检查 seq 连续、prev 链接、this 重算一致；
    可选外部锚点 anchor=(tip,len)；log_anchor 为日志内 GATE|CHAIN 行（若存在则一并核对）。"""
    if not ev:
        return ChainReport(False, 0, 0, None, "empty")
    tip, expect_seq = 0, 1
    for e in ev:
        if e.seq != expect_seq:
            return ChainReport(False, expect_seq - 1, tip, e.line_no, "seq_gap")
        if e.prev != tip:
            return ChainReport(False, expect_seq - 1, tip, e.line_no, "prev_link")
        h = fnv1a_step(e.prev, e.seq, e.event)
        if h != e.this:
            return ChainReport(False, expect_seq - 1, tip, e.line_no, "hash_mismatch")
        tip, expect_seq = h, expect_seq + 1
    n = expect_seq - 1
    for a in (log_anchor, anchor):
        if a is not None and (a[0] != tip or a[1] != n):
            return ChainReport(False, n, tip, ev[-1].line_no, "anchor_mismatch")
    return ChainReport(True, n, tip, None, None)


def verify_seq_lines(lines: List[str]) -> ChainReport:
    seqs, lnos = [], []
    for i, ln in enumerate(lines, 1):
        m = AUDIT_RE.match(ln)
        if m:
            seqs.append(int(m.group(1)))
            lnos.append(i)
    end_len = None
    for ln in reversed(lines):
        m = AUDIT_END_RE.match(ln)
        if m:
            end_len = int(m.group(1))
            break
    return verify_seq(seqs, lnos, end_len)


def verify_seq(audit_seqs: List[int], line_nos: Optional[List[int]] = None, end_len: Optional[int] = None) -> ChainReport:
    """B 的普通审计日志：序号须为 1..n 连续递增；若日志内有 AUDIT_END 行则长度一致。"""
    if not audit_seqs:
        return ChainReport(False, 0, 0, None, "empty")
    line_nos = line_nos or list(range(1, len(audit_seqs) + 1))
    for k, s in enumerate(audit_seqs):
        if s != k + 1:
            return ChainReport(False, k, 0, line_nos[k], "seq_gap")
    if end_len is not None and end_len != len(audit_seqs):
        return ChainReport(False, len(audit_seqs), 0, line_nos[-1], "anchor_mismatch")
    return ChainReport(True, len(audit_seqs), 0, None, None)


def load_tamper_module():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tamper", "tamper.py")
    spec = importlib.util.spec_from_file_location("tamper_mod", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load_corpus(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def score(results: Dict[int, CaseResult], corpus: dict) -> List[dict]:
    """输出列：case_id, name, category, subtype, gt, verdict, reason, oracle_clause, oracle_reason,
    reason_matches, outcome(TP/FN/FP/TN/INVALID)。正类 = MUST_DENY（"应拒"）。"""
    rows = []
    for c in corpus["cases"]:
        r = results.get(c["case_id"])
        v = r.verdict if r else "INVALID"
        gt = c["gt"]
        if v == "INVALID":
            oc = "INVALID"
        elif gt == "MUST_DENY":
            oc = "TP" if v == "DENY" else "FN"
        else:
            oc = "FP" if v == "DENY" else "TN"
        rows.append({
            "case_id": c["case_id"], "name": c.get("name", ""), "category": c.get("category", ""),
            "subtype": c.get("subtype", ""), "gt": gt, "verdict": v, "reason": r.reason if r else "",
            "oracle_clause": c.get("oracle_clause", ""), "oracle_reason": c.get("oracle_reason", ""),
            "reason_matches": int(bool(r) and r.reason == c.get("oracle_reason", "")),
            "spec_gap": int(bool(c.get("spec_gap", False))), "outcome": oc,
        })
    return rows


def read_results_csv(path) -> Dict[int, CaseResult]:
    out = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = int(row["case_id"])
            out[cid] = CaseResult(cid, row["raw_verdict"], row["verdict"], row["reason"], int(row["line_no"]))
    return out


# ---------------- 子命令 ----------------
def cmd_parse(a):
    corpus = load_corpus(a.corpus)
    want = {c["case_id"] for c in corpus["cases"]}
    merged: Dict[int, CaseResult] = {}
    cond = None
    try:
        for path in a.log:
            lines = read_lines(path)
            cases = parse_cases(lines)
            check_completeness(lines, cases)
            c = condition_from_log(lines)
            if cond is not None and c != cond:
                raise InvalidRun("shards from different conditions: %s vs %s" % (cond, c))
            cond = c
            for cid, r in cases.items():
                if cid in merged:
                    raise InvalidRun("case %d appears in more than one shard" % cid)
                merged[cid] = r
        if a.condition and cond != a.condition:
            raise InvalidRun("log condition %s != requested %s" % (cond, a.condition))
        missing = sorted(want - set(merged))
        extra = sorted(set(merged) - want)
        if missing or extra:
            raise InvalidRun("missing=%s extra=%s" % (missing[:10], extra[:10]))
    except InvalidRun as e:
        print("INVALID: %s" % e, file=sys.stderr)
        return EXIT_INVALID
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "raw_verdict", "verdict", "reason", "line_no", "condition"])
        for cid in sorted(merged):
            r = merged[cid]
            w.writerow([cid, r.raw_verdict, r.verdict, r.reason, r.line_no, cond])
    print("parsed %d cases, condition=%s -> %s" % (len(merged), cond, a.out))
    return EXIT_OK


def parse_anchor(s):
    d = dict(kv.split("=") for kv in s.split(","))
    return int(d["tip"], 16), int(d["len"])


def cmd_verify_chain(a):
    lines = read_lines(a.log)
    anchor = parse_anchor(a.anchor) if a.anchor else None
    if a.anchor_from_log:
        anchor = internal_anchor(read_lines(a.anchor_from_log))
    rep = verify_chain(parse_evidence(lines), anchor, internal_anchor(lines))
    print(json.dumps(asdict(rep)))
    return EXIT_OK if rep.ok else EXIT_CHAIN


def cmd_verify_seq(a):
    rep = verify_seq_lines(read_lines(a.log))
    print(json.dumps(asdict(rep)))
    return EXIT_OK if rep.ok else EXIT_CHAIN


def cmd_tamper(a):
    import random
    tm = load_tamper_module()
    lines = read_lines(a.log)
    rng = random.Random(a.seed)
    os.makedirs(a.outdir, exist_ok=True)
    meta = []
    for i in range(a.n):
        t_lines, info = tm.tamper(lines, a.kind, rng)
        p = os.path.join(a.outdir, "%s_%03d.log" % (a.kind, i))
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(t_lines) + "\n")
        info["file"] = os.path.basename(p)
        meta.append(info)
    with open(os.path.join(a.outdir, "%s_meta.json" % a.kind), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print("wrote %d %s variants to %s" % (a.n, a.kind, a.outdir))
    return EXIT_OK


def cmd_score(a):
    rows = score(read_results_csv(a.results), load_corpus(a.corpus))
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    agg = {}
    for r in rows:
        agg[r["outcome"]] = agg.get(r["outcome"], 0) + 1
    print("score: %s -> %s" % (agg, a.out))
    return EXIT_INVALID if agg.get("INVALID") else EXIT_OK


def cmd_determinism(a):
    ref = None
    for p in a.logs:
        cl = [ln for ln in read_lines(p) if ln.startswith("CASE|")]
        if ref is None:
            ref = (p, cl)
        elif cl != ref[1]:
            print("NOT deterministic: %s differs from %s" % (p, ref[0]))
            return EXIT_INVALID
    print("deterministic: %d logs, %d CASE lines each identical" % (len(a.logs), len(ref[1])))
    return EXIT_OK


def main(argv=None):
    ap = argparse.ArgumentParser(description="串口日志解析/校验/篡改/评分")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("parse"); p.add_argument("--log", action="append", required=True)
    p.add_argument("--corpus", required=True); p.add_argument("--condition"); p.add_argument("--out", required=True)
    p = sp.add_parser("verify-chain"); p.add_argument("--log", required=True)
    p.add_argument("--anchor"); p.add_argument("--anchor-from-log")
    p = sp.add_parser("verify-seq"); p.add_argument("--log", required=True)
    p = sp.add_parser("tamper"); p.add_argument("--log", required=True)
    p.add_argument("--kind", required=True, choices=["T%d" % i for i in range(1, 8)])
    p.add_argument("--n", type=int, default=20); p.add_argument("--seed", type=int, default=20261007)
    p.add_argument("--outdir", required=True)
    p = sp.add_parser("score"); p.add_argument("--results", required=True)
    p.add_argument("--corpus", required=True); p.add_argument("--out", required=True)
    p = sp.add_parser("determinism"); p.add_argument("--logs", nargs="+", required=True)
    a = ap.parse_args(argv)
    return {"parse": cmd_parse, "verify-chain": cmd_verify_chain, "verify-seq": cmd_verify_seq,
            "tamper": cmd_tamper, "score": cmd_score, "determinism": cmd_determinism}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
