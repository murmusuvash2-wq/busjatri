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

Note: this file deliberately avoids backslashes and quote-escaping so it
survives byte-exact re-typing (built via chr() constants where needed).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NL = chr(10)   # newline
BS = chr(92)   # backslash
Q = chr(34)    # double quote

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

LINE_SUB = (
    "        name = re.sub(r" + Q + BS + "s+bus stand$" + Q + ", "
    + Q + Q + ", name, flags=re.I)" + NL
)
LINE_APPEND = "        out.append((name, fname))" + NL
OLD = LINE_SUB + LINE_APPEND
INSERT = (
    "        # If the stripped name maps to a DIFFERENT file, trust the filename:" + NL
    + "        # e.g. buses-from-garia-bus-stand.html is the " + Q + "Garia Bus Stand" + Q + " page," + NL
    + "        # not the alias-merged " + Q + "Garia" + Q + " (Kolkata group) page." + NL
    + "        base = fname[len(" + Q + "buses-from-" + Q + "):-len(" + Q + ".html" + Q + ")]" + NL
    + "        if g.slug(name) != base:" + NL
    + "            name = base.replace(" + Q + "-" + Q + ", " + Q + " " + Q + ").title()" + NL
)
NEW = LINE_SUB + INSERT + LINE_APPEND

with open(GEN, encoding="utf-8") as fh:
    src = fh.read()
if INSERT in src:
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

# ---- 5. remove deleted URL from sitemap.xml (plain string surgery) ----
SM = os.path.join(ROOT, "sitemap.xml")
with open(SM, encoding="utf-8") as fh:
    sm = fh.read()
marker = "buses-from-garia.html</loc>"
i = sm.find(marker)
if i == -1:
    print("sitemap.xml: no change")
else:
    start = sm.rfind("<url>", 0, i)
    end = sm.find("</url>", i)
    end = end + len("</url>") if end != -1 else len(sm)
    while end < len(sm) and sm[end] in chr(13) + NL:
        end += 1
    with open(SM, "w", encoding="utf-8") as fh:
        fh.write(sm[:start] + sm[end:])
    print("sitemap.xml: removed buses-from-garia.html")

# ---- 6. redirects ----
RD = os.path.join(ROOT, "_redirects")
with open(RD, encoding="utf-8") as fh:
    rd = fh.read()
add = [r for r in REDIRECTS if r not in rd]
if add:
    if not rd.endswith(NL):
        rd += NL
    rd += "# deleted duplicate stand pages -> canonical" + NL + NL.join(add) + NL
    with open(RD, "w", encoding="utf-8") as fh:
        fh.write(rd)
    print("_redirects: added", len(add), "rules")
else:
    print("_redirects: already present")

print("stand cleanup complete")
