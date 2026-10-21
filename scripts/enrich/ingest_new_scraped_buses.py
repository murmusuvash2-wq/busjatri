#!/usr/bin/env python3
"""Ingest newly scraped buses from bussathi.in (IDs 1300-1353) and
wbbustime.in (new route URLs) into data/busjatri_data.json.

Ensures:
1. Strict schema compliance with existing busjatri_data.json format.
2. Complete deduplication by registration number, route, and URL.
3. Clean string sanitization and proper bus_name / reg_no parsing.
4. Auto-estimation of missing arrival times.
5. Index and client dataset rebuild.

Usage:
  python3 scripts/enrich/ingest_new_scraped_buses.py [--write]
"""

import html
import json
import math
import os
import re
import ssl
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "busjatri_data.json"
COORDS_PATH = ROOT / "data" / "stop_coords.json"

TIME_RE = re.compile(r"^(\d{1,2})[:.](\d{2})\s*(AM|PM|Noon|Midnight)?$", re.I)
BAD_TIMES = {"", "_", "_ _", "_ _ : _ _", "—", "--", "N/A", "00.00am", "00.00pm", "0:00", "00:00", "null", "None"}

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BusJatriIngest/1.0"}


def get_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def safe_fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=get_ctx()) as r:
        return r.read().decode("utf-8", "replace")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-") or "x"


def clean(s):
    return str(s or "").strip()


def parse_mins(t):
    t = clean(t).lstrip("~").strip()
    if not t or t in BAD_TIMES:
        return None
    m = TIME_RE.match(t)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").upper()
    if ap == "PM" and h != 12:
        h += 12
    elif ap == "AM" and h == 12:
        h = 0
    elif ap == "NOON":
        h = 12
    elif ap == "MIDNIGHT":
        h = 0
    return (h % 24) * 60 + mi


def fmt_time(m):
    m = m % 1440
    h, mi = divmod(m, 60)
    ap = "AM" if h < 12 else "PM"
    h = h % 12 or 12
    return f"{h}:{mi:02d} {ap}"


# ---------------- Scrape Bussathi (1300 - 1353) ----------------
def scrape_bussathi_range(start_id=1300, end_id=1354):
    sys.path.insert(0, str(ROOT / "scripts"))
    import scrape_bussathi

    buses = []
    print(f"Scraping bussathi.in from {start_id} to {end_id - 1} ...")
    for bid in range(start_id, end_id):
        url = f"https://bussathi.in/bus/{bid}"
        try:
            h = safe_fetch(url)
            txt = scrape_bussathi.text_of(h)
            b = scrape_bussathi.parse(txt, url)
            if b and b.get("origin") and b.get("destination") and b.get("departure_time"):
                # Clean up bus name and registration
                raw_name = b.get("bus_name") or ""
                m_reg = re.search(r"\b(WB\s*\d{2}[A-Z\d\s]{2,10})\b", raw_name, re.I)
                reg = b.get("reg_no") or (m_reg.group(1).replace(" ", "") if m_reg else "")
                clean_name = re.sub(r"\bRegistration\s+.*$", "", raw_name, flags=re.I).strip()
                clean_name = re.sub(r"\s+", " ", clean_name).strip() or "Private Bus"

                b["bus_name"] = clean_name
                b["reg_no"] = reg
                b["id"] = f"bussathi-{slug(clean_name)}-{bid}"
                b["bussathi_id"] = bid
                buses.append(b)
        except Exception:
            pass
        time.sleep(0.15)
    print(f"  Bussathi: fetched {len(buses)} valid buses.")
    return buses


# ---------------- Scrape WBBusTime (New URLs) ----------------
def scrape_wbbustime_new(existing_urls):
    sys.path.insert(0, str(ROOT / "scripts" / "enrich"))
    import scrape_wbbustime

    def fetch_sitemap(url):
        try:
            h = safe_fetch(url, timeout=20)
            return re.findall(r"<loc>(.*?)</loc>", h)
        except Exception:
            return []

    print("Fetching wbbustime sitemaps ...")
    bus_urls = set(fetch_sitemap("https://wbbustime.in/sitemap-bus.xml") + fetch_sitemap("https://wbbustime.in/sitemap-popular.xml"))
    new_urls = [u for u in bus_urls if u not in existing_urls and u.rstrip("/") not in existing_urls and u + "/" not in existing_urls]
    print(f"  WBBusTime: found {len(new_urls)} new URLs.")

    buses = []
    for u in new_urls:
        try:
            content = safe_fetch(u)
            b = scrape_wbbustime.parse_bus_page(content, u)
            if b and b.get("origin") and b.get("destination"):
                # Clean up bus name
                bname = re.sub(r"\s+", " ", b.get("bus_name") or "").strip()
                bname = re.sub(r"\(ROUTE.*?\)", "", bname, flags=re.I).strip() or "Private Bus"
                b["bus_name"] = bname
                b["id"] = f"wbbustime-{slug(bname)}-{slug(b['origin'])}-{slug(b['destination'])}"
                buses.append(b)
        except Exception:
            pass
        time.sleep(0.15)
    print(f"  WBBusTime: parsed {len(buses)} valid buses.")
    return buses


