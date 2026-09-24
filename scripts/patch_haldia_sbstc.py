# SBSTC Haldia-Kolkata flyer (Facebook, credit Bengal State Bus Routes page) fixes + new buses.
# 1) UPDATE: sbstc-haldia-kolkata-5 8:45 AM -> Haldia->Karunamoyee via Dharmatala (user-verified)
#    UPDATE: sbstc-haldia-kolkata-8 2:30 PM -> Haldia->Falta via Dharmatala, nonstop till Dharmatala
# 2) NEW: 30 buses (16 flyer rows new on Haldia side incl. 2 fixes re-purposed, 15 on Kolkata side)
# 3) BTT index card counts: Haldia +15, Kolkata (Esplanade) +15
# 4) Add 5 new route pages to sitemap.xml
# Backslash-free source; string ops only for BTT index and sitemap.

import json

DATA = 'data/busjatri_data.json'
BTT = 'bus-time-table/index.html'
SRC = 'SBSTC Haldia depot timetable (Facebook)'


def mk(id_, name, o, d, dep, route, stops):
    chain = []
    for n, st in enumerate(stops, 1):
        chain.append({'no': n, 'name': st, 'up_time': dep if n == 1 else '', 'down_time': ''})
    return {
        'id': id_, 'bus_name': name, 'reg_no': '', 'operator': 'SBSTC',
        'bus_type': 'Government - SBSTC', 'origin': o, 'destination': d,
        'departure_time': dep, 'arrival_time': '',
        'contact_number': 'Not Available !', 'depot_name': 'Haldia',
        'route': route, 'stoppages': chain, 'source': SRC,
        'total_stoppages': len(stops), 'detail_url': '',
    }


VIA_STD = ['Haldia', 'Mecheda', 'Kolaghat', 'Kolkata']
VIA_EXT = ['Haldia', 'Mecheda', 'Kolaghat', 'Kolkata']
VIA_KOL = ['Kolkata', 'Kolaghat', 'Mecheda', 'Haldia']

