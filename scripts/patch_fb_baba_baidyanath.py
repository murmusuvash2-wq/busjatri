#!/usr/bin/env python3
"""FB community update (report, 2026-09-19): 3 buses checked, actions:

1. BABA BAIDYANATH (Super) Junput <-> Baligeria - NEW bus.
   Via Contai (Kanthi), Egra, Kharika.
   Up: Junput 6:30 AM -> Baligeria 10:40 AM.
   Down: Baligeria 1:05 PM -> Junput 6:20 PM.
   No reg no given in the report.
   -> appended to data/community_buses.json (add).

2. NEW AHAN WB50AB9284 (Brahmandiha <-> Kukrahati) - ALREADY in data
   from bussathi.in (dep 5:10 AM, 22 stops, times verified against the
   live bussathi page). The FB report adds times for 3 stops where
   bussathi has none: Mechogram 9:05 AM, Nandakumar 10:50 AM / 4:00 PM,
   Mahishadal 11:00 AM / 3:50 PM.
   -> appended to data/community_buses.json (enrich, fills blanks only).

3. MAA LAXMI WB41S6980 (Indas <-> Bardhaman) - already in data with the
   same times as the report (bus no longer serves Manbazar; our entry is
   already Indas - Bardhaman). No action.

Idempotent: re-running never duplicates.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv

BABA = {
    "operator": "Baba Baidyanath",
    "bus_name": "BABA BAIDYANATH",
    "bus_type": "Private - Non AC",
    "reg_no": "",
    "origin": "Junput",
    "destination": "Baligeria",
    "departure_time": "6:30 AM",
    "arrival_time": "10:40 AM",
    "route": "Junput - Baligeria",
    "source": "facebook (community report)",
    "detail_url": "",
    "stops": [
        ("Junput", "6:30 AM", "6:20 PM"),
        ("Contai", "7:30 AM", "4:40 PM"),
        ("Egra", "8:15 AM", "3:50 PM"),
        ("Kharika", "10:30 AM", "1:30 PM"),
        ("Baligeria", "10:40 AM", "1:05 PM"),
    ],
}

# NEW AHAN: stop -> (up, down); only applied where bussathi has no time
AHAN_FILL = {
    "Mechogram": ("9:05 AM", ""),
    "Nandakumar": ("10:50 AM", "4:00 PM"),
    "Mahishadal": ("11:00 AM", "3:50 PM"),
}


def main():
    changed = False

    # --- 1. BABA BAIDYANATH -> community_buses.json (add) ---
    pc = ROOT / "data" / "community_buses.json"
    cb = json.loads(pc.read_text(encoding="utf-8"))
    if not any(
        (e.get("origin") or "").lower() == "junput"
        and (e.get("destination") or "").lower() == "baligeria"
        for e in cb.get("add", [])
    ):
        cb["add"].append(
            {
                **BABA,
                "stops": [
                    {"name": n, "up": up, "down": down}
                    for n, up, down in BABA["stops"]
                ],
            }
        )
        changed = True
        print("BABA BAIDYANATH appended to community_buses.json")
    else:
        print("BABA BAIDYANATH already present - skip")

    # --- 2. NEW AHAN stop-time fill -> community_buses.json (enrich) ---
    d = json.loads((ROOT / "data" / "busjatri_data.json").read_text(encoding="utf-8"))
    ahan = [b for b in d["buses"] if b.get("id") == "bussathi-new-ahan-529"]
    if ahan:
        stops = [dict(s) for s in ahan[0].get("stoppages") or []]
        filled = 0
        for s in stops:
            if s.get("name") in AHAN_FILL and not s.get("up_time"):
                s["up_time"], s["down_time"] = AHAN_FILL[s["name"]]
                filled += 1
        if filled:
            cb["enrich"] = [
                e
                for e in cb.get("enrich", [])
                if e.get("target_id") != "bussathi-new-ahan-529"
            ]
            cb["enrich"].append(
                {"target_id": "bussathi-new-ahan-529", "stoppages": stops}
            )
            changed = True
            print("NEW AHAN enrich added: %d stop times filled" % filled)
        else:
            print("NEW AHAN stops already timed - skip")
    else:
        print("NEW AHAN not found in data - skip")

    if DRY or not changed:
        print("dry run or no changes - nothing written")
        return
    pc.write_text(json.dumps(cb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written")


main()
