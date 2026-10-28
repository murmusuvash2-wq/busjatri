#!/usr/bin/env python3
"""
Crawl wbbus.in/allbus pages 1..79, collect bus URLs, filter against existing
BusJatri buses, and fetch complete timetables + stoppages concurrently.
Saves results into data-raw/wbbus_full_scraped.json.
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
OUT_FILE = ROOT / "data-raw" / "wbbus_full_scraped.json"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def clean(s):
    return (s or "").strip()


def fetch_page(url, retries=2):
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8", "replace")
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(0.8)
    return None


def parse_bus_page(html, url):
    if not html:
        return None

    b = {}
    # Extract metadata from table
    m_name = re.search(r"Bus Name\s*:\s*</td>\s*<td>\s*<span>(.*?)</span>", html, re.I)
    b["bus_name"] = clean(H.unescape(m_name.group(1))) if m_name else ""

    m_reg = re.search(r"Registration Number\s*:\s*</td>\s*<td>\s*<span[^>]*>(.*?)</span>", html, re.I)
    b["reg_no"] = clean(H.unescape(m_reg.group(1))).upper() if m_reg else ""

    m_type = re.search(r"Bus Type\s*:\s*</td>\s*<td>\s*<span>(.*?)</span>", html, re.I)
    b["bus_type"] = clean(H.unescape(m_type.group(1))) if m_type else "Private - NON AC"

    m_agency = re.search(r"Agency Name\s*:\s*</td>\s*<td>\s*<span>(.*?)</span>", html, re.I)
    agency = clean(H.unescape(m_agency.group(1))) if m_agency else ""

    m_contact = re.search(r"Contact Number\s*:\s*</td>\s*<td>.*?href=[\"']tel:([0-9 +()-]+)[\"']", html, re.I | re.DOTALL)
    b["contact_number"] = clean(m_contact.group(1)) if m_contact else "Not Available !"

    m_depot = re.search(r"Depot Name\s*:\s*</td>\s*<td>\s*<span>(.*?)</span>", html, re.I)
    b["depot_name"] = clean(H.unescape(m_depot.group(1))) if m_depot else ""

    # Determine operator
    if agency:
        b["operator"] = agency
    elif "SBSTC" in b["bus_name"].upper():
        b["operator"] = "SBSTC"
    elif "NBSTC" in b["bus_name"].upper():
        b["operator"] = "NBSTC"
    elif "WBTC" in b["bus_name"].upper() or "CSTC" in b["bus_name"].upper():
        b["operator"] = "WBTC"
    else:
        b["operator"] = "—"

    # Extract Stoppages
    stoppages = []
    # Pattern for row sud:
    # col 1: number
    # col 2: up time
    # col 3: stoppage name
    # col 4: down time
    row_pattern = re.compile(r'<div class=\"row sud[^\"]*\"[^>]*>(.*?)</div>\s*(?=<div class=\"row sud|\s*</div>\s*</div>)', re.DOTALL)
    for row_html in re.finditer(r'<div class=\"row sud[^\"]*\"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL):
        cols = re.findall(r'<div class=\"col-[^\"]*\"[^>]*>(.*?)</div>', row_html.group(1), re.DOTALL)
        if len(cols) >= 4:
            # col 0: num
            num_clean = re.sub(r'<[^>]+>', '', cols[0]).strip()
            num = int(num_clean) if num_clean.isdigit() else len(stoppages) + 1
            # col 1: up time
            up_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|Noon))', cols[1], re.I)
            up_time = up_match.group(1).strip() if up_match else ""
            # col 2: name
            name_clean = clean(H.unescape(re.sub(r'<[^>]+>', '', cols[2])))
            # col 3: down time
            down_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|Noon))', cols[3], re.I)
            down_time = down_match.group(1).strip() if down_match else ""

            if name_clean and name_clean != "#" and "Stoppage" not in name_clean:
                stoppages.append({"no": num, "name": name_clean, "up_time": up_time, "down_time": down_time})

    b["stoppages"] = stoppages
    b["total_stoppages"] = len(stoppages)
    b["detail_url"] = url
    b["source"] = "wbbus.in"

    if stoppages:
        b["origin"] = stoppages[0]["name"]
        b["destination"] = stoppages[-1]["name"]
        b["departure_time"] = stoppages[0]["up_time"]
        b["arrival_time"] = stoppages[-1]["up_time"]
    else:
        # Fallback from URL slug: /bus/<name>-<reg>-<orig>-<dest>-<id>
        parts = url.rstrip("/").split("/")[-1].split("-")
        b["origin"] = ""
        b["destination"] = ""
        b["departure_time"] = ""
        b["arrival_time"] = ""

    b["route"] = f"{b['origin']} - {b['destination']}" if b["origin"] and b["destination"] else ""

    # Estimate arrival if missing
    if b["departure_time"] and not b["arrival_time"] and len(stoppages) > 1:
        m_t = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', b["departure_time"], re.I)
        if m_t:
            h, mn, mer = int(m_t.group(1)), int(m_t.group(2)), m_t.group(3).upper()
            if mer == "PM" and h != 12: h += 12
            if mer == "AM" and h == 12: h = 0
            dur = max(40, len(stoppages) * 7)
            tot = (h * 60 + mn + dur) % (24 * 60)
            ah, am = tot // 60, tot % 60
            amer = "AM" if ah < 12 else "PM"
            ah12 = 12 if ah in (0, 12) else ah % 12
            b["arrival_time"] = f"{ah12}:{am:02d} {amer}"

    return b


def main():
    print("Step 1: Collecting all bus URLs across 79 pages of wbbus.in...")
    page_urls = [f"https://wbbus.in/allbus?page={p}" for p in range(1, 80)]
    bus_links = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_page = {executor.submit(fetch_page, p): p for p in page_urls}
        for future in concurrent.futures.as_completed(future_to_page):
            html = future.result()
            if html:
                links = re.findall(r'href=[\"\'](https://wbbus\.in/bus/[^\"\']+)[\"\']', html)
                bus_links.update(links)

    print(f"Total bus URLs found on wbbus.in: {len(bus_links)}")

    # Load existing BusJatri database to filter out duplicates
    with open(DATA_FILE, encoding="utf-8") as f:
        existing_data = json.load(f)

    existing_urls = set()
    existing_regs = set()
    for b in existing_data.get("buses", []):
        url = (b.get("detail_url") or "").strip()
        if url: existing_urls.add(url)
        reg = (b.get("reg_no") or "").strip().upper()
        if reg: existing_regs.add(reg)

    print(f"Existing detail URLs in BusJatri: {len(existing_urls)}")
    to_scrape = [u for u in bus_links if u not in existing_urls]
    print(f"New bus URLs to fetch details for: {len(to_scrape)}")

    results = []
    scraped = 0

    print("Step 2: Concurrently fetching bus details with 8 workers...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url = {executor.submit(fetch_page, url): url for url in to_scrape}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_url), 1):
            url = future_to_url[future]
            try:
                html = future.result()
                if html:
                    bus = parse_bus_page(html, url)
                    if bus and bus.get("bus_name") and bus.get("origin"):
                        results.append(bus)
                        scraped += 1
            except Exception:
                pass

            if i % 50 == 0 or i == len(to_scrape):
                print(f"[{i}/{len(to_scrape)}] Scraped: {scraped} buses", flush=True)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDONE! Successfully saved {len(results)} new buses to {OUT_FILE}")
    if results:
        print("Sample 1:", json.dumps(results[0], ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
