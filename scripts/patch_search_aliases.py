#!/usr/bin/env python3
"""Add a place-alias layer so same-town different-name searches match.

Examples: Kanthi is the Bengali name of Contai; Burdwan = Bardhaman;
Baharampur = Berhampore; Calcutta = Kolkata. The data itself mixes these
spellings (Contai 183 vs Kanthi 28 stops, Bardhaman 273 vs Burdwan 258),
so a traveller searching "kanthi to kolkata" got 0 results while the
buses carry the stop spelled "Contai".

Patch: js/app.js - rename the existing placeMatches() (fuzzy tier from
patch_search_fuzzy.py) to placeMatchesCore(), then add a new placeMatches()
wrapper that expands both the query and the value through a small alias
group table before falling back to the core matcher. All callers
(from/to route search, stoppage search, place pages - app.js and
ux-fixes.js) go through placeMatches, so one patch covers everything.

Idempotent: skips if PLACE_ALIAS_GROUPS already present.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv

CORE_SIG = "function placeMatches(value, query) {"
RENAMED_SIG = "function placeMatchesCore(value, query) {"

# tail of the fuzzy-tier matcher as shipped by patch_search_fuzzy.py
OLD_TAIL = (
    "  const skel = s => s.replace(/[^bcdfghjklmnpqrstvwxyz]/g, '');\n"
    "  const vs = skel(v), qs = skel(q);\n"
    "  if (qs.length >= 4 && (vs === qs || vs.includes(qs))) return true;\n"
    "  return false;\n"
    "}"
)

ALIAS_BLOCK = (
    "  const skel = s => s.replace(/[^bcdfghjklmnpqrstvwxyz]/g, '');\n"
    "  const vs = skel(v), qs = skel(q);\n"
    "  if (qs.length >= 4 && (vs === qs || vs.includes(qs))) return true;\n"
    "  return false;\n"
    "}\n\n"
    "/* Place alias groups: same town, different names (Bengali vs English\n"
    "   spellings). The data mixes these spellings, so expand both sides of\n"
    "   every comparison through the group table. Covers from/to route\n"
    "   search, stoppage search and place pages (all use placeMatches). */\n"
    "const PLACE_ALIAS_GROUPS = [\n"
    "  ['contai', 'kanthi'],\n"
    "  ['berhampore', 'baharampur'],\n"
    "  ['bardhaman', 'burdwan'],\n"
    "  ['kolkata', 'calcutta'],\n"
    "  ['bolpur', 'santiniketan'],\n"
    "  ['tarakeswar', 'tarakeshwar'],\n"
    "  ['malda', 'english bazar', 'malda town'],\n"
    "  ['cooch behar', 'koch bihar'],\n"
    "  ['krishnanagar', 'krishnagar']\n"
    "];\n"
    "const PLACE_ALIAS = {};\n"
    "PLACE_ALIAS_GROUPS.forEach(function (g) { g.forEach(function (n) { PLACE_ALIAS[n] = g; }); });\n"
    "function aliasVariants(name) {\n"
    "  const k = String(name || '').toLowerCase().trim();\n"
    "  const g = PLACE_ALIAS[k];\n"
    "  return g ? [k].concat(g) : [k];\n"
    "}\n"
    "function placeMatches(value, query) {\n"
    "  if (placeMatchesCore(value, query)) return true;\n"
    "  let aq = aliasVariants(query);\n"
    "  for (let i = 0; i < aq.length; i++) {\n"
    "    if (placeMatchesCore(value, aq[i])) return true;\n"
    "  }\n"
    "  let av = aliasVariants(value);\n"
    "  for (let i = 0; i < av.length; i++) {\n"
    "    if (placeMatchesCore(av[i], query)) return true;\n"
    "  }\n"
    "  return false;\n"
    "}"
)


def main():
    path = ROOT / "js" / "app.js"
    src = path.read_text(encoding="utf-8")
    if "PLACE_ALIAS_GROUPS" in src:
        print("js/app.js: alias layer already present, skipping")
        print("changed: False | dry run" if DRY else "changed: False | written")
        return
    if src.count(CORE_SIG) != 1:
        raise SystemExit(f"ERROR: expected exactly 1 placeMatches signature, found {src.count(CORE_SIG)} - aborting")
    if src.count(OLD_TAIL) != 1:
        raise SystemExit(f"ERROR: fuzzy matcher tail not found exactly once ({src.count(OLD_TAIL)}x) - aborting")
    out = src.replace(CORE_SIG, RENAMED_SIG, 1).replace(OLD_TAIL, ALIAS_BLOCK, 1)
    if "function placeMatchesCore" not in out or "PLACE_ALIAS_GROUPS" not in out:
        raise SystemExit("ERROR: patch sanity check failed - aborting, nothing written")
    if not DRY:
        path.write_text(out, encoding="utf-8")
    print("js/app.js: placeMatchesCore + alias-aware placeMatches installed")
    print("changed: True | dry run" if DRY else "changed: True | written")


main()
