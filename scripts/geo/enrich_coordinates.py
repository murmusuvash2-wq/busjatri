#!/usr/bin/env python3
"""Enrich BusJatri stop coordinates and place locations.

Merges:
1. data/ktr_stop_coords.json (94 verified Kolkata & suburban bus stops)
2. data/sources/place-districts.csv (161 verified coordinates)
3. Verified geographic coordinates for all West Bengal district headquarters and major transit hubs

Updates:
- data/stop_coords.json
- data/places/places.json
"""

import json
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STOP_COORDS_FILE = ROOT / "data" / "stop_coords.json"
PLACES_FILE = ROOT / "data" / "places" / "places.json"
KTR_FILE = ROOT / "data" / "ktr_stop_coords.json"
DISTRICTS_CSV = ROOT / "data" / "sources" / "place-districts.csv"

# Verified coordinates for West Bengal district headquarters and key transit hubs
WB_HUBS = {
    "Alipurduar": {"lat": 26.4919, "lon": 89.5271, "district": "Alipurduar"},
    "Bankura": {"lat": 23.2324, "lon": 87.0715, "district": "Bankura"},
    "Bankura Gobindanagar": {"lat": 23.2355, "lon": 87.0682, "district": "Bankura"},
    "Cooch Behar": {"lat": 26.3239, "lon": 89.4511, "district": "Cooch Behar"},
    "Coochbehar": {"lat": 26.3239, "lon": 89.4511, "district": "Cooch Behar"},
    "Darjeeling": {"lat": 27.0410, "lon": 88.2663, "district": "Darjeeling"},
    "Jalpaiguri": {"lat": 26.5414, "lon": 88.7196, "district": "Jalpaiguri"},
    "Kalimpong": {"lat": 27.0594, "lon": 88.4695, "district": "Kalimpong"},
    "Siliguri": {"lat": 26.7271, "lon": 88.3953, "district": "Darjeeling"},
    "Balurghat": {"lat": 25.2216, "lon": 88.7644, "district": "Dakshin Dinajpur"},
    "Raiganj": {"lat": 25.6192, "lon": 88.1256, "district": "Uttar Dinajpur"},
    "Malda": {"lat": 25.0108, "lon": 88.1411, "district": "Malda"},
    "English Bazar": {"lat": 25.0044, "lon": 88.1458, "district": "Malda"},
    "Baharampur": {"lat": 24.0988, "lon": 88.2680, "district": "Murshidabad"},
    "Berhampore": {"lat": 24.0988, "lon": 88.2680, "district": "Murshidabad"},
    "Suri": {"lat": 23.9056, "lon": 87.5246, "district": "Birbhum"},
    "Bolpur": {"lat": 23.6693, "lon": 87.6938, "district": "Birbhum"},
    "Rampurhat": {"lat": 24.1687, "lon": 87.7819, "district": "Birbhum"},
    "Bardhaman": {"lat": 23.2324, "lon": 87.8615, "district": "Purba Bardhaman"},
    "Burdwan": {"lat": 23.2324, "lon": 87.8615, "district": "Purba Bardhaman"},
    "Durgapur": {"lat": 23.5204, "lon": 87.3119, "district": "Paschim Bardhaman"},
    "Asansol": {"lat": 23.6739, "lon": 86.9524, "district": "Paschim Bardhaman"},
    "Purulia": {"lat": 23.3322, "lon": 86.3652, "district": "Purulia"},
    "Medinipur": {"lat": 22.4257, "lon": 87.3199, "district": "Paschim Medinipur"},
    "Midnapore": {"lat": 22.4257, "lon": 87.3199, "district": "Paschim Medinipur"},
    "Kharagpur": {"lat": 22.3460, "lon": 87.2320, "district": "Paschim Medinipur"},
    "Jhargram": {"lat": 22.4550, "lon": 86.9944, "district": "Jhargram"},
    "Tamluk": {"lat": 22.2965, "lon": 87.9221, "district": "Purba Medinipur"},
    "Contai": {"lat": 21.7781, "lon": 87.7517, "district": "Purba Medinipur"},
    "Kanthi": {"lat": 21.7781, "lon": 87.7517, "district": "Purba Medinipur"},
    "Digha": {"lat": 21.6266, "lon": 87.5074, "district": "Purba Medinipur"},
    "Haldia": {"lat": 22.0667, "lon": 88.0698, "district": "Purba Medinipur"},
    "Howrah": {"lat": 22.5958, "lon": 88.2636, "district": "Howrah"},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639, "district": "Kolkata"},
    "Barasat": {"lat": 22.7242, "lon": 88.4819, "district": "North 24 Parganas"},
    "Barrackpore": {"lat": 22.7667, "lon": 88.3667, "district": "North 24 Parganas"},
    "Basirhat": {"lat": 22.6574, "lon": 88.8914, "district": "North 24 Parganas"},
    "Bongaon": {"lat": 23.0437, "lon": 88.8266, "district": "North 24 Parganas"},
    "Diamond Harbour": {"lat": 22.1912, "lon": 88.1903, "district": "South 24 Parganas"},
    "Baruipur": {"lat": 22.3654, "lon": 88.4325, "district": "South 24 Parganas"},
    "Canning": {"lat": 22.3094, "lon": 88.6575, "district": "South 24 Parganas"},
    "Krishnanagar": {"lat": 23.4013, "lon": 88.5019, "district": "Nadia"},
    "Ranaghat": {"lat": 23.1809, "lon": 88.5795, "district": "Nadia"},
    "Kalyani": {"lat": 22.9751, "lon": 88.4345, "district": "Nadia"},
    "Chinsurah": {"lat": 22.9031, "lon": 88.3968, "district": "Hooghly"},
    "Chandannagar": {"lat": 22.8671, "lon": 88.3674, "district": "Hooghly"},
    "Tarakeswar": {"lat": 22.8869, "lon": 88.0203, "district": "Hooghly"},
    "Arambagh": {"lat": 22.8833, "lon": 87.7833, "district": "Hooghly"},
    "Arambag": {"lat": 22.8833, "lon": 87.7833, "district": "Hooghly"},
    "Mecheda": {"lat": 22.4172, "lon": 87.8631, "district": "Purba Medinipur"},
    "Kolaghat": {"lat": 22.4316, "lon": 87.8711, "district": "Purba Medinipur"},
    "Ghatal": {"lat": 22.6710, "lon": 87.7225, "district": "Paschim Medinipur"},
    "Bishnupur": {"lat": 23.0678, "lon": 87.3175, "district": "Bankura"},
    "Khatra": {"lat": 22.9814, "lon": 86.8528, "district": "Bankura"},
}


