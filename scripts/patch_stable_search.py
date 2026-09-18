#!/usr/bin/env python3
"""PERMANENT fix for stoppage search reliability.

The lite-index split (first fast paint, background full-index merge)
kept breaking stoppage searches whenever a user searched before the
background merge landed, or when a stale cached JS was served. Search
must be simple and bulletproof: every stoppage, big or small, must be
searchable the moment the app loads.

Change: go back to loading the single full app-index.json directly.
The whole index (~400 KB gzipped) arrives once at load; stoppage and
via-stop searches work instantly with zero timing dependence. The big
performance win from the audit (per-bus detail files: 5 MB bulk ->
~1.5 KB per bus page) is untouched.

Also: every new bus added via community_buses / fill_new_sources
rebuilds the index (build_client_data.py), so new buses' stoppages
are searchable automatically - no extra step needed.

Idempotent.
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
        if old not in out:
            continue  # already patched (or absent)
        n = out.count(old)
        if n != 1:
            raise SystemExit(f"ABORT ({label}): anchor found {n}x: {old[:60]!r}")
        out = out.replace(old, new, 1)
    if out != src:
        if not DRY:
            path.write_text(out, encoding="utf-8")
        applied.append(label)


LOADFN = (
    "async function loadFullIndex() {\n"
    "  /* background: full stop index (sx/ux/dx + sn) for stoppage search */\n"
    "  try {\n"
    "    const res = await fetch('data/app-index.json');\n"
    "    if (!res.ok) return;\n"
    "    const full = await res.json();\n"
    "    if (full.sn && DATA) DATA.sn = full.sn;\n"
    "    (full.buses || []).forEach(fb => {\n"
    "      const b = BUSES[fb.id];\n"
    "      if (b && !b.sx && fb.sx) { b.sx = fb.sx; b.ux = fb.ux; b.dx = fb.dx; }\n"
    "    });\n"
    "    try { window.__bjStopsRebuilt = false; } catch (e) {}\n"
    "    if (location.hash.startsWith('#/search') || location.hash.startsWith('#/stop')) render();\n"
    "  } catch (e) { /* stoppage search needs the full index; quiet fail */ }\n"
    "}\n"
)

edit(ROOT / "js" / "app.js", [
    # 1. load the full index directly - no lite/merge dance
    (
        "    let res = await fetch('data/app-index-lite.json');\n"
        "    if (!res.ok) res = await fetch('data/app-index.json');\n"
        "    if (!res.ok) throw new Error('HTTP ' + res.status);\n"
        "    DATA = await res.json();",
        "    const res = await fetch('data/app-index.json');\n"
        "    if (!res.ok) throw new Error('HTTP ' + res.status);\n"
        "    DATA = await res.json();",
    ),
    # 2. no background merge call
    (
        "    window.addEventListener('hashchange', render);\n"
        "    render();\n"
        "    loadFullIndex();\n",
        "    window.addEventListener('hashchange', render);\n"
        "    render();\n",
    ),
    # 3. remove the whole loadFullIndex function
    (LOADFN, ""),
], "js/app.js (direct full index, no merge)")

edit(ROOT / "index.html", [
    ('js/app.js?v=mob20260918c"', 'js/app.js?v=mob20260918d"'),
], "index.html (app.js version bump)")

print("applied:", applied if applied else "nothing (all already patched)")
print("dry run" if DRY else "written")
