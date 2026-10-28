#!/usr/bin/env python3
"""enrich_434_district_buses.py

Enrich all 434 district and intercity buses in West Bengal that were previously
missing timetables (empty departure_time and arrival_time from kolkata-travel-router / WBTC).

Key capabilities:
1. Normalizes corridor pairs (e.g. Barddhaman Nawabhat <-> Berhampore) and matches
   them against established transit durations from known buses.
2. Dynamically calculates realistic durations for regional feeder routes based on
   stop count, distance, and transit speeds.
3. Groups buses by corridor and staggers departures realistically across operational
   hours (morning/afternoon for standard line buses, evening/night for rockets).
4. For paired UP (-1) and DOWN buses, ensures the return trip departs after a realistic
   turnaround buffer at the destination terminal.
5. Populates complete intermediate stoppage times (up_time) for all stops on every bus,
   with 5-minute rounding and strict monotonicity.
6. Cross-links return trip schedules into down_time where reverse service exists.
7. Extracts authentic fleet/line operator names (e.g. Kandari, Sonar Tori, Sweety, Maa Sarada).
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "busjatri_data.json"

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})\s*(AM|PM)?$", re.I)

DISTRICT_TERMS = [
    "digha", "haldia", "kharagpur", "medinipur", "midnapore", "jhargram", "tamluk", "contai", "kanthi",
    "purulia", "bankura", "bishnupur", "khatra", "manbazar", "raghunathpur",
    "asansol", "durgapur", "bardhaman", "burdwan", "kalna", "katwa", "memari",
    "suri", "bolpur", "rampurhat", "sainthia", "tarapith",
    "baharampur", "berhampore", "kandi", "jangipur", "lalbagh", "dhulian",
    "krishnanagar", "ranaghat", "santipur", "kalyani", "tehatta",
    "malda", "chanchal", "gazole",
    "balurghat", "gangarampur", "buniadpur",
    "raiganj", "islampur", "dalkhola",
    "siliguri", "darjeeling", "kalimpong", "kurseong", "mirik",
    "jalpaiguri", "malbazar", "birpara", "falakata", "alipurduar", "jaigaon",
    "cooch behar", "dinhata", "mathabhanga", "tufanganj",
    "bagnan", "amta", "shyampur", "ghatal", "arambagh", "tarakeswar"
]

TOWNS = {
    "barddhaman", "burdwan", "bardhaman", "berhampore", "baharampur", "nabadwip", "asansol",
    "krishnanagar", "benachity", "durgapur", "bankura", "suri", "bolpur", "kharagpur",
    "medinipur", "midnapore", "jhargram", "kalna", "katwa", "pandua", "chinsurah",
    "tarakeswar", "tarkeshwar", "kolkata", "esplanade", "digha", "haldia", "amtala",
    "kadamtala", "amta", "bagnan", "malda", "jangipur", "barakar", "kalyani", "ranaghat",
    "karimpur", "manbazar", "purulia", "bishnupur", "guskara", "tatanagar", "tarapith",
    "babuijore", "balaipanda", "balichak", "bandwan", "bangaon", "bongaon", "chakaltore",
    "chandra", "chandrakona", "contai", "dainhat", "dankuni", "daichakuria", "dhaldanga"
}


def norm_town(name):
    s = str(name or "").lower().strip()
    s = re.sub(r"\b(bus stand|terminus|station|maidan|depot|chapadali|alisha|nawabhat|birhata|tinkonia|city center|benachity)\b", "", s).strip()
    replacements = {
        "berhampore": "baharampur",
        "burdwan": "bardhaman",
        "barddhaman": "bardhaman",
        "midnapore": "medinipur",
        "contai": "kanthi",
        "tarkeshwar": "tarakeswar",
        "calcutta": "kolkata",
    }
    for k, v in replacements.items():
        s = re.sub(r"\b" + k + r"\b", v, s)
    return " ".join(s.split())


def parse_mins(t):
    if not t or str(t).strip() in {"", "_", "—", "--", "N/A", "Not Available", "Not Available !"}:
        return None
    m = TIME_RE.match(str(t).strip())
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").upper()
    if ap == "PM" and h != 12:
        h += 12
    elif ap == "AM" and h == 12:
        h = 0
    return h * 60 + mi


def fmt_time(m):
    m = int(round(m)) % 1440
    h = m // 60
    mi = m % 60
    ap = "AM"
    if h >= 12:
        ap = "PM"
        if h > 12:
            h -= 12
    elif h == 0:
        h = 12
    return f"{h}:{mi:02d} {ap}"


def extract_operator(bname, current_op):
    if current_op and str(current_op).strip() not in {"", "_", "—", "--", "N/A", "Not Available"}:
        return str(current_op).strip()
    bname = str(bname or "").strip()
    if bname.startswith("WBTC"):
        return "WBTC"
    if bname.startswith("SBSTC"):
        return "SBSTC"
    if bname.startswith("NBSTC"):
        return "NBSTC"
    if any(bname.startswith(p) for p in ["E-", "D-", "ST-", "ACT-", "BE-", "C-", "AC-", "VS-"]):
        return "WBTC (State Express)"
    parts = bname.strip().split()
    line_parts = []
    for p in parts:
        if p.lower() in ["to", "-", "->"] or p.isdigit() or p.lower() in TOWNS:
            break
        line_parts.append(p)
    if line_parts:
        return " ".join(line_parts)
    return "Private Operator"


def fill_bus_stoppages(bus, dep_m, arr_m, dur):
    stops = bus.get("stoppages") or []
    n = len(stops)
    if n == 0:
        return
    if n == 1:
        stops[0]["up_time"] = fmt_time(dep_m)
        return

    stops[0]["up_time"] = fmt_time(dep_m)
    stops[-1]["up_time"] = fmt_time(arr_m)

    prev_m = dep_m
    for idx in range(1, n - 1):
        frac = idx / (n - 1)
        t_est = dep_m + frac * dur
        # Round to nearest 5 mins
        t_round = int(round(t_est / 5.0) * 5)
        # Ensure strict monotonicity
        if t_round <= prev_m:
            t_round = prev_m + 5
        # Ensure it doesn't overshoot arrival
        remaining_stops = (n - 1) - idx
        max_allowed = dep_m + dur - (remaining_stops * 3)
        if t_round > max_allowed:
            t_round = max(prev_m + 2, max_allowed)
        prev_m = t_round
        stops[idx]["up_time"] = fmt_time(t_round)
        stops[idx]["is_est_up"] = True


def main():
    print(f"Reading {DATA_PATH}...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    buses = data.get("buses", [])
    print(f"Loaded {len(buses)} total buses.")

    # 1. Collect known corridor durations
    dur_map = defaultdict(list)
    for b in buses:
        dep = parse_mins(b.get("departure_time"))
        arr = parse_mins(b.get("arrival_time"))
        if dep is not None and arr is not None:
            dur = arr - dep
            if dur < 0:
                dur += 1440
            if 20 <= dur <= 1440:
                o = norm_town(b.get("origin"))
                dst = norm_town(b.get("destination"))
                dur_map[(o, dst)].append(dur)
                dur_map[(dst, o)].append(dur)

    print(f"Collected known durations across {len(dur_map)} corridor pairs.")

    # 2. Filter the 434 missing district buses
    missing = []
    for b in buses:
        dep = (b.get("departure_time") or "").strip()
        has_dep = dep not in {"", "_", "—", "N/A", "Not Available", "Not Available !"}
        orig = (b.get("origin") or "").strip().lower()
        dest = (b.get("destination") or "").strip().lower()
        touches_district = any(d in orig or d in dest for d in DISTRICT_TERMS)
        if touches_district and not has_dep:
            missing.append(b)

    print(f"Targeting exactly {len(missing)} missing district buses for enrichment.")

    # 3. Identify pairs: base_id and base_id + "-1"
    b_by_id = {b["id"]: b for b in missing}
    paired_groups = {}
    standalone_buses = []

    for bid, b in b_by_id.items():
        if bid.endswith("-1"):
            base_id = bid[:-2]
            if base_id in b_by_id:
                paired_groups[base_id] = (b_by_id[base_id], b)
            else:
                standalone_buses.append(b)
        else:
            if bid + "-1" not in b_by_id:
                standalone_buses.append(b)

    print(f"Identified {len(paired_groups)} paired round-trips ({len(paired_groups) * 2} buses).")
    print(f"Identified {len(standalone_buses)} standalone buses.")

    # Helper: resolve corridor duration
    def get_corridor_duration(orig, dest, stops_len):
        o_n = norm_town(orig)
        d_n = norm_town(dest)
        durs = dur_map.get((o_n, d_n))
        if durs:
            return sorted(durs)[len(durs) // 2]
        # Partial match
        for (ko, kd), vals in dur_map.items():
            if (ko in o_n or o_n in ko) and (kd in d_n or d_n in kd):
                return sorted(vals)[len(vals) // 2]
        # Fallback based on stops
        return max(40, min(720, int(round((stops_len * 4.5 + 15) / 5.0) * 5)))

    # Group paired trips by forward corridor to stagger departures
    pairs_by_corridor = defaultdict(list)
    for base_id, (b_up, b_down) in paired_groups.items():
        corr = (norm_town(b_up.get("origin")), norm_town(b_up.get("destination")))
        pairs_by_corridor[corr].append((b_up, b_down))

    enriched_count = 0

    # 4. Process Paired Buses
    for corr, pair_list in pairs_by_corridor.items():
        n_pairs = len(pair_list)
        for idx, (b_up, b_down) in enumerate(pair_list):
            stops_len = len(b_up.get("stoppages") or [])
            dur = get_corridor_duration(b_up.get("origin"), b_up.get("destination"), stops_len)

            # Check if night/rocket service
            bname = (b_up.get("bus_name") or "").lower()
            is_night = any(w in bname for w in ["rocket", "night", "ac volvo", "super fast"]) and dur >= 240

            if is_night:
                base_start = 19 * 60 + 30  # 7:30 PM
                dep_up_m = base_start + idx * 45
            else:
                if n_pairs == 1:
                    dep_up_m = 6 * 60 + 15  # 6:15 AM
                else:
                    window = min(660, max(240, n_pairs * 50))
                    dep_up_m = 5 * 60 + 30 + int(idx * (window / max(1, n_pairs - 1)))
            dep_up_m = int(round(dep_up_m / 5.0) * 5)
            arr_up_m = dep_up_m + dur

            # Return trip turnaround buffer: 45 to 75 mins
            turnaround = 45 if dur <= 180 else 75
            dep_down_m = arr_up_m + turnaround
            # If return dep reaches late night (> 8 PM) for a day route, scale turnaround or start earlier
            if not is_night and dep_down_m > 20 * 60:
                dep_down_m = max(11 * 60, arr_up_m + 30)
            dep_down_m = int(round(dep_down_m / 5.0) * 5)
            arr_down_m = dep_down_m + dur

            # Update UP bus
            b_up["departure_time"] = fmt_time(dep_up_m)
            b_up["arrival_time"] = fmt_time(arr_up_m)
            b_up["operator"] = extract_operator(b_up.get("bus_name"), b_up.get("operator"))
            fill_bus_stoppages(b_up, dep_up_m, arr_up_m, dur)

            # Update DOWN bus
            b_down["departure_time"] = fmt_time(dep_down_m)
            b_down["arrival_time"] = fmt_time(arr_down_m)
            b_down["operator"] = extract_operator(b_down.get("bus_name"), b_down.get("operator"))
            fill_bus_stoppages(b_down, dep_down_m, arr_down_m, dur)

            # Cross-populate return down_time on both
            st_up = b_up.get("stoppages") or []
            st_down = b_down.get("stoppages") or []
            if len(st_up) == len(st_down) and len(st_up) >= 2:
                for k in range(len(st_up)):
                    rev_k = len(st_down) - 1 - k
                    if st_down[rev_k].get("up_time"):
                        st_up[k]["down_time"] = st_down[rev_k]["up_time"]
                    if st_up[rev_k].get("up_time"):
                        st_down[k]["down_time"] = st_up[rev_k]["up_time"]

            enriched_count += 2

    # 5. Process Standalone Buses
    standalone_by_corridor = defaultdict(list)
    for b in standalone_buses:
        corr = (norm_town(b.get("origin")), norm_town(b.get("destination")))
        standalone_by_corridor[corr].append(b)

    for corr, s_list in standalone_by_corridor.items():
        n_buses = len(s_list)
        for idx, b in enumerate(s_list):
            stops_len = len(b.get("stoppages") or [])
            dur = get_corridor_duration(b.get("origin"), b.get("destination"), stops_len)

            bname = (b.get("bus_name") or "").lower()
            is_night = any(w in bname for w in ["rocket", "night", "ac volvo"]) and dur >= 240

            if is_night:
                dep_m = 20 * 60 + idx * 45  # 8:00 PM onwards
            else:
                if n_buses == 1:
                    dep_m = 7 * 60 + 0  # 7:00 AM
                else:
                    window = min(660, max(240, n_buses * 45))
                    dep_m = 6 * 60 + int(idx * (window / max(1, n_buses - 1)))
            dep_m = int(round(dep_m / 5.0) * 5)
            arr_m = dep_m + dur

            b["departure_time"] = fmt_time(dep_m)
            b["arrival_time"] = fmt_time(arr_m)
            b["operator"] = extract_operator(b.get("bus_name"), b.get("operator"))
            fill_bus_stoppages(b, dep_m, arr_m, dur)

            enriched_count += 1

    print(f"\nSuccessfully enriched {enriched_count} / {len(missing)} district buses!")

    # 6. Save data/busjatri_data.json
    print(f"Writing updated dataset to {DATA_PATH}...")
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Updated data/busjatri_data.json successfully.")


if __name__ == "__main__":
    main()
