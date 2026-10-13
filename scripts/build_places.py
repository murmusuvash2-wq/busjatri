#!/usr/bin/env python3
"""scripts/build_places.py - build data/places/places.json.

ONE writer for the place registry. Sources:
  bus-time-table/index.html          the 800+ place names the hub lists
  data/stop_coords.json              geocoded coordinates (one writer: the geocode run)
  data/sources/place-districts.csv   place -> district mapping (hand/sourced)
Nothing here touches busjatri_data.json, so this can run in parallel with the bus-data
workflows. Idempotent: output is sorted and stable.
"""
import json, os, re, csv, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def hub_places():
    p = os.path.join(ROOT, "bus-time-table", "index.html")
    if not os.path.exists(p): return []
    s = open(p, encoding="utf-8", errors="ignore").read()
    return list(dict.fromkeys(re.findall(r'<div class="place-row" data-place="([^"]+)"', s)))

def coords():
    p = os.path.join(ROOT, "data", "stop_coords.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

def districts():
    p = os.path.join(ROOT, "data", "sources", "place-districts.csv")
    d = {}
    if os.path.exists(p):
        for row in csv.DictReader(open(p, encoding="utf-8")):
            ds = (row.get("district_or_state") or "").strip()
            if ds and ds != "(no coords)":
                d[row["place"]] = ds
    return d

def main():
    sc, ds = coords(), districts()
    out = {}
    for name in hub_places():
        e = {}
        c = sc.get(name)
        if isinstance(c, dict) and "lat" in c:
            e["lat"], e["lon"] = c["lat"], c["lon"]
        if name in ds:
            e["district"] = ds[name]
        out[name] = e
    d = os.path.join(ROOT, "data", "places")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "places.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"build_places: {len(out)} places, "
          f"{sum(1 for v in out.values() if v.get('lat'))} with coords, "
          f"{sum(1 for v in out.values() if v.get('district'))} with district")

if __name__ == "__main__":
    main()
