#!/usr/bin/env python3
"""Build the small initial browser index and lazy-loaded bus detail payload.

app-index.json is now self-sufficient for search:
- per-bus `sx` = indexes into the shared `sn` stop-name table
  (js/ux-fixes.js rebuilds b.stoppages from these after load)
- stops entries keep only {name, nearest_station} (bus_ids were dead weight)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / "data/busjatri_data.json").read_text(encoding="utf-8"))

sn = []
sn_index = {}

def stop_id(name):
    name = name or ""
    if name not in sn_index:
        sn_index[name] = len(sn)
        sn.append(name)
    return sn_index[name]

search_fields = ("id", "bus_name", "bus_type", "origin", "destination", "departure_time", "total_stoppages")
search_buses = []
for bus in source["buses"]:
    b = {k: bus.get(k) for k in search_fields}
    sx = [stop_id(s.get("name")) for s in (bus.get("stoppages") or [])]
    if sx:
        b["sx"] = sx
    search_buses.append(b)

stops = {}
for key, s in (source.get("stops") or {}).items():
    stops[key] = {"name": s.get("name"), "nearest_station": s.get("nearest_station")}

index = {
    "meta": source["meta"],
    "sn": sn,
    "buses": search_buses,
    "routes": source["routes"],
    "stops": stops,
}
(ROOT / "data/app-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
(ROOT / "data/bus-details.json").write_text(json.dumps({b["id"]: b for b in source["buses"]}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("Built app-index.json (compact + stop indexes) and bus-details.json")
print("Initial index bytes:", (ROOT / "data/app-index.json").stat().st_size)
print("Lazy detail bytes:", (ROOT / "data/bus-details.json").stat().st_size)
