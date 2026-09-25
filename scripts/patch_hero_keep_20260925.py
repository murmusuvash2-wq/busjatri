#!/usr/bin/env python3
"""
2026-09-25 patch (part 2 of mobile perf): keep the static hero alive.

Context: the static hero baked into index.html (perf part 1) fixed the
late JS hero paint, but renderHome() still REPLACED the whole #app
innerHTML with an identical hero once home-index.json arrived. That
identical re-paint became the LCP element (PSI mobile 72, LCP 4.7 s).

Changes:
  A. js/app.js - renderHome() no longer re-renders an existing #app > .hero:
     it parses its own template into a detached node, only rewrites the
     stats line if the numbers actually changed, and appends the sections
     below the kept hero. Nothing else in the hero is touched, so the
     early paint stays the LCP candidate.
  B. js/app.js - close the .hero div properly in the template (it used to
     stay open, so all sections parsed INSIDE the hero div; harmless
     visually, but the hero-preserve logic needs them outside).
  C. index.html - bake the (initially empty) geo-hint into the static hero
     so detectLocation() never has to insert it (insertion shifted the
     layout and re-painted the stats line).
  D. index.html - preload the two variable font files used by the
     above-the-fold text (Fraunces + IBM Plex Sans, latin) so the
     first paint uses the final fonts and the late font swap does not
     re-paint the LCP element.
  E. index.html - app.js cache buster perf20260925b -> perf20260925c.

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

changed = []

# ---------------------------------------------------------------- A+B ----

app = read('js/app.js')

OLD_A = """el.innerHTML = `
  <div class="hero">"""

NEW_A = """var homeHTML = `
  <div class="hero">"""

OLD_B = """  </div>`;
  renderBoard();
  detectLocation();"""

NEW_B = """  </div>`;
  /* 2026-09-25: keep the already-painted static hero (from index.html)
     instead of re-rendering it - the identical re-paint after data
     arrives was becoming the LCP element in PSI. Nothing is injected:
     the static markup already contains the geo hint (initially empty)
     and the stats numbers, which are only rewritten if they actually
     changed (a needless innerHTML write re-paints the element and
     resets LCP). The native datalist stays off - ux-fixes.js uses a
     custom autocomplete dropdown. */
  var keepHero = document.querySelector('#app > .hero');
  if (keepHero) {
    var tmp = document.createElement('div');
    tmp.innerHTML = homeHTML;
    var freshHero = tmp.querySelector('.hero');
    if (freshHero) {
      var s1 = keepHero.querySelector('.stats-inline');
      var s2 = freshHero.querySelector('.stats-inline');
      if (s1 && s2 && s1.innerHTML !== s2.innerHTML) s1.innerHTML = s2.innerHTML;
      freshHero.remove();
    }
    var sib = keepHero.nextElementSibling;
    while (sib) { var nx2 = sib.nextElementSibling; sib.remove(); sib = nx2; }
    while (tmp.firstChild) el.appendChild(tmp.firstChild);
  } else {
    el.innerHTML = homeHTML;
  }
  renderBoard();
  detectLocation();"""

OLD_C = """টি স্টপ</span></p>
  </div>
  <div class="section">"""

NEW_C = """টি স্টপ</span></p>
  </div>
  </div>
  <div class="section">"""

if 'keep the already-painted static hero' in app:
    print('SKIP app.js (hero-keep already present)')
else:
    assert app.count(OLD_A) == 1, 'app.js: hero assignment anchor not unique: ' + str(app.count(OLD_A))
    assert app.count(OLD_B) == 1, 'app.js: renderBoard/detectLocation anchor not unique: ' + str(app.count(OLD_B))
    assert app.count(OLD_C) == 1, 'app.js: hero close anchor not unique: ' + str(app.count(OLD_C))
    app = app.replace(OLD_A, NEW_A, 1)
    app = app.replace(OLD_B, NEW_B, 1)
    app = app.replace(OLD_C, NEW_C, 1)
    changed.append('app.js')
    print('PATCHED app.js (hero template close + keep static hero)')

write('js/app.js', app)

# ---------------------------------------------------------------- C-E ----

idx = read('index.html')

GEO = """<div class="geo-hint"><svg class="icon" viewBox="0 0 24 24"><path d="M12 21s7-6.1 7-11.3A7 7 0 0 0 5 9.7C5 14.9 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.3"/></svg> <span class="label-en">Detected:</span> <span class="geo-city"></span></div>"""
FROM_ANCHOR = """<input id="fromInput" placeholder="e.g. Bankura" onkeydown="if(event.key==='Enter'&&window.doSearch)doSearch()">"""

PRELOADS = """  <link rel="preload" as="font" type="font/woff2" crossorigin href="https://fonts.gstatic.com/s/fraunces/v38/6NUu8FyLNQOQZAnv9bYEvDiIdE9Ea92uemAk_WBq8U_9v0c2Wa0K7iN7hzFUPJH58nib14c7qv8oRcTn.woff2" />
  <link rel="preload" as="font" type="font/woff2" crossorigin href="https://fonts.gstatic.com/s/ibmplexsans/v23/zYXzKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1syxeKYbSB4Zh.woff2" />"""
PC_ANCHOR = """  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />"""

OLD_V, NEW_V = 'perf20260925b', 'perf20260925c'

if 'class="geo-hint"' in idx:
    print('SKIP index.html (geo-hint already present)')
else:
    assert idx.count(FROM_ANCHOR) == 1, 'index.html: fromInput anchor not unique: ' + str(idx.count(FROM_ANCHOR))
    NL = chr(10)
    idx = idx.replace(FROM_ANCHOR, FROM_ANCHOR + NL + GEO, 1)
    changed.append('index.html geo-hint')
    print('PATCHED index.html (geo-hint in static hero)')

if 'rel="preload" as="font"' in idx:
    print('SKIP index.html (font preloads already present)')
else:
    assert idx.count(PC_ANCHOR) == 1, 'index.html: preconnect anchor not unique: ' + str(idx.count(PC_ANCHOR))
    idx = idx.replace(PC_ANCHOR, PC_ANCHOR + chr(10) + PRELOADS, 1)
    changed.append('index.html font preload')
    print('PATCHED index.html (variable font preloads)')

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

for needle in ['keep the already-painted static hero', 'var homeHTML = `',
               "document.querySelector('#app > .hero')", 'tmp.innerHTML = homeHTML',
               's1.innerHTML !== s2.innerHTML']:
    if needle not in app2:
        errors.append('app.js: missing ' + needle)
if app2.count('detectLocation();') != 1:
    errors.append('app.js: detectLocation count != 1')
if app2.count('el.innerHTML = `' + chr(10) + '  <div class="hero">') != 0:
    errors.append('app.js: old full-replace hero assignment still present')

for needle in ['class="geo-hint"', 'rel="preload" as="font"', 'perf20260925c', 'geo-city']:
    if needle not in idx2:
        errors.append('index.html: missing ' + needle)

if errors:
    print('VALIDATION FAILED:')
    for e in errors:
        print('  -', e)
    sys.exit(1)

print('VALIDATION OK')
