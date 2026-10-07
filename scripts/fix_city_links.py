#!/usr/bin/env python3
"""Fix the "View timetable" links on the Kolkata city hub page.

Links on kolkata-city-bus-timetable.html point at
    bus-time-table/<route>-<from>-to-<to>
pages that do not exist (route pages are named bus-time-table/<from>-to-<to>).
Two places are affected:
  1. the JS LINKS map (used by the search-result rows)
  2. hardcoded href="..." on the "All 73 routes (A-Z)" / Popular cards

This rebuilds BOTH so every link points at a page that exists (verified: the
target page must mention the route number); routes with no matching page fall
back to the bus-time-table hub.

URL form: clean (extensionless) - matches the site-wide clean-URL migration.
Handles both "bus-time-table/<slug>" and legacy "bus-time-table/<slug>.html".

Idempotent.  Usage: python3 scripts/fix_city_links.py [--write]
"""
import json
import pathlib
import re
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
PAGE = BASE / "kolkata-city-bus-timetable.html"
BTT = BASE / "bus-time-table"
INDEX = BASE / "data" / "app-index.json"
FALLBACK = "bus-time-table/"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def variants(s):
    b = slug(s)
    out = {b}
    for suf in ["-stn", "-station", "-bus-stand", "-stand", "-depot", "-more",
                "-gate", "-it-park", "-terminus"]:
        if b.endswith(suf):
            out.add(b[: -len(suf)].strip("-"))
    if "stn" in b:
        out.add(b.replace("stn", "station"))
    if "station" in b:
        out.add(b.replace("station", "stn"))
    out.add(re.sub(r"-\d+$", "", b))
    return {v for v in out if v}


def pairs(a, b):
    # sorted -> deterministic candidate order (sets iterate in a per-process
    # order that varies with PYTHONHASHSEED, which made the output unstable)
    for va in sorted(variants(a)):
        for vb in sorted(variants(b)):
            yield va + "-to-" + vb
            yield vb + "-to-" + va


def find_page(n, cands, files):
    for c in cands:
        if c in files and n.upper() in (BTT / (c + ".html")).read_text(encoding="utf-8", errors="replace").upper():
            return c
    return None


def main():
    write = "--write" in sys.argv
    files = {p.name[:-5] for p in BTT.glob("*.html")}
    h = PAGE.read_text(encoding="utf-8")

    ml = re.search(r'(var|const|let)\s+LINKS\s*=\s*(\{.*?\});', h, re.DOTALL)
    mr = re.search(r'(var|const|let)\s+ROUTES\s*=\s*(\[.*?\]);', h, re.DOTALL)
    if not ml or not mr:
        sys.exit("LINKS or ROUTES not found")
    links = json.loads(ml.group(2))
    city = {x["n"]: x for x in json.loads(mr.group(2)) if not x.get("pvt")}

    buses = []
    if INDEX.exists():
        buses = json.loads(INDEX.read_text(encoding="utf-8")).get("buses", [])

    # route no -> correct target url (clean, no .html)
    target, fixed, fallback = {}, 0, 0
    for n, x in city.items():
        # A CSTC route has a dedicated city page bus-time-table/cstc-<slug>
        # (city design + real times). Prefer it over the generic
        # <from>-to-<to> page, which is a different (generic) design and
        # carries the redundant horizontal "Route Map" block. Falls back to
        # the <from>-to-<to> candidates only if no cstc page exists.
        cands = ["cstc-" + slug(n)] + list(pairs(x.get("a"), x.get("b")))
        rn = slug(n)
        bus = next((b for b in buses
                    if re.match(r"^wbtc-gov-wbtc-" + re.escape(rn) + r"-\d+$", str(b.get("id", "")))), None)
        if bus:
            cands += list(pairs(bus.get("origin"), bus.get("destination")))
        cand = find_page(n, cands, files)
        if cand:
            target[n] = "bus-time-table/" + cand
            fixed += 1
        else:
            target[n] = FALLBACK
            fallback += 1
    print("routes %d -> page %d | fallback %d" % (len(city), fixed, fallback))

    changed = False

    # ---- 1. JS LINKS map ---------------------------------------------------
    new_links = {n: target.get(n, FALLBACK) for n in links}
    if new_links != links:
        h = h[: ml.start(2)] + json.dumps(new_links, ensure_ascii=False, separators=(",", ":")) + h[ml.end(2):]
        changed = True

    # ---- 2. hardcoded hrefs (clean OR legacy .html) ------------------------
    slugs = sorted((slug(n) for n in city), key=len, reverse=True)

    def repl(m):
        nonlocal changed
        url = m.group(1)  # without optional .html
        if url == FALLBACK or (BASE / url).exists() or (BASE / (url + ".html")).exists():
            return m.group(0)
        inner = url[len("bus-time-table/"):]
        rn = next((s for s in slugs if inner == s or inner.startswith(s + "-")), None)
        newurl = None
        if rn:
            n = next(n for n in city if slug(n) == rn)
            newurl = target[n]
        if newurl and newurl != url:
            changed = True
            return 'href="' + newurl + '"'
        return m.group(0)

    h = re.sub(r'href="(bus-time-table/[^"#]+?)(?:\.html)?"', repl, h)

    if not changed:
        print("already correct - nothing to do")
        return
    if write:
        PAGE.write_text(h, encoding="utf-8")
        print("wrote %s: %d bytes" % (PAGE.name, len(h)))
    else:
        print("[dry-run] use --write")


if __name__ == "__main__":
    main()
