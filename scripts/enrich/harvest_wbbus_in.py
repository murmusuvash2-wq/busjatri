#!/usr/bin/env python3
"""harvest_wbbus_in.py - Robust, polite scraper for wbbus.in
Extracts authentic West Bengal buses with stop-by-stop Up & Down timelines,
operator information, and depot details.
"""

import concurrent.futures
import html
import json
import os
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_RAW = ROOT / "data-raw" / "wbbus_in_scraped.json"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
BAD_TIMES = {"", "_", "_ _", "_ _ : _ _", "—", "--", "N/A", "00.00am", "00.00pm", "0:00", "00:00", "null", "None"}


def get_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def clean(s):
    return re.sub(r"\s+", " ", str(s or "").strip())


def parse_page(raw_html, url):
    # Parse table metadata
    table_m = re.search(r"<tbody>(.*?)</tbody>", raw_html, re.S)
    meta = {}
    if table_m:
        for tr in re.findall(r"<tr>(.*?)</tr>", table_m.group(1), re.S):
            tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            if len(tds) >= 2:
                k = clean(re.sub(r"<[^>]+>", "", tds[0]).replace(":", "").lower())
                v = clean(html.unescape(re.sub(r"<[^>]+>", "", tds[1])))
                meta[k] = v

    bus_name = meta.get("bus name") or ""
    if not bus_name:
        title_m = re.search(r"<title>(.*?)</title>", raw_html)
        if title_m:
            bus_name = title_m.group(1).split("-")[0].strip()

    reg_no = meta.get("registration number") or ""
    bus_type = meta.get("bus type") or "Private - NON AC"
    contact = meta.get("contact number") or meta.get("alternate number") or ""
    depot_origin = meta.get("depot name") or ""
    dest_final = meta.get("destination") or ""

    # Parse timeline rows
    blocks = raw_html.split('row sud text-center border-bottom py-2">')[1:]
    up_stops = []
    down_stops = []

    for b in blocks:
        cols = re.findall(r"<div class=[\"\x27][^\"\x27]*col-[^\"\x27]*[\"\x27]>(.*?)</div>", b[:1200], re.S)
        if len(cols) >= 4:
            s_num = clean(re.sub(r"<[^>]+>", "", cols[0]))
            up_t = clean(re.sub(r"<[^>]+>", "", cols[1]))
            s_name = clean(html.unescape(re.sub(r"<[^>]+>", "", cols[2])))
            down_t = clean(re.sub(r"<[^>]+>", "", cols[3]))

            if up_t in BAD_TIMES:
                up_t = ""
            if down_t in BAD_TIMES:
                down_t = ""

            if s_name:
                num = int(s_num) if s_num.isdigit() else len(up_stops) + 1
                up_stops.append({"no": num, "name": s_name, "up_time": up_t, "down_time": down_t})
                down_stops.append({"no": num, "name": s_name, "up_time": up_t, "down_time": down_t})

    if not up_stops:
        return []

    # Infer operator
    name_upper = (bus_name + " " + (meta.get("agency name") or "")).upper()
    op = "Private"
    if "SBSTC" in name_upper:
        op = "SBSTC"
        bus_type = "Government - SBSTC"
    elif "NBSTC" in name_upper:
        op = "NBSTC"
        bus_type = "Government - NBSTC"
    elif "WBTC" in name_upper or "CSTC" in name_upper or "CTC" in name_upper:
        op = "WBTC"
        bus_type = "Government - WBTC"

    results = []

    # Build UP journey bus
    origin = depot_origin or up_stops[0]["name"]
    destination = dest_final or up_stops[-1]["name"]
    up_dep_time = ""
    up_arr_time = ""
    for s in up_stops:
        if s["up_time"]:
            if not up_dep_time:
                up_dep_time = s["up_time"]
            up_arr_time = s["up_time"]

    # Match ID slug from URL
    url_slug_m = re.search(r"/bus/([a-zA-Z0-9_\-]+)", url)
    url_id_part = url_slug_m.group(1) if url_slug_m else f"{abs(hash(url))}"

    if up_dep_time:
        results.append({
            "id": f"wbbus-{url_id_part}",
            "bus_name": bus_name or "Private Bus",
            "reg_no": reg_no,
            "operator": op,
            "bus_type": bus_type,
            "origin": origin,
            "destination": destination,
            "departure_time": up_dep_time,
            "arrival_time": up_arr_time if up_arr_time != up_dep_time else "",
            "contact_number": contact,
            "depot_name": depot_origin,
            "route": f"{origin} - {destination}",
            "stoppages": up_stops,
            "total_stoppages": len(up_stops),
            "source": "wbbus.in",
            "detail_url": url,
            "direction": "UP",
        })

    # Build DOWN journey bus (reverse route)
    down_reversed = list(reversed(down_stops))
    down_dep_time = ""
    down_arr_time = ""
    for s in down_reversed:
        if s["down_time"]:
            if not down_dep_time:
                down_dep_time = s["down_time"]
            down_arr_time = s["down_time"]

    if down_dep_time and len(down_reversed) >= 2:
        down_stops_formatted = []
        for idx, s in enumerate(down_reversed):
            down_stops_formatted.append({
                "no": idx + 1,
                "name": s["name"],
                "up_time": s["down_time"],
                "down_time": s["up_time"],
            })
        results.append({
            "id": f"wbbus-{url_id_part}-dn",
            "bus_name": bus_name or "Private Bus",
            "reg_no": reg_no,
            "operator": op,
            "bus_type": bus_type,
            "origin": destination,
            "destination": origin,
            "departure_time": down_dep_time,
            "arrival_time": down_arr_time if down_arr_time != down_dep_time else "",
            "contact_number": contact,
            "depot_name": depot_origin,
            "route": f"{destination} - {origin}",
            "stoppages": down_stops_formatted,
            "total_stoppages": len(down_stops_formatted),
            "source": "wbbus.in",
            "detail_url": url,
            "direction": "DOWN",
        })

    return results


