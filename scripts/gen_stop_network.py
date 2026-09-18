#!/usr/bin/env python3
"""BusJatri stop network ("jal") generator.

Builds the interconnected web between stoppages and routes:

1. via/<stop>.html hub pages - "Buses via <Stop>": a departure board of every
   bus that passes through the stop (time at stop + where it is headed),
   linking to the route pages. Generated for stops served by >= MIN_BUSES
   distinct buses.
2. via/index.html - A-Z directory of all stop hubs.
3. Route pages: plain-text via-chips become links to the stop hub pages.
4. sitemap.xml: via/ URLs appended (idempotent - previous via/ entries are
   replaced on each run).

Run after gen_seo_pages.py / finalize_pages.py (route pages must exist so
route links can be verified). Idempotent.
"""
import html
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_BUSES = 2
MAX_ROWS = 150
MAX_CHIPS = 80
TODAY = date.today().isoformat()
BASE = "https://busjatri.in"

GA4 = (
    "<!-- Google tag (gtag.js) - GA4 -->\n"
    '<script async src="https://www.googletagmanager.com/gtag/js?id=G-L4E3D1YX9X"></script>\n'
    "<script>\n"
    "  window.dataLayer = window.dataLayer || [];\n"
    "  function gtag(){dataLayer.push(arguments);}\n"
    "  gtag('js', new Date());\n"
    "  gtag('config', 'G-L4E3D1YX9X');\n"
    "</script>\n"
)

THEME_JS = (
    "<script>(function(){try{var b=document.getElementById(\"bjThemeBtn\");if(!b)return;"
    "if(localStorage.getItem(\"seo-theme\")===\"dark\"){document.body.classList.add(\"dark\");"
    "b.textContent=\"\\u2600\";}"
    "b.addEventListener(\"click\",function(){var d=document.body.classList.toggle(\"dark\");"
    "localStorage.setItem(\"seo-theme\",d?\"dark\":\"light\");b.textContent=d?\"\\u2600\":\"\\u25d0\";});"
    "}catch(e){}})();</script>"
)

TRUST = (
    '<div class="trust-note" role="note"><strong>Schedule data refreshed '
    + TODAY
    + '</strong> · Listed schedules can change; confirm with the operator before travel.</div>'
)

POLISH_CSS = (
    '<style id="busjatri-ux-polish">\n'
    ".trust-note{margin:12px 0;padding:10px 14px;border:1px solid color-mix(in srgb,var(--accent,#b8791f) 35%,transparent);"
    "border-radius:12px;background:color-mix(in srgb,var(--accent,#b8791f) 8%,transparent);"
    "color:var(--ink-dim,#665);font-size:.82rem;line-height:1.5}.trust-note strong{color:var(--ink,#222)}\n"
    "a.bus-row,a.bus-row:visited{color:inherit;text-decoration:none}\n"
    "@media(max-width:759px){.bus-row .dep{font-variant-numeric:tabular-nums;white-space:nowrap}}\n"
    "</style>"
)

HEADER = """<header class="header">
  <div class="container header-inner">
    <a href="../index.html" class="logo" style="text-decoration:none;color:inherit">
      <svg class="icon" viewBox="0 0 24 24" style="width:1.35rem;height:1.35rem;color:var(--amber)" aria-hidden="true">
        <path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/>
      </svg>
      Bus<span>Jatri</span>
    </a>
    <nav style="display:flex;gap:10px;align-items:center;font-size:13px">
      <a href="../index.html" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Home</a>
      <a href="../bus-time-table/" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Routes</a>
      <a href="./" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Stops</a>
    <button id="bjThemeBtn" aria-label="Toggle dark mode" style="background:var(--surface,#fffcf4);border:1px solid var(--line,#ccc);border-radius:999px;padding:6px 12px;cursor:pointer;font-weight:600;color:var(--ink-dim,#665);font-size:13px;font-family:inherit;line-height:1.2">◔</button>
</nav>
  </div>
</header>"""

