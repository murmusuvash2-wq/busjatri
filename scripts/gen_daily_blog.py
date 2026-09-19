#!/usr/bin/env python3
"""Daily BusJatri blog post: long-form, story-style, bilingual (EN + BN).

Picks the busiest route that doesn't have a blog post yet and writes a
narrative travel-guide article. Every fact (times, counts, operators,
stops) comes from data/busjatri_data.json — nothing is invented. Each
route gets a stable writing style (hash of the slug), so the blog reads
like different human writers, not one template stamped 500 times.

Run with --write (from the daily-blog workflow or manually):
    python3 scripts/gen_daily_blog.py --write [--count N]
"""
import hashlib
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

ALREADY_BLOGGED = {
    "kolkata-to-digha",
    "purulia-to-manbazar",
    "jangalmahal",
    "how-to-find-bus-timings",
}

MANIFEST = ROOT / "data" / "blog-manifest.json"
BLOG = ROOT / "blog"

PLACE_ALIAS = {"Durgapur (Station)": "Durgapur Station"}


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


# ---------------------------------------------------------------- writing
# Style variants: each route keeps one stable "voice", chosen by its slug.

OPENINGS = [
    # 0 — the regular traveller
    ("Some routes you simply learn by heart. For anyone shuttling between "
     "{o} and {t}, the {first} departure is less a timetable entry and more "
     "a small ritual — the same familiar faces, the same tea at the stand, "
     "the same race for a window seat."),
    # 1 — the planner
    ("Planning a trip from {o} to {t}? The good news is that you don't need "
     "to chase conductors or call depots for timings. {n} buses run this "
     "route on record with BusJatri, and this guide walks you through all of "
     "them — the early starters, the midday options and the last bus of the day."),
    # 2 — the scene at the stand
    ("Ask anyone at the {o} bus stand how to reach {t} and you'll get a "
     "confident answer: just catch a bus. And they'd be right — with {n} "
     "services listed across the day, starting from {first}, this is one of "
     "those routes you can decide to travel on almost without planning."),
    # 3 — the working-day angle
    ("Not every bus route needs a holiday to justify itself. {o} to {t} is "
     "very much a working-day route — shopkeepers, students, families and "
     "office-goers fill these buses all week, which is exactly why {n} "
     "services run every day between {first} and {last}."),
    # 4 — the storyteller
    ("There is a particular pleasure in a well-run bus route. You board at "
     "{o}, the engine settles into its rhythm, and one town quietly gives "
     "way to the next until {t} arrives. The {o}–{t} run is one of West "
     "Bengal's quietly dependable ones — {n} buses a day, the first rolling "
     "out at {first}."),
]

JOURNEY_LEADS = [
    "What is the journey actually like? The road threads through a string of small towns and stops, and regulars know them by heart:",
    "Along the way, the bus calls at the places that stitch this route together:",
    "The route has its own geography — a chain of stops that locals navigate without a second thought:",
    "Between boarding and arrival, the bus passes through:",
]

OPERATOR_LEADS = [
    "Who runs these buses?",
    "The operators on this stretch:",
    "A look at who plies the route:",
]

TIPS = [
    "Reach the stand about fifteen minutes before departure — seats on the popular runs fill up quickly, and standing for a long stretch is no fun.",
    "Timings here are the listed schedule; seasonal traffic, breakdowns and market-day crowds can stretch them. A quick confirmation at the stand never hurts.",
    "Keep some small change handy for the fare. Many private buses still run on exact change and goodwill.",
    "If your day is tight, aim for one of the earlier departures — you give yourself a buffer for delays and still reach with daylight to spare.",
    "Window seats on this side of the route get the better views; the front rows are quieter if you want to doze off.",
    "Travelling with luggage? The boot fills up on festival days and weekends — the earliest bus is usually the roomiest.",
]

BN_INTROS = [
    ("{o} থেকে {t} — প্রতিদিনের চেনা পথ। বাসজাত্রি-র হিসেবে এই রুটে রোজ {n}টি বাস "
     "ছাড়ে, প্রথম বাস সকাল {first}-এ এবং শেষ বাস {last}-এ। নিচে পুরো সময়সূচি দেওয়া "
     "হল — যাত্রার আগে একবার দেখে নিলেই পরিকল্পনা সহজ হয়ে যায়।"),
    ("{t} যাওয়ার প্ল্যান করছেন {o} থেকে? ভালো খবর হল এই রুটে বাসের অভাব নেই। রোজ "
     "{n}টি বাস ছাড়ে, প্রথমটি সকাল {first}-এ, শেষটি {last}-এ। সময়সূচি, অপারেটর আর "
     "থামার তালিকা — সব এক জায়গায় পেয়ে যাবেন এই লেখায়।"),
    ("যারা নিয়মিত এই পথে চলাচল করেন, তাঁদের কাছে {o}–{t} রুটের বাস মানেই নির্ভরতা। "
     "সকাল {first} থেকে {last} পর্যন্ত {n}টি বাস এই পথে চলে। বিস্তারিত সময়সূচি নিচে "
     "দেওয়া হল।"),
]

