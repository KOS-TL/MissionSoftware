#!/usr/bin/env bash
# scripts/verify_repo.sh —— 仓库卫生自检（不联网、不构建）：必需文件、个人路径/邮箱/密钥、文件名、换行符、体积、Markdown 相对链接。
# 输出每项 PASS/FAIL，最后一行 VERIFY_REPO: PASS|FAIL（失败时退出码 1）。
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
cd "$REPO_ROOT"
FAILS=0
ok()   { echo "PASS  $*"; }
bad()  { echo "FAIL  $*"; FAILS=$((FAILS+1)); }

# 待检文件清单：有 .git 时取“已跟踪 + 未忽略的新文件”，否则用 find 并排除 .gitignore 中的生成目录
if [ -d .git ] && command -v git >/dev/null 2>&1; then
  mapfile -d '' FILES < <(git ls-files -z -co --exclude-standard)
else
  mapfile -d '' FILES < <(find . \( -name .git -o -path ./microkit-sdk-2.3.1 -o -path ./.cache -o -path ./mission-shell/build \
     -o -path ./mission-shell/build_exp -o -path ./mission-shell/build_logs -o -path ./mission-shell/experiment/runs/local \
     -o -path ./mission-shell/experiment/runs/docker -o -path ./mission-shell/experiment/runs/hostsim-check \
     -o -path ./mission-shell/experiment/reports/local -o -path ./mission-shell/experiment/reports/docker -o -name __pycache__ \) -prune \
     -o -type f -printf '%P\0')
fi
echo "files checked: ${#FILES[@]}"

# 1 必需文件
REQ=(README.md README.en.md LICENSE LICENSE-docs LICENSES.md CONTRIBUTING.md CITATION.cff CHANGELOG.md .gitignore .gitattributes
     docs/INDEX.md docs/ARCHITECTURE.md docs/REPRODUCE.md docs/EXTENDING.md docs/STATUS-AND-LIMITATIONS.md docs/figs/fig-arch-detail.png
     scripts/common.sh scripts/setup_sdk.sh scripts/run_demo.sh scripts/run_experiment.sh scripts/analyze.sh scripts/check_host.sh
     scripts/check_demo_log.py scripts/check_links.py
     scripts/windows/setup_sdk.bat scripts/windows/run_demo.bat scripts/windows/run_experiment.bat scripts/windows/analyze.bat scripts/windows/check_host.bat
     mission-shell/Makefile mission-shell/gatekeeper.c mission-shell/client.c mission-shell/mission.system mission-shell/docker_build_run.sh
     mission-shell/docker_corpus_run.sh mission-shell/experiment/run_matrix.sh mission-shell/experiment/corpus/out/SHA256SUMS
     mission-shell/experiment/reports/box-qemu/report.md .github/workflows/host-checks.yml)
miss=0; for f in "${REQ[@]}"; do [ -e "$f" ] || { echo "      missing: $f"; miss=$((miss+1)); }; done
[ $miss -eq 0 ] && ok "required files (${#REQ[@]})" || bad "required files: $miss missing"

# 2 不应出现的文件
forb=$(printf '%s\n' "${FILES[@]}" | grep -E '(^|/)__pycache__/|\.pyc$|\.tgz$|Makefile\.bak-|(^|/)microkit-sdk-[0-9]|\.(elf|o|img)$|(^|/)build(_exp|_logs)?/' || true)
[ -z "$forb" ] && ok "no build outputs / caches / SDK binaries / archives" || { bad "forbidden files:"; echo "$forb" | sed 's/^/      /'; }

# 3 文件名仅 ASCII
nonascii=$(printf '%s\n' "${FILES[@]}" | LC_ALL=C grep -P '[^\x20-\x7e]' || true)
[ -z "$nonascii" ] && ok "ASCII-only file names" || { bad "non-ASCII file names:"; echo "$nonascii" | sed 's/^/      /'; }

