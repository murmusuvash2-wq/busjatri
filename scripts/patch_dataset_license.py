#!/usr/bin/env python3
"""Add recommended `license` field to Dataset JSON-LD on Kolkata city route pages.

Fixes Google Search Console "Missing field 'license'" (non-critical) warning
for the Dataset rich result type on /bus-time-table/ city pages.
Idempotent: skips pages that already have a license in the Dataset block.
"""
import glob
import os
import re

BASE = os.path.join(os.path.dirname(__file__), "..")
LICENSE_URL = "https://busjatri.in/about"
ANCHOR = ',"isAccessibleForFree":true}'
REPLACEMENT = (
    ',"license":"%s","isAccessibleForFree":true}' % LICENSE_URL
)


def main():
    patched = 0
    skipped = 0
    for f in glob.glob(os.path.join(BASE, "bus-time-table", "*.html")):
        with open(f, encoding="utf-8") as fh:
            h = fh.read()
        if '"@type":"Dataset"' not in h:
            continue
        if '"license":"%s"' % LICENSE_URL in h:
            skipped += 1
            continue
        if h.count(ANCHOR) != 1:
            print("WARN anchor count != 1, skipping:", f)
            continue
        h = h.replace(ANCHOR, REPLACEMENT)
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(h)
        patched += 1
    print("patched=%d skipped(already-done)=%d" % (patched, skipped))


if __name__ == "__main__":
    main()
