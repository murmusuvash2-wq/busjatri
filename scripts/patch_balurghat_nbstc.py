# NBSTC Balurghat terminus board (user photo, 2026-09-26).
# Adds 36 verified departures read off the terminus departure board photo.
# Only times confirmed across multiple independent reads were added.
# Intentionally NOT added (unclear on the photo): Rocket service, Baharampur,
# Medinipur, some Malda/Siliguri slots, Bangladesh routes.

import json

DATA = 'data/busjatri_data.json'
SRC = 'NBSTC Balurghat terminus timetable (user-verified photo)'


def mk(id_, name, d, dep, route, stops, btype='Government'):
    chain = []
    for n, st in enumerate(stops, 1):
        chain.append({'no': n, 'name': st, 'up_time': dep if n == 1 else '', 'down_time': ''})
    return {
        'id': id_, 'bus_name': name, 'reg_no': '', 'operator': 'NBSTC',
        'bus_type': btype, 'origin': 'Balurghat', 'destination': d,
        'departure_time': dep, 'arrival_time': '',
        'contact_number': 'Not Available !', 'depot_name': 'Balurghat',
        'route': route, 'stoppages': chain, 'source': SRC,
        'total_stoppages': len(stops), 'detail_url': '',
    }


NEW_BUSES = [
    # --- Kolkata (3 + Volvo AC via Digha, Tue/Sat) ---
    mk('nbstc-blg-kolkata-300am', 'NBSTC Balurghat-Kolkata', 'Kolkata', '3:00 AM',
       'Balurghat - Kolkata', ['Balurghat', 'Kolkata']),
    mk('nbstc-blg-kolkata-400am', 'NBSTC Balurghat-Kolkata', 'Kolkata', '4:00 AM',
       'Balurghat - Kolkata', ['Balurghat', 'Kolkata']),
    mk('nbstc-blg-kolkata-440am', 'NBSTC Balurghat-Kolkata', 'Kolkata', '4:40 AM',
       'Balurghat - Kolkata', ['Balurghat', 'Kolkata']),
    mk('nbstc-blg-kolkata-volvo-600am', 'NBSTC Balurghat-Kolkata Volvo AC (via Digha)', 'Kolkata', '6:00 AM',
       'Balurghat - Digha - Kolkata', ['Balurghat', 'Digha', 'Kolkata'], btype='Government - AC'),
    # --- Siliguri ---
    mk('nbstc-blg-siliguri-500am', 'NBSTC Balurghat-Siliguri', 'Siliguri', '5:00 AM',
       'Balurghat - Siliguri', ['Balurghat', 'Siliguri']),
    mk('nbstc-blg-siliguri-800am', 'NBSTC Balurghat-Siliguri', 'Siliguri', '8:00 AM',
       'Balurghat - Siliguri', ['Balurghat', 'Siliguri']),
    mk('nbstc-blg-siliguri-850am', 'NBSTC Balurghat-Siliguri', 'Siliguri', '8:50 AM',
       'Balurghat - Siliguri', ['Balurghat', 'Siliguri']),
    # --- Malda ---
    mk('nbstc-blg-malda-510am', 'NBSTC Balurghat-Malda', 'Malda', '5:10 AM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-800am', 'NBSTC Balurghat-Malda', 'Malda', '8:00 AM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-840am', 'NBSTC Balurghat-Malda', 'Malda', '8:40 AM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-900am', 'NBSTC Balurghat-Malda', 'Malda', '9:00 AM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-1000am', 'NBSTC Balurghat-Malda', 'Malda', '10:00 AM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-1010am', 'NBSTC Balurghat-Malda', 'Malda', '10:10 AM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-1040am', 'NBSTC Balurghat-Malda', 'Malda', '10:40 AM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-1100am', 'NBSTC Balurghat-Malda', 'Malda', '11:00 AM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-1210pm', 'NBSTC Balurghat-Malda', 'Malda', '12:10 PM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-130pm', 'NBSTC Balurghat-Malda', 'Malda', '1:30 PM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-320pm', 'NBSTC Balurghat-Malda', 'Malda', '3:20 PM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-340pm', 'NBSTC Balurghat-Malda', 'Malda', '3:40 PM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-400pm', 'NBSTC Balurghat-Malda', 'Malda', '4:00 PM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-410pm', 'NBSTC Balurghat-Malda', 'Malda', '4:10 PM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    mk('nbstc-blg-malda-440pm', 'NBSTC Balurghat-Malda', 'Malda', '4:40 PM',
       'Balurghat - Malda', ['Balurghat', 'Malda']),
    # --- Cooch Behar ---
    mk('nbstc-blg-coochbehar-520am', 'NBSTC Balurghat-Cooch Behar', 'Cooch Behar', '5:20 AM',
       'Balurghat - Cooch Behar', ['Balurghat', 'Cooch Behar']),
    # --- Raiganj ---
    mk('nbstc-blg-raiganj-810am', 'NBSTC Balurghat-Raiganj', 'Raiganj', '8:10 AM',
       'Balurghat - Raiganj', ['Balurghat', 'Raiganj']),
    mk('nbstc-blg-raiganj-930am', 'NBSTC Balurghat-Raiganj', 'Raiganj', '9:30 AM',
       'Balurghat - Raiganj', ['Balurghat', 'Raiganj']),
    mk('nbstc-blg-raiganj-1030am', 'NBSTC Balurghat-Raiganj', 'Raiganj', '10:30 AM',
       'Balurghat - Raiganj', ['Balurghat', 'Raiganj']),
    mk('nbstc-blg-raiganj-1110am', 'NBSTC Balurghat-Raiganj', 'Raiganj', '11:10 AM',
       'Balurghat - Raiganj', ['Balurghat', 'Raiganj']),
    mk('nbstc-blg-raiganj-1200pm', 'NBSTC Balurghat-Raiganj', 'Raiganj', '12:00 PM',
       'Balurghat - Raiganj', ['Balurghat', 'Raiganj']),
    mk('nbstc-blg-raiganj-140pm', 'NBSTC Balurghat-Raiganj', 'Raiganj', '1:40 PM',
       'Balurghat - Raiganj', ['Balurghat', 'Raiganj']),
    # --- Ranaghat ---
    mk('nbstc-blg-ranaghat-600am', 'NBSTC Balurghat-Ranaghat', 'Ranaghat', '6:00 AM',
       'Balurghat - Ranaghat', ['Balurghat', 'Ranaghat']),
    # --- Farakka ---
    mk('nbstc-blg-farakka-1240pm', 'NBSTC Balurghat-Farakka', 'Farakka', '12:40 PM',
       'Balurghat - Farakka', ['Balurghat', 'Farakka']),
    mk('nbstc-blg-farakka-1250pm', 'NBSTC Balurghat-Farakka', 'Farakka', '12:50 PM',
       'Balurghat - Farakka', ['Balurghat', 'Farakka']),
    mk('nbstc-blg-farakka-100pm', 'NBSTC Balurghat-Farakka', 'Farakka', '1:00 PM',
       'Balurghat - Farakka', ['Balurghat', 'Farakka']),
    mk('nbstc-blg-farakka-150pm', 'NBSTC Balurghat-Farakka', 'Farakka', '1:50 PM',
       'Balurghat - Farakka', ['Balurghat', 'Farakka']),
    mk('nbstc-blg-farakka-200pm', 'NBSTC Balurghat-Farakka', 'Farakka', '2:00 PM',
       'Balurghat - Farakka', ['Balurghat', 'Farakka']),
    # --- Jalpaiguri ---
    mk('nbstc-blg-jalpaiguri-900am', 'NBSTC Balurghat-Jalpaiguri', 'Jalpaiguri', '9:00 AM',
       'Balurghat - Jalpaiguri', ['Balurghat', 'Jalpaiguri']),
]

