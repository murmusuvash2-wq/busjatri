#!/usr/bin/env python3
"""Scrape West Bengal district bus routes and timetables from WBBusTime.in.

Fetches sitemap-bus.xml (93 district bus services), extracts:
- Bus name
- Origin & Destination
- Full intermediate stoppage chain with up_time and down_time
- Departure & Arrival timings
- Distance (km)

Saves output to data-raw/wbbustime_scraped.json.

Usage:
  python3 scripts/enrich/scrape_wbbustime.py [--limit N]
"""

import argparse
import html
import json
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data-raw"
OUT_FILE = RAW_DIR / "wbbustime_scraped.json"
SITEMAP_URL = "https://wbbustime.in/sitemap-bus.xml"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


def get_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch_url(url, timeout=12):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BusJatriEnricher/1.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout, context=get_ctx()) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_bus_page(content, url):
    title_m = re.search(r"<title>(.*?)</title>", content)
    title = html.unescape(title_m.group(1)) if title_m else ""

    bus_name_m = re.search(r"\((.*?)\)", title)
    bus_name = bus_name_m.group(1).strip() if bus_name_m else "Private Bus"

    # Extract distance
    dist_m = re.search(r"approximately\s+(\d+)\s*km", content)
    dist_km = int(dist_m.group(1)) if dist_m else None

    # Extract table rows
    rows = re.findall(r"<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>", content, re.I)
    stops = []
    for i, (name, up, down) in enumerate(rows, start=1):
        clean_name = re.sub(r"<[^>]+>", "", name).strip()
        clean_up = re.sub(r"\bPRE\b", "", re.sub(r"<[^>]+>", "", up)).strip()
        clean_down = re.sub(r"\bPRE\b", "", re.sub(r"<[^>]+>", "", down)).strip()
        if clean_name.lower() in ("stop", "bus stop", "stoppage", "timing", "stop name"):
            continue
        stops.append({"no": i, "name": clean_name, "up_time": clean_up, "down_time": clean_down})

    if len(stops) < 2:
        return None

    origin = stops[0]["name"]
    destination = stops[-1]["name"]
    dep_time = stops[0]["up_time"]
    arr_time = stops[-1]["up_time"]

    bt = "Government - NON AC" if any(k in bus_name.upper() for k in ("SBSTC", "NBSTC", "WBTC", "CSTC")) else "Private - NON AC"
    op = "—"
    for corp in ("SBSTC", "NBSTC", "WBTC", "CSTC"):
        if corp in bus_name.upper():
            op = corp
            break

    bid = f"wbbustime-{slug(bus_name)}-{slug(origin)}-{slug(destination)}"

    return {
        "id": bid,
        "bus_name": bus_name,
        "reg_no": "",
        "operator": op,
        "bus_type": bt,
        "origin": origin,
        "destination": destination,
        "departure_time": dep_time,
        "arrival_time": arr_time,
        "contact_number": "Not Available !",
        "depot_name": "",
        "route": f"{origin} - {destination}",
        "stoppages": stops,
        "distance_km": dist_km,
        "source": "wbbustime.in",
        "detail_url": url
    }


def main():
    parser = argparse.ArgumentParser(description="Scrape WBBusTime district buses.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pages to scrape")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching sitemap from {SITEMAP_URL} ...")
    sitemap_xml = fetch_url(SITEMAP_URL)
    urls = re.findall(r"<loc>(.*?)</loc>", sitemap_xml)
    print(f"Found {len(urls)} bus URLs in sitemap.")

    if args.limit:
        urls = urls[:args.limit]
        print(f"Limiting to first {len(urls)} URLs.")

    scraped_buses = []
    success = 0
    fail = 0

    for idx, u in enumerate(urls, start=1):
        try:
            content = fetch_url(u)
            b = parse_bus_page(content, u)
            if b:
                scraped_buses.append(b)
                success += 1
            else:
                fail += 1
        except Exception as e:
            fail += 1
            print(f"  [{idx}/{len(urls)}] Error {u}: {e}")

        if idx % 10 == 0 or idx == len(urls):
            print(f"  Progress: [{idx}/{len(urls)}] successfully scraped: {success}, failed/skipped: {fail}", flush=True)

        time.sleep(0.3)  # Polite delay

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(scraped_buses, f, ensure_ascii=False, indent=2)

    print(f"Scrape completed successfully:")
    print(f"  Total buses scraped: {len(scraped_buses)}")
    print(f"  Output saved to: {OUT_FILE}")


if __name__ == "__main__":
    main()
