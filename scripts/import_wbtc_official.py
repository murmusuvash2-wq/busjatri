#!/usr/bin/env python3
"""import_wbtc_official.py — apply the official WBTC long-distance route list.

Source: data/wbtc_official_longdistance.csv — 30 WBTC long-distance services
(Route_Name, Origin, Destination, Bus_Type, Departure_Times, Via stoppages).

Cross-check: our WBTC data is a bare route list from kolkata-travel-router — 956
buses, of which 944 have NO departure time, so every WBTC route page shows
"Time N/A". This list supplies the departure times and the full via-stoppage
chain for those routes.

For each route in the list we replace our WBTC buses on that route with one bus
per listed departure time (via chain stored as stoppages). Routes not in the list
are left untouched. Idempotent.
"""

import csv
import json
import re
import unicodedata
from collections import Counter

CSV_PATH = 'data/wbtc_official_longdistance.csv'
DATA_PATH = 'data/busjatri_data.json'

# the list names the Esplanade depot as "Kolkata (Esplanade)" and the city drop
# points as "Kolkata (Drop Points)"; our data uses plain "Esplanade"/"Kolkata"
ORIGIN_FIX = {'kolkata (esplanade)': 'Esplanade'}
DEST_FIX = {'kolkata (drop points)': 'Kolkata'}


def slug(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-')


def norm(s):
    s = (s or '').lower()
    s = re.sub(r'\(.*?\)', '', s).strip()
    s = re.sub(r'\bdrop\s*points?\b', '', s)
    s = re.sub(r'[^a-z0-9]+', '', s)
    for a, b in [('esplanade', 'kolkata'), ('dharmatala', 'kolkata'),
                 ('medinipur', 'midnapore'), ('kanthi', 'contai'),
                 ('bardhaman', 'burdwan'), ('krishnagar', 'krishnanagar')]:
        s = s.replace(a, b)
    return s or 'kolkata'


def clean_time(t):
    t = re.sub(r'\(.*?\)', '', t).strip()          # drop "(Daily)" / "(Fri/Sat)"
    t = re.sub(r'^0(\d:)', r'\1', t)               # 05:40 AM -> 5:40 AM
    return t


def parse_times(s):
    return [clean_time(x) for x in s.split(',') if clean_time(x)]


def parse_via(s):
    return [x.strip() for x in s.split('>>') if x.strip()]


def is_wbtc(b):
    return ((b.get('operator') or '').lower() in ('wbtc', 'wbtc (ctc)')
            or 'wbtc' in (b.get('source') or '').lower()
            or 'WBTC' in (b.get('bus_type') or '')
            or 'CSTC' in (b.get('bus_type') or ''))


def main():
    routes = list(csv.DictReader(open(CSV_PATH, encoding='utf-8')))
    covered = set()
    for r in routes:
        o = ORIGIN_FIX.get(r['Origin'].strip().lower(), r['Origin'].strip())
        d = DEST_FIX.get(r['Destination'].strip().lower(), r['Destination'].strip())
        covered.add(norm(o) + '|' + norm(d))

    data = json.load(open(DATA_PATH, encoding='utf-8'))
    was_list = isinstance(data['buses'], list)
    buses = data['buses'] if was_list else list(data['buses'].values())

    kept, removed = [], 0
    for b in buses:
        if is_wbtc(b) and (norm(b.get('origin')) + '|' + norm(b.get('destination'))) in covered:
            removed += 1
            continue
        kept.append(b)

    seen = Counter()
    added = 0
    for r in routes:
        o = ORIGIN_FIX.get(r['Origin'].strip().lower(), r['Origin'].strip())
        d = DEST_FIX.get(r['Destination'].strip().lower(), r['Destination'].strip())
        via = parse_via(r['Exhaustive_Via_Stoppages_List'])
        btype = (r['Bus_Type'] or '').strip()
        for tm in parse_times(r['Departure_Times']):
            seen[(slug(o), slug(d))] += 1
            n = seen[(slug(o), slug(d))]
            stops = []
            for i, name in enumerate(via or [o, d]):
                stops.append({'no': i + 1, 'name': name,
                              'up_time': tm if i == 0 else '', 'down_time': ''})
            kept.append({
                'id': f'wbtc-official-{slug(o)}-{slug(d)}-{n}',
                'bus_name': f'WBTC {o}-{d}', 'reg_no': '', 'operator': 'WBTC',
                'bus_type': f'Government - {btype}' if btype else 'Government',
                'origin': o, 'destination': d, 'departure_time': tm, 'arrival_time': '',
                'contact_number': 'Not Available !', 'depot_name': '',
                'route': ' - '.join(via) if via else f'{o} - {d}',
                'stoppages': stops, 'total_stoppages': len(stops),
                'source': 'WBTC official long-distance list', 'detail_url': '',
            })
            added += 1

    data['buses'] = kept if was_list else {b['id']: b for b in kept}
    data.setdefault('meta', {})['total_buses'] = len(kept)
    json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n_wbtc = sum(1 for b in kept if is_wbtc(b))
    timed = sum(1 for b in kept if is_wbtc(b) and (b.get('departure_time') or '').strip())
    print(f'routes: {len(routes)}  replaced: {removed}  trips added: {added}  '
          f'total buses: {len(kept)}  WBTC buses: {n_wbtc} (with a time: {timed})')


if __name__ == '__main__':
    main()
