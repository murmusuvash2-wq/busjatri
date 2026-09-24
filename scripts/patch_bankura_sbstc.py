# SBSTC Bankura depot flyer (Facebook) fixes + new buses.
# 1) FIX: Bankura->Chittaranjan 6:20 AM -> 6:25 AM (bussathi record)
#    FIX: Bankura->Karunamoyee 12:10 PM -> 12:00 PM + rename (NH 1)
#    RENAME: Karunamoyee 1:00 PM -> (NH 2), 2:15 PM -> (NH 3)
# 2) NEW: 19 buses (Kolkata x2, Karunamoyee x3, Ramganj, Kabilepur, Malda,
#    Lalgola, Durgapur x5, Durgapur City Centre x3, Siliguri)
# 3) BTT index card count: Bankura +19 (99 -> 118)
# 4) Add 6 new route pages to sitemap.xml
# Backslash-free source; string ops only for BTT index and sitemap.

import json

DATA = 'data/busjatri_data.json'
BTT = 'bus-time-table/index.html'
SRC = 'SBSTC Bankura depot timetable (Facebook)'


def mk(id_, name, o, d, dep, route, stops):
    chain = []
    for n, st in enumerate(stops, 1):
        chain.append({'no': n, 'name': st, 'up_time': dep if n == 1 else '', 'down_time': ''})
    return {
        'id': id_, 'bus_name': name, 'reg_no': '', 'operator': 'SBSTC',
        'bus_type': 'Government - SBSTC', 'origin': o, 'destination': d,
        'departure_time': dep, 'arrival_time': '',
        'contact_number': 'Not Available !', 'depot_name': 'Bankura',
        'route': route, 'stoppages': chain, 'source': SRC,
        'total_stoppages': len(stops), 'detail_url': '',
    }


NEW_BUSES = [
    # --- Kolkata (join bankura-to-kolkata.html) ---
    mk('sbstc-fb-bankura-kolkata-500am', 'SBSTC Bankura-Kolkata', 'Bankura', 'Kolkata', '5:00 AM',
       'Bankura - Kolkata', ['Bankura', 'Kolkata']),
    mk('sbstc-fb-bankura-kolkata-450am-arambag', 'SBSTC Bankura-Kolkata (via Arambag)', 'Bankura', 'Kolkata', '4:50 AM',
       'Bankura - Arambag - Kolkata', ['Bankura', 'Arambag', 'Kolkata']),
    # --- Karunamoyee (join bankura-to-karunamoyee.html) ---
    mk('sbstc-fb-bankura-karunamoyee-515am-ac', 'SBSTC Bankura-Karunamoyee (AC)', 'Bankura', 'Karunamoyee', '5:15 AM',
       'Bankura - Karunamoyee', ['Bankura', 'Karunamoyee']),
    mk('sbstc-fb-bankura-karunamoyee-1015am', 'SBSTC Bankura-Karunamoyee', 'Bankura', 'Karunamoyee', '10:15 AM',
       'Bankura - Karunamoyee', ['Bankura', 'Karunamoyee']),
    mk('sbstc-fb-bankura-karunamoyee-320pm-ac', 'SBSTC Bankura-Karunamoyee (AC)', 'Bankura', 'Karunamoyee', '3:20 PM',
       'Bankura - Karunamoyee', ['Bankura', 'Karunamoyee']),
    # --- new destinations ---
    mk('sbstc-fb-bankura-malda-515am', 'SBSTC Bankura-Malda', 'Bankura', 'Malda', '5:15 AM',
       'Bankura - Malda', ['Bankura', 'Malda']),
    mk('sbstc-fb-bankura-ramganj-615am', 'SBSTC Bankura-Ramganj', 'Bankura', 'Ramganj', '6:15 AM',
       'Bankura - Ramganj', ['Bankura', 'Ramganj']),
    mk('sbstc-fb-bankura-kabilepur-830am', 'SBSTC Bankura-Kabilepur', 'Bankura', 'Kabilepur', '8:30 AM',
       'Bankura - Kabilepur', ['Bankura', 'Kabilepur']),
    mk('sbstc-fb-bankura-lalgola-900am', 'SBSTC Bankura-Lalgola', 'Bankura', 'Lalgola', '9:00 AM',
       'Bankura - Lalgola', ['Bankura', 'Lalgola']),
    mk('sbstc-fb-bankura-siliguri-500pm', 'SBSTC Bankura-Siliguri', 'Bankura', 'Siliguri', '5:00 PM',
       'Bankura - Siliguri', ['Bankura', 'Siliguri']),
    # --- Durgapur (new page bankura-to-durgapur.html) ---
    mk('sbstc-fb-bankura-durgapur-640am', 'SBSTC Bankura-Durgapur', 'Bankura', 'Durgapur', '6:40 AM',
       'Bankura - Durgapur', ['Bankura', 'Durgapur']),
    mk('sbstc-fb-bankura-durgapur-715am', 'SBSTC Bankura-Durgapur', 'Bankura', 'Durgapur', '7:15 AM',
       'Bankura - Durgapur', ['Bankura', 'Durgapur']),
    mk('sbstc-fb-bankura-durgapur-740am-ac', 'SBSTC Bankura-Durgapur (AC)', 'Bankura', 'Durgapur', '7:40 AM',
       'Bankura - Durgapur', ['Bankura', 'Durgapur']),
    mk('sbstc-fb-bankura-durgapur-315pm', 'SBSTC Bankura-Durgapur', 'Bankura', 'Durgapur', '3:15 PM',
       'Bankura - Durgapur', ['Bankura', 'Durgapur']),
    mk('sbstc-fb-bankura-durgapur-400pm-ac', 'SBSTC Bankura-Durgapur (AC)', 'Bankura', 'Durgapur', '4:00 PM',
       'Bankura - Durgapur', ['Bankura', 'Durgapur']),
    mk('sbstc-fb-bankura-durgapur-430pm', 'SBSTC Bankura-Durgapur', 'Bankura', 'Durgapur', '4:30 PM',
       'Bankura - Durgapur', ['Bankura', 'Durgapur']),
    # --- Durgapur City Centre (new page bankura-to-durgapur-city-centre.html) ---
    mk('sbstc-fb-bankura-city-centre-600am', 'SBSTC Bankura-City Centre', 'Bankura', 'Durgapur City Centre', '6:00 AM',
       'Bankura - Durgapur City Centre', ['Bankura', 'Durgapur City Centre']),
    mk('sbstc-fb-bankura-city-centre-815am-via-mejia', 'SBSTC Bankura-City Centre (via Mejia)', 'Bankura', 'Durgapur City Centre', '8:15 AM',
       'Bankura - Mejia - Asansol - City Centre', ['Bankura', 'Mejia', 'Asansol', 'Durgapur City Centre']),
    mk('sbstc-fb-bankura-city-centre-130pm', 'SBSTC Bankura-City Centre', 'Bankura', 'Durgapur City Centre', '1:30 PM',
       'Bankura - Durgapur City Centre', ['Bankura', 'Durgapur City Centre']),
]

