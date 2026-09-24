#!/usr/bin/env python3
"""
2026-09-25 patch: Map button alignment + Google Maps waypoint fix.

Problem 1: On bus pages the share row buttons (Map / WhatsApp / Facebook /
Report) all share one style EXCEPT Map, which sits ~4px lower. Cause: the old
app stylesheet css/style.css has .map-btn { margin: 4px 0 18px } and nothing
overrides margin for the compact share-row map button. Fix: add
.wa-row .map-btn { margin: 0 } to css/ux-fixes.css (loads last, higher
specificity), so Map aligns exactly with the other three buttons.

Problem 2: The route-map button sends 9 waypoints to Google Maps. Google Maps
supports at most 3 waypoints on mobile browsers (see Maps URLs docs), so on
phones the route line never draws. Fix: send at most 3 waypoints, evenly
spread over the route, and encode the pipe separator as %7C per spec.

Files changed:
  css/ux-fixes.css  - margin override for .wa-row .map-btn
  js/app.js         - waypoint sampling 8 -> 3, join with %7C
  js/bus-page.js     - waypoint sampling 8 -> 3, join with %7C
  js/ux-fixes.js    - MAXW 9 -> 3, join with %7C
  index.html        - cache-buster version bumps for the four assets

Idempotent: safe to run twice. Backslash-free source.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHANGED = []

def read(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as fh:
        return fh.read()

def write(rel, content):
    with open(os.path.join(ROOT, rel), 'w', encoding='utf-8') as fh:
        fh.write(content)
    CHANGED.append(rel)

# ---------------------------------------------------------------- CSS ----
css_rel = 'css/ux-fixes.css'
css = read(css_rel)
MARGIN_FIX = '''
/* 2026-09-25: map button must align with WhatsApp/Facebook/Report.
   Old .map-btn rule in style.css has margin 4px 0 18px which pushed
   the share-row map button down. Grid row items need margin 0. */
.wa-row .map-btn{margin:0}
'''
if '.wa-row .map-btn{margin:0}' not in css:
    if css and css[-1:] != chr(10):
        css += chr(10)
    write(css_rel, css + MARGIN_FIX)
    print('PATCHED', css_rel, '(margin override added)')
else:
    print('SKIP', css_rel, '(already patched)')

# ------------------------------------------------------------- app.js ----
app_rel = 'js/app.js'
app = read(app_rel)
APP_OLD = """    const waypoints = stopNames.slice(1, -1).slice(0, 8).map(n => encodeURIComponent(n + ', West Bengal')).join('|');
"""
APP_NEW = """    const inters = stopNames.slice(1, -1);
    const wsel = [];
    const WN = Math.min(3, inters.length);
    for (let i = 0; i < WN; i++) {
      const n = inters[Math.round(i * (inters.length - 1) / Math.max(1, WN - 1))];
      if (wsel.indexOf(n) === -1) wsel.push(n);
    }
    const waypoints = wsel.map(n => encodeURIComponent(n + ', West Bengal')).join('%7C');
"""
if 'const waypoints = wsel.map' not in app:
    assert APP_OLD in app, 'app.js: expected waypoint line not found'
    write(app_rel, app.replace(APP_OLD, APP_NEW))
    print('PATCHED', app_rel)
else:
    print('SKIP', app_rel, '(already patched)')

# --------------------------------------------------------- bus-page.js ----
bp_rel = 'js/bus-page.js'
bp = read(bp_rel)
BP_OLD = """    const wp = stopNames.slice(1, -1).slice(0, 8).map(n => encodeURIComponent(n + ', West Bengal')).join('|');
"""
BP_NEW = """    const inters = stopNames.slice(1, -1);
    const wsel = [];
    const WN = Math.min(3, inters.length);
    for (let i = 0; i < WN; i++) {
      const n = inters[Math.round(i * (inters.length - 1) / Math.max(1, WN - 1))];
      if (wsel.indexOf(n) === -1) wsel.push(n);
    }
    const wp = wsel.map(n => encodeURIComponent(n + ', West Bengal')).join('%7C');
"""
if 'const wp = wsel.map' not in bp:
    assert BP_OLD in bp, 'bus-page.js: expected waypoint line not found'
    write(bp_rel, bp.replace(BP_OLD, BP_NEW))
    print('PATCHED', bp_rel)
else:
    print('SKIP', bp_rel, '(already patched)')

# --------------------------------------------------------- ux-fixes.js ----
ux_rel = 'js/ux-fixes.js'
ux = read(ux_rel)
UX_OLD_MAXW = """    var MAXW = 9;
"""
UX_NEW_MAXW = """    var MAXW = 3;
"""
UX_OLD_JOIN = ".join('|') : '') +"
UX_NEW_JOIN = ".join('%7C') : '') +"
need_write = False
if 'var MAXW = 9;' in ux:
    assert UX_OLD_MAXW in ux, 'ux-fixes.js: MAXW line not found'
    ux = ux.replace(UX_OLD_MAXW, UX_NEW_MAXW)
    need_write = True
if UX_OLD_JOIN in ux:
    ux = ux.replace(UX_OLD_JOIN, UX_NEW_JOIN)
    need_write = True
if need_write:
    write(ux_rel, ux)
    print('PATCHED', ux_rel)
else:
    print('SKIP', ux_rel, '(already patched)')

# ---------------------------------------------------------- index.html ----
idx_rel = 'index.html'
idx = read(idx_rel)
BUMPS = [
    ('css/ux-fixes.css?v=ux20260921b', 'css/ux-fixes.css?v=ux20260925a'),
    ('js/app.js?v=perf20260924a', 'js/app.js?v=perf20260925a'),
    ('js/bus-page.js?v=bj20260923b', 'js/bus-page.js?v=bj20260925a'),
    ('js/ux-fixes.js?v=rpt20260924a', 'js/ux-fixes.js?v=rpt20260925a'),
]
need_write = False
for old, new in BUMPS:
    if old in idx:
        idx = idx.replace(old, new)
        need_write = True
if need_write:
    write(idx_rel, idx)
    print('PATCHED', idx_rel, '(cache busters bumped)')
else:
    print('SKIP', idx_rel, '(already bumped or patterns changed)')

# ----------------------------------------------------------- validate ----
errors = []

if '.wa-row .map-btn{margin:0}' not in read('css/ux-fixes.css'):
    errors.append('ux-fixes.css: margin override missing')

for rel in ['js/app.js', 'js/bus-page.js']:
    txt = read(rel)
    if 'slice(0, 8)' in txt:
        errors.append(rel + ': old slice(0, 8) still present')
    if "join('%7C')" not in txt:
        errors.append(rel + ': %7C join missing')

ux_check = read('js/ux-fixes.js')
if 'MAXW = 9' in ux_check:
    errors.append('ux-fixes.js: MAXW still 9')
if "join('%7C')" not in ux_check:
    errors.append('ux-fixes.js: %7C join missing')
if ".join('|')" in ux_check:
    errors.append('ux-fixes.js: raw pipe join still present')

idx_check = read('index.html')
for expect in ['ux20260925a', 'perf20260925a', 'bj20260925a', 'rpt20260925a']:
    if expect not in idx_check:
        errors.append('index.html: version ' + expect + ' missing')

if errors:
    print('VALIDATION FAILED:')
    for e in errors:
        print('  -', e)
    sys.exit(1)

print('VALIDATION OK')
print('Changed files:', len(CHANGED))
for rel in CHANGED:
    print('  -', rel)
