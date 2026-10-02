#!/usr/bin/env python3
"""Add a "Private Long-Distance Routes" section to the All Bus Timetable hub.

The ~1,100 timed private long-distance services (bussathi / wbbus / shyamoli /
santosh ...) were only reachable as individual route pages. They are not city
routes and not WBTC, so they get their own listing on bus-time-table/index.html:

  * routes grouped by origin -> destination, most-served first
  * the earliest listed departure shown per route
  * a search CTA that opens every one of them

Derived from the existing data - no new buses, no new pages. Idempotent.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BT = ROOT / 'bus-time-table'
IDX = BT / 'index.html'
DATA = ROOT / 'data' / 'busjatri_data.json'
MARK = 'id="longDistanceSec"'
TOP_N = 30


def slug(s):
    return re.sub(r'^-|-$', '', re.sub(r'[^a-z0-9]+', '-', (s or '').lower()))


def to_min(t):
    m = re.match(r'^(\d{1,2}):(\d{2})\s*(AM|PM)$', (t or '').strip())
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap == 'AM':
        h = 0 if h == 12 else h
    else:
        h = 12 if h == 12 else h + 12
    return h * 60 + mi


def fmt(mins):
    h, mi = divmod(mins, 60)
    ap = 'AM' if h < 12 else 'PM'
    return f'{h % 12 or 12}:{mi:02d} {ap}'


def kolkata_city_places(buses):
    """City set = endpoints of WBTC routes + endpoints of the 254 city routes."""
    city = set()
    for b in buses:
        if 'WBTC' in (b.get('source') or ''):
            city.add((b.get('origin') or '').strip())
            city.add((b.get('destination') or '').strip())
    hub = ROOT / 'kolkata-city-bus-timetable.html'
    if hub.exists():
        h = hub.read_text(encoding='utf-8', errors='ignore')
        m = re.search(r'<details class="full-list">(.*?)</details>', h, re.S)
        if m:
            for href in re.findall(r'href="([^"]+)"', m.group(1)):
                fn = href.split('/')[-1][:-5]
                if '-to-' in fn:
                    o, de = fn.split('-to-', 1)
                    city.add(o.replace('-', ' ').strip())
                    city.add(de.replace('-', ' ').strip())
    return {c.lower() for c in city if len(c) > 1}


def main():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    buses = data['buses']
    city = kolkata_city_places(buses)

    def is_city(n):
        return (n or '').strip().lower() in city

    groups = defaultdict(list)
    for b in buses:
        if 'private' not in (b.get('bus_type') or '').lower():
            continue
        if not b.get('departure_time'):
            continue
        o, de = b.get('origin'), b.get('destination')
        if not o or not de or is_city(o) or is_city(de):
            continue
        groups[(o, de)].append(b)

    ranked = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0][0]))
    total = sum(len(v) for _, v in ranked)

    cards = []
    for (o, de), bs in ranked[:TOP_N]:
        firsts = [to_min(b.get('departure_time')) for b in bs]
        firsts = [f for f in firsts if f is not None]
        first = f'first {fmt(min(firsts))}' if firsts else 'times listed'
        cards.append(
            f'<a class="op-card" href="{slug(o)}-to-{slug(de)}.html">'
            f'<span class="rt">{o} <span class="arr">→</span> {de}</span>'
            f'<span class="meta">🚌 {len(bs)} bus{"es" if len(bs) > 1 else ""}</span>'
            f'<span class="go">{first} ›</span></a>')

    section = (
        f'<section class="section" {MARK}>'
        f'<h2 class="op-h2">Private Long-Distance Routes — {total}</h2>'
        '<p class="seo-text"><span class="label-en">Private services between towns across West Bengal '
        '— outside Kolkata city and separate from the WBTC routes. Departure times are shown where the '
        'operator publishes them.</span>'
        '<span class="label-bn">পশ্চিমবঙ্গের শহরগুলির মধ্যে বেসরকারি পরিষেবা — কলকাতা শহরের বাইরে এবং '
        'WBTC রুট থেকে আলাদা। যেখানে অপারেটর সময় প্রকাশ করে, সেখানে ছাড়ার সময় দেখানো হয়েছে।</span></p>'
        '<style>'
        '#longDistanceSec .op-cta-big{display:flex;gap:9px;align-items:center;justify-content:center;'
        'background:var(--amber,#b8791f);color:#fffcf4;text-decoration:none;font-weight:800;'
        'border-radius:13px;padding:14px 18px;font-size:15px;margin:16px 0 4px}'
        '#longDistanceSec .seo-text{color:var(--ink-dim,#6b6257);font-size:13.5px;line-height:1.6;margin:6px 0 14px}'
        '</style>'
        '<div class="op-grid">' + ''.join(cards) + '</div>'
        '<a class="op-cta op-cta-big" href="../index.html#/search?q=">'
        '<span class="label-en">Open all long-distance buses in search</span>'
        '<span class="label-bn">সার্চে সব দূরপাল্লার বাস দেখুন</span></a>'
        '</section>')

    h = IDX.read_text(encoding='utf-8', errors='ignore')
    if MARK in h:
        print('already present; nothing to do')
        return
    if '</main>' not in h:
        print('no </main> anchor; aborting')
        return
    h = h.replace('</main>', section + '\n</main>', 1)
    IDX.write_text(h, encoding='utf-8')
    print(f'done: long-distance section added — {total} services, top {min(TOP_N, len(ranked))} routes shown')


if __name__ == '__main__':
    main()
