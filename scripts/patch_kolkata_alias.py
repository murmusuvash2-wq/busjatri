#!/usr/bin/env python3
"""Kolkata metro-area alias group.

Battery testing showed searches like "kolkata to tarapith" or
"rampurhat to kolkata" returned 0 buses even though the data has
"Kolkata to Tarapith | Esplanade -> Tarapith" etc. - the buses carry
metro-locality origins (Esplanade, Garia, Tollygunge, Howrah...) and
"kolkata" never matched them.

Fix: expand the kolkata alias group to cover the core metro
localities people use interchangeably with Kolkata. Query-side AND
value-side expansion both apply (aliasVariants runs on both), so
"kolkata to digha" now also finds Garia->Digha, Esplanade->Digha etc.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv
applied = []


def edit(path, pairs, label):
    src = path.read_text(encoding="utf-8")
    out = src
    for old, new in pairs:
        if new in out and old not in out:
            continue
        n = out.count(old)
        if n != 1:
            raise SystemExit(f"ABORT ({label}): anchor found {n}x: {old[:60]!r}")
        out = out.replace(old, new, 1)
    if out != src:
        if not DRY:
            path.write_text(out, encoding="utf-8")
        applied.append(label)


edit(ROOT / "js" / "app.js", [
    (
        "  ['kolkata', 'calcutta'],",
        "  ['kolkata', 'calcutta', 'esplanade', 'howrah', 'santragachi', 'garia', 'tollygunge', 'kudghat', 'karunamoyee'],",
    ),
], "js/app.js (kolkata metro alias group)")

edit(ROOT / "index.html", [
    ('js/app.js?v=mob20260918b"', 'js/app.js?v=mob20260918c"'),
], "index.html (app.js version bump)")

print("applied:", applied if applied else "nothing (all already patched)")
print("dry run" if DRY else "written")