FOOTER = """<footer class="footer">
  <div class="container">
    <div style="display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;justify-content:center;font-size:13px">
      <a href="../about.html">About Us</a>
      <a href="../contact.html">Contact Us</a>
      <a href="../privacy-policy.html">Privacy Policy</a>
      <a href="../about.html#credits">Credits</a>
    </div>
    <p style="margin:14px 0 0;text-align:center">BusJatri — West Bengal Bus Timetable</p>
    <p style="margin:6px 0 0;text-align:center">Not affiliated with any transport corporation</p>
    <p style="margin:6px 0 0;text-align:center">Contact: busjatri@zohomail.in</p>
  </div>
</footer>"""


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def esc(value):
    return html.escape(str(value or ""), quote=True)


TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm|A\.M\.|P\.M\.)?")


def to_min(t):
    """Parse a display time to minutes-since-midnight; None if unparseable."""
    if not t:
        return None
    m = TIME_RE.search(str(t))
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").replace(".", "").upper()
    if ap == "AM":
        h = 0 if h == 12 else h
    elif ap == "PM":
        h = 12 if h == 12 else h + 12
    elif h > 23:
        return None
    return h * 60 + mi


def badge_for(bus):
    bt = (bus.get("bus_type") or "").lower()
    if "gov" in bt or "sbstc" in bt or "nbstc" in bt or "wbtc" in bt:
        return '<span class="badge badge-govt">Govt</span>'
    if "ac" in bt and "non" not in bt:
        return '<span class="badge badge-ac">AC</span>'
    return '<span class="badge badge-priv">Private</span>'


def fmt_min(m):
    if m is None:
        return "—"
    h, mi = divmod(m, 60)
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{mi:02d} {ap}"


def build_index(buses):
    """slug(stop) -> {display Counter, rows: [ (min, time_str, towards, bus) ]}"""
    idx = defaultdict(lambda: {"display": Counter(), "rows": []})
    for b in buses:
        stops = b.get("stoppages") or []
        if not stops:
            # origin/destination only bus: still index both ends
            stops = [{"name": b.get("origin"), "up_time": b.get("departure_time")},
                     {"name": b.get("destination"), "down_time": b.get("arrival_time")}]
        for s in stops:
            name = (s.get("name") or "").strip()
            if not name or name in {"—", "-"}:
                continue
            key = slug(name)
            if not key:
                continue
            e = idx[key]
            e["display"][name] += 1
            if s.get("up_time") or s.get("down_time"):
                if s.get("up_time"):
                    e["rows"].append((to_min(s["up_time"]), s["up_time"], b.get("destination"), b))
                if s.get("down_time"):
                    e["rows"].append((to_min(s["down_time"]), s["down_time"], b.get("origin"), b))
            else:
                e["rows"].append((None, "—", b.get("destination"), b))
    return idx


def route_href(o, d, route_pages):
    fn = f"{slug(o)}-to-{slug(d)}.html"
    if fn in route_pages:
        return f"../bus-time-table/{fn}"
    return None


def row_html(row, route_pages):
    m, t, towards, b = row
    href = route_href(b.get("origin"), b.get("destination"), route_pages) or (
        "../index.html#/bus/" + str(b.get("id") or "")
    )
    n_stops = len(b.get("stoppages") or []) or b.get("total_stoppages") or 0
    op = esc(b.get("bus_name") or b.get("operator") or "Bus")
    if b.get("operator") and b.get("operator") not in {"—", ""} and (b.get("bus_name") or "").lower() != (b.get("operator") or "").lower():
        op += " · " + esc(b.get("operator"))
    return (
        f'<a class="bus-row" href="{href}">\n'
        f'  <div class="dep">{esc(t)}<small>→ {esc(towards)}</small></div>\n'
        f'  <div class="bmid">\n'
        f'    <div class="op">{op}</div>\n'
        f'    <div class="mrow"><span>{esc(b.get("origin"))} → {esc(b.get("destination"))}</span>'
        f"<span>{n_stops} stops</span></div>\n"
        "  </div>\n"
        f"  {badge_for(b)}\n"
        "</a>"
    )


