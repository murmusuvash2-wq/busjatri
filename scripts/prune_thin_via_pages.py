#!/usr/bin/env python3
"""noindex + de-list "via" (bus-stop) pages that list too few buses.

Why: ~780 of 2,605 via pages list only 1-2 buses. They are templated near-
duplicates that Google parks as "Discovered - currently not indexed", diluting
crawl budget on a young site (~6,200 URLs, only a few dozen indexed). Pages
below MIN_SERVICES get <meta name="robots" content="noindex,follow"> and are
removed from sitemap-via.xml. They stay live for users - only search inclusion
changes. Fully reversible: change MIN_SERVICES and re-run.

Idempotent: re-running makes no further changes (tag added once, removed again
if a page later gains enough services). ASCII-only source.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIA = ROOT / "via"
SITEMAP = ROOT / "sitemap-via.xml"

MIN_SERVICES = 3  # noindex pages listing fewer than this many bus services

COUNT_RE = re.compile(r"([0-9]+) bus services")
ROBOTS_RE = re.compile(r'<meta\s+name="robots"[^>]*>\s*', re.I)
HEAD_END = "</head>"
OUR_META = '<meta name="robots" content="noindex,follow">\n'
LOC_RE = re.compile(r"<loc>https://busjatri\.in/via/([^<]+)</loc>")


def services(text):
    m = COUNT_RE.search(text)
    return int(m.group(1)) if m else None


def main() -> int:
    thin_slugs = set()
    added = removed = 0

    for p in sorted(VIA.glob("*.html")):
        s = p.read_text(encoding="utf-8")
        n = services(s)
        if n is None:
            continue
        slug = p.stem
        has_meta = bool(ROBOTS_RE.search(s))

        if n < MIN_SERVICES:
            thin_slugs.add(slug)
            if not has_meta:
                idx = s.lower().find(HEAD_END)
                if idx == -1:
                    continue
                s = s[:idx] + OUR_META + s[idx:]
                p.write_text(s, encoding="utf-8")
                added += 1
        else:
            if has_meta:  # page is no longer thin -> drop our noindex
                s = ROBOTS_RE.sub("", s, count=1)
                p.write_text(s, encoding="utf-8")
                removed += 1

    print("thin via pages:", len(thin_slugs), "| noindex added:", added, "| removed:", removed)

    if SITEMAP.exists():
        lines = SITEMAP.read_text(encoding="utf-8").splitlines(keepends=True)
        out, dropped = [], 0
        for ln in lines:
            m = LOC_RE.search(ln)
            if m and m.group(1) in thin_slugs:
                dropped += 1
                continue
            out.append(ln)
        if dropped:
            SITEMAP.write_text("".join(out), encoding="utf-8")
        print("sitemap-via.xml entries dropped:", dropped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
