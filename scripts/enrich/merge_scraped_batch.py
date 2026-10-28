#!/usr/bin/env python3
"""
Merge scraped district and SBSTC buses from bussathi_new_batch.json and wbbus_cards_all.json
into data/busjatri_data.json. Enriches existing matching buses with verified phone contacts,
registrations, and stoppages, and appends brand new unique buses.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data" / "busjatri_data.json"
BUSSATHI_FILE = ROOT / "data-raw" / "bussathi_new_batch.json"
WBBUS_FILE = ROOT / "data-raw" / "wbbus_cards_all.json"


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or "x"


def main():
    print("Loading database...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    buses = data["buses"]
    before_count = len(buses)
    print(f"Starting buses in database: {before_count}")

    existing_ids = set(b.get("id") for b in buses)
    reg_map = {(b.get("reg_no") or "").strip().upper(): b for b in buses if b.get("reg_no")}
    trip_map = {(norm(b.get("origin")), norm(b.get("destination")), norm(b.get("departure_time"))): b for b in buses}

    # 1. Process bussathi batch (319 buses)
    bussathi_added = 0
    bussathi_contacts_enriched = 0
    bussathi_regs_enriched = 0

    if BUSSATHI_FILE.exists():
        with open(BUSSATHI_FILE, "r", encoding="utf-8") as f:
            bussathi = json.load(f)

        for b in bussathi:
            r = (b.get("reg_no") or "").strip().upper()
            tk = (norm(b.get("origin")), norm(b.get("destination")), norm(b.get("departure_time")))
            matched = reg_map.get(r) or trip_map.get(tk)

            if matched:
                if (not matched.get("contact_number") or matched.get("contact_number") == "Not Available !") and (b.get("contact_number") and b.get("contact_number") != "Not Available !"):
                    matched["contact_number"] = b["contact_number"]
                    bussathi_contacts_enriched += 1
                if not matched.get("reg_no") and r:
                    matched["reg_no"] = r
                    bussathi_regs_enriched += 1
            else:
                bid = f"bussathi-{b['bussathi_id']}"
                if bid in existing_ids:
                    bid = f"bussathi-{slug(b['bus_name'])}-{b['bussathi_id']}"
                existing_ids.add(bid)

                new_bus = {
                    "id": bid,
                    "bus_name": b["bus_name"],
                    "reg_no": r,
                    "operator": b.get("operator") or "—",
                    "bus_type": b.get("bus_type") or "Private - NON AC",
                    "origin": b["origin"],
                    "destination": b["destination"],
                    "departure_time": b.get("departure_time", ""),
                    "arrival_time": b.get("arrival_time", ""),
                    "contact_number": b.get("contact_number", "Not Available !"),
                    "depot_name": b.get("depot_name", b["origin"]),
                    "route": b.get("route") or f"{b['origin']} - {b['destination']}",
                    "stoppages": b.get("stoppages", []),
                    "source": "bussathi.in",
                    "total_stoppages": len(b.get("stoppages", [])),
                    "detail_url": b.get("detail_url", "")
                }
                buses.append(new_bus)
                if r:
                    reg_map[r] = new_bus
                trip_map[tk] = new_bus
                bussathi_added += 1

    print(f"bussathi: Added {bussathi_added} new buses | Enriched {bussathi_contacts_enriched} contacts | Enriched {bussathi_regs_enriched} regs")

    # 2. Process wbbus cards (1410 buses)
    wbbus_added = 0
    wbbus_regs_enriched = 0

    if WBBUS_FILE.exists():
        with open(WBBUS_FILE, "r", encoding="utf-8") as f:
            wbbus = json.load(f)

        for b in wbbus:
            r = (b.get("reg_no") or "").strip().upper()
            tk = (norm(b.get("origin")), norm(b.get("destination")), norm(b.get("departure_time")))
            matched = reg_map.get(r) or trip_map.get(tk)

            if matched:
                if not matched.get("reg_no") and r:
                    matched["reg_no"] = r
                    wbbus_regs_enriched += 1
            else:
                bid = f"wbbus-in-{slug(b['bus_name'])}-{slug(b['origin'])}-{slug(b['destination'])}-{len(buses)+1}"
                while bid in existing_ids:
                    bid += "-x"
                existing_ids.add(bid)

                stops = [
                    {"no": 1, "name": b["origin"], "up_time": b.get("departure_time", ""), "down_time": ""},
                    {"no": 2, "name": b["destination"], "up_time": b.get("arrival_time", ""), "down_time": ""}
                ]

                new_bus = {
                    "id": bid,
                    "bus_name": b["bus_name"],
                    "reg_no": r,
                    "operator": b.get("operator") or "—",
                    "bus_type": b.get("bus_type") or "Private - NON AC",
                    "origin": b["origin"],
                    "destination": b["destination"],
                    "departure_time": b.get("departure_time", ""),
                    "arrival_time": b.get("arrival_time", ""),
                    "contact_number": "Not Available !",
                    "depot_name": b["origin"],
                    "route": b.get("route") or f"{b['origin']} - {b['destination']}",
                    "stoppages": stops,
                    "source": "wbbus.in",
                    "total_stoppages": len(stops),
                    "detail_url": b.get("detail_url", "")
                }
                buses.append(new_bus)
                if r:
                    reg_map[r] = new_bus
                trip_map[tk] = new_bus
                wbbus_added += 1

    print(f"wbbus: Added {wbbus_added} new buses | Enriched {wbbus_regs_enriched} regs")
    after_count = len(buses)
    print(f"Final buses in database: {after_count} (Net new added: {after_count - before_count})")

    data.setdefault("meta", {})["total_buses"] = after_count
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Successfully updated data/busjatri_data.json!")


if __name__ == "__main__":
    main()
