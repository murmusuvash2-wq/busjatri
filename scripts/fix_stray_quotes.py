#!/usr/bin/env python3
"""Repair malformed attribute values left behind by a bug in fix_clean_urls.py.

The bug: PARENT_HOME_RE used a lookahead for the closing quote

    re.compile(r'href="\\.\\./index\\.html(?=["?])')     # quote NOT consumed
    text = PARENT_HOME_RE.sub('href="../"', text)          # ...but re-added

so `href="../index.html"` became `href="../"` + the original `"` = `href="../""`.
Browsers tolerate it (the stray quote parses as a junk attribute name, so the
link still works) but the markup is invalid and the pattern spread to every
page fix_clean_urls.py ever touched.

This rewrites every `href="X""` -> `href="X"`. Idempotent; ASCII-only source.

Run from repo root:  python3 scripts/fix_stray_quotes.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# href="<anything without a quote>" immediately followed by a stray quote
STRAY_HREF_RE = re.compile(r'(href="[^"]*")"')

SKIP_DIRS = {"scripts", ".github", "node_modules", ".git"}


def repair(text: str) -> str:
    return STRAY_HREF_RE.sub(r"\1", text)


def main() -> int:
    files = 0
    hits = 0
    for path in sorted(ROOT.rglob("*.html")):
        if SKIP_DIRS & set(path.parts):
            continue
        try:
            src = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        n = len(STRAY_HREF_RE.findall(src))
        if not n:
            continue
        out = repair(src)
        if out != src:
            path.write_text(out, encoding="utf-8")
            files += 1
            hits += n

    # safety net: nothing should remain anywhere in the deployed tree
    leftover = 0
    for path in ROOT.rglob("*.html"):
        if SKIP_DIRS & set(path.parts):
            continue
        try:
            leftover += len(STRAY_HREF_RE.findall(path.read_text(encoding="utf-8")))
        except (UnicodeDecodeError, OSError):
            continue

    print(f"fix_stray_quotes: repaired {hits} malformed hrefs across {files} files")
    print(f"fix_stray_quotes: remaining stray-quote hrefs: {leftover}")
    return 1 if leftover else 0


if __name__ == "__main__":
    sys.exit(main())
