#!/usr/bin/env python3
"""
Via STOP page generator v2 — redesigns the existing /via/<stop>.html pages
(2,605 stop pages + A-Z index), same URLs, same set.

Old design (gen_stop_network.py) was plain single-language. New design matches
the site style approved for via-route pages (2026-09-23):
  1. Site-style header (logo + dark mode + EN/BN), crumbs, amber hero
  2. Departure board grouped by day-part (EARLY MORNING ... LATE NIGHT)
     with Bengali labels, time-at-stop + towards + route + badge
  3. Routes through the stop as chips
  4. FAQ 5 EN + 5 BN (fixes the Bengali-FAQ gap) + FAQPage/Breadcrumb schema
  5. Clean i18n: EN = zero Bengali; BN = Bengali labels/names; times numeric

Only rewrites files that already exist in via/ — no new URLs.
Usage (repo root):  python3 scripts/gen_via_stop_v2.py [--dry]
"""

import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_route_v2 as v2
import gen_via_v2 as vr

g = v2.g
bnplace = v2.bnplace
esc = vr.esc
fmt = vr.fmt
badge_html = vr.badge_html
bus_label = vr.bus_name
stops_of = vr.stops_of

CSS = vr.CSS
JS = vr.JS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIA_DIR = os.path.join(ROOT, "via")
BTT_DIR = os.path.join(ROOT, "bus-time-table")
BASE = "https://busjatri.in"

MAX_ROWS = 1000
MAX_CHIPS = 80

# (limit_minutes, EN label, BN label)
DAY_GROUPS = [
    (5 * 60, "EARLY MORNING", "ভোরের বাস"),
    (12 * 60, "MORNING", "সকালের বাস"),
    (17 * 60, "AFTERNOON", "দুপুরের বাস"),
    (22 * 60, "EVENING", "সন্ধ্যার বাস"),
    (24 * 60 + 5 * 60, "LATE NIGHT", "রাতের বাস"),
]


def to_min(t):
    return g.parse_time(t or "")


def build_index(buses):
    """slug(stop) -> {display: Counter, rows: [(min, time_str, towards, bus)]}"""
    idx = defaultdict(lambda: {"display": Counter(), "rows": []})
    for b in buses:
        stops = b.get("stoppages") or []
        if not stops:
            stops = [{"name": b.get("origin"), "up_time": b.get("departure_time")},
                     {"name": b.get("destination"), "down_time": b.get("arrival_time")}]
        for s in stops:
            name = (s.get("name") or "").strip()
            if not name or name in {"—", "-"}:
                continue
            key = g.slug(name)
            if not key:
                continue
            e = idx[key]
            e["display"][name] += 1
            if s.get("up_time"):
                e["rows"].append((to_min(s["up_time"]), s["up_time"], b.get("destination"), b))
            if s.get("down_time"):
                e["rows"].append((to_min(s["down_time"]), s["down_time"], b.get("origin"), b))
            if not (s.get("up_time") or s.get("down_time")):
                e["rows"].append((None, "—", b.get("destination"), b))
    return idx


def route_href(o, d, route_pages):
    fn = g.slug(o) + "-to-" + g.slug(d) + ".html"
    if fn in route_pages:
        return "../bus-time-table/" + fn
    return None


def row_html(row, route_pages):
    m, t, towards, b = row
    href = route_href(b.get("origin"), b.get("destination"), route_pages)
    if not href:
        href = "../index.html#/bus/" + str(b.get("id") or "")
    n_stops = len(stops_of(b)) or b.get("total_stoppages") or 0
    op = esc(bus_label(b))
    if b.get("operator") and b.get("operator") not in {"—", ""} and (b.get("bus_name") or "").lower() != (b.get("operator") or "").lower():
        op = op + " · " + esc(b.get("operator"))
    return ('<a class="bus-row" href="' + href + '">' +
            '<div class="dep">' + esc(fmt(t)) + "<small>→ " + esc(towards) + "</small></div>" +
            '<div class="bmid"><div class="op">' + op + "</div>" +
            '<div class="subrow"><span>' + esc(b.get("origin")) + " → " + esc(b.get("destination")) + "</span>" +
            "<span>" + str(n_stops) + ' <span class="label-en">stops</span><span class="label-bn">স্টপ</span></span></div></div>' +
            badge_html(b) + "</a>")