def main():
    with open(STOP_COORDS_FILE, "r", encoding="utf-8") as f:
        coords = json.load(f)

    with open(PLACES_FILE, "r", encoding="utf-8") as f:
        places = json.load(f)

    initial_coords = len(coords)
    initial_places = sum(1 for v in places.values() if v and "lat" in v)

    # 1. Apply WB_HUBS
    for name, data in WB_HUBS.items():
        if name not in coords:
            coords[name] = {
                "lat": data["lat"],
                "lon": data["lon"],
                "confidence": "high",
                "score": 100,
                "source": "wb_hubs"
            }
        if name in places:
            if not places[name] or "lat" not in places[name]:
                places[name] = {
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "district": data.get("district", ""),
                    "source": "wb_hubs"
                }

    # 2. Apply KTR Coordinates (Kolkata Transit)
    if KTR_FILE.exists():
        with open(KTR_FILE, "r", encoding="utf-8") as f:
            ktr = json.load(f)
        for name, pt in ktr.items():
            if name not in coords:
                coords[name] = {
                    "lat": pt["lat"],
                    "lon": pt["lng"],
                    "confidence": "high",
                    "score": 95,
                    "source": "ktr"
                }
            if name in places:
                if not places[name] or "lat" not in places[name]:
                    places[name] = {
                        "lat": pt["lat"],
                        "lon": pt["lng"],
                        "source": "ktr"
                    }

    # 3. Apply place-districts.csv valid coords
    if DISTRICTS_CSV.exists():
        with open(DISTRICTS_CSV, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                p = (row.get("place") or "").strip()
                lat = row.get("lat")
                lon = row.get("lon")
                dist = row.get("district_or_state")
                if p and lat and lon:
                    try:
                        fl_lat = round(float(lat), 5)
                        fl_lon = round(float(lon), 5)
                        if p not in coords:
                            coords[p] = {
                                "lat": fl_lat,
                                "lon": fl_lon,
                                "confidence": "high",
                                "score": 90,
                                "source": "place_districts"
                            }
                        if p in places:
                            if not places[p] or "lat" not in places[p]:
                                places[p] = {
                                    "lat": fl_lat,
                                    "lon": fl_lon,
                                    "district": dist or "",
                                    "source": "place_districts"
                                }
                    except ValueError:
                        pass

    final_coords = len(coords)
    final_places = sum(1 for v in places.values() if v and "lat" in v)

    with open(STOP_COORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(coords, f, ensure_ascii=False, indent=2)

    with open(PLACES_FILE, "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=1)

    print("Enrichment summary:")
    print(f"  stop_coords.json: {initial_coords} -> {final_coords} (+{final_coords - initial_coords} stops)")
    print(f"  places.json: {initial_places} -> {final_places} (+{final_places - initial_places} places filled)")


if __name__ == "__main__":
    main()
