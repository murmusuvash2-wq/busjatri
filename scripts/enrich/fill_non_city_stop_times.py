#!/usr/bin/env python3
"""Fill missing intermediate stoppage times for non-city buses in BusJatri.

Non-city buses (intercity, long-distance, district lines) have known Origin Departure
and Destination Arrival times. This script fills the unpopulated intermediate stoppage
times using segmented distance-weighted interpolation between known time anchors.

Features:
- Segmented interpolation between consecutive known time anchors.
- Haversine distance weighting when stop coordinates are available.
- Clean 5-minute schedule rounding (e.g., 6:30 AM, 6:35 AM) matching real transit standards.
- Strictly monotonic constraint to avoid sequence time inversions.
- Tags filled stops with `is_est_up: true` / `is_est_down: true` for transparency.
- Safe execution: requires `--write` to apply changes.

Usage:
  python3 scripts/enrich/fill_non_city_stop_times.py          # Dry run report
  python3 scripts/enrich/fill_non_city_stop_times.py --write  # Apply and rebuild indexes
"""

import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "busjatri_data.json"
COORDS_PATH = ROOT / "data" / "stop_coords.json"

CITY_SOURCES = {
    "kolkata-travel-router (GitHub)",
    "WBTC (govt)",
    "kolbusopedia.com",
    "transport.wb.gov.in / CSTC official",
    "WBTC official route list"
}

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})\s*(AM|PM)?$", re.I)

def parse_mins(t):
    if not t or str(t).strip() in {"", "_", "—", "--", "N/A"}:
        return None
    m = TIME_RE.match(str(t).strip())
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").upper()
    if ap == "PM" and h != 12:
        h += 12
    elif ap == "AM" and h == 12:
        h = 0
    return (h % 24) * 60 + mi

def fmt_time(m):
    m = int(round(m)) % 1440
    h, mi = divmod(m, 60)
    ap = "AM" if h < 12 else "PM"
    h = h % 12 or 12
    return f"{h}:{mi:02d} {ap}"

