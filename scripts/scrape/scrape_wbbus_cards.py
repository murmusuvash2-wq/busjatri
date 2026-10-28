#!/usr/bin/env python3
"""
Scrape all bus cards from wbbus.in/allbus (pages 1 to 79) politely.
Each card provides bus_name, reg_no, origin, departure_time, destination, arrival_time, detail_url.
Saves to data-raw/wbbus_cards_all.json.
"""
import html as H
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_FILE = ROOT / "data-raw" / "wbbus_cards_all.json"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def clean(s):
    return (s or "").strip()


def fetch_url(url):
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                return resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = int(e.headers.get("Retry-After", 10)) + 2
                print(f"[Rate-limited 429] Sleeping {wait_time}s...", flush=True)
                time.sleep(wait_time)
            elif e.code == 404:
                return None
            else:
                time.sleep(2.0)
        except Exception:
            time.sleep(2.0)
    return None


def parse_page_cards(html):
    cards = []
    # Pattern to match the bus link and card container
    # <a href="https://wbbus.in/bus/..."><div class="card flex-row busc">...
    items = re.findall(r'<a[^>]*href=[\"\'](https://wbbus\.in/bus/[^\"\']+)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
    for url, inner in items:
        m_name = re.search(r'<h4[^>]*class=\"[^\"]*card_busname[^\"]*\"[^>]*>(.*?)</h4>', inner, re.I | re.DOTALL)
        bus_name = clean(H.unescape(m_name.group(1))) if m_name else ""

        m_reg = re.search(r'Reg No\s*:\s*([A-Za-z0-9]+)', inner, re.I)
        reg_no = clean(m_reg.group(1)).upper() if m_reg else ""

        m_dip = re.search(r'<div class=\"dip\"[^>]*>\s*<span[^>]*>(.*?)</span>\s*<span[^>]*>(.*?)</span>', inner, re.DOTALL)
        origin = clean(H.unescape(m_dip.group(1))) if m_dip else ""
        dep_time = clean(H.unescape(m_dip.group(2))) if m_dip else ""

        m_dest = re.search(r'<div class=\"desti[^\"]*\"[^>]*>\s*<span[^>]*>(.*?)</span>\s*<span[^>]*>(.*?)</span>', inner, re.DOTALL)
        destination = clean(H.unescape(m_dest.group(1))) if m_dest else ""
        arr_time = clean(H.unescape(m_dest.group(2))) if m_dest else ""

        # Clean any _ _ : _ _
        if "_" in dep_time or "-" in dep_time or "—" in dep_time: dep_time = ""
        if "_" in arr_time or "-" in arr_time or "—" in arr_time: arr_time = ""

        if bus_name and (origin or destination):
            is_sbstc = "SBSTC" in bus_name.upper()
            is_nbstc = "NBSTC" in bus_name.upper()
            is_wbtc = "WBTC" in bus_name.upper()
            op = "SBSTC" if is_sbstc else ("NBSTC" if is_nbstc else ("WBTC" if is_wbtc else "—"))
            b_type = "Government - SBSTC" if is_sbstc else ("Government - NBSTC" if is_nbstc else ("Government - WBTC" if is_wbtc else "Private - NON AC"))

            cards.append({
                "bus_name": bus_name,
                "reg_no": reg_no,
                "origin": origin,
                "destination": destination,
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "operator": op,
                "bus_type": b_type,
                "route": f"{origin} - {destination}",
                "detail_url": url,
                "source": "wbbus.in"
            })
    return cards


def main():
    print("Scraping wbbus.in/allbus pages 1 to 79 politely...")
    all_buses = []
    seen_urls = set()

    for p in range(1, 80):
        url = f"https://wbbus.in/allbus?page={p}"
        html = fetch_url(url)
        if html:
            cards = parse_page_cards(html)
            new_on_page = 0
            for c in cards:
                if c["detail_url"] not in seen_urls:
                    seen_urls.add(c["detail_url"])
                    all_buses.append(c)
                    new_on_page += 1
            if p % 10 == 0 or p == 79:
                print(f"[Page {p:2d}/79] Total buses collected: {len(all_buses)} (this page +{new_on_page})", flush=True)
        else:
            print(f"[Page {p:2d}/79] Failed to fetch", flush=True)
        time.sleep(1.05)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_buses, f, ensure_ascii=False, indent=2)

    print(f"\nDONE! Saved {len(all_buses)} bus cards to {OUT_FILE}")
    if all_buses:
        print("Sample 1:", json.dumps(all_buses[0], ensure_ascii=False))


if __name__ == "__main__":
    main()