def main():
    write = "--write" in sys.argv

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    existing_urls = {b.get("detail_url") for b in data["buses"] if b.get("detail_url")}
    existing_regs = {clean(b.get("reg_no")).replace(" ", "").upper() for b in data["buses"] if clean(b.get("reg_no"))}
    existing_keys = {
        (clean(b.get("origin")).lower(), clean(b.get("destination")).lower(), clean(b.get("bus_name")).lower(), clean(b.get("departure_time")).lower())
        for b in data["buses"]
    }
    existing_ids = {b.get("id") for b in data["buses"]}

    # 1. Fetch new buses
    bussathi_buses = scrape_bussathi_range(1300, 1354)
    wbbustime_buses = scrape_wbbustime_new(existing_urls)

    all_candidates = bussathi_buses + wbbustime_buses
    print(f"\nTotal scraped candidates: {len(all_candidates)}")

    # 2. Deduplicate and normalize
    added_buses = []
    skipped_dupe = 0

    for c in all_candidates:
        orig = clean(c.get("origin"))
        dest = clean(c.get("destination"))
        bname = clean(c.get("bus_name"))
        dep = clean(c.get("departure_time"))
        arr = clean(c.get("arrival_time"))
        reg = clean(c.get("reg_no")).replace(" ", "").upper()
        url = clean(c.get("detail_url"))

        # Dedup checks
        if url and url in existing_urls:
            skipped_dupe += 1
            continue
        if reg and reg in existing_regs:
            skipped_dupe += 1
            continue
        key = (orig.lower(), dest.lower(), bname.lower(), dep.lower())
        if key in existing_keys:
            skipped_dupe += 1
            continue

        # ID collision resolution
        bid = c.get("id") or f"bus-{slug(bname)}-{slug(orig)}-{slug(dest)}"
        base_id = bid
        ctr = 1
        while bid in existing_ids:
            bid = f"{base_id}-{ctr}"
            ctr += 1

        existing_ids.add(bid)
        if reg:
            existing_regs.add(reg)
        if url:
            existing_urls.add(url)
        existing_keys.add(key)

        # Standard BusJatri bus entry schema
        entry = {
            "id": bid,
            "bus_name": bname or "Private Bus",
            "reg_no": reg,
            "operator": clean(c.get("operator")) or "—",
            "bus_type": clean(c.get("bus_type")) or "Private - NON AC",
            "origin": orig,
            "destination": dest,
            "departure_time": dep,
            "arrival_time": arr if arr not in BAD_TIMES else "",
            "contact_number": clean(c.get("contact_number")) or "Not Available !",
            "depot_name": clean(c.get("depot_name")) or "",
            "route": f"{orig} - {dest}",
            "stoppages": c.get("stoppages") or [],
            "source": c.get("source") or "wbbus.in",
            "total_stoppages": c.get("total_stoppages") or len(c.get("stoppages") or []),
            "detail_url": url,
        }

        # If arrival is missing, estimate it
        if not entry["arrival_time"] and entry["departure_time"]:
            d_min = parse_mins(entry["departure_time"])
            if d_min is not None:
                stops_cnt = len(entry["stoppages"])
                dur = min(480, max(45, stops_cnt * 16)) if stops_cnt > 2 else 120
                dur = int(round(dur / 5.0) * 5)
                arr_min = (d_min + dur) % 1440
                entry["arrival_time"] = fmt_time(arr_min)
                entry["is_estimated_arrival"] = True

        added_buses.append(entry)

    print(f"Skipped duplicates: {skipped_dupe}")
    print(f"New unique buses to add: {len(added_buses)}")

    if not added_buses:
        print("No new buses to add.")
        return

    # 3. Merge into dataset
    before_count = len(data["buses"])
    data["buses"].extend(added_buses)
    after_count = len(data["buses"])

    # 4. Rebuild route index & stop index cleanly
    routes_map = defaultdict(list)
    stops_map = defaultdict(list)
    for b in data["buses"]:
        o = clean(b.get("origin"))
        d = clean(b.get("destination"))
        if o and d and o != "—" and d != "—":
            routes_map[f"{slug(o)}-to-{slug(d)}"].append(b["id"])
        seen_stops = set()
        for s in (b.get("stoppages") or []):
            sn = s.get("name") if isinstance(s, dict) else str(s)
            sn = clean(sn)
            if sn and sn not in seen_stops:
                seen_stops.add(sn)
                stops_map[sn].append(b["id"])

    routes_out = {}
    for b in data["buses"]:
        o = clean(b.get("origin"))
        d = clean(b.get("destination"))
        k = f"{slug(o)}-to-{slug(d)}"
        if k in routes_map and k not in routes_out:
            routes_out[k] = {"from": o, "to": d, "bus_ids": list(dict.fromkeys(routes_map[k]))}

    stops_out = {sn: {"name": sn, "bus_ids": list(dict.fromkeys(ids))} for sn, ids in stops_map.items()}

    data["routes"] = routes_out
    data["stops"] = stops_out
    data["meta"].update({
        "total_buses": after_count,
        "total_routes": len(routes_out),
        "total_stops": len(stops_out),
        "last_updated": str(date.today()),
    })

    print(f"Dataset stats: {before_count} -> {after_count} buses (+{len(added_buses)})")
    print(f"Total routes: {len(routes_out)}, Total stops: {len(stops_out)}")

    if write:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("WROTE", DATA_PATH)


if __name__ == "__main__":
    main()
