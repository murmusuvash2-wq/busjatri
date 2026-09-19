#!/usr/bin/env python3
"""Swapnamay Travels Haldia-Durgapur community bus (user report, 2026-09-19).

Facebook report: WB 29H 4087, Ashok Leyland 12M FE BS-VI (air suspension),
3x2 pushback seats. Haldia -> Durgapur (City Center) overnight via Tamluk,
Mecheda, Ghatal, Chandrakona, Garhbeta, Bishnupur, Bankura.

Also fixes at data level (enrich): NBSTC Cooch Behar->Siliguri bus
nbstc-in-nbstc-cooch-behar-si-930 lists "12:00 AM" sandwiched between
11:40 AM and 12:20 PM - it is noon, not midnight.

Idempotent: appends only if not already in community_buses.json.
The entry is consumed by add_community_buses.py in the same pipeline run.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITE = "--write" in sys.argv
SRC = ROOT / "data" / "community_buses.json"

SWAPNAMAY = {
    "operator": "Swapnamay Travels",
    "bus_name": "Swapnamay Travels Haldia-Durgapur",
    "bus_type": "Private - Non AC Pushback (Air Suspension)",
    "reg_no": "WB 29H 4087",
    "origin": "Haldia",
    "destination": "Durgapur (City Center)",
    "departure_time": "12:05 AM",
    "arrival_time": "8:35 AM",
    "contact_number": "7478294087 / 9679133932",
    "route": "Haldia - Durgapur (City Center)",
    "source": "facebook (community report)",
    "detail_url": "",
    "stops": [
        {"name": "Haldia", "up": "12:05 AM", "down": "8:35 PM"},
        {"name": "Durgachak", "up": "", "down": ""},
        {"name": "Sutahata", "up": "", "down": ""},
        {"name": "Chaitanyapur", "up": "", "down": ""},
        {"name": "Mahishadal", "up": "", "down": ""},
        {"name": "Tamluk", "up": "1:45 AM", "down": "6:50 PM"},
        {"name": "Mecheda", "up": "2:15 AM", "down": "6:10 PM"},
        {"name": "Mechogram", "up": "", "down": ""},
        {"name": "Keshapat", "up": "", "down": ""},
        {"name": "Khukur Daha", "up": "", "down": ""},
        {"name": "Goura", "up": "", "down": ""},
        {"name": "Sultannagar", "up": "", "down": ""},
        {"name": "Bakultala", "up": "", "down": ""},
        {"name": "Daspur", "up": "", "down": ""},
        {"name": "Ghatal", "up": "3:45 AM", "down": "4:35 PM"},
        {"name": "Barada Chaukun", "up": "", "down": ""},
        {"name": "Radhanagar", "up": "", "down": ""},
        {"name": "Khirpai", "up": "", "down": ""},
        {"name": "Kalikapur", "up": "", "down": ""},
        {"name": "Chandrakona Town", "up": "4:30 AM", "down": "3:45 PM"},
        {"name": "Bahrashol", "up": "", "down": ""},
        {"name": "Andarnayan", "up": "", "down": ""},
        {"name": "Dabcha", "up": "", "down": ""},
        {"name": "Chandrakona Road", "up": "5:05 AM", "down": "3:15 PM"},
        {"name": "Kadamdiha", "up": "", "down": ""},
        {"name": "Kiyabani", "up": "", "down": ""},
        {"name": "Garhbeta", "up": "5:25 AM", "down": "2:50 PM"},
        {"name": "Dadhika", "up": "", "down": ""},
        {"name": "Bankadah", "up": "5:45 AM", "down": "2:25 PM"},
        {"name": "Bishnupur Bypass", "up": "6:15 AM", "down": "2:00 PM"},
        {"name": "Ramsagar", "up": "", "down": ""},
        {"name": "Onda", "up": "", "down": ""},
        {"name": "Dhaladanga", "up": "", "down": ""},
        {"name": "Bankura Bypass", "up": "7:10 AM", "down": "12:50 PM"},
        {"name": "Beliatore", "up": "", "down": ""},
        {"name": "Barjora", "up": "", "down": ""},
        {"name": "Durgapur Station", "up": "8:15 AM", "down": "11:50 AM"},
        {"name": "Durgapur (City Center)", "up": "8:35 AM", "down": "11:10 AM"},
    ],
}

NBSTC_NOON_FIX = {
    "target_id": "nbstc-in-nbstc-cooch-behar-si-930",
    "departure_time": "12:00 PM",
}


def main():
    cb = json.loads(SRC.read_text(encoding="utf-8"))
    changed = False

    have = {(e.get("origin", "").lower(), e.get("destination", "").lower(),
             (e.get("operator") or "").lower()) for e in cb.get("add", [])}
    if ("haldia", "durgapur (city center)", "swapnamay travels") not in have:
        cb.setdefault("add", []).append(SWAPNAMAY)
        changed = True
        print("appended: Swapnamay Travels Haldia -> Durgapur (City Center)")
    else:
        print("ok (already present): Swapnamay Travels")

    if not any(e.get("target_id") == NBSTC_NOON_FIX["target_id"]
              for e in cb.get("enrich", [])):
        cb.setdefault("enrich", []).append(NBSTC_NOON_FIX)
        changed = True
        print("appended: enrich NBSTC 12:00 AM -> 12:00 PM")
    else:
        print("ok (already present): NBSTC noon fix")

    if changed:
        if WRITE:
            SRC.write_text(json.dumps(cb, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
            print("written: data/community_buses.json")
        else:
            print("dry run - nothing written (use --write)")


if __name__ == "__main__":
    main()
