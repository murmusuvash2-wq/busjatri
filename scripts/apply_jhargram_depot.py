#!/usr/bin/env python3
"""Add SBSTC Jhargram Depot buses (58 services) from the depot timetable
boards (community photos, Sep 2026). Board source: Jhargram depot main
routes board + village routes board, merged and confirmed by the site
owner. Booking counter: opposite Jhargram SBI Bank, ph 7477789423.

Times confirmed from the boards; arrival times are not listed on the
boards so they stay empty. Via stops (Lodhashuli, Kherua, Jhargram,
Medinipur, Kharagpur, Keshiary) are included as intermediate stoppages.

Notes on interpretation (disclosed):
- "a / b" time pairs on the boards are ONE service with a board
  discrepancy -> the first time is used.
- The 04:20 PM / 06:20 PM Kolkata->Jhargram pair is TWO services
  (2 hours apart).
- No Patna service is listed on the boards -> the 02:10 PM bus is
  added as Jhargram->Garia only.
- Existing Kolkata->Jhargram SBSTC services (6:30, 7:30, 8:25, 9:25 AM,
  2:45, 3:15 PM) are kept; 7:00 AM / 03:12 PM pair-mates are not added.

Merges directly into data/busjatri_data.json (NOT via
add_community_buses.py - its dedup key origin+destination+operator
would drop all but one bus per route). Dedup here is
origin+destination+operator+time, idempotent.

Also patches bus-time-table/sbstc-buses.html: refreshes the hardcoded
SBSTC bus count, route count and the window.bjOpData list from the
data (the page was 17 buses stale already). ASCII-only source.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "busjatri_data.json"
SBSTC_PAGE = ROOT / "bus-time-table" / "sbstc-buses.html"

CONTACT = "7477789423"  # Jhargram depot booking counter (opposite SBI bank)
SOURCE = "SBSTC Jhargram depot board (community photo, Sep 2026)"
BUS_TYPE = "Government - SBSTC"

# (origin, destination, departure_time, via stops, bus_name)
JH = "Jhargram"
KL = "Kolkata"
MD = "Medinipur"
ENTRIES = [
    # --- Jhargram -> Kolkata ---
    (JH, KL, "4:40 AM", ["Lodhashuli"], "SBSTC Jhargram-Kolkata"),
    (JH, KL, "5:00 AM", ["Lodhashuli"], "SBSTC Jhargram-Kolkata"),
    (JH, KL, "5:40 AM", ["Lodhashuli"], "SBSTC Jhargram-Kolkata"),
    (JH, KL, "6:30 AM", ["Lodhashuli"], "SBSTC Jhargram-Kolkata"),
    (JH, KL, "6:50 AM", ["Kherua", "Medinipur"], "SBSTC Jhargram-Kolkata"),
    (JH, KL, "7:30 AM", ["Lodhashuli"], "SBSTC Jhargram-Kolkata"),
    (JH, KL, "9:00 AM", ["Medinipur"], "SBSTC Jhargram-Kolkata"),
    (JH, KL, "1:35 PM", ["Medinipur"], "SBSTC Jhargram-Kolkata"),
    (JH, KL, "3:10 PM", ["Lodhashuli", "Garia"], "SBSTC Jhargram-Kolkata"),
    # --- Bandwan / Belpahari -> Kolkata (via Jhargram) ---
    ("Bandwan", KL, "6:10 AM", [JH, "Lodhashuli"], "SBSTC Bandwan-Kolkata"),
    ("Belpahari", KL, "8:30 AM", [JH, "Lodhashuli"], "SBSTC Belpahari-Kolkata"),
    # --- Jhargram -> Garia / Karunamoyee ---
    (JH, "Garia", "10:45 AM", ["Medinipur"], "SBSTC Jhargram-Garia"),
    (JH, "Garia", "2:10 PM", ["Lodhashuli"], "SBSTC Jhargram-Garia"),
    (JH, "Karunamoyee", "3:00 PM", ["Lodhashuli"], "SBSTC Jhargram-Karunamoyee"),
    # --- Jhargram <-> Medinipur ---
    (JH, MD, "6:15 AM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (JH, MD, "7:22 AM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (JH, MD, "7:45 AM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (JH, MD, "9:00 AM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (JH, MD, "10:05 AM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (JH, MD, "12:10 PM", ["Lodhashuli"], "SBSTC Jhargram-Medinipur"),
    (JH, MD, "5:00 PM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (JH, MD, "5:50 PM", ["Lodhashuli"], "SBSTC Jhargram-Medinipur"),
    (MD, JH, "6:55 AM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (MD, JH, "8:00 AM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (MD, JH, "9:50 AM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (MD, JH, "10:20 AM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (MD, JH, "2:40 PM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (MD, JH, "6:15 PM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    (MD, JH, "7:00 PM", ["Kherua"], "SBSTC Jhargram-Medinipur"),
    # --- Jhargram -> Durgapur ---
    (JH, "Durgapur", "2:50 AM", [], "SBSTC Jhargram-Durgapur"),
    (JH, "Durgapur", "5:20 AM", [], "SBSTC Jhargram-Durgapur"),
    (JH, "Durgapur", "5:50 AM", [], "SBSTC Jhargram-Durgapur"),
    (JH, "Durgapur", "7:05 AM", [], "SBSTC Jhargram-Durgapur"),
    (JH, "Durgapur", "9:30 AM", [], "SBSTC Jhargram-Durgapur"),
    (JH, "Durgapur", "1:05 PM", [], "SBSTC Jhargram-Durgapur"),
    (JH, "Durgapur", "2:20 PM", [], "SBSTC Jhargram-Durgapur"),
    (JH, "Durgapur", "3:35 PM", [], "SBSTC Jhargram-Durgapur"),
    # --- Purulia / Suri / Bandwan / Belpahari ---
    (JH, "Purulia", "6:30 AM", [], "SBSTC Jhargram-Purulia"),
    (MD, "Purulia", "6:40 AM", [JH], "SBSTC Medinipur-Purulia"),
    (JH, "Suri", "1:00 PM", [], "SBSTC Jhargram-Suri"),
    (JH, "Bandwan", "1:40 PM", [], "SBSTC Jhargram-Bandwan"),
    (JH, "Belpahari", "4:22 PM", [], "SBSTC Jhargram-Belpahari"),
    (JH, "Belpahari", "5:30 PM", [], "SBSTC Jhargram-Belpahari"),
    # --- Kolkata -> Jhargram ---
    (KL, JH, "2:00 AM", ["Medinipur"], "SBSTC Kolkata-Jhargram"),
    (KL, JH, "9:15 AM", ["Lodhashuli"], "SBSTC Kolkata-Jhargram"),
    (KL, JH, "10:30 AM", ["Lodhashuli"], "SBSTC Kolkata-Jhargram"),
    (KL, JH, "11:40 AM", ["Lodhashuli"], "SBSTC Kolkata-Jhargram"),
    (KL, JH, "1:15 PM", ["Lodhashuli"], "SBSTC Kolkata-Jhargram"),
    (KL, JH, "2:15 PM", ["Lodhashuli"], "SBSTC Kolkata-Jhargram"),
    (KL, JH, "4:20 PM", ["Lodhashuli"], "SBSTC Kolkata-Jhargram"),
    (KL, JH, "6:20 PM", ["Lodhashuli"], "SBSTC Kolkata-Jhargram"),
    # --- Dhumsai route ---
    (KL, "Dhumsai", "6:14 AM", ["Kharagpur", "Keshiary"], "SBSTC Kolkata-Dhumsai"),
    (JH, "Dhumsai", "6:10 AM", [], "SBSTC Jhargram-Dhumsai"),
    (JH, "Dhumsai", "8:20 AM", [], "SBSTC Jhargram-Dhumsai"),
    (JH, "Dhumsai", "12:00 PM", [], "SBSTC Jhargram-Dhumsai"),
    ("Dhumsai", JH, "5:00 AM", [], "SBSTC Jhargram-Dhumsai"),
    ("Dhumsai", JH, "10:00 AM", [], "SBSTC Jhargram-Dhumsai"),
    ("Dhumsai", JH, "12:00 PM", [], "SBSTC Jhargram-Dhumsai"),
]

assert len(ENTRIES) == 58, "expected 58 entries, got %d" % len(ENTRIES)


def norm_op(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower()).replace("s", "")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "x"


def add_buses(write):
    data = json.loads(DATA.read_text(encoding="utf-8"))
    buses = data["buses"]
    before = len(buses)
    existing = set()
    for b in buses:
        existing.add(((b.get("origin") or "").strip().lower(),
                      (b.get("destination") or "").strip().lower(),
                      norm_op(b.get("operator")),
                      (b.get("departure_time") or "").strip().lower()))
    ids = {b.get("id") for b in buses}
    added = 0
    for o, d, dep, via, name in ENTRIES:
        key = (o.lower(), d.lower(), norm_op("SBSTC"), dep.lower())
        if key in existing:
            print("skip (exists):", o, "->", d, dep)
            continue
        stops = [o] + via + [d]
        stoppages = []
        for i, st in enumerate(stops):
            stoppages.append({
                "no": i + 1,
                "name": st,
                "up_time": dep if i == 0 else "",
                "down_time": "",
            })
        bid = "sbstc-jhrdep-%s-%s-%d" % (slug(o), slug(d), added + 1)
        while bid in ids:
            bid += "-x"
        ids.add(bid)
        buses.append({
            "id": bid,
            "bus_name": name,
            "reg_no": "",
            "operator": "SBSTC",
            "bus_type": BUS_TYPE,
            "origin": o,
            "destination": d,
            "departure_time": dep,
            "arrival_time": "",
            "contact_number": CONTACT,
            "depot_name": "Jhargram",
            "route": " - ".join(stops),
            "stoppages": stoppages,
            "source": SOURCE,
            "time_source": SOURCE,
            "total_stoppages": len(stops),
            "detail_url": "",
        })
        existing.add(key)
        added += 1
        print("added:", bid, dep)
    print("before: %d | added: %d | after: %d" % (before, added, len(buses)))
    if write:
        data.setdefault("meta", {})["total_buses"] = len(buses)
        data["meta"]["last_updated"] = "2026-09-27"
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
        print("written.")
    return added


def patch_sbstc_page():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    sb = [b for b in data["buses"] if norm_op(b.get("operator")) == norm_op("SBSTC")]
    n = len(sb)
    routes = {(b["origin"], b["destination"]) for b in sb}
    r = len(routes)
    busiest = {}
    for b in sb:
        k = (b["origin"], b["destination"])
        busiest[k] = busiest.get(k, 0) + 1
    (bo, bd), bc = max(busiest.items(), key=lambda x: x[1])
    print("SBSTC: %d buses, %d routes, busiest %s->%s (%d)" % (n, r, bo, bd, bc))

    s = SBSTC_PAGE.read_text(encoding="utf-8")
    en_old = "495 SBSTC services are listed on BusJatri, covering 165 routes."
    en_new = "%d SBSTC services are listed on BusJatri, covering %d routes." % (n, r)
    bn_old = ("BusJatri-\u09a4\u09c7 495\u099f\u09bf SBSTC \u09ac\u09be\u09b8 "
              "\u09a4\u09be\u09b2\u09bf\u0995\u09be\u09ad\u09c1\u0995\u09cd\u09a4, "
              "165\u099f\u09bf \u09b0\u09c1\u099f \u099c\u09c1\u09a1\u09bc\u09c7\u0964")
    bn_new = ("BusJatri-\u09a4\u09c7 %d\u099f\u09bf SBSTC \u09ac\u09be\u09b8 "
              "\u09a4\u09be\u09b2\u09bf\u0995\u09be\u09ad\u09c1\u0995\u09cd\u09a4, "
              "%d\u099f\u09bf \u09b0\u09c1\u099f \u099c\u09c1\u09a1\u09bc\u09c7\u0964") % (n, r)
    assert en_old in s, "EN FAQ string not found"
    assert bn_old in s, "BN FAQ string not found"
    s = s.replace(en_old, en_new).replace(bn_old, bn_new)
    assert s.count(en_new) == 2, "EN FAQ should appear twice (JSON-LD + visible)"
    assert s.count(bn_new) == 2, "BN FAQ should appear twice"

    stat_bus = ">\U0001F68C 495 <"
    stat_route = ">\U0001F6E3 165 <"
    assert stat_bus in s and stat_route in s, "stat spans not found"
    s = s.replace(stat_bus, ">\U0001F68C %d <" % n)
    s = s.replace(stat_route, ">\U0001F6E3 %d <" % r)

    cnt_old = '"count": 495}'
    assert cnt_old in s, "count not found"
    s = s.replace(cnt_old, '"count": %d}' % n)

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
    assert json.loads(s[start:s.find("];", start) + 1].split("= ", 1)[1].rstrip(";"))

    # busiest-route FAQ (patch only if it changed)
    busy_old = "Kolkata to Haldia, with 27 listed buses."
    busy_new = "%s to %s, with %d listed buses." % (bo, bd, bc)
    if busy_old in s and busy_new != busy_old:
        s = s.replace(busy_old, busy_new)
        print("busiest patched ->", busy_new)
    else:
        print("busiest unchanged:", busy_new)

    assert "495" not in s, "stale 495 left in page"
    assert '"count": %d}' % n in s
    SBSTC_PAGE.write_text(s, encoding="utf-8")
    print("sbstc-buses.html patched: %d buses, %d routes" % (n, r))


def main():
    write = "--write" in __import__("sys").argv
    add_buses(write)
    if write:
        patch_sbstc_page()


if __name__ == "__main__":
    main()
