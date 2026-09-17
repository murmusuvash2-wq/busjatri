#!/usr/bin/env python3
"""Merge verified schedule rows from data/new_source_times.tsv into
data/busjatri_data.json.

Each TSV row (tab-separated, 9 columns) is either:
  ADD  - a NEW bus entry (a route or operator+departure combo not yet in the
         data, scraped from a verified public timetable page)
  FILL - fill times on an EXISTING bus: by target_id if given, else the first
         time-less bus matching (origin, destination)

Dedup rule for ADD: skip if an existing bus already has the same
(origin, destination, operator, normalized departure time), so re-running
the script never duplicates buses.

Usage:
  python3 scripts/fill_new_sources.py            # dry run (report only)
  python3 scripts/fill_new_sources.py --write    # apply and save
"""
import csv
import json
import re
import sys

DATA = "data/busjatri_data.json"
TSV = "data/new_source_times.tsv"

SOURCE_URLS = {
    "santoshbusservice.com": "https://www.santoshbusservice.com/schedules",
    "durgapurhub.com": "https://durgapurhub.com/durgapur-to-kolkata-buses-routes-timings-and-fares/",
    "siligurismc.in": "https://www.siligurismc.in/bus-schedule.php",
}

TIME_RE = re.compile(r"^(\d{1,2})[:.](\d{2})\s*(AM|PM|am|pm)?$")


def norm_time(t):
    t = (str(t or "")).strip()
    m = TIME_RE.match(t)
    if not m:
        return ""
    h, mm, ap = int(m.group(1)), m.group(2), (m.group(3) or "").upper()
    if ap == "AM" and h == 12:
        h = 0
    elif ap == "PM" and h != 12:
        h += 12
    if h == 24:
        h = 0
    return "%02d:%s" % (h, mm)


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or "x"


def has_any_time(b):
    if (b.get("departure_time") or "").strip():
        return True
    for s in b.get("stoppages") or []:
        if isinstance(s, dict) and ((s.get("up_time") or "").strip() or (s.get("down_time") or "").strip()):
            return True
    return False


def main(write=False):
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    buses = data["buses"]
    before = len(buses)
    ids = {b.get("id") for b in buses}
    by_pair = {}
    for b in buses:
        by_pair.setdefault((b.get("origin"), b.get("destination")), []).append(b)

    with open(TSV, encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))[1:]

    added = filled = skipped = 0
    for r in rows:
        r = r + [""] * (9 - len(r))
        mode, source, origin, dest, op, btype, dep, arr, target = [x.strip() for x in r[:9]]
        if not dep:
            skipped += 1
            continue
        url = SOURCE_URLS.get(source, "https://" + source if source else "")
        depot = "Siliguri" if source == "siligurismc.in" else ""

        if mode == "ADD":
            nd = norm_time(dep)
            pair = by_pair.get((origin, dest), [])
            dup = any(
                norm_time(x.get("departure_time")) == nd
                and (x.get("operator") or "").strip().lower() == op.lower()
                for x in pair
            )
            if not nd or dup:
                skipped += 1
                continue
            bid = "%s-%s-%s-%d" % (slug(op), slug(origin), slug(dest), before + added + 1)
            while bid in ids:
                bid += "-x"
            ids.add(bid)
            stops = [
                {"no": 1, "name": origin, "up_time": dep, "down_time": ""},
                {"no": 2, "name": dest, "up_time": arr, "down_time": ""},
            ]
            bus = {
                "id": bid,
                "bus_name": "%s %s-%s" % (op, origin, dest),
                "reg_no": "",
                "operator": op,
                "bus_type": btype,
                "origin": origin,
                "destination": dest,
                "departure_time": dep,
                "arrival_time": arr,
                "contact_number": "",
                "depot_name": depot,
                "route": "%s - %s" % (origin, dest),
                "stoppages": stops,
                "source": source,
                "time_source": source,
                "total_stoppages": 2,
                "detail_url": url,
            }
            buses.append(bus)
            by_pair.setdefault((origin, dest), []).append(bus)
            added += 1

        elif mode == "FILL":
            if target:
                cands = [b for b in buses if b.get("id") == target and not has_any_time(b)]
            else:
                cands = [b for b in by_pair.get((origin, dest), []) if not has_any_time(b)]
            used = {norm_time(x.get("departure_time")) for x in by_pair.get((origin, dest), [])}
            if cands and norm_time(dep) and norm_time(dep) not in used:
                b = cands[0]
                b["departure_time"] = dep
                if arr:
                    b["arrival_time"] = arr
                b["time_source"] = source
                st = b.get("stoppages") or []
                if st:
                    st[0]["up_time"] = dep
                    if arr and len(st) > 1:
                        st[-1]["up_time"] = arr
                filled += 1
            else:
                skipped += 1

    print("before: %d buses | added: %d | filled: %d | skipped: %d | after: %d"
          % (before, added, filled, skipped, len(buses)))
    assert len(buses) >= before, "bus count dropped - aborting"
    if write:
        data.setdefault("meta", {})["last_updated"] = "2026-09-18"
        with open(DATA, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("written.")
    else:
        print("dry run - nothing written (use --write)")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
