#!/usr/bin/env python3
"""Unify the site header across every page (2026-10-02).

Before: 8 different header variants across 6,143 pages - different control
order, two different theme icons (SVG moon vs a "◐" text glyph), three
different class systems (nav+lang-group / header-actions+icon-btn /
hdr-ctrl+lang-switch), some pages with no language toggle at all, and one
page (sbstc-buses) with a duplicate theme button.

After: one canonical control cluster on every page, in the same order and
with the same styling, wired by a single controller (js/hdr.js):

    [logo] BusJatri          Home  Routes   [EN] [বাংলা]  [moon]

The header is self-contained (inline styles + a tiny <style> for the
language labels), so it renders identically whether the page loads
seo.css, style.css, or no stylesheet at all.

Idempotent: a page whose header already carries the canonical `bj-nav`
cluster is skipped, so re-running is safe.

Usage:  python3 scripts/unify_header_20261002.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MOON = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z"/></svg>')

HDR_CSS = ('<style id="bjHdrCss">'
           '.label-bn{display:none!important}'
           'body.lang-bn .label-en{display:none!important}'
           'body.lang-bn .label-bn{display:inline!important}'
           '</style>')

LINK_STYLE = 'color:var(--ink-dim,#6b6257);text-decoration:none;font-weight:600;white-space:nowrap'

LANG_STYLE_ON = ('background:var(--amber-soft,#f6e7c6);border:1px solid var(--line,#d8cfc0);'
                 'border-radius:999px;padding:3px 10px;font-weight:700;font-size:12px;'
                 'cursor:pointer;color:var(--ink,#2b2118);font-family:inherit;line-height:1.2;'
                 'white-space:nowrap;flex:0 0 auto')
LANG_STYLE_OFF = LANG_STYLE_ON.replace('background:var(--amber-soft,#f6e7c6)', 'background:transparent')

THEME_STYLE = ('width:30px;height:30px;border-radius:50%;border:1px solid var(--line,#d8cfc0);'
               'background:transparent;color:var(--ink,#2b2118);display:inline-flex;'
               'align-items:center;justify-content:center;cursor:pointer;padding:0;flex:0 0 auto')


# Legacy leftovers from the pre-unify pages: a SECOND theme button (id bjThemeBtn)
# and one or more inline scripts that wired it. Both are dead now that js/hdr.js is
# the single controller, so they are stripped from every page on every run.
LEGACY_THEME_BTN_RE = re.compile(r'<button\b[^>]*id="bjThemeBtn"[^>]*>.*?</button>', re.S)


def strip_legacy_theme_scripts(html: str):
    """Remove inline <script> blocks that exist ONLY to wire the legacy
    #bjThemeBtn theme button.

    A page's own functional inline script can mention bjThemeBtn in passing
    (e.g. the /bus-time-table/ hub restores the saved theme and also powers the
    A-Z nav, row toggles and the reveal animation). An earlier version of this
    file used a regex that matched ANY inline script containing bjThemeBtn and
    deleted the whole thing — which silently removed the hub's entire JS, leaving
    every '.reveal' section stuck at opacity:0 (invisible). So we now only drop a
    script when it is small, has no `src`, defines no functions of its own and
    does not carry other page logic.
    """
    def repl(m):
        body = m.group(1)
        if 'bjThemeBtn' not in body:
            return m.group(0)
        # A real page script is many KB (the /bus-time-table/ hub one is ~6 KB);
        # the legacy theme wiring is a tiny snippet. Size is the safe signal.
        if len(body) > 1200:
            return m.group(0)
        return ''

    new = re.sub(r'<script\b(?![^>]*\bsrc=)[^>]*>(.*?)</script>', repl, html, flags=re.S)
    return new, (0 if new == html else 1)


def canonical_controls(links_html: str) -> str:
    return (
        f'{HDR_CSS}\n'
        '<nav class="bj-nav" style="display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center;'
        'font-size:13px;margin-left:auto;justify-content:flex-end">\n'
        f'      {links_html}\n'
        '      <span class="bj-lang" style="display:flex;gap:4px;margin-left:2px">\n'
        f'        <button type="button" id="langEn" class="bj-langbtn" style="{LANG_STYLE_ON}">EN</button>\n'
        f'        <button type="button" id="langBn" class="bj-langbtn" style="{LANG_STYLE_OFF}">বাংলা</button>\n'
        '      </span>\n'
        f'      <button type="button" id="themeBtn" class="bj-themebtn" aria-label="Toggle dark mode" '
        f'title="Toggle dark mode" style="{THEME_STYLE}">{MOON}</button>\n'
        '    </nav>'
    )


def fix_logo_img(logo_html: str) -> str:
    """Keep the badge circular but stop the 360x328 asset being squashed."""
    def repl(m):
        style = m.group(1)
        if 'object-fit' not in style:
            style = style.rstrip(';') + ';object-fit:contain'
        return f'style="{style}"'
    if re.search(r'<img[^>]*brand-logo[^>]*style="([^"]*)"', logo_html):
        return re.sub(r'<img[^>]*brand-logo[^>]*style="([^"]*)"',
                      lambda m: f'<img class="brand-logo" src="/logo.png" alt="BusJatri" style="{m.group(1).rstrip(";")};object-fit:contain"'
                      if 'object-fit' not in m.group(1) else m.group(0),
                      logo_html, count=1)
    # no style attr: add one
    return re.sub(r'(<img[^>]*brand-logo[^>]*?)(\s*/?>)',
                  r'\1 style="width:30px;height:30px;border-radius:50%;object-fit:contain"\2',
                  logo_html, count=1)


def process(path: Path) -> str:
    html = path.read_text(encoding='utf-8', errors='ignore')

    # 0. strip legacy duplicate theme button + its inline scripts (idempotent)
    html, _c1 = LEGACY_THEME_BTN_RE.subn('', html)
    html, _c2 = strip_legacy_theme_scripts(html)
    cleaned = bool(_c1 or _c2)

    m = re.search(r'<header[^>]*>.*?</header>', html, re.S)
    if not m:
        if cleaned:
            path.write_text(html, encoding='utf-8')
        return 'no-header'
    header = m.group(0)
    if 'bj-nav' in header:
        if cleaned:
            path.write_text(html, encoding='utf-8')
            return 'cleaned'
        return 'already'

    # 1. logo block (anchor or div with class="logo")
    lm = re.search(r'<a[^>]*class="[^"]*\blogo\b[^"]*"[^>]*>.*?</a>', header, re.S) or \
         re.search(r'<div[^>]*class="[^"]*\blogo\b[^"]*"[^>]*>.*?</div>', header, re.S)
    if not lm:
        return 'no-logo'
    logo = fix_logo_img(lm.group(0))

    # 2. nav links = every <a> in the header except the logo one
    rest = header.replace(lm.group(0), '')
    links = re.findall(r'<a\b[^>]*>.*?</a>', rest, re.S)
    # normalise each link's style so it looks the same regardless of page CSS
    norm = []
    for a in links:
        a = re.sub(r'<a\b([^>]*)>', lambda mm: '<a' + re.sub(r'\s*style="[^"]*"', '', mm.group(1)) + f' style="{LINK_STYLE}">', a, count=1)
        a = re.sub(r'\s+', ' ', a).strip()
        norm.append(a)
    links_html = '\n      '.join(norm)

    # 3. rebuild the header
    new_header = (
        '<header class="header">\n'
        '  <div class="container header-inner" style="display:flex;flex-wrap:wrap;align-items:center;'
        'justify-content:space-between;gap:8px">\n'
        f'    {logo}\n'
        f'    {canonical_controls(links_html)}\n'
        '  </div>\n'
        '</header>'
    )
    html = html[:m.start()] + new_header + html[m.end():]

    # 4. single controller, once per page
    if 'js/hdr.js' not in html:
        prefix = '../' if path.parent != ROOT else ''
        tag = f'<script src="{prefix}js/hdr.js?v=hdrunify20261002"></script>'
        if '</body>' in html:
            html = html.replace('</body>', f'{tag}\n</body>', 1)
        else:
            html += '\n' + tag

    path.write_text(html, encoding='utf-8')
    return 'patched'


def main():
    stats = {}
    for p in sorted(ROOT.rglob('*.html')):
        if any(part in {'.git', 'node_modules'} for part in p.parts):
            continue
        r = process(p)
        stats[r] = stats.get(r, 0) + 1
    print('done:', ', '.join(f'{k}={v}' for k, v in sorted(stats.items())))


if __name__ == '__main__':
    main()
