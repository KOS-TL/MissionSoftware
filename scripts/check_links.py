#!/usr/bin/env python3
"""scripts/check_links.py — 检查仓库内所有 Markdown 文件中的相对链接与图片是否指向存在的文件。

用法：python3 scripts/check_links.py [仓库根]（默认取本脚本上一级目录）
- 只检查相对链接（不访问网络）；http(s)/mailto/#锚点 跳过；锚点部分（#...）被去掉后再检查文件。
- 代码块（``` 围起的段落）与行内代码中的内容不检查。
- 输出 LINKS PASS / LINKS FAIL，失败时退出码为 1。
"""
import os
import re
import sys
from urllib.parse import unquote

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
SKIP_DIRS = {".git", "microkit-sdk-2.3.1", ".cache", "build", "build_exp", "build_logs", "local", "docker", "hostsim-check", "__pycache__"}
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def md_files():
    for d, subdirs, files in os.walk(ROOT):
        subdirs[:] = [s for s in subdirs if s not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(d, f)


def main():
    bad, total = [], 0
    for path in sorted(md_files()):
        in_code = False
        for no, line in enumerate(open(path, encoding="utf-8"), 1):
            if line.lstrip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            line = re.sub(r"`[^`]*`", "", line)
            for target in LINK.findall(line):
                if re.match(r"^(https?:|mailto:|#)", target):
                    continue
                total += 1
                rel = unquote(target.split("#", 1)[0])
                if not rel:
                    continue
                full = os.path.normpath(os.path.join(os.path.dirname(path), rel))
                if not os.path.exists(full):
                    bad.append(f"{os.path.relpath(path, ROOT)}:{no}: {target}")
    for b in bad:
        print("BROKEN", b)
    print(f"checked {total} relative links in Markdown files; broken: {len(bad)}")
    print("LINKS PASS" if not bad else "LINKS FAIL")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
