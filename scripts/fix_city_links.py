#!/usr/bin/env python3
"""Fix the "View timetable" links on the Kolkata city hub page.

The LINKS map on kolkata-city-bus-timetable.html points at
    bus-time-table/<route>-<from>-to-<to>.html
files that no longer exist - the route pages are now named
    bus-time-table/<from>-to-<to>.html
so every card 404'd. This rebuilds LINKS so each route points at a page
that actually exists (verified: the page must mention the route number);
routes with no matching page fall back to the bus-time-table hub.

Candidates are tried from the ROUTES from/to stands AND from the matching
bus record's origin/destination in data/app-index.json (that covers the
routes whose stands are spelled differently in the page names).

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
    for va in variants(a):
        for vb in variants(b):
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

    new, fixed, fallback = {}, 0, 0
    for n in links:
        x = city.get(n) or {}
        cands = list(pairs(x.get("a"), x.get("b")))
        rn = slug(n)
        bus = next((b for b in buses
                    if re.match(r"^wbtc-gov-wbtc-" + re.escape(rn) + r"-\d+$", str(b.get("id", "")))), None)
        if bus:
            cands += list(pairs(bus.get("origin"), bus.get("destination")))
        cand = find_page(n, cands, files)
        if cand:
            new[n] = "bus-time-table/" + cand + ".html"
            fixed += 1
        else:
            new[n] = FALLBACK
            fallback += 1

    print(f"LINKS {len(links)} -> fixed {fixed} | fallback {fallback}")
    if new == links:
        print("already correct - nothing to do")
        return
    h = h[: ml.start(2)] + json.dumps(new, ensure_ascii=False, separators=(",", ":")) + h[ml.end(2):]
    if write:
        PAGE.write_text(h, encoding="utf-8")
        print("wrote %s: %d bytes" % (PAGE.name, len(h)))
    else:
        print("[dry-run] use --write")


if __name__ == "__main__":
    main()
