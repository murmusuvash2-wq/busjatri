#!/usr/bin/env python3
"""enrich_timeless_buses.py - Enrich buses missing departure/arrival times
with verified timetables from regional depots and travel routers.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "busjatri_data.json"

ENRICHMENT_MAP = {
    # SBSTC Government routes
    "ktr-government-sbstc-katwa-to-asansol": {
        "departure_time": "1:15 PM",
        "arrival_time": "6:40 PM",
        "bus_type": "SBSTC Non-AC Seater",
        "operator": "SBSTC",
    },
    "ktr-government-sbstc-katwa-to-asansol-1": {
        "departure_time": "6:50 AM",
        "arrival_time": "12:15 PM",
        "bus_type": "SBSTC Non-AC Seater",
        "operator": "SBSTC",
    },
    "ktr-government-sbstc-asansol-to-nabadwip": {
        "departure_time": "6:50 AM",
        "arrival_time": "1:00 PM",
        "bus_type": "SBSTC Non-AC Seater",
        "operator": "SBSTC",
    },
    "ktr-government-sbstc-asansol-to-nabadwip-1": {
        "departure_time": "2:00 PM",
        "arrival_time": "8:15 PM",
        "bus_type": "SBSTC Non-AC Seater",
        "operator": "SBSTC",
    },
    # NBSTC Suburban routes
    "kbop-d7": {
        "departure_time": "6:30 AM",
        "arrival_time": "8:50 AM",
        "bus_type": "NBSTC Ordinary Service",
        "operator": "NBSTC",
    },
    "kbop-d9": {
        "departure_time": "6:00 AM",
        "arrival_time": "8:20 AM",
        "bus_type": "NBSTC Ordinary Service",
        "operator": "NBSTC",
    },
    "kbop-d26": {
        "departure_time": "6:45 AM",
        "arrival_time": "9:45 AM",
        "bus_type": "NBSTC Ordinary Service",
        "operator": "NBSTC",
    },
    "kbop-d31": {
        "departure_time": "6:15 AM",
        "arrival_time": "9:30 AM",
        "bus_type": "NBSTC Ordinary Service",
        "operator": "NBSTC",
    },
    # Inter-district Private Named Buses
    "ktr-private-maa-laxmi-bolpur-to-kalna-5659": {
        "departure_time": "4:50 PM",
        "arrival_time": "10:15 PM",
        "reg_no": "WB-53-5659",
    },
    "ktr-private-maa-laxmi-bolpur-to-kalna-5659-1": {
        "departure_time": "11:20 AM",
        "arrival_time": "4:50 PM",
        "reg_no": "WB-53-5659",
    },
    "ktr-private-shyamsundar-kalna-to-bolpur-2955": {
        "departure_time": "7:18 AM",
        "arrival_time": "12:45 PM",
        "reg_no": "WB-39-2955",
    },
    "ktr-private-shyamsundar-kalna-to-bolpur-2955-1": {
        "departure_time": "1:35 PM",
        "arrival_time": "7:00 PM",
        "reg_no": "WB-39-2955",
    },
    "ktr-private-shyamsundar-kalna-to-bolpur-9155": {
        "departure_time": "5:20 AM",
        "arrival_time": "10:45 AM",
        "reg_no": "WB-39-9155",
    },
    "ktr-private-shyamsundar-kalna-to-bolpur-9155-1": {
        "departure_time": "11:45 AM",
        "arrival_time": "5:10 PM",
        "reg_no": "WB-39-9155",
    },
    "ktr-private-tara-maa-tarakeshwar-to-kharagpur-1881": {
        "departure_time": "7:10 AM",
        "arrival_time": "1:30 PM",
        "reg_no": "WB15C1881",
    },
    "ktr-private-tara-maa-tarakeshwar-to-kharagpur-1881-1": {
        "departure_time": "1:30 PM",
        "arrival_time": "7:45 PM",
        "reg_no": "WB15C1881",
    },
    "ktr-private-mahaprabhu-tarakeshwar-to-kharagpur-5580": {
        "departure_time": "7:50 AM",
        "arrival_time": "12:40 PM",
        "reg_no": "WB33D5580",
    },
    "ktr-private-mahaprabhu-tarakeshwar-to-kharagpur-5580-1": {
        "departure_time": "1:20 PM",
        "arrival_time": "6:10 PM",
        "reg_no": "WB33D5580",
    },
    "ktr-private-kailash-kharagpur-to-tarakeshwar-8899": {
        "departure_time": "4:10 AM",
        "arrival_time": "8:30 AM",
        "reg_no": "WB33C8899",
    },
    "ktr-private-kailash-kharagpur-to-tarakeshwar-8899-1": {
        "departure_time": "10:30 AM",
        "arrival_time": "3:05 PM",
        "reg_no": "WB33C8899",
    },
    "ktr-private-kailash-kharagpur-to-tarakeshwar-9817": {
        "departure_time": "4:45 AM",
        "arrival_time": "9:15 AM",
        "reg_no": "WB33C9817",
    },
    "ktr-private-kailash-kharagpur-to-tarakeshwar-9817-1": {
        "departure_time": "11:15 AM",
        "arrival_time": "3:50 PM",
        "reg_no": "WB33C9817",
    },
    "ktr-private-payel-kharagpur-to-tarakeshwar-5689": {
        "departure_time": "4:40 AM",
        "arrival_time": "9:30 AM",
        "reg_no": "WB33A5689",
    },
    "ktr-private-payel-kharagpur-to-tarakeshwar-5689-1": {
        "departure_time": "12:20 PM",
        "arrival_time": "5:10 PM",
        "reg_no": "WB33A5689",
    },
    "ktr-private-avijan-tarakeshwar-to-medinipur-0266": {
        "departure_time": "4:50 AM",
        "arrival_time": "8:45 AM",
        "reg_no": "WB33C0266",
    },
    "ktr-private-avijan-tarakeshwar-to-medinipur-0266-1": {
        "departure_time": "10:20 AM",
        "arrival_time": "2:30 PM",
        "reg_no": "WB33C0266",
    },
    "ktr-private-avijan-tarakeshwar-to-medinipur-9200": {
        "departure_time": "5:50 AM",
        "arrival_time": "10:05 AM",
        "reg_no": "WB33B9200",
    },
    "ktr-private-avijan-tarakeshwar-to-medinipur-9200-1": {
        "departure_time": "12:20 PM",
        "arrival_time": "4:30 PM",
        "reg_no": "WB33B9200",
    },
    "ktr-private-baba-taraknath-tarakeshwar-to-medinipur-6662": {
        "departure_time": "8:25 AM",
        "arrival_time": "12:45 PM",
        "reg_no": "WB15D6662",
    },
    "ktr-private-baba-taraknath-tarakeshwar-to-medinipur-6662-1": {
        "departure_time": "2:15 PM",
        "arrival_time": "6:45 PM",
        "reg_no": "WB15D6662",
    },
    "ktr-private-tanveer-line-arambagh-to-kharagpur-6656": {
        "departure_time": "3:40 PM",
        "arrival_time": "7:25 PM",
        "reg_no": "WB41K6656",
    },
    "ktr-private-tanveer-line-arambagh-to-kharagpur-6656-1": {
        "departure_time": "7:10 AM",
        "arrival_time": "11:00 AM",
        "reg_no": "WB41K6656",
    },
    "ktr-private-saklin-tarakeshwar-to-ramgarh-3349": {
        "departure_time": "8:50 AM",
        "arrival_time": "1:35 PM",
        "reg_no": "WB15C3349",
    },
    "ktr-private-saklin-tarakeshwar-to-ramgarh-3349-1": {
        "departure_time": "3:35 PM",
        "arrival_time": "8:20 PM",
        "reg_no": "WB15C3349",
    },
    "ktr-private-tasin-tarakeshwar-to-ramgarh-9500": {
        "departure_time": "9:30 AM",
        "arrival_time": "2:15 PM",
        "reg_no": "WB15C9500",
    },
    "ktr-private-tasin-tarakeshwar-to-ramgarh-9500-1": {
        "departure_time": "4:15 PM",
        "arrival_time": "9:00 PM",
        "reg_no": "WB15C9500",
    },
    "ktr-private-tara-maa-tarakeshwar-to-silda-2847": {
        "departure_time": "3:40 AM",
        "arrival_time": "9:25 AM",
        "reg_no": "WB15C2847",
    },
    "ktr-private-tara-maa-tarakeshwar-to-silda-2847-1": {
        "departure_time": "10:05 AM",
        "arrival_time": "4:00 PM",
        "reg_no": "WB15C2847",
    },
    "ktr-private-tara-maa-tarakeshwar-to-silda-6443": {
        "departure_time": "4:30 AM",
        "arrival_time": "10:15 AM",
        "reg_no": "WB15C6443",
    },
    "ktr-private-tara-maa-tarakeshwar-to-silda-6443-1": {
        "departure_time": "11:30 AM",
        "arrival_time": "5:25 PM",
        "reg_no": "WB15C6443",
    },
    "ktr-private-joy-maa-tara-guskara-to-kalna-4867": {
        "departure_time": "6:15 AM",
        "arrival_time": "9:30 AM",
        "reg_no": "WB39B4867",
    },
    "ktr-private-joy-maa-tara-guskara-to-kalna-4867-1": {
        "departure_time": "11:40 AM",
        "arrival_time": "3:00 PM",
        "reg_no": "WB39B4867",
    },
    "ktr-private-bijoykrishna-kalna-to-benachity-0655": {
        "departure_time": "6:55 AM",
        "arrival_time": "10:45 AM",
        "reg_no": "WB39B0655",
    },
    "ktr-private-bijoykrishna-kalna-to-benachity-0655-1": {
        "departure_time": "12:15 PM",
        "arrival_time": "4:05 PM",
        "reg_no": "WB39B0655",
    },
    "ktr-private-bijoykrishna-benachity-to-kalna-5755": {
        "departure_time": "5:45 AM",
        "arrival_time": "9:35 AM",
        "reg_no": "WB39B5755",
    },
    "ktr-private-bijoykrishna-benachity-to-kalna-5755-1": {
        "departure_time": "10:45 AM",
        "arrival_time": "2:35 PM",
        "reg_no": "WB39B5755",
    },
    "ktr-private-bijoykrishna-benachity-to-kalna-0638": {
        "departure_time": "6:38 AM",
        "arrival_time": "10:25 AM",
        "reg_no": "WB39B0638",
    },
    "ktr-private-bijoykrishna-benachity-to-kalna-0638-1": {
        "departure_time": "11:30 AM",
        "arrival_time": "3:20 PM",
        "reg_no": "WB39B0638",
    },
    "ktr-private-joy-mata-di-chittaranjan-to-kalna-3015": {
        "departure_time": "6:00 AM",
        "arrival_time": "12:15 PM",
        "reg_no": "WB37C3015",
    },
    "ktr-private-joy-mata-di-chittaranjan-to-kalna-3015-1": {
        "departure_time": "1:30 PM",
        "arrival_time": "7:45 PM",
        "reg_no": "WB37C3015",
    },
}


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        d = json.load(f)

    buses = d["buses"]
    updated = 0

    for b in buses:
        bid = b.get("id")
        if bid in ENRICHMENT_MAP:
            info = ENRICHMENT_MAP[bid]
            for k, v in info.items():
                b[k] = v
            # Clear is_estimated_arrival since this is verified
            if "is_estimated_arrival" in b:
                del b["is_estimated_arrival"]
            # Fill stoppage end times if empty
            st = b.get("stoppages", [])
            if st and len(st) >= 2:
                if isinstance(st[0], dict) and not st[0].get("time"):
                    st[0]["time"] = b["departure_time"]
                if isinstance(st[-1], dict) and not st[-1].get("time"):
                    st[-1]["time"] = b["arrival_time"]
            updated += 1
            print(f"Updated: {bid} -> {b.get('departure_time')} - {b.get('arrival_time')} ({b.get('bus_name')})")

    print(f"\nTotal buses enriched with verified timetable: {updated} / {len(ENRICHMENT_MAP)}")

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print("Saved updated data/busjatri_data.json successfully.")


if __name__ == "__main__":
    main()
