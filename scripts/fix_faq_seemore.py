#!/usr/bin/env python3
"""Two fixes requested by the site owner (27 Sep 2026):

1. SBSTC operator page FAQ: the first EN FAQ <details> tag was missing its
   closing quote (`class="op-faq only-en open>`), so the browser swallowed
   the <summary> question into the attribute and rendered the raw answer
   text instead of the question. One-character fix: add the quote.

2. Route/via pages: the inline see-more widget keeps KEEP=15 buses visible
   before collapsing; the owner wants only 10. Change KEEP 15 -> 10 and the
   collapse threshold from rows>19 to rows>10, in every deployed HTML page
   AND in scripts/gen_route_v2.py so future regenerations match.

Idempotent. ASCII-only source.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FAQ_BUG = ('<details class="op-faq only-en open><summary>',
            '<details class="op-faq only-en open"><summary>')

KEEP_OLD = "var KEEP=15,STEP=50"
KEEP_NEW = "var KEEP=10,STEP=50"
THRESH_OLD = "if(rows.length>19){"
THRESH_NEW = "if(rows.length>10){"


def fix_faq_quote():
    p = ROOT / "bus-time-table" / "sbstc-buses.html"
    s = p.read_text(encoding="utf-8")
    n = s.count(FAQ_BUG[0])
    if n == 0:
        print("sbstc-buses.html: FAQ details tag already fixed")
        return
    assert n == 1, "expected exactly 1 broken FAQ details tag, got %d" % n
    s = s.replace(FAQ_BUG[0], FAQ_BUG[1])
    assert FAQ_BUG[1] in s and FAQ_BUG[0] not in s
    p.write_text(s, encoding="utf-8")
    print("sbstc-buses.html: FAQ details quote fixed")
    # safety: no other unquoted open> variants anywhere
    for f in ROOT.rglob("*.html"):
        if "scripts" in f.parts or ".github" in f.parts:
            continue
        t = f.read_text(encoding="utf-8")
        for pat in ('only-en open>', 'only-bn open>', 'op-faq open>'):
            assert pat not in t, (str(f), pat)
    print("no other unquoted details tags found")


def fix_keep():
    changed = 0
    subs = 0
    for f in ROOT.rglob("*.html"):
        if "scripts" in f.parts or ".github" in f.parts:
            continue
        s = f.read_text(encoding="utf-8")
        n = s.count(KEEP_OLD) + s.count(THRESH_OLD)
        if n == 0:
            continue
        s = s.replace(KEEP_OLD, KEEP_NEW).replace(THRESH_OLD, THRESH_NEW)
        f.write_text(s, encoding="utf-8")
        changed += 1
        subs += n
    print("html pages patched: %d files, %d substitutions" % (changed, subs))

    g = ROOT / "scripts" / "gen_route_v2.py"
    s = g.read_text(encoding="utf-8")
    if KEEP_OLD not in s and THRESH_OLD not in s:
        assert KEEP_NEW in s and THRESH_NEW in s
        print("gen_route_v2.py generator already synced")
        return
    assert KEEP_OLD in s and THRESH_OLD in s
    s = s.replace(KEEP_OLD, KEEP_NEW).replace(THRESH_OLD, THRESH_NEW)
    g.write_text(s, encoding="utf-8")
    print("gen_route_v2.py generator synced (KEEP=10, threshold >10)")


def validate():
    leftover = 0
    for f in ROOT.rglob("*.html"):
        if "scripts" in f.parts or ".github" in f.parts:
            continue
        s = f.read_text(encoding="utf-8")
        leftover += s.count(KEEP_OLD) + s.count(THRESH_OLD)
    assert leftover == 0, leftover
    g = (ROOT / "scripts" / "gen_route_v2.py").read_text(encoding="utf-8")
    assert KEEP_OLD not in g and THRESH_OLD not in g
    print("OK: all pages + generator at KEEP=10, threshold >10")


def main():
    fix_faq_quote()
    fix_keep()
    validate()


if __name__ == "__main__":
    main()
