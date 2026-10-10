#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按编译期条件统计门闩有效代码行数（非空、非注释），用于 E2 成本指标与 X-7。

只实现本仓库 gatekeeper_field.c 用到的预处理子集：#if/#ifdef/#ifndef/#elif/#else/#endif、
defined(X)、整数对象宏（#define X 1）、&& || ! + != == 与括号。#include 不展开。

用法：loc_count.py FILE.c -D GATE_VARIANT_B [-D ABLATE_U ...]
      loc_count.py --variants FILE.c     # 输出 B / Bplus / M / M-* 的行数表（JSON）
"""
import argparse
import json
import re
import sys

COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.S)
COMMENT_LINE = re.compile(r"//[^\n]*")


def _eval(expr, defs):
    e = re.sub(r"defined\s*\(\s*(\w+)\s*\)", lambda m: "1" if m.group(1) in defs else "0", expr)
    e = re.sub(r"defined\s+(\w+)", lambda m: "1" if m.group(1) in defs else "0", e)

    def ident(m):
        v = defs.get(m.group(0))
        if v is None:
            return "0"
        try:
            return str(int(v))
        except ValueError:
            return "1"
    e = re.sub(r"\b[A-Za-z_]\w*\b", ident, e)
    e = e.replace("&&", " and ").replace("||", " or ")
    e = re.sub(r"!(?!=)", " not ", e)
    return bool(eval(e, {"__builtins__": {}}, {}))


def count(path, defines):
    src = open(path, encoding="utf-8").read()
    src = COMMENT_BLOCK.sub(lambda m: "\n" * m.group(0).count("\n"), src)
    src = COMMENT_LINE.sub("", src)
    defs = {d: "1" for d in defines}
    stack = []  # (本分支是否激活, 是否已有分支被选中, 父级是否激活)
    active, n = True, 0
    for raw in src.split("\n"):
        line = raw.strip()
        m = re.match(r"#\s*(\w+)\s*(.*)$", line)
        if m:
            d, rest = m.group(1), m.group(2)
            if d in ("if", "ifdef", "ifndef"):
                cond = (rest.strip() in defs) if d == "ifdef" else \
                       (rest.strip() not in defs) if d == "ifndef" else _eval(rest, defs)
                take = active and cond
                stack.append([take, take, active])
                active = take
                continue
            if d == "elif":
                top = stack[-1]
                take = top[2] and not top[1] and _eval(rest, defs)
                top[0] = take
                top[1] = top[1] or take
                active = take
                continue
            if d == "else":
                top = stack[-1]
                take = top[2] and not top[1]
                top[0] = take
                top[1] = True
                active = take
                continue
            if d == "endif":
                top = stack.pop()
                active = top[2]
                continue
            if active and d == "define":
                mm = re.match(r"(\w+)\s*(.*)$", rest)
                if mm and "(" not in mm.group(1):
                    defs[mm.group(1)] = mm.group(2).strip() or "1"
        if active and line:
            n += 1
    return n


VARIANTS = {
    "B": ["GATE_VARIANT_B"], "Bplus": ["GATE_VARIANT_BPLUS"], "M": ["GATE_VARIANT_M"],
    "M-cosign": ["GATE_VARIANT_M", "ABLATE_COSIGN"], "M-align": ["GATE_VARIANT_M", "ABLATE_ALIGN"],
    "M-prov": ["GATE_VARIANT_M", "ABLATE_PROV"], "M-U": ["GATE_VARIANT_M", "ABLATE_U"],
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("-D", action="append", default=[])
    ap.add_argument("--variants", action="store_true")
    a = ap.parse_args(argv)
    if a.variants:
        print(json.dumps({k: count(a.file, v) for k, v in VARIANTS.items()}, indent=1))
    else:
        print(count(a.file, a.D))
    return 0


if __name__ == "__main__":
    sys.exit(main())