def faq_block(stop, n_buses, first, last, dests, night):
    qs = [
        (f"How many buses pass through {stop}?",
         f"{n_buses} bus services stop at {stop}. Check the departure board above for timings at this stop."),
        (f"What is the first bus from {stop}?",
         (f"The earliest listed service at {stop} is {first[1]} ({first[3].get('bus_name')}) towards {first[2]}."
          if first else "Timings at this stop are still being collected.")),
        (f"What is the last bus from {stop}?",
         (f"The last listed service at {stop} is {last[1]} ({last[3].get('bus_name')}) towards {last[2]}."
          if last else "Timings at this stop are still being collected.")),
        (f"Which places can I reach from {stop} by bus?",
         ("Direct buses from this stop head to " + ", ".join(dests) + "." if dests
          else "Check the departure board above for destinations served from this stop.")),
        (f"Is there a night bus at {stop}?",
         (f"Yes — services are listed at {stop} between 10 PM and 5 AM." if night
          else f"No night service is currently listed at {stop} in the 10 PM – 5 AM window.")),
    ]
    ld = json.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q,
                         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qs]},
        ensure_ascii=False,
    )
    items = "".join(
        f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in qs
    )
    visible = f'<div class="bj-faq"><h2>FAQs — buses via {esc(stop)}</h2>{items}</div>'
    return visible, ld


def stop_page(stop, e, route_pages):
    rows = [r for r in e["rows"] if r[0] is not None] + [r for r in e["rows"] if r[0] is None]
    rows.sort(key=lambda r: (r[0] if r[0] is not None else 9999, str(r[3].get("bus_name") or "")))
    n_buses = len({id(r[3]) for r in e["rows"]})
    times = [r[0] for r in e["rows"] if r[0] is not None]
    first = min(e["rows"], key=lambda r: r[0] or 9999) if times else None
    last = max((r for r in e["rows"] if r[0] is not None), key=lambda r: r[0], default=None)
    night = any(r[0] is not None and (r[0] >= 22 * 60 or r[0] < 5 * 60) for r in e["rows"])
    dests = Counter()
    for r in e["rows"]:
        if r[2]:
            dests[r[2]] += 1
    top_dests = [d for d, _ in dests.most_common(8)]

    shown = rows[:MAX_ROWS]
    more = len(rows) - len(shown)
    board = "".join(row_html(r, route_pages) for r in shown)
    more_note = f'<p style="font-size:13px;color:var(--ink-dim);margin:8px 2px">Showing first {MAX_ROWS} of {len(rows)} departures.</p>' if more > 0 else ""

    routes = Counter()
    for r in e["rows"]:
        b = r[3]
        routes[(b.get("origin"), b.get("destination"))] += 1
    chips = []
    for (o, d), c in sorted(routes.items(), key=lambda x: -x[1])[:MAX_CHIPS]:
        href = route_href(o, d, route_pages)
        label = f"{esc(o)} → {esc(d)} ({c})" if c > 1 else f"{esc(o)} → {esc(d)}"
        if href:
            chips.append(f'<a class="rel-chip" href="{href}">{label}</a>')
        else:
            chips.append(f'<span class="rel-chip">{label}</span>')

    faq_visible, faq_ld = faq_block(stop, n_buses, first, last, top_dests, night)

    title = f"Buses via {stop} — Timings at {stop} | BusJatri"
    desc = (f"All buses passing through {stop} — {n_buses} bus services with timings at {stop}, "
            f"routes and destinations across West Bengal. Bus timetable on BusJatri.")
    s = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}/via/{slug(stop)}.html">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}/via/{slug(stop)}.html">
