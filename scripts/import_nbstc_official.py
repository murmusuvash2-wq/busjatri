#!/usr/bin/env python3
"""import_nbstc_official.py — apply the official NBSTC (Cooch Behar) timetable.

Source: data/nbstc_cooch_behar_official.csv — the official NBSTC route list for
the Cooch Behar region (Sl No., From, To, Via, Time), 459 trips.

Cross-check against our data showed we had 178 trips right, 236 missing and 45
with a wrong time. For every route this list covers, our NBSTC buses are replaced
by the official trips (origin / destination / via / time straight from the list).
Routes the list does not cover are left untouched.

Idempotent: re-running produces the same result.
"""

import csv
import json
import os
import re
import unicodedata
from collections import Counter

CSV_PATH = 'data/nbstc_cooch_behar_official.csv'
DATA_PATH = 'data/busjatri_data.json'


def norm(s):
    s = (s or '').lower()
    s = re.sub(r'\(.*?\)', '', s)
    s = re.sub(r'\bnon-?ac\b|\bac\b|\brocket\b', '', s)
    s = re.sub(r'\bn/?o\b', '', s)
    s = re.sub(r'[^a-z0-9]+', '', s)
    for a, b in [('berhampur', 'berhampore'), ('krishnagar', 'krishnanagar'),
                 ('siliguricourtmore', 'siliguri'), ('siligurinjp', 'siliguri'),
                 ('siligurimm', 'siliguri'), ('njpgbmm', 'siliguri'), ('njp', 'siliguri'),
                 ('malbazardepot', 'malbazar'), ('tncbt', 'siliguri'),
                 ('shabolda', 'shibaldaha')]:
        s = s.replace(a, b)
    s = re.sub(r'panitanki\d*', 'panitanki', s)
    s = re.sub(r'city\d*', 'city', s)
    s = re.sub(r'(kaliyaganj|kaliaganj)', 'kaliyaganj', s)
    s = re.sub(r'(gazole|gazal)', 'gazole', s)
    return s


def slug(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-')


def norm_time(t):
    return re.sub(r'(?i)noon', 'PM', (t or '').strip())


def read_official():
    trips = []
    with open(CSV_PATH, encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 5 or not row[0].strip().isdigit():
                continue
            trips.append({
                'from': row[1].strip(), 'to': row[2].strip(),
                'via': row[3].strip(), 'time': norm_time(row[4]),
            })
    return trips


def is_nbstc(b):
    return ((b.get('operator') or '').lower() == 'nbstc'
            or 'nbstc' in (b.get('source') or '').lower()
            or 'NBSTC' in (b.get('bus_type') or ''))


def main():
    trips = read_official()
    covered = {norm(t['from']) + '|' + norm(t['to']) for t in trips}

    d = json.load(open(DATA_PATH, encoding='utf-8'))
    was_list = isinstance(d['buses'], list)
    buses = d['buses'] if was_list else list(d['buses'].values())

    kept, removed = [], 0
    for b in buses:
        if is_nbstc(b) and (norm(b.get('origin')) + '|' + norm(b.get('destination'))) in covered:
            removed += 1
            continue
        kept.append(b)

    seen = Counter()
    for t in trips:
        o, dd, via, tm = t['from'], t['to'], t['via'], t['time']
        seen[(slug(o), slug(dd))] += 1
        n = seen[(slug(o), slug(dd))]
        stops = [{'no': 1, 'name': o, 'up_time': tm, 'down_time': ''}]
        if via:
            stops.append({'no': 2, 'name': via, 'up_time': '', 'down_time': ''})
        stops.append({'no': len(stops) + 1, 'name': dd, 'up_time': '', 'down_time': ''})
        kept.append({
            'id': f'nbstc-official-{slug(o)}-{slug(dd)}-{n}',
            'bus_name': f'NBSTC {o}-{dd}', 'reg_no': '', 'operator': 'NBSTC',
            'bus_type': 'Government', 'origin': o, 'destination': dd,
            'departure_time': tm, 'arrival_time': '', 'contact_number': 'Not Available !',
            'depot_name': 'Cooch Behar',
            'route': f'{o} - {via} - {dd}' if via else f'{o} - {dd}',
            'stoppages': stops, 'total_stoppages': len(stops),
            'source': 'NBSTC official (Cooch Behar) PDF', 'detail_url': '',
        })

    d['buses'] = kept if was_list else {b['id']: b for b in kept}
    d.setdefault('meta', {})['total_buses'] = len(kept)
    json.dump(d, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    nbstc = sum(1 for b in kept if is_nbstc(b))
    print(f'official trips: {len(trips)}  replaced: {removed}  '
          f'total buses: {len(kept)}  NBSTC buses: {nbstc}')


if __name__ == '__main__':
    main()
