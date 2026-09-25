#!/usr/bin/env python3
"""
2026-09-25 patch: mobile performance + memory + offline handling.

Problems (measured on 4x CPU + slow-4G throttling, local chromium):
  1. LCP 2.4 s locally / 5.3 s in PSI: the hero only rendered after
     app.js downloaded AND home-index.json was fetched (JS-rendered).
  2. app-index.json (1.9 MB) started downloading ~2.5 s after load and
     hogged bandwidth for ~11 s on every homepage visit - killing
     Time-to-Interactive, the PSI mobile score (69), and eating
     visitors' mobile data.
  3. No offline support: revisits refetched everything; a fresh visitor
     with no network got the error panel even for the shell.

Fixes:
  A. index.html: ship the hero + search form as STATIC HTML inside #app
     (template: scripts/perf_hero_template.html), so it paints right
     after CSS. renderHome replaces it with identical markup once data
     arrives.
  B. app.js: renderInitialSkeleton skips when the static hero is present;
     the 1.9 MB full-index fetch moves from idle(2.5 s) to 10 s after
     load, or immediately when a user types in a search field. Route
     navigation already loads it on demand.
  C. sw.js (new, template: scripts/perf_sw_template.js): service worker.
     Versioned /js and /css -> cache-first. /data/ JSON ->
     stale-while-revalidate. HTML -> network first with offline fallback.
  D. Memory: measured 15 MB JS heap after full load - healthy, no leak;
     the lazy fetch now also means casual visitors never pay that memory.

Idempotent. Backslash-free source.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as fh:
        return fh.read()

def write(rel, content):
    with open(os.path.join(ROOT, rel), 'w', encoding='utf-8') as fh:
        fh.write(content)

app_src = read('js/app.js')

def icon(name):
    m = re.search(name + ": '(<svg[^>]*>.*?</svg>)',", app_src)
    assert m, 'icon not found in app.js: ' + name
    return m.group(1)

meta = json.loads(read('data/home-index.json'))['meta']

# ---------------------------------------------------- A. static hero ------

hero = read('scripts/perf_hero_template.html')
_c = hero.find('<div')
if _c > 0:
    hero = hero[_c:]
hero = hero.strip()
hero = (hero
        .replace('__BUS__', icon('bus'))
        .replace('__TICKET__', icon('ticket'))
        .replace('__PIN__', icon('pin'))
        .replace('__COMPASS__', icon('compass'))
        .replace('__STOPS__', icon('stops'))
        .replace('__SEARCH__', icon('search'))
        .replace('BUS_N+', '{:,}'.format(meta['total_buses']) + '+')
        .replace('ROUTES_N+', '{:,}'.format(meta['total_routes']) + '+')
        .replace('STOPS_N+', '{:,}'.format(meta['total_stops']) + '+'))

idx = read('index.html')
APP_EMPTY = '  <div id="app"></div>'
if 'hero-route-line' in idx and APP_EMPTY not in idx:
    print('SKIP index.html (static hero already present)')
elif APP_EMPTY in idx:
    idx = idx.replace(APP_EMPTY, hero, 1)
    print('PATCHED index.html (static hero in #app)')
else:
    print('ERROR: empty #app div not found in index.html')
    sys.exit(1)

# --------------------------------------------- C. service worker ----------

SW_REG = """  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function () {
        navigator.serviceWorker.register('sw.js').catch(function () {});
      });
    }
  </script>
