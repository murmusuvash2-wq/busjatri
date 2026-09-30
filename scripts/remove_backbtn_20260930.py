#!/usr/bin/env python3
"""2026-09-30: Remove the static back-button (bjBackBtn) from all pages and
bump the seo-page.js cache version so browsers re-fetch the JS (old cached
JS still injected the button on route pages even though addBackBtn() was
disabled on 2026-09-29).

Usage:
  python3 scripts/remove_backbtn_20260930.py           # apply
  python3 scripts/remove_backbtn_20260930.py --dry-run # count only
"""
import glob
import re
import sys

DRY = '--dry-run' in sys.argv

# Exact verified variant (single distinct opening tag across the whole repo):
# <button type="button" id="bjBackBtn" class="back-nav" ... >...<svg .../>...</button>
BTN_RE = re.compile(
    r'<button type="button" id="bjBackBtn"[^>]*>.*?</button>\s*\n\s*', re.S)

OLD_VER = 'seo-page.js?v=uifix20260928a'
NEW_VER = 'seo-page.js?v=noback20260930'

files = [f for f in glob.glob('**/*.html', recursive=True)
         if not f.startswith('scripts/')]

btn_pages = []
btn_count = 0
ver_pages = []

for f in sorted(files):
    try:
        with open(f, encoding='utf-8') as fh:
            h = fh.read()
    except (UnicodeDecodeError, OSError):
        continue
    orig = h
    hits = BTN_RE.findall(h)
    if hits:
        btn_count += len(hits)
        btn_pages.append(f)
        h = BTN_RE.sub('', h)
    if OLD_VER in h:
        ver_pages.append(f)
        h = h.replace(OLD_VER, NEW_VER)
    if not DRY and h != orig:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(h)

print('back buttons removed:', btn_count, 'from', len(btn_pages), 'pages')
print('cache version bumped on', len(ver_pages), 'pages')
print('old version remaining:', sum(1 for f in files if False) or 'see validate step')

# sanity: no page should reference the button any more
left = [f for f in files if 'bjBackBtn' in open(f, encoding='utf-8', errors='ignore').read()]
print('pages still containing bjBackBtn:', len(left))
if left[:5]:
    print('examples:', left[:5])
