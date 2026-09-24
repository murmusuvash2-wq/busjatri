#!/usr/bin/env python3
"""Build the small initial browser index and lazy-loaded bus detail payload.

app-index.json is now self-sufficient for search:
- per-bus `sx` = indexes into the shared `sn` stop-name table
- per-bus `ux`/`dx` = up/down times at each stop as minutes (0 = none)
  (js/ux-fixes.js rebuilds b.stoppages with um/dm after load, so search
  covers BOTH directions of every service - return journeys too)
- stops entries keep only {name, nearest_station} (bus_ids were dead weight)

Stop names are whitespace-collapsed (scraped names sometimes contain embedded
newlines), so search and the datalist see one clean spelling.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / "data" / "busjatri_data.json").read_text(encoding="utf-8"))

sn = []
sn_index = {}

def tidy(n):
    return " ".join(str(n or "").split())

def stop_id(name):
    name = tidy(name)  # collapse newlines / extra spaces
    if name not in sn_index:
        sn_index[name] = len(sn)
        sn.append(name)
    return sn_index[name]

def t2m(t):
    """'7:50 PM' -> minutes past midnight (0 = missing)."""
    import re as _re
    if not t:
        return 0
    m = _re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM)?", str(t), _re.I)
    if not m:
        return 0
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").upper()
    if ap == "PM" and h != 12:
        h += 12
    if ap == "AM" and h == 12:
        h = 0
    return (h % 24) * 60 + mi

search_fields = ("id", "bus_name", "reg_no", "bus_type", "origin", "destination", "departure_time", "total_stoppages")
search_buses = []
for bus in source["buses"]:
    b = {k: bus.get(k) for k in search_fields}
    b["origin"] = tidy(b.get("origin"))
    b["destination"] = tidy(b.get("destination"))
    stop_list = bus.get("stoppages") or []
    sx = [stop_id(s.get("name")) for s in stop_list]
    if sx:
        b["sx"] = sx
        b["ux"] = [t2m(s.get("up_time")) for s in stop_list]
        b["dx"] = [t2m(s.get("down_time")) for s in stop_list]
    search_buses.append(b)

stops = {}
for key, s in (source.get("stops") or {}).items():
    ck = tidy(key)
    stops[ck] = {"name": ck, "nearest_station": s.get("nearest_station")}

index = {
    "meta": {**source["meta"], "total_buses": len(source["buses"])},
    "sn": sn,
    "buses": search_buses,
    "routes": source["routes"],
    "stops": stops,
}
(ROOT / "data" / "app-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

from collections import Counter as _Counter
_pair = _Counter()
for _bus in source["buses"]:
    _o = tidy(_bus.get("origin"))
    _d = tidy(_bus.get("destination"))
    if _o and _d and _o != _d:
        _pair[(_o, _d)] += 1
_home = {"meta": index["meta"], "sn": sn,
         "top": [{"from": _o, "to": _d, "n": _c} for (_o, _d), _c in _pair.most_common(10)]}
(ROOT / "data" / "home-index.json").write_text(json.dumps(_home, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
lite = dict(index)
lite["buses"] = [{k: v for k, v in b.items() if k not in ("sx", "ux", "dx")} for b in search_buses]
(ROOT / "data" / "app-index-lite.json").write_text(json.dumps(lite, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
(ROOT / "data" / "bus-details.json").write_text(json.dumps({b["id"]: b for b in source["buses"]}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
import shutil
details_dir = ROOT / "data" / "bus-details"
if details_dir.exists():
    shutil.rmtree(details_dir)
details_dir.mkdir(parents=True)
for bus in source["buses"]:
    (details_dir / (bus["id"] + ".json")).write_text(json.dumps(bus, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("Built app-index.json, home-index.json, app-index-lite.json and per-bus details")
print("Lite index bytes:", (ROOT / "data" / "app-index-lite.json").stat().st_size)
print("Full index bytes:", (ROOT / "data" / "app-index.json").stat().st_size)
print("Per-bus detail files:", len(list(details_dir.glob("*.json"))))
print("Legacy bulk detail bytes:", (ROOT / "data" / "bus-details.json").stat().st_size)