def fetch_with_retry(url, retries=3):
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=10, context=get_ctx()) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3 + attempt * 2)
            else:
                time.sleep(1)
        except Exception:
            time.sleep(1)
    return None


def fetch_and_parse(url):
    html_txt = fetch_with_retry(url)
    if html_txt:
        return parse_page(html_txt, url)
    return []


def get_all_bus_urls(max_pages=10):
    print(f"Collecting bus URLs from wbbus.in/allbus (pages 1 to {max_pages})...")
    urls = []

    for p in range(1, max_pages + 1):
        page_url = f"https://wbbus.in/allbus?page={p}"
        html_txt = fetch_with_retry(page_url)
        if html_txt:
            links = re.findall(r'href=[\"\x27](https://wbbus\.in/bus/[^\"\x27]+)[\"\x27]', html_txt)
            for l in links:
                if l not in urls:
                    urls.append(l)
        time.sleep(0.4)

    print(f"Collected {len(urls)} bus URLs.")
    return urls


def main():
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    urls = get_all_bus_urls(max_pages=pages)

    # Filter out already existing URLs
    data_path = ROOT / "data" / "busjatri_data.json"
    existing_urls = set()
    if data_path.exists():
        with open(data_path, encoding="utf-8") as f:
            d = json.load(f)
            existing_urls = {b.get("detail_url") for b in d.get("buses", []) if b.get("detail_url")}

    target_urls = [u for u in urls if u not in existing_urls]
    print(f"Targeting {len(target_urls)} new URLs (out of {len(urls)})...")

    # Load existing scraped items if any
    existing_items = []
    if OUT_RAW.exists() and OUT_RAW.stat().st_size > 10:
        try:
            with open(OUT_RAW, encoding="utf-8") as f:
                existing_items = json.load(f)
        except Exception:
            pass

    seen_ids = {b["id"] for b in existing_items}
    buses = list(existing_items)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        future_to_url = {ex.submit(fetch_and_parse, u): u for u in target_urls}
        done = 0
        for f in concurrent.futures.as_completed(future_to_url):
            done += 1
            res = f.result()
            if res:
                for b in res:
                    if b["id"] not in seen_ids:
                        seen_ids.add(b["id"])
                        buses.append(b)
            if done % 15 == 0 or done == len(target_urls):
                print(f"  [Progress] Processed {done}/{len(target_urls)} URLs -> {len(buses)} bus journeys extracted", flush=True)
            time.sleep(0.2)

    print(f"\nCompleted! Total bus journey candidates extracted: {len(buses)}")
    if buses:
        OUT_RAW.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT_RAW, "w", encoding="utf-8") as f:
            json.dump(buses, f, indent=2, ensure_ascii=False)
        print(f"Saved raw buses to {OUT_RAW}")


if __name__ == "__main__":
    main()
