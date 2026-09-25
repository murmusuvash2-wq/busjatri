#!/usr/bin/env python3
"""
2026-09-25 patch: fast bus pages + visible loading for data pages.

Problem (reported: "loading time kya jada le raha hai bus stoppage time
dekhne me"): render() awaited the full 1.9 MB app-index.json for EVERY
non-home route before rendering anything. A bus page ("bus stoppage
time dekhna") only needs its own ~1.5 KB data/bus-details/<id>.json,
but still waited for the whole index first - on slow mobile networks
that is easily 10+ seconds of staring at "Loading bus details...".

Fixes:
  A. render() no longer awaits the full index for /bus/ routes - the
     bus page renders from its own small file immediately (loadFullBus
     already has its own fallback to the aggregate file if needed).
  B. For routes that DO need the full index (search / stop / route /
     place), a spinner panel with EN + BN text is shown while the
     download runs, instead of a frozen screen.
  C. The full index download now also kicks off when the user FOCUSES
     any field (focusin), not only when they start typing.

Also bumps the app.js cache buster perf20260925d -> perf20260925e.

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

# ---------------------------------------------------------------- A+B ----

app = read('js/app.js')

OLD_A = """  if (hash !== '/' && hash !== '') { try { await ensureFullData(); } catch (e) {} }"""

NEW_A = """  /* 2026-09-25: bus pages only need their own ~1.5 KB bus-details file -
     never make them wait for the full 1.9 MB index. Other data pages
     (search/stop/route/place) do need it; show a spinner while it
     downloads instead of a frozen screen. */
  if (hash !== '/' && hash !== '' && !hash.startsWith('/bus/')) {
    if (!(DATA && DATA.buses)) {
      app.innerHTML = '<div class="container" style="padding:48px 16px;text-align:center">' +
        '<style>@keyframes bjspin{to{transform:rotate(360deg)}}.bj-ldr{display:inline-block;width:34px;height:34px;border:3px solid #e8ddc8;border-top-color:#b8791f;border-radius:50%;animation:bjspin .9s linear infinite;margin-bottom:14px}</style>' +
        '<div class="bj-ldr"></div>' +
        '<div style="font-size:15px">Loading all bus timings…</div>' +
        '<div class="label-bn" style="font-size:13px;color:var(--ink-dim);margin-top:4px">সব বাস টাইম টেবিল লোড হচ্ছে…</div>' +
        '</div>';
    }
    try { await ensureFullData(); } catch (e) {}
  }"""

if 'never make them wait for the full 1.9 MB index' in app:
    print('SKIP app.js render() (loading-ux already present)')
else:
    assert app.count(OLD_A) == 1, 'app.js: render await anchor not unique: ' + str(app.count(OLD_A))
    app = app.replace(OLD_A, NEW_A, 1)
    print('PATCHED app.js render() (bus fast path + spinner)')

# ---------------------------------------------------------------- C ------

OLD_C = """    document.addEventListener('input', function () {
      if (DATA && DATA.buses) return;
      kick();
    }, { passive: true });"""

NEW_C = """    document.addEventListener('input', function () {
      if (DATA && DATA.buses) return;
      kick();
    }, { passive: true });
    document.addEventListener('focusin', function () {
      if (DATA && DATA.buses) return;
      kick();
    }, { passive: true, capture: true });"""

if "addEventListener('focusin'" in app:
    print('SKIP app.js kick (focusin already present)')
else:
    assert app.count(OLD_C) == 1, 'app.js: input listener anchor not unique: ' + str(app.count(OLD_C))
    app = app.replace(OLD_C, NEW_C, 1)
    print('PATCHED app.js kick (focusin starts the download earlier)')

write('js/app.js', app)

# ---------------------------------------------------------------- D ------

idx = read('index.html')
OLD_V, NEW_V = 'perf20260925d', 'perf20260925e'
if NEW_V in idx:
    print('SKIP index.html (buster already bumped)')
elif OLD_V in idx:
    idx = idx.replace(OLD_V, NEW_V)
    print('PATCHED index.html (app.js buster ' + OLD_V + ' -> ' + NEW_V + ')')
else:
    print('ERROR: app.js version param not found')
    sys.exit(1)
write('index.html', idx)

# ------------------------------------------------------------ validate ----

errors = []
app2 = read('js/app.js')
idx2 = read('index.html')

for needle in ['never make them wait for the full 1.9 MB index',
               'bj-ldr', 'focusin', "hash.startsWith('/bus/')"]:
    if needle not in app2:
        errors.append('app.js: missing ' + needle)
if '{ try { await ensureFullData(); } catch (e) {} }' in app2:
    errors.append('app.js: old blanket await still present')
if 'perf20260925e' not in idx2:
    errors.append('index.html: buster not bumped')

if errors:
    print('VALIDATION FAILED:')
    for e in errors:
        print('  -', e)
    sys.exit(1)

print('VALIDATION OK')
