#!/usr/bin/env python3
"""import_wbtc_official.py — apply the official WBTC route lists.

Two official lists, both applied here (each optional):

  data/wbtc_official_longdistance.csv  — 30 long-distance services
      Route_Name, Origin, Destination, Bus_Type, Departure_Times, Via_Stoppages
  data/wbtc_official_suburban.csv      — 42 suburban / depot services
      Sl_No, Route_Name, Origin, Destination, Bus_Type, Departure_Times,
      Approx_Fare_INR, Exhaustive_Via_Stoppages

Background: our WBTC data was a bare route list from kolkata-travel-router —
956 buses, 944 of them with NO departure time, so every WBTC route page showed
"Time N/A". These lists supply departure times, the full via-stoppage chain and
(second list) the approximate fare.

For a route covered by either list we drop our WBTC buses and write one bus per
listed departure time. Where both lists cover a route their times are merged
(union) so neither list's services are lost. Routes not covered are untouched.
Idempotent.
"""

import csv
import json
import re
import unicodedata
from collections import Counter

DATA_PATH = 'data/busjatri_data.json'
LISTS = [
    'data/wbtc_official_longdistance.csv',
    'data/wbtc_official_suburban.csv',
]

# the lists name the Esplanade depot as "Kolkata (Esplanade)" and the city drop
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
                 ('bardhaman', 'burdwan'), ('krishnagar', 'krishnanagar'),
                 ('belgachia', 'shyambazar')]:
        s = s.replace(a, b)
    return s or 'kolkata'


def clean_time(t):
    t = re.sub(r'\(.*?\)', '', t).strip()          # drop "(Daily)" / "(Fri/Sat)"
    t = re.sub(r'^0(\d:)', r'\1', t)               # 05:40 AM -> 5:40 AM
    return t


def tmin(t):
    m = re.match(r'(\d{1,2}):(\d{2})\s*([AP]M)', (t or '').upper().strip())
    if not m:
        return 24 * 60
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap == 'PM' and h != 12:
        h += 12
    if ap == 'AM' and h == 12:
        h = 0
    return h * 60 + mi


def parse_via(s):
    return [x.strip() for x in (s or '').split('>>') if x.strip()]


def clean_fare(s):
    s = (s or '').strip()
    if not s:
        return ''
    s = re.sub(r'\s*-\s*', '-', s)
    return f'Rs. {s}'


def is_wbtc(b):
    return ((b.get('operator') or '').lower() in ('wbtc', 'wbtc (ctc)')
            or 'wbtc' in (b.get('source') or '').lower()
            or 'WBTC' in (b.get('bus_type') or '')
            or 'CSTC' in (b.get('bus_type') or ''))


def load_routes():
    """route key -> {origin, destination, times:set, via:list, fare:str, types:set}"""
    routes = {}
    for path in LISTS:
        try:
            rows = list(csv.DictReader(open(path, encoding='utf-8')))
        except FileNotFoundError:
            continue
        for r in rows:
            o = ORIGIN_FIX.get((r.get('Origin') or '').strip().lower(), (r.get('Origin') or '').strip())
            d = DEST_FIX.get((r.get('Destination') or '').strip().lower(), (r.get('Destination') or '').strip())
            if not o or not d:
                continue
            key = norm(o) + '|' + norm(d)
            via = parse_via(r.get('Exhaustive_Via_Stoppages_List') or r.get('Exhaustive_Via_Stoppages'))
            fare = clean_fare(r.get('Approx_Fare_INR'))
            e = routes.setdefault(key, {'origin': o, 'destination': d, 'times': [],
                                        'via': [], 'fare': '', 'types': []})
            for t in (clean_time(x) for x in (r.get('Departure_Times') or '').split(',')):
                if t and t not in e['times']:
                    e['times'].append(t)
            if len(via) > len(e['via']):
                e['via'] = via
            if fare and not e['fare']:
                e['fare'] = fare
            bt = (r.get('Bus_Type') or '').strip()
            if bt and bt not in e['types']:
                e['types'].append(bt)
    return routes


def main():
    routes = load_routes()
    covered = set(routes)
    print(f'routes in the official lists: {len(routes)}')

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
    for key, e in routes.items():
        o, d, via = e['origin'], e['destination'], e['via']
        btype = ' / '.join(e['types'])
        for tm in sorted(e['times'], key=tmin):
            seen[(slug(o), slug(d))] += 1
            n = seen[(slug(o), slug(d))]
            stops = [{'no': i + 1, 'name': name,
                      'up_time': tm if i == 0 else '', 'down_time': ''}
                     for i, name in enumerate(via or [o, d])]
            rec = {
                'id': f'wbtc-official-{slug(o)}-{slug(d)}-{n}',
                'bus_name': f'WBTC {o}-{d}', 'reg_no': '', 'operator': 'WBTC',
                'bus_type': f'Government - {btype}' if btype else 'Government',
                'origin': o, 'destination': d, 'departure_time': tm, 'arrival_time': '',
                'contact_number': 'Not Available !', 'depot_name': '',
                'route': ' - '.join(via) if via else f'{o} - {d}',
                'stoppages': stops, 'total_stoppages': len(stops),
                'source': 'WBTC official route list', 'detail_url': '',
            }
            if e['fare']:
                rec['fare'] = e['fare']
            kept.append(rec)
            added += 1

    data['buses'] = kept if was_list else {b['id']: b for b in kept}
    data.setdefault('meta', {})['total_buses'] = len(kept)
    json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    w = [b for b in kept if is_wbtc(b)]
    timed = [b for b in w if (b.get('departure_time') or '').strip()]
    fares = [b for b in w if (b.get('fare') or '').strip()]
    print(f'replaced: {removed}  trips added: {added}  total buses: {len(kept)}  '
          f'WBTC: {len(w)} (with a time: {len(timed)}, with a fare: {len(fares)})')


if __name__ == '__main__':
    main()
