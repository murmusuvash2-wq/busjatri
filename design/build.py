#!/usr/bin/env python3
"""design/build.py - BusJatri design build.

The design lives in design/ :
  tokens.css      the colour / font / spacing variables
  layout.css      shared LAYOUT rules (header, footer, container, grids, search shell)
  components.css  shared COMPONENT rules (cards, chips, badges, buttons, tables)

This script distributes them into the css/*.css files the pages load:
  * :root            -> synced from design/tokens.css (existing tokens only)
  * a shared selector -> its body is taken from design/layout.css or components.css
Only selectors that are IDENTICAL in every file they appear in are in design/,
so a page-type's own overrides are never touched. Idempotent.
"""
import re, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join(ROOT, "design")
EXCLUDE = {"seo-v2.css"}   # carries its own separate theme

def parse_rules(text):
    """yield (start, sel_start, sel_end, body_start, body_end, sel, body) for top-level rules"""
    s = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    out = []
    i, n = 0, len(text)
    while i < n:
        j = text.find('{', i)
        if j < 0: break
        sel = text[i:j]
        depth, k = 1, j + 1
        while k < n and depth:
            if text[k] == '{': depth += 1
            elif text[k] == '}': depth -= 1
            k += 1
        clean = sel.strip()
        if clean and not clean.startswith('@'):
            out.append((clean, text[j+1:k-1], j+1, k-1))
        i = k
    return out

def design_rules():
    d = {}
    for fn in ("layout.css", "components.css"):
        p = os.path.join(DESIGN, fn)
        if not os.path.exists(p): continue
        for sel, body, _, _ in parse_rules(open(p, encoding="utf-8").read()):
            d[sel] = body.strip()
    return d

def tokens():
    s = open(os.path.join(DESIGN, "tokens.css"), encoding="utf-8").read()
    return re.search(r":root\s*\{(.*?)\}", s, re.S).group(1).strip()

def main():
    dr = design_rules(); tb = tokens(); updated = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "css", "*.css"))):
        if os.path.basename(f) in EXCLUDE: continue
        s = open(f, encoding="utf-8").read(); orig = s
        # 1) tokens
        m = re.search(r":root\s*\{(.*?)\}", s, re.S)
        if m:
            keep = []
            for part in m.group(1).split(";"):
                if ":" not in part: continue
                k, v = part.split(":", 1); k = k.strip()
                cmap = dict(x.split(":", 1) for x in tb.split(";") if ":" in x)
                if k in cmap:
                    keep.append(f" {k}:{cmap[k].strip()} ")
                else:
                    keep.append(f" {k}:{v.strip()} ")
            s = s[:m.start(1)] + ";".join(keep) + s[m.end(1):]
        # 2) shared rules (rewrite bodies from design/ - last occurrence wins, do from the end)
        rules = parse_rules(s)
        for sel, body, bs, be in reversed(rules):
            if sel in dr and re.sub(r'\s+', ' ', body.strip()) != re.sub(r'\s+', ' ', dr[sel]):
                s = s[:bs] + dr[sel] + s[be:]
        if s != orig:
            open(f, "w", encoding="utf-8").write(s); updated += 1
            print("design ->", os.path.basename(f))
    print(f"design/build.py: {updated} file(s) updated")

if __name__ == "__main__":
    main()
