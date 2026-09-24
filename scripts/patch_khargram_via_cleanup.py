#!/usr/bin/env python3
# Khargram via-page cleanup - 2026-09-24 (follow-up to patch_khargram_revert_20260924.py)
# The revert removed the 6 wrong buses, but 4 stale artifacts remained from
# the flyer run: via/khargram.html, its chip in via/index.html, its URL in
# sitemap-via.xml and in sitemap.xml. This patcher deletes the stale page and
# strips its URL from sitemap.xml (sitemap-via.xml + via/index.html get rebuilt
# from disk by gen_via_stop_v2.py + patch_via_sitemap.py in the workflow).
# Idempotent: safe to re-run.

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1) delete stale via stop page
page = os.path.join(ROOT, 'via', 'khargram.html')
if os.path.exists(page):
    os.remove(page)
    print('removed via/khargram.html')
else:
    print('via/khargram.html already absent')

# 2) strip its URL from sitemap.xml
SITEMAP_PATH = os.path.join(ROOT, 'sitemap.xml')
with open(SITEMAP_PATH, encoding='utf-8') as fh:
    sm = fh.read()
marker = '<url><loc>https://busjatri.in/via/khargram</loc>'
k = sm.find(marker)
if k >= 0:
    end = sm.find('</url>', k)
    if end >= 0:
        tail = end + len('</url>')
        sm = sm[:k] + sm[tail:]
        with open(SITEMAP_PATH, 'w', encoding='utf-8') as fh:
            fh.write(sm)
        print('sitemap.xml via/khargram entry removed')
    else:
        print('sitemap.xml entry malformed - url close not found')
else:
    print('sitemap.xml via/khargram entry already absent')
