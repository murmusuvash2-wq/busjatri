# Check Seat chip -> redBus deeplink (user-approved, 2026-09-26).
# The chip on SBSTC bus cards now links to redBus with From/To + journey
# date prefilled:
#   https://www.redbus.in/bus-tickets/<from-slug>-to-<to-slug>
#     ?fromCityName=..&toCityName=..&onward=DD-Mon-YYYY&srcCountry=IND&destCountry=IND
# - Date: today if the bus still departs today, tomorrow if already departed
#   (matches the card's "tomorrow" logic). Time cannot be prefilled (redBus
#   has no time parameter).
# - Only city-level stops with a verified redBus slug get the chip; rural
#   stops not bookable on redBus get NO chip (same honest rule as before).
# - Localities fold to their redBus city (Karunamoyee->Haldia, Garia->Kolkata).
# - Return-direction cards use the direction the card displays.
# - Label stays "Check Seat" (never "Book"); affiliate URL can replace the
#   base later without touching this logic.
# Verified slugs (2026-09-26, live pages): kolkata, digha, asansol, durgapur,
# bankura, purulia; route-page footer links confirm burdwan, haldia,
# midnapore, arambagh, suri, jhargram, malda, barasat, habra, naihati,
# jamshedpur.

import re

JS = 'js/stop-search-all.js'
IDX = 'index.html'

s = open(JS, encoding='utf-8').read()
idx = open(IDX, encoding='utf-8').read()

if 'RB_CITY' in s:
    print('already applied')
    raise SystemExit(0)

NEW = (
    "      var RB_CITY = {\n"
    "        'Kolkata': ['Kolkata', 'kolkata'], 'Kolkata A.C': ['Kolkata', 'kolkata'], 'Kolkata (Esplanade)': ['Kolkata', 'kolkata'],\n"
    "        'Garia': ['Kolkata', 'kolkata'], 'Garia A.C': ['Kolkata', 'kolkata'], 'Belghoria': ['Kolkata', 'kolkata'],\n"
    "        'Thakurpukur': ['Kolkata', 'kolkata'], 'Baruipur': ['Kolkata', 'kolkata'], 'Baruipur A.C': ['Kolkata', 'kolkata'], 'Dumdum': ['Kolkata', 'kolkata'],\n"
    "        'Digha': ['Digha', 'digha'], 'New Digha': ['Digha', 'digha'],\n"
    "        'Burdwan': ['Burdwan', 'burdwan'], 'Bardhaman': ['Burdwan', 'burdwan'],\n"
    "        'Karunamoyee': ['Haldia', 'haldia'], 'Haldia': ['Haldia', 'haldia'], 'Haldia Township': ['Haldia', 'haldia'], 'Haldia Via-Kolkata': ['Haldia', 'haldia'],\n"
    "        'Asansol': ['Asansol', 'asansol'], 'Asansol A.C.': ['Asansol', 'asansol'],\n"
    "        'Durgapur': ['Durgapur', 'durgapur'], 'Durgapur (City Center)': ['Durgapur', 'durgapur'], 'Durgapur City Centre': ['Durgapur', 'durgapur'], 'Durgapur (Station)': ['Durgapur', 'durgapur'],\n"
    "        'Midnapur': ['Midnapore', 'midnapore'], 'Midnapore': ['Midnapore', 'midnapore'], 'Medinipur': ['Midnapore', 'midnapore'],\n"
    "        'Bankura': ['Bankura', 'bankura'], 'Purulia': ['Purulia', 'purulia'], 'Arambag': ['Arambagh', 'arambagh'],\n"
    "        'Suri': ['Suri', 'suri'], 'Jhargram': ['Jhargram', 'jhargram'],\n"
    "        'Barasat': ['Barasat', 'barasat'], 'Barasat A.C': ['Barasat', 'barasat'], 'Habra': ['Habra', 'habra'], 'Naihati': ['Naihati', 'naihati'],\n"
    "        'Malda': ['Malda', 'malda'], 'Tatanagar': ['Jamshedpur', 'jamshedpur']\n"
    "      };\n"
    "      function bookChip(b, ro, rd, tmr) {\n"
    "        if (!b) return '';\n"
    "        var _op = String(b.operator || '').toUpperCase();\n"
    "        var _bt = String(b.bus_type || '').toUpperCase();\n"
    "        if (_op !== 'SBSTC' && _bt.indexOf('SBSTC') === -1 && String(b.bus_name || '').toUpperCase().indexOf('SBSTC') !== 0) return '';\n"
    "        var F = RB_CITY[ro], T = RB_CITY[rd];\n"
    "        if (!F || !T) return '';\n"
    "        var d = new Date();\n"
    "        if (tmr) d.setDate(d.getDate() + 1);\n"
    "        var MN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];\n"
    "        var onw = d.getDate() + '-' + MN[d.getMonth()] + '-' + d.getFullYear();\n"
    "        var u = 'https://www.redbus.in/bus-tickets/' + F[1] + '-to-' + T[1] + '?fromCityName=' + encodeURIComponent(F[0]) + '&toCityName=' + encodeURIComponent(T[0]) + '&onward=' + onw + '&srcCountry=IND&destCountry=IND';\n"
    "        return '<a href=\"' + u + '\" target=\"_blank\" rel=\"noopener nofollow\" onclick=\"event.stopPropagation()\" title=\"Check seat availability on redBus\" style=\"position:absolute;right:14px;bottom:12px;background:var(--amber,#b8791f);color:#fffcf4;border-radius:999px;padding:6px 13px;font-size:11.5px;font-weight:800;text-decoration:none;display:inline-flex;align-items:center;gap:5px\">' + String.fromCharCode(127915) + ' <span class=\"label-en\">Check Seat</span><span class=\"label-bn\">' + '\\u09b8\\u09bf\\u099f \\u09a6\\u09c7\\u0996\\u09c1\\u09a8' + '</span></a>';\n"
    "      }\n"
)

pat = re.compile(r"      function bookChip\(b\) \{[\s\S]*?\n      \}\n")
n = len(pat.findall(s))
assert n == 1, 'bookChip not found (%d)' % n
s = pat.sub(lambda m: NEW, s, count=1)  # lambda: NEW has \\u escapes, must not be parsed by re
print('1: bookChip -> redBus deeplink version')

old_call = "'</div>' + tPill + bookChip(b) + '</div>';"
new_call = "'</div>' + tPill + bookChip(b, ro, rd, r.depMin != null && r.depMin < now) + '</div>';"
assert s.count(old_call) == 1, 'call site not found'
s = s.replace(old_call, new_call, 1)
print('2: call site passes route + tomorrow flag')

# cache buster
assert idx.count('bj20260926a') == 1, 'buster count unexpected in index.html'
idx = idx.replace('bj20260926a', 'bj20260926b')
print('3: buster bj20260926a -> bj20260926b')

with open(JS, 'w', encoding='utf-8') as fh:
    fh.write(s)
with open(IDX, 'w', encoding='utf-8') as fh:
    fh.write(idx)

s2 = open(JS, encoding='utf-8').read()
assert 'sbstconline' not in s2, 'old URL still present'
assert 'RB_CITY' in s2 and 'redbus.in/bus-tickets/' in s2
print('OK')