# stand -> (card label in BTT index, count delta)
BTT_CARDS = [
    ('Bankura', 19),
]

# new route pages this patcher creates (must be added to sitemap.xml)
SITEMAP_NEW = [
    'bankura-to-malda',
    'bankura-to-ramganj',
    'bankura-to-kabilepur',
    'bankura-to-lalgola',
    'bankura-to-durgapur',
    'bankura-to-durgapur-city-centre',
]


def patch_data():
    with open(DATA, encoding='utf-8') as fh:
        d = json.load(fh)
    buses = d['buses']
    ids = set(b.get('id') for b in buses)

    # time fixes + renames: (origin, destination, old_time, new_time, new_name)
    fixes = [
        ('Bankura', 'Chittaranjan', '6:20 AM', '6:25 AM', None),
        ('Bankura', 'Karunamoyee', '12:10 PM', '12:00 PM', 'SBSTC Bankura-Karunamoyee (NH 1)'),
        ('Bankura', 'Karunamoyee', '1:00 PM', '1:00 PM', 'SBSTC Bankura-Karunamoyee (NH 2)'),
        ('Bankura', 'Karunamoyee', '2:15 PM', '2:15 PM', 'SBSTC Bankura-Karunamoyee (NH 3)'),
    ]
    nfix = 0
    for b in buses:
        o = (b.get('origin') or '').strip()
        dst = (b.get('destination') or '').strip()
        for fo, fd, ft, fnt, fname in fixes:
            if o == fo and dst == fd and b.get('departure_time') == ft:
                b['departure_time'] = fnt
                if fname:
                    b['bus_name'] = fname
                nfix += 1
    print('fixes applied:', nfix)

    added = 0
    for nb in NEW_BUSES:
        if nb['id'] in ids:
            continue
        buses.append(nb)
        added += 1
    print('new buses added:', added)

    with open(DATA, 'w', encoding='utf-8') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    return added


def patch_btt():
    with open(BTT, encoding='utf-8') as fh:
        s = fh.read()
    for label, delta in BTT_CARDS:
        i = s.find('>' + label)
        if i < 0:
            print('BTT card not found:', label)
            continue
        mk = '<div class="smeta"><b>'
        j = s.find(mk, i)
        if j < 0:
            print('smeta not found for', label)
            continue
        k = s.find('</b>', j)
        old = s[j + len(mk):k]
        if old.isdigit():
            new = str(int(old) + delta)
            s = s[:j + len(mk)] + new + s[k:]
            print('btt card', label, ':', old, '->', new)
        else:
            print('btt card', label, ': unexpected count', old)
    with open(BTT, 'w', encoding='utf-8') as fh:
        fh.write(s)


def patch_sitemap():
    with open('sitemap.xml', encoding='utf-8') as fh:
        s = fh.read()
    today = '2026-09-24'
    added = 0
    for slugname in SITEMAP_NEW:
        loc = 'https://busjatri.in/bus-time-table/' + slugname + '.html'
        if loc in s:
            continue
        entry = ('<url><loc>' + loc + '</loc><lastmod>' + today +
                 '</lastmod><priority>0.7</priority></url>')
        k = s.find('</urlset>')
        if k < 0:
            print('sitemap: urlset close not found')
            continue
        s = s[:k] + entry + s[k:]
        added += 1
    if added:
        with open('sitemap.xml', 'w', encoding='utf-8') as fh:
            fh.write(s)
    print('sitemap urls added:', added)


def main():
    added = patch_data()
    patch_btt()
    patch_sitemap()
    print('done. new buses:', added)


if __name__ == '__main__':
    main()
