# SBSTC Medinipur depot flyer fixes (Facebook, credit Sourav Mahata) + WBTC Habra/Barasat section.
# 1) FIX: Midnapur->Karunamoyee 6:30 AM -> 6:50 AM (zoom-verified)
#    FIX: Midnapur->Kolkata 5:50 AM -> 5:10 AM (zoom-verified)
# 2) NEW: 30 buses (times from flyer, via stoppages added)
# 3) BTT index card counts: Medinipur +10, Kolkata +14, Habra +4, Barasat +2
# Backslash-free source; string ops only for BTT index.

import json

DATA = 'data/busjatri_data.json'
BTT = 'bus-time-table/index.html'
SRC_S = 'SBSTC Medinipur depot timetable (Facebook)'
SRC_W = 'WBTC Medinipur route timetable (Facebook)'


def mk(id_, name, operator, o, d, dep, route, stops, src, bustype):
    chain = []
    for n, st in enumerate(stops, 1):
        chain.append({'no': n, 'name': st, 'up_time': dep if n == 1 else '', 'down_time': ''})
    return {
        'id': id_, 'bus_name': name, 'reg_no': '', 'operator': operator,
        'bus_type': bustype, 'origin': o, 'destination': d,
        'departure_time': dep, 'arrival_time': '',
        'contact_number': 'Not Available !', 'depot_name': 'Midnapur',
        'route': route, 'stoppages': chain, 'source': src,
        'total_stoppages': len(stops), 'detail_url': '',
    }