PAGE_TMPL = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>@@TITLE@@</title>
<meta name="description" content="@@DESC@@">
<link rel="canonical" href="@@CANON@@">
<meta property="og:title" content="@@TITLE@@">
<meta property="og:description" content="@@DESC@@">
<meta property="og:type" content="article">
<meta property="og:url" content="@@CANON@@">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,500;0,600;0,700;0,900&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Bengali:wght@400;500;600;700&display=swap" rel="stylesheet">
@@SCHEMA@@
<style>@@CSS@@
.day-group{margin:20px 0 8px;font-size:12px;font-weight:800;letter-spacing:.08em;color:var(--ink-dim);border-bottom:1px solid var(--line-strong);padding-bottom:4px}
.seemore-btn{display:block;width:100%;box-sizing:border-box;margin:14px 0 6px;padding:13px 16px;font:600 15px/1.2 inherit;background:var(--surface);border:1.5px solid var(--line-strong);border-radius:14px;color:var(--ink);cursor:pointer}
.seemore-btn:hover{border-color:var(--amber-ink)}
.bus-row.cut{display:none!important}
.day-group.cut{display:none!important}
</style></head>
<body>
<header class="header">
  <div class="header-inner">
    <a class="logo" href="../index.html">
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/><path d="M4 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M17 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M6 10h12"/></svg>
      Bus<span>Jatri</span>
    </a>
    <div class="header-actions">
      <button class="icon-btn" id="themeBtn" onclick="toggleTheme()" title="Toggle theme" aria-label="Toggle dark mode"></button>
      <div class="lang-group">
        <button class="lang-btn active" id="langEN" onclick="setLang('en')">EN</button>
        <button class="lang-btn" id="langBN" onclick="setLang('bn')">বাংলা</button>
      </div>
    </div>
  </div>
</header>
<div class="wrap">
<div class="crumbs"><a href="../index.html"><span class="label-en">Home</span><span class="label-bn">হোম</span></a> › <a href="./"><span class="label-en">Bus Stops</span><span class="label-bn">বাস স্টপ</span></a> › <b>@@STOP@@</b></div>
<div class="hero">
  <h1 class="routeline"><span class="rnode"><span class="rdot rdot-via"></span>Buses via @@STOP@@</span></h1>
  <div class="hbn hbn-sub">@@STOPBN@@ হয়ে যাওয়া সব বাস — এই স্টপের সময় সহ</div>
  <div class="chips">
    <span class="schip">🚌 @@N@@ <span class="label-en">bus services</span><span class="label-bn">টি বাস</span></span>
    <span class="schip">🕐 @@FIRST@@ – @@LAST@@</span>
    <span class="schip">🛣 @@ROUTES@@ <span class="label-en">routes</span><span class="label-bn">টি রুট</span></span>
  </div>
