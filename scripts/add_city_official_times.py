#!/usr/bin/env python3
"""Add the official CSTC city-bus timetable to the Kolkata city pages,
in the EXISTING design (no new CSS).

Source: CSTC_Bus_Timetable.json (transport.wb.gov.in official listing, 73 routes
with departure + opposite-end arrival times for both directions).

A. kolkata-city-bus-timetable.html — every route card's bmeta gets the official
   journey time:  "119 buses/day"  ->  "119 buses/day · ~1h 50m"
B. each route page — a new section "Official Departure Times (CSTC)" using the
   page's own bus-row ok / bnum / broute / bmeta / tt-note markup:
     one card per direction (first + last + service count + duration)
     + a tt-note listing every official departure time.

Idempotent: guarded by <!-- city-official-v1 --> on pages, and a marker span on
the hub bmeta.
"""
import json, os, re
from statistics import median

BASE = os.path.join(os.path.dirname(__file__), "..")
BT = os.path.join(BASE, "bus-time-table")
HUB = os.path.join(BASE, "kolkata-city-bus-timetable.html")
MARK = "<!-- city-official-v1 -->"


def mins(t):
    m = re.match(r'(\d{1,2}):(\d{2})', t or '')
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def dur_fmt(m):
    if m is None:
        return ""
    h, mi = divmod(m, 60)
    return (f"{h}h {mi}m" if h else f"{mi}m")


def load_cstc():
    d = json.load(open('/scratch/saved/CSTC_Bus_Timetable.json', encoding='utf-8'))['routes']
    out = {}
    for k, v in d.items():
        rn = (v.get('route_no') or '').strip()
        if not rn:
            continue
        up = [(r['dep'], r.get('arv')) for r in v['rows'] if r.get('table') == 0 and r.get('dep')]
        dn = [(r['dep'], r.get('arv')) for r in v['rows'] if r.get('table') == 1 and r.get('dep')]
        durs = [mins(a2) - mins(a1) for a1, a2 in up if mins(a1) is not None and mins(a2) is not None and mins(a2) > mins(a1)]
        out[rn] = {'termini': v.get('termini') or [], 'up': up, 'dn': dn,
                   'dur': int(median(durs)) if durs else None}
    return out


def main():
    cstc = load_cstc()
    print(f"CSTC routes: {len(cstc)}")

    # ---------- A. hub cards ----------
    h = open(HUB, encoding='utf-8').read()
    hub_updates = 0
    def fix_card(m):
        nonlocal hub_updates
        card = m.group(0)
        rn = re.search(r'<div class="bnum">([^<]*)', card)
        bm = re.search(r'(<div class="bmeta">)(.*?)(</div>)', card, re.S)
        if not rn or not bm:
            return card
        key = rn.group(1).strip()
        info = cstc.get(key)
        if not info or info['dur'] is None:
            return card
        if '<!--d-->' in bm.group(2):
            return card
        new_meta = bm.group(2).rstrip() + f' <span style="color:var(--amber-ink,#6b4610);font-weight:700">· ~{dur_fmt(info["dur"])}</span><!--d-->'
        hub_updates += 1
        return card[:bm.start(2)] + new_meta + card[bm.end(2):]
    h2 = re.sub(r'<a class="bus-row ok"[^>]*>.*?</a>', fix_card, h, flags=re.S)
    if h2 != h:
        open(HUB, 'w', encoding='utf-8').write(h2)
    print(f"hub cards updated: {hub_updates}")

    # ---------- B. route pages ----------
    cards = re.findall(r'<a class="bus-row ok" href="([^"]+)"[^>]*>.*?<div class="bnum">([^<]*)', h, re.S)
    done = skipped = missing = 0
    for href, rn in cards:
        rn = rn.strip()
        info = cstc.get(rn)
        if not info:
            skipped += 1
            continue
        path = os.path.join(BASE, href if href.startswith('bus-time-table/') else 'bus-time-table/' + href)
        if not os.path.exists(path):
            missing += 1
            continue
        page = open(path, encoding='utf-8').read()
        if MARK in page:
            continue
        term = info['termini']
        a = term[0] if term else ''
        b = term[1] if len(term) > 1 else ''
        def card(dep_list, frm, to):
            if not dep_list:
                return ''
            first, last = dep_list[0][0], dep_list[-1][0]
            n = len(dep_list)
            return (f'<div class="bus-row ok"><div class="bnum">{first}</div>'
                    f'<div class="bmid"><div class="broute">{frm} &nbsp;→&nbsp; {to}</div>'
                    f'<div class="bmeta">{n} services · last {last} · ~{dur_fmt(info["dur"])}</div></div>'
                    f'<div class="bright"><span class="label-en">First</span><span class="label-bn">প্রথম</span></div></div>')
        all_up = ', '.join(x[0] for x in info['up'])
        all_dn = ', '.join(x[0] for x in info['dn'])
        sec = f'''{MARK}
<section class="seo-section">
  <h3 class="section-title"><span class="label-en">Official Departure Times (CSTC)</span><span class="label-bn">সরকারি ছাড়ার সময় (সিএসটিসি)</span></h3>
  {card(info['up'], a, b)}
  {card(info['dn'], b, a)}
  <p class="tt-note"><span class="label-en"><b>All official departures</b> (from the CSTC timetable, transport.wb.gov.in) — {a} → {b}: {all_up}{('  |  ' + b + ' → ' + a + ': ' + all_dn) if all_dn else ''}. Times can change; verify before travel. Spotted a change? Report it on our <a href="../contribute.html">Contribute page</a>.</span><span class="label-bn"><b>সব সরকারি ছাড়ার সময়</b> (সিএসটিসি সময়সূচি অনুযায়ী) — সময় বদলাতে পারে; যাত্রার আগে যাচাই করুন। পরিবর্তন দেখলে আমাদের <a href="../contribute.html">Contribute পেজে</a> জানান।</span></p>
</section>
'''
        # insert before the "About this route" section
        m = re.search(r'<section class="seo-section">\s*<h3 class="section-title"><span class="label-en">About this route', page)
        if m:
            page = page[:m.start()] + sec + page[m.start():]
        else:
            page = page.replace('</main>', sec + '\n</main>', 1)
        open(path, 'w', encoding='utf-8').write(page)
        done += 1
    print(f"route pages updated: {done} | skipped(no CSTC): {skipped} | no page: {missing}")


if __name__ == "__main__":
    main()
