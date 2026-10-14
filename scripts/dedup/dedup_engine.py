#!/usr/bin/env python3
"""BusJatri Duplicate Detection & Merge Engine.

Handles:
1. Endpoint Normalization (Mapping multi-stand towns & Bengali/English variants to canonical nodes)
2. Fuzzy Operator Matching (e.g. 'BURA BABA' vs 'Bura Baba Travels')
3. Departure Time Proximity Matching (within +/- 10 minutes)
4. Stoppage Overlap Verification (Jaccard similarity of stoppage names)
5. Non-destructive Merging: Combines richer stoppages, registration numbers, contact details and preserves original sources.
"""

import re
from datetime import datetime
from collections import defaultdict


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


# Canonical cluster mappings for West Bengal transport hubs
CANONICAL_HUBS = {
    # Kolkata multi-terminal cluster
    "kolkata": "kolkata",
    "calcutta": "kolkata",
    "esplanade": "kolkata",
    "dharmatala": "kolkata",
    "dharmatola": "kolkata",
    "babughat": "kolkata",
    "karunamoyee": "kolkata",
    "saltlake": "kolkata",
    "salt-lake": "kolkata",
    "howrah": "howrah",
    "howrah-stn": "howrah",
    "howrah-station": "howrah",
    "santragachi": "santragachi",
    # Durgapur terminals
    "durgapur": "durgapur",
    "durgapur-station": "durgapur",
    "durgapur-stn": "durgapur",
    "durgapur-city-center": "durgapur",
    "durgapur-city-centre": "durgapur",
    "durgapur-bus-stand": "durgapur",
    "benachity": "durgapur",
    # Bankura terminals
    "bankura": "bankura",
    "bankura-gobindanagar": "bankura",
    "bankura-bus-stand": "bankura",
    "bankura-station": "bankura",
    "bankura-bypass": "bankura",
    # Bardhaman
    "bardhaman": "bardhaman",
    "burdwan": "bardhaman",
    "bardhaman-nawabhat": "bardhaman",
    "nawabhat": "bardhaman",
    "alisha": "bardhaman",
    "ullhas": "bardhaman",
    # Medinipur & Kharagpur
    "medinipur": "medinipur",
    "midnapore": "medinipur",
    "keranitola": "medinipur",
    "kharagpur": "kharagpur",
    "kharagpur-station": "kharagpur",
    "kharagpur-chowringhee": "kharagpur",
    # Purba Medinipur
    "contai": "kanthi",
    "kanthi": "kanthi",
    "digha": "digha",
    "new-digha": "digha",
    "old-digha": "digha",
    "digha-border": "digha",
    # Murshidabad
    "berhampore": "baharampur",
    "baharampur": "baharampur",
    "berhampur": "baharampur",
    "mohona": "baharampur",
    # North Bengal
    "siliguri": "siliguri",
    "tenzing-norgay": "siliguri",
    "pc-mittal": "siliguri",
    "cooch-behar": "cooch-behar",
    "koch-bihar": "cooch-behar",
    "malda": "malda",
    "english-bazar": "malda",
}


def canon_place(name):
    """Returns canonical regional hub key for deduplication."""
    s = slug(name)
    if s in CANONICAL_HUBS:
        return CANONICAL_HUBS[s]
    # Strip terminal suffixes
    cleaned = re.sub(
        r"-(station|stn|bus-stand|bustand|terminus|more|depot|chowrasta|bridge)$",
        "",
        s,
    )
    if cleaned in CANONICAL_HUBS:
        return CANONICAL_HUBS[cleaned]
    return cleaned


def parse_time_min(t_str):
    """Converts '6:45 AM' or '18:45' to minutes from midnight (0-1439)."""
    if not t_str:
        return None
    s = str(t_str).strip().upper()
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM|NOON)?", s)
    if not m:
        return None
    h = int(m.group(1))
    mi = int(m.group(2))
    ap = m.group(3)
    if ap == "PM" and h < 12:
        h += 12
    elif ap == "AM" and h == 12:
        h = 0
    elif ap == "NOON":
        h = 12
    return h * 60 + mi


def time_diff_minutes(t1_min, t2_min):
    """Calculates circular time difference in minutes (e.g. 23:55 to 00:05 = 10 min)."""
    if t1_min is None or t2_min is None:
        return None
    diff = abs(t1_min - t2_min)
    return min(diff, 1440 - diff)


def clean_op_name(op):
    """Normalizes operator name (strips Ltd, Travels, Line, Bus, etc)."""
    s = slug(op)
    s = re.sub(r"-(travels|paribahan|transport|bus|service|services|line|express|co|pvt|ltd)$", "", s)
    return s


def stoppage_set(bus):
    """Returns set of slugged stop names for a bus."""
    stops = bus.get("stoppages") or []
    out = set()
    for s in stops:
        nm = s.get("name") if isinstance(s, dict) else str(s)
        if nm:
            out.add(canon_place(nm))
    return out


