#!/usr/bin/env python3
"""Inject the cookie-consent script before </body> on every page. Idempotent.
Usage: python3 scripts/add_consent_banner.py [--write]"""
import os, glob, sys
WRITE = "--write" in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TAG = '<script defer src="/js/cookie-consent.js"></script>\n'
changed = 0
for f in glob.glob("**/*.html", recursive=True):
    if f.startswith(".git/"):
        continue
    s = open(f, encoding="utf-8", errors="ignore").read()
    if "cookie-consent.js" in s or "</body>" not in s:
        continue
    s2 = s.replace("</body>", TAG + "</body>", 1)
    changed += 1
    if WRITE:
        open(f, "w", encoding="utf-8").write(s2)
print(f"add_consent_banner: {'updated' if WRITE else 'would update'} {changed}")
