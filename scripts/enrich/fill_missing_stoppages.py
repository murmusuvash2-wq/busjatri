#!/usr/bin/env python3
"""scripts/enrich/fill_missing_stoppages.py

Enriches buses in data/buses/*.json that lack intermediate stoppages (<= 2 stops)
using data-driven sibling inheritance and route reversal:
1. Sibling match: Copy full stoppage sequence from direct bus on same route.
2. Reverse match: Copy and reverse stoppage sequence from opposite direction route.
"""

import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


def main(write=True):
    # 1. Build catalog of rich stoppages (> 2 stops)
    rich_catalog = {}
    for p in sorted(glob.glob(str(ROOT / "data" / "buses" / "*.json"))):
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        for entry in d.get("buses", []):
            b = entry.get("bus", {})
            st = b.get("stoppages") or []
            if len(st) > 2:
                o = slug(b.get("origin"))
                d_slug = slug(b.get("destination"))
                if o and d_slug:
                    key = (o, d_slug)
                    if key not in rich_catalog or len(st) > len(rich_catalog[key]):
                        rich_catalog[key] = [
                            {"name": s.get("name") if isinstance(s, dict) else str(s)}
                            for s in st
                            if (s.get("name") if isinstance(s, dict) else str(s))
                        ]

    print(f"Loaded {len(rich_catalog)} rich route stoppage sequences into catalog.")

    total_enriched = 0
    total_sibling = 0
    total_reversed = 0

    for p in sorted(glob.glob(str(ROOT / "data" / "buses" / "*.json"))):
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        enriched_in_file = 0
        for entry in d.get("buses", []):
            b = entry.get("bus", {})
            st = b.get("stoppages") or []
            if len(st) <= 2:
                o = slug(b.get("origin"))
                d_slug = slug(b.get("destination"))
                new_stops = None
                mode = None
                if (o, d_slug) in rich_catalog:
                    new_stops = list(rich_catalog[(o, d_slug)])
                    mode = "sibling"
                elif (d_slug, o) in rich_catalog:
                    rev = rich_catalog[(d_slug, o)]
                    new_stops = list(reversed(rev))
                    mode = "reverse"

                if new_stops and len(new_stops) > 2:
                    b["stoppages"] = new_stops
                    b["total_stoppages"] = len(new_stops)
                    enriched_in_file += 1
                    total_enriched += 1
                    if mode == "sibling":
                        total_sibling += 1
                    else:
                        total_reversed += 1

        if write and enriched_in_file > 0:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            print(f"Updated {Path(p).name}: enriched {enriched_in_file} buses")
        else:
            print(f"{Path(p).name}: {enriched_in_file} buses to enrich")

    print(f"\nDone! Enriched {total_enriched} buses (Sibling: {total_sibling}, Reverse: {total_reversed})")


if __name__ == "__main__":
    main(write=True)
