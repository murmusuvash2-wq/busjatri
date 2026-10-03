#!/usr/bin/env python3
"""Fail if two served HTML pages share the same <title>.

Pages retired by a 301 in `_redirects` are ignored, so a duplicate is only a
failure when both URLs are actually served.

Usage: python scripts/check_duplicate_titles.py [repo_root]
Exit code 1 if a duplicate remains among served pages.
"""
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
SCAN_DIRS = ("", "bus-time-table", "via", "blog")


def redirected_paths():
    """Repo-relative file paths retired by a 301 in _redirects."""
    out = set()
    path = os.path.join(ROOT, "_redirects")
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            src = parts[0].lstrip("/")
            out.add(src)
            if not src.endswith(".html"):
                out.add(src + ".html")
    return out


def main():
    retired = redirected_paths()
    titles = defaultdict(list)
    scanned = 0
    for d in SCAN_DIRS:
        base = os.path.join(ROOT, d) if d else ROOT
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            if not name.endswith(".html"):
                continue
            rel = os.path.join(d, name) if d else name
            if rel in retired:
                continue
            with open(os.path.join(base, name), encoding="utf-8", errors="replace") as fh:
                m = TITLE.search(fh.read())
            if not m or not m.group(1).strip():
                continue
            titles[m.group(1).strip()].append(rel)
            scanned += 1

    dups = {t: v for t, v in titles.items() if len(v) > 1}
    print(f"Scanned {scanned} served pages ({len(retired)} retired URLs ignored).")
    if not dups:
        print("OK: no duplicate <title> among served pages.")
        return 0
    print(f"FAIL: {len(dups)} duplicate title(s) among served pages:")
    for t, v in sorted(dups.items()):
        print(f'  "{t}"')
        for rel in sorted(v):
            print(f"      {rel}")
    print("\nFix: give each page a unique title, or retire one URL with a 301 in _redirects.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
