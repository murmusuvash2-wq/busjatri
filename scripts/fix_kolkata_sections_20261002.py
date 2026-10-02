#!/usr/bin/env python3
"""Kolkata sections restructure + audit fixes (2026-10-02).

Fixes everything found in the site audit:

1. Broken interlinks - 822 links on 91 pages under bus-time-table/ were written
   as href="bus-time-table/x.html" from inside bus-time-table/, resolving to
   bus-time-table/bus-time-table/x.html (404). The prefix is stripped.
2. Language labels - two pages had an unpaired label span (a Bengali string
   showing in English mode, and vice versa).
3. meta.last_updated - stale date on every page's freshness note.
4. Sitemap - 460+ existing pages (reverse-route pages, blog, the two Kolkata
   hubs, one via page) were missing from every sitemap; they are appended.
5. Duplicate freshness note - the reverse-route pages print the "Schedule data
   refreshed" line twice; the older one is dropped.
6. WBTC section - the WBTC page now separates long-distance services
   (Habra-Midpore, Barasat-Medinipur) from the city routes.
7. Kolkata City Bus hub - the misleading "(WBTC)" branding is removed from the
   title/description (the page also lists private city routes), and a pointer
   to the long-distance / WBTC sections is added.

No new pages, no bus data changes. Idempotent.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BT = ROOT / 'bus-time-table'
stats = {}


def bump(k, n=1):
    stats[k] = stats.get(k, 0) + n


def read(p):
    return p.read_text(encoding='utf-8', errors='ignore')


def write(p, s):
    p.write_text(s, encoding='utf-8')


# ---------------------------------------------------------------- 1. links
def fix_broken_links():
    for p in BT.glob('*.html'):
        h = read(p)
        if 'href="bus-time-table/' not in h:
            continue
        n = h.count('href="bus-time-table/')
        h = h.replace('href="bus-time-table/', 'href="')
        write(p, h)
        bump('broken_links_fixed', n)
        bump('broken_link_pages')


# ---------------------------------------------------------------- 2. labels
def fix_labels():
    # kolkata-to-balurghat.html: the English of this pair sits as plain text
    p = BT / 'kolkata-to-balurghat.html'
    if p.exists():
        h = read(p)
        old = '🚌 single daily service <span class="label-bn">দৈনিক একটি পরিষেবা</span>'
        new = '🚌 <span class="label-en">single daily service</span><span class="label-bn">দৈনিক একটি পরিষেবা</span>'
        if old in h:
            write(p, h.replace(old, new, 1))
            bump('label_fixes')
    # index.html: "Detected:" has no Bengali counterpart
    p = ROOT / 'index.html'
    h = read(p)
    old = '<span class="label-en">Detected:</span>'
    new = '<span class="label-en">Detected:</span><span class="label-bn">শনাক্ত:</span>'
    if old in h and 'শনাক্ত:' not in h:
        write(p, h.replace(old, new, 1))
        bump('label_fixes')


# ---------------------------------------------------------------- 3. meta
def fix_meta():
    p = ROOT / 'data' / 'busjatri_data.json'
    d = json.loads(read(p))
    today = str(date.today())
    if d.get('meta', {}).get('last_updated') != today:
        d.setdefault('meta', {})['last_updated'] = today
        write(p, json.dumps(d, ensure_ascii=False, indent=1))
        bump('meta_updated')


# ---------------------------------------------------------------- 4. sitemap
def fix_sitemap():
    sm_path = ROOT / 'sitemap.xml'
    sm = read(sm_path)
    have = set()
    for f in ROOT.glob('sitemap*.xml'):          # all sitemaps, so we never duplicate
        for loc in re.findall(r'<loc>([^<]+)</loc>', read(f)):
            have.add(loc.strip())
    base = 'https://busjatri.in/'

    def listed(url):
        # sitemaps mix /page.html and /page forms - accept either
        if url in have:
            return True
        return url.endswith('.html') and url[:-5] in have

    # pages that should be indexed
    skip = {'404.html', 'admin.html'}
    added = 0
    new_urls = []
    for p in sorted(ROOT.rglob('*.html')):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith('scripts/') or rel in skip:
            continue
        url = base + rel
        if not listed(url):
            new_urls.append(url)
    if new_urls:
        block = '\n'.join(f'  <url><loc>{u}</loc></url>' for u in new_urls)
        sm = sm.replace('</urlset>', block + '\n</urlset>')
        write(sm_path, sm)
        added = len(new_urls)
    bump('sitemap_added', added)


# ---------------------------------------------------------------- 5. dup note
def dedupe_freshness():
    pat = re.compile(
        r'<div class="trust-note"[^>]*><strong>Schedule data refreshed[^<]*</strong>[^<]*</div>'
        r'(?=<div class="trust-note"[^>]*><strong>Schedule data refreshed)', re.S)
    for p in BT.glob('*.html'):
        h = read(p)
        if h.count('Schedule data refreshed') < 2:
            continue
        new = pat.sub('', h)
        if new != h:
            write(p, new)
            bump('dup_note_pages')


# ---------------------------------------------------------------- 6. WBTC split
LONG_ROWS = [
    ('Habra → Midnapore', 'WBTC Habra-Midnapore', '4:55 AM · 5:25 AM · 5:55 AM · 6:20 AM', 'habra-to-midnapore.html'),
    ('Barasat → Medinipur', 'WBTC Barasat-Medinipur', '8:30 AM · 3:45 PM', 'barasat-to-medinipur.html'),
]


def wbtc_split():
    p = BT / 'wbtc-buses.html'
    h = read(p)
    if 'WBTC Long Routes' in h:
        return
    anchor = '<h2 class="op-h2">Popular WBTC Routes</h2>'
    if anchor not in h:
        return
    rows = '\n'.join(
        f'    <a class="op-card" href="{href}" style="display:block;border:1.5px solid var(--line,rgba(33,28,22,.15));'
        f'border-radius:12px;padding:10px 14px;margin:8px 0;text-decoration:none;color:inherit">'
        f'<b>{route}</b><div style="color:var(--ink-dim,#6b6257);font-size:13px">{name} · {times}</div></a>'
        for route, name, times, href in LONG_ROWS)
    block = (
        '<h2 class="op-h2">WBTC Long Routes — 6</h2>\n'
        '<p style="color:var(--ink-dim,#6b6257);font-size:13.5px;margin:6px 0 4px">'
        '<span class="label-en">These WBTC services run beyond the city (long distance). '
        'All other WBTC routes below are city routes.</span>'
        '<span class="label-bn">এই WBTC পরিষেবাগুলি শহরের বাইরে যায় (দূরপাল্লার)। '
        'নিচের বাকি WBTC রুটগুলি শহরের ভিতরের।</span></p>\n'
        + rows + '\n'
    )
    h = h.replace(anchor, block + anchor, 1)
    write(p, h)
    bump('wbtc_split')


# ---------------------------------------------------------------- 7. city hub
def city_hub():
    p = ROOT / 'kolkata-city-bus-timetable.html'
    h = read(p)
    changed = False
    # title: drop the misleading "(WBTC)"
    old_t = '<title>Kolkata City Bus Timetable (WBTC) — Search Routes, Times & Stops | BusJatri</title>'
    if old_t in h:
        h = h.replace(old_t, '<title>Kolkata City Bus Timetable — Search Routes, Times & Stops | BusJatri</title>', 1)
        changed = True
    # description: no longer WBTC-only
    m = re.search(r'<meta name="description" content="([^"]*)"', h)
    if m and 'WBTC' in m.group(1) and 'private' not in m.group(1).lower():
        newdesc = ('Kolkata city bus timetable — search WBTC and private city routes by from-to or stop. '
                   'In-city routes only; long-distance buses are listed in the All Bus Timetable.')
        h = h[:m.start(1)] + newdesc + h[m.end(1):]
        changed = True
    # pointer to the long-distance / WBTC sections
    anchor_m = re.search(r'<section[^>]*id=[\'"]private-routes[\'"]', h)
    if 'Long-distance buses' not in h and anchor_m:
        ptr = (
            '<section class="seo-section"><h3 class="section-title">'
            '<span class="label-en">Long-distance buses (outside the city)</span>'
            '<span class="label-bn">দূরপাল্লার বাস (শহরের বাইরে)</span></h3>'
            '<p class="seo-text"><span class="label-en">Buses leaving Kolkata — to Digha, Asansol, '
            'Bardhaman, Kharagpur and beyond — are not city routes. See '
            '<a href="bus-time-table/">All Bus Timetables</a> for every route, and '
            '<a href="bus-time-table/wbtc-buses.html">WBTC</a> for the government services.</span>'
            '<span class="label-bn">কলকাতা ছেড়ে যাওয়া বাস — দীঘা, আসানসোল, বর্ধমান, খড়্গপুর — '
            'সিটি রুট নয়। সব রুটের জন্য <a href="bus-time-table/">সব টাইমটেবিল</a> দেখুন, '
            'সরকারি পরিষেবার জন্য <a href="bus-time-table/wbtc-buses.html">WBTC</a>।</span></p></section>\n'
        )
        h = h[:anchor_m.start()] + ptr + h[anchor_m.start():]
        changed = True
    if changed:
        write(p, h)
        bump('city_hub')


def main():
    fix_broken_links()
    fix_labels()
    fix_meta()
    dedupe_freshness()
    wbtc_split()
    city_hub()
    fix_sitemap()
    print('done:', ', '.join(f'{k}={v}' for k, v in sorted(stats.items())))


if __name__ == '__main__':
    main()
