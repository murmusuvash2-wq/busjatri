#!/usr/bin/env python3
"""Generate operator/brand pages (SBSTC, NBSTC, WBTC, Shyamoli Paribahan,
Volvo AC buses) under bus-time-table/ — same design language as the place
pages — and register them in sitemap.xml. Idempotent: pages are regenerated,
sitemap edits are guarded. The Operators chip row was REMOVED from the
timetable index on user request (operators stay reachable from the home
page); update_tti() now strips it if present.
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
    return 'sbstc' in src(b) or 'SBSTC' in btype(b) or _op(b) == 'sbstc'


def _op(b):
    return (b.get('operator') or '').strip().lower()

def is_nbstc(b):
    return 'nbstc' in src(b) or _op(b) == 'nbstc'

def is_wbtc(b):
    return 'wbtc' in src(b) or _op(b) == 'wbtc'

def is_shyamoli(b):
    return 'shyamoli' in src(b) or 'shyamoli' in (b.get('bus_name') or '').lower() or _op(b) == 'shyamoli paribahan'

def is_volvo_ac(b):
    t = btype(b)
    return 'AC' in t and 'NON' not in t.upper()

OPS_INFO = {'sbstc-buses': ('government (South Bengal State Transport Corporation)', 'সরকারি — দক্ষিণবঙ্গ রাজ্য পরিবহণ সংস্থা'), 'nbstc-buses': ('government (North Bengal State Transport Corporation)', 'সরকারি — উত্তরবঙ্গ রাজ্য পরিবহণ সংস্থা'), 'wbtc-buses': ('government (West Bengal Transport Corporation)', 'সরকারি — পশ্চিমবঙ্গ পরিবহণ নিগম'), 'shyamoli-paribahan-buses': ('a private operator', 'একটি বেসরকারি পরিবহন সংস্থা'), 'volvo-ac-buses': ('AC coach services — both government and private operators run Volvo AC buses', 'এসি কোচ পরিষেবা — সরকারি ও বেসরকারি দুই ধরনের অপারেটরই ভলভো এসি বাস চালায়')}
OFFICIAL = {'sbstc-buses': ('https://sbstconline.co.in/reservation-home', 'Book tickets on SBSTC official site', 'এসবিএসটিসি অফিসিয়াল সাইটে টিকিট বুক করুন', 'sbstconline.co.in'), 'nbstc-buses': ('https://nbstc.in/online-booking.php', 'Book tickets on NBSTC official site', 'এনবিএসটিসি অফিসিয়াল সাইটে টিকিট বুক করুন', 'nbstc.in'), 'wbtc-buses': ('https://www.wbtconline.in/', 'Book tickets on WBTC official site', 'ডব্লিউবিটিসি অফিসিয়াল সাইটে টিকিট বুক করুন', 'wbtconline.in'), 'shyamoli-paribahan-buses': ('https://www.shyamolibus.com/', 'Book tickets on Shyamoli official site', 'শ্যামলী অফিসিয়াল সাইটে টিকিট বুক করুন', 'shyamolibus.com'), 'volvo-ac-buses': ('https://www.redbus.in/', 'Check AC bus fares on redBus', 'রেডবাসে এসি বাসের ভাড়া দেখুন', None)}
BN_SHORT = {'sbstc-buses': 'এসবিএসটিসি', 'nbstc-buses': 'এনবিএসটিসি', 'wbtc-buses': 'ডব্লিউবিটিসি', 'shyamoli-paribahan-buses': 'শ্যামলী', 'volvo-ac-buses': 'এসি ভলভো'}


OPERATORS = [
    dict(stem='sbstc-buses', name='SBSTC', title='SBSTC Bus Time Table (সময়সূচি) — Routes & Timings',
         h1='SBSTC Buses', bn='দক্ষিণবঙ্গ রাজ্য পরিবহণ সংস্থার বাস',
         desc='SBSTC bus time table: routes, departure times & destinations across West Bengal. এসবিএসটিসি বাসের সময়সূচি, রুট ও ছাড়ার সময় — কলকাতা, দীঘা, দুর্গাপুর সহ সব রুট।',
         ogt='SBSTC বাসের সময়সূচি — Bus Time Table | BusJatri',
         ogd='এসবিএসটিসি (SBSTC) বাসের সময়সূচি — রুট, ছাড়ার সময় ও গন্তব্য। কলকাতা–দীঘা, দুর্গাপুর, বর্ধমান সহ সব রুট BusJatri-তে।',
         intro='Explore listed SBSTC (South Bengal State Transport Corporation) bus services with routes, departure times and destinations.',
         pred=is_sbstc, tag='Government'),
    dict(stem='nbstc-buses', name='NBSTC', title='NBSTC Bus Time Table (সময়সূচি) — Routes & Timings',
         h1='NBSTC Buses', bn='উত্তরবঙ্গ রাজ্য পরিবহণ সংস্থার বাস',
         desc='NBSTC bus time table: routes, departure times & destinations across North Bengal. এনবিএসটিসি বাসের সময়সূচি, রুট ও ছাড়ার সময় — শিলিগড়ি, কোচবিহার, মালদা সহ সব রুট।',
         ogt='NBSTC বাসের সময়সূচি — Bus Time Table | BusJatri',
         ogd='এনবিএসটিসি (NBSTC) বাসের সময়সূচি — রুট, ছাড়ার সময় ও গন্তব্য। শিলিগড়ি, কোচবিহার, মালদা সহ সব রুট BusJatri-তে।',
         intro='Explore listed NBSTC (North Bengal State Transport Corporation) bus services with routes, departure times and destinations.',
         pred=is_nbstc, tag='Government'),
    dict(stem='wbtc-buses', name='WBTC', title='WBTC Bus Time Table (সময়সূচি) — Routes & Timings',
         h1='WBTC Buses', bn='পশ্চিমবঙ্গ পরিবহণ নিগমের বাস',
         desc='WBTC (CSTC) bus time table: routes, departure times & destinations across Kolkata and West Bengal. ডব্লিউবিটিসি বাসের সময়সূচি ও রুট — কলকাতা সহ সব রুট।',
         ogt='WBTC বাসের সময়সূচি — Bus Time Table | BusJatri',
         ogd='ডব্লিউবিটিসি (WBTC) বাসের সময়সূচি — রুট, ছাড়ার সময় ও গন্তব্য। কলকাতা ও পশ্চিমবঙ্গের সব রুট BusJatri-তে।',
         intro='Explore listed WBTC / CSTC (Calcutta State Transport Corporation) bus services with routes, departure times and destinations.',
         pred=is_wbtc, tag='Government'),
    dict(stem='shyamoli-paribahan-buses', name='Shyamoli Paribahan', title='Shyamoli Paribahan Bus Time Table (সময়সূচি)',
         h1='Shyamoli Paribahan Buses', bn='শ্যামলী পরিবহনের বাস',
         desc='Shyamoli Paribahan AC Volvo bus time table: routes, departure times & destinations. শ্যামলী পরিবহনের এসি ভল্ভো বাসের সময়সূচি ও রুট — কলকাতা সহ সব রুট।',
         ogt='শ্যামলী পরিবহনের বাসের সময়সূচি | BusJatri',
         ogd='শ্যামলী পরিবহনের এসি ভল্ভো বাসের সময়সূচি — রুট, ছাড়ার সময় ও গন্তব্য। সব রুট BusJatri-তে।',
         intro='Explore listed Shyamoli Paribahan AC Volvo bus services with routes, departure times and destinations.',
         pred=is_shyamoli, tag='Private'),
    dict(stem='volvo-ac-buses', name='Volvo AC', title='Volvo AC Bus Time Table (সময়সূচি) — Routes & Timings',
         h1='Volvo AC Buses', bn='এসি ভলভো বাস',
         desc='Volvo AC bus time table: routes, departure times & destinations across West Bengal. এসি ভল্ভো বাসের সময়সূচি — রুট ও ছাড়ার সময় এক জায়গায়।',
         ogt='ভল্ভো এসি বাসের সময়সূচি — Bus Time Table | BusJatri',
         ogd='এসি ভল্ভো বাসের সময়সূচি — রুট, ছাড়ার সময় ও গন্তব্য। পশ্চিমবঙ্গের সব রুট BusJatri-তে।',
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
<meta property="og:title" content="{ogt}">
<meta property="og:description" content="{ogd}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}/bus-time-table/{stem}.html">
<meta property="og:image" content="{BASE}/og-image.png">
<meta property="og:locale" content="en_IN">
<meta property="og:locale:alternate" content="bn_IN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{ogt}">
<meta name="twitter:description" content="{ogd}">
<meta name="twitter:image" content="{BASE}/og-image.png">
<meta name="theme-color" content="#b8791f">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="stylesheet" href="../css/seo.css?v=opt20260920">
<link rel="stylesheet" href="../css/extras.css">
<script type="application/ld+json">{{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{{"@type": "ListItem", "position": 1, "name": "Home", "item": "{BASE}/"}}, {{"@type": "ListItem", "position": 2, "name": "Bus Timetable", "item": "{BASE}/bus-time-table/"}}, {{"@type": "ListItem", "position": 3, "name": "{h1}", "item": "{BASE}/bus-time-table/{stem}.html"}}]}}</script>
{faq_schema}
</head>
<body>
<header class="header">
  <div class="container header-inner">
    <a href="../index.html" class="logo" style="text-decoration:none;color:inherit">
      <img class="brand-logo" src="/logo.png" alt="BusJatri" style="width:30px;height:30px;border-radius:50%">


      Bus<span>Jatri</span>
    </a>
    <nav style="display:flex;gap:10px;align-items:center;font-size:13px">
      <a href="../index.html" style="color:var(--ink-dim);text-decoration:none;font-weight:600"><span class="label-en">Home</span><span class="label-bn">হোম</span></a>
      <a href="./" style="color:var(--ink-dim);text-decoration:none;font-weight:600"><span class="label-en">Routes</span><span class="label-bn">রুট</span></a>
      <span class="lang-group" style="display:flex;gap:4px;margin-left:4px">
        <button class="lang-btn" id="langEN" onclick="setLang('en')" style="background:var(--amber-soft,#f6e7c6);border:1px solid var(--line,#ccc);border-radius:999px;padding:4px 10px;cursor:pointer;font-weight:700;font-size:12px;font-family:inherit">EN</button>
        <button class="lang-btn" id="langBN" onclick="setLang('bn')" style="background:transparent;border:1px solid var(--line,#ccc);border-radius:999px;padding:4px 10px;cursor:pointer;font-weight:700;font-size:12px;font-family:inherit">বাংলা</button>
      </span>
    </nav>
  </div>
</header>
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:860px">
<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">Bus Timetable</a> › <span>{h1}</span></div>
<div class="op-hero">
<h1 style="font-size:clamp(1.8rem,5vw,2.5rem);line-height:1.2;margin:0">{h1}</h1>
<div class="bn-line only-bn" style="color:var(--ink-dim);margin-top:6px">{bn}</div>
</div>
'''

ROW_T = '''<a href="{href}" class="op-card">
  <span class="rt">{fr} <span class="arr">→</span> {to}</span>
  <span class="meta">🚌 {n} buses</span>
  <span class="go">View Schedule ›</span>
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
<script>(function(){function setLang(l){document.body.classList.toggle('lang-bn',l==='bn');var a=document.getElementById('langEN'),b=document.getElementById('langBN');if(a)a.style.background=l==='en'?'var(--amber-soft,#f6e7c6)':'transparent';if(b)b.style.background=l==='bn'?'var(--amber-soft,#f6e7c6)':'transparent';try{localStorage.setItem('seo-lang',l);}catch(e){}}window.setLang=setLang;var sv=null;try{sv=localStorage.getItem('seo-lang');}catch(e){}setLang(sv||'en');})();</script>
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


    popular = f'''<h2 class="op-h2">Popular {esc(op['name'])} Routes</h2>
<div class="op-grid">
{''.join(rows)}
</div>'''

    chiprow = f'''<h2 class="op-h2" style="margin-top:26px">All Destinations</h2>
<div class="chip-row" aria-label="All destinations">{''.join(chips)}</div>'''

    op_info = OPS_INFO.get(op["stem"], ("bus services", "বাস পরিষেবা"))
    op_token = op['stem'].replace('-buses', '')
    clean_name = op['name'].replace(' Buses', '')
    cta_btn = ('<a class="op-cta" href="../index.html#/search?op=' + op_token + '">' +
               '<span class="label-en">Open all ' + esc(op['name']) + ' buses in search</span>' +
               '<span class="label-bn">সার্চে সব বাস দেখুন</span></a>')
    cta_main = ('<a class="op-cta-big" href="../index.html#/search?op=' + op_token + '">' +
                '<span class="label-en">🚌 View all ' + esc(clean_name) + ' buses — live</span>' +
                '<span class="label-bn">🚌 লাইভ সব বাস দেখুন</span></a>')
    FAQ_CSS = ('<style>'
               '.op-faq{border:1.5px solid var(--line,rgba(33,28,22,.15));border-radius:13px;'
               'background:var(--surface,#fffcf4);margin-bottom:9px;overflow:hidden}'
               '.op-faq[open]{border-color:var(--amber,#b8791f)}'
               '.op-faq summary{list-style:none;cursor:pointer;padding:13px 16px;font-weight:600;'
               'font-size:14.5px;line-height:1.45;display:flex;gap:10px;align-items:baseline}'
               '.op-faq summary::-webkit-details-marker{display:none}'
               '.op-faq summary::before{content:"+";color:var(--amber,#b8791f);font-weight:800;'
               'font-size:16px;flex:none}'
               '.op-faq[open] summary::before{content:"–"}'
               '.op-faq .fa-body{padding:0 16px 14px 36px;font-size:13.5px;line-height:1.7;color:var(--ink-dim,#665)}'
               '.op-cta{display:inline-flex;gap:8px;align-items:center;background:var(--amber,#b8791f);'
               'color:#fffcf4;text-decoration:none;font-weight:800;border-radius:999px;padding:10px 18px;'
               'font-size:13.5px;margin-top:10px}'
               '.op-cta-big{display:flex;gap:9px;align-items:center;justify-content:center;'
               'background:var(--amber,#b8791f);color:#fffcf4;text-decoration:none;font-weight:800;'
               'border-radius:13px;padding:14px 18px;font-size:15px;margin:16px 0 4px;'
               'box-shadow:0 2px 10px rgba(184,121,31,.35)}'
               '</style>')
    top_fr, top_to, top_n = "", "", 0
    if top:
        (top_fr, top_to), top_n = top[0]
    dest_names = [d for d, _ in dests.most_common(8) if d]
    nb = op["bn"]
    # --- compact stats + search card + depo board (2026-09-25) ---
    stats = ("<section class='op-stats' style='background:var(--surface,#fffcf4);border:1.5px solid var(--line,rgba(33,28,22,.15));" +
             "border-radius:13px;padding:14px 18px;display:flex;gap:18px;align-items:center;justify-content:center;flex-wrap:wrap'>" +
             "<span style='font-size:14px;font-weight:700'>🚌 " + str(len(buses)) + " <span class='label-en'>buses listed</span><span class='label-bn'>টি বাস তালিকাভুক্ত</span></span>" +
             "<span style='color:var(--line,rgba(33,28,22,.15));font-weight:800'>|</span>" +
             "<span style='font-size:14px;font-weight:700'>🛣 " + str(len(routes)) + " <span class='label-en'>routes covered</span><span class='label-bn'>টি রুট</span></span>" +
             "</section>")
    off = OFFICIAL.get(op['stem'])
    bn_short = BN_SHORT.get(op['stem'], op['name'])
    ph_fr = esc(top_fr) if top_fr else 'Burdwan'
    ph_to = esc(top_to) if top_to else 'Kolkata'
    off_link = ''
    search_card = (
        "<section class='bj-op-search'>" +
        "<div class='lb'><span class='label-en'>Search " + esc(op['name']) + " buses</span><span class='label-bn'>" + bn_short + " বাস খুঁজুন</span></div>" +
        "<div class='row'>" +
        "<input id='bjFrom' type='text' placeholder='e.g. " + ph_fr + "' autocomplete='off'>" +
        "<button class='swap' onclick='bjSwap()' title='Swap' type='button'>⇆</button>" +
        "<input id='bjTo' type='text' placeholder='e.g. " + ph_to + "' autocomplete='off'>" +
        "</div>" +
        "<div class='row' style='margin-top:8px'>" +
        "<input id='bjDate' type='date' style='flex:1.2'>" +
        "<button class='go' style='margin-top:0;width:auto;flex:1.4' onclick='bjSearchGo()' type='button'>🚊 <span class='label-en'>Search</span><span class='label-bn'>সার্চ করুন</span></button>" +
        "</div>" +
        off_link +
        "</section>" +
        "<style>" +
        ".bj-op-search{background:var(--surface,#fffcf4);border:1.5px solid var(--line,rgba(33,28,22,.15));border-radius:14px;padding:16px;margin:20px 0 14px;box-shadow:0 2px 12px rgba(33,28,22,.06)}" +
        ".bj-op-search .lb{font-size:11px;letter-spacing:.12em;font-weight:700;color:var(--amber-ink,#6b4610);text-transform:uppercase;margin-bottom:10px}" +
        ".bj-op-search .row{display:flex;gap:8px;align-items:stretch}" +
        ".bj-op-search input{flex:1;min-width:0;padding:12px;border-radius:10px;border:1.5px solid var(--line,#ccc);background:var(--bg,#fff);font:inherit;font-size:15px}" +
        ".bj-op-search input:focus{outline:none;border-color:var(--amber,#b8791f)}" +
        ".bj-op-search .swap{flex:none;width:40px;border-radius:10px;border:1.5px solid var(--line,#ccc);background:var(--surface,#fffcf4);font-size:16px;cursor:pointer;color:var(--amber,#b8791f)}" +
        ".bj-op-search .go{display:block;width:100%;margin-top:10px;background:var(--amber,#b8791f);color:#fffcf4;border:none;border-radius:11px;padding:13px;font:inherit;font-size:15px;font-weight:800;cursor:pointer}" +
        ".bj-op-search .alt{text-align:center;font-size:12.5px;color:var(--ink-dim,#665);margin-top:10px}" +
        ".bj-op-search .alt a{color:var(--amber,#b8791f);font-weight:700;text-decoration:none}" +
        "</style>")
    lv_rows = []
    for b in buses:
        lv_rows.append([b.get('id', '') or '', b.get('bus_name', '') or '', b.get('origin', '') or '', b.get('destination', '') or '', b.get('departure_time', '') or ''])
    board = ("<section id='bjLive' style='margin-top:16px'></section>" +
        "<script>window.bjOpCfg = " + json.dumps({'name': op['name'], 'bn': bn_short, 'token': op_token, 'count': len(buses)}, ensure_ascii=False) + "; window.bjOpData = " + json.dumps(lv_rows, ensure_ascii=False) + ";</script>" +
        "<script src='../js/op-board.js?v=opse20260926' defer></script>")
    booking_q = 'How do I book a ' + clean_name + ' bus ticket online?'
    booking_q_bn = bn_short + ' বাসের টিকিট অনলাইনে কীভাবে বুক করব?'
    if off and off[3]:
        booking_a = ("Book on the official " + clean_name + " site <a href='" + off[0] + "' target='_blank' rel='noopener'>" + off[3] + "</a>, or compare fares and seats on <a href='https://www.redbus.in/' target='_blank' rel='nofollow noopener'>redBus</a>.")
        booking_a_bn = ("অফিসিয়াল সাইট <a href='" + off[0] + "' target='_blank' rel='noopener'>" + off[3] + "</a>-তে বুক করুন, অথবা <a href='https://www.redbus.in/' target='_blank' rel='nofollow noopener'>রেডবাস</a>-এ ভাড়া ও সিট দেখুন।")
    else:
        booking_a = "Compare fares and book AC bus tickets on <a href='https://www.redbus.in/' target='_blank' rel='nofollow noopener'>redBus</a>."
        booking_a_bn = "ভাড়া দেখে <a href='https://www.redbus.in/' target='_blank' rel='nofollow noopener'>রেডবাস</a>-এ এসি বাসের টিকিট বুক করুন।"

    faq_en = [
        ("How many " + op["name"] + " bus services are listed?",
         str(len(buses)) + " " + op["name"] + " services are listed on BusJatri, covering " + str(len(routes)) + " routes."),
        ("Which is the busiest " + op["name"] + " route?",
         (esc(top_fr) + " to " + esc(top_to) + ", with " + str(top_n) + " listed buses." if top_n else "Open the route list below for currently listed services.")),
        ("Where do " + op["name"] + " buses go?",
         ("Popular destinations include " + ", ".join(esc(d) for d in dest_names) + "." if dest_names else "See the destinations listed below.")),
        ("Are " + op["name"] + " buses government or private?",
         op["name"] + " buses are " + op_info[0] + "."),
        ("How do I check departure times for a " + op["name"] + " bus?",
         "Open any route page from the lists above for the full timetable. Times can change — confirm at the bus stand counter before travel."),
        ("How do I see all " + op["name"].replace(" Buses", "") + " buses in one place?",
         "Tap the button below — BusJatri search opens with every listed " + op["name"] + " service, sorted by next departure." + cta_btn),
        (booking_q, booking_a),
    ]
    faq_bn = [
        (op["name"] + " বাস কতটি তালিকাভুক্ত?",
         "BusJatri-তে " + str(len(buses)) + "টি " + op["name"] + " বাস তালিকাভুক্ত, " + str(len(routes)) + "টি রুট জুড়ে।"),
        (op["name"] + "-এর সবচেয়ে ব্যস্ত রুট কোনটি?",
         (esc(top_fr) + " থেকে " + esc(top_to) + " — " + str(top_n) + "টি বাস।" if top_n else "নিচের রুট তালিকা দেখুন।")),
        (op["name"] + " বাস কোথায় যায়?",
         ("জনপ্রিয় গন্তব্য: " + ", ".join(esc(d) for d in dest_names) + "।" if dest_names else "নিচের গন্তব্যের তালিকা দেখুন।")),
        (op["name"] + " কি সরকারি না বেসরকারি?",
         nb + " — " + op_info[1] + "।"),
        (op["name"] + " বাসের সময় কোথায় দেখব?",
         "উপরের যেকোনো রুট পেজ খুললে সম্পূর্ণ সময়সূচি পাবেন। সময় বদলাতে পারে — যাত্রার আগে কাউন্টারে নিশ্চিত করে নিন।"),
        (op["name"].replace(" Buses", "") + " বাসগুলো একসঙ্গে দেখব কীভাবে?",
         "নিচের বাটনে ট্যাপ করুন — BusJatri সার্চ খুলবে, তালিকাভুক্ত সব " + op["name"] + " বাস পরবর্তী ছাড়ার সময় অনুযায়ী সাজানো থাকবে।" + cta_btn),
        (booking_q_bn, booking_a_bn),
    ]
    faq_items = "".join(
        ('<details class="op-faq' + (' open' if i == 0 else '') + '"><summary>' + q + '</summary><div class="fa-body">' + a + '</div></details>')
        for i, (q, a) in enumerate(faq_en))
    faq_items += "".join(
        ('<details class="op-faq only-bn' + (' open' if i == 0 else '') + '"><summary>' + q + '</summary><div class="fa-body">' + a + '</div></details>')
        for i, (q, a) in enumerate(faq_bn))
    faq_section = ('<h2 class="op-h2" style="margin-top:26px"><span class="label-en">FAQs</span>'
                   '<span class="label-bn">সাধারণ প্রশ্ন</span></h2>' + FAQ_CSS + faq_items)
    import json as _j
    faq_schema = ('<script type="application/ld+json">' + _j.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q,
                         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq_en + faq_bn]},
        ensure_ascii=False) + "</script>")

    body = HEAD.format(title=esc(op['title']), desc=esc(op['desc']), stem=op['stem'], ogt=esc(op['ogt']), ogd=esc(op['ogd']),
                       BASE=BASE, h1=esc(op['h1']), bn=op['bn'], intro=esc(op['intro']), faq_schema=faq_schema)
    body += stats + search_card + board + popular + chiprow + faq_section + chr(10) + '</main>' + chr(10) + FOOT
    return apply_sbstc_toggle(body, op)



SBSTC_STOPS = {'Kolkata': 'কলকাতা', 'Digha': 'দীঘা', 'Burdwan': 'বর্ধমান', 'Bardhaman': 'বর্ধমান', 'Karunamoyee': 'করুণাময়ী', 'Durgapur': 'দুর্গাপুর', 'Haldia': 'হলদিয়া', 'Asansol': 'আসানসোল', 'Midnapur': 'মেদিনীপুর', 'Midnapore': 'মেদিনীপুর', 'Medinipur': 'মেদিনীপুর', 'Bankura': 'বাঁকুড়া', 'Purulia': 'পুরুলিয়া', 'Garia': 'গড়িয়া', 'Arambag': 'আরামবাগ', 'Arambagh': 'আরামবাগ', 'Suri': 'সিউড়ি', 'Habra': 'হাবড়া', 'Barasat': 'বারাসাত', 'Dhamakhali': 'ধামাখালি', 'Jhargram': 'ঝাড়গ্রাম', 'Kandra': 'কান্দ্রা', 'Nagar': 'নগর', 'Nandigram': 'নন্দীগ্রাম', 'Garhbhowanipur': 'গড়ভবানীপুর', 'Gopiganj': 'গোপীগঞ্জ', 'Belghoria': 'বেলঘরিয়া', 'Falta': 'ফলতা', 'Thakurpukur': 'ঠাকুরপুকুর', 'Haldia Via-Kolkata': 'হলদিয়া (কলকাতা হয়ে)', 'Indus Via-Kolkata': 'ইন্দাস (কলকাতা হয়ে)', 'Durgapur (City Center)': 'দুর্গাপুর (সিটি সেন্টার)', 'Durgapur City Centre': 'দুর্গাপুর সিটি সেন্টার', 'Durgapur (Station)': 'দুর্গাপুর (স্টেশন)', 'Manbazar': 'মানবাজার', 'Nabadwip': 'নবদ্বীপ', 'Kalna': 'কালনা', 'Lalgola': 'লালগোলা', 'Diamond Harbour': 'ডায়মন্ড হারবার', 'Bishnupur': 'বিষ্ণুপুর', 'Khatra': 'খাতড়া', 'Jamuria': 'জামুরিয়া', 'Sonachura': 'সোনাচুড়া', 'Belpahari': 'বেলপাহাড়ি', 'Baruipur': 'বারুইপুর', 'Dumdum': 'ডামডাম', 'Goyespur': 'গয়েশপুর', 'Kakdwip': 'কাকদ্বীপ', 'Salar': 'সালার', 'Kirnahar': 'কির্নাহার', 'Naihati': 'নৈহাটি', 'Namkhana': 'নামখানা', 'Mohar': 'মোহর', 'Haldia Township': 'হলদিয়া টাউনশিপ', 'Malda': 'মালদা', 'Kolkata (Esplanade)': 'কলকাতা (এসপ্ল্যানেড)', 'Egra': 'এগরা', 'Balrampur': 'বলরামপুর', 'Chittaranjan': 'চিত্তরঞ্জন', 'Tarapith': 'তারাপীঠ', 'Kuli': 'কুলি', 'Barakar': 'বরাকর', 'Ramganj': 'রামগঞ্জ', 'Kabilepur': 'কবিলেপুর', 'Siliguri': 'শিলিগুড়ি', 'Gopiballabpur': 'গোপীবল্লভপুর', 'Bolpur': 'বোলপুর', 'Kharagpur': 'খড়্গপুর', 'Baghmundi': 'বাঘমুণ্ডি', 'Ajodhya Hills': 'অযোধ্যা পাহাড়', 'Bandwan': 'বান্দোয়ান', 'Kolkata A.C': 'কলকাতা এসি', 'Garia A.C': 'গড়িয়া এসি', 'Barasat A.C': 'বারাসাত এসি', 'Asansol A.C.': 'আসানসোল এসি', 'Baruipur A.C': 'বারুইপুর এসি', 'Diamond': 'ডায়মন্ড হারবার'}
SBSTC_STOPS_JSON = '{"Kolkata": "কলকাতা", "Digha": "দীঘা", "Burdwan": "বর্ধমান", "Bardhaman": "বর্ধমান", "Karunamoyee": "করুণাময়ী", "Durgapur": "দুর্গাপুর", "Haldia": "হলদিয়া", "Asansol": "আসানসোল", "Midnapur": "মেদিনীপুর", "Midnapore": "মেদিনীপুর", "Medinipur": "মেদিনীপুর", "Bankura": "বাঁকুড়া", "Purulia": "পুরুলিয়া", "Garia": "গড়িয়া", "Arambag": "আরামবাগ", "Arambagh": "আরামবাগ", "Suri": "সিউড়ি", "Habra": "হাবড়া", "Barasat": "বারাসাত", "Dhamakhali": "ধামাখালি", "Jhargram": "ঝাড়গ্রাম", "Kandra": "কান্দ্রা", "Nagar": "নগর", "Nandigram": "নন্দীগ্রাম", "Garhbhowanipur": "গড়ভবানীপুর", "Gopiganj": "গোপীগঞ্জ", "Belghoria": "বেলঘরিয়া", "Falta": "ফলতা", "Thakurpukur": "ঠাকুরপুকুর", "Haldia Via-Kolkata": "হলদিয়া (কলকাতা হয়ে)", "Indus Via-Kolkata": "ইন্দাস (কলকাতা হয়ে)", "Durgapur (City Center)": "দুর্গাপুর (সিটি সেন্টার)", "Durgapur City Centre": "দুর্গাপুর সিটি সেন্টার", "Durgapur (Station)": "দুর্গাপুর (স্টেশন)", "Manbazar": "মানবাজার", "Nabadwip": "নবদ্বীপ", "Kalna": "কালনা", "Lalgola": "লালগোলা", "Diamond Harbour": "ডায়মন্ড হারবার", "Bishnupur": "বিষ্ণুপুর", "Khatra": "খাতড়া", "Jamuria": "জামুরিয়া", "Sonachura": "সোনাচুড়া", "Belpahari": "বেলপাহাড়ি", "Baruipur": "বারুইপুর", "Dumdum": "ডামডাম", "Goyespur": "গয়েশপুর", "Kakdwip": "কাকদ্বীপ", "Salar": "সালার", "Kirnahar": "কির্নাহার", "Naihati": "নৈহাটি", "Namkhana": "নামখানা", "Mohar": "মোহর", "Haldia Township": "হলদিয়া টাউনশিপ", "Malda": "মালদা", "Kolkata (Esplanade)": "কলকাতা (এসপ্ল্যানেড)", "Egra": "এগরা", "Balrampur": "বলরামপুর", "Chittaranjan": "চিত্তরঞ্জন", "Tarapith": "তারাপীঠ", "Kuli": "কুলি", "Barakar": "বরাকর", "Ramganj": "রামগঞ্জ", "Kabilepur": "কবিলেপুর", "Siliguri": "শিলিগুড়ি", "Gopiballabpur": "গোপীবল্লভপুর", "Bolpur": "বোলপুর", "Kharagpur": "খড়্গপুর", "Baghmundi": "বাঘমুণ্ডি", "Ajodhya Hills": "অযোধ্যা পাহাড়", "Bandwan": "বান্দোয়ান", "Kolkata A.C": "কলকাতা এসি", "Garia A.C": "গড়িয়া এসি", "Barasat A.C": "বারাসাত এসি", "Asansol A.C.": "আসানসোল এসি", "Baruipur A.C": "বারুইপুর এসি", "Diamond": "ডায়মন্ড হারবার"}'


def sbstc_bn_name(s):
    """Longest-match English -> Bengali stop-name mapping."""
    r = str(s)
    for k in sorted(SBSTC_STOPS, key=len, reverse=True):
        if k in r:
            r = r.replace(k, SBSTC_STOPS[k])
    return r


def _sbstc_bn_walk(html):
    """Apply stop-name mapping to text nodes only (leave tags/attrs alone)."""
    out = []
    for part in re.split(r'(<[^>]+>)', html):
        out.append(part if part.startswith('<') else sbstc_bn_name(part))
    return ''.join(out)


SBSTC_TOGGLE_CSS = ('<style id="bjLangToggle">.label-bn{display:none!important}'
                    'body.lang-bn .label-en{display:none!important}'
                    'body.lang-bn .label-bn{display:inline!important}'
                    '.only-bn{display:none!important}'
                    'body.lang-bn .only-bn{display:block!important}'
                    'body.lang-bn .only-en{display:none!important}'
                    '.lang-btn.on{background:var(--amber-soft,#f6e7c6)!important}'
                    '.hero-badge{display:inline-flex;align-items:center;background:linear-gradient(135deg,#c98a2b,#a13b2e);'
                    'color:#fffcf4;font-weight:800;letter-spacing:.08em;border-radius:14px;'
                    'padding:6px 18px;font-size:.72em;box-shadow:0 3px 14px rgba(184,121,31,.4);text-transform:uppercase}'
                    '.schip{border:1.5px solid var(--line,rgba(33,28,22,.15));background:var(--surface,#fffcf4);'
                    'border-radius:999px;padding:6px 13px;font:inherit;font-size:12.5px;font-weight:600;'
                    'cursor:pointer;margin:2px}'
                    '.schip.on{background:var(--amber,#b8791f);color:#fffcf4;border-color:var(--amber,#b8791f)}'
                    '.bj-chip-row{display:flex;flex-wrap:wrap;gap:2px;margin-top:8px}'
                    '.bj-dt-row{display:flex;gap:10px;margin-top:10px}'
                    '.bj-dt{flex:1;min-width:0}'
                    '.bj-dt label{display:block;font-size:11px;letter-spacing:.12em;font-weight:700;color:var(--amber-ink,#6b4610);text-transform:uppercase;margin-bottom:6px}'
                    '.bj-dt input,.bj-dt select{width:100%;padding:12px;border-radius:10px;border:1.5px solid var(--line,#ccc);background:var(--bg,#fff);font:inherit;font-size:15px;color:var(--ink,#211c16)}'
                    '.bj-dt input:focus,.bj-dt select:focus{outline:none;border-color:var(--amber,#b8791f)}'
                    '.op-res-card{background:var(--surface,#fffcf4);border:1.5px solid var(--line,rgba(33,28,22,.15));'
                    'border-radius:14px;padding:14px 16px;margin:14px 0}'
                    '.op-res-h{font-size:13px;font-weight:800;color:var(--amber-ink,#6b4610);margin-bottom:8px}'
                    '.op-res-row{display:flex;gap:10px;align-items:baseline;padding:8px 4px;border-top:1px dashed var(--line,rgba(33,28,22,.12));cursor:pointer}'
                    '.op-res-row:hover{background:var(--amber-soft,rgba(184,121,31,.12))}'
                    '.op-res-row .t{font-family:var(--font-mono,monospace);font-weight:700;font-size:13px;color:var(--amber,#b8791f);flex:none}'
                    '.op-res-row .nm{font-weight:600;font-size:13.5px}'
                    '.op-res-row .dst{color:var(--ink-dim,#665);font-size:12.5px}'
                    '.op-res-alt{margin-top:9px;font-size:13px}'
                    '</style>')


def apply_sbstc_toggle(body, op):
    """SBSTC only: full EN/BN toggle + v2 search/dark/names features."""
    if op['stem'] != 'sbstc-buses':
        return body
    b = body

    # ---- toggle CSS + color-scheme ----
    b = b.replace('<link rel="stylesheet" href="../css/extras.css">',
                  '<link rel="stylesheet" href="../css/extras.css">' + SBSTC_TOGGLE_CSS, 1)
    assert 'bjLangToggle' in b

    # ---- site-standard controls: theme button + seo-page.js ----
    b = b.replace('<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                  '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                  '<meta name="color-scheme" content="light dark">', 1)
    moon = ('<button id="themeBtn" class="lang-btn" aria-label="Theme" style="background:transparent;'
            'border:1px solid var(--line,#ccc);border-radius:999px;padding:4px 10px;cursor:pointer;'
            'font-weight:700;font-size:12px;font-family:inherit;display:inline-flex;align-items:center">'
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true" style="width:14px;height:14px">'
            '<path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z"/></svg></button>')
    b = b.replace('<span class="lang-group"', moon + '\n        <span class="lang-group"', 1)
    b = b.replace("id=\"langEN\" onclick=\"setLang('en')\"", 'id="langEn"', 1)
    b = b.replace("id=\"langBN\" onclick=\"setLang('bn')\"", 'id="langBn"', 1)
    # swap the inline setLang IIFE for the site-standard controls script
    b = re.sub(r'<script>\(function\(\)\{function setLang[\s\S]*?\}\)\(\);</script>',
               '<script src="../js/seo-page.js?v=spg20260926" defer></script>', b, count=1)
    assert 'seo-page.js' in b and 'function setLang' not in b

    # ---- hero: badge + bilingual ----
    old_h1 = '<h1 style="font-size:clamp(1.8rem,5vw,2.5rem);line-height:1.2;margin:0">SBSTC Buses</h1>'
    new_h1 = ('<h1 style="font-size:clamp(1.8rem,5vw,2.5rem);line-height:1.2;margin:0;'
              'display:flex;align-items:center;gap:12px;flex-wrap:wrap">'
              '<span class="hero-badge">SBSTC</span>'
              '<span class="label-en">Buses</span><span class="label-bn">\u09ac\u09be\u09b8</span></h1>'
              '<div class="only-en" style="color:var(--ink-dim);margin-top:8px;font-size:14.5px">'
              'South Bengal State Transport Corporation \u2014 routes, time tables & schedules</div>')
    assert old_h1 in b, 'h1 not found'
    b = b.replace(old_h1, new_h1, 1)
    # Bengali subtitle: map is not needed (already Bengali); wrap for safety
    b = b.replace('<div class="bn-line only-bn" style="color:var(--ink-dim);margin-top:6px">',
                  '<div class="bn-line only-bn" style="color:var(--ink-dim);margin-top:8px;font-size:14.5px">', 1)

    # ---- crumbs ----
    b = b.replace('<a href="./">Bus Timetable</a>',
                  '<a href="./"><span class="label-en">Bus Timetable</span>'
                  '<span class="label-bn">\u09ac\u09be\u09b8 \u09b8\u09ae\u09df\u09b8\u09c2\u099a\u09bf</span></a>', 1)
    b = b.replace('<span>SBSTC Buses</span>',
                  '<span><span class="label-en">SBSTC Buses</span>'
                  '<span class="label-bn">SBSTC \u09ac\u09be\u09b8</span></span>', 1)

    # ---- section headings ----
    b = b.replace('<h2 class="op-h2">Popular SBSTC Routes</h2>',
                  '<h2 class="op-h2"><span class="label-en">Popular SBSTC Routes</span>'
                  '<span class="label-bn">\u099c\u09a8\u09aa\u09cd\u09b0\u09bf\u09df SBSTC \u09b0\u09c1\u099f</span></h2>', 1)
    b = b.replace('<h2 class="op-h2" style="margin-top:26px">All Destinations</h2>',
                  '<h2 class="op-h2" style="margin-top:26px"><span class="label-en">All Destinations</span>'
                  '<span class="label-bn">\u09b8\u09ac \u0997\u09a8\u09cd\u09a4\u09ac\u09cd\u09af</span></h2>', 1)

    # ---- route cards: bilingual stop names ----
    def rt_sub(m):
        fr, to = m.group(1), m.group(2)
        return ('<span class="rt"><span class="label-en">' + fr + ' <span class="arr">→</span> ' + to + '</span>'
                '<span class="label-bn">' + sbstc_bn_name(fr) + ' <span class="arr">→</span> ' + sbstc_bn_name(to) + '</span></span>')
    b = re.sub(r'<span class="rt">([^<]+) <span class="arr">→</span> ([^<]+)</span>', rt_sub, b)
    # ---- destination chips: bilingual ----
    def chip_sub(m):
        return (m.group(1) + '<span class="label-en">' + m.group(2) + '</span>'
                '<span class="label-bn">' + sbstc_bn_name(m.group(2)) + '</span>' + m.group(3))
    b = re.sub(r'((?:<a|<span) class="via-chip"[^>]*>)([^<]+)(</(?:a|span)>)', chip_sub, b)
    # ---- route row labels ----
    b = b.replace(' buses</span>', ' <span class="label-en">buses</span>'
                  '<span class="label-bn">\u099f\u09bf \u09ac\u09be\u09b8</span></span>')
    b = b.replace('<span class="go">View Schedule \u203a</span>',
                  '<span class="go"><span class="label-en">View Schedule \u203a</span>'
                  '<span class="label-bn">\u09b8\u09ae\u09df\u09b8\u09c2\u099a\u09bf \u09a6\u09c7\u0996\u09c1\u09a8 \u203a</span></span>')

    # ---- FAQ: hide EN blocks in BN mode; map stop names inside BN blocks ----
    b = b.replace('<details class="op-faq open">', '<details class="op-faq only-en open>')
    b = b.replace('<details class="op-faq">', '<details class="op-faq only-en">')
    def _faq_walk(m):
        return _sbstc_bn_walk(m.group(1)) + m.group(2)
    b = re.sub(r'(<details class="op-faq only-bn[\s\S]*?)(</main>)', _faq_walk, b, count=1)

    # ---- footer ----
    for en, bn in [('../about.html">About Us', '../about.html"><span class="label-en">About Us</span><span class="label-bn">\u0986\u09ae\u09be\u09a6\u09c7\u09b0 \u09b8\u09ae\u09cd\u09aa\u09b0\u09cd\u0995\u09c7</span>'),
                   ('../contact.html">Contact Us', '../contact.html"><span class="label-en">Contact Us</span><span class="label-bn">\u09af\u09cb\u0997\u09be\u09af\u09cb\u0997</span>'),
                   ('../privacy-policy.html">Privacy Policy', '../privacy-policy.html"><span class="label-en">Privacy Policy</span><span class="label-bn">\u0997\u09cb\u09aa\u09a8\u09c0\u09df\u09a4\u09be \u09a8\u09c0\u09a4\u09bf</span>'),
                   ('../about.html#credits">Credits', '../about.html#credits"><span class="label-en">Credits</span><span class="label-bn">\u0995\u09c3\u09a4\u099c\u09cd\u099e\u09a4\u09be</span>'),
                   ('./">All Bus Timetables', './"><span class="label-en">All Bus Timetables</span><span class="label-bn">\u09b8\u09ac \u09ac\u09be\u09b8 \u09b8\u09ae\u09df\u09b8\u09c2\u099a\u09bf</span>')]:
        b = b.replace('<a href="' + en + '</a>', '<a href="' + bn + '</a>', 1)
    b = b.replace('<strong>BusJatri</strong> \u2014 West Bengal Bus Timetable',
                  '<strong>BusJatri</strong> \u2014 <span class="label-en">West Bengal Bus Timetable</span>'
                  '<span class="label-bn">\u09aa\u09b6\u09cd\u099a\u09bf\u09ae\u09ac\u0999\u09cd\u0997\u09c7\u09b0 \u09ac\u09be\u09b8 \u09b8\u09ae\u09df\u09b8\u09c2\u099a\u09bf</span>', 1)
    b = b.replace('Contact: <a href="mailto:busjatri@zohomail.in">busjatri@zohomail.in</a>',
                  '<span class="label-en">Contact:</span>'
                  '<span class="label-bn">\u09af\u09cb\u0997\u09be\u09af\u09cb\u0997:</span> <a href="mailto:busjatri@zohomail.in">busjatri@zohomail.in</a>', 1)
    b = b.replace('    Not affiliated with any transport corporation',
                  '    <span class="label-en">Not affiliated with any transport corporation</span>'
                  '<span class="label-bn">\u0995\u09cb\u09a8\u09cb \u09aa\u09b0\u09bf\u09ac\u09b9\u09a3 \u09b8\u0982\u09b8\u09cd\u09a5\u09be\u09b0 \u09b8\u0999\u09cd\u0997\u09c7 \u0986\u09ae\u09be\u09a6\u09c7\u09b0 \u09b8\u09ae\u09cd\u09aa\u09b0\u09cd\u0995 \u09a8\u09c7\u0987</span>', 1)

    # ---- Check Seat CTA (was Book tickets) ----
    b = b.replace('>Book tickets on SBSTC official site</span>',
                  '>Check Seat & Book on SBSTC official site</span>', 1)
    b = b.replace(' \u099f\u09bf\u0995\u09bf\u099f \u09ac\u09c1\u0995 \u0995\u09b0\u09c1\u09a8</span>', ' \u09b8\u09bf\u099f \u09a6\u09c7\u0996\u09c7 \u09ac\u09c1\u0995 \u0995\u09b0\u09c1\u09a8</span>', 1)

    # ---- Check Seat: inject seat URL for below-results CTA ----
    b = b.replace("<script src='../js/op-board.js?v=", "<script>window.BJ_SEAT_URL='https://sbstconline.co.in/reservation-home';</script><script src='../js/op-board.js?v=", 1)

    # ---- search card v2: day chips + time chips + on-page results ----
    ph_m = re.search(r"placeholder=['\"]e\.g\. ([^'\"]+)['\"]", b)
    ph_fr = ph_m.group(1) if ph_m else 'Burdwan'
    ph_m2 = re.search(r"placeholder=['\"]e\.g\. ([^'\"]+)['\"]", b[ph_m.end():]) if ph_m else None
    ph_to = ph_m2.group(1) if ph_m2 else 'Kolkata'
    off_link_v2 = ''
    off_m = re.search(r"<div class='alt'>[\s\S]*?</div>", b)
    if off_m:
        off_link_v2 = _sbstc_bn_walk(off_m.group(0))
    search_v2 = ('<section class="bj-op-search">'
                 '<div class="lb"><span class="label-en">Search SBSTC buses</span>'
                 '<span class="label-bn">\u098f\u09b8\u09ac\u09bf\u098f\u09b8\u099f\u09bf\u09b8\u09bf \u09ac\u09be\u09b8 \u0996\u09c1\u0981\u099c\u09c1\u09a8</span></div>'
                 '<div class="row">'
                 '<input id="bjFrom" type="text" placeholder="e.g. ' + ph_fr + '" autocomplete="off" style="color:var(--ink,#211c16)">'
                 '<button class="swap" onclick="bjSwap()" title="Swap" type="button">\u21c6</button>'
                 '<input id="bjTo" type="text" placeholder="e.g. ' + ph_to + '" autocomplete="off" style="color:var(--ink,#211c16)">'
                 '</div>'
'<div class="bj-dt-row">'
'<div class="bj-dt"><label for="bjDate">\U0001F4C5 <span class="label-en">Date</span><span class="label-bn">\u09a4\u09be\u09b0\u09bf\u0996</span></label>'
'<input id="bjDate" type="date"></div>'
'<div class="bj-dt"><label for="bjHour">\U0001F550 <span class="label-en">Time (hour)</span><span class="label-bn">\u09b8\u09ae\u09df (\u0998\u09a3\u09cd\u099f\u09be)</span></label>'
'<select id="bjHour">'
'<option value="any" selected>Any time</option>'
'<option value="0">12 AM</option>'
'<option value="1">1 AM</option>'
'<option value="2">2 AM</option>'
'<option value="3">3 AM</option>'
'<option value="4">4 AM</option>'
'<option value="5">5 AM</option>'
'<option value="6">6 AM</option>'
'<option value="7">7 AM</option>'
'<option value="8">8 AM</option>'
'<option value="9">9 AM</option>'
'<option value="10">10 AM</option>'
'<option value="11">11 AM</option>'
'<option value="12">12 PM</option>'
'<option value="13">1 PM</option>'
'<option value="14">2 PM</option>'
'<option value="15">3 PM</option>'
'<option value="16">4 PM</option>'
'<option value="17">5 PM</option>'
'<option value="18">6 PM</option>'
'<option value="19">7 PM</option>'
'<option value="20">8 PM</option>'
'<option value="21">9 PM</option>'
'<option value="22">10 PM</option>'
'<option value="23">11 PM</option>'
'</select></div>'
'</div>'
                 '<button class="go" style="margin-top:10px;width:100%" onclick="bjSearchGo()" type="button">'
                 '\U0001F68A <span class="label-en">Search</span><span class="label-bn">\u09b8\u09be\u09b0\u09cd\u099a \u0995\u09b0\u09c1\u09a8</span></button>'
                 + off_link_v2 +
                 '</section>'
                 '<div id="bjOpResults"></div>')
    b = re.sub(r"<section class=['\"]bj-op-search['\"][\s\S]*?</section>", lambda m: search_v2, b, count=1)

    # ---- embed stop mapping for op-board.js ----
    b = b.replace('<script>window.bjOpCfg',
                  '<script>window.bjStops = ' + SBSTC_STOPS_JSON + ';</scr' + 'ipt>\n<script>window.bjOpCfg', 1)
    return b


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
    """Remove the Operators chip row from the timetable index (user request:
    operators stay reachable from the home page instead)."""
    p = PAGES / 'index.html'
    if not p.exists():
        return
    s = p.read_text(encoding='utf-8')
    if TTI_MARKER not in s:
        print('  tti: operators row not present')
        return
    before = len(s)
    s2 = s.replace('\n' + TTI_BLOCK, '', 1)
    if TTI_MARKER in s2:
        # fallback: strip from the Operators heading through the bjOpsRow chip-row
        s2 = re.sub(r'\n?<h3 class="section-title"[^>]*>Operators</h3>\s*\n?<div class="chip-row" id="bjOpsRow".*?</div>\n', '', s, count=1, flags=re.S)
    if TTI_MARKER in s2:
        raise SystemExit('tti: operators row marker still present after strip - review bus-time-table/index.html')
    p.write_text(s2, encoding='utf-8')
    print(f'  tti: operators row removed ({before - len(s2)} bytes)')

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
