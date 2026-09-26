# Remove redBus booking links from search results (user: "redBus me bus hi nahi").
# 1. Route-level "Check fares & book on redBus" link under the results header:
#    removed entirely (redBus does not list most of these buses).
# 2. Per-card amber "Book" chip: now ONLY on SBSTC operator buses, relabelled
#    "Check Seat", linking to the SBSTC official site (sbstconline.co.in).
#    Private / WBTC / NBSTC / other operators get no booking option at all.
# 3. index.html: stop-search-all.js cache buster bumped.

import re

JS = 'js/stop-search-all.js'
IDX = 'index.html'
SEAT_URL = 'https://sbstconline.co.in/reservation-home'
BN_SEAT = '\\u09b8\\u09bf\\u099f \\u09a6\\u09c7\\u0996\\u09c1\\u09a8'  # "sith dekhun"

s = open(JS, encoding='utf-8').read()
idx = open(IDX, encoding='utf-8').read()

if 'sbstconline.co.in' in s:
    print('already applied')
    raise SystemExit(0)

# --- 1) drop the route-level redBus link ---
n1 = len(re.findall(r"      var redbUrl = [^\n]*\n      var redbHtml = [^\n]*\n", s))
assert n1 == 1, '1: redBus route link not found (%d)' % n1
s = re.sub(r"      var redbUrl = [^\n]*\n      var redbHtml = [^\n]*\n",
           "      var redbHtml = '';\n", s, count=1)
print('1: route-level redBus link removed')

# --- 2) SBSTC-only Check Seat chip ---
n2 = len(re.findall(r"      function bookChip\(fr, td\) \{\n        return '<a href=\"https://www\.redbus\.in[^\n]*\n      \}\n", s))
assert n2 == 1, '2: bookChip not found (%d)' % n2
new_chip = (
    "      function bookChip(b) {\n"
    "        if (!b) return '';\n"
    "        var _op = String(b.operator || '').toUpperCase();\n"
    "        var _bt = String(b.bus_type || '').toUpperCase();\n"
    "        if (_op !== 'SBSTC' && _bt.indexOf('SBSTC') === -1 && String(b.bus_name || '').toUpperCase().indexOf('SBSTC') !== 0) return '';\n"
    "        return '<a href=\"" + SEAT_URL + "\" target=\"_blank\" rel=\"noopener\" onclick=\"event.stopPropagation()\" title=\"Check seat availability on the SBSTC official site\" style=\"position:absolute;right:14px;bottom:12px;background:var(--amber,#b8791f);color:#fffcf4;border-radius:999px;padding:6px 13px;font-size:11.5px;font-weight:800;text-decoration:none;display:inline-flex;align-items:center;gap:5px\">' + String.fromCharCode(127915) + ' <span class=\"label-en\">Check Seat</span><span class=\"label-bn\">' + '" + BN_SEAT + "' + '</span></a>';\n"
    "      }\n"
)
s = re.sub(r"      function bookChip\(fr, td\) \{\n        return '<a href=\"https://www\.redbus\.in[^\n]*\n      \}\n",
           new_chip.replace('\\', '\\\\'), s, count=1)
print('2: bookChip now SBSTC-only Check Seat')

# --- 3) call site: pass the bus object ---
old_call = "bookChip(ro, rd)"
assert s.count(old_call) == 1, '3: call site not found'
s = s.replace(old_call, "bookChip(b)", 1)
print('3: call site updated')

# --- 4) bump cache buster in index.html ---
old_b = 'js/stop-search-all.js?v=bj20260925b'
assert old_b in idx, '4: buster not found'
idx = idx.replace(old_b, 'js/stop-search-all.js?v=bj20260926a', 1)
print('4: buster bumped')

with open(JS, 'w', encoding='utf-8') as fh:
    fh.write(s)
with open(IDX, 'w', encoding='utf-8') as fh:
    fh.write(idx)

# verify
s2 = open(JS, encoding='utf-8').read()
i2 = open(IDX, encoding='utf-8').read()
assert 'redbus.in' not in s2, 'redbus.in still present in js'
assert 'redbUrl' not in s2, 'redbUrl still present'
assert SEAT_URL in s2 and 'Check Seat' in s2 and 'bookChip(b)' in s2
assert "_op !== 'SBSTC' && _bt.indexOf('SBSTC') === -1" in s2
assert 'bj20260926a' in i2 and 'bj20260925b' not in i2
print('OK')
