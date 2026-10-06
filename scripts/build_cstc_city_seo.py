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
    """Return the canonical Kolkata-only visual layer.

    Keeping the stylesheet external prevents generated route pages and the hub
    from drifting into separate design systems.
    """
    return CSS.read_text(encoding="utf-8") if CSS.exists() else ""


def stops_html(stops: list[str]) -> str:
    if not stops:
        return '<p class="cstc-stop-note">Detailed via/stoppage data is not available in the supplied route record.</p>'
    items = "".join(f'<li><span class="cstc-stop-dot" aria-hidden="true"></span><span>{esc(stop)}</span></li>' for stop in stops)
    return f'<div class="cstc-stops" aria-label="Route stoppages"><div class="cstc-stops-head"><strong>Via / stoppages</strong><span>{len(stops)} listed</span></div><ol>{items}</ol></div>'


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
  <div class="cstc-table-wrap"><table class="cstc-table"><caption class="sr-only">{esc(route)} {esc(name)} departure and arrival timetable</caption><thead><tr><th>#</th><th>Departure</th><th>Arrival</th><th>Ride</th></tr></thead><tbody>{''.join(tr)}</tbody></table></div>{stops_html(direction.get("stoppages") or [])}{warn}
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
