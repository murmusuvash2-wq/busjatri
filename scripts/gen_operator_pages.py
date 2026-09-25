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
<p class="intro" style="color:var(--ink-dim);line-height:1.7;max-width:700px;margin:8px 0 0">{intro}</p>
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

    stats = f'''<section class="op-stats">
  <div class="op-stat"><div class="lbl">🚌 Listed services</div><div class="val">{len(buses)}</div></div>
  <div class="op-stat"><div class="lbl">🗺 Routes covered</div><div class="val">{len(routes)}</div></div>
</section>'''

    popular = f'''<h2 class="op-h2">Popular {esc(op['name'])} Routes</h2>
<div class="op-grid">
{''.join(rows)}
</div>'''

    chiprow = f'''<h2 class="op-h2" style="margin-top:26px">All Destinations</h2>
<div class="chip-row" aria-label="All destinations">{''.join(chips)}</div>'''

    op_info = OPS_INFO.get(op["stem"], ("bus services", "বাস পরিষেবা"))
    top_fr, top_to, top_n = "", "", 0
    if top:
        (top_fr, top_to), top_n = top[0]
    dest_names = [d for d, _ in dests.most_common(8) if d]
    nb = op["bn"]
    DET_STYLE = ' style="border:1px solid var(--line,rgba(33,28,22,.15));border-radius:10px;padding:10px 14px;margin:8px 0;background:var(--surface,#fffcf4)"'
    SUM_STYLE = '<summary style="cursor:pointer;font-weight:600;font-size:.95rem">'
    ANS_STYLE = '<p style="margin:8px 0 0;font-size:.9rem;line-height:1.7;color:var(--ink-dim,#665)">'
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
    ]
    faq_items = "".join(
        ('<details' + (' open' if i == 0 else '') + DET_STYLE + SUM_STYLE + q + "</summary>"
         + ANS_STYLE + a + "</p></details>")
        for i, (q, a) in enumerate(faq_en))
    faq_items += "".join(
        ('<details class="only-bn"' + (' open' if i == 0 else '') + DET_STYLE + SUM_STYLE + q + "</summary>"
         + ANS_STYLE + a + "</p></details>")
        for i, (q, a) in enumerate(faq_bn))
    faq_section = '<h2 class="op-h2" style="margin-top:26px">FAQ</h2>' + faq_items
    import json as _j
    faq_schema = ('<script type="application/ld+json">' + _j.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q,
                         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq_en + faq_bn]},
        ensure_ascii=False) + "</script>")

    body = HEAD.format(title=esc(op['title']), desc=esc(op['desc']), stem=op['stem'],
                       BASE=BASE, h1=esc(op['h1']), bn=op['bn'], intro=esc(op['intro']), faq_schema=faq_schema)
    body += stats + popular + chiprow + faq_section + '\n</main>\n' + FOOT
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
