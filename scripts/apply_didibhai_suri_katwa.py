#!/usr/bin/env python3
"""Add Didibhai Bus Service (Suri <-> Katwa), from a Facebook group
report received 2026-09-27 announcing the route's inauguration.

Route: Suri -> Kirnahar -> Katwa via Purundur, Ahmedpur, Chouhatta, Labhpur,
Laghata, Akupurchati, Kirnahar, Daskalgram, Futishanko, Kandra, Komorpur,
Nirol, Pachundi, Ketugram.

The post gives one morning service Suri -> Katwa (6:10 AM to 9:40 AM) and
one afternoon return Katwa -> Suri (3:10 PM to 6:30 PM), both added as
separate searchable listings. Reg no WB 53 B 8677. The post notes this is
the first bus of the morning from Suri and the last direct bus back from
Katwa. Stops without times in the report carry no times.

Only appends to data/community_buses.json; the merge into site data is
done by scripts/add_community_buses.py --write (run separately).
Idempotent: re-running does nothing if the entries are already present.
"""
import json

SRC = "data/community_buses.json"
REG = "WB53B8677"

# (name, up=Suri->Katwa, down=Katwa->Suri)
STOPS_SD = [
    ("Suri", "6:10 AM", "6:30 PM"),
    ("Purundur", "", ""),
    ("Ahmedpur", "7:10 AM", "5:30 PM"),
    ("Chouhatta", "", ""),
    ("Labhpur", "7:45 AM", "5:05 PM"),
    ("Laghata", "", ""),
    ("Akupurchati", "", ""),
    ("Kirnahar", "8:25 AM", "4:35 PM"),
    ("Daskalgram", "", ""),
    ("Futishanko", "8:45 AM", "4:05 PM"),
    ("Kandra", "", ""),
    ("Komorpur", "", ""),
    ("Nirol", "", ""),
    ("Pachundi", "9:15 AM", "3:40 PM"),
    ("Ketugram", "", ""),
    ("Katwa", "9:40 AM", "3:10 PM"),
]

OUTBOUND = {
    "operator": "Didibhai",
    "bus_name": "Didibhai Suri-Katwa",
    "bus_type": "Private",
    "reg_no": REG,
    "origin": "Suri",
    "destination": "Katwa",
    "departure_time": "6:10 AM",
    "arrival_time": "9:40 AM",
    "route": "Suri - Katwa (via Labhpur, Kirnahar)",
    "source": "facebook (community report)",
    "detail_url": "",
    "contact_number": "",
    "stops": [{"name": n, "up": u, "down": d} for n, u, d in STOPS_SD],
}

RETURN = {
    "operator": "Didibhai",
    "bus_name": "Didibhai Suri-Katwa",
    "bus_type": "Private",
    "reg_no": REG,
    "origin": "Katwa",
    "destination": "Suri",
    "departure_time": "3:10 PM",
    "arrival_time": "6:30 PM",
    "route": "Katwa - Suri (via Kirnahar, Labhpur)",
    "source": "facebook (community report)",
    "detail_url": "",
    "contact_number": "",
    "stops": [{"name": n, "up": d, "down": u} for n, u, d in reversed(STOPS_SD)],
}


def main():
    with open(SRC, encoding="utf-8") as f:
        report = json.load(f)
    changed = False
    for key, entry in (("Suri->Katwa", OUTBOUND), ("Katwa->Suri", RETURN)):
        have = any(
            (e.get("origin") == entry["origin"]
             and e.get("destination") == entry["destination"]
             and e.get("bus_name") == entry["bus_name"]
             and e.get("operator") == entry["operator"])
            for e in report.get("add", [])
        )
        if not have:
            report.setdefault("add", []).append(entry)
            changed = True
            print("appended:", key)
        else:
            print("already present:", key)
    if changed:
        with open(SRC, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        print("written.")
    else:
        print("nothing to do.")


if __name__ == "__main__":
    main()

