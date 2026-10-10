#!/usr/bin/env python3
"""Fix the mislabeled "Darjeeling" stoppage on South-Bengal corridor buses.

The Bolpur - Illambazar - Panagarh stretch of NH-19 passes a junction called
"Darjeeling More". Some scraped records stored that stop as a bare "Darjeeling",
which made those buses (e.g. ACT-13 Suri -> Esplanade) show up on the Darjeeling
place page even though they never go anywhere near the hill town.

Rule: if a bus's own origin/destination is NOT Darjeeling, rename any stoppage
named exactly "Darjeeling" to "Darjeeling More". Buses that genuinely start or
end at Darjeeling (the NBSTC Siliguri-Darjeeling services) are left untouched.

Idempotent - a stop already named "Darjeeling More" is skipped.

Usage:
  python3 scripts/patch_fb_zzz_darjeeling_more.py          # dry run
  python3 scripts/patch_fb_zzz_darjeeling_more.py --write  # apply
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "busjatri_data.json"
WRITE = "--write" in sys.argv

TARGET = "darjeeling"
FIXED = "Darjeeling More"


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    buses = data.get("buses", [])
    changed = []

    for b in buses:
        ends = (b.get("origin", "") + " " + b.get("destination", "")).lower()
        if TARGET in ends:
            # a genuine Darjeeling route - leave it alone
            continue
        for s in b.get("stoppages", []):
            if (s.get("name") or "").strip().lower() == TARGET:
                s["name"] = FIXED
                changed.append((b.get("id"), b.get("origin"), b.get("destination")))

    if not changed:
        print("darjeeling-more: nothing to fix (already clean)")
        return

    print("darjeeling-more: renamed a mislabeled stop on %d bus(es):" % len(changed))
    for bid, o, d in changed:
        print("   %s  (%s -> %s)" % (bid, o, d))

    if not WRITE:
        print("dry run - nothing written (use --write)")
        return

    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written: %s" % DATA.name)


if __name__ == "__main__":
    main()
