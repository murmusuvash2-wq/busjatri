#!/usr/bin/env python3
"""FB community update (report, 2026-09-19, batch 2): 6 buses checked, actions:

1. MAA BINAPANI (Super Fast) Kantakhali <-> Jhargram via Medinipur - NEW.
   Up: Kantakhali 6:30 AM -> Medinipur 9:45 AM -> Jhargram 11:00 AM.
   Down: Jhargram 11:20 AM -> Panchmathar More 11:35 AM -> Medinipur 1:15 PM.
   -> appended to data/community_buses.json (add).

2. SBSTC (Purulia Depot) WB 39B 9072 Purulia <-> Durgapur via Bankura - NEW
   (this bus previously ran to Katwa; now truncated to Durgapur).
   Up: Purulia 9:05 AM -> City Center 1:00 PM.
   Down: Durgapur 8:40 AM -> Purulia 12:45 PM.
   -> appended to data/community_buses.json (add).

3. SBSTC (Durgapur Depot) WB 39C 5072 Durgapur <-> Balrampur via Asansol,
   Purulia - NEW. Only bus on this route.
   Up: Durgapur 5:30 AM -> Balrampur 10:10 AM.
   Down: Balrampur 10:35 AM -> Durgapur 4:00 PM.
   -> appended to data/community_buses.json (add).

4. GOBINDA AISHANI (Super Fast) Medinipur <-> Contai via Belda, Egra - NEW.
   Up: Medinipur 8:05 AM -> Contai 11:35 AM.
   Down: Contai 2:30 PM -> Medinipur 5:15 PM.
   -> appended to data/community_buses.json (add).

5. ARMAN (WB33D4137) + RUDRANI (WB33D3454) Purulia <-> Digha - already in
   data from bussathi.in as two separate buses with the same times and the
   same contact number as the report. No action.

6. NEW AHAN WB50AB9284 - added in the previous batch. No action.

(BABA BAIDYANATH schedule conflict in this report vs previous report is
NOT handled here - pending owner confirmation.)

Idempotent: re-running never duplicates.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv

SRC = "facebook (community report)"

NEW_BUSES = [
    {
        "operator": "Maa Binapani",
        "bus_name": "MAA BINAPANI",
        "bus_type": "Private - Non AC",
        "reg_no": "",
        "origin": "Kantakhali",
        "destination": "Jhargram",
        "departure_time": "6:30 AM",
        "arrival_time": "11:00 AM",
        "route": "Kantakhali - Medinipur - Jhargram",
        "source": SRC,
        "detail_url": "",
        "stops": [
            ("Kantakhali", "6:30 AM", ""),
            ("Ruinan", "", ""),
            ("Sabong", "", ""),
            ("Temathani", "", ""),
            ("Jamna", "", ""),
            ("Barbetia", "", ""),
            ("Kharagpur", "", ""),
            ("Medinipur", "9:45 AM", "1:15 PM"),
            ("Gurguripal", "", ""),
            ("Chandra", "", ""),
            ("Dherua", "", ""),
            ("Baita", "", ""),
            ("Sebayatan", "", ""),
            ("Radhanagar", "", ""),
            ("Panchmathar More", "", "11:35 AM"),
            ("Jhargram", "11:00 AM", "11:20 AM"),
        ],
    },
    {
        "operator": "SBSTC",
        "bus_name": "SBSTC Purulia-Durgapur",
        "bus_type": "Government - SBSTC",
        "reg_no": "WB 39B 9072",
        "depot_name": "Purulia Depot",
        "origin": "Purulia",
        "destination": "Durgapur",
        "departure_time": "9:05 AM",
        "arrival_time": "1:00 PM",
        "route": "Purulia - Bankura - Durgapur",
        "source": SRC,
        "detail_url": "",
        "stops": [
            ("Purulia", "9:05 AM", "12:45 PM"),
            ("Lalpur", "10:00 AM", "11:45 AM"),
            ("Hura", "", ""),
            ("Bishpuriya", "10:20 AM", "11:25 AM"),
            ("Kamalpur", "10:40 AM", "11:00 AM"),
            ("Kharbona", "11:00 AM", "10:50 AM"),
            ("Chhatna", "", ""),
            ("Bankura", "11:25 AM", "10:20 AM"),
            ("Beliator", "", ""),
            ("Barjora", "", ""),
            ("Durgapur", "", "8:40 AM"),
            ("City Center", "1:00 PM", ""),
        ],
    },
    {
        "operator": "SBSTC",
        "bus_name": "SBSTC Durgapur-Balrampur",
        "bus_type": "Government - SBSTC",
        "reg_no": "WB 39C 5072",
        "depot_name": "Durgapur Depot",
        "origin": "Durgapur",
        "destination": "Balrampur",
        "departure_time": "5:30 AM",
        "arrival_time": "10:10 AM",
        "route": "Durgapur - Asansol - Purulia - Balrampur",
        "source": SRC,
        "detail_url": "",
        "stops": [
            ("Durgapur", "5:30 AM", "4:00 PM"),
            ("City Center", "5:40 AM", "3:40 PM"),
            ("Andal", "", ""),
            ("Raniganj", "", ""),
            ("Asansol", "6:40 AM", "2:40 PM"),
            ("Niyamatpur", "", ""),
            ("D. Ghat", "", ""),
            ("Sorbari More", "7:20 AM", "2:00 PM"),
            ("Gobag", "", ""),
            ("Raghunathpur", "8:10 AM", "1:10 PM"),
            ("Anara", "", ""),
            ("Jhapra", "", ""),
            ("Golakunda", "8:40 AM", "12:30 PM"),
            ("Purulia", "9:15 AM", "12:00 PM"),
            ("Kantadi", "9:40 AM", "11:10 AM"),
            ("Urma", "", ""),
            ("Balrampur", "10:10 AM", "10:35 AM"),
        ],
    },
    {
        "operator": "Gobinda Aishani",
        "bus_name": "GOBINDA AISHANI",
        "bus_type": "Private - Non AC",
        "reg_no": "",
        "origin": "Medinipur",
        "destination": "Contai",
        "departure_time": "8:05 AM",
        "arrival_time": "11:35 AM",
        "route": "Medinipur - Belda - Contai",
        "source": SRC,
        "detail_url": "",
        "stops": [
            ("Medinipur", "8:05 AM", "5:15 PM"),
            ("Kharagpur", "9:05 AM", "4:40 PM"),
            ("Belda", "10:05 AM", "4:00 PM"),
            ("Thakurchak", "10:15 AM", "4:10 PM"),
            ("Khakurda", "10:35 AM", "4:25 PM"),
            ("Egra", "10:55 AM", "3:15 PM"),
            ("Contai", "11:35 AM", "2:30 PM"),
        ],
    },
]


def main():
    pc = ROOT / "data" / "community_buses.json"
    cb = json.loads(pc.read_text(encoding="utf-8"))

    changed = False
    for bus in NEW_BUSES:
        if any(
            (e.get("origin") or "").lower() == bus["origin"].lower()
            and (e.get("destination") or "").lower() == bus["destination"].lower()
            and (e.get("operator") or "").lower() == bus["operator"].lower()
            for e in cb.get("add", [])
        ):
            print("%s already present - skip" % bus["bus_name"])
            continue
        entry = {k: v for k, v in bus.items() if k != "stops"}
        entry["stops"] = [
            {"name": n, "up": up, "down": down} for n, up, down in bus["stops"]
        ]
        cb["add"].append(entry)
        changed = True
        print("%s appended to community_buses.json" % bus["bus_name"])

    if DRY or not changed:
        print("dry run or no changes - nothing written")
        return
    pc.write_text(json.dumps(cb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written")


main()
