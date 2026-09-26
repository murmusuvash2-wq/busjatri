# SBSTC page flow fix (user-approved, 2026-09-26):
# On the SBSTC operator page, searching now OPENS the main search page
# (index.html#/search?from=X&to=Y) instead of rendering results on-page.
# 1. The v2 on-page results renderer (window.bjSearchGo override) is deleted;
#    the base redirect version (defined earlier in op-board.js) remains.
# 2. The date/hour re-trigger of bjSearchGo (in syncFilters and the
#    MutationObserver) is removed - changing filters or language must not
#    navigate away from the page.
# 3. The below-results Check Seat CTA and window.BJ_SEAT_URL page injection
#    are removed (Check Seat now lives on the main search page chips).
# 4. The depo departure board (bjLive) + date/hour pickers keep working.
# 5. genop: op-board.js cache buster bumped opse20260926 -> opsf20260926.

import re

OPBOARD = 'js/op-board.js'
GENOP = 'scripts/gen_operator_pages.py'

ob = open(OPBOARD, encoding='utf-8').read()
g = open(GENOP, encoding='utf-8').read()

if 'opsf20260926' in g:
    print('already applied')
    raise SystemExit(0)

# --- 1) delete the v2 on-page results override (base redirect stays) ---
pat_override = re.compile(
    r"    window\.bjSearchGo = function \(\) \{\n"
    r"      var f = fromI \? fromI\.value\.trim\(\) : '';\n"
    r"      var t = toI \? toI\.value\.trim\(\) : '';\n"
    r"      var isBn = document\.body\.classList\.contains\('lang-bn'\);\n"
    r"[\s\S]*?\n"
    r"      el\.innerHTML = H;\n"
    r"    \};\n")
n1 = len(pat_override.findall(ob))
assert n1 == 1, '1: v2 override not found (%d)' % n1
ob = pat_override.sub('', ob, count=1)
print('1: v2 on-page results override removed')

# --- 2) remove date/hour + language re-trigger of the search ---
pat_rs = re.compile(
    r" *var rs = document\.getElementById\('bjOpResults'\);\n"
    r" *if \(rs && rs\.getAttribute\('data-q'\) === '1'\) window\.bjSearchGo\(\);\n")
n2 = len(pat_rs.findall(ob))
assert n2 == 2, '2: expected 2 re-trigger blocks, found %d' % n2
ob = pat_rs.sub('', ob)
print('2: %d search re-triggers removed (filters/language)' % n2)

# --- 3) genop: drop the BJ_SEAT_URL page injection ---
pat_inj = re.compile(
    r"    # ---- Check Seat: inject seat URL for below-results CTA ----\n"
    r"    b = b\.replace\(\"<script src='\.\./js/op-board\.js\?v=\", \"<script>window\.BJ_SEAT_URL='https://sbstconline\.co\.in/reservation-home';</script><script src='\.\./js/op-board\.js\?v=\", 1\)\n\n")
n3 = len(pat_inj.findall(g))
assert n3 == 1, '3: genop injection not found (%d)' % n3
g = pat_inj.sub('', g)
print('3: BJ_SEAT_URL page injection removed from genop')

# --- 4) bump cache buster ---
assert g.count('opse20260926') == 1, '4: buster count unexpected'
g = g.replace('opse20260926', 'opsf20260926')
print('4: buster bumped')

with open(OPBOARD, 'w', encoding='utf-8') as fh:
    fh.write(ob)
with open(GENOP, 'w', encoding='utf-8') as fh:
    fh.write(g)

# verify
ob2 = open(OPBOARD, encoding='utf-8').read()
g2 = open(GENOP, encoding='utf-8').read()
assert 'bjOpResults' not in ob2, 'bjOpResults still in op-board.js'
assert 'BJ_SEAT_URL' not in ob2, 'BJ_SEAT_URL still in op-board.js'
assert 'BJ_SEAT_URL' not in g2, 'BJ_SEAT_URL still in genop'
assert ob2.count('window.bjSearchGo = function') == 1, 'base bjSearchGo missing'
assert 'opsf20260926' in g2 and 'opse20260926' not in g2
print('OK')
