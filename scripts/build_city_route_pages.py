#!/usr/bin/env python3
"""Build Kolkata CITY route pages — design: hero + TIME + ROUTE + STOPPAGE.

Replaces the generic route page for intra-Kolkata city routes with the
approved design (cstc-city.css layer). Idempotent: only writes pages whose
slug is a city route; run AFTER gen_seo_pages.py.

Usage:  python3 scripts/build_city_route_pages.py [--limit N]
"""
import json, os, re, html, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "busjatri_data.json")
OUT = os.path.join(ROOT, "bus-time-table")
BASE = "https://busjatri.in"
TODAY = "2026-10-06"

CITY = ['esplanade','howrah','park street','barabazar','sealdah','shyambazar','garia','behala','jadavpur',
 'tollygunge','dumdum','barasat','salt lake','karunamoyee','ballygunge','bhowanipore','alipore','entally',
 'maniktala','baguiati','kestopur','lake town','park circus','gariahat','rajabazar','shibpur','bally','belur',
 'uttarpara','dankuni','baranagar','kamalgazi','narendrapur','taratala','metiabruz','garden reach','khidirpur',
 'cossipore','bagbazar','chitpur','kankurgachi','dhakuria','kasba','thakurpukur','joka','santragachi','birati',
 'madhyamgram','sodepur','agarpara','belghoria','baruipur','sonarpur','nabanna','ultadanga','sarsuna','parnasree',
 'babughat','dunlop','tobin','mukundapur','badartala','chetla','barisha','topsia','chapadanga','bonhooghly',
 'picnic garden','layalka','dakshineswar','shibrampur','shilpara','bengal chemical','behala 14','rajarhat','new town','ecospace']

# Bengali names for common city places (falls back to English)
BN = {'esplanade':'এসপ্ল্যানেড','howrah':'হাওড়া','howrah station':'হাওড়া স্টেশন','park street':'পার্ক স্ট্রিট',
 'sealdah':'শিয়ালদহ','shyambazar':'শ্যামবাজার','garia':'গড়িয়া','behala':'বেহালা','jadavpur':'যাদবপুর',
 'tollygunge':'টালিগঞ্জ','dumdum':'দমদম','barasat':'বারাসাত','salt lake':'সল্টলেক','karunamoyee':'করুণাময়ী',
 'ballygunge':'বালিগঞ্জ','ballygunge stn':'বালিগঞ্জ স্টেশন','alipore':'আলিপুর','baguiati':'বাগুইআটি',
 'kestopur':'কেষ্টপুর','lake town':'লেক টাউন','park circus':'পার্ক সার্কাস','gariahat':'গড়িয়াহাট',
 'rajabazar':'রাজাবাজার','baranagar':'বরানগর','kamalgazi':'কামালগাজি','narendrapur':'নারেন্দ্রপুর',
 'taratala':'তারাতলা','garden reach':'গার্ডেন রিচ','khidirpur':'খিদিরপুর','cossipore':'কাশীপুর',
 'bagbazar':'বাগবাজার','chitpur':'চিৎপুর','kankurgachi':'কাঁকুড়গাছি','dhakuria':'ধাকুরিয়া','kasba':'কসবা',
 'thakurpukur':'ঠাকুরপুকুর','joka':'জোকা','santragachi':'সাঁতরাগাছি','birati':'বিরাটি','madhyamgram':'মধ্যমগ্রাম',
 'sodepur':'সোদপুর','agarpara':'আগরপাড়া','baruipur':'বারুইপুর','sonarpur':'সোনারপুর','nabanna':'নবান্ন',
 'ultadanga':'উল্টোডাঙ্গা','parnasree':'পার্নাশ্রী','babughat':'বাবুঘাট','dunlop':'ডানলপ','tobin road':'টোবিন রোড',
 'sinthi more':'সিন্থি মোড়','chiriamore':'চিড়িয়ামোড়','grey street':'গ্রে স্ট্রিট','vivekananda road':'বিবেকানন্দ রোড',
 'm.g. road':'এম জি রোড','bbd bag':'বিবিডি বাগ','hazra':'হাজরা','rashbehari avenue':'রাসবিহারী অ্যাভিনিউ',
 'deshapriya park':'দেশপ্রিয় পার্ক','college street':'কলেজ স্ট্রিট','howrah maidan':'হাওড়া ময়দান','bandha ghat':'বাঁধাঘাট'}

