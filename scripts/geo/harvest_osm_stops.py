#!/usr/bin/env python3
"""Harvest West Bengal bus stops, stations, and towns from OpenStreetMap Overpass API.

Enriches:
- data/places/places.json (fills empty {} entries with verified lat/lon)
- data/stop_coords.json (adds newly geocoded bus stops/stations)

Usage:
  python3 scripts/geo/harvest_osm_stops.py          # dry run
  python3 scripts/geo/harvest_osm_stops.py --write  # apply changes
"""

import json
import re
import sys
import ssl
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STOPS_FILE = ROOT / "data" / "stops.json"
STOP_COORDS_FILE = ROOT / "data" / "stop_coords.json"
PLACES_FILE = ROOT / "data" / "places" / "places.json"

# West Bengal bounding box (approx. with margins for border towns)
WB_BBOX = "21.5,85.8,27.3,89.9"

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")

def clean_name(s):
    """Cleans suffixes like 'Bus Stand', 'Terminal', 'More', etc."""
    s = re.sub(r"\s*\([^)]*\)", "", str(s or ""))
    s = re.sub(r"\b(bus stand|bus stop|bus terminal|terminus|depot|station|stn|more|chowmatha|chowrasta)\b", "", s, flags=re.I)
    return s.strip()

def fetch_osm_data():
    """Queries OSM Overpass for bus stations, bus stops, and towns in West Bengal with retries."""
    import time
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    query = f"""
[out:json][timeout:35];
(
  node["amenity"="bus_station"]({WB_BBOX});
  node["highway"="bus_stop"]["name"]({WB_BBOX});
  node["place"~"city|town"]({WB_BBOX});
);
out body;
"""
    mirrors = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter"
    ]
    
    encoded = urllib.parse.quote(query)
    for mirror in mirrors:
        url = mirror + "?data=" + encoded
        print(f"Trying Overpass mirror: {mirror} ...")
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "BusJatriHarvester/1.0"})
                with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    elements = data.get("elements", [])
                    if elements:
                        return elements
            except Exception as e:
                print(f"  Attempt {attempt+1} failed: {e}")
                time.sleep(2)
    return []

def main(write=False):
    elements = fetch_osm_data()
    print(f"Retrieved {len(elements)} elements from OSM.")

    with open(STOPS_FILE, "r", encoding="utf-8") as f:
        known_stops = json.load(f)
    
    with open(PLACES_FILE, "r", encoding="utf-8") as f:
        places_data = json.load(f)

    with open(STOP_COORDS_FILE, "r", encoding="utf-8") as f:
        coords_data = json.load(f)

    # Build lookup index for known BusJatri stops
    stop_slug_map = {}
    for s in known_stops:
        sl = slug(s)
        stop_slug_map[sl] = s
        c_sl = slug(clean_name(s))
        if c_sl and c_sl not in stop_slug_map:
            stop_slug_map[c_sl] = s

    # Build lookup index for places.json
    places_slug_map = {slug(k): k for k in places_data.keys()}

    new_places_filled = 0
    new_stops_geocoded = 0

    for elem in elements:
        tags = elem.get("tags", {})
        lat = elem.get("lat")
        lon = elem.get("lon")
        if not lat or not lon:
            continue

        lat = round(lat, 5)
        lon = round(lon, 5)

        # Names to check: name, name:en, name:bn
        names = [tags.get("name"), tags.get("name:en"), tags.get("name:bn")]
        matched_stop_key = None
        matched_place_key = None

        for n in names:
            if not n:
                continue
            s1 = slug(n)
            s2 = slug(clean_name(n))

            if s1 in stop_slug_map:
                matched_stop_key = stop_slug_map[s1]
                break
            if s2 in stop_slug_map:
                matched_stop_key = stop_slug_map[s2]
                break

        for n in names:
            if not n:
                continue
            s1 = slug(n)
            s2 = slug(clean_name(n))

            if s1 in places_slug_map:
                matched_place_key = places_slug_map[s1]
                break
            if s2 in places_slug_map:
                matched_place_key = places_slug_map[s2]
                break

        # 1. Enrich places.json if empty
        if matched_place_key:
            curr_val = places_data.get(matched_place_key, {})
            if not curr_val or "lat" not in curr_val:
                places_data[matched_place_key] = {
                    "lat": lat,
                    "lon": lon,
                    "source": "osm"
                }
                new_places_filled += 1

        # 2. Enrich stop_coords.json if missing
        if matched_stop_key:
            if matched_stop_key not in coords_data:
                is_station = tags.get("amenity") == "bus_station"
                coords_data[matched_stop_key] = {
                    "lat": lat,
                    "lon": lon,
                    "confidence": "high" if is_station else "medium",
                    "score": 90 if is_station else 75,
                    "source": "osm"
                }
                new_stops_geocoded += 1

    print(f"Results:")
    print(f"  Empty places filled in places.json: {new_places_filled}")
    print(f"  New stops geocoded in stop_coords.json: {new_stops_geocoded}")

    if write:
        with open(PLACES_FILE, "w", encoding="utf-8") as f:
            json.dump(places_data, f, ensure_ascii=False, indent=1)
        print(f"Wrote updated {PLACES_FILE}")

        with open(STOP_COORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(coords_data, f, ensure_ascii=False, indent=2)
        print(f"Wrote updated {STOP_COORDS_FILE}")
    else:
        print("Dry run complete. Use --write to apply.")

if __name__ == "__main__":
    write_flag = "--write" in sys.argv
    main(write=write_flag)