<meta property="og:image" content="{BASE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="stylesheet" href="../css/seo.css">
<link rel="stylesheet" href="../css/extras.css">
{GA4}<style>.bj-faq{{margin:26px 0 6px}}.bj-faq h2{{font-size:1.12rem;margin:0 0 10px}}.bj-faq details{{border:1px solid var(--line,#e5dcc7);border-radius:12px;padding:10px 14px;margin:8px 0;background:var(--surface,#fffcf4)}}.bj-faq summary{{cursor:pointer;font-weight:600;font-size:.92rem}}.bj-faq p{{margin:8px 0 0;font-size:.88rem;color:var(--ink-dim,#665)}}</style>
{POLISH_CSS}
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
    {{"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"}},
    {{"@type": "ListItem", "position": 2, "name": "Stops", "item": BASE + "/via/"}},
    {{"@type": "ListItem", "position": 3, "name": stop}}
]})}</script>
<script type="application/ld+json">{faq_ld}</script>
</head>
<body>
{HEADER}
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">Stops</a> › <span>Buses via {esc(stop)}</span></div>
<div class="seo-hero">
  <h1>Buses via <span class="arr">→</span> {esc(stop)}</h1>
  <p class="bn-sub">{esc(stop)} স্টপেজ হয়ে যাওয়া সব বাসের সময়সূচী</p>
  {TRUST}<div class="stat-chips">
    <span class="schip">🚘 {n_buses} buses</span>
    <span class="schip hot">⏰ First {esc(first[1]) if first else '—'}</span>
    <span class="schip">⏰ Last {esc(last[1]) if last else '—'}</span>
    <span class="schip">📍 {len(dests)} destinations</span>
  </div>
</div>
<section class="seo-section">
  <h3 class="section-title">Departures at {esc(stop)}</h3>
  {board}
  {more_note}
</section>
<section class="seo-section">
  <h3 class="section-title">Routes via {esc(stop)}</h3>
  <div class="chip-row">{''.join(chips)}</div>
</section>
<section class="seo-section">
  <a class="rel-chip" href="./">📚 Browse all stops A–Z</a>
</section>
{faq_visible}
</main>
{FOOTER}
{THEME_JS}
</body>
</html>
"""
    return s


def index_page(entries):
    letters = defaultdict(list)
    for stop, key in sorted(entries):
        letters[stop[0].upper()].append((stop, key))
    nav = "".join(
        f'<a href="#{L}" style="font-weight:700;color:var(--amber);text-decoration:none;padding:2px 7px">{L}</a>'
        for L in sorted(letters)
    )
    sections = []
    for L in sorted(letters):
        chips = "".join(
            f'<a class="rel-chip" href="{key}.html">{esc(stop)}</a>' for stop, key in letters[L]
        )
        sections.append(
            f'<section class="seo-section" id="{L}"><h3 class="section-title">{L}</h3>'
            f'<div class="chip-row">{chips}</div></section>'
        )
    title = "All Bus Stops A–Z in West Bengal | BusJatri"
    desc = "Browse every bus stop on BusJatri — see all buses and timings passing through each stop across West Bengal."
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}/via/">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="stylesheet" href="../css/seo.css">
<link rel="stylesheet" href="../css/extras.css">
{GA4}{POLISH_CSS}
</head>
<body>
{HEADER}
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
<div class="crumbs"><a href="../index.html">Home</a> › <span>Stops A–Z</span></div>
<div class="seo-hero">
  <h1>All Bus Stops <span class="arr">A–Z</span></h1>
  <p class="bn-sub">সব স্টপেজ — প্রতিটি স্টপ থেকে বাসের সময়সূচী</p>
  {TRUST}<div class="stat-chips">
    <span class="schip">📍 {len(entries)} stops</span>
    <span class="schip hot">🚘 {sum(1 for _ in entries)} hub pages</span>
  </div>
</div>
<section class="seo-section" style="text-align:center;letter-spacing:1px">{nav}</section>
{''.join(sections)}
</main>
{FOOTER}
{THEME_JS}
</body>
</html>
"""


