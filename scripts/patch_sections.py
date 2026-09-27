#!/usr/bin/env python3
"""Split the BusJatri blog index into two sections: Travel Guides and Stories.

1. gen_blog.py: replaces index_page() with a version that groups posts by
   'type' (guides first, then stories). All embedded ARTICLES are guides;
   manifest entries get an explicit 'type'.
2. data/blog-manifest.json: adds 'type' to every entry and drops the legacy
   duplicate 'kolkata-to-digha-bus-guide' story card (same slug as the
   embedded guide article, so the card showed the guide page - misleading,
   and it duplicated the URL in sitemap.xml).

ASCII-only source; Bengali text via unicode escapes.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STORY_SLUGS = [
    "durgapur-to-karunamoyee",
    "cooch-behar-to-siliguri",
    "burdwan-to-kolkata",
    "bankura-to-kolkata",
]

NEW_INDEX_FN = '''def index_page():
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
<title>Blog \u2014 Bus Travel Guides & Stories | BusJatri</title>
<meta name="description" content="West Bengal bus travel guides and bus-journey stories: route timetables, first and last bus timings, operators and travel tips from BusJatri.">
<link rel="canonical" href="{BASE}/blog/">
<meta property="og:title" content="Blog \u2014 Bus Travel Guides & Stories | BusJatri">
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
<div class="crumbs"><a href="../index.html">Home</a> \u203a <span>Blog</span></div>
<div class="seo-hero">
  <h1>Blog <span class="arr">\u2014</span> Guides & Stories</h1>
  <p class="bn-sub">West Bengal bus timetables, travel guides and bus-journey stories</p>
</div>
<h2 id="guides" style="font-size:1.18rem;margin:26px 0 4px">Travel Guides <span class="sec-sub">\u00b7 \u09ac\u09be\u09b8 \u099f\u09be\u0987\u09ae \u0993 \u09ad\u09cd\u09b0\u09ae\u09a3 \u0997\u09be\u0987\u09a1</span></h2>
<p class="bn-sub" style="margin:0 0 14px">Route time tables, operators and practical travel tips</p>
{_cards(guides)}
<h2 id="stories" style="font-size:1.18rem;margin:34px 0 4px">\u0997\u09b2\u09cd\u09aa <span class="sec-sub">\u00b7 Bus Journey Stories</span></h2>
<p class="bn-sub" style="margin:0 0 14px">\u09ac\u09be\u09b8\u09af\u09be\u09a4\u09cd\u09b0\u09be\u09b0 \u0997\u09b2\u09cd\u09aa \u2014 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf\u09b0 \u09b8\u09be\u09a5\u09c7</p>
{_cards(stories)}
</main>
{FOOTER}
</body>
</html>
"""
'''


def main():
    # 1. patch gen_blog.py
    gp = ROOT / "scripts" / "gen_blog.py"
    src = gp.read_text(encoding="utf-8")
    if 'id="guides"' in src:
        print("gen_blog.py: already sectioned, skip")
    else:
        i = src.find("def index_page():")
        j = src.find("\ndef main():")
        assert i != -1 and j != -1 and i < j, "index_page/main markers not found"
        src = src[:i] + NEW_INDEX_FN + src[j:]
        gp.write_text(src, encoding="utf-8")
        print("gen_blog.py: index_page() replaced (sections)")

    # 2. patch manifest
    mp = ROOT / "data" / "blog-manifest.json"
    m = json.loads(mp.read_text(encoding="utf-8"))
    before = len(m)
    m = [e for e in m if e["slug"] != "kolkata-to-digha-bus-guide"]
    dropped = before - len(m)
    for e in m:
        e["type"] = "story" if e["slug"] in STORY_SLUGS else "guide"
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n",
                  encoding="utf-8")
    print(f"manifest: {len(m)} entries, {dropped} duplicate dropped, "
          f"{sum(1 for e in m if e['type']=='story')} stories, "
          f"{sum(1 for e in m if e['type']=='guide')} guides")


if __name__ == "__main__":
    main()