def is_duplicate(bus_a, bus_b, max_time_diff=15):
    """Determines whether two bus records represent the exact same service."""
    # 1. Endpoint match
    oa, da = canon_place(bus_a.get("origin")), canon_place(bus_a.get("destination"))
    ob, db = canon_place(bus_b.get("origin")), canon_place(bus_b.get("destination"))

    if oa != ob or da != db:
        return False

    # 2. Operator check
    op_a = clean_op_name(bus_a.get("operator") or bus_a.get("bus_name") or "")
    op_b = clean_op_name(bus_b.get("operator") or bus_b.get("bus_name") or "")

    # Operator matches or one is generic
    op_match = (op_a and op_b and (op_a == op_b or op_a in op_b or op_b in op_a)) or (not op_a or not op_b)

    # 3. Departure time check
    ta = parse_time_min(bus_a.get("departure_time"))
    tb = parse_time_min(bus_b.get("departure_time"))

    # Both have departure times
    if ta is not None and tb is not None:
        tdiff = time_diff_minutes(ta, tb)
        if tdiff is not None and tdiff <= max_time_diff:
            # If operators match or both are govt/same operator
            if op_match:
                return True
            # Even if operators differ, check if stoppage overlap is >= 70%
            sa, sb = stoppage_set(bus_a), stoppage_set(bus_b)
            if sa and sb and (len(sa & sb) / max(len(sa), len(sb))) >= 0.7:
                return True
        return False

    # If one or both lack departure times, check stoppage sequence overlap
    sa, sb = stoppage_set(bus_a), stoppage_set(bus_b)
    if sa and sb:
        inter = len(sa & sb)
        union = len(sa | sb)
        if union > 0 and (inter / union) >= 0.75 and op_match:
            return True

    return False


def merge_bus_records(primary, secondary):
    """Combines secondary bus record into primary, prioritizing richer data."""
    merged = dict(primary)

    # 1. Prefer richer stoppages
    primary_stops = primary.get("stoppages") or []
    secondary_stops = secondary.get("stoppages") or []

    # Count stops with timings
    def timed_count(sts):
        return sum(1 for s in sts if isinstance(s, dict) and (s.get("up_time") or s.get("down_time")))

    if timed_count(secondary_stops) > timed_count(primary_stops) or len(secondary_stops) > len(primary_stops):
        merged["stoppages"] = secondary_stops
        merged["total_stoppages"] = len(secondary_stops)

    # 2. Prefer valid departure/arrival times
    if not merged.get("departure_time") and secondary.get("departure_time"):
        merged["departure_time"] = secondary["departure_time"]
    if not merged.get("arrival_time") and secondary.get("arrival_time"):
        merged["arrival_time"] = secondary["arrival_time"]

    # 3. Fill registration & contact
    if not merged.get("reg_no") and secondary.get("reg_no"):
        merged["reg_no"] = secondary["reg_no"]
    if (merged.get("contact_number") in ("", "Not Available !", None)) and secondary.get("contact_number"):
        merged["contact_number"] = secondary["contact_number"]

    # 4. Fill bus type / AC status
    if not merged.get("bus_type") and secondary.get("bus_type"):
        merged["bus_type"] = secondary["bus_type"]

    # 5. Track merged sources
    src1 = primary.get("source", "")
    src2 = secondary.get("source", "")
    if src2 and src2 not in src1:
        merged["merged_sources"] = f"{src1} + {src2}" if src1 else src2

    return merged


def deduplicate_dataset(bus_list):
    """Takes a list of buses, clusters duplicates and returns merged unique list."""
    unique_buses = []
    merged_count = 0

    # Group by (canon_origin, canon_dest) for fast comparison
    buckets = defaultdict(list)
    for b in bus_list:
        co = canon_place(b.get("origin"))
        cd = canon_place(b.get("destination"))
        buckets[(co, cd)].append(b)

    for (co, cd), bucket in buckets.items():
        processed = [False] * len(bucket)
        for i in range(len(bucket)):
            if processed[i]:
                continue
            curr = bucket[i]
            processed[i] = True
            for j in range(i + 1, len(bucket)):
                if not processed[j] and is_duplicate(curr, bucket[j]):
                    curr = merge_bus_records(curr, bucket[j])
                    processed[j] = True
                    merged_count += 1
            unique_buses.append(curr)

    return unique_buses, merged_count


if __name__ == "__main__":
    b1 = {
        "id": "b1",
        "origin": "Durgapur Station",
        "destination": "Bankura",
        "departure_time": "7:00 AM",
        "operator": "Bura Baba",
        "stoppages": [{"name": "Barjora"}, {"name": "Beliatore"}],
        "source": "bussathi.in"
    }
    b2 = {
        "id": "b2",
        "origin": "Durgapur Stn",
        "destination": "Bankura Gobindanagar",
        "departure_time": "7:05 AM",
        "operator": "BURA BABA TRAVELS",
        "stoppages": [
            {"name": "Barjora", "up_time": "7:20 AM"},
            {"name": "Beliatore", "up_time": "7:45 AM"},
            {"name": "Bikna", "up_time": "8:00 AM"}
        ],
        "source": "wbbustime.in"
    }

    print("Checking duplicate test:")
    dup = is_duplicate(b1, b2)
    print(f"  Is duplicate: {dup}")
    if dup:
        merged = merge_bus_records(b1, b2)
        print(f"  Merged bus stops count: {len(merged['stoppages'])}")
        print(f"  Merged sources: {merged.get('merged_sources')}")
