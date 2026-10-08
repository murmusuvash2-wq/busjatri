#!/usr/bin/env python3
"""Unify page headers.

Drops the two nav links that only some pages carried ("Home" / "Routes") and
the duplicate dark-mode button (id="bjThemeBtn") so every page header matches
the standard one (logo + language switch + a single theme toggle).

Idempotent: safe to re-run. Operates on the <header>...</header> block only.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HDR = re.compile(r'<header\b.*?</header>', re.S)
A_TAG = re.compile(r'<a\b[^>]*>.*?</a>', re.S)
BTN = re.compile(r'<button\b[^>]*id="bjThemeBtn"[^>]*>.*?</button>', re.S)
DROP = {'home', 'routes', 'হোম', 'রুট'}


def _text(html):
    return re.sub(r'<[^>]+>', '', html).replace('&nbsp;', ' ').strip().lower()


def fix_header(h):
    # 1. drop nav links whose visible text is Home / Routes
    def repl_a(m):
        t = _text(m.group(0))
        return '' if any(d in t for d in DROP) else m.group(0)
    h = A_TAG.sub(repl_a, h)
    # 2. drop the duplicate theme button
    h = BTN.sub('', h)
    return h


def main():
    pages = []
    for pat in ('*.html', 'bus-time-table/*.html', 'via/*.html', 'blog/*.html'):
        pages += list(ROOT.glob(pat))
    n = 0
    for p in pages:
        s = p.read_text(encoding='utf-8')
        m = HDR.search(s)
        if not m:
            continue
        h2 = fix_header(m.group(0))
        if h2 != m.group(0):
            p.write_text(s[:m.start()] + h2 + s[m.end():], encoding='utf-8')
            n += 1
    print(f'headers fixed: {n} of {len(pages)} pages')


if __name__ == '__main__':
    main()
