#!/usr/bin/env python3
"""Blog English labels + homepage link fix (user request, 2026-09-19).

Applies (idempotently, with --write):
1. gen_blog.py          - blog name/labels in English (title, h1, crumbs,
                          footer link, homepage patch string); blog index now
                          also lists daily posts from data/blog-manifest.json
                          and adds them to the sitemap.
2. gen_reverse_routes.py- footer blog link in English (463 return pages).
3. index.html           - homepage footer link 'ব্লগ (Blog)' -> 'Blog'.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITE = "--write" in sys.argv


def patch(path, edits):
    p = ROOT / path
    s = p.read_text(encoding="utf-8")
    changed = False
    for old, new in edits:
        if new in s:
            continue  # already applied
        if s.count(old) != 1:
            print(f"FAIL {path}: anchor not found or ambiguous:")
            print(old[:160])
            sys.exit(1)
        s = s.replace(old, new)
        changed = True
    if changed and WRITE:
        p.write_text(s, encoding="utf-8")
        print(f"patched {path}")
    elif changed:
        print(f"would patch {path}")
    else:
        print(f"ok (already patched): {path}")


patch(
    "scripts/gen_blog.py",
    [
        (
            '      <a href="../blog/">ব্লগ</a>',
            '      <a href="../blog/">Blog</a>',
        ),
        (
            '<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">ব্লগ</a> › <span>{a["title"][:34]}…</span></div>',
            '<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">Blog</a> › <span>{a["title"][:34]}…</span></div>',
        ),
        (
            '  <h3 class="section-title">সম্পর্কিত পেজ</h3>',
            '  <h3 class="section-title">Related Pages</h3>',
        ),
        (
            '  <a class="rel-chip" href="./">📚 সব লেখা</a>',
            '  <a class="rel-chip" href="./">📚 All Posts</a>',
        ),
        (
            'def index_page():\n    import html as _h\n    cards = ""\n    for a in ARTICLES:',
            'def manifest_articles():\n    """Daily auto-generated route posts (data/blog-manifest.json)."""\n    import json\n    p = ROOT / "data" / "blog-manifest.json"\n    if not p.exists():\n        return []\n    try:\n        return json.loads(p.read_text(encoding="utf-8"))\n    except Exception:\n        return []\n\n\ndef index_page():\n    import html as _h\n    all_posts = manifest_articles() + ARTICLES\n    all_posts.sort(key=lambda a: a["date"], reverse=True)\n    cards = ""\n    for a in all_posts:',
        ),
        (
            '<title>ব্লগ — বাস ভ্রমণের গাইড | BusJatri</title>\n<meta name="description" content="পশ্চিমবঙ্গের বাস ভ্রমণ নিয়ে BusJatri-র বাংলা ব্লগ — রুট গাইড, সময়সূচি টিপস এবং বাস্তব অভিজ্ঞতা।">\n<link rel="canonical" href="{BASE}/blog/">\n<meta property="og:title" content="ব্লগ — বাস ভ্রমণের গাইড | BusJatri">\n<meta property="og:description" content="পশ্চিমবঙ্গের বাস ভ্রমণ নিয়ে BusJatri-র বাংলা ব্লগ।">',
            '<title>Blog — Bus Travel Guides | BusJatri</title>\n<meta name="description" content="West Bengal bus travel guides: route timetables, first and last bus timings, operators and travel tips from BusJatri.">\n<link rel="canonical" href="{BASE}/blog/">\n<meta property="og:title" content="Blog — Bus Travel Guides | BusJatri">\n<meta property="og:description" content="West Bengal bus travel guides: route timetables, operators and travel tips from BusJatri.">',
        ),
        (
            '<div class="crumbs"><a href="../index.html">Home</a> › <span>ব্লগ</span></div>\n<div class="seo-hero">\n  <h1>ব্লগ <span class="arr">—</span> বাস ভ্রমণের গাইড</h1>\n  <p class="bn-sub">পশ্চিমবঙ্গের বাসপথ নিয়ে বাংলায় লেখা</p>\n</div>',
            '<div class="crumbs"><a href="../index.html">Home</a> › <span>Blog</span></div>\n<div class="seo-hero">\n  <h1>Blog <span class="arr">—</span> Bus Travel Guides</h1>\n  <p class="bn-sub">West Bengal bus routes, timetables and travel tips</p>\n</div>',
        ),
        (
            '        for a in ARTICLES:\n            add += f"<url><loc>{BASE}/blog/{a[\'slug\']}.html</loc><lastmod>{TODAY}</lastmod><priority>0.7</priority></url>\\n"',
            '        for a in manifest_articles() + ARTICLES:\n            add += f"<url><loc>{BASE}/blog/{a[\'slug\']}.html</loc><lastmod>{TODAY}</lastmod><priority>0.7</priority></url>\\n"',
        ),
        (
            "                s = s.replace(anchor, '<a href=\"blog/\">ব্লগ (Blog)</a>\\n      ' + anchor, 1)",
            "                s = s.replace(anchor, '<a href=\"blog/\">Blog</a>\\n      ' + anchor, 1)",
        ),
    ],
)

patch(
    "scripts/gen_reverse_routes.py",
    [
        (
            '      <a href="../blog/">ব্লগ</a>',
            '      <a href="../blog/">Blog</a>',
        ),
    ],
)

patch(
    "index.html",
    [
        (
            '<a href="blog/">ব্লগ (Blog)</a>',
            '<a href="blog/">Blog</a>',
        ),
    ],
)

print("blog english patch done")
