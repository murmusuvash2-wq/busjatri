#!/usr/bin/env python3
"""Insert Disclaimer + Terms of Use links into the site footer of every generated page.

Runs after the generators + fix_clean_urls, so the privacy-policy anchor is already a
clean URL. Handles any relative prefix ("" / "../" / "../../") and both ".html" and
clean forms. Idempotent: skips pages that already link the disclaimer.

Usage:  python3 scripts/add_legal_links.py [--write]
"""
import os, re, sys, glob

WRITE = "--write" in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# privacy-policy anchor, capturing the relative prefix and the exact href form used
PAT = re.compile(r'(<a[^>]*href="((?:\.\./)*)privacy-policy(?:\.html)?"[^>]*>.*?</a>)', re.S)
HAS = re.compile(r'href="(?:\.\./)*disclaimer(?:\.html)?"')

changed = 0
scanned = 0
for f in glob.glob("**/*.html", recursive=True):
    if f.startswith(".git/") or f.endswith(("disclaimer.html", "terms.html")):
        continue
    scanned += 1
    try:
        s = open(f, encoding="utf-8", errors="ignore").read()
    except OSError:
        continue
    if HAS.search(s):
        continue

    def rep(m):
        full, pre = m.group(1), m.group(2)
        ext = ".html" if m.group(0).endswith('.html">' + full.split('>', 1)[1]) else ""
        # keep whatever form the privacy link used
        form = ".html" if re.search(r'privacy-policy\.html"', m.group(0)) else ""
        return (full +
                f'\n      <a href="{pre}disclaimer{form}">Disclaimer</a>' +
                f'\n      <a href="{pre}terms{form}">Terms of Use</a>')

    s2, k = PAT.subn(rep, s, count=1)
    if k:
        changed += 1
        if WRITE:
            open(f, "w", encoding="utf-8").write(s2)

print(f"add_legal_links: scanned {scanned}, {'updated' if WRITE else 'would update'} {changed}")
