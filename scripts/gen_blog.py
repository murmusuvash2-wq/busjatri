#!/usr/bin/env python3
"""BusJatri Bengali blog: static article pages + index + homepage link + sitemap.

Articles are embedded in this script so the whole blog regenerates
idempotently on every run (part of the fb-update rebuild chain).
"""
import os
import json
import os
import re
import sys
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

HEADER = """<header class="header">
  <div class="container header-inner">
    <a href="../index.html" class="logo" style="text-decoration:none;color:inherit">
      <img class="brand-logo" src="/logo.png" alt="BusJatri" style="width:30px;height:30px;border-radius:50%">


      Bus<span>Jatri</span>
    </a>
    <nav style="display:flex;gap:10px;align-items:center;font-size:13px">
      <a href="../index.html" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Home</a>
      <a href="../bus-time-table/" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Routes</a>
      <a href="../via/" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Stops</a>
      <button id="bjThemeBtn" aria-label="Toggle dark mode" style="background:var(--surface,#fffcf4);border:1px solid var(--line,#ccc);border-radius:999px;padding:6px 12px;cursor:pointer;font-weight:600;color:var(--ink-dim,#665);font-size:13px;font-family:inherit;line-height:1.2">◐</button>
    </nav>
  </div>
</header>
<script>(function(){try{var b=document.getElementById("bjThemeBtn");if(!b)return;if(localStorage.getItem("seo-theme")==="dark"){document.body.classList.add("dark");b.textContent="\u2600";}b.addEventListener("click",function(){var d=document.body.classList.toggle("dark");try{localStorage.setItem("seo-theme",d?"dark":"light");}catch(e){}b.textContent=d?"\u2600":"\u25d0";});}catch(e){}})();</script>
"""

FOOTER = """<footer class="footer">
  <div class="container">
    <div style="display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;justify-content:center;font-size:13px">
      <a href="../about.html">About Us</a>
      <a href="../contact.html">Contact Us</a>
      <a href="../privacy-policy.html">Privacy Policy</a>
    </div>
    <p style="margin:14px 0 0;text-align:center">BusJatri — West Bengal Bus Timetable</p>
    <p style="margin:6px 0 0;text-align:center">Contact: busjatri@zohomail.in</p>
  </div>
</footer>"""

BLOG_FAQ_DONE = True
ARTICLES = []
_CONTENT_BLOG = os.path.join(ROOT, "content", "blog")
if os.path.isdir(_CONTENT_BLOG):
    import glob as _glob
    for _f in sorted(_glob.glob(os.path.join(_CONTENT_BLOG, "*.json"))):
        ARTICLES.append(json.load(open(_f, encoding="utf-8")))



