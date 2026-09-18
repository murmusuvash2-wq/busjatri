#!/usr/bin/env python3
"""SEO extras from the 18 Sept 2026 audit.

1. scripts/gen_seo_pages.py: route pages get og:image + twitter:card
   (previously only the homepage had them - link previews on FB/WhatsApp
   showed no image for the 2,691 route pages).
2. about.html: second H1 becomes H2 (one H1 per page).

Idempotent. All-or-nothing per file.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv
applied = []


def edit(path, pairs, label):
    src = path.read_text(encoding="utf-8")
    out = src
    for old, new in pairs:
        if new in out and old not in out:
            continue
        n = out.count(old)
        if n != 1:
            raise SystemExit(f"ABORT ({label}): anchor found {n}x: {old[:60]!r}")
        out = out.replace(old, new, 1)
    if out != src:
        if not DRY:
            path.write_text(out, encoding="utf-8")
        applied.append(label)


gsp = ROOT / "scripts" / "gen_seo_pages.py"
edit(gsp, [
    (
        '<meta property="og:url" content="{esc(canonical)}">\n'
        '<meta name="theme-color" content="#b8791f">',
        '<meta property="og:url" content="{esc(canonical)}">\n'
        '<meta property="og:image" content="https://busjatri.in/og-image.png">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<meta name="twitter:title" content="{esc(title)}">\n'
        '<meta name="twitter:description" content="{esc(description)}">\n'
        '<meta name="theme-color" content="#b8791f">',
    ),
], "scripts/gen_seo_pages.py (og:image + twitter card)")

about = ROOT / "about.html"
edit(about, [
    (
        '<h1 style="font-size:clamp(1.2rem,3.5vw,1.6rem);margin-top:20px">কৃতজ্ঞতা ও তথ্যসূত্র</h1>',
        '<h2 style="font-size:clamp(1.2rem,3.5vw,1.6rem);margin-top:20px">কৃতজ্ঞতা ও তথ্যসূত্র</h2>',
    ),
], "about.html (H1 -> H2)")

print("applied:", applied if applied else "nothing (all already patched)")
print("dry run" if DRY else "written")
