#!/usr/bin/env python3
"""
Route pages: replace Route Map with ALL Via Stoppages (2026-09-23).

Before: route pages had a "Route Map" timeline (one bus sequence, 2-5 stops)
followed by a "Via Stoppages" chip row limited to ~8 common stops.

After: the Route Map section is REMOVED and Via Stoppages lists every
stoppage name from every bus on the route (direct + through buses), ordered
by how many buses serve the stop (main route first, rare stops last).
The chip row keeps its horizontal scroll with prev/next arrows
(route-slider.js attaches to .chip-row.hscroll).

Idempotent, backslash-free. Run from repo root.
"""

import ast
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)

OLD_MAP = (
    '    map_buses = list(buses) + [tb for _sk, tb, _d, _a in through]' + NL +
    '    route_section = g.route_stops_html(map_buses, origin, destination)' + NL +
    NL +
    '    major_stops = g.stoppage_summary(map_buses)'
)

NEW_MAP = (
    '    map_buses = list(buses) + [tb for _sk, tb, _d, _a in through]' + NL +
    NL +
    "    # all stoppage names across the route's buses - common stops first, then rarer ones" + NL +
    '    from collections import Counter as _Counter' + NL +
    '    _cnt, _first = _Counter(), {}' + NL +
    '    for _i, _sq in enumerate(sq for sq in (g.bus_stops(b) for b in map_buses) if sq):' + NL +
    '        for _pos, _st in enumerate(_sq):' + NL +
    '            _cnt[_st] += 1' + NL +
    '            if _st not in _first:' + NL +
    '                _first[_st] = (_i, _pos)' + NL +
    '    major_stops = sorted(_cnt.keys(), key=lambda st: (-_cnt[st], _first[st]))'
)

OLD_BODY = 'body = hero + timetable + alt_section + route_section + major_section + faq_section + reverse_section + related_section'

NEW_BODY = 'body = hero + timetable + alt_section + major_section + faq_section + reverse_section + related_section'


def main():
    p = os.path.join(ROOT, "scripts", "gen_route_v2.py")
    s = io.open(p, encoding="utf-8").read()

    if "all stoppage names across the route's buses" in s:
        print("gen_route_v2.py: already patched (all stops)")
        return

    if s.count(OLD_MAP) != 1:
        raise SystemExit("map_buses anchor not found exactly once - aborting")
    if s.count(OLD_BODY) != 1:
        raise SystemExit("body anchor not found exactly once - aborting")
    if '<div class="chip-row hscroll">{chips2}</div>' not in s:
        raise SystemExit("hscroll chip container not found - aborting")

    s = s.replace(OLD_MAP, NEW_MAP, 1)
    s = s.replace(OLD_BODY, NEW_BODY, 1)

    ast.parse(s)
    io.open(p, "w", encoding="utf-8").write(s)
    print("gen_route_v2.py: Route Map removed, Via Stoppages = ALL stops (hscroll + arrows kept)")


if __name__ == "__main__":
    main()