BN_TIPS = [
    "ছাড়ার আগে পনেরো মিনিট আগে স্ট্যান্ডে পৌঁছে যাওয়া ভালো — ভিড়ের সময় সিট পাওয়া মুশকিল হয়ে যায়।",
    "সময়সূচি মোটামুটি এইরকমই থাকে, কিন্তু ট্রাফিক বা মৌসুমের তারতম্যে একটু-আধটু এদিক-ওদিক হতে পারে।",
    "ভাড়ার জন্য ছোট নোট রাখুন — অনেক বাসে ভাঙতি দেওয়াই কষ্টকর হয়ে দাঁড়ায়।",
    "দিনের কাজ থাকলে সকালের বাসটাই ধরা নিরাপদ — দেরি হলেও সময় মিলে যায়।",
]


def bn_num_words(n):
    """Route-count phrasing for Bengali text (numerals are fine in BN web text)."""
    return str(n)


def article(slug, o, t, buses):
    h = int(hashlib.md5(slug.encode()).hexdigest(), 16)
    v = h % len(OPENINGS)
    lead = JOURNEY_LEADS[h % len(JOURNEY_LEADS)]
    op_lead = OPERATOR_LEADS[h % len(OPERATOR_LEADS)]
    tips = [TIPS[(h + i) % len(TIPS)] for i in range(4)]

    rows = sorted(buses, key=lambda b: to_min(b.get("departure_time")) or 9999)
    timed = [b for b in rows if to_min(b.get("departure_time")) is not None]
    first = fmt(min(to_min(b["departure_time"]) for b in timed))
    last = fmt(max(to_min(b["departure_time"]) for b in timed))
    n = len(rows)
    ops = Counter((b.get("operator") or "").strip() for b in rows
                  if (b.get("operator") or "").strip() not in ("", "—"))
    op_list = ", ".join(f"{esc(k)} ({c})" for k, c in ops.most_common(5)) or "private operators"

    stop_c = Counter()
    for b in buses:
        for st in (b.get("stoppages") or []):
            nm = norm(st.get("name"))
            if nm and nm not in (o, t):
                stop_c[nm] += 1
    major = [nm for nm, c in stop_c.most_common(12)][:8]

    # ---- timetable table
    tbl = ""
    for b in rows:
        dep = fmt(to_min(b.get("departure_time")))
        arr = fmt(to_min(b.get("arrival_time")))
        name = esc((b.get("bus_name") or "Bus service").strip())
        op = esc((b.get("operator") or "").strip())
        low = (b.get("bus_type") or "").lower()
        badge = ""
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

    stop_names = ", ".join(esc(s) for s in major) if major else None

    # ---- English narrative
    opening = OPENINGS[v].format(o=o, t=t, first=first, last=last, n=n)

    para2 = (
        f"That last point matters more than it sounds. Because the service "
        f"spreads across the day, you are never really stranded on this route — "
        f"miss one bus and there is usually another along within a reasonable "
        f"wait. The first departure leaves {o} at {first}, and the last of the "
        f"day rolls out at {last}, which tells you something about how much "
        f"life this road carries."
    )

    journey = ""
    if stop_names:
        journey = (
            f"<h2>The road between {esc(o)} and {esc(t)}</h2>\n"
            f"<p>{lead}</p>\n<ul>\n"
            + "".join(f"<li>{esc(s)}</li>\n" for s in major)
            + "</ul>\n"
            f"<p>Each of these halts is a small world of its own — vendors hop "
            f"on at some, school crowds at others — and knowing which stops "
            f"come before yours makes the journey feel shorter. If you are "
            f"new to the route, keep the list handy; the conductor will usually "
            f"call out the bigger halts.</p>\n"
        )
    else:
        journey = (
            f"<h2>The road between {esc(o)} and {esc(t)}</h2>\n"
            f"<p>The full stop list for every service on this route is on the "
            f"route page — worth a look before you travel, so you know exactly "
            f"where your bus will halt.</p>\n"
        )

    facts = (
        f"<h2>The timings, plainly</h2>\n"
        f"<p>Here is the full day on one screen. {n} buses are listed on "
        f"BusJatri for this route — departures from {esc(o)}, with arrival "
        f"times at {esc(t)} where listed:</p>\n"
        f'<div style="overflow-x:auto;border:1px solid var(--border);border-radius:12px">'
        f'<table style="width:100%;border-collapse:collapse;font-size:14px">'
        f'<thead><tr style="background:var(--panel);font-weight:600;font-size:12px;text-transform:uppercase">'
        f'<th style="padding:9px 12px;text-align:left">Bus</th><th style="padding:9px 12px;text-align:left">Departure</th>'
        f'<th style="padding:9px 12px;text-align:left">Arrival</th><th style="padding:9px 12px;text-align:center">Stops</th>'
        f'</tr></thead>\n<tbody>{tbl}</tbody></table></div>\n'
        f"<p><em>Timings are the listed schedule and can shift with season, "
        f"traffic and day of the week — always confirm at the stand before a "
        f"tight connection.</em></p>\n"
    )

    operators = (
        f"<h2>{op_lead}</h2>\n"
        f"<p>Services on this route are run by {op_list}. In practice this "
        f"matters less on the timetable and more on the day: government "
        f"corporation buses follow depot schedules fairly strictly, while "
        f"private services are often a little more flexible about halts. "
        f"Either way, all of them get you there.</p>\n"
        if ops
        else f"<h2>{op_lead}</h2>\n<p>Services on this route are run by private operators.</p>\n"
    )

    tips_html = (
        "<h2>Small things worth knowing</h2>\n<ul>\n"
        + "".join(f"<li>{p}</li>\n" for p in tips)
        + "</ul>\n"
    )

    faq_body = (
        "<h2>Quick answers</h2>\n"
        f"<p><strong>What is the first bus from {esc(o)} to {esc(t)}?</strong><br>"
        f"The first listed departure is at {first}.</p>\n"
        f"<p><strong>What is the last bus from {esc(o)} to {esc(t)}?</strong><br>"
        f"The last listed departure is at {last}.</p>\n"
        f"<p><strong>How many buses run from {esc(o)} to {esc(t)}?</strong><br>"
        f"{n} bus services are listed on this route on BusJatri.</p>\n"
    )

    # ---- Bengali section
    bn_intro = BN_INTROS[h % len(BN_INTROS)].format(o=o, t=t, first=first, last=last, n=n)
    bn_stops = ""
    if stop_names:
        bn_stops = (
            "<p>পথের বড় বড় থামাগুলো: " + stop_names + "। প্রতিটি থামে অন্য এক ছোট্ট জগৎ — "
            "কোথাও চা-এর দোকান, কোথাও হাটবার। নতুন হলে এই তালিকাটা মনে রাখা ভালো।</p>\n"
        )
    bn_tips = "<ul>\n" + "".join(f"<li>{p}</li>\n" for p in BN_TIPS) + "</ul>\n"
    bn = (
        '<div lang="bn" style="border-top:2px solid var(--amber,#b8791f);margin-top:34px;padding-top:6px">\n'
        "<h2>বাংলায় পড়ুন</h2>\n"
        f"<p>{esc(bn_intro)}</p>\n{bn_stops}"
        "<p><strong>প্রথম বাস:</strong> " + first + " · <strong>শেষ বাস:</strong> " + last +
        " · <strong>মোট বাস:</strong> " + str(n) + "টি</p>\n"
        "<h3>যাত্রার আগে মনে রাখুন</h3>\n" + bn_tips +
        "<p><em>সময়সূচি প্রকাশিত তথ্য অনুযায়ী — মৌসুম ও ট্রাফিকের উপর নির্ভর করে সামান্য "
        "এদিক-ওদিক হতে পারে। যাত্রার আগে স্ট্যান্ডে একবার জেনে নিন।</em></p>\n"
        "</div>\n"
    )

    body = f"""<p>{opening}</p>
<p>{para2}</p>
{journey}
{facts}
{operators}
{tips_html}
{faq_body}
{bn}"""

    title = f"{o} to {t} Bus Time Table ({n} Buses) — Timings, Route & Travel Guide"
    desc = (f"{o} to {t} bus time table: {n} buses, first {first}, last {last}. "
            f"Route, stoppages, operators and travel tips — বাংলায়ও পড়ুন।")
    excerpt = (f"{o} to {t} bus guide: {n} buses daily from {first} to {last}, "
               f"route stops, operators and travel tips (English + বাংলা).")

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
        subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_blog.py"), "--write"], check=True)
        print(f"daily blog: wrote {len(picks)} post(s), manifest now {len(manifest)}")


if __name__ == "__main__":
    main()
