#!/usr/bin/env python3
"""Repair the operator-page FAQ <details> tag that is missing its closing quote.

gen_operator_pages.py wrote  <details class="op-faq only-en open>  (no quote),
so the browser swallowed <summary> into the attribute and rendered one FAQ
wrong. This adds the quote on every affected page. Idempotent.

Usage:  python3 scripts/fix_faq_details_quote.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# class="op-faq ... open>   ->   class="op-faq ..." open>
PAT = re.compile(r'(<details class="(?:op-faq|faq)(?:[^">]*?))(\s+open>)')


def main():
    pages = subs = 0
    for p in sorted(ROOT.rglob("*.html")):
        if any(part in {".git", "scripts", ".github"} for part in p.parts):
            continue
        t = p.read_text(encoding="utf-8")
        if "open>" not in t:
            continue
        t2, n = PAT.subn(r'\g<1>"\g<2>', t)
        if n and t2 != t:
            p.write_text(t2, encoding="utf-8")
            pages += 1
            subs += n
    print(f"done: fixed {subs} malformed <details> tag(s) across {pages} page(s)")


if __name__ == "__main__":
    main()
