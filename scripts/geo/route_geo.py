#!/usr/bin/env python3
"""BusJatri Route Geography, Polyline, Distance & Fare Engine.

Provides:
- Geocoding lookup for West Bengal bus stops (stop_coords.json + places.json)
- Ordered polyline coordinates for a sequence of stoppages
- Accurate road distance (km) estimation using Haversine + road winding factor (1.25)
- Realistic approx travel time estimation based on terrain & bus category
- West Bengal stage carriage fare estimation (Ordinary, Express, AC/Volvo)
"""

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STOP_COORDS_FILE = ROOT / "data" / "stop_coords.json"
PLACES_FILE = ROOT / "data" / "places" / "places.json"

_COORDS_CACHE = None


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


def load_coords():
    global _COORDS_CACHE
    if _COORDS_CACHE is not None:
        return _COORDS_CACHE

    coords = {}

    # 1. Primary stop_coords.json
    if STOP_COORDS_FILE.exists():
        try:
            with open(STOP_COORDS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                for name, data in raw.items():
                    if isinstance(data, dict) and "lat" in data and "lon" in data:
                        k = slug(name)
                        coords[k] = (float(data["lat"]), float(data["lon"]))
        except Exception:
            pass

    # 2. Supplementary places.json
    if PLACES_FILE.exists():
        try:
            with open(PLACES_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                for name, data in raw.items():
                    if isinstance(data, dict) and "lat" in data and "lon" in data:
                        k = slug(name)
                        if k not in coords:
                            coords[k] = (float(data["lat"]), float(data["lon"]))
        except Exception:
            pass

    _COORDS_CACHE = coords
    return _COORDS_CACHE


# Common place name aliases in West Bengal
ALIASES = {
    "durgapur-station": "durgapur",
    "durgapur-stn": "durgapur",
    "durgapur-city-center": "durgapur",
    "durgapur-city-centre": "durgapur",
    "durgapur-bus-stand": "durgapur",
    "bankura-bus-stand": "bankura",
    "bankura-gobindanagar": "bankura",
    "bankura-station": "bankura",
    "bankura-bypass": "bankura",
    "esplanade": "kolkata",
    "dharmatala": "kolkata",
    "dharmatola": "kolkata",
    "babughat": "kolkata",
    "karunamoyee": "kolkata",
    "saltlake": "kolkata",
    "howrah-stn": "howrah",
    "howrah-station": "howrah",
    "sealdah": "kolkata",
    "contai": "kanthi",
    "berhampore": "baharampur",
    "berhampur": "baharampur",
    "burdwan": "bardhaman",
    "burdwan-nawabhat": "bardhaman",
    "barddhaman": "bardhaman",
    "midnapore": "medinipur",
    "midnapur": "medinipur",
    "coochbehar": "cooch-behar",
    "koch-bihar": "cooch-behar",
    "siliguri-tenzing-norgay": "siliguri",
    "siliguri-junction": "siliguri",
    "tarakeshwar": "tarakeswar",
    "arambagh": "arambag",
    "barasat-chapadali": "barasat",
    "barasat-chapadali-bus-stand": "barasat",
    "barddhaman-nawabhat-bus-stand": "bardhaman",
    "barddhaman-nawabhat": "bardhaman",
    "barddhaman-alisha-bus-stand": "bardhaman",
    "alisha-bus-stand": "bardhaman",
    "habra-depot": "habra",
    "habra-station": "habra",
    "siliguri-courtmore": "siliguri",
    "siliguri-tncbt": "siliguri",
    "kolkata-a-c": "kolkata",
    "kolkata-airport": "airport",
    "kolkata-esplanade": "kolkata",
    "barrackpore-court": "barrackpore",
    "tollygunge-metro": "tollygunge",
    "kudghat": "tollygunge",
    "panshkura": "panskura",
    "naihati-station": "naihati",
    "ballyhalt": "bally",
    "unitech-gate-2": "unitech-gate-1",
    "ecospace": "shapoorji",
    "eco-space": "shapoorji",
    "technopolis": "saltlake",
}


def get_stop_coords(stop_name):
    """Returns (lat, lon) tuple for a stop name or None."""
    coords = load_coords()
    k = slug(stop_name)
    if k in coords:
        return coords[k]
    # Check aliases
    if k in ALIASES and ALIASES[k] in coords:
        return coords[ALIASES[k]]
    # Check partial / strip common stand suffixes
    cleaned = re.sub(
        r"-(station|stn|bus-stand|bustand|more|chowmatha|terminal|depot|bypass)$",
        "",
        k,
    )
    if cleaned in coords:
        return coords[cleaned]
    if cleaned in ALIASES and ALIASES[cleaned] in coords:
        return coords[ALIASES[cleaned]]
    return None


def haversine_km(lat1, lon1, lat2, lon2):
    """Calculates straight-line distance in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def calculate_route_polyline(stoppages):
    """Given a list of stop names or stop objects, returns list of [lat, lon] points."""
    pts = []
    for s in stoppages:
        name = s.get("name") if isinstance(s, dict) else str(s)
        c = get_stop_coords(name)
        if c:
            pts.append([round(c[0], 5), round(c[1], 5)])
    return pts


def calculate_route_distance(stoppages, origin=None, destination=None):
    """Estimates road distance in km for a sequence of stops.

    Applies road tortuosity/winding factor (1.25) over geographic points.
    Filters out outlier geocodes that stray far outside the origin-destination corridor.
    Guarantees consistency against origin-destination baseline.
    """
    pts = calculate_route_polyline(stoppages)

    co = get_stop_coords(origin) if origin else None
    cd = get_stop_coords(destination) if destination else None
    od_road_km = None
    if co and cd:
        od_road_km = round(haversine_km(co[0], co[1], cd[0], cd[1]) * 1.25, 1)

    # Filter out outlier intermediate points that lie far outside the origin-destination corridor
    if co and cd:
        min_lat = min(co[0], cd[0]) - 0.4
        max_lat = max(co[0], cd[0]) + 0.4
        min_lon = min(co[1], cd[1]) - 0.4
        max_lon = max(co[1], cd[1]) + 0.4
        pts = [p for p in pts if min_lat <= p[0] <= max_lat and min_lon <= p[1] <= max_lon]
        # Anchor endpoints
        pts = [[co[0], co[1]]] + [p for p in pts if p != [co[0], co[1]] and p != [cd[0], cd[1]]] + [[cd[0], cd[1]]]

    if len(pts) < 2:
        return od_road_km

    total_km = 0.0
    for i in range(len(pts) - 1):
        d = haversine_km(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        # Ignore spurious jumps > 150km for single local stop hops
        if d < 120:
            total_km += d

    road_km = round(total_km * 1.25, 1)
    if od_road_km:
        road_km = max(road_km, od_road_km)

    return road_km if road_km >= 3.0 else None


def calculate_approx_time(distance_km, bus_type="Ordinary"):
    """Calculates realistic travel duration in minutes based on distance and bus category.

    - Express / Long Distance / AC: ~45-50 km/h avg speed
    - Local / Line / Ordinary: ~30-35 km/h avg speed
    """
    if not distance_km or distance_km <= 0:
        return None

    bt = (bus_type or "").lower()
    if "ac" in bt or "volvo" in bt or "express" in bt or "super" in bt:
        avg_speed = 46.0  # km/h
        buffer_min = 10
    else:
        avg_speed = 32.0  # km/h
        buffer_min = 15

    mins = int(round((distance_km / avg_speed) * 60.0 + buffer_min))
    return mins


def format_duration(minutes):
    """Formats minutes into human-readable English and Bengali string."""
    if not minutes:
        return {"en": "—", "bn": "—"}
    h = minutes // 60
    m = minutes % 60
    bn_digits = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

    if h > 0 and m > 0:
        en = f"{h}h {m}m"
        bn = f"{str(h).translate(bn_digits)} ঘণ্টা {str(m).translate(bn_digits)} মিনিট"
    elif h > 0:
        en = f"{h} hours"
        bn = f"{str(h).translate(bn_digits)} ঘণ্টা"
    else:
        en = f"{m} mins"
        bn = f"{str(m).translate(bn_digits)} মিনিট"
    return {"en": en, "bn": bn, "minutes": minutes}


def calculate_fare(distance_km, bus_type="Ordinary"):
    """Estimates West Bengal bus fare range based on official stage carriage slabs.

    West Bengal Stage Carriage Fare structure:
    1. Ordinary / Non-AC Stage Carriage:
       - Base fare up to 4 km: ₹10
       - 5 to 25 km: ₹1.05/km
       - 25+ km: ₹0.95 - ₹1.00/km
    2. Express / Limited Stop:
       - Base: ₹15
       - Per km: ~₹1.20 - ₹1.40/km
    3. AC / Volvo (Govt & Private):
       - Base: ₹25 - ₹35
       - Per km: ~₹1.80 - ₹2.50/km
    """
    if not distance_km or distance_km <= 0:
        return None

    bt = (bus_type or "").lower()
    is_ac = "ac" in bt or "volvo" in bt
    is_express = "express" in bt or "fast" in bt or "limited" in bt

    if is_ac:
        min_fare = int(round(max(30, 25 + distance_km * 1.85)))
        max_fare = int(round(max(40, 35 + distance_km * 2.40)))
    elif is_express:
        min_fare = int(round(max(15, 12 + distance_km * 1.15)))
        max_fare = int(round(max(20, 16 + distance_km * 1.40)))
    else:  # Ordinary / Private Line Bus
        min_fare = int(round(max(10, 8 + distance_km * 0.95)))
        max_fare = int(round(max(12, 11 + distance_km * 1.15)))

    # Round to nearest ₹5 for clean user display
    min_fare = max(10, int(round(min_fare / 5.0) * 5))
    max_fare = max(min_fare + 5, int(round(max_fare / 5.0) * 5))

    bn_digits = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
    return {
        "min": min_fare,
        "max": max_fare,
        "label_en": f"₹{min_fare} – ₹{max_fare}",
        "label_bn": f"₹{str(min_fare).translate(bn_digits)} – ₹{str(max_fare).translate(bn_digits)}",
    }


if __name__ == "__main__":
    # Test with Durgapur to Bankura
    durgapur_stops = [
        "Durgapur Station",
        "Barjora",
        "Beliatore",
        "Bankura",
    ]
    dist = calculate_route_distance(
        durgapur_stops, "Durgapur Station", "Bankura"
    )
    poly = calculate_route_polyline(durgapur_stops)
    dur = calculate_approx_time(dist, "Ordinary")
    fare = calculate_fare(dist, "Ordinary")
    print(f"Durgapur -> Bankura:")
    print(f"  Stops with coords: {len(poly)}/{len(durgapur_stops)}")
    print(f"  Estimated road distance: {dist} km")
    print(f"  Estimated duration: {format_duration(dur)['en']}")
    print(f"  Estimated fare: {fare['label_en']} ({fare['label_bn']})")
