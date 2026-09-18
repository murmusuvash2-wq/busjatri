#!/usr/bin/env python3
"""Batch-4 dedup fixes: three community entries matched existing buses.

1. LALKAMAL  - bussathi-lalkamal-348 (reg WB33L8127) == community entry
   (reg WB 33L 8127). Duplicate removed; 348 already carries times/contact.
2. MAA PARUL - bussathi-maa-parul-419 (4:30 AM, Jayrambati-Durgapur) ==
   community entry (same route/time). Merge FB data into 419 (duo regs
   WB 67 3747 & WB 67C 2099), remove community entry.
3. MAHAMAYA  - bussathi-mahamaya-458 (reg WB29E4991) == community entry
   (WB 29E 4991 & 4954 duo, Kolkata Station-Manbazar). Merge FB data
   into 458, remove community entry.

All three community entries also removed from community_buses.json queue.

Idempotent: re-running makes no changes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv

LALKAMAL_NAME = "Lalkamal Kharagpur-Manbazar (Super Fast)"
MAA_PARUL_NAME = "Maa Parul Jayrambati-Durgapur"
MAHAMAYA_NAME = "Mahamaya Kolkata Station-Manbazar (STA Super Fast)"

MAA_PARUL_STOPS = [
    ("Jayrambati", "4:30 AM", "5:45 PM"),
    ("Ramdiha", "4:50 AM", "5:30 PM"),
    ("Kuchakol", "", ""),
    ("Moynapur", "5:15 AM", "4:40 PM"),
    ("Jaypur", "5:35 AM", "4:25 PM"),
    ("Bishnupur", "6:20 AM", "3:40 PM"),
    ("Ramsagar", "", ""),
    ("Onda", "", ""),
    ("Kalisen", "", ""),
    ("Dholdanga", "", ""),
    ("Bankura", "8:10 AM", "2:10 PM"),
    ("Hevry More", "", ""),
    ("Bikna", "", ""),
    ("Makurgram", "", ""),
    ("Beliatore", "", ""),
    ("Barjora", "", ""),
    ("Durgapur (Station)", "9:55 AM", "11:40 AM"),
]

MAHAMAYA_STOPS = [
    ("Kolkata Station", "4:30 AM", "5:50 PM"),
    ("Shyambazar", "4:40 AM", "5:40 PM"),
    ("Chiria More", "", ""),
    ("Sinthi More", "", ""),
    ("Baranagar", "", ""),
    ("Dum Dum Airport", "", ""),
    ("Dunlop", "4:57 AM", "5:30 PM"),
    ("Dakshineswar", "", ""),
    ("Bally", "", ""),
    ("Bali Halt", "5:05 AM", "5:20 PM"),
    ("Dankuni", "5:20 AM", "5:10 PM"),
    ("Chanditala", "5:30 AM", "5:05 PM"),
    ("Mashat", "", ""),
    ("Siyakhala", "5:45 AM", "4:45 PM"),
    ("Gajar More", "", ""),
    ("Champadanga", "6:20 AM", "4:10 PM"),
    ("Sodepur", "", ""),
    ("Arambagh", "7:20 AM", "3:25 PM"),
    ("Bengai", "", ""),
    ("Khatul", "", ""),
    ("Kotulpur", "8:05 AM", "2:30 PM"),
    ("Jaypur", "", ""),
    ("Bishnupur", "9:15 AM", "1:25 PM"),
    ("Ramsagar", "", ""),
    ("Onda", "", ""),
    ("Dholdanga More", "", ""),
    ("Bankura Bypass", "", ""),
    ("Tamlibandh", "", ""),
    ("Bankura Pump More", "10:50 AM", "11:55 AM"),
    ("Shunukpahari", "11:00 AM", "11:30 AM"),
    ("Puabagan", "", ""),
    ("Bangla", "11:15 AM", "11:15 AM"),
    ("Molian", "11:35 AM", "10:55 AM"),
    ("Gadapathar", "", ""),
    ("Payrachali", "11:55 AM", "10:35 AM"),
    ("Manbazar", "12:10 PM", "10:20 AM"),
]


def upd(bus, fields, stops, marker):
    names = [s.get("name") for s in bus.get("stoppages") or []]
    if marker in names and bus.get("total_stoppages") == len(stops):
        return False
    f = dict(fields)
    f["stoppages"] = [
        {"no": i + 1, "name": n, "up_time": u, "down_time": d}
        for i, (n, u, d) in enumerate(stops)
    ]
    f["total_stoppages"] = len(stops)
    bus.update(f)
    return True


def main():
    changed = False
    p = ROOT / "data" / "busjatri_data.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    by_id = {b["id"]: b for b in d["buses"]}

    # --- remove community duplicates by name ---
    dup_names = [LALKAMAL_NAME, MAA_PARUL_NAME, MAHAMAYA_NAME]
    removed = [b["id"] for b in d["buses"] if b.get("bus_name") in dup_names]
    if removed:
        d["buses"] = [b for b in d["buses"] if b.get("bus_name") not in dup_names]
        changed = True
        print("removed community duplicates:", ", ".join(removed))
    else:
        print("community duplicates already removed - skip")

    # --- enrich MAA PARUL 419 ---
    b = by_id.get("bussathi-maa-parul-419")
    assert b, "missing bussathi-maa-parul-419"
    if upd(
        b,
        {
            "bus_name": "MAA PARUL (Maa Santoshi)",
            "operator": "Maa Parul",
            "bus_type": "Private",
            "origin": "Jayrambati",
            "destination": "Durgapur (Station)",
            "departure_time": "4:30 AM",
            "arrival_time": "9:55 AM",
            "reg_no": "WB 67 3747 & WB 67C 2099",
            "route": "Jayrambati - Bishnupur - Bankura - Durgapur",
        },
        MAA_PARUL_STOPS,
        "Kuchakol",
    ):
        changed = True
        print(f"MAA PARUL 419: enriched ({len(MAA_PARUL_STOPS)} stops)")
    else:
        print("MAA PARUL 419: already enriched - skip")

    # --- enrich MAHAMAYA 458 ---
    b = by_id.get("bussathi-mahamaya-458")
    assert b, "missing bussathi-mahamaya-458"
    if upd(
        b,
        {
            "bus_name": "MAHAMAYA (STA Super Fast)",
            "operator": "Mahamaya",
            "bus_type": "Private",
            "origin": "Kolkata",
            "destination": "Manbazar",
            "departure_time": "4:30 AM",
            "arrival_time": "12:10 PM",
            "reg_no": "WB 29E 4991 & WB 29E 4954",
            "contact_number": "9474154532",
            "route": "Kolkata Station - Arambagh - Bishnupur - Bankura - Manbazar",
        },
        MAHAMAYA_STOPS,
        "Tamlibandh",
    ):
        changed = True
        print(f"MAHAMAYA 458: enriched ({len(MAHAMAYA_STOPS)} stops)")
    else:
        print("MAHAMAYA 458: already enriched - skip")

    # --- also drop from community queue ---
    pc = ROOT / "data" / "community_buses.json"
    cb = json.loads(pc.read_text(encoding="utf-8"))
    before = len(cb.get("add", []))
    cb["add"] = [x for x in cb.get("add", []) if x.get("bus_name") not in dup_names]
    if len(cb["add"]) != before:
        changed = True
        print("removed from community queue:", before - len(cb["add"]))

    if DRY or not changed:
        print("dry run or no changes - nothing written")
        return
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    pc.write_text(json.dumps(cb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written")


main()