</body>"""

if "navigator.serviceWorker.register('sw.js')" in idx:
    print('SKIP index.html (SW registration already present)')
elif '</body>' in idx:
    idx = idx.replace('</body>', SW_REG, 1)
    print('PATCHED index.html (service worker registration)')
else:
    print('ERROR: </body> not found')
    sys.exit(1)

OLD_V, NEW_V = 'perf20260925a', 'perf20260925b'
if NEW_V in idx:
    print('SKIP index.html (app.js buster already bumped)')
elif OLD_V in idx:
    idx = idx.replace(OLD_V, NEW_V)
    print('PATCHED index.html (app.js buster bumped)')
else:
    print('ERROR: app.js version param not found')
    sys.exit(1)

write('index.html', idx)

sw = read('scripts/perf_sw_template.js')
if os.path.exists(os.path.join(ROOT, 'sw.js')):
    print('SKIP sw.js (already exists)')
else:
    write('sw.js', sw)
    print('CREATED sw.js')

# ------------------------------------------------- B. app.js patches ------

OLD_SKEL = """function renderInitialSkeleton() {
  document.getElementById('app').innerHTML = `"""

NEW_SKEL = """function renderInitialSkeleton() {
  if (document.querySelector('#app .hero')) return; /* 2026-09-25: static hero in index.html already painted */
  document.getElementById('app').innerHTML = `"""

OLD_KICK = """    var kick = function () {
      ensureFullData().then(function () { renderBoard(); }).catch(function () {});
    };
    if (window.requestIdleCallback) {
      requestIdleCallback(function () { kick(); }, { timeout: 2500 });
    } else {
      setTimeout(kick, 2000);
    }"""

NEW_KICK = """    /* 2026-09-25: app-index.json (1.9 MB) used to start downloading
       ~2.5 s after load and hogged mobile bandwidth for 10+ s, which
       wrecked Time-to-Interactive and the PSI mobile score. Now the
       full index loads only when needed: 10 s after load (still fills
       the live board for engaged users), or the moment someone types
       in a search field. Route changes already load it on demand. */
    var kicked = false;
    var kick = function () {
      if (kicked) return;
      if (document.visibilityState === 'hidden') { setTimeout(kick, 5000); return; }
      kicked = true;
      ensureFullData().then(function () { renderBoard(); }).catch(function () {});
    };
    setTimeout(kick, 10000);
    document.addEventListener('input', function () {
      if (DATA && DATA.buses) return;
      kick();
    }, { passive: true });"""

app = read('js/app.js')
if 'static hero in index.html already painted' in app:
    print('SKIP app.js (skeleton guard already present)')
else:
    assert OLD_SKEL in app, 'app.js: renderInitialSkeleton anchor not found'
    app = app.replace(OLD_SKEL, NEW_SKEL, 1)
    print('PATCHED app.js (skeleton guard)')

if 'the moment someone types' in app:
    print('SKIP app.js (lazy kick already present)')
else:
    assert OLD_KICK in app, 'app.js: kick block not found verbatim'
    app = app.replace(OLD_KICK, NEW_KICK, 1)
    print('PATCHED app.js (lazy full-data kick)')

write('js/app.js', app)

# ------------------------------------------------------------ validate ----
errors = []

idx2 = read('index.html')
app2 = read('js/app.js')
sw2 = read('sw.js')

checks = [
    (idx2, 'index.html', 'hero-route-line'),
    (idx2, 'index.html', 'tagline en'),
    (idx2, 'index.html', 'serviceWorker'),
    (idx2, 'index.html', 'perf20260925b'),
    (idx2, 'index.html', 'stats-inline'),
    (app2, 'app.js', 'static hero in index.html already painted'),
    (app2, 'app.js', 'the moment someone types'),
    (app2, 'app.js', 'setTimeout(kick, 10000)'),
    (sw2, 'sw.js', 'stale-while-revalidate'),
    (sw2, 'sw.js', "caches.match('/index.html')"),
]
for content, where, needle in checks:
    if needle not in content:
        errors.append(where + ': missing ' + needle)

if 'requestIdleCallback(function () { kick(); }, { timeout: 2500 });' in app2:
    errors.append('app.js: old eager kick still present')
if '  <div id="app"></div>' in idx2:
    errors.append('index.html: empty #app still present')
if app2.count('function renderInitialSkeleton()') != 1:
    errors.append('app.js: renderInitialSkeleton count != 1')
if chr(92) in sw2:
    errors.append('sw.js: backslash found')

if errors:
    print('VALIDATION FAILED:')
    for e in errors:
        print('  -', e)
    sys.exit(1)

print('VALIDATION OK')
