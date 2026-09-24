#!/usr/bin/env python3
# Homepage performance: load a tiny home-index.json first (meta + stop names +
# top routes), render home immediately, and fetch the big app-index.json in
# the background / on demand (search, route, place, stop, bus pages).
# Also patches build_client_data.py to emit home-index.json.
# Backslash-free. Idempotent.

import io

# ---------------- js/app.js ----------------
AP = 'js/app.js'
s = io.open(AP, encoding='utf-8').read()

if 'ensureFullData' in s:
    print('app.js already patched')
else:
    # 1) vars
    old = "let DATA = null, BUSES = {}, ROUTES = {}, STOPS = {}, FULL_BUSES = null, LANG = 'en';"
    assert old in s
    s = s.replace(old, "let DATA = null, BUSES = {}, ROUTES = {}, STOPS = {}, FULL_BUSES = null, LANG = 'en', SN = [], TOP_ROUTES = null, FULL_PROMISE = null;", 1)

    # 2) loadData -> home-index + ensureFullData (position-based slice)
    i = s.index('async function loadData() {')
    j = s.index('function setLang(l) {')
    new_block = '''async function loadData() {
  renderInitialSkeleton();
  try {
    const res = await fetch('data/home-index.json');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const home = await res.json();
    DATA = { meta: home.meta || {} };
    SN = home.sn || [];
    TOP_ROUTES = home.top || [];
    BUSES = {}; ROUTES = {}; STOPS = {};
    window.addEventListener('hashchange', render);
    render();
    var kick = function () {
      ensureFullData().then(function () { renderBoard(); }).catch(function () {});
    };
    if (window.requestIdleCallback) {
      requestIdleCallback(function () { kick(); }, { timeout: 2500 });
    } else {
      setTimeout(kick, 2000);
    }
  } catch (e) {
    try {
      await ensureFullData();
      window.addEventListener('hashchange', render);
      render();
      return;
    } catch (e2) {}
    document.getElementById('app').innerHTML = `
    <div class="container"><div class="error-panel">
      ${icon('alert')}
      <p><strong>Could not load the timetable.</strong><br>${esc(e.message)}</p>
      <button class="retry-btn" onclick="loadData()">Try again</button>
    </div></div>`;
  }
}

function ensureFullData() {
  if (DATA && DATA.buses) return Promise.resolve();
  if (!FULL_PROMISE) {
    FULL_PROMISE = fetch('data/app-index.json').then(function (res) {
      if (!res.ok) { FULL_PROMISE = null; throw new Error('HTTP ' + res.status); }
      return res.json();
    }).then(function (full) {
      DATA = full;
      BUSES = {};
      DATA.buses.forEach(b => BUSES[b.id] = b);
      ROUTES = DATA.routes || {};
      STOPS = DATA.stops || {};
      if (DATA.sn && DATA.sn.length) SN = DATA.sn;
    });
  }
  return FULL_PROMISE;
}

'''
    s = s[:i] + new_block + s[j:]

    # 3) render(): ensure full data before any non-home view
    old = """async function render() {
  const hash = location.hash.slice(1) || '/';
  const app = document.getElementById('app');
  if (hash === '/' || hash === '') renderHome(app);"""
    new = """async function render() {
  const hash = location.hash.slice(1) || '/';
  const app = document.getElementById('app');
  if (hash !== '/' && hash !== '') { try { await ensureFullData(); } catch (e) {} }
  if (hash === '/' || hash === '') renderHome(app);"""
    assert old in s
    s = s.replace(old, new, 1)

    # 4) computePopularRoutes: prefer precomputed top routes
    old = """function computePopularRoutes() {
  const pair = {};"""
    new = """function computePopularRoutes() {
  if (TOP_ROUTES && TOP_ROUTES.length) return TOP_ROUTES;
  const pair = {};"""
    assert old in s
    s = s.replace(old, new, 1)

    # 5) stopList datalist: SN fallback before full data arrives
    old = "[...new Set([...Object.keys(STOPS), ...Object.values(BUSES).flatMap(b => [b.origin, b.destination]).filter(Boolean)])"
    new = "[...new Set([...(SN && SN.length ? SN : Object.keys(STOPS)), ...Object.values(BUSES).flatMap(b => [b.origin, b.destination]).filter(Boolean)])"
    assert old in s
    s = s.replace(old, new, 1)

    # 6) renderBoard: loading placeholder while full data is still loading
    k = s.index('No timed departures listed')
    # find the start of the "} else {" line just before it
    m = s.rindex('} else {', 0, k)
    insert = """} else if (!(DATA && DATA.buses)) {
    rows = `<div class="lv-row"><span class="lnm">Loading departures...</span></div>`;
  """
    s = s[:m] + insert + s[m:]

    io.open(AP, 'w', encoding='utf-8').write(s)
    print('app.js patched')

# ---------------- scripts/build_client_data.py ----------------
BP = 'scripts/build_client_data.py'
b = io.open(BP, encoding='utf-8').read()

if 'home-index.json' in b:
    print('build_client_data.py already patched')
else:
    anchor = '(ROOT / "data" / "app-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")'
    assert anchor in b
    add = anchor + '''

from collections import Counter as _Counter
_pair = _Counter()
for _bus in source["buses"]:
    _o = tidy(_bus.get("origin"))
    _d = tidy(_bus.get("destination"))
    if _o and _d and _o != _d:
        _pair[(_o, _d)] += 1
_home = {"meta": index["meta"], "sn": sn,
         "top": [{"from": _o, "to": _d, "n": _c} for (_o, _d), _c in _pair.most_common(10)]}
(ROOT / "data" / "home-index.json").write_text(json.dumps(_home, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")'''
    b = b.replace(anchor, add, 1)
    b = b.replace('print("Built app-index.json, app-index-lite.json and per-bus details")',
                  'print("Built app-index.json, home-index.json, app-index-lite.json and per-bus details")', 1)
    io.open(BP, 'w', encoding='utf-8').write(b)
    print('build_client_data.py patched')

# ---------------- index.html: cache-buster + defer ----------------
IH = 'index.html'
h = io.open(IH, encoding='utf-8').read()
h2 = h.replace('js/app.js?v=mob20260920a', 'js/app.js?v=perf20260924a', 1)
changed = h2 != h
for name in ['js/time-overrides.js?v=ovr20260919a', 'js/app.js?v=perf20260924a',
             'js/extras.js?v=rpt20260920d', 'js/bus-page.js?v=bj20260923b',
             'js/lang-persist.js?v=communitytime20260915', 'js/ux-fixes.js?v=rpt20260924a',
             'js/stop-search-all.js?v=bj20260924a', 'js/alt-route.js?v=alt20260922a']:
    old = '<script src="' + name + '"></script>'
    new = '<script defer src="' + name + '"></script>'
    if old in h2 and new not in h2:
        h2 = h2.replace(old, new, 1)
        changed = True
if changed:
    io.open(IH, 'w', encoding='utf-8').write(h2)
    print('index.html patched (cache-buster + defer)')
else:
    print('index.html already patched / nothing to do')
