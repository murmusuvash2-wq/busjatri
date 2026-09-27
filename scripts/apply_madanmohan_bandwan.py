#!/usr/bin/env python3
"""Add MADAN MOHAN (SuperFast) return trip + fill missing outbound times,
from a Facebook group report received 2026-09-27.

Route: Durgapur (Station) <-> Bandwan via Barjora, Beliatore, Makurgram,
Bankura, Dhaldanga, Puabagan, Bangla, Hatirampur, Manbazar.

What the report adds:
  1. ADD  - the return trip Bandwan -> Durgapur (Station), 10:30 AM to
     3:05 PM, as its own searchable listing (the outbound 6:05 AM listing
     already exists as bussathi-madanmohan-452).
  2. ENRICH - the existing outbound entry gets its missing up-direction
     times (Bangla 8:15, Hatirampur 8:45, Manbazar 9:20, Bandwan 10:20)
     and the FB report's departure times on the way back (Barjora 2:45,
     Bankura 1:45). Stops from the original entry (Sunukpahari, Indpur)
     are preserved; new via stops from the report (Bheduashol, Gobindpur,
     Ledakendi, Gadapathar, Khariduar, Kumari, Boro, Ankhro, Bankura
     Bypass) are added without times.

Reg no: existing entry says WB67B4671; the FB post says WB 67B 4771.
The existing value is kept until confirmed against the vehicle.

Only appends to data/community_buses.json; the merge into site data is
done by scripts/add_community_buses.py --write (run separately).
Idempotent: re-running does nothing if the entries are already present.
"""
import json

SRC = "data/community_buses.json"
TARGET_ID = "bussathi-madanmohan-452"
REG = "WB67B4671"


def stop(n, u="", d=""):
    return {"name": n, "up": u, "down": d}


# Return trip (own direction = Bandwan -> Durgapur; up = that direction,
# down = the Durgapur -> Bandwan direction).
RETURN_ENTRY = {
    "operator": "Madan Mohan",
    "bus_name": "MADANMOHAN",
    "bus_type": "Private - NON AC",
    "reg_no": REG,
    "origin": "Bandwan",
    "destination": "Durgapur (Station)",
    "departure_time": "10:30 AM",
    "arrival_time": "3:05 PM",
    "route": "Bandwan - Durgapur (Station) (via Manbazar, Hatirampur, Bangla, Bankura, Beliatore, Barjora)",
    "source": "facebook (community report)",
    "detail_url": "",
    "contact_number": "",
    "stops": [
        stop("Bandwan", "10:30 AM", "10:20 AM"),
        stop("Ankhro"),
        stop("Boro"),
        stop("Kumari"),
        stop("Khariduar"),
        stop("Manbazar", "11:35 AM", "9:20 AM"),
        stop("Pairachali"),
        stop("Gadapathar"),
        stop("Ledakendi"),
        stop("Gobindpur"),
        stop("Bheduashol"),
        stop("Hatirampur", "12:25 PM", "8:45 AM"),
        stop("Bangla", "12:55 PM", "8:15 AM"),
        stop("Puabagan", "1:10 PM"),
        stop("Dhaldanga", "", "7:55 AM"),
        stop("Bankura", "1:45 PM", "7:30 AM"),
        stop("Bankura Bypass"),
        stop("Makurgram", "", "7:00 AM"),
        stop("Beliatore", "2:25 PM", "6:45 AM"),
        stop("Barjora", "2:45 PM", "6:25 AM"),
        stop("Durgapur (Station)", "3:05 PM", "6:05 AM"),
    ],
}

# Full stop list for the existing outbound entry (Durgapur -> Bandwan).
# up = outbound (Durgapur -> Bandwan), down = return (Bandwan -> Durgapur).
OUTBOUND_STOPS = [
    stop("Durgapur (Station)", "6:05 AM", "3:05 PM"),
    stop("Barjora", "6:25 AM", "2:45 PM"),
    stop("Beliatore", "6:45 AM", "2:25 PM"),
    stop("Makurgram", "7:00 AM", "2:10 PM"),
    stop("Bankura Bypass"),
    stop("Bankura", "7:30 AM", "1:45 PM"),
    stop("Dhaldanga", "7:55 AM", ""),
    stop("Puabagan", "", "1:10 PM"),
    stop("Sunukpahari"),
    stop("Indpur"),
    stop("Bangla", "8:15 AM", "12:55 PM"),
    stop("Bheduashol"),
    stop("Gobindpur"),
    stop("Hatirampur", "8:45 AM", "12:25 PM"),
    stop("Ledakendi"),
    stop("Gadapathar"),
    stop("Pairachali"),
    stop("Manbazar", "9:20 AM", "11:35 AM"),
    stop("Khariduar"),
    stop("Kumari"),
    stop("Boro"),
    stop("Ankhro"),
    stop("Bandwan", "10:20 AM", "10:30 AM"),
]

ENRICH_ENTRY = {
    "target_id": TARGET_ID,
    "arrival_time": "10:20 AM",
    "route": "Durgapur (Station) - Bandwan (via Barjora, Beliatore, Bankura, Bangla, Hatirampur, Manbazar)",
    "time_source": "facebook (community report)",
    "stoppages": [
        {"no": i + 1, "name": s["name"], "up_time": s["up"], "down_time": s["down"]}
        for i, s in enumerate(OUTBOUND_STOPS)
    ],
}


def main():
    with open(SRC, encoding="utf-8") as f:
        report = json.load(f)

    changed = False

    # add: return trip
    have_add = any(
        (e.get("origin") == RETURN_ENTRY["origin"]
         and e.get("destination") == RETURN_ENTRY["destination"]
         and e.get("bus_name") == RETURN_ENTRY["bus_name"])
        for e in report.get("add", [])
    )
    if not have_add:
        report.setdefault("add", []).append(RETURN_ENTRY)
        changed = True
        print("appended: return trip Bandwan -> Durgapur (Station) 10:30 AM")
    else:
        print("add already present")

    # enrich: outbound entry
    have_enrich = any(
        e.get("target_id") == TARGET_ID for e in report.get("enrich", [])
    )
    if not have_enrich:
        report.setdefault("enrich", []).append(ENRICH_ENTRY)
        changed = True
        print("appended: enrich for %s (%d stops)" % (TARGET_ID, len(OUTBOUND_STOPS)))
    else:
        print("enrich already present")

    if changed:
        with open(SRC, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        print("written.")
    else:
        print("nothing to do.")


if __name__ == "__main__":
    main()

