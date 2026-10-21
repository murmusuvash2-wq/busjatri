#!/usr/bin/env python3
"""merge_wbbus_and_wbbustime.py - Ingest and merge scraped buses from wbbus.in
and wbbustime.com into data/busjatri_data.json with strict deduplication and schema adherence.

Usage:
  python3 scripts/enrich/merge_wbbus_and_wbbustime.py [--write]
"""

import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "busjatri_data.json"
WBBUS_RAW = ROOT / "data-raw" / "wbbus_in_scraped.json"
WBBUSTIME_RAW = ROOT / "data-raw" / "wbbustime_com_scraped.json"
COORDS_PATH = ROOT / "data" / "stop_coords.json"

TIME_RE = re.compile(r"^(\d{1,2})[:.](\d{2})\s*(AM|PM|Noon|Midnight)?$", re.I)
BAD_TIMES = {"", "_", "_ _", "_ _ : _ _", "—", "--", "N/A", "00.00am", "00.00pm", "0:00", "00:00", "null", "None"}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-") or "x"


def clean(s):
    return re.sub(r"\s+", " ", str(s or "").strip())


def parse_mins(t):
    t = clean(t).lstrip("~").strip()
    if not t or t in BAD_TIMES:
        return None
    m = TIME_RE.match(t)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").upper()
    if ap == "PM" and h != 12:
        h += 12
    elif ap == "AM" and h == 12:
        h = 0
    elif ap == "NOON":
        h = 12
    elif ap == "MIDNIGHT":
        h = 0
    return (h % 24) * 60 + mi


def fmt_time(m):
    m = m % 1440
    h, mi = divmod(m, 60)
    ap = "AM" if h < 12 else "PM"
    h = h % 12 or 12
    return f"{h}:{mi:02d} {ap}"


