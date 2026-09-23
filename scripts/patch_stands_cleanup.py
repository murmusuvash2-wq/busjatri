#!/usr/bin/env python3
"""Stand-page cleanup: new design for Garia Bus Stand + 2 Bardhaman stands.

Three stand pages were still in the OLD design (left over from before the
SEO v3 rollout) while duplicates of them existed in the new design:

  buses-from-garia-bus-stand.html          (OLD design, linked from BTT)
  buses-from-barddhaman-alisha-bus-stand.html  (OLD design, linked from BTT)
  buses-from-barddhaman-nawabhat-bus-stand.html (OLD design, linked from BTT)
  buses-from-garia.html                    (alias-merged "Garia" = Kolkata
                                            group duplicate, 687 buses)
  buses-from-barddhaman-alisha.html        (orphan, unlinked)
  buses-from-barddhaman-nawabhat.html     (orphan, unlinked)

This script:
  1. patches discover_stands() in scripts/gen_stand_v2.py so a stand whose
     title-stripped name maps to a different file keeps its filename-derived
     name (fixes "Garia Bus Stand" being treated as the "Garia" alias stand
     and the BTT card showing the wrong bus count),
  2. deletes the 3 duplicate/orphan files,
  3. regenerates the 3 stand pages in the new design,
  4. regenerates the BTT hub (bus-time-table/index.html) so the duplicate
     Garia card disappears,
  5. removes buses-from-garia.html from sitemap.xml,
  6. adds 301 redirects for the 3 deleted URLs to _redirects.

Idempotent: safe to run multiple times.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DUPES = [
    "bus-time-table/buses-from-garia.html",
    "bus-time-table/buses-from-barddhaman-alisha.html",
    "bus-time-table/buses-from-barddhaman-nawabhat.html",
]
STANDS = ["Garia Bus Stand", "Barddhaman Alisha Bus Stand", "Barddhaman Nawabhat Bus Stand"]
REDIRECTS = [
    "/bus-time-table/buses-from-garia /bus-time-table/buses-from-garia-bus-stand.html 301",
    "/bus-time-table/buses-from-garia.html /bus-time-table/buses-from-garia-bus-stand.html 301",
    "/bus-time-table/buses-from-barddhaman-alisha /bus-time-table/buses-from-barddhaman-alisha-bus-stand.html 301",
    "/bus-time-table/buses-from-barddhaman-alisha.html /bus-time-table/buses-from-barddhaman-alisha-bus-stand.html 301",
    "/bus-time-table/buses-from-barddhaman-nawabhat /bus-time-table/buses-from-barddhaman-nawabhat-bus-stand.html 301",
    "/bus-time-table/buses-from-barddhaman-nawabhat.html /bus-time-table/buses-from-barddhaman-nawabhat-bus-stand.html 301",
]

# ---- 1. patch discover_stands ----
GEN = os.path.join(ROOT, "scripts/gen_stand_v2.py")
OLD = ('        name = re.sub(r"\\s+bus stand$", "", name, flags=re.I)\n'
       "        out.append((name, fname))\n")
NEW = ('        name = re.sub(r"\\s+bus stand$", "", name, flags=re.I)\n'
       "        # If the stripped name maps to a DIFFERENT file, trust the filename:\n"
       "        # e.g. buses-from-garia-bus-stand.html is the \"Garia Bus Stand\" page,\n"
       "        # not the alias-merged \"Garia\" (Kolkata group) page.\n"
       "        base = fname[len("buses-from-"):-len(".html")]\n"
       "        if g.slug(name) != base:\n"
       "            name = base.replace("-", " ").title()\n"
       "        out.append((name, fname))\n")

with open(GEN, encoding="utf-8") as fh:
    src = fh.read()
if NEW in src:
    print("gen_stand_v2.py: already patched")
elif OLD not in src:
    raise SystemExit("ABORT: discover_stands block not found in gen_stand_v2.py")
else:
    with open(GEN, "w", encoding="utf-8") as fh:
        fh.write(src.replace(OLD, NEW, 1))
    print("gen_stand_v2.py: patched")

# ---- 2. delete duplicates ----
for d in DUPES:
    p = os.path.join(ROOT, d)
    if os.path.exists(p):
        os.remove(p)
        print("deleted:", d)
    else:
        print("already absent:", d)

# ---- 3. regenerate the 3 stand pages ----
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import gen_stand_v2 as gs  # noqa: E402

for stand in STANDS:
    fname, page = gs.generate_stand_page_v2(stand)
    with open(os.path.join(ROOT, "bus-time-table", fname), "w", encoding="utf-8") as fh:
        fh.write(page)
    print("regenerated:", fname, len(page) // 1024, "KB")

# ---- 4. regenerate BTT hub ----
subprocess.run([sys.executable, os.path.join(ROOT, "scripts/gen_btt_v2.py")],
               cwd=ROOT, check=True)

# ---- 5. remove deleted URL from sitemap.xml ----
SM = os.path.join(ROOT, "sitemap.xml")
with open(SM, encoding="utf-8") as fh:
    sm = fh.read()
sm2 = re.sub(r"<url>\s*<loc>[^<]*buses-from-garia\.html</loc>.*?</url>\s*", "", sm, flags=re.S)
if sm2 != sm:
    with open(SM, "w", encoding="utf-8") as fh:
        fh.write(sm2)
    print("sitemap.xml: removed buses-from-garia.html")
else:
    print("sitemap.xml: no change")

# ---- 6. redirects ----
RD = os.path.join(ROOT, "_redirects")
with open(RD, encoding="utf-8") as fh:
    rd = fh.read()
add = [r for r in REDIRECTS if r not in rd]
if add:
    if not rd.endswith("\n"):
        rd += "\n"
    rd += "# deleted duplicate stand pages -> canonical\n" + "\n".join(add) + "\n"
    with open(RD, "w", encoding="utf-8") as fh:
        fh.write(rd)
    print("_redirects: added", len(add), "rules")
else:
    print("_redirects: already present")

print("stand cleanup complete")
