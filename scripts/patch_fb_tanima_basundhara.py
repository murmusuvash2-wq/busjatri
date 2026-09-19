#!/usr/bin/env python3
"""FB community update (report, 2026-09-19, batch 3): 8 buses checked, actions:

1. TANIMA (GHOSH MOTORS) - ENRICH bussathi-tanima-810.
   bussathi lists it as Rohini <-> Contai, but the FB report shows the
   bus actually starts at Chandpal (Kolkata): Chandpal 8:35 AM ->
   Rohini 9:40 -> Kultikri 10:00 -> Keshiari 10:40 -> Belda 11:15 ->
   Egra 12:00 PM -> Contai 12:45 PM. Return: Contai 3:50 PM ->
   ... -> Chandpal 8:00 PM. Extends origin to Kolkata (Chandpal),
   adds Kultikri times, updates times per the FB report.

2. BASUNDHARA (SHREE KRISHNA TRAVELS) WB178192 - ENRICH
   bussathi-basundhara-120. Service resumed after accident repair with
   a slightly later up schedule: Kolkata 7:20 AM, Shyambazar 7:30 AM,
   Dunlop 7:50 AM, Dankuni 8:20 AM, Arambagh 10:25 AM (down times
   unchanged). New contact 7595824650.

3. Already fully covered, no action (FB reposts of buses already in data):
   - JAI MAA DURGA Manbazar-Kolkata (bussathi-jai-maa-durga-264, same times)
   - KRISHNA Supa-Baruipur WB39C2142 (krishna-supa-baruipur-4014, same times
     + same contact numbers)
   - MAJOR Durgapur-Bokaro WB37K/H5392 (bussathi-major-467, same times + contact)
   - SANNYASI Kultikri-Bishnupur WB67J5268 (bussathi-sannyasi-684, same times
     + contact)
   - MONAMI TRAVELS Jhargram-Manbazar WB39F2442 (bussathi-monami-507, same times)
   - RBN TRAVELS Kharagpur-Barabazar WB55B7065
     (rbn-travels-kharagpur-barabazar-4016, same times)

Idempotent: re-running never duplicates.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv

TANIMA_STOPS = [
    ("Chandpal", "8:35 AM", "8:00 PM"),
    ("Rohini", "9:40 AM", "6:55 PM"),
    ("Kultikri", "10:00 AM", "6:35 PM"),
    ("Keshiari", "10:40 AM", "5:55 PM"),
    ("Belda", "11:15 AM", "5:20 PM"),
    ("Khakurda", "", ""),
    ("Egra", "12:00 PM", "4:35 PM"),
    ("Contai", "12:45 PM", "3:50 PM"),
]

BASUNDHARA_TIME_FIXES = {
    # stop name -> new up_time (FB report; down times unchanged)
    "Shyambazar": "7:30 AM",
    "Dunlop": "7:50 AM",
    "Dankuni": "8:20 AM",
    "Arambagh": "10:25 AM",
}


def main():
    data_p = ROOT / "data" / "busjatri_data.json"
    d = json.loads(data_p.read_text(encoding="utf-8"))
    buses = {b["id"]: b for b in d["buses"]}

    # --- 1. TANIMA: extend to Chandpal (Kolkata) with FB times ---
    tanima = buses.get("bussathi-tanima-810")
    tanima_stops = None
    if tanima:
        names = [s.get("name") for s in (tanima.get("stoppages") or [])]
        if "Chandpal" not in names:
            tanima_stops = [
                {"no": i + 1, "name": n, "up_time": up, "down_time": down}
                for i, (n, up, down) in enumerate(TANIMA_STOPS)
            ]

    # --- 2. BASUNDHARA: shifted up times from FB report ---
    basun = buses.get("bussathi-basundhara-120")
    basun_stops = None
    if basun:
        stops = [dict(s) for s in (basun.get("stoppages") or [])]
        fixed = 0
        for s in stops:
            if s.get("name") in BASUNDHARA_TIME_FIXES:
                s["up_time"] = BASUNDHARA_TIME_FIXES[s["name"]]
                fixed += 1
        if fixed:
            basun_stops = stops

    pc = ROOT / "data" / "community_buses.json"
    cb = json.loads(pc.read_text(encoding="utf-8"))
    changed = False

    def drop_enrich(target):
        cb["enrich"] = [
            e for e in cb.get("enrich", []) if e.get("target_id") != target
        ]

    if tanima_stops:
        drop_enrich("bussathi-tanima-810")
        cb["enrich"].append(
            {
                "target_id": "bussathi-tanima-810",
                "origin": "Kolkata (Chandpal)",
                "destination": "Contai",
                "departure_time": "8:35 AM",
                "arrival_time": "12:45 PM",
                "route": "Kolkata (Chandpal) - Contai",
                "contact_number": "8967633936, 7001548338",
                "stoppages": tanima_stops,
            }
        )
        changed = True
        print("TANIMA enrich: extended to Kolkata (Chandpal) + FB times")
    else:
        print("TANIMA already enriched or not found - skip")

    if basun_stops:
        drop_enrich("bussathi-basundhara-120")
        cb["enrich"].append(
            {
                "target_id": "bussathi-basundhara-120",
                "contact_number": "7595824650",
                "departure_time": "7:30 AM",
                "stoppages": basun_stops,
            }
        )
        changed = True
        print("BASUNDHARA enrich: shifted up times + new contact")
    else:
        print("BASUNDHARA already enriched or not found - skip")

    if DRY or not changed:
        print("dry run or no changes - nothing written")
        return
    pc.write_text(json.dumps(cb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written")


main()
