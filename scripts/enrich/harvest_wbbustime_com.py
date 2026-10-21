#!/usr/bin/env python3
"""harvest_wbbustime_com.py - Fast, robust multithreaded scraper for wbbustime.com
Extracts authentic West Bengal buses with stop-by-stop timelines.
"""

import concurrent.futures
import json
import os
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_RAW = ROOT / "data-raw" / "wbbustime_com_scraped.json"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BusJatriMegaScraper/1.0"}


def get_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def parse_page(html, bid):
    title_m = re.search(r"<title>(.*?)</title>", html)
    if not title_m or "Bus Time Table" not in title_m.group(1):
        return None
    raw_title = title_m.group(1).split("|")[0].strip()

    m_split = re.match(r"^(.*?)\s*-\s*(.*?)\s+to\s+(.*?)\s+Bus Time Table", raw_title, re.I)
    if not m_split:
        return None

    bus_name = m_split.group(1).strip()
    origin = m_split.group(2).strip()
    destination = m_split.group(3).strip()

    items = re.findall(
        r"<div class=[\"\x27]timeline-item[\"\x27]>(.*?)(?=<div class=[\"\x27]timeline-item[\"\x27]|</div>\s*</div>\s*</div>\s*</div>)",
        html,
        re.S,
    )
    stops = []
    dep_time = ""
    arr_time = ""

    for i, it in enumerate(items):
        m_name = re.search(r"fw-bold[\"\x27][^>]*>(.*?)</a>", it)
        m_time = re.search(r"class=[\"\x27]stop-time[\"\x27]>(.*?)</span>", it)
        name = re.sub(r"<[^>]+>", "", m_name.group(1)).strip() if m_name else ""
        time_str = m_time.group(1).strip() if m_time else ""
        if name:
            stops.append({"no": len(stops) + 1, "name": name, "up_time": time_str, "down_time": ""})
            if not dep_time and time_str:
                dep_time = time_str
            if time_str:
                arr_time = time_str

    if not dep_time or not arr_time or len(stops) < 2:
        return None

    op = "Private"
    btype = "Private - NON AC"
    name_l = bus_name.lower()
    if "sbstc" in name_l:
        op = "SBSTC"
        btype = "Government - NON AC"
    elif "nbstc" in name_l:
        op = "NBSTC"
        btype = "Government - NON AC"
    elif "wbtc" in name_l or "cstc" in name_l or "ctc" in name_l:
        op = "WBTC"
        btype = "Government - NON AC"

    return {
        "id": f"wbbustimecom-{bid}",
        "bus_name": bus_name,
        "operator": op,
        "bus_type": btype,
        "origin": origin,
        "destination": destination,
        "departure_time": dep_time,
        "arrival_time": arr_time,
        "route": f"{origin} - {destination}",
        "stoppages": stops,
        "total_stoppages": len(stops),
        "source": "wbbustime.com",
        "detail_url": f"https://wbbustime.com/bus/{bid}/view",
    }


def fetch_bus(bid):
    url = f"https://wbbustime.com/bus/{bid}/view"
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=6, context=get_ctx()) as resp:
            if resp.status == 200:
                html = resp.read().decode("utf-8", errors="ignore")
                return parse_page(html, bid)
    except Exception:
        pass
    return None


def main():
    start_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    end_id = int(sys.argv[2]) if len(sys.argv) > 2 else 600

    print(f"Scraping wbbustime.com IDs {start_id} to {end_id} with 8 workers...")
    buses = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_id = {executor.submit(fetch_bus, bid): bid for bid in range(start_id, end_id + 1)}
        done = 0
        for future in concurrent.futures.as_completed(future_to_id):
            bid = future_to_id[future]
            done += 1
            res = future.result()
            if res:
                buses.append(res)
                if len(buses) % 10 == 0:
                    print(f"  [Progress] Scraped {len(buses)} buses (checked {done}/{len(future_to_id)})", flush=True)

    print(f"\nCompleted! Total valid buses scraped: {len(buses)}")
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_RAW, "w", encoding="utf-8") as f:
        json.dump(buses, f, indent=2, ensure_ascii=False)
    print(f"Saved raw scraped buses to {OUT_RAW}")


if __name__ == "__main__":
    main()
