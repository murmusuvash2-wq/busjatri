#!/usr/bin/env python3
"""Fix: TANIMA (bussathi-tanima-810) stop count changed 7 -> 8 when the
route was extended to Chandpal, but the enrich entry in
data/community_buses.json did not update total_stoppages (app cards show
total_stoppages). Adds total_stoppages to the enrich entry. Idempotent."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv

pc = ROOT / "data" / "community_buses.json"
cb = json.loads(pc.read_text(encoding="utf-8"))

for e in cb.get("enrich", []):
    if e.get("target_id") == "bussathi-tanima-810" and isinstance(
        e.get("stoppages"), list
    ):
        n = len(e["stoppages"])
        if e.get("total_stoppages") == n:
            print("ok (total_stoppages already %d)" % n)
            sys.exit(0)
        e["total_stoppages"] = n
        if DRY:
            print("dry run: would set total_stoppages = %d" % n)
            sys.exit(0)
        pc.write_text(
            json.dumps(cb, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print("written: total_stoppages = %d" % n)
        sys.exit(0)

print("TANIMA enrich entry not found - nothing to do")