def esc(v): return html.escape(str(v or ''), quote=True)
def slug(v): return re.sub(r'[^a-z0-9]+', '-', (v or '').lower()).strip('-') or 'x'
def bn(name):
    return BN.get((name or '').strip().lower(), '')

def is_city(p):
    p = (p or '').lower()
    return any(c in p for c in CITY)

def norm_place(p):
    p = re.sub(r'\s+', ' ', (p or '').strip())
    p = re.sub(r'\s+(station|stn|bus stand|bus-stand|terminus|depot|more|stand)$', '', p, flags=re.I)
    return p.strip() or p

def collect_stops(bs):
    out = []
    for b in sorted(bs, key=lambda x: -len(x.get('stoppages') or [])):
        for st in (b.get('stoppages') or []):
            nm = (st.get('name') if isinstance(st, dict) else st) or ''
            nm = re.sub(r'\s+', ' ', nm).strip()
            if nm and nm not in out:
                out.append(nm)
    return out

def routenum(name):
    n = re.sub(r'^(WBTC|CSTC|SBSTC)\s+', '', (name or '').strip(), flags=re.I)
    m = re.search(r'([A-Za-z]{0,3}-?\d+[A-Za-z0-9/]*)', n)
    return m.group(1) if m else (n[:12] or 'CITY')

def parse_min(t):
    m = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)?', (t or '').strip(), re.I)
    if not m: return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or '').upper()
    if ap == 'PM' and h < 12: h += 12
    if ap == 'AM' and h == 12: h = 0
    return h * 60 + mi

def fmt(minutes):
    if minutes is None: return '—'
    h, mi = divmod(minutes, 60); ap = 'AM' if h < 12 else 'PM'; h = h % 12 or 12
    return f'{h}:{mi:02d} {ap}'

def lbl(en, bn_txt):
    b = f'<span class="label-bn" style="display:none">{esc(bn_txt)}</span>' if bn_txt else ''
    return f'<span class="label-en">{esc(en)}</span>{b}'

def header():
    return ('<header class="header"><div class="container header-inner"><a href="../" class="logo" aria-label="BusJatri home">'
            '<img class="brand-logo" src="/logo.png" alt="BusJatri" style="width:30px;height:30px;border-radius:50%">Bus<span>Jatri</span></a>'
            '<div class="hdr-ctrl"><div class="lang-switch" role="group" aria-label="Language">'
            '<button type="button" id="langEn" class="pill pill-en on">EN</button>'
            '<button type="button" id="langBn" class="pill pill-bn">বাংলা</button></div>'
            '<button type="button" id="themeBtn" class="theme-btn" aria-label="Toggle dark mode">☾</button></div></div></header>')

ROUTE_CSS = """<style>
.rm-wrap{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:16px;margin:12px 0}
.rm-track{overflow-x:auto;padding:6px 0 4px;scrollbar-width:thin}
.rm-stops{display:flex;align-items:flex-start;width:max-content;min-width:100%;position:relative}
.rm-stop{display:flex;flex-direction:column;align-items:center;width:96px;flex-shrink:0;position:relative}
.rm-stop:not(:last-child):after{content:"";position:absolute;top:5px;left:50%;width:100%;height:2px;background:color-mix(in srgb,var(--amber) 45%,transparent)}
.rm-dot{width:11px;height:11px;border-radius:50%;background:var(--surface);border:2px solid var(--amber);z-index:1}
.rm-stop.end .rm-dot{background:var(--amber)}
.rm-name{margin-top:7px;font-size:11px;font-weight:700;text-align:center;line-height:1.25}
.rm-name .bn{display:block;font-size:10px;color:var(--ink-dim);font-weight:500}
.dep-chips{display:flex;flex-wrap:wrap;gap:7px}
.dep-chip{font:700 13px var(--font-mono);background:var(--surface-2);border:1px solid var(--line);border-radius:9px;padding:7px 12px;color:var(--ink);min-width:74px;text-align:center}
.dep-chip.next{background:var(--amber);border-color:var(--amber);color:#fff9ee;box-shadow:0 4px 12px rgba(184,121,31,.22)}
.dep-chip.past{opacity:.42}
</style>"""

