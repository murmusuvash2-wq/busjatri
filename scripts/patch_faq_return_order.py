#!/usr/bin/env python3
"""
Patch route pages: shift FAQ below Return Route.
Previously:
  [Via Stoppages] -> [FAQ] -> [Return Route] -> [Related / More Routes]
Now:
  [Via Stoppages] -> [Return Route] -> [FAQ] -> [Related / More Routes]
"""

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUS_DIR = os.path.join(ROOT, "bus-time-table")

PATTERN = re.compile(
    r'(<section class="(?:seo-section|section)[^"]*">\s*<h[23][^>]*>FAQ.*?<\/section>)\s*(<section class="(?:seo-section|section)[^"]*">\s*<a class="rel-chip"[^>]*href="[^"]*"[^>]*>↩.*?\(return\)<\/a>\s*<\/section>)',
    re.DOTALL
)

def main():
    files = sorted(glob.glob(os.path.join(BUS_DIR, "*.html")))
    updated = 0
    skipped = 0

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        m = PATTERN.search(content)
        if m:
            faq_sec = m.group(1)
            ret_sec = m.group(2)
            # Put return route section first, then FAQ section
            replacement = ret_sec + "\n" + faq_sec
            new_content = PATTERN.sub(lambda _: replacement, content, count=1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            updated += 1
        else:
            skipped += 1

    print(f"Total files scanned: {len(files)}")
    print(f"Successfully shifted (Return Route -> FAQ): {updated}")
    print(f"Skipped (no adjacent FAQ + Return pair): {skipped}")

if __name__ == "__main__":
    main()
