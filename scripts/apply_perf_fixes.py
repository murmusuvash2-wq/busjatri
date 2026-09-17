#!/usr/bin/env python3
"""One-time search performance patches (2026-09-17), applied in CI so the
large JS files never travel through an API push. Idempotent; fails loudly
if an anchor is missing.

1. js/app.js - renderSearch no longer downloads the 5MB bus-details file;
   the compact app-index already carries stop names + times.
2. js/ux-fixes.js - search v2 route mode uses the compact index instantly
   (no 5s wait); the autocomplete dropdown is debounced (keyboard jank fix).
3. index.html - cache-bust the changed JS files.
4. (2026-09-18) js/app.js - the search datalist now offers ALL stops plus
every origin/destination (it was capped at 800 entries, so many stoppages
never appeared as search suggestions).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def patch(path, old, new):
    p = ROOT / path
    s = p.read_text(encoding='utf-8')
    if new in s:
        print(f'  {path}: already applied')
        return
    if old not in s:
        raise SystemExit(f'ANCHOR MISSING in {path}: {old[:60]!r}')
    p.write_text(s.replace(old, new, 1), encoding='utf-8')
    print(f'  {path}: patched')

patch('js/app.js',
"""  if (from || to || stop) {
    el.innerHTML = '<div class="container" style="padding:40px"><div class="loading">Searching the full timetable\u2026</div></div>';
    try { await loadFullBusData(); } catch (e) { /* fall back to compact index below */ }
  }
  let results = Object.values(FULL_BUSES || BUSES);""",
"""  /* compact index (app-index.json) already carries stop names + times:
     search no longer downloads the 5MB detail file */
  let results = Object.values(BUSES);""")

patch('js/ux-fixes.js',
"""      if (routeMode) {
        el.innerHTML = '<div class="container" style="padding:40px"><div class="loading">Searching the full timetable\u2026</div></div>';
        try { await bjTimedLoad(); } catch (e) {}
        all = Object.values(FULL_BUSES || BUSES);""",
"""      if (routeMode) {
        /* compact index has full stop coverage \u2014 no 5MB download, instant results */
        all = Object.values(BUSES);""")

patch('js/ux-fixes.js',
"""  document.addEventListener('input', function (e) {
    if (isSearchInput(e.target)) showDrop(e.target);
  });""",
"""  var acTimer = null;
  document.addEventListener('input', function (e) {
    if (!isSearchInput(e.target)) return;
    if (acTimer) clearTimeout(acTimer);
    var t = e.target;
    acTimer = setTimeout(function () { showDrop(t); }, 110);
  });""")

# datalist: all stops + origins/destinations (built with chr() so no exotic
# characters appear in this source file)
BT = chr(96)
AR = chr(61) + chr(62)
SQ = chr(39)
DL = chr(36)
OPT_OLD = BT + '<option value="' + DL + '{esc(s.name)}">' + BT
OPT_NEW = BT + '<option value="' + DL + '{esc(n)}">' + BT
DL_OLD = ('        <datalist id="stopList">' + DL + '{Object.values(STOPS).slice(0, 800).map(s ' + AR + ' ' + OPT_OLD + ').join(' + SQ + SQ + ')}</datalist>')
DL_NEW = ('        <datalist id="stopList">' + DL + '{[...new Set([...Object.keys(STOPS), ...Object.values(BUSES).flatMap(b ' + AR + ' [b.origin, b.destination]).filter(Boolean)])].map(n ' + AR + ' ' + OPT_NEW + ').join(' + SQ + SQ + ')}</datalist>')
patch('js/app.js', DL_OLD, DL_NEW)

for a, b in [('js/app.js?v=communitytime20260915', 'js/app.js?v=bj20260917a'),
             ('js/extras.js?v=communitytime20260915', 'js/extras.js?v=bj20260917a'),
             ('js/bus-page.js?v=communitytime20260915', 'js/bus-page.js?v=bj20260917a'),
             ('js/ux-fixes.js?v=ux20260916k', 'js/ux-fixes.js?v=ux20260917a'),
             ('js/app.js?v=bj20260917a', 'js/app.js?v=bj20260918a')]:
    patch('index.html', a, b)

print('performance patches done')
