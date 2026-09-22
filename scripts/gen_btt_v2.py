#!/usr/bin/env python3
"""
BTT index generator v2 — bus-time-table/index.html, "all bus timetables" hub.

Demo-approved design (2026-09-22, v4):
  1. Own page design — simple top bar (logo + dark mode), NOT the homepage
  2. Hero: "All Bus Timetables" + Bengali + chips (stands / routes / buses)
  3. Search box filtering stand cards
  4. BIG stand cards: name + Bengali + "N buses listed · M destinations"
     + "⏰ First – Last" (or "Timings on page" when times are unknown)
  5. 8 popular stands first (Kolkata, Digha, Durgapur, Siliguri, Asansol,
     Bankura, Burdwan, Purulia), rest A-Z; 8 visible, "See more" +8 per tap
  6. FAQ: 5 English + 5 Bengali
  7. NO 789-place route dump — route pages cover that

Same URL: bus-time-table/index.html (design change only).

Usage (run from repo root):
  python3 scripts/gen_btt_v2.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_route_v2 as v2
from gen_stand_v2 import stand_buses, destination_groups, discover_stands, display_name

g = v2.g

POPULAR = ["Kolkata", "Digha", "Durgapur", "Siliguri", "Asansol", "Bankura", "Burdwan", "Purulia"]

CSS = """:root{--amber:#b8791f;--amber2:#8a5a12;--bg:#fffcf4;--ink:#211c16;--mut:#7a6a4f;--line:#e8dfc8;--card:#fffdf8;--chipbg:#faf1dd}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}
body.dark{--bg:#17130c;--ink:#f3e8d2;--mut:#b8a480;--line:#3a3222;--card:#221c11;--chipbg:#33290f}
.wrap{max-width:760px;margin:0 auto;padding:14px 14px 60px}
header{display:flex;justify-content:space-between;align-items:center;padding:14px 2px}
.logo{font-size:22px;font-weight:900;text-decoration:none;color:inherit}.logo em{color:var(--amber);font-style:normal}
.pills{display:flex;gap:8px;align-items:center;font-size:12px;font-weight:700}
.pill{border:1.5px solid var(--line);border-radius:999px;padding:5px 12px;cursor:pointer}
.crumbs{font-size:12px;color:var(--mut);margin:6px 0 14px}.crumbs a{color:var(--mut)}
.hero{background:linear-gradient(135deg,var(--amber) 0%,var(--amber2) 100%);border-radius:18px;padding:26px 20px;color:#fff;margin-bottom:14px}
.hero h1{font-size:30px;letter-spacing:-.5px;line-height:1.15}
.hero .hbn{font-size:15px;opacity:.92;margin-top:4px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.schip{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:6px 13px;font-size:12.5px;font-weight:700}
.search{display:flex;gap:8px;margin:0 0 18px}
.search input{flex:1;border:1.5px solid var(--line);background:var(--card);color:var(--ink);border-radius:12px;padding:12px 14px;font-size:15px;font-weight:600;outline:none}
.sec{margin:22px 0 10px;display:flex;align-items:baseline;justify-content:space-between}
.sec h3{font-size:17px}.sec .bn{font-size:12px;color:var(--mut);margin-left:8px}
.sgrid{display:grid;grid-template-columns:1fr;gap:10px}
@media(min-width:560px){.sgrid{grid-template-columns:1fr 1fr}}
.scard{display:block;background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:14px;text-decoration:none;color:inherit;transition:transform .15s,border-color .15s}
.scard:hover{transform:translateY(-2px);border-color:var(--amber)}
.sname{font-size:16.5px;font-weight:800}.sbn{font-size:12.5px;color:var(--mut);font-weight:600;margin-left:6px}
.smeta{font-size:12px;color:var(--amber2);font-weight:700;margin-top:4px}
body.dark .smeta{color:var(--amber)}
.stime{font-size:12px;color:var(--mut);margin-top:4px}
.morebtn{display:block;width:100%;margin-top:12px;border:1.5px dashed var(--amber);background:transparent;color:var(--amber2);border-radius:12px;padding:11px;font-size:14px;font-weight:800;cursor:pointer}
body.dark .morebtn{color:var(--amber)}
details.faq{background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:13px 15px;margin-bottom:8px}
details.faq summary{font-weight:700;font-size:14px;cursor:pointer}
details.faq p{margin-top:8px;font-size:13.5px;color:var(--mut)}
.note{background:var(--chipbg);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:13px;color:var(--mut);margin:18px 0}
footer{margin-top:30px;border-top:1px solid var(--line);padding-top:14px;font-size:12px;color:var(--mut);text-align:center}
footer a{color:var(--mut);margin:0 6px}"""

JS = """var mstep=8;
function scards(){return Array.prototype.slice.call(document.querySelectorAll('#stands .scard'));}
function srefresh(){
  var cs=scards();var shown=cs.filter(function(c){return c.style.display!=='none';}).length;
  var b=document.getElementById('smore');
  if(shown>=cs.length){b.style.display='none';}else{b.style.display='';b.textContent='See more ('+(cs.length-shown)+' stands remaining)';}
  document.getElementById('scnt').textContent=shown+' of '+cs.length;
}
function showMore(){
  var cs=scards();var shown=cs.filter(function(c){return c.style.display!=='none';}).length;
  var nxt=Math.min(shown+mstep,cs.length);
  cs.forEach(function(c,i){c.style.display=i<nxt?'':'none';});
  srefresh();
}
sc=scards();sc.forEach(function(c,i){c.style.display=i<mstep?'':'none';});
srefresh();
function fil(){var q=document.getElementById('q').value.toLowerCase().trim();scards().forEach(function(c){c.style.display=!q||c.textContent.toLowerCase().indexOf(q)>-1?'':'none';});if(!q){srefresh();}else{var cs=scards();var shown=cs.filter(function(c){return c.style.display!=='none';}).length;document.getElementById('scnt').textContent=shown+' of '+cs.length;var b=document.getElementById('smore');b.style.display=shown>=cs.length?'none':'';}}"""


def stand_stats():
    """[(name, filename, n, dests, first, last)] for every existing stand page."""
    out = []
    for name, fname in discover_stands():
        buses = stand_buses(name)
        stats = g.route_stats(buses)
        dests = len(destination_groups(name, buses))
        out.append((name, fname, len(buses), dests, stats["first"], stats["last"]))
    return out


def _card(name, fname, n, dests, first, last):
    bn = v2.bnplace(name)
    bn_span = ' <span class="sbn">{}</span>'.format(g.esc(bn)) if bn and bn != name else ""
    if first is not None and last is not None:
        time_row = "⏰ First {} – Last {}".format(g.esc(g.format_time(first)), g.esc(g.format_time(last)))
    else:
        time_row = "⏰ Timings on page"
    return """<a class="scard" href="{href}">
  <div class="sname">{name}{bn}</div>
  <div class="smeta"><b>{n}</b> buses listed · {d} destinations</div>
  <div class="stime">{t}</div>
</a>""".format(href=g.esc(fname), name=g.esc(name), bn=bn_span, n=n, d=dests, t=time_row)


def generate_btt_page():
    stats = stand_stats()
    n_stands = len(stats)
    n_routes = len(g.route_meta)
    n_buses = len(g.BUSES)

    # popular first (by name), rest A-Z
    by_name = {}
    for row in stats:
        by_name.setdefault(row[0], row)
    popular = [by_name[n] for n in POPULAR if n in by_name]
    rest = sorted((r for r in stats if r[0] not in POPULAR), key=lambda r: r[0].lower())
    ordered = popular + rest
    cards = "".join(_card(*row) for row in ordered)

    title = "West Bengal Bus Time Table – All Routes | BusJatri"
    description = ("Complete West Bengal bus time table: {} routes from {} stands. "
                   "Find SBSTC, WBTC, NBSTC and private bus timings with departure times, "
                   "operators and stoppages.".format(n_routes, n_stands))[:300]
    canonical = "{}/bus-time-table/".format(g.BASE)

    chips = ('<span class="schip">🚏 {} bus stands</span>'.format(n_stands)
             + '<span class="schip">🛣 {:,} routes</span>'.format(n_routes)
             + '<span class="schip">🚌 {:,} buses</span>'.format(n_buses))

    # ---- FAQ (5 EN + 5 BN) ----
    top3 = sorted(stats, key=lambda r: -r[2])[:3]
    top3_txt = ", ".join("{} ({} listed)".format(r[0], r[2]) for r in top3)
    en = [
        ("Where can I find all West Bengal bus time tables?",
         "This page lists every major bus stand in West Bengal — {} stands covering {:,} route pages. Open your stand to see departures, popular routes and all destinations.".format(n_stands, n_routes)),
        ("How do I find a bus from my city or stand?",
         "Type your stand name in the search box above (e.g. 'Bankura' or 'Digha'), open its page and check Popular Routes — times, operators and route links are all there."),
        ("Which bus stands have the most buses listed?",
         "The busiest stands on BusJatri are {}. Every stand page shows the exact number of listed buses.".format(top3_txt)),
        ("Do you have SBSTC, NBSTC and WBTC government bus timings?",
         "Yes — government (SBSTC, NBSTC, WBTC) and private buses are listed together on every stand and route page, with departure times and stoppages."),
        ("Are these bus timings guaranteed?",
         "No — timetables change often. BusJatri lists what is published; always verify with the operator or depot before travelling, especially for early-morning and long routes."),
    ]
    bn = [
        ("সব বাসের সময়সূচী কোথায় পাব?",
         "এই পেজে পশ্চিমবঙ্গের প্রধান প্রতিটি বাস স্ট্যান্ড — {}টি স্ট্যান্ড, {:,}টি রুট পেজ — দেওয়া আছে। নিজের স্ট্যান্ড খুলে ছাড়ার সময় ও গন্তব্য দেখুন।".format(n_stands, n_routes)),
        ("আমার শহর বা স্ট্যান্ডের বাস কীভাবে খুঁজব?",
         "উপরের সার্চ বক্সে স্ট্যান্ডের নাম লিখুন (যেমন 'বাঁকুড়া'), পেজ খুলুন — জনপ্রিয় রুট, সময় ও অপারেটর সব সেখানেই।"),
        ("কোন কোন স্ট্যান্ডে সবচেয়ে বেশি বাস আছে?",
         "BusJatri-তে সবচেয়ে ব্যস্ত স্ট্যান্ডগুলি হল {}। প্রতিটি স্ট্যান্ড পেজে তালিকাভুক্ত বাসের সংখ্যা দেওয়া আছে।".format(top3_txt)),
        ("সরকারি SBSTC, NBSTC, WBTC বাসের সময় পাওয়া যায়?",
         "হ্যাঁ — সরকারি (SBSTC, NBSTC, WBTC) ও বেসরকারি বাস একসঙ্গে প্রতিটি স্ট্যান্ড ও রুট পেজে সময়সহ দেওয়া আছে।"),
        ("এই সময়সূচি কি নিশ্চিত?",
         "না — সময়সূচি প্রায়ই বদলায়। ভ্রমণের আগে অপারেটর বা ডিপোতে জেনে নিন, বিশেষ করে ভোরের ও দূরের রুটে।"),
    ]
    faq_html = "".join('<details class="faq"><summary>{}</summary><p>{}</p></details>'.format(g.esc(q), g.esc(a)) for q, a in en)
    faq_html += "".join('<details class="faq"><summary class="bn">📌 {}</summary><p>{}</p></details>'.format(q, a) for q, a in bn)

    note = ("📍 Every stand page shows buses <b>starting</b> from that stand. For buses that pass "
            "through a place, open the route page. More services may exist — ask at the stand.")

    body = """<div class="wrap">
<header><a class="logo" href="../index.html">Bus<em>Jatri</em></a>
<div class="pills"><span class="pill" onclick="document.body.classList.toggle('dark')">🌙 Dark</span></div></header>
<div class="crumbs"><a href="../index.html">Home</a> › <b>All Bus Timetables</b></div>
<div class="hero">
  <h1>All Bus Timetables</h1>
  <div class="hbn">সব বাসের সময়সূচী — বাস স্ট্যান্ড অনুযায়ী</div>
  <div class="chips">{chips}</div>
</div>
<div class="search"><input id="q" type="text" placeholder="🔎 Bus stand khojo — 'Bankura', 'Digha'…" oninput="fil()"></div>
<div class="sec"><h3>Bus Stands <span class="bn">বাস স্ট্যান্ড</span></h3><span style="font-size:12px;color:var(--mut)" id="scnt"></span></div>
<div class="sgrid" id="stands">{cards}</div>
<button class="morebtn" id="smore" onclick="showMore()"></button>
<div class="note">{note}</div>
<div class="sec"><h3>FAQ <span class="bn">প্রশ্নোত্তর</span></h3></div>
{faq}
<footer>{n} bus stands · {r:,} routes · {b:,} buses · <a href="../about.html">About</a><a href="../contribute.html">Contribute</a><a href="../blog/">Blog</a><a href="../privacy-policy.html">Privacy</a></footer>
</div>
<script>{js}</script>
</body></html>""".format(chips=chips, cards=cards, note=note, faq=faq_html,
                         n=n_stands, r=n_routes, b=n_buses, js=JS)

    head = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{ogimg}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
{schema}
<style>{css}</style></head>""".format(
        title=g.esc(title), desc=g.esc(description), canon=g.esc(canonical),
        ogimg=g.BASE + "/og-image.png", schema="{schema}", css=CSS)

    schema = (g.faq_schema(en + bn) + "\n"
              + g.breadcrumb_schema([
                  ("Home", "/"),
                  ("Bus Timetable", "/bus-time-table/"),
              ]))
    return head.replace("{schema}", schema) + body


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="report only, don't write")
    args = ap.parse_args()
    page = generate_btt_page()
    n_stands = page.count('class="scard"')
    print("btt index: {} stand cards, {} KB".format(n_stands, len(page) // 1024))
    if not args.dry:
        with open(os.path.join(g.OUT, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page)


if __name__ == "__main__":
    main()