NEW_BUSES = [
    # --- Haldia -> Kolkata plain (join haldia-to-kolkata.html) ---
    mk('sbstc-fb-haldia-kolkata-910am', 'SBSTC Haldia-Kolkata', 'Haldia', 'Kolkata', '9:10 AM',
       'Haldia - Mecheda - Kolaghat - Kolkata', VIA_STD),
    mk('sbstc-fb-haldia-kolkata-1200pm', 'SBSTC Haldia-Kolkata', 'Haldia', 'Kolkata', '12:00 PM',
       'Haldia - Mecheda - Kolaghat - Kolkata', VIA_STD),
    mk('sbstc-fb-haldia-kolkata-1220pm', 'SBSTC Haldia-Kolkata', 'Haldia', 'Kolkata', '12:20 PM',
       'Haldia - Mecheda - Kolaghat - Kolkata', VIA_STD),
    mk('sbstc-fb-haldia-kolkata-100pm', 'SBSTC Haldia-Kolkata', 'Haldia', 'Kolkata', '1:00 PM',
       'Haldia - Mecheda - Kolaghat - Kolkata', VIA_STD),
    mk('sbstc-fb-haldia-kolkata-300pm', 'SBSTC Haldia-Kolkata', 'Haldia', 'Kolkata', '3:00 PM',
       'Haldia - Mecheda - Kolaghat - Kolkata', VIA_STD),
    mk('sbstc-fb-haldia-kolkata-430pm', 'SBSTC Haldia-Kolkata', 'Haldia', 'Kolkata', '4:30 PM',
       'Haldia - Mecheda - Kolaghat - Kolkata', VIA_STD),
    # --- extended buses (via Dharmatala, final stop beyond Kolkata) ---
    mk('sbstc-fb-haldia-chittaranjan-500am', 'SBSTC Haldia-Chittaranjan', 'Haldia', 'Chittaranjan', '5:00 AM',
       'Haldia - Mecheda - Kolaghat - Kolkata - Chittaranjan', VIA_EXT + ['Chittaranjan']),
    mk('sbstc-fb-haldia-dhamakhali-600am', 'SBSTC Haldia-Dhamakhali', 'Haldia', 'Dhamakhali', '6:00 AM',
       'Haldia - Mecheda - Kolaghat - Kolkata - Dhamakhali', VIA_EXT + ['Dhamakhali']),
    mk('sbstc-fb-haldia-karunamoyee-715am-ns', 'SBSTC Haldia-Karunamoyee (Nonstop)', 'Haldia', 'Karunamoyee', '7:15 AM',
       'Haldia - Kolkata - Karunamoyee', ['Haldia', 'Kolkata', 'Karunamoyee']),
    mk('sbstc-fb-haldia-township-asansol-930am', 'SBSTC Haldia-Asansol', 'Haldia Township', 'Asansol', '9:30 AM',
       'Haldia - Mecheda - Kolaghat - Kolkata - Asansol', ['Haldia Township', 'Mecheda', 'Kolaghat', 'Kolkata', 'Asansol']),
    mk('sbstc-fb-haldia-tarapith-1025am', 'SBSTC Haldia-Tarapith', 'Haldia', 'Tarapith', '10:25 AM',
       'Haldia - Mecheda - Kolaghat - Kolkata - Tarapith', VIA_EXT + ['Tarapith']),
    mk('sbstc-fb-haldia-kuli-1050am', 'SBSTC Haldia-Kuli', 'Haldia', 'Kuli', '10:50 AM',
       'Haldia - Mecheda - Kolaghat - Kolkata - Kuli', VIA_EXT + ['Kuli']),
    mk('sbstc-fb-haldia-barakar-1130am', 'SBSTC Haldia-Barakar', 'Haldia', 'Barakar', '11:30 AM',
       'Haldia - Mecheda - Kolaghat - Kolkata - Barakar', VIA_EXT + ['Barakar']),
    mk('sbstc-fb-haldia-township-asansol-1240pm', 'SBSTC Haldia-Asansol', 'Haldia Township', 'Asansol', '12:40 PM',
       'Haldia - Mecheda - Kolaghat - Kolkata - Asansol', ['Haldia Township', 'Mecheda', 'Kolaghat', 'Kolkata', 'Asansol']),
    mk('sbstc-fb-haldia-diamond-harbour-400pm', 'SBSTC Haldia-Diamond Harbour', 'Haldia', 'Diamond Harbour', '4:00 PM',
       'Haldia - Mecheda - Kolaghat - Kolkata - Diamond Harbour', VIA_EXT + ['Diamond Harbour']),
    # --- Kolkata -> Haldia (join kolkata-to-haldia.html) ---
    mk('sbstc-fb-kolkata-haldia-600am', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '6:00 AM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
    mk('sbstc-fb-kolkata-haldia-630am', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '6:30 AM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
    mk('sbstc-fb-kolkata-haldia-800am', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '8:00 AM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
    mk('sbstc-fb-kolkata-haldia-900am-ns', 'SBSTC Kolkata-Haldia (Nonstop)', 'Kolkata', 'Haldia', '9:00 AM',
       'Kolkata - Haldia', ['Kolkata', 'Haldia']),
    mk('sbstc-fb-kolkata-haldia-930am-ns', 'SBSTC Kolkata-Haldia (Nonstop)', 'Kolkata', 'Haldia', '9:30 AM',
       'Kolkata - Haldia', ['Kolkata', 'Haldia']),
    mk('sbstc-fb-kolkata-haldia-1000am', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '10:00 AM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
    mk('sbstc-fb-kolkata-haldia-1015am', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '10:15 AM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
    mk('sbstc-fb-kolkata-haldia-1030am', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '10:30 AM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
    mk('sbstc-fb-kolkata-haldia-1200pm', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '12:00 PM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
    mk('sbstc-fb-kolkata-haldia-100pm', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '1:00 PM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
    mk('sbstc-fb-kolkata-haldia-130pm', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '1:30 PM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
    mk('sbstc-fb-kolkata-haldia-300pm', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '3:00 PM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
    mk('sbstc-fb-kolkata-haldia-330pm-ns', 'SBSTC Kolkata-Haldia (Nonstop)', 'Kolkata', 'Haldia', '3:30 PM',
       'Kolkata - Haldia', ['Kolkata', 'Haldia']),
    mk('sbstc-fb-kolkata-haldia-400pm', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '4:00 PM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
    mk('sbstc-fb-kolkata-haldia-430pm', 'SBSTC Kolkata-Haldia', 'Kolkata', 'Haldia', '4:30 PM',
       'Kolkata - Kolaghat - Mecheda - Haldia', VIA_KOL),
]

# stand -> (card label in BTT index, count delta)
BTT_CARDS = [
    ('Haldia', 15),
    ('Kolkata (Esplanade)', 15),
]

# new route pages this patcher creates (must be added to sitemap.xml)
SITEMAP_NEW = [
    'haldia-to-dhamakhali',
    'haldia-to-tarapith',
    'haldia-to-kuli',
    'haldia-to-falta',
    'haldia-to-diamond-harbour',
]


def chain_of(stops, dep):
    out = []
    for n, st in enumerate(stops, 1):
        out.append({'no': n, 'name': st, 'up_time': dep if n == 1 else '', 'down_time': ''})
    return out


def patch_data():
    with open(DATA, encoding='utf-8') as fh:
        d = json.load(fh)
    buses = d['buses']
    ids = set(b.get('id') for b in buses)

    updates = {
        'sbstc-haldia-kolkata-5': {
            'check': ('8:45 AM', 'Kolkata'),
            'bus_name': 'SBSTC Haldia-Karunamoyee',
            'destination': 'Karunamoyee',
            'route': 'Haldia - Mecheda - Kolaghat - Kolkata - Karunamoyee',
            'stops': ['Haldia', 'Mecheda', 'Kolaghat', 'Kolkata', 'Karunamoyee'],
        },
        'sbstc-haldia-kolkata-8': {
            'check': ('2:30 PM', 'Kolkata'),
            'bus_name': 'SBSTC Haldia-Falta (Nonstop)',
            'destination': 'Falta',
            'route': 'Haldia - Kolkata - Falta',
            'stops': ['Haldia', 'Kolkata', 'Falta'],
        },
    }
    nupd = 0
    for b in buses:
        uid = b.get('id')
        if uid in updates:
            u = updates[uid]
            t, dst = u['check']
            if b.get('departure_time') == t and (b.get('destination') or '').strip() == dst:
                b['bus_name'] = u['bus_name']
                b['destination'] = u['destination']
                b['route'] = u['route']
                b['stoppages'] = chain_of(u['stops'], t)
                b['total_stoppages'] = len(u['stops'])
                if 'fare' in b:
                    b['fare'] = ''
                nupd += 1
    print('existing bus updates applied:', nupd)

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
