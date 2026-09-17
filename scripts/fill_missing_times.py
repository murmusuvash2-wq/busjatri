#!/usr/bin/env python3
"""
Fill missing departure/arrival times in data/busjatri_data.json.

Phase A (offline, default): derive departure_time / arrival_time from each bus's
own stoppage data (first stop up_time -> departure, last stop down_time -> arrival).

Phase B (--crawl, network): for buses still missing times, crawl public sources
(wbbustime.in route pages) and fill by confident matching.
Always run Phase B as --dry-run first to see the match report.

Usage:
  python3 scripts/fill_missing_times.py                # Phase A only (offline)
  python3 scripts/fill_missing_times.py --write         # apply Phase A to the data file
  python3 scripts/fill_missing_times.py --crawl --dry-run   # report crawl matches only
  python3 scripts/fill_missing_times.py --crawl --write      # apply crawl fills
"""
import json
import re
import sys
import time
import urllib.request

DATA = "data/busjatri_data.json"

BAD = {"", "_", "_ _", "_ _ : _ _", "—", "--", "N/A", "00.00am", "00.00pm", "0:00", "00:00"}
TIME_RE = re.compile(r"^\d{1,2}[:.]\d{2}\s*(AM|PM|am|pm)?$")

def clean(t):
    t = (str(t or "")).strip()
    return "" if t in BAD else t

def valid_time(t):
    return bool(clean(t)) and bool(TIME_RE.match(clean(t)))

def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)

def save(data):
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

# ---------------- Phase A: offline fill from stoppages ----------------

def phase_a(data, write=False):
    filled_dep = filled_arr = 0
    for b in data["buses"]:
        stops = b.get("stoppages") or []
        if not stops:
            continue
        if not clean(b.get("departure_time")):
            t = clean(stops[0].get("up_time")) or clean(stops[0].get("down_time"))
            if valid_time(t):
                b["departure_time"] = t
                filled_dep += 1
        if not clean(b.get("arrival_time")):
            t = clean(stops[-1].get("down_time")) or clean(stops[-1].get("up_time"))
            if valid_time(t):
                b[arrival_placeholder] = t
                filled_arr += 1
    still_missing = sum(1 for b in data["buses"] if not clean(b.get("departure_time")))
    print(f"Phase A: filled departure_time for {filled_dep} buses, arrival_time for {filled_arr} buses")
    print(f"Still missing times after Phase A: {still_missing} / {len(data['buses'])}")
    if write:
        data.setdefault("meta", {})["last_time_fill"] = "phase-a"
        save(data)
        print("WROTE", DATA)
    return data

# ---------------- Phase B: crawl helpers ----------------

def fetch(url, tries=2, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "BusJatriDataBot/1.0 (community timetable project)"})
    for _ in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print("  fetch error:", url, e)
            time.sleep(2)
    return ""

def find_candidate_urls_on_wbbustime(missing_buses):
    """Discover wbbustime.in route pages and index them by (from, to)."""
    html = fetch("https://wbbustime.in/all-routes/")
    links = re.findall(r'href="(https://wbbustime\.in/bus-timetable/[^"]+)"[^>]*>([^<]+)', html)
    idx = {}
    for url, text in links:
        m = re.search(r"([A-Za-z .&()'-]+?)\s*(?:→| to )\s*([A-Za-z .&()'-]+?)(?:\s+Bus\b|$)", text)
        if m:
            idx[(m.group(1).strip().lower(), m.group(2).strip().lower())] = url
    print(f"  wbbustime index: {len(idx)} route pages")
    return idx

def parse_wbbustime_stops(page_html):
    """Return list of (stop_name, up_time, down_time) from a route page's table."""
    rows = re.findall(r"<tr[^>]*>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]*)</td>\s*<td[^>]*>([^<]*)</td>", page_html)
    out = []
    for name, up, down in rows:
        out.append((name.strip(), clean(up), clean(down)))
    return out

def phase_b(data, write=False, dry_run=False):
    missing = [b for b in data["buses"] if not clean(b.get("departure_time"))]
    print(f"Phase B: {len(missing)} buses missing times; discovering sources...")
    idx = find_candidate_urls_on_wbbustime(missing)

    matched = tried = 0
    for b in missing:
        key = (b["origin"].strip().lower(), b["destination"].strip().lower())
        url = idx.get(key)
        if not url:
            continue
        tried += 1
        page = fetch(url)
        stops = parse_wbbustime_stops(page)
        if not stops or not any(t for _, u, d in stops for t in (u, d)):
            continue
        first_up = next((u or d for _, u, d in stops if (u or d)), "")
        if valid_time(first_up):
            matched += 1
            if not dry_run:
                b["departure_time"] = first_up
                b["time_source"] = "wbbustime.in"
        time.sleep(1.0)  # be polite
        if tried >= 60:
            print("  (capped at 60 pages per run to stay polite - rerun later for more)")
            break

    print(f"Phase B (wbbustime): tried {tried} route pages, matched {matched} buses")
    if matched and write and not dry_run:
        save(data)
        print("WROTE", DATA)
    return data

def main():
    args = set(sys.argv[1:])
    data = load()
    data = phase_a(data, write=("--write" in args))
    if "--crawl" in args:
        data = phase_b(data, write=("--write" in args), dry_run=("--dry-run" in args))

if __name__ == "__main__":
    main()
