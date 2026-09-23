#!/usr/bin/env python3
"""
Copy text v3 (2026-09-23) — stoppages now include return (arrival) times too.

Before: stoppages listed only outbound times (up_time, falling back to down_time).
After: when a bus has both outbound and return stop times, each stop line shows
"Name - 1:50 PM / 5:20 PM" (outbound / return). Buses with only outbound times
keep the single-time format.

Idempotent, backslash-free. Run from repo root.
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)

OLD = NL.join([
    "  var timed = stops.filter(function (s) { return s.up_time; }).map(function (s) { return pn(s.name) + ' ' + DASH + ' ' + s.up_time; });",
    "  if (!timed.length) timed = stops.filter(function (s) { return s.down_time; }).map(function (s) { return pn(s.name) + ' ' + DASH + ' ' + s.down_time; });",
    "  if (timed.length) {",
    "    L.push('');",
    "    L.push(STOP + ' Stoppages:');",
    "    timed.forEach(function (t, i) { L.push((i + 1) + '. ' + t); });",
    "  }",
])

NEW = NL.join([
    "  var hasUp = stops.some(function (s) { return s.up_time; });",
    "  var hasDown = stops.some(function (s) { return s.down_time; });",
    "  if (hasUp || hasDown) {",
    "    L.push('');",
    "    L.push(STOP + (hasUp && hasDown ? ' Stoppages (outbound / return):' : ' Stoppages:'));",
    "    var n = 0;",
    "    stops.forEach(function (s) {",
    "      var up = s.up_time || '', down = s.down_time || '';",
    "      var line = '';",
    "      if (hasUp && hasDown) {",
    "        if (up || down) line = pn(s.name) + ' ' + DASH + ' ' + (up || '-') + ' / ' + (down || '-');",
    "      } else if (up) {",
    "        line = pn(s.name) + ' ' + DASH + ' ' + up;",
    "      } else if (down) {",
    "        line = pn(s.name) + ' ' + DASH + ' ' + down;",
    "      }",
    "      if (line) { n = n + 1; L.push(n + '. ' + line); }",
    "    });",
    "  }",
])


def main():
    p = os.path.join(ROOT, "js", "bus-page.js")
    s = open(p, encoding="utf-8").read()
    if "outbound / return):" in s:
        print("js/bus-page.js: stops v3 already applied")
        return
    if OLD not in s:
        raise SystemExit("old stoppages block not found - review js/bus-page.js")
    s = s.replace(OLD, NEW, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("js/bus-page.js: stoppages now include return times")


if __name__ == "__main__":
    main()