def round_5min(m):
    return int(round(m / 5.0) * 5)

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def main():
    write = "--write" in sys.argv

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    coords = {}
    if COORDS_PATH.exists():
        try:
            with open(COORDS_PATH, encoding="utf-8") as f:
                coords = json.load(f)
        except Exception:
            pass

    def get_coord(name):
        if not name:
            return None
        k = str(name).strip().lower()
        if k in coords:
            c = coords[k]
            if isinstance(c, dict) and "lat" in c and "lon" in c:
                return (float(c["lat"]), float(c["lon"]))
        return None

    buses = data["buses"] if isinstance(data["buses"], list) else list(data["buses"].values())
    non_city = [b for b in buses if b.get("source") not in CITY_SOURCES]

    print(f"Total buses in dataset: {len(buses)}")
    print(f"Non-city buses targeted: {len(non_city)}")

    filled_up = 0
    filled_down = 0
    buses_updated = 0
    sample_buses = []

    for b in non_city:
        stops = b.get("stoppages") or []
        if len(stops) < 2:
            continue

        dep_min = parse_mins(b.get("departure_time"))
        arr_min = parse_mins(b.get("arrival_time"))
        if dep_min is None or arr_min is None:
            continue

        bus_changed = False

        # 1. Ensure Origin and Destination have anchor times
        if not parse_mins(stops[0].get("up_time")):
            stops[0]["up_time"] = b.get("departure_time")
            bus_changed = True
            filled_up += 1

        if not parse_mins(stops[-1].get("up_time")):
            stops[-1]["up_time"] = b.get("arrival_time")
            bus_changed = True
            filled_up += 1

        # 2. Segmented interpolation for UP direction
        anchor_indices = [i for i, s in enumerate(stops) if parse_mins(s.get("up_time")) is not None]

        for a_idx in range(len(anchor_indices) - 1):
            i = anchor_indices[a_idx]
            j = anchor_indices[a_idx + 1]
            if j - i <= 1:
                continue

            t_i = parse_mins(stops[i]["up_time"])
            t_j = parse_mins(stops[j]["up_time"])
            dur = t_j - t_i
            if dur <= 0:
                dur += 1440

            dists = []
            all_have_coords = True
            for idx in range(i, j):
                c1 = get_coord(stops[idx].get("name"))
                c2 = get_coord(stops[idx + 1].get("name"))
                if c1 and c2:
                    dists.append(max(1.0, haversine_km(c1[0], c1[1], c2[0], c2[1])))
                else:
                    all_have_coords = False
                    break

            prev_t = t_i
            for step, k in enumerate(range(i + 1, j)):
                if not stops[k].get("up_time"):
                    if all_have_coords and sum(dists) > 0:
                        cum_dist = sum(dists[:step + 1])
                        frac = cum_dist / sum(dists)
                    else:
                        frac = (k - i) / (j - i)
                    t_k = t_i + frac * dur
                    t_k_round = round_5min(t_k)
                    # Preserve strict monotonicity
                    if t_k_round <= prev_t:
                        t_k_round = prev_t + 5
                    if t_k_round >= t_j and dur > 5 * (j - i):
                        t_k_round = t_j - 5 * (j - k)
                    prev_t = t_k_round
                    stops[k]["up_time"] = fmt_time(t_k_round)
                    stops[k]["is_est_up"] = True
                    filled_up += 1
                    bus_changed = True

        # 3. Segmented interpolation for DOWN direction (if down anchors exist)
        down_anchor_indices = [i for i, s in enumerate(stops) if parse_mins(s.get("down_time")) is not None]
        if len(down_anchor_indices) >= 2:
            for a_idx in range(len(down_anchor_indices) - 1):
                i = down_anchor_indices[a_idx]
                j = down_anchor_indices[a_idx + 1]
                if j - i <= 1:
                    continue

                t_i = parse_mins(stops[i]["down_time"])
                t_j = parse_mins(stops[j]["down_time"])
                dur = t_j - t_i
                if dur <= 0:
                    dur += 1440

                prev_t = t_i
                for k in range(i + 1, j):
                    if not stops[k].get("down_time"):
                        frac = (k - i) / (j - i)
                        t_k = t_i + frac * dur
                        t_k_round = round_5min(t_k)
                        if t_k_round <= prev_t:
                            t_k_round = prev_t + 5
                        if t_k_round >= t_j and dur > 5 * (j - i):
                            t_k_round = t_j - 5 * (j - k)
                        prev_t = t_k_round
                        stops[k]["down_time"] = fmt_time(t_k_round)
                        stops[k]["is_est_down"] = True
                        filled_down += 1
                        bus_changed = True

        if bus_changed:
            buses_updated += 1
            if len(sample_buses) < 4:
                sample_buses.append(b)

    print(f"\n--- ENRICHMENT SUMMARY ---")
    print(f"Buses updated with filled stoppage times: {buses_updated} / {len(non_city)}")
    print(f"Total UP stoppage times filled: {filled_up}")
    print(f"Total DOWN stoppage times filled: {filled_down}")
    print(f"Grand total stoppage times filled: {filled_up + filled_down}")

    print("\n--- SAMPLE ENRICHED BUSES ---")
    for b in sample_buses:
        print(f"\nBus: {b.get('bus_name')} ({b.get('operator', 'Private')}) | {b.get('origin')} -> {b.get('destination')}")
        print(f"Journey: {b.get('departure_time')} -> {b.get('arrival_time')}")
        for s in b.get("stoppages", [])[:7]:
            est_flag = " [Est]" if s.get("is_est_up") else " [Orig]"
            print(f"   - {s.get('name')}: UP={s.get('up_time')}{est_flag} | DOWN={s.get('down_time', '')}")

    if write:
        print(f"\nWriting changes to {DATA_PATH}...")
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("Successfully saved data/busjatri_data.json!")

        # Rebuild client index and bus-details
        import subprocess
        print("Rebuilding client indexes (app-index.json, bus-details)...")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_client_data.py")], check=True)
        print("Rebuilding client data completed successfully.")
    else:
        print("\n[Dry run complete] Pass --write to apply changes.")

if __name__ == "__main__":
    main()