# 4 个人信息：用户名/本机路径/邮箱/密钥（本脚本自身与 CI 定义除外，它们只含检测用的模式）
SELF='scripts/verify_repo.sh'
TEXTS=(); for f in "${FILES[@]}"; do [ "$f" = "$SELF" ] && continue; TEXTS+=("$f"); done
hits=$(printf '%s\0' "${TEXTS[@]}" | xargs -0 grep -nIiE 'chenpeng|C:\\Users|DESKTOP-[A-Z0-9]|re-Palantir|/home/box' 2>/dev/null || true)
[ -z "$hits" ] && ok "no user-specific paths/usernames (chenpeng, C:\\Users, DESKTOP-, re-Palantir, /home/box)" || { bad "user-specific paths:"; echo "$hits" | head -20 | sed 's/^/      /'; }
emails=$(printf '%s\0' "${TEXTS[@]}" | xargs -0 grep -hoIE '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}' 2>/dev/null | grep -vE '^(noreply@example\.invalid|Requirements@run\.time)$' | sort -u || true)
[ -z "$emails" ] && ok "no e-mail addresses (except noreply@example.invalid)" || { bad "e-mail addresses found:"; echo "$emails" | sed 's/^/      /'; }
secrets=$(printf '%s\0' "${TEXTS[@]}" | xargs -0 grep -nIE 'BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|github_pat_|AKIA[0-9A-Z]{16}|xox[baprs]-|sk-[A-Za-z0-9]{32,}|(password|passwd|secret|api_key|token)[[:space:]]*[:=][[:space:]]*[^[:space:]]{6,}' 2>/dev/null || true)
[ -z "$secrets" ] && ok "no secret-looking strings" || { bad "secret-looking strings:"; echo "$secrets" | head -20 | sed 's/^/      /'; }
# 可执行代码中不得硬编码作者沙箱路径（历史文档与历史日志允许出现 /workspace/...，见各文档顶部“仓库化说明”）
codeabs=$(printf '%s\n' "${FILES[@]}" | grep -E '\.(sh|py|bat|c|h|yml)$|(^|/)Makefile$' | grep -v "^$SELF$" | tr '\n' '\0' | xargs -0 grep -nI '/workspace/' 2>/dev/null || true)
[ -z "$codeabs" ] && ok "no hard-coded /workspace/ paths in code/scripts" || { bad "hard-coded /workspace/ in code:"; echo "$codeabs" | sed 's/^/      /'; }

# 5 换行符
crlf_bad=$(printf '%s\n' "${FILES[@]}" | grep -E '\.(sh|py|c|h|system|md|yml|cff|json)$|(^|/)Makefile$|(^|/)SHA256SUMS$' | tr '\n' '\0' | xargs -0 grep -lI $'\r' 2>/dev/null || true)
[ -z "$crlf_bad" ] && ok "LF line endings for *.sh *.py *.c *.h Makefile *.md ..." || { bad "CRLF in LF-only files:"; echo "$crlf_bad" | sed 's/^/      /'; }
bat_bad=""; for f in "${FILES[@]}"; do case "$f" in *.bat) lines=$(wc -l < "$f"); cr=$(grep -c $'\r$' "$f"); [ "$lines" = "$cr" ] || bat_bad+="$f "; ;; esac; done
[ -z "$bat_bad" ] && ok "CRLF line endings for *.bat" || bad "bat files without CRLF: $bat_bad"

# 6 体积
total=0; for f in "${FILES[@]}"; do total=$((total + $(stat -c %s "$f" 2>/dev/null || stat -f %z "$f"))); done
mb=$(awk "BEGIN{printf \"%.1f\", $total/1048576}")
[ "$total" -lt $((25*1024*1024)) ] && ok "total size ${mb} MiB (< 25 MiB)" || bad "total size ${mb} MiB (>= 25 MiB)"

# 7 Markdown 相对链接
if python3 scripts/check_links.py "$REPO_ROOT" > /tmp/.check_links.$$ 2>&1; then ok "markdown relative links ($(grep -o 'checked [0-9]*' /tmp/.check_links.$$))"; else bad "markdown links:"; sed 's/^/      /' /tmp/.check_links.$$; fi
rm -f /tmp/.check_links.$$

echo
[ $FAILS -eq 0 ] && { echo "VERIFY_REPO: PASS"; exit 0; } || { echo "VERIFY_REPO: FAIL ($FAILS)"; exit 1; }
