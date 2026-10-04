# SBSTC via-stop fill.
# Reads data/sbstc_via_map.json (curated corridor -> via stops) and inserts the via
# stops into SBSTC buses in data/busjatri_data.json that currently carry no via
# (origin + destination only).  Nothing is guessed: every via in the map comes from
#   - RailYatri SBSTC operator route names (e.g. "Sbstc Karunamoyee Bankura Via Durgapur")
#   - a user-verified route list
#   - or is derived from SBSTC buses that already carry the same corridor's stops
# Idempotent: buses that already have >=3 stoppages are left untouched.

import json, re

DATA = 'data/busjatri_data.json'
VIAMAP = 'data/sbstc_via_map.json'


def norm(s):
    s = str(s).strip().lower()
    s = re.sub(r'\(.*?\)', '', s)
    for t in ['bus terminus', 'bus stand', 'bus depot', ' depot', ' station', ' halt', ' more', ' bypass']:
        s = s.replace(t, '')
    return re.sub(r'\s+', ' ', s).strip()


def is_sbstc(b):
    s = (b.get('bus_name', '') + ' ' + b.get('operator', '') + ' ' + b.get('route', '') + ' ' + str(b.get('source', ''))).lower()
    return 'sbstc' in s or 'south bengal' in s


def main():
    d = json.load(open(DATA))
    vmap = {f"{c['a']}|{c['b']}": c for c in json.load(open(VIAMAP))['corridors']}

    changed = 0
    touched = set()
    for b in d['buses']:
        if not is_sbstc(b):
            continue
        if len(b.get('stoppages', [])) > 2:
            continue
        o, dd = norm(b['origin']), norm(b['destination'])
        rec = vmap.get('|'.join(sorted([o, dd])))
        if not rec:
            continue
        via = list(rec['via'])
        if o != rec['first']:
            via = list(reversed(via))
        via = [v for v in via if norm(v) not in (o, dd)]
        if not via:
            continue
        chain = [{'no': 1, 'name': b['origin'], 'up_time': b.get('departure_time', ''), 'down_time': ''}]
        for i, v in enumerate(via, 2):
            chain.append({'no': i, 'name': v, 'up_time': '', 'down_time': ''})
        chain.append({'no': len(chain) + 1, 'name': b['destination'], 'up_time': '', 'down_time': ''})
        b['stoppages'] = chain
        b['total_stoppages'] = len(chain)
        b['via_source'] = rec['source']
        changed += 1
        touched.add('|'.join(sorted([o, dd])))

    json.dump(d, open(DATA, 'w'), ensure_ascii=False)
    print('SBSTC buses given via stops:', changed)
    print('corridors touched:', len(touched))


if __name__ == '__main__':
    main()