</div>
@@BOARD@@
<div class="sec"><h3><span class="label-en">Routes through @@STOP@@</span><span class="label-bn">@@STOPBN@@ হয়ে যাওয়া রুট</span></h3></div>
<div class="chip-row">@@CHIPS@@</div>
<div class="note">📍 <span class="label-en"><b>Stop page = every bus that halts at @@STOP@@.</b> Times shown are at this stop, in both directions. Times can change — verify with the operator.</span><span class="label-bn"><b>স্টপ পেজ = এই স্টপে থামা সব বাস।</b> সময়গুলি এই স্টপে, দুই দিকেরই। সময় বদলাতে পারে।</span></div>
<div class="sec"><h3>FAQ</h3></div>
@@FAQ@@
<footer><a href="../about.html">About</a><a href="../contribute.html">Contribute</a><a href="../blog/">Blog</a><a href="../privacy-policy.html">Privacy</a></footer>
</div>
<script>@@JS@@</script>
</body></html>"""


def stop_page(stop, e, route_pages, fname):
    rows = [r for r in e["rows"] if r[0] is not None] + [r for r in e["rows"] if r[0] is None]
    rows.sort(key=lambda r: (r[0] if r[0] is not None else 99999, str(r[3].get("bus_name") or "")))
    n_buses = len({id(r[3]) for r in e["rows"]})
    times = [r[0] for r in e["rows"] if r[0] is not None]
    first = min(e["rows"], key=lambda r: r[0] or 99999) if times else None
    last = max((r for r in e["rows"] if r[0] is not None), key=lambda r: r[0], default=None)
    night = any(r[0] is not None and (r[0] >= 22 * 60 or r[0] < 5 * 60) for r in e["rows"])
    dests = Counter()
    for r in e["rows"]:
        if r[2]:
            dests[r[2]] += 1
    for self_name in list(dests):
        if g.slug(self_name) == g.slug(stop):
            del dests[self_name]
    top_dests = [d for d, _ in dests.most_common(8)]

    shown = rows[:MAX_ROWS]

    parts = []
    cur_label = None
    for r in shown:
        label = None
        if r[0] is None:
            label = ("OTHER TIMES", "সময় নেই")
        else:
            for lim, en, bn in DAY_GROUPS:
                if r[0] < lim:
                    label = (en, bn)
                    break
        if label and label != cur_label:
            cur_label = label
            parts.append('<div class="day-group"><span class="label-en">' + label[0] + "</span>" +
                         '<span class="label-bn">' + label[1] + "</span></div>")
        parts.append(row_html(r, route_pages))
    board = "".join(parts)
    if len(rows) > len(shown):
        board += ('<div class="note">Showing first ' + str(len(shown)) + " of " + str(len(rows)) +
                  ' departures.</div>')
    if len(shown) > 14:
        board = ('<div class="vboard" id="vboard">' + board + '</div>' +
                 '<button type="button" class="seemore-btn" id="seemoreBtn"></button>')
    else:
        board = '<div class="vboard">' + board + '</div>' 

    routes = Counter()
    for r in e["rows"]:
        b = r[3]
        routes[(b.get("origin"), b.get("destination"))] += 1
    chips = []
    for (o, d), c in sorted(routes.items(), key=lambda x: -x[1])[:MAX_CHIPS]:
        href = route_href(o, d, route_pages)
        label = esc(o) + " → " + esc(d) + (" (" + str(c) + ")" if c > 1 else "")
        if href:
            chips.append('<a class="rel-chip" href="' + href + '">' + label + "</a>")
        else:
            chips.append('<span class="rel-chip">' + label + "</span>")

    first_txt = fmt(first[1] if first else None)
    last_txt = fmt(last[1] if last else None)
    faq_en = [
        ("How many buses pass through " + stop + "?",
         str(n_buses) + " bus services stop at " + stop + ". Check the departure board above for timings at this stop."),
        ("What is the first bus from " + stop + "?",
         ("The earliest listed service at " + stop + " is " + first[1] + " (" + bus_label(first[3]) + ") towards " + first[2] + ".") if first
         else "Timings at this stop are still being collected."),
        ("What is the last bus from " + stop + "?",
         ("The last listed service at " + stop + " is " + last[1] + " (" + bus_label(last[3]) + ") towards " + last[2] + ".") if last
         else "Timings at this stop are still being collected."),
        ("Which places can I reach from " + stop + " by bus?",
         ("Direct buses from this stop head to " + ", ".join(top_dests) + ".") if top_dests
         else "Check the departure board above for destinations served from this stop."),
        ("Is there a night bus at " + stop + "?",
         ("Yes — services are listed at " + stop + " between 10 PM and 5 AM.") if night
         else "No night service is currently listed at " + stop + " in the 10 PM – 5 AM window."),
    ]
    sbn = bnplace(stop)
    faq_bn = [
        ("📌 কয়টি বাস এই স্টপে থামে?",
         str(n_buses) + "টি বাস এই স্টপে থামে। উপরের বোর্ডে প্রতিটি বাসের সময় দেওয়া আছে।"),
        ("📌 প্রথম বাস কখন?",
         ("সবচেয়ে আগের বাস " + first[1] + " (" + bus_label(first[3]) + ") — " + bnplace(first[2]) + " যায়।") if first
         else "এই স্টপের সময় এখনও সংগ্রহ করা হচ্ছে।"),
        ("📌 শেষ বাস কতক্ষণে?",
         ("শেষ বাস " + last[1] + " (" + bus_label(last[3]) + ") — " + bnplace(last[2]) + " যায়।") if last
         else "এই স্টপের সময় এখনও সংগ্রহ করা হচ্ছে।"),
        ("📌 এই স্টপ থেকে কোথায় যাওয়া যায়?",
         (", ".join(bnplace(d) for d in top_dests) + " — এসব জায়গায় সরাসরি বাস আছে।") if top_dests
         else "উপরের বোর্ডে গন্তব্যগুলি দেখুন।"),
        ("📌 রাতের বাস আছে কি?",
         ("হ্যাঁ — রাত ১০টা থেকে ভোর ৫টার মধ্যে বাস আছে।") if night
         else "এখনও রাত ১০টা – ভোর ৫টার মধ্যে কোনো বাস তালিকাভুক্ত নেই।"),
    ]

    title = "Buses via " + stop + " — Timings at " + stop + " | BusJatri"
    desc = ("All buses passing through " + stop + " — " + str(n_buses) +
            " bus services with timings at " + stop + ", routes and destinations across West Bengal.")[:300]
    schema = (g.faq_schema(faq_en) + chr(10) +
              g.breadcrumb_schema([("Home", "/"), ("Bus Stops", "/via/"), (stop, "/via/" + fname)]))

    page = PAGE_TMPL
    for token, value in [
        ("@@TITLE@@", esc(title)), ("@@DESC@@", esc(desc)), ("@@CANON@@", esc(BASE + "/via/" + fname)),
        ("@@SCHEMA@@", schema), ("@@CSS@@", CSS), ("@@JS@@", JS),
        ("@@STOP@@", esc(stop)), ("@@STOPBN@@", esc(sbn)), ("@@STOPBN2@@", esc(sbn)),
        ("@@N@@", str(n_buses)), ("@@FIRST@@", first_txt), ("@@LAST@@", last_txt),
        ("@@ROUTES@@", str(len(routes))),
        ("@@BOARD@@", board), ("@@CHIPS@@", "".join(chips)),
        ("@@FAQ@@", "".join('<details class="faq only-en"><summary>' + esc(q) + "</summary><p>" + esc(a) + "</p></details>" for q, a in faq_en) +
         "".join('<details class="faq only-bn"><summary>' + q + "</summary><p>" + a + "</p></details>" for q, a in faq_bn)),
    ]:
        page = page.replace(token, value)
    return page


INDEX_TMPL = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>All Bus Stops A–Z | BusJatri</title>
<meta name="description" content="Every bus stop on BusJatri — departure boards for @@N@@ stops across West Bengal, with bus timings at each stop.">
<link rel="canonical" href="https://busjatri.in/via/">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,500;0,600;0,700;0,900&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Bengali:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>@@CSS@@
.day-group{margin:20px 0 8px;font-size:12px;font-weight:800;letter-spacing:.08em;color:var(--ink-dim);border-bottom:1px solid var(--line-strong);padding-bottom:4px}
.idx-letter{margin:22px 0 8px;font-family:var(--font-display);font-size:18px;font-weight:700;color:var(--amber-ink)}
</style></head>
<body>
<header class="header">
  <div class="header-inner">
    <a class="logo" href="../index.html">
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/><path d="M4 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M17 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M6 10h12"/></svg>
      Bus<span>Jatri</span>
    </a>
    <div class="header-actions">
      <button class="icon-btn" id="themeBtn" onclick="toggleTheme()" title="Toggle theme" aria-label="Toggle dark mode"></button>
      <div class="lang-group">
        <button class="lang-btn active" id="langEN" onclick="setLang('en')">EN</button>
        <button class="lang-btn" id="langBN" onclick="setLang('bn')">বাংলা</button>
      </div>
    </div>
  </div>
</header>
<div class="wrap">
<div class="crumbs"><a href="../index.html"><span class="label-en">Home</span><span class="label-bn">হোম</span></a> › <b>Bus Stops</b></div>
<div class="hero">
  <h1 class="routeline"><span class="rnode"><span class="rdot rdot-via"></span><span class="label-en">All bus stops A–Z</span><span class="label-bn">সব বাস স্টপ</span></span></h1>
  <div class="hbn hbn-sub">প্রতিটি স্টপে থামা বাসের সময়সূচি</div>
  <div class="chips"><span class="schip">🚏 @@N@@ <span class="label-en">stops</span><span class="label-bn">টি স্টপ</span></span></div>
</div>
@@LIST@@
<footer><a href="../about.html">About</a><a href="../contribute.html">Contribute</a><a href="../blog/">Blog</a><a href="../privacy-policy.html">Privacy</a></footer>
</div>
<script>@@JS@@</script>
</body></html>"""