def shell(title, desc, canonical, body, jsonld=""):
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))}</script>' if jsonld else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canonical}">
<meta property="og:type" content="article"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canonical}"><meta property="og:site_name" content="BusJatri"><meta property="og:image" content="{BASE}/og-image.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="theme-color" content="#b8791f">
<link rel="icon" href="../favicon.svg"><link rel="stylesheet" href="../css/seo.css?v=city20261006"><link rel="stylesheet" href="../css/extras.css"><link rel="stylesheet" href="../css/cstc-city.css?v=city20261006">
{ROUTE_CSS}{ld}</head><body>{header()}<main class="container seo-main">
<div class="cstc-breadcrumb" style="font:600 11px var(--font-mono);color:var(--ink-dim);padding:14px 0 2px"><a href="../">Home</a> / <a href="../kolkata-city-bus-timetable">Kolkata City Bus</a> / {esc(title.split(' Bus ')[0])}</div>
{body}</main><footer class="footer"><div class="container"><p><strong>BusJatri</strong> — West Bengal bus timetable<br>Not affiliated with any transport corporation</p></div></footer>
<script defer src="../js/hdr.js?v=hdrunify20261005d"></script><script defer src="../js/lang.js?v=lang20261005c"></script><script>(function(){{var c=[].slice.call(document.querySelectorAll(".dep-chip"));if(!c.length)return;var d=new Date(),n=d.getHours()*60+d.getMinutes(),nx=null;c.forEach(function(x){{var m=+x.dataset.min;if(m<n)x.classList.add("past");if(m>=n&&(!nx||m<+nx.dataset.min))nx=x;}});if(nx){{nx.classList.add("next");var el=document.getElementById("nextNote");if(el)el.textContent="Next bus "+nx.textContent+" — in "+(+nx.dataset.min-n)+" min";}}}})();</script></body></html>'''

def build_page(origin, destination, buses):
    rn = routenum(buses[0].get('bus_name'))
    stops = collect_stops(buses)
    # times
    times = sorted({parse_min(b.get('departure_time')) for b in buses if parse_min(b.get('departure_time'))})
    operators = sorted({(b.get('operator') or '').strip() for b in buses if (b.get('operator') or '').strip()})
    op = ' · '.join(operators[:2]) or 'Kolkata city bus'
    title = f'{origin} to {destination} Bus Timetable ({rn})'
    desc = (f'{origin} to {destination} {rn} Kolkata city bus route — official route stops, '
            f'{"departure times, " if times else ""}timetable and related city routes. English and Bengali route details on BusJatri.')[:300]
    canonical = f'{BASE}/bus-time-table/{slug(origin)}-to-{slug(destination)}'

    # stats
    n_stops = len(stops)
    stats = [f'<span class="cstc-stat">{lbl("Route","রুট")} <strong>{esc(rn)}</strong></span>']
    if times:
        stats.append(f'<span class="cstc-stat">{lbl("Departures","ছাড়া")} <strong>{len(times)}</strong></span>')
        stats.append(f'<span class="cstc-stat">{lbl("First","প্রথম")} <strong>{fmt(times[0])}</strong></span>')
        stats.append(f'<span class="cstc-stat">{lbl("Last","শেষ")} <strong>{fmt(times[-1])}</strong></span>')
    stats.append(f'<span class="cstc-stat">{lbl("Stops","স্টপ")} <strong>{n_stops}</strong></span>')

    # TIME section — only when times exist; every departure listed individually
    if times:
        chips = ''.join(f'<span class="dep-chip" data-min="{t}">{fmt(t)}</span>' for t in times)
        time_sec = f'''<section class="cstc-direction" id="departures">
  <div class="cstc-direction-head"><div><h2 class="cstc-direction-title">{lbl("Departure times","ছাড়ার সময়")}</h2>
  <p class="cstc-direction-meta">{len(times)} departures · first {fmt(times[0])} · last {fmt(times[-1])}</p></div>
  <span class="cstc-eyebrow">{lbl("Time","সময়")}</span></div>
  <div class="dep-chips">{chips}</div>
  <p class="cstc-stop-note" id="nextNote">{lbl("All published departure times for this route.","এই রুটের সব প্রকাশিত ছাড়ার সময়।")}</p>
