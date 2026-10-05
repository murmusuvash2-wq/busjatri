#!/usr/bin/env python3
"""Build crawlable CSTC Kolkata city-bus timetable pages.

Input: data/cstc_city_bus_timetable.json and assets/cstc-schedules/*.png
Output: 73 static route pages, a linked hub section, CSS and sitemap entries.
The source image is always retained alongside the visible HTML schedule.
"""
from __future__ import annotations
import html
import json
import re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cstc_city_bus_timetable.json"
ASSET_DIR = ROOT / "assets" / "cstc-schedules"
OUT_DIR = ROOT / "bus-time-table"
HUB = ROOT / "kolkata-city-bus-timetable.html"
CSS = ROOT / "css" / "cstc-city.css"
SITEMAP = ROOT / "sitemap.xml"
MARK = "<!-- cstc-timetable-v2 -->"
TODAY = date.today().isoformat()


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def slug(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return s or "route"


def split_direction(value: str) -> tuple[str, str]:
    parts = re.split(r"\s*(?:->|→|➝|–|—)\s*", value or "", maxsplit=1)
    return (parts[0].strip(), parts[1].strip()) if len(parts) == 2 else (value.strip(), "")


def mins(t: str):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", str(t or ""))
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def fmt12(t: str) -> str:
    m = mins(t)
    if m is None:
        return t or "—"
    h, minute = divmod(m, 60)
    suffix = "AM" if h < 12 else "PM"
    h = h % 12 or 12
    return f"{h}:{minute:02d} {suffix}"


def duration(dep: str, arr: str) -> str:
    a, b = mins(dep), mins(arr)
    if a is None or b is None or b < a:
        return ""
    d = b - a
    return f"{d // 60}h {d % 60:02d}m" if d >= 60 else f"{d}m"


def pair_rows(direction: dict) -> list[tuple[str, str]]:
    deps = direction.get("departures") or []
    arrs = direction.get("arrivals") or []
    return [(deps[i] if i < len(deps) else "", arrs[i] if i < len(arrs) else "")
            for i in range(max(len(deps), len(arrs)))]


def css_text() -> str:
    return r'''/* CSTC city timetable v2 — static, responsive and crawlable */
.cstc-panel{background:var(--surface,#fffcf4);border:1px solid var(--line,rgba(33,28,22,.13));border-radius:18px;padding:16px;margin:16px 0;box-shadow:var(--shadow-sm,0 2px 12px rgba(33,28,22,.1))}
.cstc-eyebrow{display:inline-flex;align-items:center;gap:6px;background:var(--govt-soft,rgba(53,96,138,.12));color:var(--govt,#35608a);border:1px solid color-mix(in srgb,var(--govt,#35608a) 35%,transparent);border-radius:999px;padding:5px 10px;font-family:var(--font-mono,monospace);font-size:10px;font-weight:800;letter-spacing:.04em;text-transform:uppercase}
.cstc-panel h2,.cstc-panel h3{font-family:var(--font-display,Georgia,serif);line-height:1.2}.cstc-panel h2{font-size:1.35rem;margin:10px 0 5px}.cstc-panel h3{font-size:1.05rem;margin:0}.cstc-muted{color:var(--ink-dim,#6f6653);font-size:.87rem;line-height:1.6}.cstc-note{padding:10px 12px;margin-top:12px;border-left:3px solid var(--amber,#b8791f);background:var(--amber-soft,rgba(184,121,31,.14));color:var(--ink-dim,#6f6653);font-size:.78rem;line-height:1.55}
.cstc-route-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:9px;margin-top:14px}.cstc-route-link{display:flex;align-items:center;justify-content:space-between;gap:10px;background:var(--surface-2,#efe6d3);border:1px solid var(--line,rgba(33,28,22,.13));border-radius:12px;padding:11px 12px;color:var(--ink,#211c16);transition:border-color .15s,transform .15s}.cstc-route-link:hover{border-color:var(--amber,#b8791f);transform:translateY(-1px)}.cstc-route-link strong{font-family:var(--font-mono,monospace);font-size:.82rem;color:var(--amber-ink,#6b4610)}.cstc-route-link span{font-size:.78rem;text-align:right;color:var(--ink-dim,#6f6653)}
.cstc-hero{background:linear-gradient(135deg,var(--surface,#fffcf4),var(--surface-2,#efe6d3));border:1px solid var(--line,rgba(33,28,22,.13));border-radius:20px;padding:18px;margin:16px 0}.cstc-hero h1{font-family:var(--font-display,Georgia,serif);font-size:clamp(1.55rem,5vw,2.25rem);line-height:1.15;margin:9px 0 7px}.cstc-hero .route-code{color:var(--amber,#b8791f);font-family:var(--font-mono,monospace)}.cstc-stats{display:flex;flex-wrap:wrap;gap:7px;margin-top:13px}.cstc-stat{display:inline-flex;gap:5px;align-items:center;background:var(--surface,#fffcf4);border:1px solid var(--line,rgba(33,28,22,.13));border-radius:999px;padding:6px 10px;font-size:.75rem;color:var(--ink-dim,#6f6653)}.cstc-stat strong{color:var(--ink,#211c16);font-family:var(--font-mono,monospace)}
.cstc-direction{margin:15px 0 0;padding:15px;background:var(--surface,#fffcf4);border:1px solid var(--line,rgba(33,28,22,.13));border-radius:16px}.cstc-direction-head{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:11px}.cstc-direction-title{font-weight:800;font-size:1rem}.cstc-direction-meta{font-size:.73rem;color:var(--ink-dim,#6f6653);margin-top:3px}.cstc-table-wrap{overflow-x:auto;border:1px solid var(--line,rgba(33,28,22,.13));border-radius:12px}.cstc-table{width:100%;border-collapse:collapse;font-family:var(--font-mono,monospace);font-size:.8rem;min-width:350px}.cstc-table th{background:var(--surface-2,#efe6d3);padding:8px 10px;text-align:left;font-size:.68rem;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-dim,#6f6653)}.cstc-table td{padding:7px 10px;border-top:1px solid var(--line,rgba(33,28,22,.13));font-variant-numeric:tabular-nums}.cstc-table td:first-child{color:var(--amber-ink,#6b4610);font-weight:800}.cstc-table td:nth-child(2){color:var(--govt,#35608a);font-weight:700}.cstc-table td:nth-child(3){color:var(--ink-dim,#6f6653);font-family:var(--font-body,system-ui);font-size:.75rem}.cstc-table .unmatched{color:var(--maroon,#a13b2e);font-style:italic}.cstc-source{display:grid;grid-template-columns:minmax(0,1fr) 220px;gap:14px;align-items:start;margin-top:16px}.cstc-source-copy{font-size:.8rem;color:var(--ink-dim,#6f6653);line-height:1.65}.cstc-source-copy strong{color:var(--ink,#211c16)}.cstc-source img{width:100%;height:auto;display:block;border:1px solid var(--line,rgba(33,28,22,.13));border-radius:12px;background:#fff;box-shadow:var(--shadow-sm,0 2px 12px rgba(33,28,22,.1))}.cstc-source figcaption{font-size:.68rem;color:var(--ink-dim,#6f6653);margin-top:5px;text-align:center}.cstc-breadcrumb{font-family:var(--font-mono,monospace);font-size:.7rem;color:var(--ink-dim,#6f6653);margin-top:14px}.cstc-breadcrumb a{color:var(--amber-ink,#6b4610)}.cstc-faq{margin-top:16px}.cstc-faq details{border:1px solid var(--line,rgba(33,28,22,.13));border-radius:10px;margin:8px 0;background:var(--surface,#fffcf4)}.cstc-faq summary{cursor:pointer;padding:11px 13px;font-weight:700;font-size:.86rem}.cstc-faq p{padding:0 13px 12px;color:var(--ink-dim,#6f6653);font-size:.8rem;line-height:1.6}.cstc-back{display:inline-flex;margin-top:14px;background:var(--amber,#b8791f);color:#fff9ee!important;border-radius:999px;padding:9px 14px;font-size:.78rem;font-weight:800}.cstc-verify{font-size:.7rem;color:var(--ink-dim,#6f6653);margin-top:8px}
@media(max-width:680px){.cstc-source{grid-template-columns:1fr}.cstc-source figure{max-width:280px;margin:auto}.cstc-direction-head{display:block}.cstc-direction-meta{margin-top:5px}}
body.dark .cstc-hero{background:linear-gradient(135deg,var(--surface,#201c2b),var(--surface-2,#2a2537))}
'''


def page_html(route: str, obj: dict, image_rel: str) -> str:
    dirs = obj.get("directions") or []
    first_from, first_to = split_direction(dirs[0].get("direction", "")) if dirs else (route, "Kolkata")
    title = f"{route} Kolkata City Bus Timetable | BusJatri"
    total = sum(len(x.get("departures") or []) for x in dirs)
    all_times = [t for x in dirs for t in x.get("departures") or []]
    first = fmt12(all_times[0]) if all_times else "—"
    last = fmt12(all_times[-1]) if all_times else "—"
    mismatch = any(len(x.get("departures") or []) != len(x.get("arrivals") or []) for x in dirs)
    desc = f"{route} CSTC/WBTC Kolkata city bus timetable with {total} scheduled departures, terminal arrival times, both directions and official schedule image."
    page_url = f"https://busjatri.in/bus-time-table/cstc-{slug(route)}"
    sections = []
    for direction in dirs:
        name = direction.get("direction", "")
        frm, to = split_direction(name)
        rows = pair_rows(direction)
        dep_count = len(direction.get("departures") or [])
        arr_count = len(direction.get("arrivals") or [])
        duration_values = [duration(a, b) for a, b in rows if a and b and duration(a, b)]
        duration_text = duration_values[0] if duration_values else ""
        tr = []
        for idx, (dep, arr) in enumerate(rows, 1):
            tr.append(f'<tr><td>{idx}</td><td>{esc(fmt12(dep) if dep else "—")}</td><td>{esc(fmt12(arr) if arr else "—")}</td><td>{esc(duration(dep, arr) or "—")}</td></tr>')
        warn = ''
        if dep_count != arr_count:
            warn = f'<p class="cstc-note">This direction has {dep_count} departure entries and {arr_count} arrival entries in the supplied schedule image. Unmatched values are shown as — and should be checked against the original notice.</p>'
        sections.append(f'''<section class="cstc-direction" aria-labelledby="dir-{slug(name)}">
  <div class="cstc-direction-head"><div><h2 class="cstc-direction-title" id="dir-{slug(name)}">{esc(frm)} <span aria-hidden="true">→</span> {esc(to)}</h2><p class="cstc-direction-meta">{dep_count} departures · first {esc(fmt12((direction.get("departures") or [""])[0]))} · last {esc(fmt12((direction.get("departures") or [""])[-1]))}{(' · typical terminal ride '+esc(duration_text)) if duration_text else ''}</p></div><span class="cstc-eyebrow">CSTC timetable</span></div>
  <div class="cstc-table-wrap"><table class="cstc-table"><caption class="sr-only">{esc(route)} {esc(name)} departure and arrival timetable</caption><thead><tr><th>#</th><th>Departure</th><th>Arrival</th><th>Ride</th></tr></thead><tbody>{''.join(tr)}</tbody></table></div>{warn}
</section>''')
    faq = f'''<section class="cstc-faq" aria-labelledby="faq-title"><h2 id="faq-title">{esc(route)} bus timetable FAQs</h2><details open><summary>What time does {esc(route)} bus start?</summary><p>The first listed departure for this route is {esc(first)}. The last listed departure in the supplied schedule is {esc(last)}.</p></details><details><summary>Does this page show both directions?</summary><p>Yes. This page lists the official CSTC schedule for both directions where both direction records are available.</p></details><details><summary>Are these timings official?</summary><p>The source supplied for this page is the CSTC/West Bengal Transport schedule image. Timings can change, so confirm before travelling.</p></details></section>'''
    jsonld = {
        "@context": "https://schema.org", "@type": "Dataset", "name": f"{route} CSTC Kolkata City Bus Timetable",
        "description": desc, "url": page_url, "isAccessibleForFree": True,
        "creator": {"@type": "Organization", "name": "BusJatri"},
        "distribution": {"@type": "DataDownload", "encodingFormat": "text/html", "contentUrl": page_url},
        "license": "https://busjatri.in/about"
    }
    faq_json = {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":f"What time does {route} bus start?","acceptedAnswer":{"@type":"Answer","text":f"The first listed departure is {first}."}},
        {"@type":"Question","name":"Does this page show both directions?","acceptedAnswer":{"@type":"Answer","text":"Yes, the official schedule directions available for this route are shown."}},
        {"@type":"Question","name":"Are these timings official?","acceptedAnswer":{"@type":"Answer","text":"The supplied source is the CSTC/West Bengal Transport schedule image. Verify before travelling."}}
    ]}
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{page_url}"><meta property="og:type" content="article"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{page_url}"><meta property="og:site_name" content="BusJatri"><meta property="og:image" content="https://busjatri.in/{image_rel}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="theme-color" content="#b8791f"><link rel="icon" href="../favicon.svg"><link rel="stylesheet" href="../css/seo.css?v=rt20260920"><link rel="stylesheet" href="../css/extras.css"><link rel="stylesheet" href="../css/cstc-city.css?v=cstc20261006"><script type="application/ld+json">{json.dumps(jsonld,ensure_ascii=False,separators=(',',':'))}</script><script type="application/ld+json">{json.dumps(faq_json,ensure_ascii=False,separators=(',',':'))}</script></head><body><header class="header"><div class="container header-inner"><a href="../" class="logo" aria-label="BusJatri home"><img class="brand-logo" src="/logo.png" alt="BusJatri" style="width:30px;height:30px;border-radius:50%">Bus<span>Jatri</span></a><div class="hdr-ctrl"><div class="lang-switch" role="group" aria-label="Language"><button type="button" id="langEn" class="pill pill-en on">EN</button><button type="button" id="langBn" class="pill pill-bn">বাংলা</button></div><button type="button" id="themeBtn" class="theme-btn" aria-label="Toggle dark mode">☾</button></div></div></header><main class="container seo-main"><div class="cstc-breadcrumb"><a href="../">Home</a> / <a href="../kolkata-city-bus-timetable">Kolkata City Bus Timetable</a> / Route {esc(route)}</div><section class="cstc-hero"><span class="cstc-eyebrow">Official CSTC schedule</span><h1><span class="route-code">{esc(route)}</span> Kolkata City Bus Timetable</h1><p class="cstc-muted">{esc(first_from)} → {esc(first_to)} and reverse direction departure and terminal arrival times.</p><div class="cstc-stats"><span class="cstc-stat">Departures <strong>{total}</strong></span><span class="cstc-stat">First <strong>{esc(first)}</strong></span><span class="cstc-stat">Last <strong>{esc(last)}</strong></span><span class="cstc-stat">Directions <strong>{len(dirs)}</strong></span></div></section>{''.join(sections)}<section class="cstc-panel"><div class="cstc-source"><div class="cstc-source-copy"><h2>Official schedule source</h2><p><strong>Source:</strong> West Bengal Transport Department / CSTC timetable image supplied for this route.</p><p class="cstc-verify">Schedule data imported on {TODAY}. Timings may change; confirm at the bus stand or with the operator before travel.</p><a class="cstc-back" href="../kolkata-city-bus-timetable">← All Kolkata city bus routes</a></div><figure><a href="../{image_rel}"><img src="../{image_rel}" loading="lazy" decoding="async" alt="Official CSTC {esc(route)} bus timetable schedule"></a><figcaption>View official {esc(route)} schedule image</figcaption></figure></div></section>{faq}</main><footer class="footer"><div class="container"><p><strong>BusJatri</strong> — West Bengal bus timetable<br>Not affiliated with any transport corporation</p></div></footer><script defer src="../js/hdr.js?v=hdrunify20261005d"></script><script defer src="../js/lang.js?v=lang20261005c"></script></body></html>'''


