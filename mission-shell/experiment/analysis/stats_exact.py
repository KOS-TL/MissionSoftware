# -*- coding: utf-8 -*-
"""
精确统计工具（仅标准库）：二项、Clopper–Pearson、Wilson、精确 McNemar、Fisher 精确、Holm、符号检验、Cohen's κ。
"""
import math
from fractions import Fraction


def binom_pmf(k, n, p=0.5):
    if p == 0.5:
        return float(Fraction(math.comb(n, k), 2 ** n))
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def binom_cdf(k, n, p):
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    return min(1.0, sum(math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(0, k + 1)))


def binom_sf(k, n, p):
    """P(X >= k)"""
    return 1.0 - binom_cdf(k - 1, n, p)


def _bisect(f, lo=0.0, hi=1.0, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if f(mid):
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def clopper_pearson(x, n, alpha=0.05):
    """双侧 (1-alpha) 精确区间。"""
    if n == 0:
        return (0.0, 1.0)
    lo = 0.0 if x == 0 else _bisect(lambda p: binom_sf(x, n, p) >= alpha / 2)
    hi = 1.0 if x == n else _bisect(lambda p: binom_cdf(x, n, p) <= alpha / 2)
    return (lo, hi)


def wilson(x, n, z=1.959963984540054):
    if n == 0:
        return (0.0, 1.0)
    ph = x / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def mcnemar_exact(b, c):
    """返回 (双侧 p, 单侧 p[H1: b > c])；对 b+c 个不一致对做 Binomial(0.5) 检验。"""
    n = b + c
    if n == 0:
        return (1.0, 1.0)
    k = min(b, c)
    two = min(1.0, 2 * sum(binom_pmf(i, n) for i in range(0, k + 1)))
    one = sum(binom_pmf(i, n) for i in range(b, n + 1))
    return (two, min(1.0, one))


def fisher_exact(a, b, c, d):
    """2x2 表 [[a,b],[c,d]]；返回 (双侧 p, 单侧 p[第一行比例更高])。"""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d

    def hp(x):
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    p0 = hp(a)
    two = sum(hp(x) for x in range(lo, hi + 1) if hp(x) <= p0 * (1 + 1e-9))
    one = sum(hp(x) for x in range(a, hi + 1))
    return (min(1.0, two), min(1.0, one))


def holm(pvals):
    """Holm 逐步校正；输入 {key: p}，返回 {key: p_adj}。"""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def sign_test(wins, losses):
    """双侧精确符号检验（平局剔除）。"""
    return mcnemar_exact(wins, losses)[0]


def cohen_kappa(labels_a, labels_b):
    assert len(labels_a) == len(labels_b) and labels_a
    cats = sorted(set(labels_a) | set(labels_b))
    n = len(labels_a)
    po = sum(x == y for x, y in zip(labels_a, labels_b)) / n
    pe = sum((labels_a.count(k) / n) * (labels_b.count(k) / n) for k in cats)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)
