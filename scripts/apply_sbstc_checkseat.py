# SBSTC Check Seat fix (user request, 2026-09-26):
# 1. NO operator page gets the static "Book tickets" link under the search
#    button anymore (it was showing below Search - wrong flow).
# 2. Only the SBSTC page gets a "Check Seat on SBSTC official site" button,
#    rendered BELOW the search results (search -> times -> check seat).
#    Done via window.BJ_SEAT_URL + op-board.js CTA after results render.
# 3. Private / other operators: no booking system at all.

import re

GENOP = 'scripts/gen_operator_pages.py'
OPBOARD = 'js/op-board.js'


def jsesc(s):
    out = []
    for ch in s:
        cp = ord(ch)
        if cp < 128:
            out.append(ch)
        elif cp > 0xFFFF:
            cp -= 0x10000
            out.append('\\u%04x\\u%04x' % (0xD800 + (cp >> 10), 0xDC00 + (cp & 0x3FF)))
        else:
            out.append('\\u%04x' % cp)
    return ''.join(out)


g = open(GENOP, encoding='utf-8').read()
ob = open(OPBOARD, encoding='utf-8').read()

if 'BJ_SEAT_URL' in ob:
    print('already applied')
    raise SystemExit(0)

# --- A) drop the static booking link from the shared search card ---
old_a = """    off_link = ''
    if off:
        off_link = ("<div class='alt'><a href='" + off[0] + "' target='_blank' rel='noopener'>\U0001F3AB <span class='label-en'>" + off[1] + "</span><span class='label-bn'>" + off[2] + "</span> \u2197</a></div>")"""
if old_a not in g:
    # emoji may be the ticket symbol; try to locate by regex instead
    m = re.search(r"    off_link = ''\n    if off:\n        off_link = \(.*?\)\n", g, re.S)
    assert m, 'A: anchor not found in genop'
    g = g[:m.start()] + "    off_link = ''\n" + g[m.end():]
    print('A: removed static booking link (regex)')
else:
    g = g.replace(old_a, "    off_link = ''", 1)
    print('A: removed static booking link')

# --- B) inject window.BJ_SEAT_URL on the SBSTC page only ---
anchor_b = "    # ---- search card v2: day chips + time chips + on-page results ----"
assert anchor_b in g, 'B: anchor not found'
inject_b = ("    # ---- Check Seat: inject seat URL for below-results CTA ----\n"
            "    b = b.replace(\"<script src='../js/op-board.js?v=\", \"<script>window.BJ_SEAT_URL='https://sbstconline.co.in/reservation-home';</script><script src='../js/op-board.js?v=\", 1)\n\n")
g = g.replace(anchor_b, inject_b + anchor_b, 1)
print('B: BJ_SEAT_URL injection added')

# --- C) bump op-board.js cache buster ---
n_c = g.count('opd20260926')
assert n_c >= 1, 'C: buster not found'
g = g.replace('opd20260926', 'opse20260926')
print('C: buster bumped (%d)' % n_c)

# --- D) op-board.js: Check Seat CTA below search results ---
# Bengali label derived from the existing OFFICIAL dict text.
_D_PAT = r"'sbstc-buses': \('https://sbstconline\.co\.in/reservation-home', '[^']*', '([^']*)'"
m = re.search(_D_PAT, g)
assert m, 'D: OFFICIAL bn label not found'
bn_old = m.group(1)
bn_new = bn_old.replace('\u099f\u09bf\u0995\u09bf\u099f \u09ac\u09c1\u0995 \u0995\u09b0\u09c1\u09a8', '\u09b8\u09bf\u099f \u09a6\u09c7\u0996\u09c1\u09a8')
assert bn_new != bn_old, 'D: bn replace failed'
bn_js = jsesc(bn_new)
ticket_js = jsesc('\U0001F3AB')
arrow_js = jsesc('\u2197')

old_d = "      H += '</div>';\n      el.innerHTML = H;"
assert old_d in ob, 'D: op-board anchor not found'
new_d = ("      H += '</div>';\n"
         "      if (window.BJ_SEAT_URL) {\n"
         "        H += '<a class=\"op-cta-big\" style=\"margin:14px 0 2px\" href=\"' + window.BJ_SEAT_URL + '\" target=\"_blank\" rel=\"noopener\">' + '" + ticket_js + " <span class=\"label-en\">Check Seat on SBSTC official site</span><span class=\"label-bn\">' + '" + bn_js + "' + '</span> " + arrow_js + "</a>';\n"
         "      }\n"
         "      el.innerHTML = H;")
ob = ob.replace(old_d, new_d, 1)
print('D: op-board.js CTA added (bn=%s)' % bn_new)

with open(GENOP, 'w', encoding='utf-8') as fh:
    fh.write(g)
with open(OPBOARD, 'w', encoding='utf-8') as fh:
    fh.write(ob)

# verify
g2 = open(GENOP, encoding='utf-8').read()
ob2 = open(OPBOARD, encoding='utf-8').read()
assert "off_link = (\"<div class='alt'>" not in g2
assert 'BJ_SEAT_URL' in g2 and 'BJ_SEAT_URL' in ob2
assert 'opse20260926' in g2 and 'opd20260926' not in g2
print('OK')
