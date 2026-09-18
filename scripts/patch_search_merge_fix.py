#!/usr/bin/env python3
"""Fix: stoppage search broke with the lite-index split.

Root cause: ux-fixes.js rebuildCompactStops() has a one-time guard
(window.__bjStopsRebuilt). If the first search ran before the full
stop index finished merging in the background, the guard got set
while buses still had no sx data - so stoppages were NEVER built
and stoppage/via-stop searches returned nothing.

Fix (idempotent):
  1. js/ux-fixes.js: drop the one-time guard. The loop already
     self-guards via (b.sx && !b.stoppages), so re-running is cheap.
  2. js/app.js: after the background merge, reset the guard too
     (defensive - works even if a browser still has the old
     ux-fixes.js cached).
  3. index.html: bump app.js / ux-fixes.js version params so every
     browser fetches the fixed files.
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


edit(ROOT / "js" / "ux-fixes.js", [
    (
        "  function rebuildCompactStops() {\n"
        "    if (window.__bjStopsRebuilt) return;\n"
        "    if (typeof DATA === 'undefined' || !DATA || !DATA.buses || !DATA.sn) return;\n"
        "    window.__bjStopsRebuilt = true;\n",
        "  function rebuildCompactStops() {\n"
        "    if (typeof DATA === 'undefined' || !DATA || !DATA.buses || !DATA.sn) return;\n",
    ),
], "js/ux-fixes.js (drop one-time guard)")

app_src = (ROOT / "js" / "app.js").read_text(encoding="utf-8")
if "window.__bjStopsRebuilt = false" in app_src:
    print("js/app.js: guard reset already present, skipping")
else:
    edit(ROOT / "js" / "app.js", [
        (
            "    if (location.hash.startsWith('#/search') || location.hash.startsWith('#/stop')) render();\n"
            "  } catch (e) { /* stoppage search needs the full index; quiet fail */ }",
            "    try { window.__bjStopsRebuilt = false; } catch (e) {}\n"
            "    if (location.hash.startsWith('#/search') || location.hash.startsWith('#/stop')) render();\n"
            "  } catch (e) { /* stoppage search needs the full index; quiet fail */ }",
        ),
    ], "js/app.js (reset guard after merge)")

edit(ROOT / "index.html", [
    ('js/app.js?v=mob20260918"', 'js/app.js?v=mob20260918b"'),
    ('js/ux-fixes.js?v=ux20260917a"', 'js/ux-fixes.js?v=mob20260918b"'),
], "index.html (version bumps)")

print("applied:", applied if applied else "nothing (all already patched)")
print("dry run" if DRY else "written")
