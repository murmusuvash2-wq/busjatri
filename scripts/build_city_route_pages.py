#!/usr/bin/env python3
"""Kolkata CITY route pages — unified design for CSTC (with times) + private (stops only).

Design: hero (bidirectional) + direction switch + compact vertical trips with
click-drop-down (times) OR stops-only list (no time). Dark toggle, breadcrumb
(Home / Kolkata City Bus / Route), popular routes interlinked, FAQ + About.
Idempotent; run AFTER gen_seo_pages.py.
"""
from city_route_lib import *
from components.footer import footer_html
import json, os, re, html

def header():
    """Canonical site header (same as every other bus-time-table page).

    Uses the shared bj-nav control cluster wired by js/hdr.js, so city route
    pages match the rest of the site (see scripts/unify_header_20261002.py).
    """
    return (
        '<header class="header">\n'
        '  <div class="container header-inner" style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px">\n'
        '    <a href="../" class="logo" style="text-decoration:none;color:inherit;display:flex;align-items:center;gap:8px">\n'
        '      <img class="brand-logo" src="/logo.png" alt="BusJatri" style="width:30px;height:30px;border-radius:50%;object-fit:contain">\n'
        '      Bus<span>Jatri</span>\n'
        '    </a>\n'
        '    <style id="bjHdrCss">.label-bn{display:none!important}body.lang-bn .label-en{display:none!important}body.lang-bn .label-bn{display:inline!important}</style>\n'
        '    <nav class="bj-nav" style="display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center;font-size:13px;margin-left:auto;justify-content:flex-end">\n'
        '      <span class="bj-lang" style="display:flex;gap:4px;margin-left:2px">\n'
        '        <button type="button" id="langEn" class="bj-langbtn" style="background:var(--amber-soft,#f6e7c6);border:1px solid var(--line,#d8cfc0);border-radius:999px;padding:3px 10px;font-weight:700;font-size:12px;cursor:pointer;color:var(--ink,#2b2118);font-family:inherit;line-height:1.2;white-space:nowrap;flex:0 0 auto">EN</button>\n'
        '        <button type="button" id="langBn" class="bj-langbtn" style="background:transparent;border:1px solid var(--line,#d8cfc0);border-radius:999px;padding:3px 10px;font-weight:700;font-size:12px;cursor:pointer;color:var(--ink,#2b2118);font-family:inherit;line-height:1.2;white-space:nowrap;flex:0 0 auto">\u09ac\u09be\u0982\u09b2\u09be</button>\n'
        '      </span>\n'
        '      <button type="button" id="themeBtn" class="bj-themebtn" aria-label="Toggle dark mode" title="Toggle dark mode" style="width:30px;height:30px;border-radius:50%;border:1px solid var(--line,#d8cfc0);background:transparent;color:var(--ink,#2b2118);display:inline-flex;align-items:center;justify-content:center;cursor:pointer;padding:0;flex:0 0 auto"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z"/></svg></button>\n'
        '    </nav>\n'
        '  </div>\n'
        '</header>')

