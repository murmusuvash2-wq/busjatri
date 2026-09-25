#!/usr/bin/env python3
"""
2026-09-25 patch: stop-search fix + admin override visibility.

Problem 1 (reported: "santuri stopage search karo or dekho kya garbar
hai"): searching the stoppage "Santuri" (a small village in Purulia)
returned 1585 buses. Root cause: placeMatchesCore's transliteration
skeleton tier allowed CONTAINMENT - the query skeleton "sntr" is
contained in "Santragachi"'s skeleton "sntrgch", so Santragachi
matched; and because Santragachi sits in the kolkata alias group,
every Kolkata / Esplanade / Garia bus matched too. Fix: containment
only when the value skeleton is at most 2 consonants longer than the
query skeleton (small suffixes are already covered by the plain
substring tier). Santuri now matches exactly the 9 buses that halt
there; all major searches keep their counts.

Problem 2 (reported: "admin panel se bus ka time change nahi ho
raha"): the runtime override chain itself works (verified locally:
commit time-overrides.json -> deploy -> next real page load patches
search results and the bus page), but the service worker's
stale-while-revalidate /data/ policy ignored the page's cache:'no-cache'
request for data/time-overrides.json, so a freshly committed admin
correction only appeared after TWO reloads. Fix: sw.js now serves
data/time-overrides.json network-first (cache fallback when offline),
so an admin save shows up on the next reload.

Also bumps the app.js cache buster perf20260925c -> perf20260925d.

Idempotent. Backslash-free source.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as fh:
        return fh.read()

def write(rel, content):
    with open(os.path.join(ROOT, rel), 'w', encoding='utf-8') as fh:
        fh.write(content)

# ---------------------------------------------------------------- A ------

app = read('js/app.js')

OLD_A = """  if (qs.length >= 4 && (vs === qs || vs.includes(qs))) return true;
  return false;"""

NEW_A = """  /* 2026-09-25: containment only for near-equal skeletons. Loose
     containment matched e.g. Santragachi (sntrgch) for the query
     "santuri" (sntr), and via the kolkata alias group that pulled
     1585 buses into a small village's stop search. */
  if (qs.length >= 4 && (vs === qs || (vs.includes(qs) && vs.length - qs.length <= 2))) return true;
  return false;"""

if 'containment only for near-equal skeletons' in app:
    print('SKIP app.js (skeleton guard already present)')
else:
    assert app.count(OLD_A) == 1, 'app.js: skeleton anchor not unique: ' + str(app.count(OLD_A))
    app = app.replace(OLD_A, NEW_A, 1)
    print('PATCHED app.js (skeleton containment guard)')

write('js/app.js', app)

# ---------------------------------------------------------------- B ------

idx = read('index.html')
OLD_V, NEW_V = 'perf20260925c', 'perf20260925d'
if NEW_V in idx:
    print('SKIP index.html (buster already bumped)')
elif OLD_V in idx:
    idx = idx.replace(OLD_V, NEW_V)
    print('PATCHED index.html (app.js buster ' + OLD_V + ' -> ' + NEW_V + ')')
else:
    print('ERROR: app.js version param not found')
    sys.exit(1)
write('index.html', idx)

# ---------------------------------------------------------------- C ------

sw = read('sw.js')

OLD_C = """  var isData = url.pathname.indexOf('/data/') === 0;"""

NEW_C = """  /* 2026-09-25: admin time corrections must be visible on the next
     reload - network-first for the tiny overrides file, cache (or an
     empty object) only when offline. */
  if (url.pathname === '/data/time-overrides.json') {
    e.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok) {
          var cl = res.clone();
          caches.open(DATA_CACHE).then(function (c) { c.put(req, cl); });
        }
        return res;
      }).catch(function () {
        return caches.match(req).then(function (hit) {
          return hit || new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
        });
      })
    );
    return;
  }
  var isData = url.pathname.indexOf('/data/') === 0;"""

if 'admin time corrections must be visible' in sw:
    print('SKIP sw.js (network-first block already present)')
else:
    assert sw.count(OLD_C) == 1, 'sw.js: isData anchor not unique: ' + str(sw.count(OLD_C))
    sw = sw.replace(OLD_C, NEW_C, 1)
    print('PATCHED sw.js (time-overrides.json network-first)')

write('sw.js', sw)

# ------------------------------------------------------------ validate ----

errors = []
app2 = read('js/app.js')
idx2 = read('index.html')
sw2 = read('sw.js')

for needle in ['containment only for near-equal skeletons',
               'vs.length - qs.length <= 2']:
    if needle not in app2:
        errors.append('app.js: missing ' + needle)
if 'vs.includes(qs))) return true;' in app2:
    errors.append('app.js: old unguarded containment still present')

if 'perf20260925d' not in idx2:
    errors.append('index.html: buster not bumped')

for needle in ['admin time corrections must be visible',
               "url.pathname === '/data/time-overrides.json'",
               "new Response('{}'"]:
    if needle not in sw2:
        errors.append('sw.js: missing ' + needle)

if errors:
    print('VALIDATION FAILED:')
    for e in errors:
        print('  -', e)
    sys.exit(1)

print('VALIDATION OK')
