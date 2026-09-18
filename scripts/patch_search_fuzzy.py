#!/usr/bin/env python3
"""Make stop search tolerant of Bengali-transliteration spelling variants.

Problem: search used exact substring matching, so "Mollarpur" found nothing
while the data spells the stop "Mallarpur". Locals type several spellings
(Mallarpur/Mollarpur, Medinipur/Midnapore, Tarapith/Tarapeeth...).

Fix (2 files):
  1. js/app.js    - upgrade the shared placeMatches() matcher with a
     consonant-skeleton tier: after the existing substring and compact
     checks fail, compare consonant-only skeletons (vowels are the main
     source of transliteration drift). Guarded to queries with >= 4
     consonants so short queries like "pur" cannot match everything.
  2. js/ux-fixes.js - the V2 search override matched stop names with raw
     substring .includes(); route these through placeMatches() so stop
     searches (and place pages) get the same fuzzy tier.

Idempotent: skips files already carrying the fuzzy tier.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv

OLD_MATCHER = (
    "function placeMatches(value, query) {\n"
    "  const v = String(value || '').toLowerCase().trim();\n"
    "  const q = String(query || '').toLowerCase().trim();\n"
    "  if (!v || !q) return false;\n"
    "  if (v.includes(q)) return true;\n"
    "  const compact = s => s.replace(/[^a-z0-9]/g, '');\n"
    "  const vc = compact(v).replace(/ac$/, '');\n"
    "  const qc = compact(q).replace(/ac$/, '');\n"
    "  return vc === qc || vc.includes(qc);\n"
    "}"
)

NEW_MATCHER = (
    "function placeMatches(value, query) {\n"
    "  const v = String(value || '').toLowerCase().trim();\n"
    "  const q = String(query || '').toLowerCase().trim();\n"
    "  if (!v || !q) return false;\n"
    "  if (v.includes(q)) return true;\n"
    "  const compact = s => s.replace(/[^a-z0-9]/g, '');\n"
    "  const vc = compact(v).replace(/ac$/, '');\n"
    "  const qc = compact(q).replace(/ac$/, '');\n"
    "  if (vc === qc || vc.includes(qc)) return true;\n"
    "  /* Fuzzy tier for Bengali transliteration variants: compare consonant\n"
    "     skeletons (Mallarpur/Mollarpur, Medinipur/Midnapore, Tarapith/...\n"
    "     Tarapeeth). Only for queries with at least 4 consonants so short\n"
    "     words like 'pur' cannot match every place. */\n"
    "  const skel = s => s.replace(/[^bcdfghjklmnpqrstvwxyz]/g, '');\n"
    "  const vs = skel(v), qs = skel(q);\n"
    "  if (qs.length >= 4 && (vs === qs || vs.includes(qs))) return true;\n"
    "  return false;\n"
    "}"
)

UX_EDITS = [
    # stop-only search branch: raw substring -> shared fuzzy matcher
    (
        "            if (!mS && (s.name || '').toLowerCase().includes(stop)) mS = s;\n"
        "          });\n"
        "          var isO = (b.origin || '').toLowerCase().includes(stop);\n"
        "          var isD = (b.destination || '').toLowerCase().includes(stop);",
        "            if (!mS && placeMatches(s.name, stop)) mS = s;\n"
        "          });\n"
        "          var isO = placeMatches(b.origin, stop);\n"
        "          var isD = placeMatches(b.destination, stop);",
    ),
]

# generic stop-name matching against q (search single-query branch + place pages)
UX_STOP_Q_OLD = "(b.stoppages || []).some(function (s) { return (s.name || '').toLowerCase().includes(q); });"
UX_STOP_Q_NEW = "(b.stoppages || []).some(function (s) { return placeMatches(s.name, q); });"


def patch_app(path):
    src = path.read_text(encoding="utf-8")
    if "consonant" in src and "const skel" in src:
        print(f"{path.name}: already fuzzy-patched, skipping")
        return False
    if OLD_MATCHER not in src:
        raise SystemExit(f"ERROR: placeMatches anchor not found in {path.name} - aborting, no changes")
    out = src.replace(OLD_MATCHER, NEW_MATCHER, 1)
    assert out != src
    if not DRY:
        path.write_text(out, encoding="utf-8")
    print(f"{path.name}: placeMatches upgraded with fuzzy tier")
    return True


def patch_ux(path):
    src = path.read_text(encoding="utf-8")
    if "placeMatches(s.name, stop)" in src:
        print(f"{path.name}: stop branch already fuzzy-patched, skipping")
        return False
    out = src
    for old, new in UX_EDITS:
        if out.count(old) != 1:
            raise SystemExit(f"ERROR: stop-branch anchor found {out.count(old)}x in {path.name} - aborting")
        out = out.replace(old, new, 1)
    n = out.count(UX_STOP_Q_OLD)
    if n == 0:
        raise SystemExit(f"ERROR: no generic stop-match anchors found in {path.name} - aborting")
    out = out.replace(UX_STOP_Q_OLD, UX_STOP_Q_NEW)
    if not DRY:
        path.write_text(out, encoding="utf-8")
    print(f"{path.name}: stop search now uses placeMatches ({n} generic spots + stop branch)")
    return True


changed = False
changed |= patch_app(ROOT / "js" / "app.js")
changed |= patch_ux(ROOT / "js" / "ux-fixes.js")
print("changed:", changed, "| dry run" if DRY else "| written")
