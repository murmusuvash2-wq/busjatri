#!/usr/bin/env python3
"""
Generate PWA icons for busjatri.in with PIL (no network needed).

Design: amber (#b8791f) rounded square, white front-view bus glyph
(route board, windshield with divider, headlights, wheels). Outputs:
  icons/icon-192.png          192x192  (purpose any)
  icons/icon-512.png          512x512  (purpose any)
  icons/icon-maskable-192.png 192x192  (full-bleed, safe zone)
  icons/icon-maskable-512.png 512x512  (full-bleed, safe zone)
  apple-touch-icon.png        180x180  (full square, no transparency)

Idempotent: overwrites outputs on every run. Backslash-free source.
"""

import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AMBER = (184, 121, 31, 255)
WHITE = (255, 255, 255, 255)


def draw_bus(d, s):
    """Front-view bus glyph on a square canvas of side s (percent coords)."""
    def px(x):
        return round(x * s / 100.0)

    d.rounded_rectangle([px(37), px(17), px(63), px(24)], radius=px(2), fill=WHITE)
    d.rounded_rectangle([px(16), px(27), px(84), px(72)], radius=px(5), fill=WHITE)
    d.rounded_rectangle([px(23), px(34), px(77), px(56)], radius=px(3), fill=AMBER)
    d.rectangle([px(49), px(34), px(51), px(56)], fill=WHITE)
    d.rounded_rectangle([px(22), px(61), px(34), px(68)], radius=px(2), fill=AMBER)
    d.rounded_rectangle([px(66), px(61), px(78), px(68)], radius=px(2), fill=AMBER)
    d.ellipse([px(23), px(71), px(41), px(89)], fill=WHITE)
    d.ellipse([px(59), px(71), px(77), px(89)], fill=WHITE)
    d.ellipse([px(27), px(75), px(37), px(85)], fill=AMBER)
    d.ellipse([px(63), px(75), px(73), px(85)], fill=AMBER)


def make_icon(size, maskable):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if maskable:
        # full-bleed square for the maskable safe zone; smaller glyph
        d.rounded_rectangle([0, 0, size - 1, size - 1], radius=0, fill=AMBER)
        glyph = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glyph)
        draw_bus(gd, size)
        small = round(size * 0.76)
        glyph = glyph.resize((small, small), Image.LANCZOS)
        off = round((size - small) / 2)
        img.alpha_composite(glyph, (off, off))
    else:
        r = round(size * 0.21)
        d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=AMBER)
        draw_bus(d, size)
    return img


def main():
    outdir = os.path.join(ROOT, 'icons')
    os.makedirs(outdir, exist_ok=True)

    for size in (192, 512):
        make_icon(size, False).save(os.path.join(outdir, 'icon-%d.png' % size))
        make_icon(size, True).save(os.path.join(outdir, 'icon-maskable-%d.png' % size))
        print('icons/icon-%d.png + maskable written' % size)

    # apple-touch-icon: opaque full square (iOS rounds it itself)
    bg = Image.new('RGBA', (180, 180), AMBER)
    bg.alpha_composite(make_icon(180, False))
    bg.convert('RGB').save(os.path.join(ROOT, 'apple-touch-icon.png'))
    print('apple-touch-icon.png written')
    print('DONE')


if __name__ == '__main__':
    main()