def hub_section(data: dict) -> str:
    cards = []
    for route in sorted(data, key=lambda x: (0 if x.isdigit() else 1, x)):
        obj = data[route]
        all_dep = [t for d in obj.get("directions", []) for t in d.get("departures", [])]
        href = f"bus-time-table/cstc-{slug(route)}.html"
        first, last = (fmt12(all_dep[0]), fmt12(all_dep[-1])) if all_dep else ("—", "—")
        cards.append(f'<a class="cstc-route-link" href="{href}"><strong>{esc(route)}</strong><span>{len(all_dep)} departures<br>{esc(first)} – {esc(last)}</span></a>')
    return f'''{MARK}<section class="cstc-panel" aria-labelledby="cstc-official-title"><span class="cstc-eyebrow">Official schedule data</span><h2 id="cstc-official-title">Kolkata CSTC city bus timetable</h2><p class="cstc-muted">Browse 73 route-wise official schedule pages with departure and terminal arrival times for both directions. Each page includes the original timetable image, a crawlable HTML table and route-specific SEO metadata.</p><div class="cstc-route-grid">{''.join(cards)}</div><p class="cstc-note">These schedules are based on the supplied CSTC/West Bengal Transport timetable images. Bus timings can change; verify before travel.</p></section>'''


def update_hub(data: dict):
    h = HUB.read_text(encoding="utf-8")
    if "css/cstc-city.css" not in h:
        h = h.replace("</head>", '<link rel="stylesheet" href="css/cstc-city.css?v=cstc20261006">\n</head>', 1)
    h = re.sub(r"<title>.*?</title>", "<title>Kolkata City Bus Timetable — 73 Official CSTC Routes, Times & Stops | BusJatri</title>", h, count=1, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="Kolkata city bus timetable with 73 official CSTC/WBTC route schedules, departures, terminal arrivals, stops and route images. Search BusJatri.">', h, count=1)
    h = re.sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="Kolkata City Bus Timetable — 73 Official CSTC Routes | BusJatri">', h, count=1)
    h = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="Browse 73 official CSTC/WBTC Kolkata city bus route schedules with departure and arrival times, stops and timetable images.">', h, count=1)
    if MARK in h:
        h = h[:h.index(MARK)] + hub_section(data) + h[h.index(MARK)+len(MARK):]
    else:
        h = h.replace("</main>", hub_section(data) + "\n</main>", 1)
    HUB.write_text(h, encoding="utf-8")


def update_sitemap(data: dict):
    if not SITEMAP.exists():
        return
    s = SITEMAP.read_text(encoding="utf-8")
    urls = [f"https://busjatri.in/bus-time-table/cstc-{slug(route)}" for route in data]
    for url in urls:
        if f">{url}<" not in s:
            s = s.replace("</urlset>", f"  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>\n</urlset>", 1)
    SITEMAP.write_text(s, encoding="utf-8")


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    CSS.parent.mkdir(parents=True, exist_ok=True)
    CSS.write_text(css_text(), encoding="utf-8")
    generated = 0
    for route, obj in data.items():
        image_rel = f"assets/cstc-schedules/{route}.png"
        path = OUT_DIR / f"cstc-{slug(route)}.html"
        path.write_text(page_html(route, obj, image_rel), encoding="utf-8")
        generated += 1
    update_hub(data)
    update_sitemap(data)
    print(f"generated route pages: {generated}")
    print(f"routes in source: {len(data)}")
    print(f"css: {CSS}")

if __name__ == "__main__":
    main()