def norm_name(n):
    n = re.sub(r"\s+", " ", (n or "").strip().lower())
    n = re.sub(r"\s+(bus stand|bus-stand|terminus|depot|stand|station|stn)$", "", n)
    return n


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def main():
    write = "--write" in sys.argv

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    raw_candidates = []
    if WBBUS_RAW.exists():
        with open(WBBUS_RAW, encoding="utf-8") as f:
            raw_candidates.extend(json.load(f))
    if WBBUSTIME_RAW.exists():
        with open(WBBUSTIME_RAW, encoding="utf-8") as f:
            raw_candidates.extend(json.load(f))

    print(f"Total raw candidates loaded: {len(raw_candidates)}")

    stop_coords = {}
    if COORDS_PATH.exists():
        with open(COORDS_PATH, encoding="utf-8") as f:
            stop_coords = json.load(f)

    coord_map = {}
    for k, v in stop_coords.items():
        if isinstance(v, dict) and v.get("lat") and v.get("lon"):
            coord_map[norm_name(k)] = (float(v["lat"]), float(v["lon"]))

    # Index existing data
    existing_ids = {b.get("id") for b in data["buses"]}
    existing_trips = {
        (norm_name(b.get("origin")), norm_name(b.get("destination")), clean(b.get("departure_time")).lower())
        for b in data["buses"]
    }
    existing_reg_trips = {
        (clean(b.get("reg_no")).replace(" ", "").upper(), norm_name(b.get("origin")), clean(b.get("departure_time")).lower())
        for b in data["buses"]
        if clean(b.get("reg_no"))
    }

    # Build known corridor durations from existing data
    corridors = defaultdict(list)
    for b in data["buses"]:
        d = parse_mins(b.get("departure_time"))
        a = parse_mins(b.get("arrival_time"))
        if d is not None and a is not None:
            dur = a - d
            if dur < 0:
                dur += 1440
            if 15 <= dur <= 900:
                k = (norm_name(b.get("origin")), norm_name(b.get("destination")))
                corridors[k].append(dur)

    added = []
    skipped_dupe = 0
    skipped_invalid = 0

    for raw in raw_candidates:
        orig = clean(raw.get("origin"))
        dest = clean(raw.get("destination"))
        bname = clean(raw.get("bus_name")) or "Private Bus"
        dep = clean(raw.get("departure_time"))
        arr = clean(raw.get("arrival_time"))
        reg = clean(raw.get("reg_no")).replace(" ", "").upper()
        url = clean(raw.get("detail_url"))
        source = raw.get("source") or "wbbus.in"

        if not orig or not dest or orig == dest or orig in ("—", "_ _") or dest in ("—", "_ _"):
            skipped_invalid += 1
            continue
        if not dep or dep in BAD_TIMES:
            skipped_invalid += 1
            continue

        # Format departure time consistently
        d_p = parse_mins(dep)
        if d_p is not None:
            dep = fmt_time(d_p)
        else:
            skipped_invalid += 1
            continue

        bid = raw.get("id")
        if not bid or bid in existing_ids:
            # Generate deterministic fallback ID
            prefix = "wbbus" if "wbbus.in" in source else "wbbustime"
            bid = f"{prefix}-{slug(bname)}-{slug(orig)}-{slug(dest)}"
            base_id = bid
            ctr = 1
            while bid in existing_ids:
                bid = f"{base_id}-{ctr}"
                ctr += 1

        trip_key = (norm_name(orig), norm_name(dest), dep.lower())
        if trip_key in existing_trips:
            skipped_dupe += 1
            continue

        if reg and (reg, norm_name(orig), dep.lower()) in existing_reg_trips:
            skipped_dupe += 1
            continue

        # Clean stoppages
        stoppages = raw.get("stoppages") or []
        clean_stops = []
        for s in stoppages:
            if isinstance(s, dict):
                clean_stops.append({
                    "no": s.get("no") or len(clean_stops) + 1,
                    "name": clean(s.get("name")),
                    "up_time": clean(s.get("up_time")),
                    "down_time": clean(s.get("down_time")),
                })

        # Calculate arrival time if missing or equal to departure
        is_estimated = False
        a_p = parse_mins(arr) if arr and arr not in BAD_TIMES else None
        if a_p is None or a_p == d_p:
            dur = None
            durs = corridors.get((norm_name(orig), norm_name(dest))) or corridors.get((norm_name(dest), norm_name(orig)))
            if durs:
                dur = sorted(durs)[len(durs) // 2]
            if dur is None:
                c1 = coord_map.get(norm_name(orig))
                c2 = coord_map.get(norm_name(dest))
                if c1 and c2:
                    dist = haversine_km(c1[0], c1[1], c2[0], c2[1]) * 1.35
                    speed = 46.0 if dist > 140 else 36.0
                    dur = int((dist / speed) * 60)
            if dur is None:
                stops_cnt = len(clean_stops)
                dur = min(480, max(45, stops_cnt * 16)) if stops_cnt > 2 else 120

            dur = int(round(dur / 5.0) * 5)
            arr = fmt_time((d_p + dur) % 1440)
            is_estimated = True
        else:
            arr = fmt_time(a_p)

        op = clean(raw.get("operator")) or "Private"
        bt = clean(raw.get("bus_type")) or "Private - NON AC"
        for corp in ("SBSTC", "NBSTC", "WBTC", "CSTC"):
            if corp in bname.upper():
                op = corp
                bt = f"Government - {corp}"
                break

        bus_entry = {
            "id": bid,
            "bus_name": bname,
            "reg_no": reg,
            "operator": op,
            "bus_type": bt,
            "origin": orig,
            "destination": dest,
            "departure_time": dep,
            "arrival_time": arr,
            "contact_number": clean(raw.get("contact_number")) or "Not Available !",
            "depot_name": clean(raw.get("depot_name")) or "",
            "route": f"{orig} - {dest}",
            "stoppages": clean_stops,
            "source": source,
            "total_stoppages": len(clean_stops) or int(raw.get("total_stoppages") or 0),
            "detail_url": url,
        }
        if is_estimated:
            bus_entry["is_estimated_arrival"] = True

        existing_ids.add(bid)
        existing_trips.add(trip_key)
        if reg:
            existing_reg_trips.add((reg, norm_name(orig), dep.lower()))

        added.append(bus_entry)

    print(f"Skipped duplicates: {skipped_dupe}")
    print(f"Skipped invalid: {skipped_invalid}")
    print(f"New unique valid buses to append: {len(added)}")

    if not added:
        print("No new buses to add.")
        return

    before_count = len(data["buses"])
    data["buses"].extend(added)
    after_count = len(data["buses"])

    # Rebuild routes map and stops map
    routes_map = defaultdict(list)
    stops_map = defaultdict(list)
    for b in data["buses"]:
        o = clean(b.get("origin"))
        d = clean(b.get("destination"))
        if o and d and o != "—" and d != "—":
            routes_map[f"{slug(o)}-to-{slug(d)}"].append(b["id"])
        seen_stops = set()
        for s in (b.get("stoppages") or []):
            sn = s.get("name") if isinstance(s, dict) else str(s)
            sn = clean(sn)
            if sn and sn not in seen_stops:
                seen_stops.add(sn)
                stops_map[sn].append(b["id"])

    routes_out = {}
    for b in data["buses"]:
        o = clean(b.get("origin"))
        d = clean(b.get("destination"))
        k = f"{slug(o)}-to-{slug(d)}"
        if k in routes_map and k not in routes_out:
            routes_out[k] = {"from": o, "to": d, "bus_ids": list(dict.fromkeys(routes_map[k]))}

    stops_out = {sn: {"name": sn, "bus_ids": list(dict.fromkeys(ids))} for sn, ids in stops_map.items()}

    data["routes"] = routes_out
    data["stops"] = stops_out
    data["meta"].update({
        "total_buses": after_count,
        "total_routes": len(routes_out),
        "total_stops": len(stops_out),
        "last_updated": str(date.today()),
    })

    print(f"\nFinal dataset update:")
    print(f"  Total buses: {before_count} -> {after_count} (+{len(added)})")
    print(f"  Total routes: {len(routes_out)}")
    print(f"  Total stops: {len(stops_out)}")

    if write:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("WROTE", DATA_PATH)


if __name__ == "__main__":
    main()