SITEMAP_NEW = [
    'balurghat-to-kolkata',
    'balurghat-to-siliguri',
    'balurghat-to-malda',
    'balurghat-to-cooch-behar',
    'balurghat-to-raiganj',
    'balurghat-to-ranaghat',
    'balurghat-to-farakka',
    'balurghat-to-jalpaiguri',
]


def patch_data():
    with open(DATA, encoding='utf-8') as fh:
        d = json.load(fh)
    buses = d['buses']
    ids = set(b.get('id') for b in buses)
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


def patch_sitemap():
    with open('sitemap.xml', encoding='utf-8') as fh:
        s = fh.read()
    today = '2026-09-26'
    added = 0
    for slugname in SITEMAP_NEW:
        loc = 'https://busjatri.in/bus-time-table/' + slugname + '.html'
        if loc in s:
            continue
        entry = ('<url><loc>' + loc + '</loc><lastmod>' + today +
                 '</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>')
        s = s.replace('</urlset>', entry + '</urlset>')
        added += 1
    with open('sitemap.xml', 'w', encoding='utf-8') as fh:
        fh.write(s)
    print('sitemap entries added:', added)


if __name__ == '__main__':
    n = patch_data()
    patch_sitemap()
    assert n == 36, 'expected 36 adds, got %d' % n
    print('OK')
