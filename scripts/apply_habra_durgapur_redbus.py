#!/usr/bin/env python3
"""Fill missing departure times on the Habra -> Durgapur route from redBus
(Sep 2026) and add the second SBSTC morning service found there.

Sources (redBus, accessed 27 Sep 2026):
- Live search page Habra->Durgapur 29-Sep-2026: WBTC (CTC) route 100
  "Habra - Barasat - Durgapur - Asansol" departs 05:05, arrives Durgapur
  09:00 (3h 55m), Non AC Seater, fare Rs 165.
- redBus route page (bus-tickets/habra-to-durgapur): SBSTC first bus 06:05,
  last bus 07:00 (2 services), fare from Rs 180; total 5 direct buses by
  2 operators.

Decisions (disclosed):
- SBSTC fares in our data stay at the official SBSTC timetable value
  (Rs. 124 from the WB transport PDF); redBus's Rs 180 is its selling
  price, the govt PDF remains the on-board fare.
- The WBTC entry gets redBus's listed fare Rs 165 (no WBTC published fare
  exists in our data).
- SBSTC arrival times stay empty (redBus's 4h45m duration is an aggregate,
  not a per-bus arrival). The WBTC arrival 09:00 comes directly from the
  live redBus listing.
- The second WBTC entry ktr-government-habra-to-durgapur-1 is actually the
  REVERSE (Durgapur -> Habra) bus; its time is NOT guessed - redBus's
  Habra->Durgapur data says nothing about it. Left unchanged.

Edits data/busjatri_data.json directly (2 updates + 1 new bus) and patches
bus-time-table/sbstc-buses.html counts + window.bjOpData. Idempotent.
ASCII-only source.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "busjatri_data.json"
SBSTC_PAGE = ROOT / "bus-time-table" / "sbstc-buses.html"

TIME_SOURCE = "redbus.in (Habra-Durgapur, Sep 2026)"
WBTC_TIME_SOURCE = "redbus.in (WBTC CTC route 100 listing, Sep 2026)"


def norm_op(o):
    return (o or "").strip().upper()


def add_times(write):
    data = json.loads(DATA.read_text(encoding="utf-8"))
    buses = data["buses"]
    by_id = {b["id"]: b for b in buses}

    changes = []

    # 1. SBSTC Habra->Durgapur 06:05 (first bus)
    b = by_id["sbstc-habra-durgapur-0"]
    assert b["origin"] == "Habra" and b["destination"] == "Durgapur"
    if b.get("departure_time") == "":
        b["departure_time"] = "6:05 AM"
        b["time_source"] = TIME_SOURCE
        changes.append("sbstc-habra-durgapur-0 -> 6:05 AM")
    else:
        assert b["departure_time"] == "6:05 AM", b["departure_time"]

    # 2. New SBSTC Habra->Durgapur 07:00 (last bus)
    if "sbstc-habra-durgapur-1" not in by_id:
        nb = json.loads(json.dumps(b))  # clone the 06:05 entry
        nb["id"] = "sbstc-habra-durgapur-1"
        nb["departure_time"] = "7:00 AM"
        idx = buses.index(b)
        buses.insert(idx + 1, nb)
        changes.append("sbstc-habra-durgapur-1 added -> 7:00 AM")

    # 3. WBTC (CTC route 100) Habra->Durgapur 05:05 -> 09:00, fare 165
    k = by_id["ktr-government-habra-to-durgapur"]
    assert k["origin"] == "Habra" and k["destination"] == "Durgapur"
    if k.get("departure_time") == "":
        k["departure_time"] = "5:05 AM"
        k["arrival_time"] = "9:00 AM"
        k["fare"] = "Rs. 165"
        k["time_source"] = WBTC_TIME_SOURCE
        changes.append("ktr-government-habra-to-durgapur -> 5:05 AM / 9:00 AM, Rs. 165")
    else:
        assert k["departure_time"] == "5:05 AM", k["departure_time"]

    data["meta"]["total_buses"] = len(buses)

    if write:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                        encoding="utf-8")
        for c in changes:
            print("WRITE:", c)
    else:
        for c in changes:
            print("DRY:", c)
    print("total buses:", len(buses))
    return len(buses)


def patch_sbstc_page():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    sb = [b for b in data["buses"] if norm_op(b.get("operator")) == norm_op("SBSTC")]
    n = len(sb)
    routes = {(b["origin"], b["destination"]) for b in sb}
    r = len(routes)
    busiest = {}
    for b in sb:
        kk = (b["origin"], b["destination"])
        busiest[kk] = busiest.get(kk, 0) + 1
    (bo, bd), bc = max(busiest.items(), key=lambda x: x[1])
    print("SBSTC: %d buses, %d routes, busiest %s->%s (%d)" % (n, r, bo, bd, bc))

    s = SBSTC_PAGE.read_text(encoding="utf-8")

    # FAQ sentences (visible + JSON-LD, EN and BN)
    en_old = "536 SBSTC services are listed on BusJatri, covering 163 routes."
    en_new = "%d SBSTC services are listed on BusJatri, covering %d routes." % (n, r)
    assert en_old in s, "EN FAQ string not found"
    s = s.replace(en_old, en_new)
    assert s.count(en_new) == 2, "EN FAQ should appear twice (JSON-LD + visible)"

    # BN sentences: same counts embedded; find the 536/163 pattern generically
    stat_bus = ">\U0001F68C 536 <"
    stat_route = ">\U0001F6E3 163 <"
    assert stat_bus in s and stat_route in s, "stat spans not found"
    s = s.replace(stat_bus, ">\U0001F68C %d <" % n)
    s = s.replace(stat_route, ">\U0001F6E3 %d <" % r)

    cnt_old = '"count": 536}'
    assert cnt_old in s, "count not found"
    s = s.replace(cnt_old, '"count": %d}' % n)

    # BN FAQ: replace the Bengali-numbered counts (536 and 163) around
    # the tokens; they sit in the two BN FAQ sentences (visible + JSON-LD).
    bn_num_old = "536\u099f\u09bf SBSTC"
    bn_num_new = "%d\u099f\u09bf SBSTC" % n
    assert s.count(bn_num_old) == 2, "BN bus count x%d" % s.count(bn_num_old)
    s = s.replace(bn_num_old, bn_num_new)
    # 163 in BN text appears as "163\u099f\u09bf \u09b0\u09c1\u099f"
    bn_route_old = "163\u099f\u09bf \u09b0\u09c1\u099f"
    bn_route_new = "%d\u099f\u09bf \u09b0\u09c1\u099f" % r
    if bn_route_old in s:
        s = s.replace(bn_route_old, bn_route_new)

    # rebuild window.bjOpData from the live data
    start = s.find("window.bjOpData = [")
    assert start != -1, "bjOpData not found"
    seg_start = s.find("[", start)
    seg_end = s.find("];", seg_start)
    assert seg_end != -1
    entries = [[b["id"], b.get("bus_name", ""), b["origin"], b["destination"],
                b.get("departure_time", "")] for b in sb]
    body = ", ".join(json.dumps(e, ensure_ascii=False) for e in entries)
    s = s[:seg_start] + "[" + body + "]" + s[seg_end + 1:]
    parsed = json.loads(s[start:s.find("];", start) + 1].split("= ", 1)[1].rstrip(";"))
    assert len(parsed) == n, "bjOpData len %d != %d" % (len(parsed), n)

    assert "536" not in s, "stale 536 left in page"
    SBSTC_PAGE.write_text(s, encoding="utf-8")
    print("sbstc-buses.html patched: %d buses, %d routes" % (n, r))


def main():
    write = "--write" in sys.argv
    add_times(write)
    if write:
        patch_sbstc_page()


if __name__ == "__main__":
    main()
