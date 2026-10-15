#!/usr/bin/env python3
"""Export BusJatri data into General Transit Feed Specification (GTFS) standard format.

Generates standard GTFS feed files:
- agency.txt
- routes.txt
- stops.txt
- trips.txt
- stop_times.txt
- calendar.txt
- feed_info.txt

Outputs to data/gtfs/ and packages into data/gtfs/busjatri_gtfs.zip.
"""

import csv
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data" / "busjatri_data.json"
STOP_COORDS_FILE = ROOT / "data" / "stop_coords.json"
GTFS_DIR = ROOT / "data" / "gtfs"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


def parse_to_gtfs_time(time_str):
    """Parses '4:45 AM' or '12:00 PM' to '04:45:00' or '12:00:00'."""
    if not time_str or time_str in ("—", "-", "Time N/A", "Not Available"):
        return None
    time_str = time_str.strip()
    try:
        dt = datetime.strptime(time_str, "%I:%M %p")
        return dt.strftime("%H:%M:00")
    except ValueError:
        pass
    try:
        dt = datetime.strptime(time_str, "%H:%M")
        return dt.strftime("%H:%M:00")
    except ValueError:
        pass
    return None


def main():
    GTFS_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        master = json.load(f)
    buses = master.get("buses", [])

    with open(STOP_COORDS_FILE, "r", encoding="utf-8") as f:
        coords = json.load(f)

    # 1. agency.txt
    agencies = [
        {"agency_id": "SBSTC", "agency_name": "South Bengal State Transport Corporation", "agency_url": "https://online.sbstc.com", "agency_timezone": "Asia/Kolkata", "agency_lang": "bn", "agency_phone": "0343-2556442"},
        {"agency_id": "WBTC", "agency_name": "West Bengal Transport Corporation", "agency_url": "https://wbtc.co.in", "agency_timezone": "Asia/Kolkata", "agency_lang": "bn", "agency_phone": "033-22361916"},
        {"agency_id": "NBSTC", "agency_name": "North Bengal State Transport Corporation", "agency_url": "https://nbstc.in", "agency_timezone": "Asia/Kolkata", "agency_lang": "bn", "agency_phone": "03582-222479"},
        {"agency_id": "CSTC", "agency_name": "Calcutta State Transport Corporation", "agency_url": "https://wbtc.co.in", "agency_timezone": "Asia/Kolkata", "agency_lang": "bn", "agency_phone": "033-22361916"},
        {"agency_id": "PRIVATE", "agency_name": "Private Stage Carriage Operators", "agency_url": "https://busjatri.in", "agency_timezone": "Asia/Kolkata", "agency_lang": "bn", "agency_phone": "busjatri@zohomail.in"},
    ]
    with open(GTFS_DIR / "agency.txt", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang", "agency_phone"])
        writer.writeheader()
        writer.writerows(agencies)

    # 2. calendar.txt
    calendar = [{
        "service_id": "DAILY",
        "monday": "1", "tuesday": "1", "wednesday": "1", "thursday": "1", "friday": "1", "saturday": "1", "sunday": "1",
        "start_date": "20260101",
        "end_date": "20261231"
    }]
    with open(GTFS_DIR / "calendar.txt", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"])
        writer.writeheader()
        writer.writerows(calendar)

    # 3. stops.txt
    used_stops = {}
    for name, data in coords.items():
        if isinstance(data, dict) and "lat" in data and "lon" in data:
            sid = slug(name)
            used_stops[sid] = {
                "stop_id": sid,
                "stop_name": name,
                "stop_lat": data["lat"],
                "stop_lon": data["lon"],
                "zone_id": sid
            }

    with open(GTFS_DIR / "stops.txt", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["stop_id", "stop_name", "stop_lat", "stop_lon", "zone_id"])
        writer.writeheader()
        writer.writerows(used_stops.values())

    # 4. routes.txt, trips.txt, stop_times.txt
    routes_dict = {}
    trips_list = []
    stop_times_list = []

    for b in buses:
        bid = b.get("id") or f"b-{slug(b.get('bus_name'))}-{slug(b.get('origin'))}-{slug(b.get('destination'))}"
        orig = b.get("origin") or "Origin"
        dest = b.get("destination") or "Destination"
        op_raw = (b.get("operator") or b.get("bus_name") or "").upper()
        
        if "SBSTC" in op_raw:
            agency_id = "SBSTC"
        elif "NBSTC" in op_raw:
            agency_id = "NBSTC"
        elif "CSTC" in op_raw:
            agency_id = "CSTC"
        elif "WBTC" in op_raw:
            agency_id = "WBTC"
        else:
            agency_id = "PRIVATE"

        route_id = f"rt-{slug(orig)}-to-{slug(dest)}"
        if route_id not in routes_dict:
            routes_dict[route_id] = {
                "route_id": route_id,
                "agency_id": agency_id,
                "route_short_name": b.get("bus_name") or f"{orig}-{dest}",
                "route_long_name": f"{orig} to {dest}",
                "route_type": "3"  # Bus
            }

        trip_id = f"trip-{bid}"
        trips_list.append({
            "route_id": route_id,
            "service_id": "DAILY",
            "trip_id": trip_id,
            "trip_headsign": dest,
            "direction_id": "0"
        })

        # Process stop_times
        stoppages = b.get("stoppages") or []
        dep_time = parse_to_gtfs_time(b.get("departure_time")) or "06:00:00"
        arr_time = parse_to_gtfs_time(b.get("arrival_time"))

        if not stoppages:
            stoppages = [{"name": orig}, {"name": dest}]

        for seq, s in enumerate(stoppages, start=1):
            s_name = s.get("name") if isinstance(s, dict) else str(s)
            sid = slug(s_name)
            # Create dummy coordinate if stop is not yet in coords
            if sid not in used_stops:
                used_stops[sid] = {
                    "stop_id": sid,
                    "stop_name": s_name,
                    "stop_lat": 22.5726,  # Default WB centroid
                    "stop_lon": 88.3639,
                    "zone_id": sid
                }

            # Intermediate stop time calculation
            s_time = dep_time
            if isinstance(s, dict):
                t_val = s.get("up_time") or s.get("down_time")
                parsed_t = parse_to_gtfs_time(t_val)
                if parsed_t:
                    s_time = parsed_t

            stop_times_list.append({
                "trip_id": trip_id,
                "arrival_time": s_time,
                "departure_time": s_time,
                "stop_id": sid,
                "stop_sequence": str(seq)
            })

    # Write routes.txt
    with open(GTFS_DIR / "routes.txt", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"])
        writer.writeheader()
        writer.writerows(routes_dict.values())

    # Write trips.txt
    with open(GTFS_DIR / "trips.txt", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["route_id", "service_id", "trip_id", "trip_headsign", "direction_id"])
        writer.writeheader()
        writer.writerows(trips_list)

    # Write stop_times.txt
    with open(GTFS_DIR / "stop_times.txt", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"])
        writer.writeheader()
        writer.writerows(stop_times_list)

    # 5. feed_info.txt
    feed_info = [{
        "feed_publisher_name": "BusJatri Open Transit Initiative",
        "feed_publisher_url": "https://busjatri.in",
        "feed_lang": "en",
        "default_lang": "bn",
        "feed_start_date": "20260101",
        "feed_end_date": "20261231",
        "feed_version": "2026.10"
    }]
    with open(GTFS_DIR / "feed_info.txt", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["feed_publisher_name", "feed_publisher_url", "feed_lang", "default_lang", "feed_start_date", "feed_end_date", "feed_version"])
        writer.writeheader()
        writer.writerows(feed_info)

    # 6. Package into GTFS zip
    zip_path = GTFS_DIR / "busjatri_gtfs.zip"
    gtfs_files = ["agency.txt", "calendar.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt", "feed_info.txt"]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in gtfs_files:
            zf.write(GTFS_DIR / fname, arcname=fname)

    print(f"GTFS Export Complete:")
    print(f"  Agencies: {len(agencies)}")
    print(f"  Routes: {len(routes_dict)}")
    print(f"  Stops: {len(used_stops)}")
    print(f"  Trips: {len(trips_list)}")
    print(f"  Stop Times: {len(stop_times_list)}")
    print(f"  Packaged archive: {zip_path} ({zip_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
