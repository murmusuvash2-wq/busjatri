#!/usr/bin/env python3
"""Daily BusJatri blog post: one data-driven route article per run.

Picks the busiest route that doesn't have a blog post yet and writes an
English article with the real timetable from data/busjatri_data.json.
No invented facts: every time/count/operator comes from the data.

Run with --write (from the daily-blog workflow or manually):
    python3 scripts/gen_daily_blog.py --write [--count N]

Also updates data/blog-manifest.json and re-runs gen_blog.py so the blog
index and sitemap pick the new post up immediately.
"""
import html
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://busjatri.in"
TODAY = date.today().isoformat()

# routes that already have a hand-written article (route page slugs)
ALREADY_BLOGGED = {
    "kolkata-to-digha",
    "purulia-to-manbazar",
    "jangalmahal",
    "how-to-find-bus-timings",
}

MANIFEST = ROOT / "data" / "blog-manifest.json"
BLOG = ROOT / "blog"

PLACE_ALIAS = {
    # merge spelling variants of the same place (must match gen_seo_pages.py)
    "Durgapur (Station)": "Durgapur Station",
}


def norm(name):
    t = re.sub(r"\s+", " ", str(name or "")).strip()
    return PLACE_ALIAS.get(t, t)


def slugify(v):
    return re.sub(r"[^a-z0-9]+", "-", str(v or "").lower()).strip("-")


def esc(v):
    return html.escape(str(v or ""), quote=True)


def to_min(t):
    m = re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM)?", str(t or "").strip(), re.I)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").upper()
    if mi > 59:
        return None
    if ap == "PM" and h < 12:
        h += 12
    if ap == "AM" and h == 12:
        h = 0
    if h > 23:
        return None
    return h * 60 + mi