CHIP_RE = re.compile(r'<span class="via-chip"([^>]*)>([^<]+)</span>')


def main():
    data = json.loads((ROOT / "data" / "busjatri_data.json").read_text(encoding="utf-8"))
    buses = data["buses"]

    route_pages = {p.name for p in (ROOT / "bus-time-table").glob("*.html")}

    idx = build_index(buses)

    via_dir = ROOT / "via"
    via_dir.mkdir(exist_ok=True)

    # keep only stops with >= MIN_BUSES distinct buses
    entries = []
    for key, e in idx.items():
        if len({id(r[3]) for r in e["rows"]}) >= MIN_BUSES:
            stop = e["display"].most_common(1)[0][0]
            entries.append((stop, key))
    entries.sort()

    import sys
    dry = "--write" not in sys.argv
    written = 0
    if not dry:
        for stop, key in entries:
            page = stop_page(stop, idx[key], route_pages)
            (via_dir / f"{key}.html").write_text(page, encoding="utf-8")
            written += 1
        (via_dir / "index.html").write_text(index_page(entries), encoding="utf-8")
    print(f"stop hubs: {written} pages (of {len(idx)} indexed stops, >= {MIN_BUSES} buses)")

    # --- linkify via-chips on route pages ---
    key_by_stop = {}
    for stop, key in entries:
        key_by_stop[stop] = key
    # also allow variants of the display name to map to the same hub
    for key, e in idx.items():
        if key in {k for _, k in entries}:
            for name in e["display"]:
                key_by_stop.setdefault(name, key)

    linked = 0
    if not dry:
        for p in (ROOT / "bus-time-table").glob("*.html"):
            s = p.read_text(encoding="utf-8")
            if "<span class=\"via-chip\"" not in s:
                continue

            def repl(m):
                nonlocal linked
                attrs, name = m.group(1), m.group(2).strip()
                key = key_by_stop.get(name)
                if not key:
                    return m.group(0)
                linked += 1
                return (f'<a class="via-chip"{attrs} href="../via/{key}.html">{esc(name)}</a>')

            s2 = CHIP_RE.sub(repl, s)
            if s2 != s:
                p.write_text(s2, encoding="utf-8")
    print(f"via-chips linked on route pages: {linked}")

    # --- sitemap ---
    if not dry:
        sm = ROOT / "sitemap.xml"
        s = sm.read_text(encoding="utf-8")
        s = re.sub(r"<url><loc>" + re.escape(BASE) + r"/via/[^<]*</loc>.*?</url>\n?", "", s)
        add = "".join(
            f"<url><loc>{BASE}/via/{key}.html</loc><lastmod>{TODAY}</lastmod><priority>0.6</priority></url>\n"
            for _, key in entries
        )
        add += f"<url><loc>{BASE}/via/</loc><lastmod>{TODAY}</lastmod><priority>0.8</priority></url>\n"
        s = s.replace("</urlset>", add + "</urlset>")
        sm.write_text(s, encoding="utf-8")
        print(f"sitemap updated: +{len(entries)} via URLs")

    # --- bus-time-table index: link to stops directory (idempotent) ---
    if not dry:
        p = ROOT / "bus-time-table" / "index.html"
        s = p.read_text(encoding="utf-8")
        link = '<a href="../via/" style="display:inline-block;margin:6px 8px 6px 0;padding:8px 14px;border:1px solid var(--line,#e5dcc7);border-radius:999px;text-decoration:none;color:var(--amber);font-weight:600;font-size:13px">📍 Browse all stops A–Z</a>'
        if "Browse all stops A" not in s:
            m = re.search(r'<div class="stat-chips">', s)
            if m:
                s = s[: m.start()] + link + s[m.start():]
                p.write_text(s, encoding="utf-8")
                print("bus-time-table index: stops directory link added")


if __name__ == "__main__":
    main()