</section>'''
    else:
        time_sec = ''

    # ROUTE + STOPPAGE
    rm = ''.join(f'<div class="rm-stop {"end" if i in (0, n_stops-1) else ""}"><span class="rm-dot"></span>'
                 f'<span class="rm-name">{esc(s)}{f"<span class=\"bn\">{esc(bn(s))}</span>" if bn(s) else ""}</span></div>' for i, s in enumerate(stops))
    li = ''.join(f'<li class="{"end" if i in (0, n_stops-1) else ""}"><span class="cstc-stop-dot"></span>{esc(s)}'
                 f'<span class="bn">{esc(bn(s))}</span></li>' for i, s in enumerate(stops))
    stop_sec = f'''<section class="cstc-direction">
  <div class="cstc-direction-head"><div><h2 class="cstc-direction-title">{lbl(f"Route & stoppages — {rn}", f"রুট ও স্টপ — {rn}")}</h2>
  <p class="cstc-direction-meta">{n_stops} route stops · {esc(origin)} → {esc(destination)}</p></div>
  <span class="cstc-eyebrow">{lbl("Route","রুট")}</span></div>
  <div class="rm-wrap" style="margin:0 0 14px;box-shadow:none"><div class="rm-track"><div class="rm-stops">{rm}</div></div></div>
  <div class="cstc-stops" style="margin-top:0"><div class="cstc-stops-head"><strong>{lbl("Stop list","স্টপ তালিকা")}</strong><span>{n_stops} stops</span></div><ol>{li}</ol></div>
  <p class="cstc-stop-note">{lbl("Stoppages from the WBTC route record. Stop-wise times are added when published.","WBTC রুট রেকর্ড থেকে স্টপ। স্টপ-ভিত্তিক সময় প্রকাশিত হলে যোগ হবে।")}</p>
</section>''' if stops else ''

    body = f'''<section class="cstc-hero">
  <span class="cstc-eyebrow">{lbl("Kolkata city bus","কলকাতা সিটি বাস")}</span>
  <h1><span class="route-code">{esc(rn)}</span> {esc(origin)} → {esc(destination)}</h1>
  <p class="cstc-muted">{esc(origin)} → {esc(destination)} and reverse direction — {esc(op)}.</p>
  <div class="cstc-stats">{''.join(stats)}</div>
</section>
{time_sec}
{stop_sec}'''

    jsonld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f"What is the {rn} bus route from {origin} to {destination}?",
         "acceptedAnswer": {"@type": "Answer", "text": f"The {rn} city bus runs from {origin} to {destination} via {n_stops} stops" + (f", first departure {fmt(times[0])}." if times else ".")}},
        {"@type": "Question", "name": f"How many stops are on the {origin} to {destination} route?",
         "acceptedAnswer": {"@type": "Answer", "text": f"The route has {n_stops} stops: {', '.join(stops[:8])}" + ("…" if n_stops > 8 else "") + "."}}]}
    return shell(title, desc, canonical, body, jsonld)

def main():
    limit = None
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])
    data = json.load(open(DATA, encoding='utf-8'))
    buses = data['buses'] if isinstance(data, dict) else data
    groups = defaultdict(list)
    for b in buses:
        o, d = (b.get('origin') or '').strip(), (b.get('destination') or '').strip()
        if o and d and is_city(o) and is_city(d):
            groups[(norm_place(o), norm_place(d))].append(b)
    # global route-number -> stops (for routes with a rich record elsewhere)
    by_rn = defaultdict(list)
    for b in buses:
        rn = routenum(b.get('bus_name'))
        if rn and (b.get('stoppages')):
            by_rn[rn].append(b)
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for (o, d), bs in sorted(groups.items()):
        if not collect_stops(bs):
            rn = routenum(bs[0].get('bus_name'))
            bs = bs + by_rn.get(rn, [])   # borrow stops from the same route number
        page = build_page(o, d, bs)
        with open(os.path.join(OUT, f'{slug(o)}-to-{slug(d)}.html'), 'w', encoding='utf-8') as f:
            f.write(page)
        n += 1
        if limit and n >= limit: break
    print(f'city route pages written: {n}')

if __name__ == '__main__':
    main()
