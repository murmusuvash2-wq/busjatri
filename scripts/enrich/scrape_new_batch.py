#!/usr/bin/env python3
"""Scrape new bus candidates from bussathi.in (1300-1354) and wbbustime.in sitemaps,
saving the results to data-raw/new_buses_scraped.json.
"""

import json
import os
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_OUT = ROOT / "data-raw" / "new_buses_scraped.json"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BusJatriScraper/1.0"}


def get_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def safe_fetch(url, timeout=7):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=get_ctx()) as r:
        return r.read().decode("utf-8", "replace")


def scrape_bussathi():
    sys.path.insert(0, str(ROOT / "scripts"))
    import scrape_bussathi

    buses = []
    print("--- Scraping bussathi.in (1300 - 1353) ---", flush=True)
    for bid in range(1300, 1354):
        url = f"https://bussathi.in/bus/{bid}"
        try:
            h = safe_fetch(url)
            txt = scrape_bussathi.text_of(h)
            b = scrape_bussathi.parse(txt, url)
            if b and b.get("origin") and b.get("destination") and b.get("departure_time"):
                raw_name = b.get("bus_name") or ""
                m_reg = re.search(r"\b(WB\s*\d{2}[A-Z\d\s]{2,10})\b", raw_name, re.I)
                reg = b.get("reg_no") or (m_reg.group(1).replace(" ", "") if m_reg else "")
                clean_name = re.sub(r"\bRegistration\s+.*$", "", raw_name, flags=re.I).strip()
                clean_name = re.sub(r"\s+", " ", clean_name).strip() or "Private Bus"

                b["bus_name"] = clean_name
                b["reg_no"] = reg
                b["bussathi_id"] = bid
                buses.append(b)
                print(f"  [bussathi {bid}] {clean_name} | {b['origin']} -> {b['destination']} ({b['departure_time']})", flush=True)
        except Exception:
            pass
        time.sleep(0.1)
    return buses


def scrape_wbbustime():
    sys.path.insert(0, str(ROOT / "scripts" / "enrich"))
    import scrape_wbbustime

    def fetch_sitemap(url):
        try:
            h = safe_fetch(url, timeout=12)
            return re.findall(r"<loc>(.*?)</loc>", h)
        except Exception as e:
            print(f"  sitemap error {url}: {e}", flush=True)
            return []

    print("--- Scraping wbbustime.in ---", flush=True)
    bus_urls = set(fetch_sitemap("https://wbbustime.in/sitemap-bus.xml") + fetch_sitemap("https://wbbustime.in/sitemap-popular.xml"))
    print(f"  Found {len(bus_urls)} sitemap URLs", flush=True)

    buses = []
    for u in bus_urls:
        try:
            content = safe_fetch(u, timeout=10)
            b = scrape_wbbustime.parse_bus_page(content, u)
            if b and b.get("origin") and b.get("destination"):
                bname = re.sub(r"\s+", " ", b.get("bus_name") or "").strip()
                bname = re.sub(r"\(ROUTE.*?\)", "", bname, flags=re.I).strip() or "Private Bus"
                b["bus_name"] = bname
                buses.append(b)
                print(f"  [wbbustime] {bname} | {b['origin']} -> {b['destination']} (stops: {len(b.get('stoppages') or [])})", flush=True)
        except Exception:
            pass
        time.sleep(0.1)
    return buses


def main():
    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    all_buses = []

    b1 = scrape_bussathi()
    all_buses.extend(b1)

    b2 = scrape_wbbustime()
    all_buses.extend(b2)

    with open(RAW_OUT, "w", encoding="utf-8") as f:
        json.dump(all_buses, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(all_buses)} raw buses to {RAW_OUT}", flush=True)


if __name__ == "__main__":
    main()
