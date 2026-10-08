#!/usr/bin/env python3
"""add_related_links.py — strengthen internal linking on route pages.

Search Console shows route pages stuck at position 8-12. One reason is that a
route page barely links anywhere: it links to almost no other route page, so
crawl paths and internal PageRank are thin. This adds a "Related routes" block
to every route page linking to

  * the reverse route        (Kolkata -> Asansol, from Asansol -> Kolkata)
  * other routes from the same origin
  * other routes to the same destination
  * the operator page(s) for this route (SBSTC / NBSTC / WBTC / Shyamoli / Volvo AC)
  * the "Buses from <origin>" place page

Every target is checked against the pages that actually exist, so no dead links
are emitted. Idempotent: a page that already has class="related-routes" is left
alone, so this is safe to re-run.
"""

import glob
import html
import json
import os
import re
from collections import Counter, defaultdict

DATA = json.load(open('data/busjatri_data.json', encoding='utf-8'))
_raw = DATA['buses']
BUSES = _raw if isinstance(_raw, list) else list(_raw.values())

H1 = re.compile(r'<h1[^>]*>(.*?)</h1>', re.S)
ARR = re.compile(r'<span class="arr">.*?</span>', re.S)


def slug(s):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', (s or '').lower())).strip('-')


def h1_route(page_html):
    m = H1.search(page_html)
    if not m:
        return None
    txt = ARR.sub('|', m.group(1))
    txt = re.sub(r'<[^>]+>', '', txt)
    txt = html.unescape(txt)
    if '|' not in txt:
        return None
    a, b = txt.split('|', 1)
    a, b = a.strip(), b.strip()
    return (a, b) if a and b else None


PAGES = {os.path.basename(f)[:-5] for f in glob.glob('bus-time-table/*.html')}

route_ops = defaultdict(set)
from_origin = defaultdict(Counter)
to_dest = defaultdict(Counter)
for b in BUSES:
    o = (b.get('origin') or '').strip()
    d = (b.get('destination') or '').strip()
    if not o or not d:
        continue
    op = (b.get('operator') or '').strip()
    if op and op not in ('—', '-'):
        route_ops[(o, d)].add(op)
    from_origin[o][d] += 1
    to_dest[d][o] += 1

OP_STEMS = [
    ('sbstc', 'sbstc-buses', 'SBSTC'),
    ('nbstc', 'nbstc-buses', 'NBSTC'),
    ('wbtc', 'wbtc-buses', 'WBTC'),
    ('shyamoli', 'shyamoli-paribahan-buses', 'Shyamoli Paribahan'),
    ('volvo', 'volvo-ac-buses', 'Volvo AC'),
]


def operator_links(origin, dest):
    out = []
    seen = set()
    for op in sorted(route_ops.get((origin, dest), ())):
        low = op.lower()
        for needle, stem, label in OP_STEMS:
            if needle in low and stem not in seen and stem in PAGES:
                seen.add(stem)
                out.append((f'./{stem}', f'{label} buses'))
    return out[:3]


def chip(href, text):
    return f'<a class="rel-chip" href="{html.escape(href, quote=True)}">{html.escape(text)}</a>'


def build_block(origin, dest):
    chips = []
    rev = f'{slug(dest)}-to-{slug(origin)}'
    if rev in PAGES and rev != f'{slug(origin)}-to-{slug(dest)}':
        chips.append(chip(f'./{rev}', f'{dest} → {origin}'))
    for d2, _n in from_origin.get(origin, Counter()).most_common(9):
        s = f'{slug(origin)}-to-{slug(d2)}'
        if s in PAGES and d2 != dest:
            chips.append(chip(f'./{s}', f'{origin} → {d2}'))
        if len(chips) >= 7:
            break
    for o2, _n in to_dest.get(dest, Counter()).most_common(9):
        s = f'{slug(o2)}-to-{slug(dest)}'
        if s in PAGES and o2 != origin:
            chips.append(chip(f'./{s}', f'{o2} → {dest}'))
        if len(chips) >= 12:
            break
    for href, label in operator_links(origin, dest):
        chips.append(chip(href, label))
    place = f'buses-from-{slug(origin)}'
    if place in PAGES:
        chips.append(chip(f'./{place}', f'All buses from {origin}'))
    if not chips:
        return ''
    return (
        '<section class="related-routes" style="margin:26px 0 10px">'
        '<h2 style="font-size:1.05rem;margin:0 0 10px">'
        f'Related routes &amp; operators — {html.escape(origin)} to {html.escape(dest)}</h2>'
        f'<div class="via-chips">{"".join(chips)}</div>'
        '</section>'
    )


def main():
    changed = skipped = 0
    for path in sorted(glob.glob('bus-time-table/*.html')):
        base = os.path.basename(path)[:-5]
        if '-to-' not in base or base.startswith('buses-from'):
            skipped += 1
            continue
        page = open(path, encoding='utf-8').read()
        if 'class="related-routes"' in page:
            skipped += 1
            continue
        r = h1_route(page)
        if not r:
            skipped += 1
            continue
        block = build_block(*r)
        if not block:
            skipped += 1
            continue
        i = page.rfind('</main>')
        if i == -1:
            skipped += 1
            continue
        open(path, 'w', encoding='utf-8').write(page[:i] + block + page[i:])
        changed += 1
    print(f'related-link blocks added: {changed}   skipped: {skipped}')


if __name__ == '__main__':
    main()
