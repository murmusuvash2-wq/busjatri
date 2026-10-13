#!/usr/bin/env python3
"""design/build.py - make every css file's :root match design/tokens.css.

Idempotent. Safe by construction:
  * only tokens a file ALREADY has are rewritten (never added -> no new rules)
  * tokens whose value is a var() alias are left alone (keeps the link)
  * seo-v2.css is excluded (it carries its own separate theme values)
Run in the build so a colour change in design/tokens.css reaches every page.
"""
import re, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS = os.path.join(ROOT, "design", "tokens.css")
EXCLUDE = {"seo-v2.css"}

def canon():
    s = open(TOKENS, encoding="utf-8").read()
    block = re.search(r":root\s*\{(.*?)\}", s, re.S).group(1)
    d = {}
    for part in block.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            d[k.strip()] = v.strip()
    return d

def main():
    c = canon()
    n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "css", "*.css"))):
        if os.path.basename(f) in EXCLUDE:
            continue
        s = open(f, encoding="utf-8").read()
        m = re.search(r":root\s*\{(.*?)\}", s, re.S)
        if not m:
            continue
        out, changed = [], False
        for part in m.group(1).split(";"):
            if ":" not in part:
                out.append(part); continue
            k, v = part.split(":", 1)
            k = k.strip()
            if k in c and "var(" not in c[k]:
                nv = c[k]
                if v.strip() != nv:
                    changed = True
                out.append(f" {k}:{nv} ")
            else:
                out.append(part)
        if not changed:
            continue
        s = s[:m.start(1)] + ";".join(out) + s[m.end(1):]
        open(f, "w", encoding="utf-8").write(s)
        n += 1
        print("tokens synced ->", os.path.basename(f))
    print(f"design/build.py: {n} file(s) updated")

if __name__ == "__main__":
    main()
