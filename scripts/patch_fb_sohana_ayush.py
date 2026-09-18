#!/usr/bin/env python3
"""FB community update (Subrata report, 2026-09-18):

1. AYUSH RIYA (Devi Maa Bargabhima) - NEW premium 2/1 AC sleeper.
   Berhampore 6:50 PM -> Krishnanagar 9:30 PM -> Kolkata 2:00 AM -> Digha.
   Return: Digha 9:00 PM -> Kanthi 10:00 PM -> Kolkata 2:00 AM.
   Reg WB 29J 9676, Tata LPO 1822C BS VI. Contact 9647062600.
   Appended to data/community_buses.json.

2. SOHANA PARIBAHAN (bussathi-sohana-749, reg WB29C4818) - same bus
   already in data (Digha -> Barasat 6:20 AM); enriched with the full
   31-stop route from the FB report + return times
   (Dunlop 10:20 AM up; Barasat 12:15 PM, Dunlop 1:10 PM down).
   Old bussathi stop times were partially garbled.

Idempotent: re-running makes no changes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv

SOHANA_STOPS = [
    ("Digha", "6:20 AM", ""),
    ("Digha Border (Udaypur)", "", ""),
    ("New Digha", "", ""),
    ("Old Digha", "", ""),
    ("Ramnagar", "", ""),
    ("Chaulkhola (Mandarmani)", "", ""),
    ("Pichabani", "", ""),
    ("Kanthi", "7:20 AM", ""),
    ("Nachinda", "", ""),
    ("Heria", "", ""),
    ("Bajkul", "", ""),
    ("Chandipur", "", ""),
    ("Nandakumar", "", ""),
    ("Nimtouri", "", ""),
    ("Radhamani", "", ""),
    ("Mecheda", "", ""),
    ("Kolaghat", "", ""),
    ("Bagnan", "", ""),
    ("Uluberia", "", ""),
    ("Dhulagarh", "", ""),
    ("Kona", "", ""),
    ("Bali Halt", "", ""),
    ("Dakshineswar", "", ""),
    ("Dunlop", "10:20 AM", "1:10 PM"),
    ("Belgharia", "", ""),
    ("Expressway", "", ""),
    ("Airport No.3", "", ""),
    ("Birati", "", ""),
    ("Madhyamgram", "", ""),
    ("Champadali More", "", ""),
    ("Barasat", "", "12:15 PM"),
]

AYUSH = {
    "operator": "Ayush Riya",
    "bus_name": "Ayush Riya (Devi Maa Bargabhima) Berhampore-Digha AC Sleeper",
    "bus_type": "Private - AC Sleeper (2/1)",
    "reg_no": "WB 29J 9676",
    "origin": "Berhampore",
    "destination": "Digha",
    "departure_time": "6:50 PM",
    "arrival_time": "",
    "route": "Berhampore - Digha",
    "source": "facebook (community report)",
    "detail_url": "",
    "contact_number": "9647062600",
    "stops": [
        ("Berhampore", "6:50 PM", ""),
        ("Beldanga", "", ""),
        ("Rejinagar", "", ""),
        ("Palashi", "", ""),
        ("Dhubulia", "", ""),
        ("Krishnanagar", "9:30 PM", ""),
        ("Santipur Bypass", "", ""),
        ("Fulia", "", ""),
        ("Ranaghat", "", ""),
        ("Chakdaha", "", ""),
        ("Jagulia", "", ""),
        ("Awalsiddhi", "", ""),
        ("Barasat", "", ""),
        ("Madhyamgram", "", ""),
        ("Airport", "", ""),
        ("Baguihati", "", ""),
        ("Ultodanga", "", ""),
        ("Sealdah", "", ""),
        ("Dharmatala", "2:00 AM", "2:00 AM"),
        ("Santragachi", "", ""),
        ("Dhulagarh", "", ""),
        ("Kolaghat", "", ""),
        ("Mecheda", "", ""),
        ("Nimtouri", "", ""),
        ("Nandakumar", "", ""),
        ("Nachinda", "", ""),
        ("Kanthi", "", "10:00 PM"),
        ("Chaulkhola", "", ""),
        ("Ramnagar", "", ""),
        ("Digha", "", "9:00 PM"),
    ],
}


def main():
    changed = False

    # --- 1. enrich SOHANA PARIBAHAN in main data ---
    p = ROOT / "data" / "busjatri_data.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    matches = [b for b in d["buses"] if b["id"] == "bussathi-sohana-749"]
    assert len(matches) == 1, f"sohana: expected 1 match, got {len(matches)}"
    b = matches[0]
    stop_names = [s.get("name") for s in b.get("stoppages") or []]
    if "Digha Border (Udaypur)" not in stop_names:
        b.update(
            {
                "bus_name": "SOHANA PARIBAHAN",
                "operator": "Sohana Paribahan",
                "bus_type": "Private - AC",
                "reg_no": "WB 29C 4818",
                "origin": "Digha",
                "destination": "Barasat",
                "departure_time": "6:20 AM",
                "arrival_time": "11:00 AM",
                "contact_number": "9647062600, 9091294818",
                "route": "Digha - Barasat",
                "stoppages": [
                    {"no": i + 1, "name": n, "up_time": up, "down_time": down}
                    for i, (n, up, down) in enumerate(SOHANA_STOPS)
                ],
                "total_stoppages": len(SOHANA_STOPS),
            }
        )
        changed = True
        print("SOHANA PARIBAHAN enriched: 31-stop route + return times")
    else:
        print("SOHANA PARIBAHAN already enriched - skip")

    # --- 2. append AYUSH RIYA to community_buses.json ---
    pc = ROOT / "data" / "community_buses.json"
    cb = json.loads(pc.read_text(encoding="utf-8"))
    if not any("Ayush Riya" in (e.get("bus_name") or "") for e in cb.get("add", [])):
        cb["add"].append(
            {
                **AYUSH,
                "stops": [
                    {"name": n, "up": up, "down": down}
                    for n, up, down in AYUSH["stops"]
                ],
            }
        )
        changed = True
        print("AYUSH RIYA appended to community_buses.json")
    else:
        print("AYUSH RIYA already present - skip")

    if DRY or not changed:
        print("dry run or no changes - nothing written")
        return
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    pc.write_text(json.dumps(cb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written")


main()
