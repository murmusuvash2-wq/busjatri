#!/usr/bin/env python3
# Revert wrong flyer additions - 2026-09-24 (evening)
# User-caught OCR mistakes in patch_flyers_20260924.py:
#   - 5 "Kolkata-Khargram" buses = misread of Jhargram (Bengali Jhargram vs Khargram)
#     and duplicate existing sbstc-fb-kolkata-jhargram-* entries (same times).
#   - 1 "Medinipur-Howrah 2:00 PM" bus = misread of Habra (Bengali Howrah vs Habra)
#     and duplicate of existing sbstc-fb-midnapore-habra-200pm.
# Removes all 6 buses + the kolkata-to-khargram route page + its sitemap URL.
# Keeps: 3 CB-Siliguri evening buses, CB-Kolkata 1:30 PM fix, Haldia 8:25 AM fix.
# Idempotent: safe to re-run.

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'busjatri_data.json')

BAD_IDS = [
    'sbstc-fb-kolkata-khargram-730am',
    'sbstc-fb-kolkata-khargram-825am',
    'sbstc-fb-kolkata-khargram-925am',
    'sbstc-fb-kolkata-khargram-245pm',
    'sbstc-fb-kolkata-khargram-315pm',
    'sbstc-fb-medinipur-howrah-200pm',
]

with open(DATA, encoding='utf-8') as fh:
    d = json.load(fh)
before = len(d['buses'])
d['buses'] = [b for b in d['buses'] if b.get('id') not in BAD_IDS]
removed = before - len(d['buses'])
with open(DATA, 'w', encoding='utf-8') as fh:
    json.dump(d, fh, ensure_ascii=False, indent=1)
print('buses removed:', removed, '| total now:', len(d['buses']))

# remove wrongly created route page
page = os.path.join(ROOT, 'bus-time-table', 'kolkata-to-khargram.html')
if os.path.exists(page):
    os.remove(page)
    print('removed bus-time-table/kolkata-to-khargram.html')
else:
    print('kolkata-to-khargram.html already absent')

# remove its sitemap entry
SITEMAP_PATH = os.path.join(ROOT, 'sitemap.xml')
with open(SITEMAP_PATH, encoding='utf-8') as fh:
    sm = fh.read()
loc = 'https://busjatri.in/bus-time-table/kolkata-to-khargram.html'
marker = '<url><loc>' + loc
k = sm.find(marker)
if k >= 0:
    end = sm.find('</url>', k)
    if end >= 0:
        tail = end + len('</url>')
        sm = sm[:k] + sm[tail:]
        with open(SITEMAP_PATH, 'w', encoding='utf-8') as fh:
            fh.write(sm)
        print('sitemap entry removed')
    else:
        print('sitemap entry malformed - url close not found')
else:
    print('sitemap entry already absent')
