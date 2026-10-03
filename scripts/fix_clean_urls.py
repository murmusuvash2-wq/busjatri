#!/usr/bin/env python3
"""Normalize every busjatri.in *page* URL to clean (extensionless) form.

Why: Cloudflare serves /page.html as a 301 to /page, and Google already indexes
the clean URL as canonical (verified in GSC: googleCanonical is the extensionless
URL while our tags say .html). This aligns every deployed artifact with what
Google already picked - a consolidation, not a URL change.

Scope (deployed files only; scripts/ and .github/ excluded):
  - sitemap.xml, sitemap-via.xml, sitemap-popular.xml, sitemap-extra.xml,
    sitemap-city.xml        <loc> entries
  - every .html under the repo root (root, bus-time-table/, via/, blog/)
      * absolute URLs      https://busjatri.in/<p>.html  -> https://busjatri.in/<p>
      * canonical / og:url / twitter:url / JSON-LD url+item (all absolute)
      * parent-relative    ../<p>.html                   -> ../<p>
      * bare-relative      <dir>/<p>.html                -> <dir>/<p>
  - _redirects   destination field (.html -> clean) so redirects land directly
                 on the canonical clean URL instead of a second hop

Never touched:
  - SPA hash routes: index.html#/bus/..., ../index.html#/search?...  (8k+ links)
  - asset links: .css .js .png .svg .json .woff2
  - mailto:, anchors, absolute/root-relative non-page URLs, redirect sources

Idempotent: re-running makes no further changes. ASCII-only source.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SITEMAPS = [
    "sitemap.xml",
    "sitemap-via.xml",
    "sitemap-popular.xml",
    "sitemap-extra.xml",
    "sitemap-city.xml",
]

# absolute homepage file URL -> site root
ABS_HOME_RE = re.compile(r'https://busjatri\.in/index\.html(?=["\'<>\s&])')
# absolute page URL ending .html (excludes index.html, which ABS_HOME handles)
ABS_RE = re.compile(r'(https://busjatri\.in/(?!index\.html)[^"\'<>\s]+?)\.html(?=["\'<>\s&#])')
# sitemap <loc> forms
LOC_HOME_RE = re.compile(r'<loc>https://busjatri\.in/index\.html</loc>')
LOC_RE = re.compile(r'(<loc>https://busjatri\.in/(?!index\.html)[^<]+?)\.html(</loc>)')
# parent-relative page links ../<p>.html  (never ../index.html#...)
PARENT_HOME_RE = re.compile(r'href="\.\./index\.html(?=["?])')
PARENT_RE = re.compile(r'href="\.\./(?!index\.html)([A-Za-z0-9][A-Za-z0-9._/-]*)\.html(?=["?#])')
# dot-slash relative page links ./<p>.html  (never ./index.html)
DOT_RE = re.compile(r'href="\./(?!index\.html)([A-Za-z0-9][A-Za-z0-9._/-]*)\.html(?=["?#])')
# bare-relative page links <dir>/<p>.html  (no scheme, no leading . / , not index)
BARE_RE = re.compile(r'href="(?!https?:|\.\.?/|/|mailto:|#|index\.html)([A-Za-z0-9][A-Za-z0-9._/-]*)\.html(?=["?#])')
# _redirects: "<source> <destination.html> <status>"  -> clean the destination
REDIR_RE = re.compile(r'^(\S+\s+)(/\S+?)\.html(\s+\d{3}.*)$')


def normalize(text: str) -> str:
    text = ABS_HOME_RE.sub("https://busjatri.in/", text)
    text = LOC_HOME_RE.sub("<loc>https://busjatri.in/</loc>", text)
    text = ABS_RE.sub(r"\1", text)
    text = LOC_RE.sub(r"\1\2", text)
    text = PARENT_HOME_RE.sub('href="../"', text)
    text = PARENT_RE.sub(r'href="../\1"', text)
    text = DOT_RE.sub(r'href="\1"', text)
    text = BARE_RE.sub(r'href="\1"', text)
    return text


def normalize_redirects(text: str) -> str:
    out = []
    for line in text.splitlines(keepends=True):
        m = REDIR_RE.match(line.rstrip("\n"))
        if m:
            line = m.group(1) + m.group(2) + m.group(3) + ("\n" if line.endswith("\n") else "")
        out.append(line)
    return "".join(out)


def fix_sitemaps() -> int:
    n = 0
    for name in SITEMAPS:
        p = ROOT / name
        if not p.exists():
            print("skip missing sitemap:", name)
            continue
        s = p.read_text(encoding="utf-8")
        before = s.count("<loc>")
        out = normalize(s)
        assert out.count("<loc>") == before, (name, before, out.count("<loc>"))
        assert ".html</loc>" not in out, name
        if out != s:
            p.write_text(out, encoding="utf-8")
            n += 1
        print("sitemap %s: %d locs clean" % (name, before))
    return n


def fix_html_files() -> int:
    files = [
        p for p in ROOT.rglob("*.html")
        if "scripts" not in p.parts and ".github" not in p.parts
    ]
    changed = 0
    for p in files:
        try:
            s = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        out = normalize(s)
        if out != s:
            p.write_text(out, encoding="utf-8")
            changed += 1
    print("html files scanned: %d, changed: %d" % (len(files), changed))
    return changed


def fix_redirects() -> int:
    p = ROOT / "_redirects"
    if not p.exists():
        print("skip missing _redirects")
        return 0
    s = p.read_text(encoding="utf-8")
    out = normalize_redirects(s)
    if out != s:
        p.write_text(out, encoding="utf-8")
        print("_redirects: destinations cleaned")
        return 1
    print("_redirects: already clean")
    return 0


def main() -> int:
    total = fix_sitemaps() + fix_html_files() + fix_redirects()
    print("TOTAL files changed:", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
