#!/usr/bin/env python3
"""
Via-route page generator v2 — redesigns the existing *-to-*-via-*.html pages
(demo approved 2026-09-23: via-route-demo.html).

For every existing via page (same URL, same sitemap):
  1. Site-style header (logo + dark mode + EN/BN), crumbs, amber hero
  2. 3-place route line: Origin -> VIA chip -> via stop -> Destination
  3. Through buses: buses of the (origin, destination) route that stop at the
     via stop, showing the ONWARD time at that stop (up_time — the old design
     wrongly showed down_time) + arrival + stops + badge
  4. "Board at <via>" section: buses that START at the via stop and go to the
     destination (user-requested 2026-09-23)
  5. Related chips: direct route, other via pages of the same route, the
     via-stop page (/via/) when it exists
  6. FAQ 5 EN + 5 BN (data-driven) + FAQPage + BreadcrumbList JSON-LD
  7. Clean i18n: EN = zero Bengali; BN = Bengali labels/names; times numeric

Files whose "via" is part of a literal place name (e.g. Indus Via-Kolkata)
are plain route pages and are skipped untouched.
Usage (repo root):  python3 scripts/gen_via_v2.py [--dry]
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_route_v2 as v2

g = v2.g
bnplace = v2.bnplace

OUT = g.OUT
BASE = g.BASE

BN_STOPS = "স্টপ"
BN_BUSES = "বাস"


def stops_of(b):
    st = b.get("stoppages") or []
    if isinstance(st, list):
        return [x for x in st if isinstance(x, dict)]
    return []


def parse_via_file(fname):
    stem = fname[:-5]
    vi = stem.find("-via-")
    ti = stem.find("-to-")
    if vi == -1 or ti == -1:
        return None
    if vi < ti:
        o = stem[:vi]
        v = stem[vi + 5:ti]
        t = stem[ti + 4:]
    else:
        left = stem[:vi]
        v = stem[vi + 5:]
        if "-to-" not in left:
            return None
        o, t = left.split("-to-", 1)
    if o and v and t:
        return (o, t, v)
    return None


def sort_key(b):
    pt = g.parse_time(b.get("departure_time") or "")
    return (0, pt) if pt else (1, "")


def badge_html(b):
    bt = (b.get("bus_type") or "") + " " + (b.get("operator") or "") + " " + (b.get("bus_name") or "")
    if "SBSTC" in bt:
        return '<span class="badge badge-gov">SBSTC</span>'
    if "NBSTC" in bt:
        return '<span class="badge badge-gov">NBSTC</span>'
    if "WBTC" in bt:
        return '<span class="badge badge-gov">WBTC</span>'
    if "AC" in (b.get("bus_type") or "").upper():
        return '<span class="badge badge-ac"><span class="label-en">AC</span><span class="label-bn">এসি</span></span>'
    return '<span class="badge badge-priv"><span class="label-en">Private</span><span class="label-bn">বেসরকারি</span></span>'


def bus_name(b):
    n = (b.get("bus_name") or "").strip()
    if n and n not in ("-", "—"):
        return n
    return (b.get("operator") or "").strip() or "—"


def esc(s):
    return g.esc(str(s or ""))


def fmt(t):
    t = (t or "").strip()
    return t if t else "—"


CSS = """:root{--bg:#f5efe1;--surface:#fffcf4;--surface-2:#efe6d3;--ink:#211c16;--ink-dim:#6f6653;--line:rgba(33,28,22,.13);--line-strong:rgba(33,28,22,.24);--amber:#b8791f;--amber-ink:#6b4610;--amber-soft:rgba(184,121,31,.14);--shadow-sm:0 2px 12px rgba(33,28,22,.1);--radius-lg:20px;--radius:14px;--font-display:'Fraunces',Georgia,serif;--font-body:'IBM Plex Sans','IBM Plex Sans Bengali',system-ui,sans-serif}
[data-theme="dark"]{--bg:#15121d;--surface:#201c2b;--surface-2:#29243570;--ink:#f1ead8;--ink-dim:#a89b87;--line:rgba(241,234,216,.1);--line-strong:rgba(241,234,216,.2);--amber:#eda94a;--amber-ink:#f6cd8f;--amber-soft:rgba(237,169,74,.16)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--font-body);background:var(--bg);color:var(--ink);line-height:1.55}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.header{background:var(--surface);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:100;backdrop-filter:blur(14px) saturate(1.1);background:color-mix(in srgb,var(--surface) 88%,transparent)}
.header::after{content:"";position:absolute;left:0;right:0;bottom:-6px;height:6px;background-image:radial-gradient(circle at 10px 0,var(--bg) 5px,transparent 5.5px);background-size:20px 6px;background-repeat:repeat-x}
.header-inner{display:flex;align-items:center;justify-content:space-between;padding:13px 18px;gap:10px;position:relative;z-index:1;max-width:788px;margin:0 auto}
.logo{display:flex;align-items:center;gap:9px;font-family:var(--font-display);font-size:1.32rem;font-weight:700;color:var(--ink);letter-spacing:-.2px;text-decoration:none}
.logo .icon{width:1.35rem;height:1.35rem;color:var(--amber);stroke-width:1.6}
.logo span{color:var(--amber-ink)}
.header-actions{display:flex;align-items:center;gap:8px}
.icon-btn{width:38px;height:38px;display:inline-flex;align-items:center;justify-content:center;background:var(--surface-2);border:1px solid var(--line);border-radius:50%;cursor:pointer;color:var(--ink);font-size:15px;transition:.2s}
.icon-btn:active{transform:scale(.92)}
.icon-btn svg{width:17px;height:17px}
.lang-group{display:flex;border:1px solid var(--line);border-radius:999px;padding:3px;gap:2px;background:var(--surface-2)}
.lang-btn{background:transparent;border:none;border-radius:999px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;color:var(--ink-dim);transition:.2s;font-family:var(--font-body)}
.lang-btn.active{background:var(--amber);color:#fff9ee}
[data-theme="dark"] .lang-btn.active{color:#241706}
.wrap{max-width:760px;margin:0 auto;padding:14px 14px 60px}
.crumbs{font-size:12px;color:var(--ink-dim);margin:14px 0}.crumbs a{color:var(--ink-dim)}
.hero{background:linear-gradient(135deg,#b8791f 0%,#8a5a12 100%);border-radius:var(--radius-lg);padding:18px;color:#fff;margin-bottom:12px;animation:fadeUp .5s .05s ease both}
.hero .hbn-sub{font-size:12.5px;opacity:.92}
.routeline{display:flex;align-items:center;gap:8px;margin:2px 0 6px;flex-wrap:wrap}
.rnode{display:flex;align-items:center;gap:6px;font-family:var(--font-display);font-size:15px;font-weight:700}
.rdot{width:9px;height:9px;border-radius:50%;background:rgba(255,255,255,.95);flex:none}
.rdot-via{background:#ffd98a;box-shadow:0 0 0 4px rgba(255,217,138,.25)}
.rlink{flex:none;width:26px;height:2px;background:rgba(255,255,255,.5);border-radius:2px}
.via-chip{background:rgba(255,255,255,.18);border:1px solid rgba(255,217,138,.7);color:#ffe3ad;border-radius:999px;padding:3px 10px;font-size:11px;font-weight:800;letter-spacing:.03em}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.schip{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:4px 10px;font-size:11px;font-weight:700}
.sec{margin:20px 0 8px;display:flex;align-items:baseline;justify-content:space-between}
.sec h3{font-size:16px;font-family:var(--font-display)}
.sec .cnt{font-size:12px;color:var(--ink-dim)}
.bus-row{display:flex;align-items:center;gap:12px;background:var(--surface);border:1.5px solid var(--line);border-radius:12px;padding:10px 12px;margin-bottom:8px;text-decoration:none;color:inherit;transition:transform .15s,border-color .15s;animation:fadeUp .4s ease both;animation-delay:calc(var(--i,0)*.05s)}
a.bus-row:hover{transform:translateY(-2px);border-color:var(--amber)}
.dep{flex:none;font-family:var(--font-mono,monospace);font-size:14px;font-weight:700;color:var(--amber-ink);line-height:1.2}
[data-theme="dark"] .dep{color:var(--amber)}
.dep small{display:block;font-size:10px;font-weight:600;color:var(--ink-dim)}
.bmid{flex:1;min-width:0}
.op{font-size:13.5px;font-weight:800}
.subrow{display:flex;flex-wrap:wrap;gap:5px;align-items:center;font-size:11px;color:var(--ink-dim);margin-top:3px}
.atvia{background:var(--amber-soft);color:var(--amber-ink);font-weight:700;border-radius:6px;padding:2px 7px;font-size:10.5px}
[data-theme="dark"] .atvia{color:var(--amber)}
.badge{flex:none;font-size:9.5px;font-weight:800;letter-spacing:.05em;border-radius:6px;padding:3px 7px;text-transform:uppercase}
.badge-gov{background:rgba(43,74,138,.12);color:#2b4a8a}
.badge-priv{background:var(--amber-soft);color:var(--amber-ink)}
.badge-ac{background:rgba(6,112,92,.12);color:#06705c}
[data-theme="dark"] .badge-gov{background:rgba(122,162,247,.15);color:#a9c4ff}
[data-theme="dark"] .badge-priv{background:rgba(237,169,74,.16);color:#f6cd8f}
[data-theme="dark"] .badge-ac{background:rgba(94,214,184,.14);color:#8ce0c4}
.board-sec{background:var(--surface);border:1.5px solid var(--amber);border-radius:var(--radius);padding:12px;animation:fadeUp .5s .3s ease both}
.board-head{display:flex;align-items:center;gap:8px;margin-bottom:4px}
.board-head svg{width:18px;height:18px;color:var(--amber);stroke-width:2.2;flex:none}
.board-head h4{font-size:14px;font-family:var(--font-display)}
.board-note{font-size:11.5px;color:var(--ink-dim);margin:2px 0 10px}
.note{background:var(--amber-soft);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:13px;color:var(--ink-dim);margin:18px 0}
.chip-row{display:flex;flex-wrap:wrap;gap:7px;animation:fadeUp .5s .2s ease both}
.rel-chip{border:1px solid var(--line-strong);border-radius:999px;padding:6px 12px;font-size:12px;font-weight:600;color:var(--ink);text-decoration:none;transition:.15s}
.rel-chip:hover{border-color:var(--amber);color:var(--amber-ink)}
details.faq{background:var(--surface);border:1.5px solid var(--line);border-radius:12px;padding:13px 15px;margin-bottom:8px}
details.faq summary{font-weight:700;font-size:14px;cursor:pointer}
details.faq p{margin-top:8px;font-size:13.5px;color:var(--ink-dim)}
footer{margin-top:30px;border-top:1px solid var(--line);padding-top:14px;font-size:12px;color:var(--ink-dim);text-align:center}
footer a{color:var(--ink-dim);margin:0 6px}
.label-bn{display:none}
body.lang-bn .label-en{display:none}
body.lang-bn .label-bn{display:inline}
.only-bn{display:none}
body.lang-bn .only-en{display:none}
body.lang-bn .only-bn{display:block}
body:not(.lang-bn) .hbn{display:none}"""

JS = """var MOON='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
var SUN='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>';
function updateThemeIcon(theme){var btn=document.getElementById('themeBtn');if(btn)btn.innerHTML=theme==='dark'?SUN:MOON;}
function toggleTheme(){var cur=document.documentElement.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');var next=cur==='dark'?'light':'dark';document.documentElement.setAttribute('data-theme',next);localStorage.setItem('bj-theme',next);updateThemeIcon(next);}
function setLang(l){document.body.className=l==='bn'?'lang-bn':'';localStorage.setItem('bj-lang',l);document.getElementById('langEN').classList.toggle('active',l==='en');document.getElementById('langBN').classList.toggle('active',l==='bn');}
(function(){var t=localStorage.getItem('bj-theme');if(t)document.documentElement.setAttribute('data-theme',t);updateThemeIcon(t||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));var l=localStorage.getItem('bj-lang');if(l&&l!=='en'){setLang(l);}})();"""

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
<style>@@CSS@@</style></head>
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
<div class="crumbs"><a href="../index.html"><span class="label-en">Home</span><span class="label-bn">হোম</span></a> › <a href="index.html"><span class="label-en">Bus Timetable</span><span class="label-bn">বাস টাইমটেবল</span></a> › <a href="@@DIRECT@@">@@O@@ → @@T@@</a> › <b>via @@V@@</b></div>
<div class="hero">
  <h1 class="routeline">
    <span class="rnode"><span class="rdot"></span>@@O@@</span><span class="rlink"></span>
    <span class="via-chip"><span class="label-en">VIA</span><span class="label-bn">ভায়া</span></span>
    <span class="rnode"><span class="rdot rdot-via"></span>@@V@@</span><span class="rlink"></span>
    <span class="rnode"><span class="rdot"></span>@@T@@</span>
  </h1>
  <div class="hbn hbn-sub">@@OBN@@ → @@TBN@@ — @@VBN@@ হয়ে</div>
  <div class="chips">
    <span class="schip">🚌 @@N@@ <span class="label-en">through buses</span><span class="label-bn">টি বাস @@VBN@@ হয়ে</span></span>
    <span class="schip">🕐 @@FIRST@@ – @@LAST@@</span>
    @@BCHIP@@
  </div>
</div>
<div class="sec"><h3><span class="label-en">@@O@@ → @@T@@ via @@V@@</span><span class="label-bn">@@OBN@@ → @@TBN@@ (@@VBN@@ হয়ে)</span></h3><span class="cnt">@@N@@ <span class="label-en">buses</span><span class="label-bn">বাস</span></span></div>
@@ROWS@@
<div class="sec"><h3><span class="label-en">Related</span><span class="label-bn">সম্পর্কিত</span></h3></div>
<div class="chip-row">@@CHIPS@@</div>
@@BOARD@@
<div class="note">📍 <span class="label-en"><b>Via page = buses that stop at @@V@@.</b> For the full @@O@@ → @@T@@ route, open the direct route page. Times can change — verify with the operator.</span><span class="label-bn"><b>ভায়া পেজ = @@VBN@@ থামা বাস।</b> পুরো @@OBN@@ → @@TBN@@ রুটের জন্য সরাসরি রুট পেজ খুলুন। সময় বদলাতে পারে।</span></div>
<div class="sec"><h3>FAQ</h3></div>
@@FAQ@@
<footer><a href="../about.html">About</a><a href="../contribute.html">Contribute</a><a href="../blog/">Blog</a><a href="../privacy-policy.html">Privacy</a></footer>
</div>
<script>@@JS@@</script>
</body></html>"""


def build_page(fname, O, T, V, through, board, chips_html, faq_en, faq_bn, first, last):
    n = len(through)
    m = len(board)
    direct_file = g.slug(O) + "-to-" + g.slug(T) + ".html"
    title = O + " to " + T + " via " + V + " Bus Time Table | BusJatri"
    desc = (str(n) + " buses from " + O + " to " + T + " stop at " + V +
            " — when each bus reaches " + V + ", plus buses you can board at " + V +
            " for " + T + ".")[:300]

    rows = []
    for i, item in enumerate(through):
        b = item[0]
        at = item[1]
        stops = b.get("total_stoppages") or len(stops_of(b))
        rows.append('<a class="bus-row" style="--i:' + str(i) + '" href="' + direct_file + '">' +
                    '<div class="dep">' + esc(fmt(b.get("departure_time"))) + "<small>" + esc(O) + "</small></div>" +
                    '<div class="bmid"><div class="op">' + esc(bus_name(b)) + "</div>" +
                    '<div class="subrow"><span class="atvia">⏱ ' + esc(V) + " " + esc(fmt(at)) + "</span>" +
                    "<span>" + esc(T) + " " + esc(fmt(b.get("arrival_time"))) + "</span>" +
                    "<span>" + str(stops) + ' <span class="label-en">stops</span><span class="label-bn">' + BN_STOPS + "</span></span></div></div>" +
                    badge_html(b) + "</a>")

    brows = []
    for i, b in enumerate(sorted(board, key=sort_key)):
        rf = g.slug(b.get("origin")) + "-to-" + g.slug(b.get("destination")) + ".html"
        if os.path.exists(os.path.join(OUT, rf)):
            open_tag = '<a class="bus-row" style="--i:' + str(i) + '" href="' + rf + '">'
            close = "</a>"
        else:
            open_tag = '<div class="bus-row" style="--i:' + str(i) + '">'
            close = "</div>"
        if (b.get("departure_time") or "").strip():
            sub = "<span>" + esc(b.get("origin")) + " → " + esc(T) + "</span>"
        else:
            sub = '<span class="label-en">Time not listed — check page</span><span class="label-bn">সময় নেই — পেজে দেখুন</span>'
        brows.append(open_tag +
                      '<div class="dep">' + esc(fmt(b.get("departure_time"))) + "<small>" + esc(b.get("origin")) + "</small></div>" +
                      '<div class="bmid"><div class="op">' + esc(bus_name(b)) + "</div>" +
                      '<div class="subrow">' + sub + "</div></div>" +
                      badge_html(b) + close)

    if brows:
        board_sec = ('<div class="board-sec" style="margin-top:20px">' +
                     '<div class="board-head"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 21s-8-6-8-11a8 8 0 0 1 16 0c0 5-8 11-8 11Z"/><circle cx="12" cy="10" r="3"/></svg>' +
                     '<h4><span class="label-en">Board at ' + esc(V) + " → " + esc(T) + '</span>' +
                     '<span class="label-bn">' + esc(bnplace(V)) + " থেকে উঠুন → " + esc(bnplace(T)) + "</span></h4></div>" +
                     '<div class="board-note"><span class="label-en">These buses start at ' + esc(V) + " and go to " + esc(T) + ".</span>" +
                     '<span class="label-bn">এই বাসগুলি ' + esc(bnplace(V)) + " থেকে ছাড়ে " + esc(bnplace(T)) + "-এ।</span></div>" +
                     "".join(brows) + "</div>")
    else:
        board_sec = ""

    faq_html = "".join('<details class="faq only-en"><summary>' + esc(q) + "</summary><p>" + esc(a) + "</p></details>" for q, a in faq_en)
    faq_html += "".join('<details class="faq only-bn"><summary>' + q + "</summary><p>" + a + "</p></details>" for q, a in faq_bn)

    if m:
        bchip = ('<span class="schip">🚏 ' + str(m) + ' <span class="label-en">buses from ' + esc(V) + "</span>" +
                 '<span class="label-bn">টি বাস ' + esc(bnplace(V)) + " থেকে</span></span>")
    else:
        bchip = ""

    schema = (g.faq_schema(faq_en) + chr(10) +
              g.breadcrumb_schema([("Home", "/"), ("Bus Timetable", "/bus-time-table/"),
                                   (O + " to " + T + " via " + V, "/bus-time-table/" + fname)]))

    page = PAGE_TMPL
    for token, value in [
        ("@@TITLE@@", esc(title)), ("@@DESC@@", esc(desc)), ("@@CANON@@", esc(BASE + "/bus-time-table/" + fname)),
        ("@@SCHEMA@@", schema), ("@@CSS@@", CSS), ("@@JS@@", JS),
        ("@@DIRECT@@", direct_file),
        ("@@O@@", esc(O)), ("@@T@@", esc(T)), ("@@V@@", esc(V)),
        ("@@OBN@@", esc(bnplace(O))), ("@@TBN@@", esc(bnplace(T))), ("@@VBN@@", esc(bnplace(V))),
        ("@@N@@", str(n)), ("@@FIRST@@", first), ("@@LAST@@", last), ("@@BCHIP@@", bchip),
        ("@@ROWS@@", "".join(rows)), ("@@CHIPS@@", chips_html), ("@@BOARD@@", board_sec), ("@@FAQ@@", faq_html),
    ]:
        page = page.replace(token, value)
    return page


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="report only, don't write")
    args = ap.parse_args()

    route_by_slug = {}
    for (o, t) in g.route_meta:
        route_by_slug.setdefault((g.slug(o), g.slug(t)), (o, t))

    files = sorted(f for f in os.listdir(OUT) if f.endswith(".html") and "-via-" in f and "-to-" in f)
    done = 0
    skipped = []
    for fname in files:
        parsed = parse_via_file(fname)
        if not parsed:
            skipped.append(fname)
            continue
        oslug, tslug, vslug = parsed
        # guard: places literally named "X Via Y" (e.g. Indus Via-Kolkata) —
        # those files are plain ROUTE pages, not via pages; leave untouched
        if (oslug + "-via-" + vslug, tslug) in route_by_slug:
            skipped.append(fname + " (route page: place name contains via)")
            continue
        if (oslug, tslug + "-via-" + vslug) in route_by_slug:
            skipped.append(fname + " (route page: place name contains via)")
            continue
        route = route_by_slug.get((oslug, tslug))
        if not route:
            skipped.append(fname)
            continue
        O, T = route
        buses = g.route_meta.get((O, T)) or []

        via_name = None
        through = []
        for b in buses:
            for s in stops_of(b):
                nm = (s.get("name") or "").strip()
                if nm and g.slug(nm) == vslug:
                    if not via_name:
                        via_name = nm
                    through.append((b, (s.get("up_time") or "").strip()))
                    break
        if not via_name:
            via_name = vslug.replace("-", " ").title()

        through.sort(key=lambda x: sort_key(x[0]))
        # board buses: start at the via stop (or a variant of it, e.g.
        # "Durgapur" buses on a "via Durgapur (City Center)" page) and go to
        # the destination. Only the safe direction: origin slug is the BASE
        # name of the via stop (durgapur -> durgapur-city-center), never the
        # other way (ondal is NOT onda).
        board = []
        for b in g.BUSES:
            osl = g.slug(b.get("origin"))
            if (osl == vslug or vslug.startswith(osl + "-")) and g.slug(b.get("destination")) == tslug:
                board.append(b)
        board.sort(key=sort_key)

        times = [b.get("departure_time") for b, at in through if (b.get("departure_time") or "").strip()]
        if times:
            def tk(x):
                pt = g.parse_time(x)
                return (0, pt) if pt else (1, "")
            first = min(times, key=tk)
            last = max(times, key=tk)
        else:
            first = "—"
            last = "—"

        direct_file = g.slug(O) + "-to-" + g.slug(T) + ".html"
        chips = ['<a class="rel-chip" href="' + direct_file + '">' + esc(O) + " → " + esc(T) + " (" + str(len(buses)) + ")</a>"]
        for other in files:
            if other == fname:
                continue
            p2 = parse_via_file(other)
            if p2 and p2[0] == oslug and p2[1] == tslug:
                chips.append('<a class="rel-chip" href="' + other + '">via ' + esc(p2[2].replace("-", " ").title()) + "</a>")
        if os.path.exists(os.path.join(OUT, "..", "via", vslug + ".html")):
            chips.append('<a class="rel-chip" href="../via/' + vslug + '.html"><span class="label-en">All buses at ' + esc(via_name) + '</span><span class="label-bn">' + esc(bnplace(via_name)) + " এর সব বাস</span></a>")

        dep_list = ", ".join(fmt(b.get("departure_time")) for b, at in through[:6])
        faq_en = [
            ("How many buses run from " + O + " to " + T + " via " + via_name + "?",
             str(len(through)) + " of the " + str(len(buses)) + " buses on the " + O + " to " + T +
             " route pass through " + via_name + ". Departure times from " + O + ": " + dep_list + "."),
            ("When do these buses reach " + via_name + "?",
             "Each bus row above shows the exact time the bus is at " + via_name + ". Timings can change — always verify with the operator before travelling."),
            ("I am at " + via_name + ". Can I board a bus to " + T + " directly?",
             ("Yes — " + str(len(board)) + " buses start from " + via_name + " and go to " + T +
              '. See the "Board at ' + via_name + '" section above.') if board else
             ("No bus from " + via_name + " to " + T + " is listed yet. You can take any through bus above — it stops at " + via_name + ".")),
            ("Do I have to change buses at " + via_name + "?",
             "No, these are through-buses. They pass through " + via_name + " on the way from " + O + " to " + T + "."),
            ("What is the difference between this page and the " + O + " to " + T + " route page?",
             "This page shows only the buses that stop at " + via_name + ", with their time at that stop. The direct route page shows all " + str(len(buses)) + " buses of the route end-to-end."),
        ]
        obn, tbn, vbn = bnplace(O), bnplace(T), bnplace(via_name)
        faq_bn = [
            ("📌 " + obn + " থেকে " + tbn + " কয়টি বাস " + vbn + " হয়ে যায়?",
             obn + " → " + tbn + " রুটের " + str(len(buses)) + "টি বাসের মধ্যে " + str(len(through)) + "টি " + vbn + " হয়ে যায়। ছাড়ে: " + dep_list + "।"),
            ("📌 বাসগুলি " + vbn + "-এ কখন পৌঁছায়?",
             "উপরের প্রতিটি বাসের সারিতে " + vbn + "-এ পৌঁছানোর সঠিক সময় দেওয়া আছে। সময় বদলাতে পারে — যাওয়ার আগে জেনে নিন।"),
            ("📌 আমি " + vbn + "-এ আছি। সোজা " + tbn + "-এর বাস পাব?",
             ("হ্যাঁ — " + str(len(board)) + "টি বাস " + vbn + " থেকে ছাড়ে " + tbn + "-এ। উপরের বোর্ড অংশ দেখুন।") if board else
             ("এখনও " + vbn + " থেকে " + tbn + " সরাসরি কোনো বাস তালিকাভুক্ত নেই। উপরের যেকোনো বাস " + vbn + "-এ থামে — সেটিই নিতে পারেন।")),
            ("📌 " + vbn + "-এ বাস বদলাতে হবে?",
             "না — এগুলি থ্রু বাস, " + obn + " থেকে " + tbn + " যাওয়ার পথে " + vbn + " হয়ে যায়।"),
            ("📌 এই পেজ আর রুট পেজের তফাত কী?",
             "এই পেজে শুধু " + vbn + "-এ থামা বাস আর তাদের ওই স্টপে সময় দেখানো হয়। সরাসরি রুট পেজে রুটের সব " + str(len(buses)) + "টি বাস থাকে।"),
        ]

        page = build_page(fname, O, T, via_name, through, board, "".join(chips), faq_en, faq_bn, first, last)

        if not args.dry:
            with open(os.path.join(OUT, fname), "w", encoding="utf-8") as fh:
                fh.write(page)
        done += 1
        if done <= 3 or args.dry:
            print(fname + ": " + str(len(through)) + " through, " + str(len(board)) + " board, " + str(len(page) // 1024) + "KB")

    print("regenerated " + str(done) + " via pages; skipped " + str(len(skipped)) + (": " + ", ".join(skipped) if skipped else ""))


if __name__ == "__main__":
    main()
