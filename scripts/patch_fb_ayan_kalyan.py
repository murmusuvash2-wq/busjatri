#!/usr/bin/env python3
"""FB community update (report by Dinesh Rock, 2026-09-18):

1. AYAN EXPRESS (Super Fast) Jhargram <-> Digha - NEW bus.
   Up: Jhargram 5:30 AM -> Digha 10:25 AM.
   Down: Digha 12:30 PM -> Jhargram 6:30 PM.
   Contact 9382172869. Appended to data/community_buses.json.

2. KALYAN TRAVELS (bussathi-kalyan-322, reg WB55B9666) - same bus
   already in data with 14 stops; enriched with the fuller 25-stop
   route + times from the FB report
   (Jhalda 4:00 AM -> Jhargram 10:00 AM, return Jhargram 10:50 AM
   -> Purulia 4:10 PM, Purulia 6:20 PM -> Jhalda 8:00 PM).

Idempotent: re-running makes no changes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv

KALYAN_STOPS = [
    ("Jhalda", "4:00 AM", "8:00 PM"),
    ("Jaypur", "4:30 AM", "7:10 PM"),
    ("Chashmoda", "", ""),
    ("Lagda", "", ""),
    ("Purulia", "5:30 AM", "6:20 PM"),
    ("Tamna", "", ""),
    ("Chakoltor", "5:50 AM", "3:45 PM"),
    ("Tokariya", "", ""),
    ("Bamundaha", "6:10 AM", "3:05 PM"),
    ("Manpur", "", ""),
    ("Barabazar", "6:40 AM", "2:50 PM"),
    ("Jamboni", "", ""),
    ("Katin", "7:00 AM", "2:10 PM"),
    ("Madhupur", "", ""),
    ("Bandowan", "7:30 AM", "1:40 PM"),
    ("Kuilapal", "8:00 AM", "1:00 PM"),
    ("Jhilimili", "8:10 AM", "12:50 PM"),
    ("Chakadoba", "", ""),
    ("Bhulabheda", "", ""),
    ("Belpahari", "8:50 AM", "12:10 PM"),
    ("Shilda", "9:15 AM", "11:55 AM"),
    ("Binpur", "9:30 AM", "11:40 AM"),
    ("Dahijuri", "", ""),
    ("Panchmathar More", "", "11:00 AM"),
    ("Jhargram", "10:00 AM", "10:50 AM"),
]

AYAN = {
    "operator": "Ayan Express",
    "bus_name": "Ayan Express Jhargram-Digha (Super Fast)",
    "bus_type": "Private",
    "reg_no": "",
    "origin": "Jhargram",
    "destination": "Digha",
    "departure_time": "5:30 AM",
    "arrival_time": "10:25 AM",
    "route": "Jhargram - Digha",
    "source": "facebook (community report)",
    "detail_url": "",
    "contact_number": "9382172869",
    "stops": [
        ("Jhargram", "5:30 AM", "6:30 PM"),
        ("Lodhashuli", "5:50 AM", "6:10 PM"),
        ("Feko", "6:10 AM", ""),
        ("Gopiballabpur", "6:30 AM", "5:25 PM"),
        ("Kharika", "7:30 AM", "4:15 PM"),
        ("Keshiary", "8:00 AM", "3:35 PM"),
        ("Belda", "8:25 AM", "2:55 PM"),
        ("Egra", "9:15 AM", "2:05 PM"),
        ("Paniparul", "9:45 AM", "1:35 PM"),
        ("Ramnagar", "10:10 AM", "1:10 PM"),
        ("New Digha", "", "12:40 PM"),
        ("Digha", "10:25 AM", "12:30 PM"),
    ],
}


def main():
    changed = False

    # --- 1. enrich KALYAN TRAVELS in main data ---
    p = ROOT / "data" / "busjatri_data.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    matches = [b for b in d["buses"] if b["id"] == "bussathi-kalyan-322"]
    assert len(matches) == 1, f"kalyan: expected 1 match, got {len(matches)}"
    b = matches[0]
    stop_names = [s.get("name") for s in b.get("stoppages") or []]
    if "Jaypur" not in stop_names:
        b.update(
            {
                "bus_name": "KALYAN TRAVELS",
                "operator": "Kalyan Travels",
                "bus_type": "Private - NON AC",
                "reg_no": "WB 55B 9666",
                "origin": "Jhalda",
                "destination": "Jhargram",
                "departure_time": "4:00 AM",
                "arrival_time": "10:00 AM",
                "contact_number": "",
                "route": "Jhalda - Jhargram",
                "stoppages": [
                    {"no": i + 1, "name": n, "up_time": up, "down_time": down}
                    for i, (n, up, down) in enumerate(KALYAN_STOPS)
                ],
                "total_stoppages": len(KALYAN_STOPS),
            }
        )
        changed = True
        print("KALYAN TRAVELS enriched: 25-stop route with times")
    else:
        print("KALYAN TRAVELS already enriched - skip")

    # --- 2. append AYAN EXPRESS to community_buses.json ---
    pc = ROOT / "data" / "community_buses.json"
    cb = json.loads(pc.read_text(encoding="utf-8"))
    if not any("Ayan Express" in (e.get("bus_name") or "") for e in cb.get("add", [])):
        cb["add"].append(
            {
                **AYAN,
                "stops": [
                    {"name": n, "up": up, "down": down}
                    for n, up, down in AYAN["stops"]
                ],
            }
        )
        changed = True
        print("AYAN EXPRESS appended to community_buses.json")
    else:
        print("AYAN EXPRESS already present - skip")

    if DRY or not changed:
        print("dry run or no changes - nothing written")
        return
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    pc.write_text(json.dumps(cb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written")


main()
