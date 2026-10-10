#!/usr/bin/env python3
"""Apply shared stats, trust copy, and accessibility/UX polish after page generation."""
from pathlib import Path
import json, re

ROOT = Path(__file__).resolve().parents[1]
meta = json.loads((ROOT / 'data' / 'busjatri_data.json').read_text(encoding='utf-8')).get('meta', {})
stops = int(meta.get('total_stops', 0))
routes = int(meta.get('total_routes', 0))
buses = int(meta.get('total_buses', 0))
updated = str(meta.get('last_updated', ''))
source_text = ' · '.join(meta.get('sources', [])[:4])
trust = (f'<div class="trust-note" role="note"><strong>Schedule data refreshed {updated}</strong> · '
         'Listed schedules can change; confirm with the operator before travel.</div>')
seo_css = '<style id="busjatri-ux-polish">\n.trust-note{margin:12px 0;padding:10px 14px;border:1px solid color-mix(in srgb,var(--accent,#b8791f) 35%,transparent);border-radius:12px;background:color-mix(in srgb,var(--accent,#b8791f) 8%,transparent);color:var(--ink-dim,#665);font-size:.82rem;line-height:1.5}.trust-note strong{color:var(--ink,#222)}\n.no-results,.empty-state{display:none}.bus-card{transition:transform .18s ease,box-shadow .18s ease}.bus-card:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(50,35,10,.10)}.bus-card .dep{font-variant-numeric:tabular-nums;white-space:nowrap}.missing-data{color:var(--ink-dim,#777);font-style:italic}\n@media(min-width:760px){.bus-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.bus-card{height:fit-content}.search-panel,.search-box{position:sticky;top:10px;z-index:4}.letter-nav{position:sticky;top:0;z-index:3;background:var(--paper,#fbf7ee);padding:8px 0}}\n@media(max-width:759px){.bus-card{border-radius:14px}.trust-note{font-size:.76rem}.letter-nav{overflow-x:auto;white-space:nowrap}}\n</style>'

def inject_once(s, marker, value):
    return s if value in s else s.replace(marker, value + marker, 1)

# Homepage labels are dynamic, but this also updates static copy if present.
p = ROOT / 'index.html'
s = p.read_text(encoding='utf-8')
s = s.replace('Live Departures', 'Next Scheduled Departures')
s = inject_once(s, '</main>', trust)
s = inject_once(s, '</head>', seo_css)
p.write_text(s, encoding='utf-8')

# Generated timetable index: use the same dataset truth everywhere.
p = ROOT / 'bus-time-table' / 'index.html'
s = p.read_text(encoding='utf-8')
# gen_seo_pages.py already baked the true counts into the stat chips
# (data-count). Read THOSE back and reuse them for the meta description and
# the FAQ, so every number on the page comes from one place and agrees.
# (Before this, the FAQ was overwritten from busjatri_data.json meta while
#  the chips came from live data -> the page contradicted itself.)
_counts = re.findall(r'data-count="([0-9]+)"', s)
if len(_counts) >= 3:
    _places, _routes, _buses = int(_counts[0]), int(_counts[1]), int(_counts[2])
else:
    _places, _routes, _buses = stops, routes, buses
old_desc = re.compile('Complete West Bengal bus time table: [^' + chr(34) + ']+')
new_desc = f'Complete West Bengal bus time table: {_routes:,} routes from {_places} places. Find SBSTC, WBTC, NBSTC and private bus timings with departure times, operators and stoppages.'
s = old_desc.sub(new_desc, s)
s = re.sub(r'The timetable covers [^<]+daily bus services listed[.]',
           f'The timetable covers {_routes:,} bus routes connecting {_places} places across West Bengal, with {_buses:,} listed bus services.', s)
s = s.replace('<b>No matches found</b>', '<b class="no-results">No matches found</b>')
s = s.replace('buses daily', 'listed buses')
s = inject_once(s, '<div class="stat-chips">', trust)
s = inject_once(s, '</head>', seo_css)
p.write_text(s, encoding='utf-8')

# Route pages: honest scheduled-data language, missing-value clarity, trust notice, and card polish.
for p in (ROOT / 'bus-time-table').glob('*.html'):
    if p.name == 'index.html':
        continue
    s = p.read_text(encoding='utf-8')
    s = s.replace("Today's Departures", 'Scheduled Departures')
    s = s.replace('Live Departures', 'Scheduled Departures')
    s = re.sub(r'>0 stops<', '><span class="missing-data">Stops not available</span><', s)
    s = inject_once(s, '<div class="stat-chips">', trust)
    s = inject_once(s, '</head>', seo_css)
    p.write_text(s, encoding='utf-8')

print(f'finalized pages with stats: {stops:,} stops, {routes:,} routes, {buses:,} buses; refreshed {updated}')

import subprocess, sys

# --- Kolkata city route design (CSTC times + private stops). MUST run after
#     gen_seo_pages.py: a plain regen overwrites bus-time-table/*.html with the
#     generic template and wipes the city route pages (stoppage list lost).
#     Idempotent. ---
subprocess.run([sys.executable, str(ROOT / 'scripts' / 'build_city_route_pages.py')], check=True)

# --- Operator pages (SBSTC/NBSTC/WBTC/Shyamoli/Volvo AC) + sitemap + index links ---
subprocess.run([sys.executable, str(ROOT / 'scripts' / 'gen_operator_pages.py')], check=True)

# --- Same hero design on every operator page (badge + description). The
#     generator emits a plain h1 and only SBSTC gets the badge, so this brings
#     the rest in line (idempotent). ---
subprocess.run([sys.executable, str(ROOT / 'scripts' / 'add_operator_badges.py')], check=True)

# --- GA4 analytics: keep the tag on every (re)generated page (idempotent) ---
subprocess.run([sys.executable, str(ROOT / 'scripts' / 'add_ga4.py')], check=True)

# --- Data-driven FAQ (visible + JSON-LD) on every route page (idempotent) ---
subprocess.run([sys.executable, str(ROOT / 'scripts' / 'add_faq.py')], check=True)

# --- Bus-row links + dark-mode toggle on every route page (idempotent) ---
subprocess.run([sys.executable, str(ROOT / 'scripts' / 'polish_route_pages.py')], check=True)

# --- Unify page headers: drop the stray Home/Routes nav links + the duplicate
#     theme button so every page header matches the standard one (idempotent). ---
subprocess.run([sys.executable, str(ROOT / 'scripts' / 'fix_headers.py')], check=True)

# --- Internal linking: a "Related routes & operators" block on every route page
#     (reverse route, same-origin / same-destination routes, operator pages and
#     the place page). Must run AFTER the route pages are generated, otherwise a
#     regen wipes it. Idempotent. ---
subprocess.run([sys.executable, str(ROOT / 'scripts' / 'add_related_links.py')], check=True)

# --- Homepage SEO: trimmed meta description (<=155 chars) + an H2 for the
#     "Popular Operators" block. Rank Math flagged a 191-char description and a
#     page with no H2. Idempotent. ---
subprocess.run([sys.executable, str(ROOT / 'scripts' / 'patch_home_seo_20261009.py')], check=True)
