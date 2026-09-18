#!/usr/bin/env python3
"""One-shot maintenance patch: fixes generator bugs found in the 2026-09-18 audit.

Applies (idempotently, with --write):
1. gen_seo_pages.py   - place-name alias merge (kills duplicate sitemap URLs),
                         sitemap dedupe guard, robots.txt keeps sitemap-extra,
                         zombie page cleanup (stale via pages + ghost routes).
2. gen_reverse_routes.py - alias merge + untimed return services listed with
                         an honest dash; stale reverse page cleanup.
3. gen_operator_pages.py - operator field matching (WBTC page was showing 100
                         of 946 buses).
4. build_client_data.py  - meta.total_buses kept in sync with the bus list.

After the first run the patched files are committed, and this script no-ops.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITE = "--write" in sys.argv


def patch(path, edits):
    p = ROOT / path
    s = p.read_text(encoding="utf-8")
    changed = False
    for old, new in edits:
        if new in s:
            continue  # already applied
        if s.count(old) != 1:
            print(f"FAIL {path}: anchor not found or ambiguous:")
            print(old[:200])
            sys.exit(1)
        s = s.replace(old, new)
        changed = True
    if changed and WRITE:
        p.write_text(s, encoding="utf-8")
        print(f"patched {path}")
    elif changed:
        print(f"would patch {path}")
    else:
        print(f"ok (already patched): {path}")


# ---------------------------------------------------------------- gen_seo_pages
patch(
    "scripts/gen_seo_pages.py",
    [
        (
            'def clean_text(value):\n    return re.sub(r"\\s+", " ", str(value or "")).strip()\n\n\ndef bn(name):',
            'def clean_text(value):\n    return re.sub(r"\\s+", " ", str(value or "")).strip()\n\n\nPLACE_ALIAS = {\n    # merge spelling variants of the same place so route pages and the\n    # sitemap never carry duplicate URLs for the same real route\n    "Durgapur (Station)": "Durgapur Station",\n}\n\n\ndef norm_place(name):\n    t = clean_text(name)\n    return PLACE_ALIAS.get(t, t)\n\n\ndef bn(name):',
        ),
        (
            "def route_pairs():\n    routes = defaultdict(list)\n\n    for bus in BUSES:\n        origin = clean_text(bus.get(\"origin\"))\n        destination = clean_text(bus.get(\"destination\"))",
            "def route_pairs():\n    routes = defaultdict(list)\n\n    for bus in BUSES:\n        origin = norm_place(bus.get(\"origin\"))\n        destination = norm_place(bus.get(\"destination\"))",
        ),
        (
            "place_buses = defaultdict(list)\n\nfor bus in BUSES:\n    origin = clean_text(bus.get(\"origin\"))",
            "place_buses = defaultdict(list)\n\nfor bus in BUSES:\n    origin = norm_place(bus.get(\"origin\"))",
        ),
        (
            "for url in sitemap_urls:\n    sitemap.append(",
            "_seen = set()\nfor url in sitemap_urls:\n    if url in _seen:\n        continue\n    _seen.add(url)\n    sitemap.append(",
        ),
        (
            'with open(\n    "robots.txt",\n    "w",\n    encoding="utf-8",\n) as f:\n    f.write(\n        "User-agent: *\\n"\n        "Allow: /\\n\\n"\n        f"Sitemap: {BASE}/sitemap.xml\\n"\n    )',
            '_extra = f"Sitemap: {BASE}/sitemap-extra.xml\\n" if os.path.exists("sitemap-extra.xml") else ""\nwith open(\n    "robots.txt",\n    "w",\n    encoding="utf-8",\n) as f:\n    f.write(\n        "User-agent: *\\n"\n        "Allow: /\\n\\n"\n        f"Sitemap: {BASE}/sitemap.xml\\n"\n        + _extra\n    )',
        ),
        (
            "# ------------------------------------------------------------\n# SUMMARY\n# ------------------------------------------------------------",
            "# ------------------------------------------------------------\n# CLEANUP: remove zombie pages the generators no longer emit\n# (stale via pages + ghost route pages whose data no longer exists)\n# ------------------------------------------------------------\n\nimport glob as _glob\n\n_live_via = {w for w in written if \"-via-\" in w}\n_fwd_slugs = {f\"{slug(o)}-to-{slug(t)}\" for (o, t) in route_meta}\n_rev_slugs = {f\"{slug(t)}-to-{slug(o)}\" for (o, t) in route_meta}\n_removed = []\nfor p in _glob.glob(os.path.join(OUT, \"*.html\")):\n    fn = os.path.basename(p)\n    if fn == \"index.html\" or fn.startswith(\"buses-from-\") or fn.endswith(\"-buses.html\"):\n        continue\n    if \"-via-\" in fn:\n        if fn not in _live_via:\n            os.remove(p)\n            _removed.append(fn)\n        continue\n    if \"-to-\" in fn:\n        base = fn[:-5]\n        if base not in _fwd_slugs and base not in _rev_slugs:\n            os.remove(p)\n            _removed.append(fn)\n\nprint(f\"cleanup: removed {len(_removed)} stale pages\")\n\n# ------------------------------------------------------------\n# SUMMARY\n# ------------------------------------------------------------",
        ),
    ],
)

# ---------------------------------------------------------- gen_reverse_routes
patch(
    "scripts/gen_reverse_routes.py",
    [
        (
            'def stop_time(b, name, key):\n    for s in b.get("stoppages") or []:\n        if (s.get("name") or "").strip() == (name or "").strip() and s.get(key):\n            return s[key]\n    return None',
            'def stop_time(b, name, key):\n    for s in b.get("stoppages") or []:\n        if norm_stop(s.get("name")) == norm_stop(name) and s.get(key):\n            return s[key]\n    return None\n\nPLACE_ALIAS = {\n    # merge spelling variants of the same place (must match gen_seo_pages.py)\n    "Durgapur (Station)": "Durgapur Station",\n}\n\ndef norm_stop(name):\n    t = (name or "").strip()\n    return PLACE_ALIAS.get(t, t)',
        ),
        (
            '    fwd = defaultdict(list)\n    for b in buses:\n        o, dd = (b.get("origin") or "").strip(), (b.get("destination") or "").strip()',
            '    fwd = defaultdict(list)\n    for b in buses:\n        o, dd = norm_stop(b.get("origin")), norm_stop(b.get("destination"))',
        ),
        (
            '            dep = stop_time(b, dd, "down_time")\n            arr = stop_time(b, o, "down_time")\n            if dep:\n                rows.append((to_min(dep) if to_min(dep) is None else to_min(dep), dep, arr, b))\n        if not rows:\n            continue',
            '            dep = stop_time(b, dd, "down_time")\n            arr = stop_time(b, o, "down_time")\n            if dep:\n                rows.append((to_min(dep) if to_min(dep) is None else to_min(dep), dep, arr, b))\n            else:\n                # untimed return service: still list it with an honest dash\n                rows.append((None, "—", arr, b))\n        _timed = [r for r in rows if r[0] is not None]\n        if not _timed:\n            # no timed return info at all -> no page (all-dash page is useless)\n            continue\n        if not rows:\n            continue',
        ),
        (
            '        n_stops_total = len({id(r[3]) for r in rows})\n        first_t = rows[0][1] if rows else "—"\n        last_t = rows[-1][1] if rows else "—"',
            '        n_stops_total = len({id(r[3]) for r in rows})\n        first_t = _timed[0][1] if _timed else "—"\n        last_t = _timed[-1][1] if _timed else "—"',
        ),
        (
            '    pages = 0\n    added_urls = []\n    for (o, dd), bs in fwd.items():',
            '    pages = 0\n    added_urls = []\n    written = set()\n    for (o, dd), bs in fwd.items():',
        ),
        (
            '        if "--write" in sys.argv:\n            out = ROOT / "bus-time-table" / f"{slug(dd)}-to-{slug(o)}.html"\n            out.write_text(page, encoding="utf-8")\n            added_urls.append(f"{BASE}/bus-time-table/{slug(dd)}-to-{slug(o)}.html")\n        pages += 1\n\n    print(f"reverse route pages: {pages}")',
            '        if "--write" in sys.argv:\n            out = ROOT / "bus-time-table" / f"{slug(dd)}-to-{slug(o)}.html"\n            out.write_text(page, encoding="utf-8")\n            written.add(out.name)\n            added_urls.append(f"{BASE}/bus-time-table/{slug(dd)}-to-{slug(o)}.html")\n        pages += 1\n\n    print(f"reverse route pages: {pages}")\n\n    # cleanup: delete stale reverse pages from earlier runs\n    if "--write" in sys.argv:\n        fwd_slug = {f"{slug(o)}-to-{slug(dd)}" for (o, dd) in fwd}\n        rev_slug = {f"{slug(dd)}-to-{slug(o)}" for (o, dd) in fwd if (dd, o) not in fwd}\n        removed = 0\n        for p in (ROOT / "bus-time-table").glob("*-to-*.html"):\n            if "-via-" in p.name:\n                continue\n            base = p.name[:-5]\n            if base in rev_slug and p.name not in written:\n                p.unlink()\n                removed += 1\n        if removed:\n            print(f"reverse cleanup: removed {removed} stale pages")',
        ),
    ],
)

# ----------------------------------------------------------- gen_operator_pages
patch(
    "scripts/gen_operator_pages.py",
    [
        (
            "def is_sbstc(b):\n    return 'sbstc' in src(b) or 'SBSTC' in btype(b)",
            "def is_sbstc(b):\n    return 'sbstc' in src(b) or 'SBSTC' in btype(b) or _op(b) == 'sbstc'\n\n\ndef _op(b):\n    return (b.get('operator') or '').strip().lower()",
        ),
        (
            "def is_nbstc(b):\n    return 'nbstc' in src(b)",
            "def is_nbstc(b):\n    return 'nbstc' in src(b) or _op(b) == 'nbstc'",
        ),
        (
            "def is_wbtc(b):\n    return 'wbtc' in src(b)",
            "def is_wbtc(b):\n    return 'wbtc' in src(b) or _op(b) == 'wbtc'",
        ),
        (
            "def is_shyamoli(b):\n    return 'shyamoli' in src(b) or 'shyamoli' in (b.get('bus_name') or '').lower()",
            "def is_shyamoli(b):\n    return 'shyamoli' in src(b) or 'shyamoli' in (b.get('bus_name') or '').lower() or _op(b) == 'shyamoli paribahan'",
        ),
    ],
)

# ------------------------------------------------------------ build_client_data
patch(
    "scripts/build_client_data.py",
    [
        (
            'index = {\n    "meta": source["meta"],',
            'index = {\n    "meta": {**source["meta"], "total_buses": len(source["buses"])},',
        ),
    ],
)

print("generator maintenance patch done")