def fmt(m):
    if m is None:
        return "—"
    h, mi = (m // 60) % 24, m % 60
    ap = "AM" if h < 12 else "PM"
    return f"{h % 12 or 12}:{mi:02d} {ap}"


def pick_routes(fwd, count):
    """Busiest routes with >=3 buses and >=2 timed departures, not yet blogged."""
    have = {p.stem for p in BLOG.glob("*.html")}
    ranked = []
    for (o, t), buses in fwd.items():
        s = f"{slugify(o)}-to-{slugify(t)}"
        r = f"{slugify(t)}-to-{slugify(o)}"
        if s in have or r in have or s in ALREADY_BLOGGED or r in ALREADY_BLOGGED:
            continue
        if not (ROOT / "bus-time-table" / (s + ".html")).exists():
            continue
        timed = [b for b in buses if to_min(b.get("departure_time")) is not None]
        if len(buses) < 3 or len(timed) < 2:
            continue
        ranked.append((len(buses), o, t, buses))
    ranked.sort(key=lambda x: -x[0])
    return ranked[:count]


def article(slug, o, t, buses):
    rows = sorted(buses, key=lambda b: to_min(b.get("departure_time")) or 9999)
    timed = [b for b in rows if to_min(b.get("departure_time")) is not None]
    first = fmt(min(to_min(b["departure_time"]) for b in timed))
    last = fmt(max(to_min(b["departure_time"]) for b in timed))
    n = len(rows)
    ops = Counter((b.get("operator") or "").strip() for b in rows if (b.get("operator") or "").strip() not in ("", "—"))
    op_list = ", ".join(f"{esc(k)} ({v})" for k, v in ops.most_common(5)) or "multiple private operators"

    stop_c = Counter()
    for b in buses:
        for st in (b.get("stoppages") or []):
            nm = norm(st.get("name"))
            if nm and nm not in (o, t):
                stop_c[nm] += 1
    major = [nm for nm, c in stop_c.most_common(12) if c >= 2][:10]

    tbl = ""
    for b in rows:
        dep = fmt(to_min(b.get("departure_time")))
        arr = fmt(to_min(b.get("arrival_time")))
        name = esc((b.get("bus_name") or "Bus service").strip())
        op = esc((b.get("operator") or "").strip())
        bt = (b.get("bus_type") or "").strip()
        badge = ""
        low = bt.lower()
        if "gov" in low or "sbstc" in low or "nbstc" in low or "wbtc" in low:
            badge = " · Govt"
        elif "ac" in low and "non" not in low:
            badge = " · AC"
        if op and op.lower() != name.lower():
            name += f" ({op})"
        tbl += (
            f'<tr><td style="padding:9px 12px;border-bottom:1px solid var(--border)">{name}{esc(badge)}</td>'
            f'<td style="padding:9px 12px;border-bottom:1px solid var(--border);white-space:nowrap">{dep}</td>'
            f'<td style="padding:9px 12px;border-bottom:1px solid var(--border);white-space:nowrap">{arr}</td>'
            f'<td style="padding:9px 12px;border-bottom:1px solid var(--border);text-align:center">{len(b.get("stoppages") or []) or "—"}</td></tr>\n'
        )

    stops_html = "".join(f'<span class="via-chip">{esc(s)}</span>' for s in major)

    title = f"{o} to {t} Bus Time Table — Timings, Operators & Stops"
    desc = f"{o} to {t} bus time table: {n} buses, first departure {first}, last {last}. Timings, operators and stoppages on BusJatri."
    excerpt = f"{o} to {t} bus timetable: {n} buses daily, first {first}, last {last}, run by {len(ops) or 'multiple'} operators."

    faqs = [
        (f"What is the first bus from {o} to {t}?", f"The first listed departure from {o} is at {first}."),
        (f"What is the last bus from {o} to {t}?", f"The last listed departure from {o} is at {last}."),
        (f"How many buses run from {o} to {t}?", f"{n} bus services are listed on this route on BusJatri."),
    ]
    faq_schema = json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
                             "mainEntity": [{"@type": "Question", "name": q,
                                             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]})
    crumb_schema = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList",
                               "itemListElement": [
                                   {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                                   {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{BASE}/blog/"},
                                   {"@type": "ListItem", "position": 3, "name": f"{o} to {t}", "item": f"{BASE}/blog/{slug}.html"}]})

    rev_slug = f"{slugify(t)}-to-{slugify(o)}.html"
    rel = f'<a class="rel-chip" href="../bus-time-table/{slug}.html">🚌 {esc(o)} → {esc(t)} route page</a>'
    if (ROOT / "bus-time-table" / rev_slug).exists():
        rel += f'<a class="rel-chip" href="../bus-time-table/{rev_slug}">↩ {esc(t)} → {esc(o)} (return)</a>'
    if (ROOT / "bus-time-table" / f"buses-from-{slugify(o)}.html").exists():
        rel += f'<a class="rel-chip" href="../bus-time-table/buses-from-{slugify(o)}.html">All buses from {esc(o)}</a>'

    body = f"""<p>Travelling from <strong>{esc(o)} to {esc(t)}</strong> by bus? This guide lists every bus service BusJatri has on record for this route — <strong>{n} buses</strong> in total, with the first departure at <strong>{first}</strong> and the last at <strong>{last}</strong>. Services are run by {op_list}.</p>
<h2>{esc(o)} → {esc(t)} Bus Timings</h2>
<p>Below is the full timetable as listed on BusJatri. Times can shift with season, traffic and day of the week — always confirm at the bus stand before you travel.</p>
<div style="overflow-x:auto;border:1px solid var(--border);border-radius:12px"><table style="width:100%;border-collapse:collapse;font-size:14px"><thead><tr style="background:var(--panel);font-weight:600;font-size:12px;text-transform:uppercase"><th style="padding:9px 12px;text-align:left">Bus</th><th style="padding:9px 12px;text-align:left">Departure</th><th style="padding:9px 12px;text-align:left">Arrival</th><th style="padding:9px 12px;text-align:center">Stops</th></tr></thead>
<tbody>{tbl}</tbody></table></div>
<h2>Quick Facts</h2>
<ul>
<li><strong>Buses listed:</strong> {n}</li>
<li><strong>First bus:</strong> {first}</li>
<li><strong>Last bus:</strong> {last}</li>
<li><strong>Major stops en route:</strong> {(", ".join(esc(s) for s in major)) if major else "see the route page for the full stop list"}</li>
</ul>
{f'<h2>Major Stops on the Way</h2><div class="chip-row">{stops_html}</div>' if stops_html else ''}
<h2>FAQ</h2>
<p><strong>What is the first bus from {esc(o)} to {esc(t)}?</strong><br>The first listed departure is at {first}.</p>
<p><strong>What is the last bus from {esc(o)} to {esc(t)}?</strong><br>The last listed departure is at {last}.</p>
<p><strong>How many buses run from {esc(o)} to {esc(t)}?</strong><br>{n} bus services are listed on this route.</p>
<p><em>Schedule data refreshed {TODAY}. Timings can change; confirm with the operator or at the bus stand before travel.</em></p>"""

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} | BusJatri</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}/blog/{slug}.html">
<meta property="og:title" content="{esc(title)} | BusJatri">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{BASE}/blog/{slug}.html">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="stylesheet" href="../css/seo.css">
<link rel="stylesheet" href="../css/extras.css">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-L4E3D1YX9X"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-L4E3D1YX9X');</script>
<script type="application/ld+json">{faq_schema}</script>
<script type="application/ld+json">{crumb_schema}</script>
</head>
<body>
<header class="header">
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
      <a href="../via/" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Stops</a>
    </nav>
  </div>
