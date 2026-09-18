#!/usr/bin/env python3
"""Add community-reported buses from data/community_buses.json.

Community reports come from Facebook groups, emails and the Report Time
button - buses with full stop-level times that are not in any public
timetable site. The JSON has two sections:

  add    - list of new buses: each has operator, bus_type, reg_no, origin,
           destination, departure_time, route, source, and a stops list of
           {name, up, down} (up = own direction time, down = return time)
  enrich - list of {target_id, ...fields} merged into an existing bus

Dedup: an ADD is skipped if a bus with the same (origin, destination,
operator) already exists, so re-running never duplicates.

Usage:
  python3 scripts/add_community_buses.py          # dry run
  python3 scripts/add_community_buses.py --write  # apply
"""
import json
import re
import sys

DATA = "data/busjatri_data.json"
SRC = "data/community_buses.json"


def norm_op(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower()).replace("s", "")


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or "x"


def main(write=False):
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    buses = data["buses"]
    before = len(buses)
    ids = {b.get("id") for b in buses}
    existing_pairs = {}
    for b in buses:
        existing_pairs.setdefault(
            ((b.get("origin") or "").strip().lower(),
             (b.get("destination") or "").strip().lower(),
             norm_op(b.get("operator"))), True
        )

    with open(SRC, encoding="utf-8") as f:
        report = json.load(f)

    added = enriched = skipped = 0
    for entry in report.get("add", []):
        key = ((entry["origin"] or "").strip().lower(),
               (entry["destination"] or "").strip().lower(),
               norm_op(entry["operator"]))
        if existing_pairs.get(key):
            skipped += 1
            print("skip (already exists):", entry["operator"], entry["origin"], "->", entry["destination"])
            continue
        stops = [
            {"no": i + 1, "name": s["name"], "up_time": s.get("up", ""), "down_time": s.get("down", "")}
            for i, s in enumerate(entry.get("stops", []))
        ]
        if not stops:
            stops = [
                {"no": 1, "name": entry["origin"], "up_time": entry.get("departure_time", ""), "down_time": ""},
                {"no": 2, "name": entry["destination"], "up_time": "", "down_time": ""},
            ]
        bid = "%s-%s-%s-%d" % (slug(entry["operator"]), slug(entry["origin"]),
                               slug(entry["destination"]), before + added + 1)
        while bid in ids:
            bid += "-x"
        ids.add(bid)
        buses.append({
            "id": bid,
            "bus_name": entry.get("bus_name") or ("%s %s-%s" % (entry["operator"], entry["origin"], entry["destination"])),
            "reg_no": entry.get("reg_no", ""),
            "operator": entry["operator"],
            "bus_type": entry.get("bus_type", ""),
            "origin": entry["origin"],
            "destination": entry["destination"],
            "departure_time": entry.get("departure_time", ""),
            "arrival_time": entry.get("arrival_time", ""),
            "contact_number": entry.get("contact_number", ""),
            "depot_name": entry.get("depot_name", ""),
            "route": entry.get("route") or ("%s - %s" % (entry["origin"], entry["destination"])),
            "stoppages": stops,
            "source": entry.get("source", "facebook (community report)"),
            "time_source": entry.get("source", "facebook (community report)"),
            "total_stoppages": len(stops),
            "detail_url": entry.get("detail_url", ""),
        })
        existing_pairs[key] = True
        added += 1
        print("added:", bid)

    for entry in report.get("enrich", []):
        for b in buses:
            if b.get("id") == entry.get("target_id"):
                for k, v in entry.items():
                    if k != "target_id" and v not in (None, ""):
                        b[k] = v
                enriched += 1
                print("enriched:", entry["target_id"])
                break
        else:
            print("enrich target not found:", entry.get("target_id"))

    print("before: %d | added: %d | enriched: %d | skipped: %d | after: %d"
          % (before, added, enriched, skipped, len(buses)))
    assert len(buses) >= before, "bus count dropped - aborting"
    if write:
        data.setdefault("meta", {})["last_updated"] = "2026-09-18"
        with open(DATA, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("written.")
    else:
        print("dry run - nothing written (use --write)")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
