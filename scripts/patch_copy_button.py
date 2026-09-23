#!/usr/bin/env python3
"""
Copy button text v2 (2026-09-23) — well-organised copy text with departure AND arrival.

Old format: bus/reg/contact/route+dep on separate lines, stops crammed in one
line with dot separators, arrival missing.

New format:
  BUS NAME
  REG NO
  Origin -> Destination

  Departure: 7:30 AM
  Arrival: 11:45 AM
  Contact: 98xxxxxx

  Stoppages:
  1. Stop - 7:45 AM
  2. ...

  - BusJatri.in

Idempotent, backslash-free. Run from repo root.
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)

OLD = NL.join([
    "function buildBusCopyText(b, stops) {",
    "  var E = String.fromCharCode;",
    "  var BUS = E(0xD83D,0xDE8C), NUM = E(0xD83D,0xDD22), PHONE = E(0xD83D,0xDCDE), PIN = E(0xD83D,0xDCCD), STOP = E(0xD83D,0xDE8F);",
    "  var DOT = E(0xB7), ARROW = E(0x2192), DASH = E(0x2014), NL = E(10);",
    "  var L = [];",
    "  L.push(BUS + ' ' + (b.bus_name || ''));",
    "  if (b.reg_no) L.push(NUM + ' ' + fmtRegNo(b.reg_no));",
    "  if (b.contact_number && b.contact_number !== 'Not Available !') L.push(PHONE + ' ' + b.contact_number);",
    "  if (b.origin && b.destination) L.push(PIN + ' ' + pn(b.origin) + ' ' + ARROW + ' ' + pn(b.destination) + (b.departure_time ? ' ' + DOT + ' ' + b.departure_time : ''));",
    "  var timed = stops.filter(function (s) { return s.up_time; }).map(function (s) { return pn(s.name) + ' ' + s.up_time; });",
    "  if (!timed.length) timed = stops.filter(function (s) { return s.down_time; }).map(function (s) { return pn(s.name) + ' ' + s.down_time; });",
    "  if (timed.length) { L.push(''); L.push(STOP + ' ' + timed.join(' ' + DOT + ' ')); }",
    "  L.push('');",
    "  L.push(DASH + ' BusJatri.in ' + BUS);",
    "  return L.join(NL);",
    "}",
])

NEW = NL.join([
    "function buildBusCopyText(b, stops) {",
    "  var E = String.fromCharCode;",
    "  var BUS = E(0xD83D,0xDE8C), NUM = E(0xD83D,0xDD22), PHONE = E(0xD83D,0xDCDE), PIN = E(0xD83D,0xDCCD), STOP = E(0xD83D,0xDE8F);",
    "  var CLOCK = E(0x23F0), FLAG = E(0x1F3C1), DOT = E(0xB7), ARROW = E(0x2192), DASH = E(0x2014), NL = E(10);",
    "  var L = [];",
    "  L.push(BUS + ' ' + (b.bus_name || ''));",
    "  if (b.reg_no) L.push(NUM + ' ' + fmtRegNo(b.reg_no));",
    "  if (b.origin && b.destination) L.push(PIN + ' ' + pn(b.origin) + ' ' + ARROW + ' ' + pn(b.destination));",
    "  var det = [];",
    "  if (b.departure_time) det.push(CLOCK + ' Departure: ' + b.departure_time);",
    "  if (b.arrival_time) det.push(FLAG + ' Arrival: ' + b.arrival_time);",
    "  if (b.contact_number && b.contact_number !== 'Not Available !') det.push(PHONE + ' Contact: ' + b.contact_number);",
    "  if (det.length) { L.push(''); L.push(det.join(NL)); }",
    "  var timed = stops.filter(function (s) { return s.up_time; }).map(function (s) { return pn(s.name) + ' ' + DASH + ' ' + s.up_time; });",
    "  if (!timed.length) timed = stops.filter(function (s) { return s.down_time; }).map(function (s) { return pn(s.name) + ' ' + DASH + ' ' + s.down_time; });",
    "  if (timed.length) {",
    "    L.push('');",
    "    L.push(STOP + ' Stoppages:');",
    "    timed.forEach(function (t, i) { L.push((i + 1) + '. ' + t); });",
    "  }",
    "  L.push('');",
    "  L.push(DASH + ' BusJatri.in ' + BUS);",
    "  return L.join(NL);",
    "}",
])


def main():
    p = os.path.join(ROOT, "js", "bus-page.js")
    s = open(p, encoding="utf-8").read()
    if "Arrival: ' + b.arrival_time" in s:
        print("js/bus-page.js: already patched")
        return
    if OLD not in s:
        raise SystemExit("old buildBusCopyText not found - review js/bus-page.js")
    s = s.replace(OLD, NEW, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("js/bus-page.js: copy text v2 applied (departure + arrival + organised)")


if __name__ == "__main__":
    main()
