#!/usr/bin/env python3
"""Patch js/stop-search-all.js + index.html (2026-09-25): redBus deep links.

1. Every search result card gets a small amber 'Book' chip (bottom-right)
   linking to redBus with THAT bus's route prefilled
   (redbus.in/bus-tickets/<from>-to-<to>). nofollow + new tab +
   stopPropagation so the card's own bus-page link keeps working.
2. When a from+to route is set, a 'Check fares & book on redBus' link
   renders under the results header (route-level deep link).
3. index.html: stop-search-all.js buster bj20260925a -> bj20260925b.

Backslash-free (asserted). Idempotent: exits 0 if already applied.
"""
from pathlib import Path
import sys

HERE = Path(__file__)
assert chr(92) not in HERE.read_text(encoding='utf-8'), 'patcher must stay backslash-free'

ROOT = HERE.resolve().parents[1]
js = ROOT / 'js' / 'stop-search-all.js'
src = js.read_text(encoding='utf-8')

if 'bookChip' in src:
    print('stop-search-all.js: bookChip already present, nothing to do')
    sys.exit(0)

Q = chr(39)  # single quote
D = chr(34)  # double quote

DEFS = '''      function rbSlug(s) { return String(s || '').toLowerCase().replace(new RegExp('[^a-z0-9]+', 'g'), '-').replace(new RegExp('^-+|-+$', 'g'), ''); }
      var redbUrl = (from && to) ? ('https://www.redbus.in/bus-tickets/' + rbSlug(from) + '-to-' + rbSlug(to)) : '';
      var redbHtml = (redbUrl && rows.length) ? ('<p style="text-align:center;font-size:13px;margin:4px 0 12px"><a href="' + redbUrl + '" target="_blank" rel="nofollow noopener" style="color:var(--amber,#b8791f);font-weight:700;text-decoration:none">' + String.fromCharCode(127915) + ' <span class="label-en">Check fares & book on redBus</span><span class="label-bn">রেডবাসে ভাড়া দেখুন</span> ' + String.fromCharCode(8599) + '</a></p>') : '';
      function bookChip(fr, td) {
        return '<a href="https://www.redbus.in/bus-tickets/' + rbSlug(fr) + '-to-' + rbSlug(td) + '" target="_blank" rel="nofollow noopener" onclick="event.stopPropagation()" title="Check fares & seats on redBus" style="position:absolute;right:14px;bottom:12px;background:var(--amber,#b8791f);color:#fffcf4;border-radius:999px;padding:6px 13px;font-size:11.5px;font-weight:800;text-decoration:none;display:inline-flex;align-items:center;gap:5px">' + String.fromCharCode(127915) + ' <span class="label-en">Book</span><span class="label-bn">বুক করুন</span></a>';
      }
'''

A1 = '      var opHtml = opq ? ('
assert src.count(A1) == 1, 'anchor 1 (opHtml) not unique'
src = src.replace(A1, DEFS + A1)

A2 = 'viaHtml + timeHtml + opHtml +'
assert src.count(A2) == 1, 'anchor 2 (header concat) not unique'
src = src.replace(A2, 'viaHtml + timeHtml + opHtml + redbHtml +')

A3 = ' + i + ' + Q + D + ' onclick=' + D + 'location.hash='
assert src.count(A3) == 1, 'anchor 3 (card style) not unique: ' + str(src.count(A3))
src = src.replace(A3, ' + i + ' + Q + ';position:relative' + D + ' onclick=' + D + 'location.hash=')

A4 = Q + '</div>' + Q + ' + tPill + ' + Q + '</div>' + Q + ';'
assert src.count(A4) == 1, 'anchor 4 (card close) not unique'
src = src.replace(A4, Q + '</div>' + Q + ' + tPill + bookChip(ro, rd) + ' + Q + '</div>' + Q + ';')

js.write_text(src, encoding='utf-8')
print('stop-search-all.js: rbSlug + redbHtml + bookChip added')

idx = ROOT / 'index.html'
s = idx.read_text(encoding='utf-8')
OLD_B = 'stop-search-all.js?v=bj20260925a'
NEW_B = 'stop-search-all.js?v=bj20260925b'
if NEW_B in s:
    print('index.html: buster already bj20260925b')
elif OLD_B in s:
    idx.write_text(s.replace(OLD_B, NEW_B), encoding='utf-8')
    print('index.html: stop-search-all buster bj20260925a -> bj20260925b')
else:
    raise SystemExit('index.html: expected buster bj20260925a not found')
print('patch_redbus_chips done')