</header>
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">Blog</a> › <span>{esc(o)} to {esc(t)}</span></div>
<article>
<h1 style="font-size:1.5rem;line-height:1.35;margin:14px 0 4px">{esc(title)}</h1>
<div class="article-meta">{TODAY} · BusJatri Team</div>
<div class="article-body" style="line-height:1.85">
{body}
</div>
</article>
<section class="seo-section" style="margin-top:26px">
  <h3 class="section-title">Related Pages</h3>
  <div class="chip-row">{rel}</div>
</section>
<section class="seo-section">
  <a class="rel-chip" href="./">📚 All Posts</a>
</section>
</main>
<footer class="footer">
  <div class="container">
    <div style="display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;justify-content:center;font-size:13px">
      <a href="../blog/">Blog</a>
      <a href="../about.html">About Us</a>
      <a href="../contact.html">Contact Us</a>
      <a href="../privacy-policy.html">Privacy Policy</a>
    </div>
    <p style="margin:14px 0 0;text-align:center">BusJatri — West Bengal Bus Timetable</p>
    <p style="margin:6px 0 0;text-align:center">Contact: busjatri@zohomail.in</p>
  </div>
</footer>
</body>
</html>"""

    return page, {"slug": slug, "title": title, "date": TODAY, "excerpt": excerpt}


def main():
    count = 1
    if "--count" in sys.argv:
        count = int(sys.argv[sys.argv.index("--count") + 1])
    write = "--write" in sys.argv

    data = json.loads((ROOT / "data" / "busjatri_data.json").read_text(encoding="utf-8"))
    fwd = defaultdict(list)
    for b in data["buses"]:
        o, t = norm(b.get("origin")), norm(b.get("destination"))
        if o and t and o != t and o != "—" and t != "—":
            fwd[(o, t)].append(b)

    picks = pick_routes(fwd, count)
    if not picks:
        print("daily blog: no eligible routes left")
        return

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else []
    have = {m["slug"] for m in manifest}

    for n, o, t, buses in picks:
        slug = f"{slugify(o)}-to-{slugify(t)}"
        if slug in have:
            continue
        page, meta = article(slug, o, t, buses)
        print(f"daily blog: {slug} ({n} buses, {o} → {t})")
        if write:
            (BLOG / f"{slug}.html").write_text(page, encoding="utf-8")
            manifest.append(meta)

    if write:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        # regenerate blog index + sitemap entries (includes manifest posts)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_blog.py"), "--write"], check=True)
        print(f"daily blog: wrote {len(picks)} post(s), manifest now {len(manifest)}")


if __name__ == "__main__":
    main()
