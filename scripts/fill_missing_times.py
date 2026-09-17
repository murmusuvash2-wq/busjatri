#!/usr/bin/env python3
"""
Fill missing departure/arrival times in data/busjatri_data.json.

Phase A (offline, default): derive departure_time / arrival_time from each bus's
own stoppage data. A bus's own journey is ALWAYS the up_time column of its own
stop list (down_time belongs to the opposite direction), so arrival is read
from the LAST stop's up_time. Arrivals previously derived from the down column
are repaired.

Phase B (--crawl, network): for buses still missing times, crawl public sources
(wbbustime.in route pages) and fill by confident matching. At most ONE bus per
(origin, destination) key is filled per run, so several buses on the same route
never end up with the same time. The reverse direction is matched too (using
the page's down column). Run with --dry-run first to see the match report.

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
    filled_dep = filled_arr = fixed_arr = 0
    for b in data["buses"]:
        stops = b.get("stoppages") or []
        if not stops:
            continue
        if not clean(b.get("departure_time")):
            t = clean(stops[0].get("up_time")) or clean(stops[0].get("down_time"))
            if valid_time(t):
                b["departure_time"] = t
                filled_dep += 1
        arr = clean(b.get("arrival_time"))
        last_up = clean(stops[-1].get("up_time"))
        last_dn = clean(stops[-1].get("down_time"))
        if not arr:
            # the bus's own journey is the up column: arrival = last stop's up_time
            if valid_time(last_up):
                b["arrival_time"] = last_up
                filled_arr += 1
            elif valid_time(last_dn):
                b["arrival_time"] = last_dn
                filled_arr += 1
        else:
            # repair arrivals that were derived from the return-direction column
            if valid_time(last_up) and arr == last_dn and arr != last_up:
                b["arrival_time"] = last_up
                fixed_arr += 1
    still_missing = sum(1 for b in data["buses"] if not clean(b.get("departure_time")))
    print(f"Phase A: filled departure_time for {filled_dep} buses, arrival_time for {filled_arr} buses (repaired {fixed_arr})")
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
    # links may be absolute (https://wbbustime.in/bus-timetable/...) or relative (/bus-timetable/...)
    links = re.findall(r'href="(?:https://wbbustime\.in)?(/bus-timetable/[^"]+)"[^>]*>([^<]+)', html)
    # links text like "Kharagpur to Burdwan Bus Timetable, ..."
    idx = {}
    for path, text in links:
        url = "https://wbbustime.in" + path
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

    page_cache = {}
    def get_stops(url):
        if url not in page_cache:
            page_cache[url] = parse_wbbustime_stops(fetch(url))
            time.sleep(0.5)  # be polite
        return page_cache[url]

    filled_keys = set()   # one bus per (origin, destination) per run
    matched = tried = 0
    for b in missing:
        key = (b["origin"].strip().lower(), b["destination"].strip().lower())
        if key in filled_keys:
            continue
        dep = None
        # forward match: page lists origin -> destination; up column = that direction
        url = idx.get(key)
        if url:
            tried += 1
            stops = get_stops(url)
            first_up = next((u for _, u, d in stops if u), "")
            if valid_time(first_up):
                dep = first_up
        if dep is None:
            # reverse match: page lists destination -> origin; our bus goes the
            # other way, so its departure is the down time at the page's last stop
            rurl = idx.get((key[1], key[0]))
            if rurl:
                tried += 1
                stops = get_stops(rurl)
                last_down = next((d for _, u, d in reversed(stops) if d), "")
                if valid_time(last_down):
                    dep = last_down
        if dep is None:
            continue
        filled_keys.add(key)
        matched += 1
        if not dry_run:
            b["departure_time"] = dep
            b["time_source"] = "wbbustime.in"
        if matched >= 250:
            print("  (capped at 250 fills per run to stay polite - rerun later for more)")
            break

    print(f"Phase B (wbbustime): fetched {len(page_cache)} route pages, matched {matched} buses")
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
