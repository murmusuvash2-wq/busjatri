#!/usr/bin/env python3
"""FB community update (Vishwakarma Puja report, 2026-09-18):

1. MAA LAXMI (bussathi-maa-laxmi-892, reg WB41S6980) no longer runs
   Manbazar -> Bardhaman. It now runs Indas <-> Bardhaman
   (Indas 9:40 AM -> Bardhaman Alisha 11:05 AM, return
   Bardhaman 11:50 AM -> Indas 2:10 PM). The old bussathi.in stop
   list was also mismatched (Nadia-route stops on a Bankura route).
2. SNEMITA PARIBAHAN (AC Seater/Sleeper, WB 31AB 4746) -
   Kolkata (Dharmatala) <-> Digha Border (Udaypur) appended to
   data/community_buses.json.

Idempotent: re-running makes no changes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv

MAA_LAXMI_STOPS = [
    ("Indas", "9:40 AM", "2:10 PM"),
    ("Sashpur", "9:50 AM", "1:25 PM"),
    ("Bamniahat", "10:20 AM", "1:05 PM"),
    ("Uchalan", "10:30 AM", "12:50 PM"),
    ("Moghalmari", "10:40 AM", "12:40 PM"),
    ("Seharabazar", "10:45 AM", "12:35 PM"),
    ("Bankura More", "10:55 AM", "12:20 PM"),
    ("Telipukur", "11:00 AM", "12:10 PM"),
    ("Bardhaman Alisha Bus Stand", "11:05 AM", "11:50 AM"),
]

SNEMITA = {
    "operator": "Snemita Paribahan",
    "bus_name": "Snemita Paribahan Kolkata-Digha Border (AC Coach)",
    "bus_type": "Private - AC Seater/Sleeper",
    "reg_no": "WB 31AB 4746",
    "origin": "Kolkata (Dharmatala)",
    "destination": "Digha Border (Udaypur)",
    "departure_time": "7:00 AM",
    "arrival_time": "11:45 AM",
    "route": "Kolkata (Dharmatala) - Digha Border (Udaypur)",
    "source": "facebook (community report)",
    "detail_url": "",
    "contact_number": "9635766935",
    "stops": [
        ("Kolkata (Dharmatala)", "7:00 AM", ""),
        ("Park Street", "", ""),
        ("PTI", "", ""),
        ("Hastings", "", ""),
        ("Second Hooghly Bridge", "", ""),
        ("Nabanna", "", ""),
        ("Carry Road", "", ""),
        ("Belepole", "", ""),
        ("Santragachi", "", ""),
        ("Ankurhati", "", ""),
        ("Alampur", "", ""),
        ("Dhulagarh", "8:00 AM", ""),
        ("Ranihati", "", ""),
        ("Panchla", "", ""),
        ("Uluberia (Nimidighi)", "", ""),
        ("Bagnan", "", ""),
        ("Kolaghat", "", ""),
        ("Mecheda", "9:00 AM", "1:00 AM"),
        ("Radhamani", "", ""),
        ("Nimtouri", "", ""),
        ("Nandakumar (Highroad)", "9:30 AM", ""),
        ("Norghat", "", ""),
        ("Chandipur", "", ""),
        ("Bajkul", "", ""),
        ("Heria", "10:05 AM", "11:55 PM"),
        ("Kalingar", "", ""),
        ("Nachinda", "", ""),
        ("Marishda", "", ""),
        ("Kanthi Rupsi Bypass", "", ""),
        ("Kanthi Central Bus Stand", "10:35 AM", "11:25 PM"),
        ("Ghatua", "", ""),
        ("Pichabani", "", ""),
        ("Chaulkhola (Mandarmani)", "", ""),
        ("Balisai (Tajpur)", "", ""),
        ("Chhodomile (Shankarpur)", "", ""),
        ("Thikra More", "", ""),
        ("Alankarpur", "", ""),
        ("Old Digha", "", ""),
        ("New Digha", "", "10:20 PM"),
        ("Digha Border (Udaypur)", "11:45 AM", ""),
    ],
}


def main():
    changed = False

    # --- 1. update MAA LAXMI in main data ---
    p = ROOT / "data" / "busjatri_data.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    matches = [b for b in d["buses"] if b["id"] == "bussathi-maa-laxmi-892"]
    assert len(matches) == 1, f"maa laxmi: expected 1 match, got {len(matches)}"
    b = matches[0]
    if b.get("origin") != "Indas":
        b.update(
            {
                "bus_name": "MAA LAXMI",
                "operator": "Maa Laxmi Travels",
                "bus_type": "Private - Non AC",
                "reg_no": "WB 41S 6980",
                "origin": "Indas",
                "destination": "Bardhaman",
                "departure_time": "9:40 AM",
                "arrival_time": "11:05 AM",
                "contact_number": "",
                "route": "Indas - Bardhaman",
                "stoppages": [
                    {"no": i + 1, "name": n, "up_time": up, "down_time": down}
                    for i, (n, up, down) in enumerate(MAA_LAXMI_STOPS)
                ],
                "source": "facebook (community report)",
                "detail_url": "",
                "total_stoppages": len(MAA_LAXMI_STOPS),
            }
        )
        changed = True
        print("MAA LAXMI updated: Indas -> Bardhaman (route change)")
    else:
        print("MAA LAXMI already updated - skip")

    # --- 2. append SNEMITA to community_buses.json ---
    pc = ROOT / "data" / "community_buses.json"
    cb = json.loads(pc.read_text(encoding="utf-8"))
    if not any("Snemita" in (e.get("bus_name") or "") for e in cb.get("add", [])):
        cb["add"].append(
            {
                **SNEMITA,
                "stops": [
                    {"name": n, "up": up, "down": down}
                    for n, up, down in SNEMITA["stops"]
                ],
            }
        )
        changed = True
        print("SNEMITA appended to community_buses.json")
    else:
        print("SNEMITA already present - skip")

    if DRY or not changed:
        print("dry run or no changes - nothing written")
        return
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    pc.write_text(json.dumps(cb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written")


main()