def article_page(a):
    import html as _h
    related = "".join(
        f'<a class="rel-chip" href="{href}">{_h.escape(label)}</a>' for href, label in a["related"]
    )
    faq_html = ""
    faq_schema = ""
    if a.get("faq"):
        import json as _j
        items = "".join(
            "<details" + (" open" if i == 0 else "") + ' style="border:1px solid var(--line,rgba(33,28,22,.15));border-radius:10px;padding:10px 14px;margin:8px 0;background:var(--surface,#fffcf4)">' + '<summary style="cursor:pointer;font-weight:600;font-size:.95rem">' + q + "</summary>" + '<p style="margin:8px 0 0;font-size:.9rem;line-height:1.7;color:var(--ink-dim,#665)">' + ans + "</p></details>"
            for i, (q, ans) in enumerate(a["faq"]))
        faq_html = ('<section class="seo-section" style="margin-top:26px"><h3 class="section-title">FAQ</h3>' + items + "</section>")
        faq_schema = ('<script type="application/ld+json">' + _j.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": an}} for q, an in a["faq"]]}, ensure_ascii=False) + "</script>")
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{a["title"]} | BusJatri</title>
<meta name="description" content="{a["desc"]}">
<link rel="canonical" href="{BASE}/blog/{a["slug"]}">
<meta name="robots" content="noindex,follow">
<meta property="og:title" content="{a["title"]} | BusJatri">
<meta property="og:description" content="{a["desc"]}">
<meta property="og:type" content="article">
<meta property="og:url" content="{BASE}/blog/{a["slug"]}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#b8791f">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="stylesheet" href="../css/seo.css">
<link rel="stylesheet" href="../css/extras.css">
{faq_schema}{GA4}<style>.article-body p{{line-height:1.85;font-size:1rem;color:var(--ink,#222);margin:0 0 16px}}.article-body h2{{font-size:1.18rem;margin:28px 0 12px;color:var(--ink,#222)}}.article-meta{{font-size:.82rem;color:var(--ink-dim,#665);margin:6px 0 18px}}a.bus-row,a.bus-row:visited{{color:inherit;text-decoration:none}}</style>
</head>
<body>
{HEADER}
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">Blog</a> › <span>{a["title"][:34]}…</span></div>
<article>
<h1 style="font-size:1.5rem;line-height:1.35;margin:14px 0 4px">{a["title"]}</h1>
<div class="article-meta">{a["date"]} · BusJatri টিম</div>
<div class="article-body">
{a["body"]}
</div>
</article>
{faq_html}
<section class="seo-section" style="margin-top:26px">
  <h3 class="section-title">Related Pages</h3>
  <div class="chip-row">{related}</div>
</section>
<section class="seo-section">
  <a class="rel-chip" href="./">📚 All Posts</a>
</section>
</main>
{FOOTER}
</body>
</html>
"""


def manifest_articles():
    """Daily auto-generated route posts (data/blog-manifest.json)."""
    import json
    p = ROOT / "data" / "blog-manifest.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def index_page():
    all_posts = manifest_articles() + ARTICLES
    for a in all_posts:
        a.setdefault("type", "guide")
    guides = sorted(
        (a for a in all_posts if a["type"] == "guide"),
        key=lambda a: a["date"], reverse=True)
    stories = sorted(
        (a for a in all_posts if a["type"] == "story"),
        key=lambda a: a["date"], reverse=True)

    def _cards(items):
        out = ""
        for a in items:
            out += f"""<a class="bus-row" href="{a["slug"]}.html" style="display:block">
  <div class="bmid">
    <div class="op" style="font-size:1rem">{a["title"]}</div>
    <div class="mrow" style="margin-top:6px"><span>{a["date"]}</span></div>
    <p style="margin:8px 0 0;font-size:.9rem;color:var(--ink-dim,#665);line-height:1.6">{a["excerpt"]}</p>
  </div>
</a>"""
        return out

    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Blog — Bus Travel Guides & Stories | BusJatri</title>
<meta name="description" content="West Bengal bus travel guides and bus-journey stories: route timetables, first and last bus timings, operators and travel tips from BusJatri.">
<link rel="canonical" href="{BASE}/blog/">
<meta name="robots" content="noindex,follow">
<meta property="og:title" content="Blog — Bus Travel Guides & Stories | BusJatri">
<meta property="og:description" content="West Bengal bus travel guides and bus-journey stories: route timetables, operators and travel tips from BusJatri.">
<meta property="og:type" content="website">
<meta name="theme-color" content="#b8791f">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="stylesheet" href="../css/seo.css">
<link rel="stylesheet" href="../css/extras.css">
{GA4}<style>.bus-row{{display:block;margin-bottom:14px}}a.bus-row,a.bus-row:visited{{color:inherit;text-decoration:none}}.sec-sub{{color:var(--ink-dim,#665);font-size:.92rem;font-weight:400}}</style>
</head>
<body>
{HEADER}
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
<div class="crumbs"><a href="../index.html">Home</a> › <span>Blog</span></div>
<div class="seo-hero">
  <h1>Blog <span class="arr">—</span> Guides & Stories</h1>
  <p class="bn-sub">West Bengal bus timetables, travel guides and bus-journey stories</p>
</div>
<h2 id="guides" style="font-size:1.18rem;margin:26px 0 4px">Travel Guides <span class="sec-sub">· বাস টাইম ও ভ্রমণ গাইড</span></h2>
<p class="bn-sub" style="margin:0 0 14px">Route time tables, operators and practical travel tips</p>
{_cards(guides)}
<h2 id="stories" style="font-size:1.18rem;margin:34px 0 4px">গল্প <span class="sec-sub">· Bus Journey Stories</span></h2>
<p class="bn-sub" style="margin:0 0 14px">বাসযাত্রার গল্প — সময়সূচির সাথে</p>
{_cards(stories)}
</main>
{FOOTER}
</body>
</html>
"""

def main():
    dry = "--write" not in sys.argv
    if not dry:
        bdir = ROOT / "blog"
        bdir.mkdir(exist_ok=True)
        for a in ARTICLES:
            (bdir / (a["slug"] + ".html")).write_text(article_page(a), encoding="utf-8")
        (bdir / "index.html").write_text(index_page(), encoding="utf-8")
        print(f"blog: {len(ARTICLES)} articles + index written")

        # blog is HIDDEN (owner: timetable site) — no link injected into the homepage

        # sitemap: blog urls (idempotent)
        sm = ROOT / "sitemap.xml"
        s = sm.read_text(encoding="utf-8")
        s = re.sub(r"<url><loc>" + re.escape(BASE) + r"/blog/[^<]*</loc>.*?</url>\n?", "", s)
        add = f"<url><loc>{BASE}/blog/</loc><lastmod>{TODAY}</lastmod><priority>0.8</priority></url>\n"
        for a in manifest_articles() + ARTICLES:
            add += f"<url><loc>{BASE}/blog/{a['slug']}</loc><lastmod>{TODAY}</lastmod><priority>0.7</priority></url>\n"
        s = s.replace("</urlset>", add + "</urlset>")
        sm.write_text(s, encoding="utf-8")
        print("sitemap: blog urls added")


if __name__ == "__main__":
    main()