NEW_BUSES = [
    # --- Midnapur -> Kolkata (join midnapur-to-kolkata.html) ---
    mk('sbstc-fb-midnapur-kolkata-530am', 'SBSTC Midnapur-Kolkata', 'SBSTC', 'Midnapur', 'Kolkata', '5:30 AM',
       'Midnapur - Kolaghat - Kolkata', ['Midnapur', 'Kolaghat', 'Kolkata'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-midnapur-kolkata-730am-ac', 'SBSTC Midnapur-Kolkata (AC)', 'SBSTC', 'Midnapur', 'Kolkata', '7:30 AM',
       'Midnapur - Kolaghat - Kolkata', ['Midnapur', 'Kolaghat', 'Kolkata'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-midnapur-kolkata-800am-ac', 'SBSTC Midnapur-Kolkata (AC)', 'SBSTC', 'Midnapur', 'Kolkata', '8:00 AM',
       'Midnapur - Kolaghat - Kolkata', ['Midnapur', 'Kolaghat', 'Kolkata'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-midnapur-kolkata-1130am', 'SBSTC Midnapur-Kolkata', 'SBSTC', 'Midnapur', 'Kolkata', '11:30 AM',
       'Midnapur - Kolaghat - Kolkata', ['Midnapur', 'Kolaghat', 'Kolkata'], SRC_S, 'Government - SBSTC'),
    # --- Midnapur -> Karunamoyee (join midnapur-to-karunamoyee.html) ---
    mk('sbstc-fb-midnapur-karunamoyee-305pm', 'SBSTC Midnapur-Karunamoyee', 'SBSTC', 'Midnapur', 'Karunamoyee', '3:05 PM',
       'Midnapur - Kolaghat - Esplanade - Karunamoyee', ['Midnapur', 'Kolaghat', 'Esplanade', 'Karunamoyee'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-midnapur-karunamoyee-440pm', 'SBSTC Midnapur-Karunamoyee', 'SBSTC', 'Midnapur', 'Karunamoyee', '4:40 PM',
       'Midnapur - Kolaghat - Esplanade - Karunamoyee', ['Midnapur', 'Kolaghat', 'Esplanade', 'Karunamoyee'], SRC_S, 'Government - SBSTC'),
    # --- Midnapore -> Garia (join midnapore-to-garia.html) ---
    mk('sbstc-fb-midnapore-garia-1220pm', 'SBSTC Midnapore-Garia', 'SBSTC', 'Midnapore', 'Garia', '12:20 PM',
       'Midnapore - Kolaghat - Esplanade - Garia', ['Midnapore', 'Kolaghat', 'Esplanade', 'Garia'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-midnapore-garia-330pm', 'SBSTC Midnapore-Garia', 'SBSTC', 'Midnapore', 'Garia', '3:30 PM',
       'Midnapore - Kolaghat - Esplanade - Garia', ['Midnapore', 'Kolaghat', 'Esplanade', 'Garia'], SRC_S, 'Government - SBSTC'),
    # --- Midnapore -> Habra (join midnapore-to-habra.html) ---
    mk('sbstc-fb-midnapore-habra-200pm', 'SBSTC Midnapore-Habra', 'SBSTC', 'Midnapore', 'Habra', '2:00 PM',
       'Midnapore - Airport Gate 2 - Barasat - Habra', ['Midnapore', 'Kolaghat', 'Airport Gate 2', 'Barasat', 'Habra'], SRC_S, 'Government - SBSTC'),
    # --- Medinipur -> Barasat (new page medinipur-to-barasat.html) ---
    mk('sbstc-fb-medinipur-barasat-400pm', 'SBSTC Medinipur-Barasat', 'SBSTC', 'Medinipur', 'Barasat', '4:00 PM',
       'Medinipur - Dunlop - Madhyamgram - Barasat', ['Medinipur', 'Kolaghat', 'Dunlop', 'Madhyamgram', 'Barasat'], SRC_S, 'Government - SBSTC'),
    # --- Kolkata -> Midnapur (join kolkata-to-midnapur.html), via Kolaghat ---
    mk('sbstc-fb-kolkata-midnapur-600am', 'SBSTC Kolkata-Midnapur', 'SBSTC', 'Kolkata', 'Midnapur', '6:00 AM',
       'Kolkata - Kolaghat - Midnapur', ['Kolkata', 'Kolaghat', 'Midnapur'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-midnapur-700am', 'SBSTC Kolkata-Midnapur', 'SBSTC', 'Kolkata', 'Midnapur', '7:00 AM',
       'Kolkata - Kolaghat - Midnapur', ['Kolkata', 'Kolaghat', 'Midnapur'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-midnapur-845am', 'SBSTC Kolkata-Midnapur', 'SBSTC', 'Kolkata', 'Midnapur', '8:45 AM',
       'Kolkata - Kolaghat - Midnapur', ['Kolkata', 'Kolaghat', 'Midnapur'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-midnapur-130pm-ac', 'SBSTC Kolkata-Midnapur (AC)', 'SBSTC', 'Kolkata', 'Midnapur', '1:30 PM',
       'Kolkata - Kolaghat - Midnapur', ['Kolkata', 'Kolaghat', 'Midnapur'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-midnapur-200pm', 'SBSTC Kolkata-Midnapur', 'SBSTC', 'Kolkata', 'Midnapur', '2:00 PM',
       'Kolkata - Kolaghat - Midnapur', ['Kolkata', 'Kolaghat', 'Midnapur'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-midnapur-350pm', 'SBSTC Kolkata-Midnapur', 'SBSTC', 'Kolkata', 'Midnapur', '3:50 PM',
       'Kolkata - Kolaghat - Midnapur', ['Kolkata', 'Kolaghat', 'Midnapur'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-midnapur-400pm', 'SBSTC Kolkata-Midnapur', 'SBSTC', 'Kolkata', 'Midnapur', '4:00 PM',
       'Kolkata - Kolaghat - Midnapur', ['Kolkata', 'Kolaghat', 'Midnapur'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-midnapur-430pm-ac', 'SBSTC Kolkata-Midnapur (AC)', 'SBSTC', 'Kolkata', 'Midnapur', '4:30 PM',
       'Kolkata - Kolaghat - Midnapur', ['Kolkata', 'Kolaghat', 'Midnapur'], SRC_S, 'Government - SBSTC'),
    # --- Kolkata -> Jhargram (new page kolkata-to-jhargram.html), via Medinipur ---
    mk('sbstc-fb-kolkata-jhargram-630am', 'SBSTC Kolkata-Jhargram', 'SBSTC', 'Kolkata', 'Jhargram', '6:30 AM',
       'Kolkata - Kolaghat - Medinipur - Jhargram', ['Kolkata', 'Kolaghat', 'Medinipur', 'Jhargram'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-jhargram-730am', 'SBSTC Kolkata-Jhargram', 'SBSTC', 'Kolkata', 'Jhargram', '7:30 AM',
       'Kolkata - Kolaghat - Medinipur - Jhargram', ['Kolkata', 'Kolaghat', 'Medinipur', 'Jhargram'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-jhargram-825am', 'SBSTC Kolkata-Jhargram', 'SBSTC', 'Kolkata', 'Jhargram', '8:25 AM',
       'Kolkata - Kolaghat - Medinipur - Jhargram', ['Kolkata', 'Kolaghat', 'Medinipur', 'Jhargram'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-jhargram-925am', 'SBSTC Kolkata-Jhargram', 'SBSTC', 'Kolkata', 'Jhargram', '9:25 AM',
       'Kolkata - Kolaghat - Medinipur - Jhargram', ['Kolkata', 'Kolaghat', 'Medinipur', 'Jhargram'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-jhargram-245pm', 'SBSTC Kolkata-Jhargram', 'SBSTC', 'Kolkata', 'Jhargram', '2:45 PM',
       'Kolkata - Kolaghat - Medinipur - Jhargram', ['Kolkata', 'Kolaghat', 'Medinipur', 'Jhargram'], SRC_S, 'Government - SBSTC'),
    mk('sbstc-fb-kolkata-jhargram-315pm', 'SBSTC Kolkata-Jhargram', 'SBSTC', 'Kolkata', 'Jhargram', '3:15 PM',
       'Kolkata - Kolaghat - Medinipur - Jhargram', ['Kolkata', 'Kolaghat', 'Medinipur', 'Jhargram'], SRC_S, 'Government - SBSTC'),
    # --- WBTC Habra -> Midnapore (join habra-to-midnapore.html) ---
    mk('wbtc-fb-habra-midnapore-455am', 'WBTC Habra-Midnapore', 'WBTC', 'Habra', 'Midnapore', '4:55 AM',
       'Habra - Dunlop - Midnapore', ['Habra', 'Dunlop', 'Kolaghat', 'Midnapore'], SRC_W, 'Government - WBTC'),
    mk('wbtc-fb-habra-midnapore-525am', 'WBTC Habra-Midnapore', 'WBTC', 'Habra', 'Midnapore', '5:25 AM',
       'Habra - Dunlop - Midnapore', ['Habra', 'Dunlop', 'Kolaghat', 'Midnapore'], SRC_W, 'Government - WBTC'),
    mk('wbtc-fb-habra-midnapore-555am', 'WBTC Habra-Midnapore', 'WBTC', 'Habra', 'Midnapore', '5:55 AM',
       'Habra - Dunlop - Midnapore', ['Habra', 'Dunlop', 'Kolaghat', 'Midnapore'], SRC_W, 'Government - WBTC'),
    mk('wbtc-fb-habra-midnapore-620am', 'WBTC Habra-Midnapore', 'WBTC', 'Habra', 'Midnapore', '6:20 AM',
       'Habra - Barasat - Airport Gate 2 - Midnapore', ['Habra', 'Barasat', 'Airport Gate 2', 'Kolaghat', 'Midnapore'], SRC_W, 'Government - WBTC'),
    # --- WBTC Barasat -> Medinipur (new page barasat-to-medinipur.html) ---
    mk('wbtc-fb-barasat-medinipur-830am', 'WBTC Barasat-Medinipur', 'WBTC', 'Barasat', 'Medinipur', '8:30 AM',
       'Barasat - Dunlop - Airport Gate 2 - Medinipur', ['Barasat', 'Dunlop', 'Airport Gate 2', 'Kolaghat', 'Medinipur'], SRC_W, 'Government - WBTC'),
    mk('wbtc-fb-barasat-medinipur-345pm', 'WBTC Barasat-Medinipur', 'WBTC', 'Barasat', 'Medinipur', '3:45 PM',
       'Barasat - Dunlop - Medinipur', ['Barasat', 'Dunlop', 'Kolaghat', 'Medinipur'], SRC_W, 'Government - WBTC'),
]

# stand -> (card label in BTT index, count delta)
BTT_CARDS = [
    ('Medinipur', 10),
    ('Kolkata (Esplanade)', 14),
    ('Habra', 4),
    ('Barasat', 2),
]


def patch_data():
    with open(DATA, encoding='utf-8') as fh:
        d = json.load(fh)
    buses = d['buses']
    ids = set(b.get('id') for b in buses)

    fixed = {'sbstc-midnapur-kolkata-1': ('5:50 AM', '5:10 AM'),
             'sbstc-midnapur-karunamoyee-0': ('6:30 AM', '6:50 AM')}
    nfix = 0
    for b in buses:
        fid = b.get('id')
        if fid in fixed:
            old, new = fixed[fid]
            if b.get('departure_time') == old:
                b['departure_time'] = new
                nfix += 1
                # 6:50 AM row on flyer: via Dunlop + Airport
                if fid == 'sbstc-midnapur-karunamoyee-0':
                    chain = []
                    for n, st in enumerate(['Midnapur', 'Kolaghat', 'Dunlop', 'Airport Gate 2', 'Karunamoyee'], 1):
                        chain.append({'no': n, 'name': st, 'up_time': new if n == 1 else '', 'down_time': ''})
                    b['stoppages'] = chain
                    b['total_stoppages'] = len(chain)
                    b['route'] = 'Midnapur - Dunlop - Karunamoyee'
    print('time fixes applied:', nfix)

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


def main():
    added = patch_data()
    patch_btt()
    print('done. new buses:', added)


if __name__ == '__main__':
    main()
