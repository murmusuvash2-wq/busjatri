# NBSTC Cooch Behar Depot flyer (Facebook) - fixes + via enrichment.
# 1) CB->Siliguri 1:00 PM -> 12:50 PM (flyer row 20)
# 2) CB->Beldanga 5:15 AM -> 6:15 AM (flyer bottom rows, 2/3 OCR reads)
# 3) NEW bus CB->Siliguri 2:00 PM (flyer rows 21+22 both 2:00 PM; data had one)
# 4) Via stoppages (Falakata / Mathabhanga) added to all CB-depot NBSTC buses,
#    as origin(dep time) + via + destination chain - existing via-page listings
#    preserved, Falakata/Mathabhanga via pages get these buses too.
# 5) BTT index static card count for Cooch Behar bumped to new bus count.
# NOTE: flyer shows CB->Kolkata 1:30 PM but nbstc.in data says 1:30 AM - left
# unchanged (flyer footnote itself is ambiguous about the asterisked rows).
# Idempotent + backslash-free.

import json

DATA = 'data/busjatri_data.json'
BTT = 'bus-time-table/index.html'
NEW_ID = 'nbstc-fb-cb-siliguri-2pm'
SRC = 'NBSTC Cooch Behar Depot timetable (Facebook)'

MATHABHANGA_SILIGURI = {'8:20 AM', '9:30 AM', '3:15 PM'}
VIA_DEFAULT = 'Falakata'
VIA_M = 'Mathabhanga'


def stops_for(o, d, dep, via):
    return [
        {'no': 1, 'name': o, 'up_time': dep, 'down_time': ''},
        {'no': 2, 'name': via, 'up_time': '', 'down_time': ''},
        {'no': 3, 'name': d, 'up_time': '', 'down_time': ''}
    ]


def pick_via(dest, dep):
    if dest == 'Beldanga':
        return VIA_M
    if dest == 'Siliguri' and dep in MATHABHANGA_SILIGURI:
        return VIA_M
    return VIA_DEFAULT


def main():
    data = json.load(open(DATA, encoding='utf-8'))
    buses = data['buses']
    n_fix = n_via = 0

    for b in buses:
        if (b.get('origin') or '').strip() != 'Cooch Behar':
            continue
        if (b.get('operator') or '') != 'NBSTC':
            continue
        dest = b.get('destination') or ''
        dep = b.get('departure_time') or ''
        if dest == 'Siliguri' and dep == '1:00 PM':
            b['departure_time'] = '12:50 PM'
            dep = '12:50 PM'
            n_fix += 1
            print('fix: CB->Siliguri 1:00 PM -> 12:50 PM')
        if dest == 'Beldanga' and dep == '5:15 AM':
            b['departure_time'] = '6:15 AM'
            dep = '6:15 AM'
            n_fix += 1
            print('fix: CB->Beldanga 5:15 AM -> 6:15 AM')
        via = pick_via(dest, dep)
        b['stoppages'] = stops_for('Cooch Behar', dest, dep, via)
        b['total_stoppages'] = 3
        b['route'] = 'Cooch Behar - ' + via + ' - ' + dest
        n_via += 1

    new_id_added = False
    if not any(b.get('id') == NEW_ID for b in buses):
        nb = {
            'id': NEW_ID,
            'bus_name': 'NBSTC Cooch Behar-Siliguri',
            'reg_no': '',
            'operator': 'NBSTC',
            'bus_type': 'Government',
            'origin': 'Cooch Behar',
            'destination': 'Siliguri',
            'departure_time': '2:00 PM',
            'arrival_time': '',
            'contact_number': 'Not Available !',
            'depot_name': '',
            'route': 'Cooch Behar - Falakata - Siliguri',
            'stoppages': stops_for('Cooch Behar', 'Siliguri', '2:00 PM', VIA_DEFAULT),
            'source': SRC,
            'total_stoppages': 3,
            'detail_url': ''
        }
        buses.append(nb)
        new_id_added = True
        print('add: new CB->Siliguri 2:00 PM bus (' + NEW_ID + ')')

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('data: ' + str(n_fix) + ' time fixes, ' + str(n_via) + ' buses enriched with via')

    # --- BTT index static card count for Cooch Behar (old + 1: exactly one bus added) ---
    s = open(BTT, encoding='utf-8').read()
    i = s.find('href="buses-from-cooch-behar.html"')
    if i > -1:
        mk = '<div class="smeta"><b>'
        j = s.find(mk, i)
        if j > -1:
            k = s.find('</b>', j)
            if k > -1:
                old = s[j + len(mk):k]
                if old.isdigit():
                    new = str(int(old) + 1)
                    if new_id_added:
                        if old != new:
                            s = s[:j + len(mk)] + new + s[k:]
                            open(BTT, 'w', encoding='utf-8').write(s)
                            print('btt: Cooch Behar card count ' + old + ' -> ' + new)
                        else:
                            print('btt: count already ' + new)
                    else:
                        print('btt: no new bus added, count stays ' + old)
                else:
                    print('btt: unexpected card count text: ' + old[:20])
    else:
        print('btt: CB card not found')


if __name__ == '__main__':
    main()
