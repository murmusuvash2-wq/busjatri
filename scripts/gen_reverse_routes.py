#!/usr/bin/env python3
"""Generate reverse-direction route pages from return (down_time) data.

Many private buses run A->B in the morning and return B->A later, but only the
forward direction exists in busjatri_data.json as an origin/destination pair.
This script derives the return trip from the stoppages' down_time fields and
creates the missing <dest>-to-<origin>.html route pages, so both search
directions ("x to y bus" AND "y to x bus") have an exact-match page.

Only creates a page when:
  - the forward route has buses,
  - no buses exist for the reverse direction,
  - at least one bus has a usable down_time at the reverse origin stop.

Run AFTER gen_seo_pages.py (it rewrites the sitemap; we append). Idempotent.
"""
import html
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://busjatri.in"
TODAY = date.today().isoformat()

GA4 = (
    '<script async src="https://www.googletagmanager.com/gtag/js?id=G-L4E3D1YX9X"></script>\n'
    "<script>\n"
    "  window.dataLayer = window.dataLayer || [];\n"
    "  function gtag(){dataLayer.push(arguments);}\n"
    "  gtag('js', new Date());\n"
    "  gtag('config', 'G-L4E3D1YX9X');\n"
    "</script>\n"
)

TRUST = (
    '<div class="trust-note" role="note"><strong>Schedule data refreshed '
    + TODAY
    + '</strong> · Listed schedules can change; confirm with the operator before travel.</div>'
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
      <a href="./" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Routes</a>
      <a href="../via/" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Stops</a>
    </nav>
  </div>
</header>"""

FOOTER = """<footer class="footer">
  <div class="container">
    <div style="display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;justify-content:center;font-size:13px">
      <a href="../about.html">About Us</a>
      <a href="../contact.html">Contact Us</a>
      <a href="../privacy-policy.html">Privacy Policy</a>
      <a href="../blog/">ব্লগ</a>
    </div>
    <p style="margin:14px 0 0;text-align:center">BusJatri — West Bengal Bus Timetable</p>
    <p style="margin:6px 0 0;text-align:center">Contact: busjatri@zohomail.in</p>
  </div>
</footer>"""

TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm|A\.M\.|P\.M\.)?")


def to_min(t):
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


def slug(v):
    return re.sub(r"[^a-z0-9]+", "-", str(v or "").lower()).strip("-")


def esc(v):
    return html.escape(str(v or ""), quote=True)


def badge_for(bus):
    bt = (bus.get("bus_type") or "").lower()
    if "gov" in bt or "sbstc" in bt or "nbstc" in bt or "wbtc" in bt:
        return '<span class="badge badge-govt">Govt</span>'
    if "ac" in bt and "non" not in bt:
        return '<span class="badge badge-ac">AC</span>'
    return '<span class="badge badge-priv">Private</span>'


def stop_time(b, name, key):
    for s in b.get("stoppages") or []:
        if norm_stop(s.get("name")) == norm_stop(name) and s.get(key):
            return s[key]
    return None

PLACE_ALIAS = {
    # merge spelling variants of the same place (must match gen_seo_pages.py)
    "Durgapur (Station)": "Durgapur Station",
}

def norm_stop(name):
    t = (name or "").strip()
    return PLACE_ALIAS.get(t, t)


def main():
    data = json.loads((ROOT / "data" / "busjatri_data.json").read_text(encoding="utf-8"))
    buses = data["buses"]

    fwd = defaultdict(list)
    for b in buses:
        o, dd = norm_stop(b.get("origin")), norm_stop(b.get("destination"))
        if o and dd and o != dd and o not in {"—"} and dd not in {"—"}:
            fwd[(o, dd)].append(b)

    via_dir = ROOT / "via"

    pages = 0
    added_urls = []
    written = set()
    for (o, dd), bs in fwd.items():
        if (dd, o) in fwd:
            continue
        # reverse trip dd->o; need down_time at dd (departure of return)
        rows = []
        for b in bs:
            dep = stop_time(b, dd, "down_time")
            arr = stop_time(b, o, "down_time")
            if dep:
                rows.append((to_min(dep) if to_min(dep) is None else to_min(dep), dep, arr, b))
            else:
                # untimed return service: still list it with an honest dash
                rows.append((None, "—", arr, b))
        _timed = [r for r in rows if r[0] is not None]
        if not _timed:
            # no timed return info at all -> no page (all-dash page is useless)
            continue
        if not rows:
            continue
        rows.sort(key=lambda r: (r[0] if r[0] is not None else 9999, str(r[3].get("bus_name") or "")))

        chips = []
        seen = set()
        for b in bs:
            for s in (b.get("stoppages") or []):
                n = (s.get("name") or "").strip()
                if n and n not in {o, dd, ""} and n not in seen and s.get("down_time"):
                    seen.add(n)
                    k = slug(n)
                    if (via_dir / (k + ".html")).exists():
                        chips.append(f'<a class="via-chip" href="../via/{k}.html">{esc(n)}</a>')
                    else:
                        chips.append(f'<span class="via-chip">{esc(n)}</span>')
        chip_html = "".join(chips[:12])

        n_stops_total = len({id(r[3]) for r in rows})
        first_t = _timed[0][1] if _timed else "—"
        last_t = _timed[-1][1] if _timed else "—"

        board = ""
        for m, dep, arr, b in rows:
            href = f"./{slug(o)}-to-{slug(dd)}.html"
            op = esc(b.get("bus_name") or "Bus")
            if b.get("operator") and (b.get("operator") or "").strip() not in {"", "—"} and (b.get("bus_name") or "").lower() != (b.get("operator") or "").lower():
                op += " · " + esc(b.get("operator"))
            arr_html = f"<small>{esc(arr)} arr</small>" if arr and arr != "—" else ""
            board += (
                f'<a class="bus-row" href="{href}">\n'
                f'  <div class="dep">{esc(dep)}{arr_html}</div>\n'
                f'  <div class="bmid">\n'
                f'    <div class="op">{op}</div>\n'
                f'    <div class="mrow"><span>{esc(dd)} → {esc(o)}</span><span>return service</span></div>\n'
                f"  </div>\n"
                f"  {badge_for(b)}\n"
                "</a>"
            )

        title = f"{dd} to {o} Bus Time Table | BusJatri"
        desc = (f"{dd} to {o} bus time table — {n_stops_total} return services, first {first_t}, last {last_t}. "
                f"Timings and stoppages on BusJatri.")
        faq = [
            (f"What is the first bus from {dd} to {o}?", f"The first listed service departs {dd} at {first_t}."),
            (f"What is the last bus from {dd} to {o}?", f"The last listed service departs {dd} at {last_t}."),
            (f"How many buses run from {dd} to {o}?", f"{n_stops_total} return services are listed on this route."),
            (f"Which places does the {dd} to {o} bus pass through?", "The main stoppages are listed above."),
        ]
        ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
                         "mainEntity": [{"@type": "Question", "name": q,
                                         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
                        ensure_ascii=False)
        items = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faq)
        faq_visible = f'<div class="bj-faq"><h2>FAQs — {esc(dd)} to {esc(o)}</h2>{items}</div>'

        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}/bus-time-table/{slug(dd)}-to-{slug(o)}.html">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}/bus-time-table/{slug(dd)}-to-{slug(o)}.html">
<meta property="og:image" content="{BASE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="stylesheet" href="../css/seo.css">
<link rel="stylesheet" href="../css/extras.css">
{GA4}<style>.bj-faq{{margin:26px 0 6px}}.bj-faq h2{{font-size:1.12rem;margin:0 0 10px}}.bj-faq details{{border:1px solid var(--line,#e5dcc7);border-radius:12px;padding:10px 14px;margin:8px 0;background:var(--surface,#fffcf4)}}.bj-faq summary{{cursor:pointer;font-weight:600;font-size:.92rem}}.bj-faq p{{margin:8px 0 0;font-size:.88rem;color:var(--ink-dim,#665)}}a.bus-row,a.bus-row:visited{{color:inherit;text-decoration:none}}</style>
<script type="application/ld+json">{ld}</script>
</head>
<body>
{HEADER}
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">Bus Timetable</a> › <span>{esc(dd)} → {esc(o)}</span></div>
<div class="seo-hero">
  <h1>{esc(dd)} <span class="arr">→</span> {esc(o)}</h1>
  <p class="bn-sub">{esc(dd)} থেকে {esc(o)} বাসের সময়সূচী</p>
  {TRUST}<div class="stat-chips">
    <span class="schip">🚌 {n_stops_total} buses</span>
    <span class="schip hot">⏰ First {esc(first_t)}</span>
    <span class="schip">⏰ Last {esc(last_t)}</span>
  </div>
</div>
<section class="seo-section">
  <h3 class="section-title">Return Departures from {esc(dd)}</h3>
  {board}
  <p style="font-size:12.5px;color:var(--ink-dim,#665);margin:10px 2px">These are return timings of the {esc(o)} – {esc(dd)} services. Departure times can shift with season and traffic; confirm at the bus stand.</p>
</section>
<section class="seo-section">
  <h3 class="section-title">Via Stoppages</h3>
  <div class="chip-row">{chip_html}</div>
</section>
<section class="seo-section">
  <a class="rel-chip" href="{slug(o)}-to-{slug(dd)}.html">↩ {esc(o)} → {esc(dd)} (main service)</a>
</section>
{faq_visible}
</main>
{FOOTER}
</body>
</html>
"""
        if "--write" in sys.argv:
            out = ROOT / "bus-time-table" / f"{slug(dd)}-to-{slug(o)}.html"
            out.write_text(page, encoding="utf-8")
            written.add(out.name)
            added_urls.append(f"{BASE}/bus-time-table/{slug(dd)}-to-{slug(o)}.html")
        pages += 1

    print(f"reverse route pages: {pages}")

    # cleanup: delete stale reverse pages from earlier runs
    if "--write" in sys.argv:
        fwd_slug = {f"{slug(o)}-to-{slug(dd)}" for (o, dd) in fwd}
        rev_slug = {f"{slug(dd)}-to-{slug(o)}" for (o, dd) in fwd if (dd, o) not in fwd}
        removed = 0
        for p in (ROOT / "bus-time-table").glob("*-to-*.html"):
            if "-via-" in p.name:
                continue
            base = p.name[:-5]
            if base in rev_slug and p.name not in written:
                p.unlink()
                removed += 1
        if removed:
            print(f"reverse cleanup: removed {removed} stale pages")

    if "--write" in sys.argv and added_urls:
        sm = ROOT / "sitemap.xml"
        s = sm.read_text(encoding="utf-8")
        add = "".join(
            f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>0.6</priority></url>\n"
            for u in added_urls
            if f"<loc>{u}</loc>" not in s
        )
        s = s.replace("</urlset>", add + "</urlset>")
        sm.write_text(s, encoding="utf-8")
        print(f"sitemap: +{len([u for u in added_urls])} reverse urls")


if __name__ == "__main__":
    main()