SEE_MORE_JS = """<script>
(function(){
  var board=document.getElementById('vboard');
  if(!board){return;}
  var els=[].slice.call(board.children);
  var rows=[];
  for(var i=0;i<els.length;i++){if(els[i].classList.contains('bus-row')){rows.push(els[i]);}}
  if(rows.length<=14){return;}
  var KEEP=10,STEP=20,btn=null;
  function bn(n){var d='০১২৩৪৫৬৭৮৯';return String(n).replace(/[0-9]/g,function(c){return d[+c];});}
  function isBn(){return document.body.className.indexOf('lang-bn')>-1;}
  function leftCount(){var n=0;for(var i=0;i<rows.length;i++){if(rows[i].classList.contains('cut')){n++;}}return n;}
  function label(){
    var m=leftCount();
    if(m<1){return;}
    var n=Math.min(STEP,m);
    if(btn){btn.textContent=isBn()?('আরও '+bn(n)+'টি বাস দেখুন ('+bn(m)+'টি বাকি)'):('See '+n+' more buses ('+m+' left)');}
  }
  var shown=0;
  for(var i=0;i<els.length;i++){
    var e=els[i];
    if(e.classList.contains('bus-row')){shown++;if(shown>KEEP){e.classList.add('cut');}}
    else{if(shown>=KEEP){e.classList.add('cut');}}
  }
  btn=document.getElementById('seemoreBtn');
  if(!btn){return;}
  btn.addEventListener('click',function(){
    var revealed=0;
    for(var j=0;j<els.length&&revealed<STEP;j++){
      var e=els[j];
      if(e.classList.contains('cut')){e.classList.remove('cut');if(e.classList.contains('bus-row')){revealed++;}}
    }
    if(leftCount()<1){if(btn.parentNode){btn.parentNode.removeChild(btn);}}
    else{label();}
  });
  label();
  if(window.MutationObserver){
    new MutationObserver(function(){if(btn){label();}}).observe(document.body,{attributes:true,attributeFilter:['class']});
  }
})();
</script>"""


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="report only, don't write")
    ap.add_argument("--limit", type=int, default=0, help="only first N pages (testing)")
    args = ap.parse_args()

    buses = g.BUSES
    route_pages = set(f for f in os.listdir(BTT_DIR) if f.endswith(".html"))
    idx = build_index(buses)

    existing = set(f for f in os.listdir(VIA_DIR) if f.endswith(".html"))
    stop_files = sorted(f for f in existing if f != "index.html")

    # map file slug -> canonical display name (most common spelling in data)
    name_for = {}
    for f in stop_files:
        sslug = f[:-5]
        if sslug in idx:
            name_for[f] = idx[sslug]["display"].most_common(1)[0][0]
        else:
            name_for[f] = sslug.replace("-", " ").title()

    todo = stop_files if not args.limit else stop_files[:args.limit]
    done = 0
    missing = []
    for f in todo:
        stop = name_for[f]
        e = idx.get(g.slug(stop))
        if not e:
            missing.append(f)
            continue
        page = stop_page(stop, e, route_pages, f)
        if not args.dry:
            with open(os.path.join(VIA_DIR, f), "w", encoding="utf-8") as fh:
                fh.write(page.replace("</body>", SEE_MORE_JS + "</body>", 1))
        done += 1
        if done <= 3 or args.dry:
            print(f + ": " + str(len({id(r[3]) for r in e["rows"]})) + " buses, " + str(len(page) // 1024) + "KB")

    # A-Z index
    by_letter = defaultdict(list)
    for f in stop_files:
        nm = name_for[f]
        by_letter[(nm[0].upper() if nm[:1].isascii() and nm[:1].isalpha() else "#")].append((nm, f))
    parts = []
    for letter in sorted(by_letter):
        parts.append('<div class="idx-letter">' + letter + "</div>" + '<div class="chip-row">')
        for nm, f in sorted(by_letter[letter]):
            parts.append('<a class="rel-chip" href="' + f + '">' + esc(nm) + "</a>")
        parts.append("</div>")
    ipage = INDEX_TMPL.replace("@@CSS@@", CSS).replace("@@JS@@", JS)
    ipage = ipage.replace("@@N@@", str(len(stop_files))).replace("@@LIST@@", "".join(parts))
    if not args.dry:
        with open(os.path.join(VIA_DIR, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(ipage)
    print("index: " + str(len(stop_files)) + " stops, " + str(len(ipage) // 1024) + "KB")

    print("regenerated " + str(done) + " stop pages + index" +
          ("; no data for: " + ", ".join(missing[:10]) if missing else ""))


if __name__ == "__main__":
    main()