def shell(title, desc, canonical, body, jsonld):
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))}</script>' if jsonld else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canonical}">
<meta property="og:type" content="article"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canonical}"><meta property="og:site_name" content="BusJatri"><meta property="og:image" content="{BASE}/og-image.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="theme-color" content="#b8791f">
<link rel="icon" href="../favicon.svg"><link rel="stylesheet" href="../css/seo.css?v=city20261006"><link rel="stylesheet" href="../css/extras.css"><link rel="stylesheet" href="../css/cstc-city.css?v=city20261006">
{CSS}{ld}</head><body>{header()}<main class="container seo-main">{body}</main>
{footer_html("../")}
<script defer src="../js/hdr.js?v=hdrunify20261005d"></script><script defer src="../js/lang.js?v=lang20261005c"></script>
<script>function bjTheme(){{var d=document.body.classList.toggle('dark');try{{localStorage.setItem('seo-theme',d?'dark':'light')}}catch(e){{}}document.getElementById('themeBtn').textContent=d?'☀':'☾'}}
try{{if(localStorage.getItem('seo-theme')==='dark')document.body.classList.add('dark')}}catch(e){{}}
function sw(i,b){{document.querySelectorAll('.dswitch button').forEach(function(x){{x.classList.remove('on')}});b.classList.add('on');document.querySelectorAll('.dpanel').forEach(function(p){{p.classList.toggle('on',+p.dataset.dir===i)}});}}
function pick(el){{var o=el.classList.contains('open');document.querySelectorAll('.trip.open').forEach(function(t){{t.classList.remove('open')}});if(!o)el.classList.add('open');}}</script>
</body></html>'''

def popular_html(others):
    if not others: return ''
    chips = ''.join(f'<a class="pchip" href="{esc(href)}"><span class="rn">{esc(rn)}</span>{esc(name)}</a>' for rn, name, href in others)
    return f'<section class="sec"><h2><span class="label-en">Popular Kolkata city bus routes</span><span class="label-bn">জনপ্রিয় কলকাতা শহরের বাস রুট</span></h2><div class="pchips">{chips}</div></section>'

def faq_html(faqs):
    items = ''.join(f'<details><summary>{esc(q)}</summary><div class="a">{esc(a)}</div></details>' for q, a in faqs)
    return f'<section class="sec faq"><h2><span class="label-en">Frequently asked questions</span><span class="label-bn">সাধারণ প্রশ্ন উত্তর</span></h2>{items}</section>'

def about_html(txt):
    return f'<section class="sec"><h2><span class="label-en">About this route</span><span class="label-bn">এই রুটের বিবরণ</span></h2><div class="about">{txt}</div></section>'

def short_ends(t):
    """'DUDUM STATION -> HOWRAH STN.' -> ('Dum Dum Stn', 'Howrah Stn')"""
    p = (t or '').replace('->', '|').split('|')
    def fix(x):
        x = re.sub(r'\s+', ' ', x).strip(' .')
        x = re.sub(r'STATION|STN\.?|STN', 'Stn', x, flags=re.I)
        x = re.sub(r'\bDudum\b', 'Dum Dum', x, flags=re.I)
        return x.title()
    return (fix(p[0]), fix(p[1])) if len(p) == 2 else (fix(t or ''), '')

# ---------------- city route with no published timetable (stops only) ----------------
def cstc_stops_page(route, obj, dirs, a0, b0, others):
    """City routes (AC-2, C43, S-9C …) have no published departure times — only
    the route and its stoppages. Renders the same CSTC design but stops-only."""
    title = f'{a0} to {b0} Bus Route ({route}) | BusJatri'
    desc = (f'{route} Kolkata city bus route — {a0} ⇄ {b0}, {len(dirs[0].get("stoppages") or [])} stoppages. '
            f'City buses run to frequency (no fixed timetable). English and Bengali details on BusJatri.')[:300]
    canonical = f'{BASE}/bus-time-table/cstc-{slug(route)}'

    btns, panels = [], []
    for di, d in enumerate(dirs):
        x, y = short_ends(d['direction'])
        stops = d.get('stoppages') or []
        btns.append(f'<button class="{"on" if di==0 else ""}" onclick="sw({di},this)">{esc(x)} <span class="ar">→</span> {esc(y)}</button>')
        lis = ''.join(f'<li><span class="cstc-stop-dot"></span>{esc(s)}</li>' for s in stops)
        panels.append(f'<div class="dpanel{" on" if di==0 else ""}" data-dir="{di}">'
                      f'<div class="meta">{len(stops)} <span class="label-en">stops · runs to frequency</span><span class="label-bn">স্টপ · ফ্রিকোয়েন্সি অনুযায়ী চলে</span></div>'
                      f'<section class="cstc-stops" style="margin-top:0"><div class="cstc-stops-head">'
                      f'<strong><span class="label-en">Stop list</span><span class="label-bn">স্টপ তালিকা</span></strong><span>{len(stops)} <span class="label-en">stops</span><span class="label-bn">স্টপ</span></span></div><ol>{lis}</ol></section></div>')
    stops0 = dirs[0].get('stoppages') or []
    body = (f'<div class="crumb"><a href="../"><span class="label-en">Home</span><span class="label-bn">হোম</span></a> / <a href="../kolkata-city-bus-timetable"><span class="label-en">Kolkata City Bus</span><span class="label-bn">কলকাতা শহরের বাস</span></a> / <span>{esc(route)}</span></div>'
            f'<section class="hero"><span class="eyebrow"><span class="label-en">WBTC city route</span><span class="label-bn">WBTC সিটি রুট</span></span>'
            f'<h1><span class="rcode">{esc(route)}</span>{esc(a0)} <span class="bi">⇄</span> {esc(b0)}</h1>'
            f'<div class="stats"><span class="stat"><b>{len(stops0)}</b> <span class="label-en">stops</span><span class="label-bn">স্টপ</span></span>'
            f'<span class="stat"><span class="label-en">Runs to <b>frequency</b></span><span class="label-bn"><b>ফ্রিকোয়েন্সি</b> অনুযায়ী চলে</span></span></div>'
            f'<p class="note" style="margin:10px 0 0;color:var(--ink-dim,#665);font-size:13.5px">'
            f'<span class="label-en">City buses on this route have no fixed departure times — they run to frequency. Times shown elsewhere are not published by the operator; confirm at the stand.</span>'
            f'<span class="label-bn">এই রুটে সিটি বাসগুলি নির্দিষ্ট সময়সূচি ছাড়া ফ্রিকোয়েন্সি অনুযায়ী চলে। স্ট্যান্ড থেকে সময় যাচাই করে নিন।</span></p></section>'
            f'<div class="dswitch" role="tablist">{"".join(btns)}</div>{"".join(panels)}')
    faqs = [(f'Does route {route} have a timetable?',
             f'No — {route} is a Kolkata city bus route and runs to frequency, so there are no fixed departure times. The route and its {len(stops0)} stoppages are listed here.'),
            (f'Which stops does route {route} cover?',
             f'Route {route} has {len(stops0)} stops: {", ".join(stops0[:8])}.'),
            (f'Where does route {route} run between?',
             f'Route {route} connects {a0} and {b0} in both directions.'),
            (f'Who runs route {route}?', f'Route {route} is a WBTC (West Bengal Transport Corporation) Kolkata city route.')]
    about = (f'<p>Route <b>{route}</b> is a Kolkata city bus route connecting <b>{esc(a0)}</b> and <b>{esc(b0)}</b> '
             f'in both directions, with {len(stops0)} stoppages. City buses run to frequency — there is no published timetable.</p>'
             f'<p>Spotted a change? <a href="../contact">Tell us</a>.</p>')
    jsonld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    body += popular_html(others) + faq_html(faqs) + about_html(about)
    return shell(title, desc, canonical, body, jsonld)


# ---------------- CSTC page (with times) ----------------
def cstc_page(route, obj, others):
    dirs = obj.get('directions') or []
    a0, b0 = short_ends(dirs[0]['direction']) if dirs else ('', '')
    total = sum(len(d.get('departures') or []) for d in dirs)
    stops0 = (dirs[0].get('stoppages') or []) if dirs else []
    if total == 0:
        # city route with no published timetable — stops only
        return cstc_stops_page(route, obj, dirs, a0, b0, others)
    title = f'{a0} to {b0} Bus Timetable ({route}) | BusJatri'
    desc = (f'{route} CSTC Kolkata city bus timetable — {total} departures, first/last times and {len(stops0)} stoppages '
            f'for {a0} ⇄ {b0}. English and Bengali route details on BusJatri.')[:300]
    canonical = f'{BASE}/bus-time-table/cstc-{slug(route)}'

    # direction switch
    btns = []
    panels = []
    for di, d in enumerate(dirs):
        x, y = short_ends(d['direction']); deps = d.get('departures') or []; arrs = d.get('arrivals') or []
        btns.append(f'<button class="{"on" if di==0 else ""}" onclick="sw({di},this)">{esc(x)} <span class="ar">→</span> {esc(y)}</button>')
        stops = d.get('stoppages') or []
        n = max(len(deps), len(arrs))
        rows = []
        for i in range(n):
            dp = f12(deps[i]) if i < len(deps) else '—'; ar = f12(arrs[i]) if i < len(arrs) else '—'
            rd = dur(deps[i], arrs[i]) if i < len(deps) and i < len(arrs) else ''
            t0 = mins(deps[i]) if i < len(deps) else None; t1 = mins(arrs[i]) if i < len(arrs) else None
            def est(si, t0=t0, t1=t1, stops=stops):
                if t0 is None or t1 is None or len(stops) < 2: return ''
                m = t0 + round((t1 - t0) * si / (len(stops) - 1)); h, mi = divmod(m, 60)
                ap = 'AM' if (h % 24) < 12 else 'PM'; h = h % 12 or 12; return f'{h}:{mi:02d} {ap}'
            sh = ''.join(f'<li><span class="dot"></span><span class="sn">{esc(s)}</span><span class="st">{est(si)}</span></li>' for si, s in enumerate(stops))
            rows.append(f'<button class="trip" onclick="pick(this)"><span class="v dep">{esc(dp)}</span>'
                        f'<span class="mid"><span class="ride">{esc(rd) or "—"}</span><span class="chev">▾</span></span>'
                        f'<span class="v arr">{esc(ar)}</span>'
                        f'<span class="dd"><span class="dd-in"><span class="dd-h">{len(stops)} <span class="label-en">stoppages</span><span class="label-bn">স্টপেজ</span></span><ol>{sh}</ol>'
                        f'<span class="dd-note"><span class="label-en">Stop times estimated from the trip departure + route length. Verify before travel.</span><span class="label-bn">স্টপের সময়গুলি আনুমানিক। ভ্রমণের আগে যাচাই করে নিন।</span></span></span></span></button>')
        panels.append(f'<div class="dpanel{" on" if di==0 else ""}" data-dir="{di}">'
                      f'<div class="meta">{len(deps)} <span class="label-en">trips · first</span><span class="label-bn">ট্রিপ · প্রথম</span> {esc(f12(deps[0]) if deps else "—")} <span class="label-en">· last</span><span class="label-bn">· শেষ</span> {esc(f12(deps[-1]) if deps else "—")} · {len(stops)} <span class="label-en">stops</span><span class="label-bn">স্টপ</span></div>'
                      f'<div class="thead"><span><span class="label-en">Departure</span><span class="label-bn">ছাড়ার সময়</span></span><span class="m"><span class="label-en">ride · stops</span><span class="label-bn">সময় · স্টপ</span></span><span class="r"><span class="label-en">Arrival</span><span class="label-bn">পৌঁছানোর সময়</span></span></div>'
                      f'<div class="trips">{"".join(rows)}</div></div>')
    first_all = min((d.get('departures') or ['zz'])[0] for d in dirs if d.get('departures')) if any(d.get('departures') for d in dirs) else '—'
    last_all = max((d.get('departures') or ['00'])[-1] for d in dirs if d.get('departures')) if any(d.get('departures') for d in dirs) else '—'
    stops_html = ''
    if stops0:
        lis = ''.join(f'<li><span class="cstc-stop-dot"></span>{esc(s)}</li>' for s in stops0)
        stops_html = (f'<section class="cstc-stops" style="margin-top:0">'
                      f'<div class="cstc-stops-head"><strong><span class="label-en">Stop list</span><span class="label-bn">স্টপ তালিকা</span></strong><span>{len(stops0)} <span class="label-en">stops</span><span class="label-bn">স্টপ</span></span></div>'
                      f'<ol>{lis}</ol></section>')

    body = (f'<div class="crumb"><a href="../"><span class="label-en">Home</span><span class="label-bn">হোম</span></a> / <a href="../kolkata-city-bus-timetable"><span class="label-en">Kolkata City Bus</span><span class="label-bn">কলকাতা শহরের বাস</span></a> / <span>{esc(route)}</span></div>'
            f'<section class="hero"><span class="eyebrow"><span class="label-en">Official CSTC schedule</span><span class="label-bn">অফিসিয়াল CSTC সময়সূচি</span></span>'
            f'<h1><span class="rcode">{esc(route)}</span>{esc(a0)} <span class="bi">⇄</span> {esc(b0)}</h1>'
            f'<div class="stats"><span class="stat"><b>{total}</b> <span class="label-en">trips/day</span><span class="label-bn">ট্রিপ/দিন</span></span>'
            f'<span class="stat"><span class="label-en">First</span><span class="label-bn">প্রথম</span> <b>{esc(f12(first_all))}</b></span><span class="stat"><span class="label-en">Last</span><span class="label-bn">শেষ</span> <b>{esc(f12(last_all))}</b></span>'
            f'<span class="stat"><b>{len(stops0)}</b> <span class="label-en">stops</span><span class="label-bn">স্টপ</span></span></div></section>'
            f'<div class="dswitch" role="tablist">{"".join(btns)}</div>{"".join(panels)}'
            f'{stops_html}')
    faqs = [(f'What is the first {route} bus?', f'The first {route} bus departs at {f12(first_all)}.'),
            (f'What is the last {route} bus?', f'The last {route} bus departs at {f12(last_all)}.'),
            (f'How many stops does route {route} have?', f'Route {route} has {len(stops0)} stops: {", ".join(stops0[:8])}.'),
            (f'How many {route} trips run per day?', f'About {total} trips per day across both directions.'),
            (f'Is route {route} a CSTC Kolkata city bus?', f'Yes — {route} is an official CSTC city route ({a0} ⇄ {b0}).')]
    about = (f'<p>Route <b>{route}</b> is an official CSTC (Calcutta State Transport Corporation) Kolkata city bus route '
             f'connecting <b>{esc(a0)}</b> and <b>{esc(b0)}</b> in both directions, with {total} scheduled trips per day and {len(stops0)} stoppages.</p>'
             f'<p>Times are from the published West Bengal Transport Department / CSTC schedule. Timings can change — verify before travel. '
             f'Spotted a change? <a href="../contact">Tell us</a>.</p>')
    jsonld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    body += popular_html(others) + faq_html(faqs) + about_html(about)
    return shell(title, desc, canonical, body, jsonld)

# ---------------- private city page (stops only) ----------------
def private_page(o, d, buses, others):
    rn = routenum(buses[0].get('bus_name'))
    stops = collect_stops(buses)
    operators = sorted({(b.get('operator') or '').strip() for b in buses if (b.get('operator') or '').strip()})
    op = ' · '.join(operators[:2]) or 'Kolkata city bus'
    n = len(stops)
    title = f'{o} to {d} Bus Timetable ({rn}) | BusJatri'
    desc = (f'{o} to {d} {rn} Kolkata city bus route — route stops and timetable status. '
            f'{n} stoppages listed. English and Bengali route details on BusJatri.')[:300]
    canonical = f'{BASE}/bus-time-table/{slug(o)}-to-{slug(d)}'
    items = []
    for i, s in enumerate(stops):
        cls_end = ' class="end"' if i in (0, n - 1) else ''
        bn_str = f"<span class='bn'>{esc(bn(s))}</span>" if bn(s) else ""
        items.append(f'<li{cls_end}><span class="dot"></span><span class="sn">{esc(s)}</span>{bn_str}</li>')
    li = ''.join(items)
    body = (f'<div class="crumb"><a href="../"><span class="label-en">Home</span><span class="label-bn">হোম</span></a> / <a href="../kolkata-city-bus-timetable"><span class="label-en">Kolkata City Bus</span><span class="label-bn">কলকাতা শহরের বাস</span></a> / <span>{esc(rn)}</span></div>'
            f'<section class="hero"><span class="eyebrow"><span class="label-en">Kolkata city bus</span><span class="label-bn">কলকাতা শহরের বাস</span></span>'
            f'<h1><span class="rcode">{esc(rn)}</span>{esc(o)} <span class="bi">⇄</span> {esc(d)}</h1>'
            f'<div class="stats"><span class="stat"><b>{n}</b> <span class="label-en">stops</span><span class="label-bn">স্টপ</span></span><span class="stat">{esc(op)}</span>'
            f'<span class="stat"><span class="label-en">Time <b>not listed</b></span><span class="label-bn">সময় <b>তালিকাভুক্ত নয়</b></span></span></div></section>'
            f'<div class="meta">{n} <span class="label-en">route stops ·</span><span class="label-bn">রুট স্টপ ·</span> {esc(o)} ⇄ {esc(d)}</div>'
            f'<ol class="stoplist">{li}</ol>'
            f'<div class="notime-note"><span class="label-en">This route\u2019s departure/arrival times are not published yet. The full stop chain is shown above. '
            f'Know the timing? <a href="../contact">Report it</a> — it will be added here in the same layout.</span>'
            f'<span class="label-bn">এই রুটের সময়সূচি এখনও প্রকাশিত হয়নি। স্টপ তালিকা উপরে দেওয়া হলো। সঠিক সময় জানা থাকলে <a href="../contact">আমাদের জানান</a>।</span></div>')
    faqs = [(f'Which stops does the {rn} bus cover?', f'It runs {o} ⇄ {d} via {n} stops: {", ".join(stops[:8])}.'),
            (f'What are the {o} to {d} bus timings?', 'The published timetable for this route is not listed yet.'),
            (f'Is {rn} a Kolkata city bus?', f'Yes — {rn} is a Kolkata city bus route ({o} ⇄ {d}).'),
            (f'How many stops are on this route?', f'{n} stops are listed on this route.')]
    about = (f'<p><b>{rn}</b> is a Kolkata city bus route between <b>{esc(o)}</b> and <b>{esc(d)}</b>, '
             f'covering {n} stoppages. Stoppages are from the route record; departure and arrival times are added once a reliable timetable is available.</p>')
    jsonld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    body += popular_html(others) + faq_html(faqs) + about_html(about)
    return shell(title, desc, canonical, body, jsonld)

def main():
    os.makedirs(OUT, exist_ok=True)
    # CSTC routes
    cstc = json.load(open(CSTC, encoding='utf-8')) if os.path.exists(CSTC) else {}
    cstc = cstc.get('routes', cstc)
    cstc_list = []
    for route, obj in cstc.items():
        ds = obj.get('directions') or []
        if not ds: continue
        a, b = short_ends(ds[0]['direction'])
        cstc_list.append((route, a, b, f'cstc-{slug(route)}'))
    # write CSTC pages
    n_cstc = 0
    for route, obj in cstc.items():
        ds = obj.get('directions') or []
        if not ds: continue
        others = [(r, f'{a} ⇄ {b}', f'cstc-{slug(r)}') for r, a, b, h in cstc_list if r != route][:8]
        page = cstc_page(route, obj, others)
        open(os.path.join(OUT, f'cstc-{slug(route)}.html'), 'w', encoding='utf-8').write(page)
        n_cstc += 1
    # private city routes
    data = json.load(open(DATA, encoding='utf-8'))
    buses = data['buses'] if isinstance(data, dict) else data
    groups = {}
    for b in buses:
        o, d = (b.get('origin') or '').strip(), (b.get('destination') or '').strip()
        if o and d and is_city(o) and is_city(d):
            groups.setdefault((norm_place(o), norm_place(d)), []).append(b)
    by_rn = {}
    for b in buses:
        rn = routenum(b.get('bus_name'))
        if rn and b.get('stoppages'): by_rn.setdefault(rn, []).append(b)
    # popular private chips (first 8)
    priv_keys = sorted(groups.keys())
    n_priv = 0
    for (o, d), bs in groups.items():
        if not collect_stops(bs):
            bs = bs + by_rn.get(routenum(bs[0].get('bus_name')), [])
        others = [(routenum(groups[k][0].get('bus_name')), f'{k[0]} ⇄ {k[1]}', f'{slug(k[0])}-to-{slug(k[1])}')
                  for k in priv_keys if k != (o, d)][:8]
        page = private_page(o, d, bs, others)
        open(os.path.join(OUT, f'{slug(o)}-to-{slug(d)}.html'), 'w', encoding='utf-8').write(page)
        n_priv += 1
    print(f'CSTC pages: {n_cstc} | private city pages: {n_priv}')

if __name__ == '__main__':
    main()
