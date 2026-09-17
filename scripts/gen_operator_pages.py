#!/usr/bin/env python3
"""Generate operator/brand pages (SBSTC, NBSTC, WBTC, Shyamoli Paribahan,
Volvo AC buses) under bus-time-table/ — same design language as the place
pages — and register them in sitemap.xml + link them from the timetable
index. Idempotent: pages are regenerated, sitemap/index edits are guarded.
Run with no arguments (called from finalize_pages.py).
"""
import json, re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / 'bus-time-table'
DATA = json.loads((ROOT / 'data' / 'busjatri_data.json').read_text(encoding='utf-8'))
BASE = 'https://busjatri.in'

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', (s or '').lower()).strip('-')

AMP = chr(38)
def esc(s):
    return (s or '').replace(AMP, AMP + 'amp;').replace('<', AMP + 'lt;').replace('>', AMP + 'gt;').replace('"', AMP + 'quot;')

def src(b):
    return (b.get('source') or '').lower()

def btype(b):
    return (b.get('bus_type') or '')

def is_sbstc(b):
    return 'sbstc' in src(b) or 'SBSTC' in btype(b)

def is_nbstc(b):
    return 'nbstc' in src(b)

def is_wbtc(b):
    return 'wbtc' in src(b)

def is_shyamoli(b):
    return 'shyamoli' in src(b) or 'shyamoli' in (b.get('bus_name') or '').lower()

def is_volvo_ac(b):
    t = btype(b)
    return 'AC' in t and 'NON' not in t.upper()

OPERATORS = [
    dict(stem='sbstc-buses', name='SBSTC Buses', title='SBSTC Bus Time Table',
         h1='SBSTC Buses', bn='দক্ষিণবঙ্গ রাজ্য পরিবহণ সংস্থার বাস',
         desc='Complete SBSTC bus time table: routes, departure times and destinations across West Bengal.',
         intro='Explore listed SBSTC (South Bengal State Transport Corporation) bus services with routes, departure times and destinations.',
         pred=is_sbstc, tag='Government'),
    dict(stem='nbstc-buses', name='NBSTC Buses', title='NBSTC Bus Time Table',
         h1='NBSTC Buses', bn='উত্তরবঙ্গ রাজ্য পরিবহণ সংস্থার বাস',
         desc='Complete NBSTC bus time table: routes, departure times and destinations across West Bengal.',
         intro='Explore listed NBSTC (North Bengal State Transport Corporation) bus services with routes, departure times and destinations.',
         pred=is_nbstc, tag='Government'),
    dict(stem='wbtc-buses', name='WBTC Buses', title='WBTC Bus Time Table',
         h1='WBTC Buses', bn='পশ্চিমবঙ্গ পরিবহণ নিগমের বাস',
         desc='Complete WBTC (CSTC) bus time table: routes, departure times and destinations across Kolkata and West Bengal.',
         intro='Explore listed WBTC / CSTC (Calcutta State Transport Corporation) bus services with routes, departure times and destinations.',
         pred=is_wbtc, tag='Government'),
    dict(stem='shyamoli-paribahan-buses', name='Shyamoli Paribahan', title='Shyamoli Paribahan Bus Time Table',
         h1='Shyamoli Paribahan Buses', bn='শ্যামলী পরিবহনের বাস',
         desc='Shyamoli Paribahan (Green Line) AC Volvo bus time table: routes, departure times and destinations.',
         intro='Explore listed Shyamoli Paribahan AC Volvo bus services with routes, departure times and destinations.',
         pred=is_shyamoli, tag='Private'),
    dict(stem='volvo-ac-buses', name='Volvo AC Buses', title='Volvo AC Bus Time Table',
         h1='Volvo AC Buses', bn='এসি ভলভো বাস',
         desc='All Volvo AC bus time tables in West Bengal: routes, departure times and destinations.',
         intro='Explore every listed AC / Volvo bus service in West Bengal with routes, departure times and destinations.',
         pred=is_volvo_ac, tag='AC'),
]

HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | BusJatri</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{BASE}/bus-time-table/{stem}.html">
<meta property="og:title" content="{title} | BusJatri">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}/bus-time-table/{stem}.html">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="stylesheet" href="../css/seo.css">
<link rel="stylesheet" href="../css/extras.css">
<script type="application/ld+json">{{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{{"@type": "ListItem", "position": 1, "name": "Home", "item": "{BASE}/"}}, {{"@type": "ListItem", "position": 2, "name": "Bus Timetable", "item": "{BASE}/bus-time-table/"}}, {{"@type": "ListItem", "position": 3, "name": "{h1}", "item": "{BASE}/bus-time-table/{stem}.html"}}]}}</script>
</head>
<body>
<header class="header">
  <div class="container header-inner">
    <a href="../index.html" class="logo" style="text-decoration:none;color:inherit">
      <svg class="icon" viewBox="0 0 24 24" style="width:1.35rem;height:1.35rem;color:var(--amber)" aria-hidden="true">
        <path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/>
      </svg>
      Bus<span>Jatri</span>
    </a>
    <nav style="display:flex;gap:10px;align-items:center;font-size:13px">
      <a href="../index.html" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Home</a>
      <a href="./" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Routes</a>
    </nav>
  </div>
</header>
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">Bus Timetable</a> › <span>{h1}</span></div>
<h1 style="font-size:clamp(1.8rem,5vw,2.5rem);line-height:1.2;margin:0">{h1}</h1>
<div style="color:var(--ink-dim);margin-top:6px">{bn}</div>
<p style="color:var(--ink-dim);line-height:1.7;max-width:700px;margin-bottom:0">{intro}</p>
'''

ROW_T = '''<a href="{href}" class="bj-pop-row" style="
     display:flex;
     justify-content:space-between;
     gap:12px;
     padding:13px 14px;
     border-bottom:1px solid var(--border);
     text-decoration:none;
   ">
  <span>{fr} → {to}</span>
  <span style="color:var(--ink-dim);font-size:13px;white-space:nowrap">{n} buses</span>
</a>'''

FOOT = '''<footer class="footer">
  <div class="container">
    <div class="footer-links">
      <a href="../about.html">About Us</a>
      <a href="../contact.html">Contact Us</a>
      <a href="../privacy-policy.html">Privacy Policy</a>
      <a href="../about.html#credits">Credits</a>
      <a href="./">All Bus Timetables</a>
    </div>
    <p><strong>BusJatri</strong> — West Bengal Bus Timetable<br>
    Not affiliated with any transport corporation<br>
    Contact: <a href="mailto:busjatri@zohomail.in">busjatri@zohomail.in</a></p>
  </div>
</footer>
<style>.bj-pop-row{transition:background .15s}.bj-pop-row:hover{background:var(--amber-soft)}.bj-pop-row span:first-child{font-weight:600}.bj-pop-row:last-of-type{border-bottom-color:transparent}</style>
</body>
</html>
'''

def build_page(op, stems):
    buses = [b for b in DATA['buses'] if op['pred'](b)]
    routes = Counter()
    for b in buses:
        routes[(b.get('origin', ''), b.get('destination', ''))] += 1
    top = routes.most_common(15)
    dests = Counter()
    for b in buses:
        dests[b.get('destination', '')] += 1

    rows = []
    for (fr, to), n in top:
        target = f'{slug(fr)}-to-{slug(to)}'
        if target in stems:
            rows.append(ROW_T.format(href=target + '.html', fr=esc(fr), to=esc(to), n=n))
        else:
            rows.append(ROW_T.format(href='./', fr=esc(fr), to=esc(to), n=n))

    dest_href = {}
    for (fr, to), _n in routes.items():
        if to and to not in dest_href:
            t = f'{slug(fr)}-to-{slug(to)}'
            if t in stems:
                dest_href[to] = t + '.html'
    chips = []
    for i, (name, n) in enumerate(dests.most_common(40)):
        label = f'{name} ({n})' if name else '—'
        href = dest_href.get(name)
        if href:
            chips.append(f'<a class="via-chip" style="--i:{min(i, 15)}" href="{href}">{esc(label)}</a>')
        else:
            chips.append(f'<span class="via-chip" style="--i:{min(i, 15)}">{esc(label)}</span>')

    stats = f'''<section style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:32px">
  <div style="flex:1 1 170px;background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:15px">
    <div style="font-size:12px;color:var(--ink-dim)">Listed services</div>
    <strong style="font-size:1.6rem">{len(buses)}</strong>
  </div>
  <div style="flex:1 1 170px;background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:15px">
    <div style="font-size:12px;color:var(--ink-dim)">Routes</div>
    <strong style="font-size:1.6rem">{len(routes)}</strong>
  </div>
