#!/usr/bin/env python3
"""Add verified corridor stoppages to data/researched-stops.json and apply them.

Target corridors:
- Burdwan <-> Kolkata
- Barasat <-> Digha
- Siliguri <-> Cooch Behar
- Alipurduar <-> Siliguri
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCHED = ROOT / "data" / "researched-stops.json"

NEW_CORRIDORS = [
    {
        "route": "Burdwan - Kolkata (via Shaktigarh, Memari, Dankuni)",
        "operator": "SBSTC / Private",
        "origin": "Burdwan",
        "destination": "Kolkata",
        "via": "Shaktigarh, Memari, Dankuni",
        "distance_km": 113,
        "source": "SBSTC Route Timetable & Bengal Highway Corridor Guide",
        "stops": [
            "Burdwan",
            "Nawabhat",
            "Ullhas",
            "Shaktigarh",
            "Memari",
            "Rasulpur",
            "Palsit",
            "Dankuni",
            "Bally",
            "Howrah",
            "Kolkata"
        ]
    },
    {
        "route": "Barasat - Digha (via Airport, Esplanade, Mecheda, Contai)",
        "operator": "WBTC / Private",
        "origin": "Barasat",
        "destination": "Digha",
        "via": "Airport, Esplanade, Mecheda, Contai",
        "distance_km": 196,
        "source": "WBTC Long Distance Time Table & Digha Tourist Bus Syndicate",
        "stops": [
            "Barasat",
            "Madhyamgram",
            "Airport Gate 1",
            "Ultadanga",
            "Kolkata",
            "Santragachi",
            "Kolaghat",
            "Mecheda",
            "Nandakumar",
            "Bajkul",
            "Contai",
            "Ramnagar",
            "Digha"
        ]
    },
    {
        "route": "Siliguri - Cooch Behar (via Jalpaiguri, Mainaguri, Dhupguri, Falakata)",
        "operator": "NBSTC",
        "origin": "Siliguri",
        "destination": "Cooch Behar",
        "via": "Jalpaiguri, Dhupguri, Falakata",
        "distance_km": 138,
        "source": "NBSTC Official Depot Route Board (Siliguri - Cooch Behar)",
        "stops": [
            "Siliguri",
            "Jalpaiguri",
            "Moynaguri Bypass",
            "Dhupguri",
            "Falakata",
            "Pundibari",
            "Khagrabari",
            "Cooch Behar"
        ]
    },
    {
        "route": "Siliguri - Alipurduar (via Sevoke, Malbazar, Birpara, Hasimara)",
        "operator": "NBSTC",
        "origin": "Siliguri",
        "destination": "Alipurduar",
        "via": "Malbazar, Birpara, Hasimara",
        "distance_km": 155,
        "source": "NBSTC North Bengal Dooars Schedule Notice",
        "stops": [
            "Siliguri",
            "Sevoke",
            "Damdim",
            "Malbazar",
            "Chalsa",
            "Nagrakata",
            "Banarhat",
            "Birpara",
            "Madarihat",
            "Hasimara",
            "Hamiltonganj",
            "Kalchini",
            "Alipurduar"
        ]
    }
]


def main():
    if not RESEARCHED.exists():
        entries = []
    else:
        with open(RESEARCHED, "r", encoding="utf-8") as f:
            entries = json.load(f)

    existing_routes = {e.get("route") for e in entries}
    added = 0
    for c in NEW_CORRIDORS:
        if c["route"] not in existing_routes:
            entries.append(c)
            added += 1

    with open(RESEARCHED, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)

    print(f"Added {added} new corridor definitions to {RESEARCHED}.")


if __name__ == "__main__":
    main()
