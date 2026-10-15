#!/usr/bin/env python3
"""District-Level Bus Scraper & Enrichment Pipeline for BusJatri.

Provides:
1. Ingestion of scraped district buses from web sources (wbbus, bussathi, district transport blogs)
2. Intelligent deduplication and non-destructive merging with existing buses
3. Safe enrichment of data/buses/private.json and rebuilding of data/busjatri_data.json

Usage:
  python3 scripts/enrich/scrape_district_buses.py --input <path_to_scraped_json_or_csv> [--write]
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data" / "busjatri_data.json"
PRIVATE_BUSES_FILE = ROOT / "data" / "buses" / "private.json"

sys.path.insert(0, str(ROOT))
from scripts.dedup.dedup_engine import is_duplicate, merge_bus_records, slug, canon_place


def parse_args():
    parser = argparse.ArgumentParser(description="Enrich district buses into BusJatri.")
    parser.add_argument("--input", help="Path to scraped JSON or CSV file", default=None)
    parser.add_argument("--write", action="store_true", help="Apply changes to data files")
    return parser.parse_args()


def load_input_data(path_str):
    if not path_str:
        return []
    p = Path(path_str)
    if not p.exists():
        print(f"Error: file not found: {p}")
        return []

    if p.suffix == ".json":
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if isinstance(raw, list):
                return raw
            if isinstance(raw, dict) and "buses" in raw:
                return raw["buses"]
            return []
    elif p.suffix in (".csv", ".tsv"):
        delimiter = "\t" if p.suffix == ".tsv" else ","
        entries = []
        with open(p, "r", encoding="utf-8") as f:
            r = csv.DictReader(f, delimiter=delimiter)
            for row in r:
                stops_str = row.get("stoppages") or row.get("stops") or ""
                stops_list = [{"name": s.strip()} for s in stops_str.split(",") if s.strip()]
                entries.append({
                    "id": row.get("id") or f"dist-{slug(row.get('bus_name', 'bus'))}-{slug(row.get('origin', ''))}-{slug(row.get('destination', ''))}",
                    "bus_name": row.get("bus_name", ""),
                    "reg_no": row.get("reg_no", ""),
                    "operator": row.get("operator", "—"),
                    "bus_type": row.get("bus_type", "Private - NON AC"),
                    "origin": row.get("origin", ""),
                    "destination": row.get("destination", ""),
                    "departure_time": row.get("departure_time", ""),
                    "arrival_time": row.get("arrival_time", ""),
                    "contact_number": row.get("contact_number", "Not Available !"),
                    "depot_name": row.get("depot_name", ""),
                    "route": row.get("route") or f"{row.get('origin', '')} - {row.get('destination', '')}",
                    "stoppages": stops_list,
                    "source": row.get("source", "district-scrape")
                })
        return entries
    return []


def main():
    args = parse_args()
    new_entries = load_input_data(args.input)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    existing_buses = master_data.get("buses", [])
    print(f"Loaded {len(existing_buses)} master buses.")
    print(f"Input contains {len(new_entries)} candidate district records.")

    enriched_count = 0
    newly_added = []

    for cand in new_entries:
        # Check against existing buses
        matched_idx = None
        for i, b in enumerate(existing_buses):
            if is_duplicate(b, cand):
                matched_idx = i
                break

        if matched_idx is not None:
            # Merge into existing record
            existing_buses[matched_idx] = merge_bus_records(existing_buses[matched_idx], cand)
            enriched_count += 1
        else:
            # Genuinely new bus
            newly_added.append(cand)

    print(f"Pipeline outcome:")
    print(f"  Existing buses enriched with richer stops/details: {enriched_count}")
    print(f"  New district buses ready to be added: {len(newly_added)}")

    if args.write and (enriched_count > 0 or newly_added):
        # 1. Update data/busjatri_data.json
        master_data["buses"] = existing_buses + newly_added
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(master_data, f, ensure_ascii=False, indent=1)
        print(f"Updated {DATA_FILE}")

        # 2. Append newly added to data/buses/private.json if applicable
        if newly_added and PRIVATE_BUSES_FILE.exists():
            with open(PRIVATE_BUSES_FILE, "r", encoding="utf-8") as f:
                priv = json.load(f)
            seq_start = max((e.get("seq", 0) for e in priv.get("buses", [])), default=9000) + 1
            for idx, nb in enumerate(newly_added):
                priv["buses"].append({
                    "seq": seq_start + idx,
                    "bus": nb
                })
            priv["count"] = len(priv["buses"])
            with open(PRIVATE_BUSES_FILE, "w", encoding="utf-8") as f:
                json.dump(priv, f, ensure_ascii=False, indent=1)
            print(f"Appended {len(newly_added)} buses to {PRIVATE_BUSES_FILE}")


if __name__ == "__main__":
    main()
