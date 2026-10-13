#!/usr/bin/env python3
"""scripts/build_buses.py - merge the source files back into the frozen file.

data/buses/*.json + data/routes.json + data/stops.json + data/meta.json
    -> data/busjatri_data.json   (schema + byte format unchanged: indent=1)
Buses are restored to their original global order via each record's seq.
"""
import json, sys, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main(write=True):
    recs = []
    for f in sorted(glob.glob(str(ROOT/"data"/"buses"/"*.json"))):
        for e in json.loads(Path(f).read_text(encoding="utf-8")).get("buses", []):
            recs.append((e["seq"], e["bus"]))
    recs.sort(key=lambda x: x[0])
    data = {
        "buses":  [b for _, b in recs],
        "routes": json.loads((ROOT/"data"/"routes.json").read_text(encoding="utf-8")),
        "stops":  json.loads((ROOT/"data"/"stops.json").read_text(encoding="utf-8")),
        "meta":   json.loads((ROOT/"data"/"meta.json").read_text(encoding="utf-8")),
    }
    s = json.dumps(data, ensure_ascii=False, indent=1)
    if write:
        (ROOT/"data"/"busjatri_data.json").write_text(s, encoding="utf-8")
    print(f"build_buses: {len(data['buses'])} buses, {len(data['routes'])} routes, {len(data['stops'])} stops")

if __name__ == "__main__":
    main(write="--dry" not in sys.argv)
