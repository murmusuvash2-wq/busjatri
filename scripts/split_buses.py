#!/usr/bin/env python3
"""scripts/split_buses.py - busjatri_data.json -> the editable source files.

Reads the frozen interface file and writes the one-writer-per-file sources:
  data/buses/{sbstc,nbstc,wbtc,cstc,private,community}.json
  data/routes.json   data/stops.json   data/meta.json
Each bus keeps its global position (seq) so build_buses.py can rebuild the
frozen file byte-for-byte. Idempotent.
"""
import json, os, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ORDER = ["sbstc", "nbstc", "wbtc", "cstc", "private", "community"]

def bucket(b):
    src = (b.get("source") or "").lower()
    if "facebook" in src or "community" in src: return "community"
    n = ((b.get("bus_name") or "") + " " + (b.get("bus_type") or "") + " " + (b.get("operator") or "")).upper()
    if "SBSTC" in n: return "sbstc"
    if "NBSTC" in n: return "nbstc"
    if "WBTC" in n:  return "wbtc"
    if "CSTC" in n:  return "cstc"
    return "private"

def main(write=True):
    d = json.loads((ROOT/"data"/"busjatri_data.json").read_text(encoding="utf-8"))
    buckets = collections.defaultdict(list)
    for i, b in enumerate(d["buses"]):
        buckets[bucket(b)].append({"seq": i, "bus": b})
    out = ROOT/"data"
    if write:
        (out/"buses").mkdir(parents=True, exist_ok=True)
        for k in ORDER:
            (out/"buses"/f"{k}.json").write_text(
                json.dumps({"operator": k.upper(), "count": len(buckets.get(k, [])), "buses": buckets.get(k, [])},
                           ensure_ascii=False, indent=1), encoding="utf-8")
        (out/"routes.json").write_text(json.dumps(d["routes"], ensure_ascii=False, indent=1), encoding="utf-8")
        (out/"stops.json").write_text(json.dumps(d["stops"], ensure_ascii=False, indent=1), encoding="utf-8")
        (out/"meta.json").write_text(json.dumps(d["meta"], ensure_ascii=False, indent=1), encoding="utf-8")
    print("split:", {k: len(buckets.get(k, [])) for k in ORDER}, "total", sum(len(v) for v in buckets.values()))

if __name__ == "__main__":
    main(write="--dry" not in sys.argv)
