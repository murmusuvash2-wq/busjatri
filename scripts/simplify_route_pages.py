#!/usr/bin/env python3
"""Simplify route pages (2026-10-07):

1. Header: drop the "Home" / "Routes" links from the header nav on every page,
   so the header is just [logo] + [EN/বাংলা] + [theme]. The route pages already
   carry a breadcrumb, so the header links are redundant.

2. Remove the horizontal "Route Map" block
   (<section class="seo-section"><h3 class="section-title">Route Map</h3>
    <div class="routemap">…</div></section>) — it duplicates the stoppage list
   and truncates on mobile.

Idempotent. Usage: python3 scripts/simplify_route_pages.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# <a ...>Home</a> / <a ...>Routes</a> inside a header
HDR_LINK_RE = re.compile(r'\s*<a\b[^>]*>\s*(?:Home|Routes)\s*</a>')
HEADER_RE = re.compile(r'<header\b.*?</header>', re.S | re.I)
# the Route Map section
ROUTEMAP_RE = re.compile(
    r'\s*<section class="seo-section">\s*<h3 class="section-title">Route Map</h3>.*?</section>',
    re.S)
# horizontal map inside <section class="cstc-direction"> (rm-wrap > rm-track > rm-stops)
RMWRAP_RE = re.compile(r'\s*<div class="rm-wrap"[^>]*>.*?</div></div></div>', re.S)


def strip_rmwrap(html: str) -> str:
    return RMWRAP_RE.sub('', html)


def strip_header_links(html: str) -> str:
    def fix(m):
        return HDR_LINK_RE.sub('', m.group(0))
    return HEADER_RE.sub(fix, html)


def strip_routemap(html: str) -> str:
    return ROUTEMAP_RE.sub('', html)


def main():
    changed = 0
    hl = rm = rmw = 0
    for p in sorted(ROOT.rglob('*.html')):
        if any(part in {'.git', 'node_modules', 'scripts', '.github'} for part in p.parts):
            continue
        try:
            s = p.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        out = s
        if '<header' in out:
            n = strip_header_links(out)
            if n != out:
                hl += 1
            out = n
        if 'Route Map' in out and 'routemap' in out:
            n = strip_routemap(out)
            if n != out:
                rm += 1
            out = n
        if 'rm-wrap' in out:
            n = strip_rmwrap(out)
            if n != out:
                rmw += 1
            out = n
        if out != s:
            p.write_text(out, encoding='utf-8')
            changed += 1
    print(f'pages changed: {changed} (header-links: {hl}, route-map: {rm}, rm-wrap: {rmw})')


if __name__ == '__main__':
    main()
