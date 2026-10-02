#!/usr/bin/env python3
"""Guard the Private Long-Distance Routes section on the All Bus Timetable hub.

Fails if the section is missing, if it shows no route cards, or if any card
points at a route page that does not exist (a broken link on a hub page).
"""
import glob
import os
import re
import sys

IDX = 'bus-time-table/index.html'
h = open(IDX, encoding='utf-8', errors='ignore').read()

m = re.search(r'<section class="section" id="longDistanceSec">(.*?)</section>', h, re.S)
if not m:
    print('long-distance section missing')
    sys.exit(1)

sec = m.group(1)
cards = re.findall(r'<a class="op-card" href="([^"]+)"', sec)
if not cards:
    print('long-distance section has no route cards')
    sys.exit(1)

missing = [c for c in cards if not os.path.exists('bus-time-table/' + c)]
if missing:
    print('cards pointing at missing pages:', missing[:5])
    sys.exit(1)

pages = set(os.path.basename(p) for p in glob.glob('bus-time-table/*.html'))
print(f'long-distance section OK: {len(cards)} cards, all targets exist')
