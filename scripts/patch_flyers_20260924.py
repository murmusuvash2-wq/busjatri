#!/usr/bin/env python3
# Flyer additions + 2 time fixes - 2026-09-24
# Sources (user-verified depot timetable photos, uploaded 2026-09-24):
#   - NBSTC Cooch Behar depot notice: evening Siliguri services 8:00/8:15/8:45 PM
#     (day services already in DB from nbstc.in); CB-Kolkata 1:30 AM is a
#     misparse of Bengali "dupur 1:30" (afternoon) -> fix to 1:30 PM.
#   - SBSTC Haldia depot notice: Haldia-Karunamoyee departs 8:25 AM (DB had 8:45 AM).
#   - SBSTC Medinipur depot notice: Kolkata-Khargram services via Medinipur
#     (7:30 AM, 8:25 AM, 9:25 AM, 2:45 PM, 3:15 PM) and Medinipur-Howrah 2:00 PM.
# Idempotent: safe to re-run.

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'busjatri_data.json')

with open(DATA, encoding='utf-8') as fh:
    d = json.load(fh)
buses = d['buses']
by_id = {b.get('id'): b for b in buses}

changes = []

def nbstc_cb_siliguri(dep, dep_id):
    return {
        'id': dep_id,
        'bus_name': 'NBSTC Cooch Behar-Siliguri',
        'reg_no': '',
        'operator': 'NBSTC',
        'bus_type': 'Government',
        'origin': 'Cooch Behar',
        'destination': 'Siliguri',
        'departure_time': dep,
        'arrival_time': '',
        'contact_number': 'Not Available !',
        'depot_name': '',
        'route': 'Cooch Behar - Falakata - Siliguri',
        'stoppages': [
            {'no': 1, 'name': 'Cooch Behar', 'up_time': dep, 'down_time': ''},
            {'no': 2, 'name': 'Falakata', 'up_time': '', 'down_time': ''},
            {'no': 3, 'name': 'Siliguri', 'up_time': '', 'down_time': ''},
        ],
        'source': 'NBSTC Cooch Behar depot timetable (user-verified photo)',
        'total_stoppages': 3,
        'detail_url': 'https://nbstc.in/bus-routes.php',
    }

def sbstc_khargram(dep, dep_id):
    return {
        'id': dep_id,
        'bus_name': 'SBSTC Kolkata-Khargram',
        'reg_no': '',
        'operator': 'SBSTC',
        'bus_type': 'Government - SBSTC',
        'origin': 'Kolkata',
        'destination': 'Khargram',
        'departure_time': dep,
        'arrival_time': '',
        'contact_number': 'Not Available !',
        'depot_name': 'Midnapur',
        'route': 'Kolkata - Midnapur - Khargram',
        'stoppages': [
            {'no': 1, 'name': 'Kolkata', 'up_time': dep, 'down_time': ''},
            {'no': 2, 'name': 'Midnapur', 'up_time': '', 'down_time': ''},
            {'no': 3, 'name': 'Khargram', 'up_time': '', 'down_time': ''},
        ],
        'source': 'SBSTC Medinipur depot timetable (user-verified photo)',
        'total_stoppages': 3,
        'detail_url': '',
    }

def sbstc_howrah(dep, dep_id):
    return {
        'id': dep_id,
        'bus_name': 'SBSTC Medinipur-Howrah',
        'reg_no': '',
        'operator': 'SBSTC',
        'bus_type': 'Government - SBSTC',
        'origin': 'Medinipur',
        'destination': 'Howrah',
        'departure_time': dep,
        'arrival_time': '',
        'contact_number': 'Not Available !',
        'depot_name': 'Midnapur',
        'route': 'Medinipur - Bimanbandar Gate 2 - Barasat - Howrah',
        'stoppages': [
            {'no': 1, 'name': 'Medinipur', 'up_time': dep, 'down_time': ''},
            {'no': 2, 'name': 'Bimanbandar Gate 2', 'up_time': '', 'down_time': ''},
            {'no': 3, 'name': 'Barasat', 'up_time': '', 'down_time': ''},
            {'no': 4, 'name': 'Howrah', 'up_time': '', 'down_time': ''},
        ],
        'source': 'SBSTC Medinipur depot timetable (user-verified photo)',
        'total_stoppages': 4,
        'detail_url': '',
    }

# --- 1) CB -> Siliguri evening services ---
for dep, dep_id in [
    ('8:00 PM', 'nbstc-fb-cb-siliguri-800pm'),
    ('8:15 PM', 'nbstc-fb-cb-siliguri-815pm'),
    ('8:45 PM', 'nbstc-fb-cb-siliguri-845pm'),
]:
    if dep_id not in by_id:
        buses.append(nbstc_cb_siliguri(dep, dep_id))
        by_id[dep_id] = True
        changes.append('ADD ' + dep_id)

# --- 2) CB -> Kolkata 1:30 AM -> 1:30 PM (Bengali "dupur" misparse) ---
b = by_id.get('nbstc-in-nbstc-cooch-behar-ko-949')
if b and b.get('departure_time') == '1:30 AM':
    b['departure_time'] = '1:30 PM'
    if b.get('stoppages') and b['stoppages'][0].get('name') == 'Cooch Behar':
        b['stoppages'][0]['up_time'] = '1:30 PM'
    changes.append('FIX cb-kolkata 1:30 AM -> 1:30 PM')

# --- 3) Haldia -> Karunamoyee 8:45 AM -> 8:25 AM ---
b = by_id.get('sbstc-haldia-kolkata-5')
if b and b.get('departure_time') == '8:45 AM':
    b['departure_time'] = '8:25 AM'
    if b.get('stoppages') and b['stoppages'][0].get('name') == 'Haldia':
        b['stoppages'][0]['up_time'] = '8:25 AM'
    changes.append('FIX haldia-karunamoyee 8:45 AM -> 8:25 AM')

# --- 4) Kolkata -> Khargram (new route, via Midnapur) ---
for dep, dep_id in [
    ('7:30 AM', 'sbstc-fb-kolkata-khargram-730am'),
    ('8:25 AM', 'sbstc-fb-kolkata-khargram-825am'),
    ('9:25 AM', 'sbstc-fb-kolkata-khargram-925am'),
    ('2:45 PM', 'sbstc-fb-kolkata-khargram-245pm'),
    ('3:15 PM', 'sbstc-fb-kolkata-khargram-315pm'),
]:
    if dep_id not in by_id:
        buses.append(sbstc_khargram(dep, dep_id))
        by_id[dep_id] = True
        changes.append('ADD ' + dep_id)

# --- 5) Medinipur -> Howrah 2:00 PM ---
if 'sbstc-fb-medinipur-howrah-200pm' not in by_id:
    buses.append(sbstc_howrah('2:00 PM', 'sbstc-fb-medinipur-howrah-200pm'))
    changes.append('ADD sbstc-fb-medinipur-howrah-200pm')

if changes:
    with open(DATA, 'w', encoding='utf-8') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    print('changes applied:')
    for c in changes:
        print(' -', c)
    print('total buses:', len(buses))
else:
    print('no changes needed (already applied)')
