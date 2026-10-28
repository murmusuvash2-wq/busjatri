#!/usr/bin/env python3
"""
Scrape missing bus pages from bussathi.in (IDs 1 to 1353) into data-raw/bussathi_new_batch.json.
Uses modern JSON-LD and HTML table parsing with concurrent workers.
"""
import concurrent.futures
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
DATA_FILE = ROOT / "data" / "busjatri_data.json"
OUT_FILE = ROOT / "data-raw" / "bussathi_new_batch.json"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def parse_modern(html, url, bus_id):
    # 1. Try JSON-LD first
    trip = None
    for s in re.findall(r'<script type=\"application/ld\+json\">(.*?)</script>', html, re.DOTALL):
        try:
            d = json.loads(s)
            if d.get('@type') == 'BusTrip':
                trip = d
                break
        except Exception:
            pass

    if not trip:
        return None

    b = {}
    b['bus_name'] = trip.get('name', '').strip()
    b['reg_no'] = trip.get('identifier', '').strip()
    b['origin'] = trip.get('departureBusStop', {}).get('name', '').strip()
    b['destination'] = trip.get('arrivalBusStop', {}).get('name', '').strip()
    
    dep = trip.get('departureTime', '').strip()
    arr = trip.get('arrivalTime', '').strip()
    b['departure_time'] = '' if ('_' in dep or '—' in dep or '-' in dep) else dep
    b['arrival_time'] = '' if ('_' in arr or '—' in arr or '-' in arr) else arr

    # 2. Extract facts from irow
    facts = {}
    for m in re.finditer(r'<div class=\"irow-lbl\">([^<]+)</div>\s*<div class=\"irow-val\"[^>]*>([^<]+)</div>', html):
        lbl, val = m.group(1).strip().lower(), m.group(2).strip()
        facts[lbl] = val
    
    b['bus_type'] = facts.get('type', 'Private - NON AC')
    b['operator'] = facts.get('operator', '—')
    b['depot_name'] = facts.get('depot', b['origin'])

    # Contact number
    m_cont = re.search(r'href=\"tel:([^\"]+)\"', html)
    b['contact_number'] = m_cont.group(1).strip() if m_cont else 'Not Available !'

    # 3. Extract Stoppages from table.tt
    stoppages = []
    m_table = re.search(r'<table class=\"tt\">(.*?)</table>', html, re.DOTALL)
    if m_table:
        tbody = m_table.group(1)
        for tr in re.findall(r'<tr>(.*?)</tr>', tbody, re.DOTALL):
            tds = re.findall(r'<td>(.*?)</td>', tr, re.DOTALL)
            if len(tds) >= 4:
                m_num = re.search(r'<span class=\"tt-num\">(\d+)</span>', tds[0])
                num = int(m_num.group(1)) if m_num else len(stoppages) + 1
                m_name = re.search(r'<span class=\"tt-name\">([^<]+)</span>', tds[1])
                name = m_name.group(1).strip() if m_name else ''
                m_up = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|Noon))', tds[2])
                up_time = m_up.group(1).strip() if m_up else ''
                m_down = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|Noon))', tds[3])
                down_time = m_down.group(1).strip() if m_down else ''
                if name:
                    stoppages.append({'no': num, 'name': name, 'up_time': up_time, 'down_time': down_time})

    b['stoppages'] = stoppages
    b['total_stoppages'] = len(stoppages)
    b['detail_url'] = url
    b['source'] = 'bussathi.in'
    b['bussathi_id'] = bus_id
    b['route'] = f"{b['origin']} - {b['destination']}"

    # Fallback for departure / arrival
    if not b['departure_time'] and stoppages and stoppages[0]['up_time']:
        b['departure_time'] = stoppages[0]['up_time']
    if not b['arrival_time'] and stoppages and stoppages[-1]['up_time']:
        b['arrival_time'] = stoppages[-1]['up_time']

    # Estimate arrival if still missing but departure exists
    if b['departure_time'] and not b['arrival_time'] and stoppages:
        m_t = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', b['departure_time'], re.I)
        if m_t:
            h, mn, mer = int(m_t.group(1)), int(m_t.group(2)), m_t.group(3).upper()
            if mer == 'PM' and h != 12: h += 12
            if mer == 'AM' and h == 12: h = 0
            # Approx 7 mins per stop
            duration_mins = max(45, len(stoppages) * 7)
            tot = (h * 60 + mn + duration_mins) % (24 * 60)
            ah, am = tot // 60, tot % 60
            amer = 'AM' if ah < 12 else 'PM'
            ah12 = 12 if ah in (0, 12) else ah % 12
            b['arrival_time'] = f"{ah12}:{am:02d} {amer}"

    return b


def fetch_bus(bus_id):
    url = f"https://bussathi.in/bus/{bus_id}"
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
                if resp.status == 200:
                    html_content = resp.read().decode("utf-8", "replace")
                    return parse_modern(html_content, url, bus_id)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            if attempt == 1:
                return None
            time.sleep(1.0)
    return None


def main():
    print("Finding missing bussathi IDs...")
    with open(DATA_FILE, encoding="utf-8") as f:
        existing_data = json.load(f)

    existing_ids = set()
    for b in existing_data.get("buses", []):
        m = re.search(r"bussathi-(\d+)", b.get("id", ""))
        if m:
            existing_ids.add(int(m.group(1)))
        m2 = re.search(r"bussathi\.in/bus/(\d+)", b.get("detail_url", ""))
        if m2:
            existing_ids.add(int(m2.group(1)))

    missing_ids = [i for i in range(1, 1354) if i not in existing_ids]
    print(f"Total existing bussathi IDs in BusJatri: {len(existing_ids)}")
    print(f"Total IDs to scrape: {len(missing_ids)}")

    results = []
    scraped_count = 0
    skipped_count = 0

    print("Scraping missing IDs with 8 concurrent workers...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_id = {executor.submit(fetch_bus, bid): bid for bid in missing_ids}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_id), 1):
            bid = future_to_id[future]
            try:
                res = future.result()
                if res:
                    results.append(res)
                    scraped_count += 1
                else:
                    skipped_count += 1
            except Exception:
                skipped_count += 1

            if i % 50 == 0 or i == len(missing_ids):
                print(f"[{i}/{len(missing_ids)}] Live Scraped: {scraped_count} | 404/Empty: {skipped_count}", flush=True)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDONE! Successfully saved {len(results)} new buses to {OUT_FILE}")
    if results:
        print("Sample 1:", json.dumps(results[0], ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
