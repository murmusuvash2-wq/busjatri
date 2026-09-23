#!/usr/bin/env python3
"""Route-map fix 2: pick a stop sequence that actually matches the route.

The Route Map used the most-common stoppage sequence of the route's buses,
which can belong to an unrelated through-service (e.g. Jhargram ->
Durgapur Station showed a Purulia -> Kolkata sequence because one bus in
the group carried those stoppages). Now the generator:
  1. considers direct + through buses,
  2. prefers a sequence that can be trimmed to origin -> destination,
  3. hides the Route Map entirely when no sequence matches the route.

Idempotent: safe to run multiple times.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch(path, replacements):
    p = os.path.join(ROOT, path)
    with open(p, encoding="utf-8") as fh:
        s = fh.read()
    if replacements[0][1] in s:
        print(path + ": already patched")
        return
    for old, new in replacements:
        if old not in s:
            raise SystemExit("ABORT: expected text not found in " + path + ": " + old[:60])
        s = s.replace(old, new, 1)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(s)
    print(path + ": patched")


GEN = "scripts/gen_seo_pages.py"

patch(GEN, [
    ("def route_stops_html(buses):\n    sequences = []\n    for bus in buses:\n        stops = bus_stops(bus)\n        if stops:\n            sequences.append(stops)\n    if not sequences:\n        return \"\"\n    from collections import Counter as _C\n    sc = _C(tuple(s) for s in sequences)\n    sequence, frequency = sc.most_common(1)[0]\n    sequence = list(sequence)\n",
     "def route_stops_html(buses, origin=None, destination=None):\n    sequences = []\n    for bus in buses:\n        stops = bus_stops(bus)\n        if stops:\n            sequences.append(stops)\n    if not sequences:\n        return \"\"\n    from collections import Counter as _C\n    sc = _C(tuple(s) for s in sequences)\n\n    def _hit(stop, place):\n        if not place:\n            return False\n        a, b = slug(stop), slug(place)\n        return a == b or b in a\n\n    def _best(seq):\n        # Prefer a sequence that can be trimmed to origin -> destination\n        oi = di = None\n        if origin:\n            for i, st in enumerate(seq):\n                if _hit(st, origin):\n                    oi = i\n                    break\n        if destination:\n            for i in range(len(seq) - 1, -1, -1):\n                if _hit(seq[i], destination):\n                    di = i\n                    break\n        if oi is not None and di is not None and di > oi:\n            return 3, list(seq[oi:di + 1])\n        if (not origin or _hit(seq[0], origin)) and (not destination or _hit(seq[-1], destination)):\n            return 2, list(seq)\n        return 0, None\n\n    best = None  # (score, count, seq)\n    for seq, count in sc.most_common():\n        score, cand = _best(seq)\n        if score == 0:\n            continue\n        if best is None or score > best[0] or (score == best[0] and count > best[1]):\n            best = (score, count, cand)\n    if best is None:\n        return \"\"\n    sequence = best[2]\n"),
    ("    route_section = route_stops_html(buses)",
     "    route_section = route_stops_html(buses, origin, destination)"),
])

patch("scripts/gen_route_v2.py", [
    ("    route_section = g.route_stops_html(buses)\n\n    major_stops = g.stoppage_summary(buses)",
     "    map_buses = list(buses) + [tb for _sk, tb, _d, _a in through]\n    route_section = g.route_stops_html(map_buses, origin, destination)\n\n    major_stops = g.stoppage_summary(map_buses)"),
])

print("route-map fix 2 complete")
