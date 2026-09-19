#!/usr/bin/env python3
"""Remove duplicate buses (same bus listed more than once).

Duplicate rules (conservative - only near-certain cases):
  1. Same origin + destination + same normalized departure time + same
     normalized bus name  ->  keep ONE best copy.
     (Typical case: the same physical bus scraped from both bussathi.in
     and wbbus.in, or kolkata-travel-router route variants.)
  2. Same origin + destination + bus name where one copy HAS a time and
     another has none, with matching first/last stop  ->  drop the
     untimed copy (the timed one is strictly more useful).

Keeper preference: has time > bussathi.in source > more stoppages >
more info fields (reg_no, contact_number, detail_url).

Two buses with the SAME name+route but DIFFERENT times are kept -
those are separate trips (e.g. SRI KRISHNA 5:20 and 5:40 are two real
services, not duplicates).

Removed records are saved to data/removed_duplicates.json for
transparency and manual undo. Idempotent (re-run = no-op).
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv


def norm_time(t):
    if not t:
        return ""
    t = str(t).strip().upper().replace(" ", "")
    m = re.match(r"(\d{1,2}):(\d{2})(AM|PM)?", t)
    if not m:
        return t
    h, mi, ap = int(m.group(1)), m.group(2), m.group(3)
    if ap == "PM" and h != 12:
        h += 12
    if ap == "AM" and h == 12:
        h = 0
    return f"{h:02d}:{mi}"


def norm_name(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


SOURCE_RANK = {"bussathi.in": 0, "wbbus.in": 1}


def keeper_rank(b):
    info = sum(1 for f in ("reg_no", "contact_number", "detail_url", "arrival_time") if b.get(f))
    timed = 1 if norm_time(b.get("departure_time")) else 0
    return (
        -timed,
        SOURCE_RANK.get(b.get("source") or "", 5),
        -(b.get("total_stoppages") or len(b.get("stoppages") or [])),
        -info,
    )


def main():
    path = ROOT / "data" / "busjatri_data.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    buses = d["buses"]
    total_before = len(buses)

    # rule 1: same route + time + name
    groups = defaultdict(list)
    for b in buses:
        key = (
            b.get("origin", "").strip().lower(),
            b.get("destination", "").strip().lower(),
            norm_time(b.get("departure_time")),
            norm_name(b.get("bus_name")),
        )
        groups[key].append(b)

    removed = []
    keep_ids = set()
    for key, v in groups.items():
        if len(v) < 2:
            keep_ids.add(v[0]["id"])
            continue
        v_sorted = sorted(v, key=keeper_rank)
        keep_ids.add(v_sorted[0]["id"])
        for b in v_sorted[1:]:
            removed.append((b, "same route+time+name as kept copy"))

    # rule 2: untimed copy shadowed by a timed copy (same route+name,
    # matching first/last stop)
    rn = defaultdict(list)
    for b in buses:
        if b["id"] in keep_ids:
            key = (
                b.get("origin", "").strip().lower(),
                b.get("destination", "").strip().lower(),
                norm_name(b.get("bus_name")),
            )
            rn[key].append(b)
    for key, v in rn.items():
        timed = [b for b in v if norm_time(b.get("departure_time"))]
        untimed = [b for b in v if not norm_time(b.get("departure_time"))]
        if not timed or not untimed:
            continue
        for t in timed:
            stops_t = [s.get("name", "").strip().lower() for s in t.get("stoppages") or []]
            if not stops_t:
                continue
            for u in untimed:
                if u["id"] not in keep_ids:
                    continue
                stops_u = [s.get("name", "").strip().lower() for s in u.get("stoppages") or []]
                if not stops_u:
                    continue
                if stops_u[0] == stops_t[0] and stops_u[-1] == stops_t[-1]:
                    keep_ids.discard(u["id"])
                    removed.append((u, "untimed copy of a timed service with same route+name"))

    out_buses = [b for b in buses if b["id"] in keep_ids]
    print(f"buses: {total_before} -> {len(out_buses)} (removed {len(removed)})")

    if DRY:
        print("dry run - nothing written")
        return

    log = [
        {
            "id": b["id"],
            "bus_name": b.get("bus_name"),
            "route": f'{b.get("origin")} - {b.get("destination")}',
            "time": b.get("departure_time"),
            "source": b.get("source"),
            "reason": reason,
        }
        for b, reason in removed
    ]
    (ROOT / "data" / "removed_duplicates.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    d["buses"] = out_buses
    d.setdefault("meta", {})["total_buses"] = len(d["buses"])
    path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    print("removed-duplicates log: data/removed_duplicates.json")


main()
