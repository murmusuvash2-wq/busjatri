#!/usr/bin/env python3
"""scripts/check_content.py - validate content/ before it is published.

content/ is the single source for written material:
  content/blog/NN-<slug>.json   blog posts (slug, title, desc, date, body)
  content/about-route/          per-route "About" snippets
  content/place-notes/          place descriptions
  content/stand-guides/         bus-stand travel guides
Exit non-zero if a file is malformed, so a bad commit never reaches the build."""
import json, os, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = {"slug", "title", "desc", "date", "body"}
bad = 0
for f in sorted(glob.glob(os.path.join(ROOT, "content", "blog", "*.json"))):
    try:
        a = json.load(open(f, encoding="utf-8"))
    except Exception as e:
        print(f"BAD JSON {f}: {e}"); bad += 1; continue
    miss = REQUIRED - set(a)
    if miss:
        print(f"MISSING {sorted(miss)} in {os.path.basename(f)}"); bad += 1
    if not str(a.get("body", "")).strip():
        print(f"EMPTY body in {os.path.basename(f)}"); bad += 1
print(f"check_content: {bad} problem(s)")
sys.exit(1 if bad else 0)
