#!/usr/bin/env python3
"""Remove 6 duplicate alias-group stand pages (same data as canonical).

These 6 stand pages each show the exact same alias-merged bus list as their
canonical stand page (identical bus counts), so they are pure duplicates:

  buses-from-burdwan.html     -> 301 -> buses-from-bardhaman.html
  buses-from-midnapur.html    -> 301 -> buses-from-medinipur.html
  buses-from-tarkeshwar.html  -> 301 -> buses-from-tarakeshwar.html
  buses-from-esplanade.html   -> 301 -> buses-from-kolkata.html
  buses-from-karunamoyee.html -> 301 -> buses-from-kolkata.html
  buses-from-santragachi.html -> 301 -> buses-from-kolkata.html

The route pages (esplanade-to-*.html, santragachi-to-*.html, etc.) are NOT
touched - they carry their own distinct data.

This script deletes the 6 files, regenerates the BTT hub so the duplicate
cards disappear, removes the 6 URLs from sitemap.xml, and adds 301 redirect
rules to _redirects. Idempotent: safe to run multiple times.

Note: this file deliberately avoids backslashes so it survives byte-exact
re-typing.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NL = chr(10)

PAIRS = [
    ("burdwan", "bardhaman"),
    ("midnapur", "medinipur"),
    ("tarkeshwar", "tarakeshwar"),
    ("esplanade", "kolkata"),
    ("karunamoyee", "kolkata"),
    ("santragachi", "kolkata"),
]

REDIRECTS = []
for old, new in PAIRS:
    REDIRECTS.append("/bus-time-table/buses-from-" + old + " /bus-time-table/buses-from-" + new + ".html 301")
    REDIRECTS.append("/bus-time-table/buses-from-" + old + ".html /bus-time-table/buses-from-" + new + ".html 301")

# ---- 1. delete duplicate stand pages ----
for old, new in PAIRS:
    p = os.path.join(ROOT, "bus-time-table", "buses-from-" + old + ".html")
    if os.path.exists(p):
        os.remove(p)
        print("deleted: buses-from-" + old + ".html -> buses-from-" + new + ".html")
    else:
        print("already absent: buses-from-" + old + ".html")

# ---- 2. regenerate BTT hub ----
subprocess.run([sys.executable, os.path.join(ROOT, "scripts/gen_btt_v2.py")],
               cwd=ROOT, check=True)

# ---- 3. remove deleted URLs from sitemap.xml ----
SM = os.path.join(ROOT, "sitemap.xml")
with open(SM, encoding="utf-8") as fh:
    sm = fh.read()
changed = 0
for old, _new in PAIRS:
    marker = "buses-from-" + old + ".html</loc>"
    i = sm.find(marker)
    while i != -1:
        start = sm.rfind("<url>", 0, i)
        end = sm.find("</url>", i)
        end = end + len("</url>") if end != -1 else len(sm)
        while end < len(sm) and sm[end] in chr(13) + NL:
            end += 1
        sm = sm[:start] + sm[end:]
        changed += 1
        i = sm.find(marker)
if changed:
    with open(SM, "w", encoding="utf-8") as fh:
        fh.write(sm)
print("sitemap.xml: removed", changed, "URL blocks")
# also sitemap-popular.xml and sitemap-extra.xml, just in case
for extra in ("sitemap-popular.xml", "sitemap-extra.xml"):
    ep = os.path.join(ROOT, extra)
    if not os.path.exists(ep):
        continue
    with open(ep, encoding="utf-8") as fh:
        es = fh.read()
    if "buses-from-" in es:
        for old, _new in PAIRS:
            if "buses-from-" + old + ".html" in es:
                print("WARNING:", extra, "still references buses-from-" + old + ".html")

# ---- 4. redirects ----
RD = os.path.join(ROOT, "_redirects")
with open(RD, encoding="utf-8") as fh:
    rd = fh.read()
add = [r for r in REDIRECTS if r not in rd]
if add:
    if not rd.endswith(NL):
        rd += NL
    rd += "# deleted duplicate alias-group stand pages -> canonical" + NL + NL.join(add) + NL
    with open(RD, "w", encoding="utf-8") as fh:
        fh.write(rd)
    print("_redirects: added", len(add), "rules")
else:
    print("_redirects: already present")

print("stand dedup complete")
