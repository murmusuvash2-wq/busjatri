#!/usr/bin/env python3
"""Remove buses listed in data/bus_removals.json from data/busjatri_data.json.

Why this exists: dedup_buses.py only catches untimed copies that share the same
bus_name AND the same first/last stoppage. Untimed stubs scraped from other
timetable sites often fail both tests - they carry a bare operator name and
sometimes only cover a middle segment of the route - so they survive as a second,
empty row on the route page (and can skew the journey-time estimate).

Ids listed here are dropped from the master bus list. build_client_data.py then
regenerates data/bus-details/ from that list, so a removal is permanent.

Idempotent: an id that is already absent is skipped.

Usage:
  python3 scripts/patch_fb_zzz_remove_buses.py          # dry run
  python3 scripts/patch_fb_zzz_remove_buses.py --write  # apply
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITE = "--write" in sys.argv


def main():
    data_p = ROOT / "data" / "busjatri_data.json"
    rem_p = ROOT / "data" / "bus_removals.json"
    if not rem_p.exists():
        print("ok (no data/bus_removals.json - nothing to remove)")
        return

    removals = json.loads(rem_p.read_text(encoding="utf-8"))
    ids = {r.get("id") for r in removals if r.get("id")}
    if not ids:
        print("ok (bus_removals.json is empty)")
        return

    data = json.loads(data_p.read_text(encoding="utf-8"))
    before = len(data["buses"])
    kept, dropped = [], []
    for b in data["buses"]:
        if b.get("id") in ids:
            dropped.append(b.get("id"))
        else:
            kept.append(b)

    if not dropped:
        print("ok (all %d removal ids already absent)" % len(ids))
        return

    print("removing %d bus(es): %s" % (len(dropped), ", ".join(dropped)))
    data["buses"] = kept
    data.setdefault("meta", {})["total_buses"] = len(kept)

    if WRITE:
        data_p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print("written: %d -> %d buses" % (before, len(kept)))
    else:
        print("dry run - nothing written (use --write)")


main()
