#!/usr/bin/env python3
"""Add GOLDEN private bus (Mecheda Station <-> Tarakeswar) from a Facebook
group report received 2026-09-26.

The post advertises a full Gadiara <-> Tarakeswar service via Bagnan,
but states the bus CURRENTLY runs only between Mecheda Station and
Tarakeswar - so only the operational section is recorded. Reg no
WB 29H 2439 (Ashok Leyland Lynx Strong 49 BS-VI), contact numbers
from the post. Intermediate stops between the timed stops are from
the post's via list and carry no times (bus passes them).

Only appends to data/community_buses.json; the merge into site data
is done by scripts/add_community_buses.py --write (run separately).
Idempotent: re-running does nothing if the reg_no is already present.
"""
import json

SRC = "data/community_buses.json"
REG = "WB 29H 2439"


def stop(n, u="", d=""):
    return {"name": n, "up": u, "down": d}


ENTRY = {
    "operator": "Golden",
    "bus_name": "Golden Mecheda-Tarakeswar",
    "bus_type": "Private",
    "reg_no": REG,
    "origin": "Mecheda Station",
    "destination": "Tarakeswar",
    "departure_time": "6:50 AM",
    "arrival_time": "",
    "route": "Mecheda Station - Tarakeswar (via Ghatal, Kamarpukur, Arambagh)",
    "source": "facebook (community report)",
    "detail_url": "",
    "contact_number": "9735509964 / 8116834556",
    "stops": [
        stop("Mecheda Station", "6:50 AM", "4:25 PM"),
        stop("Haldia More"),
        stop("Deulia Bazar"),
        stop("Siddha Bazar"),
        stop("Mechogram", "7:15 AM", "4:00 PM"),
        stop("Khukurdah"),
        stop("Gaura"),
        stop("Daspur"),
        stop("Ghatal", "8:15 AM", "3:05 PM"),
        stop("Borda Chaukan"),
        stop("Khara"),
        stop("Mangrul", "9:10 AM", "2:05 PM"),
        stop("Tatarpur"),
        stop("Hajipur"),
        stop("Kamarpukur", "9:35 AM", "1:35 PM"),
        stop("Goghat"),
        stop("Kalipur"),
        stop("Arambagh", "10:05 AM", "1:10 PM"),
        stop("Mayapur"),
        stop("Kable"),
        stop("Chapadanga"),
        stop("Muktarpur"),
        stop("Ramnarayanpur"),
        stop("Tarakeswar", "", "12:05 PM"),
    ],
}


def main():
    with open(SRC, encoding="utf-8") as f:
        cb = json.load(f)
    if any(e.get("reg_no") == REG for e in cb.get("add", [])):
        print("already present: GOLDEN", REG, "- nothing to do")
        return
    cb["add"].append(ENTRY)
    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(cb, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("appended GOLDEN", REG, "- now", len(cb["add"]), "adds")


if __name__ == "__main__":
    main()
