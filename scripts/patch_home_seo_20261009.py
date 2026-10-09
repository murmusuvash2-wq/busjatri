#!/usr/bin/env python3
"""Homepage SEO fixes from the Rank Math audit (2026-10-09).

Two fixes to index.html, both idempotent:

1. Meta description was 191 characters — search engines truncate past ~160,
   so the tail ("Kolkata, Mukutmanipur & more") never showed. Trimmed to
   <=155 while keeping the main keywords.

2. The page had no H2 at all. "Popular Operators" was a plain <div>; it is
   now an <h2> with the identical inline styling, so nothing changes visually.

Everything else in the audit that is actionable is infrastructure, not page
markup: http://busjatri.in still serves content instead of redirecting to
https, www.busjatri.in does not resolve, and Cloudflare's managed robots.txt
blocks AI crawlers (Google-Extended, ChatGPT-User, Perplexity-User...).
Those need Cloudflare/DNS access, not a commit.

Run:  python3 scripts/patch_home_seo_20261009.py
"""
import re
import sys

PATH = "index.html"

OLD_DESC = ("West Bengal's largest bus timetable. Search buses, routes &amp; stoppages across "
            "SBSTC, WBTC, NBSTC, private operators. Bus stand departure times for Bankura, "
            "Digha, Kolkata, Mukutmanipur &amp; more.")
OLD_DESC_RAW = ("West Bengal's largest bus timetable. Search buses, routes & stoppages across "
                "SBSTC, WBTC, NBSTC, private operators. Bus stand departure times for Bankura, "
                "Digha, Kolkata, Mukutmanipur & more.")

NEW_DESC = ("Search West Bengal bus timetables, routes and stoppages for SBSTC, WBTC, NBSTC and "
            "private buses \u2014 departure times from Kolkata, Digha and more.")

POP_DIV_OPEN = ('<div style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;'
                'color:var(--amber-ink,#6b4610);font-weight:600;margin-bottom:10px">')
POP_H2_OPEN = ('<h2 style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;'
               'color:var(--amber-ink,#6b4610);font-weight:600;margin:0 0 10px">')


def main() -> int:
    with open(PATH, encoding="utf-8") as f:
        html = f.read()
    changed = []

    # --- 1. meta description -------------------------------------------------
    if len(NEW_DESC) > 155:
        print(f"FAIL: new description is {len(NEW_DESC)} chars (>155)", file=sys.stderr)
        return 1
    for old in (OLD_DESC, OLD_DESC_RAW):
        if old in html:
            html = html.replace(old, NEW_DESC)
            changed.append(f"meta description -> {len(NEW_DESC)} chars")
            break
    else:
        if NEW_DESC in html:
            changed.append("meta description already trimmed")
        else:
            print("WARN: old meta description not found", file=sys.stderr)

    # --- 2. Popular Operators div -> h2 --------------------------------------
    if POP_DIV_OPEN in html:
        i = html.find(POP_DIV_OPEN)
        j = html.find("</div>", i)
        html = html[:i] + POP_H2_OPEN + html[i + len(POP_DIV_OPEN):j] + "</h2>" + html[j + len("</div>"):]
        changed.append("Popular Operators div -> h2")
    elif POP_H2_OPEN in html:
        changed.append("Popular Operators already an h2")
    else:
        print("WARN: Popular Operators block not found", file=sys.stderr)

    with open(PATH, "w", encoding="utf-8") as f:
        f.write(html)

    h2 = html.count("<h2")
    d = re.search(r'<meta name="description" content="([^"]*)"', html)
    print("changed:", "; ".join(changed))
    print("verify -> h2 tags:", h2, "| desc chars:", len(d.group(1)) if d else "?")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
