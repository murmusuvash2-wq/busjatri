#!/usr/bin/env python3
"""
2026-09-25 patch: bigger "See more" batches on long pages.

User request: on long pages the See More button reveals too few items per
tap, so scrolling through a 100-800 item list needs many taps.

Changes (bus-row list pages):
  gen_via_stop_v2.py : KEEP 10 -> 15, STEP 20 -> 50  (via stop pages)
  gen_route_v2.py   : KEEP 10 -> 15, STEP 20 -> 50, button threshold
                       rows.length > 14 -> > 19 (route pages)
Changes (card grid pages):
  gen_stand_v2.py    : mstep 8 -> 24 (stand destination cards)
  gen_btt_v2.py      : mstep 8 -> 24 (BTT index stand cards)

Net effect: a 96-bus via page now needs 2 taps instead of 5; a 60-bus route
page needs 1 tap instead of 3; stand/BTT grids show 24 cards up front.

Only the four generator sources are patched here. The regeneration of the
actual HTML pages (route/stand/via/btt) happens in the companion workflow,
which runs the generators and commits the rebuilt pages.

Idempotent: safe to run twice. Backslash-free source.
"""

import ast
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

def patch(rel, pairs, done_marker):
    txt = read(rel)
    if done_marker in txt:
        print('SKIP', rel, '(already patched)')
        return
    for old, new in pairs:
        assert old in txt, rel + ': expected string not found: ' + old[:60]
        txt = txt.replace(old, new)
    write(rel, txt)
    print('PATCHED', rel)

# via stop pages: 10 + 20  ->  15 + 50
patch('scripts/gen_via_stop_v2.py', [
    ('var KEEP=10,STEP=20,btn=null;', 'var KEEP=15,STEP=50,btn=null;'),
], 'var KEEP=15,STEP=50,btn=null;')

# route pages: 10 + 20  ->  15 + 50, threshold 14 -> 19
patch('scripts/gen_route_v2.py', [
    ('var KEEP=10,STEP=20,btn=null;', 'var KEEP=15,STEP=50,btn=null;'),
    ('if(rows.length>14){', 'if(rows.length>19){'),
], 'var KEEP=15,STEP=50,btn=null;')

# stand pages: card batch 8 -> 24
patch('scripts/gen_stand_v2.py', [
    ('var mstep=8;', 'var mstep=24;'),
], 'var mstep=24;')

# BTT index: card batch 8 -> 24
patch('scripts/gen_btt_v2.py', [
    ('var mstep=8;', 'var mstep=24;'),
], 'var mstep=24;')

# ------------------------------------------------------------ validate ----
errors = []

checks = [
    ('scripts/gen_via_stop_v2.py', 'var KEEP=15,STEP=50,btn=null;', 'KEEP=10'),
    ('scripts/gen_route_v2.py', 'var KEEP=15,STEP=50,btn=null;', 'KEEP=10'),
    ('scripts/gen_stand_v2.py', 'var mstep=24;', 'var mstep=8;'),
    ('scripts/gen_btt_v2.py', 'var mstep=24;', 'var mstep=8;'),
]
for rel, want, notwant in checks:
    txt = read(rel)
    if want not in txt:
        errors.append(rel + ': new value missing')
    if notwant in txt:
        errors.append(rel + ': old value still present')

rt = read('scripts/gen_route_v2.py')
if 'rows.length>19' not in rt:
    errors.append('gen_route_v2.py: threshold 19 missing')
if 'rows.length>14' in rt:
    errors.append('gen_route_v2.py: old threshold still present')

# python syntax of all patched generators
for rel, _, _ in checks:
    try:
        ast.parse(read(rel))
    except SyntaxError as e:
        errors.append(rel + ': syntax error: ' + str(e))

if errors:
    print('VALIDATION FAILED:')
    for e in errors:
        print('  -', e)
    sys.exit(1)

print('VALIDATION OK')
print('Changed files:', len(CHANGED))
for rel in CHANGED:
    print('  -', rel)
