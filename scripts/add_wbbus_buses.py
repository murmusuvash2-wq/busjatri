#!/usr/bin/env python3
"""Add new buses scraped from wbbus.in/allbus (2026-09-26 scrape).

Reads data/wbbus_new.json (list of {bus_name, reg_no, origin, destination,
departure_time, arrival_time, detail_url}) and appends entries that are not
already in data/busjatri_data.json.

Dedup (an entry is SKIPPED if any match):
  1. same reg_no already exists in our data
  2. same (normalized bus_name, origin, destination) already exists
  3. same (reg_no, origin, destination) seen earlier in this batch

Entry shape follows the existing wbbus.in-sourced buses: operator '-',
2-stop stoppages (origin with up time, destination), source 'wbbus.in'.

Usage:
  python3 scripts/add_wbbus_buses.py          # dry run
  python3 scripts/add_wbbus_buses.py --write # apply
"""
import json
import re
import sys

DATA = "data/busjatri_data.json"
SRC = "data/wbbus_new.json"


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or "x"


def main(write=False):
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    buses = data["buses"]
    before = len(buses)
    ids = {b.get("id") for b in buses}

    our_regs = set()
    our_keys = set()
    for b in buses:
        r = (b.get("reg_no") or "").strip().upper()
        if r:
            our_regs.add(r)
        our_keys.add((norm(b.get("bus_name")), norm(b.get("origin")), norm(b.get("destination"))))

    with open(SRC, encoding="utf-8") as f:
        entries = json.load(f)

    added = skipped = 0
    batch_regs = set()
    batch_keys = set()
    for e in entries:
        r = (e.get("reg_no") or "").strip().upper()
        key = (norm(e["bus_name"]), norm(e["origin"]), norm(e["destination"]))
        rk = (r, norm(e["origin"]), norm(e["destination"]))
        if r and (r in our_regs or rk in batch_regs):
            skipped += 1
            continue
        if key in our_keys or key in batch_keys:
            skipped += 1
            continue
        is_gov = e["bus_name"].strip().upper() in ("SBSTC", "NBSTC", "WBTC")
        bus_type = "Government - SBSTC" if e["bus_name"].strip().upper() == "SBSTC" else (
            "Government" if is_gov else "Private")
        stops = [
            {"no": 1, "name": e["origin"], "up_time": e.get("departure_time", ""), "down_time": ""},
            {"no": 2, "name": e["destination"], "up_time": "", "down_time": e.get("arrival_time", "")},
        ]
        bid = "wbbus-in-%s-%s-%s-%d" % (slug(e["bus_name"]), slug(e["origin"]),
                                         slug(e["destination"]), before + added + 1)
        while bid in ids:
            bid += "-x"
        ids.add(bid)
        if r:
            batch_regs.add(rk)
        batch_keys.add(key)
        buses.append({
            "id": bid,
            "bus_name": e["bus_name"],
            "reg_no": e.get("reg_no", ""),
            "operator": "\u2014",
            "bus_type": bus_type,
            "origin": e["origin"],
            "destination": e["destination"],
            "departure_time": e.get("departure_time", ""),
            "arrival_time": e.get("arrival_time", ""),
            "contact_number": "Not Available !",
            "depot_name": e["origin"],
            "route": "%s - %s" % (e["origin"], e["destination"]),
            "stoppages": stops,
            "source": "wbbus.in",
            "time_source": "wbbus.in",
            "total_stoppages": len(stops),
            "detail_url": e.get("detail_url", ""),
        })
        added += 1

    print("before: %d | added: %d | skipped (dup): %d | after: %d" % (before, added, skipped, len(buses)))
    assert len(buses) == before + added
    assert added > 200, "expected to add ~289 buses, added only %d" % added
    if write:
        data.setdefault("meta", {})["total_buses"] = len(buses)
        data.setdefault("meta", {})["last_updated"] = "2026-09-26"
        with open(DATA, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("written.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
