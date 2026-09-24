#!/usr/bin/env python3
# Preload fix - 2026-09-24
# patch_home_perf.py made app.js lazy (home-index.json first paint, app-index
# fetched on idle), but index.html still had a HIGH-priority preload of the
# 1.9MB data/app-index.json - so the browser downloaded the full payload on
# every homepage load anyway, defeating the perf win.
# This patcher points the preload at the 40KB data/home-index.json instead
# (exact URL match with the fetch in app.js, so the browser reuses it).
# Idempotent: safe to re-run.

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, 'index.html')

OLD = '<link rel="preload" as="fetch" href="data/app-index.json" />'
NEW = '<link rel="preload" as="fetch" href="data/home-index.json" />'

with open(PAGE, encoding='utf-8') as fh:
    html = fh.read()

if NEW in html:
    print('index.html already patched')
elif OLD in html:
    html = html.replace(OLD, NEW, 1)
    with open(PAGE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    print('index.html preload switched to home-index.json')
else:
    print('expected preload line not found - check manually')
    raise SystemExit(1)