</section>'''

    popular = f'''<h2 style="font-size:1.25rem;margin:0 0 12px">Popular {esc(op['name'])} Routes</h2>
<div style="background:var(--panel);border:1px solid var(--border);border-radius:16px;overflow:hidden">
{''.join(rows)}
</div>'''

    chiprow = f'''<h2 style="font-size:1.25rem;margin:26px 0 12px">All Destinations</h2>
<div class="chip-row" aria-label="All destinations">{''.join(chips)}</div>'''

    body = HEAD.format(title=esc(op['title']), desc=esc(op['desc']), stem=op['stem'],
                       BASE=BASE, h1=esc(op['h1']), bn=op['bn'], intro=esc(op['intro']))
    body += stats + popular + chiprow + '\n</main>\n' + FOOT
    return body

def update_sitemap(stems):
    p = ROOT / 'sitemap.xml'
    s = p.read_text(encoding='utf-8')
    add = ''
    for op in OPERATORS:
        url = f'{BASE}/bus-time-table/{op["stem"]}.html'
        if url not in s:
            add += f'<url><loc>{url}</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>'
    if add:
        s = s.replace('</urlset>', add + '</urlset>')
        p.write_text(s, encoding='utf-8')
        print(f'  sitemap: +{len(OPERATORS)} operator pages')
    else:
        print('  sitemap: already up to date')

TTI_MARKER = 'id="bjOpsRow"'
TTI_BLOCK = '''<h3 class="section-title" style="margin-bottom:2px">Operators</h3>
<div class="chip-row" id="bjOpsRow" style="margin:0 0 18px">
  <a class="via-chip" href="sbstc-buses.html">SBSTC</a>
  <a class="via-chip" href="nbstc-buses.html">NBSTC</a>
  <a class="via-chip" href="wbtc-buses.html">WBTC</a>
  <a class="via-chip" href="shyamoli-paribahan-buses.html">Shyamoli Paribahan</a>
  <a class="via-chip" href="volvo-ac-buses.html">Volvo AC</a>
</div>
'''

def update_tti():
    p = PAGES / 'index.html'
    if not p.exists():
        return
    s = p.read_text(encoding='utf-8')
    if TTI_MARKER in s:
        print('  tti: operator links already present')
        return
    anchor = '<main'
    i = s.find(anchor)
    if i == -1:
        print('  tti: no <main> anchor, skipped')
        return
    j = s.find('>', i) + 1
    s = s[:j] + '\n' + TTI_BLOCK + s[j:]
    p.write_text(s, encoding='utf-8')
    print('  tti: operator links added')

def main():
    stems = {p.stem for p in PAGES.glob('*.html')}
    for op in OPERATORS:
        n = sum(1 for b in DATA['buses'] if op['pred'](b))
        (PAGES / f"{op['stem']}.html").write_text(build_page(op, stems), encoding='utf-8')
        print(f"  {op['stem']}.html: {n} buses")
    update_sitemap(stems)
    update_tti()
    print('operator pages done')

if __name__ == '__main__':
    main()
