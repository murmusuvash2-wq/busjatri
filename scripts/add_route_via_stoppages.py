#!/usr/bin/env python3
"""add_route_via_stoppages.py — fill in the missing via-stoppages on the four
highest-impression route pairs.

Those pages currently carry only two "stops" (origin > destination), which is why
they read as thin. data/route_via_stoppages.json holds the verified major
stoppages for each pair; this writes them onto every bus on that pair — the
forward chain for the from->to direction and the reversed chain for the return.
Departure times are untouched.

Idempotent: a bus whose stoppage list already equals the chain is left alone.
"""

import json
import re

DATA_PATH = 'data/busjatri_data.json'
VIA_PATH = 'data/route_via_stoppages.json'


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())


def chain_stops(names, departure_time):
    out = []
    for i, name in enumerate(names):
        out.append({'no': i + 1, 'name': name,
                    'up_time': departure_time if i == 0 else '',
                    'down_time': ''})
    return out


def main():
    via = json.load(open(VIA_PATH, encoding='utf-8'))['routes']
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    was_list = isinstance(data['buses'], list)
    buses = data['buses'] if was_list else list(data['buses'].values())

    changed = 0
    for r in via:
        fwd, rev = r['forward'], list(reversed(r['forward']))
        for b in buses:
            o, d = norm(b.get('origin')), norm(b.get('destination'))
            if o == norm(r['from']) and d == norm(r['to']):
                names = fwd
            elif o == norm(r['to']) and d == norm(r['from']):
                names = rev
            else:
                continue
            cur = [(s.get('name') if isinstance(s, dict) else s) for s in (b.get('stoppages') or [])]
            if [norm(x) for x in cur] == [norm(x) for x in names]:
                continue
            b['stoppages'] = chain_stops(names, b.get('departure_time') or '')
            b['total_stoppages'] = len(names)
            if r.get('source'):
                b['via_source'] = r['source']
            if r.get('variant_note'):
                b['via_note'] = r['variant_note']
            changed += 1

    data['buses'] = buses if was_list else {b['id']: b for b in buses}
    json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'buses given via-stoppages: {changed}')


if __name__ == '__main__':
    main()
