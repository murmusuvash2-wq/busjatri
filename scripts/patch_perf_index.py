#!/usr/bin/env python3
"""Perf fix for index.html (busjatri.in).

1. Loads the Google Fonts stylesheet asynchronously (media="print" onload trick)
   so it no longer blocks first paint on slow mobile connections.
2. Removes the duplicated inline <style id="busjatri-ux-polish"> block.

Idempotent: safe to run multiple times. Use --write to modify the file.
Without --write it only reports what it would change (dry run).
"""
import argparse
import re

PATH = 'index.html'
FONT_TAG_RE = re.compile(
    r'<link href="(https://fonts\.googleapis\.com/css2[^"]+)" rel="stylesheet"\s*/>'
)
STYLE_TAG = '<style id="busjatri-ux-polish">'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help='apply changes to file')
    args = ap.parse_args()

    with open(PATH, encoding='utf-8') as f:
        s = f.read()
    orig = s
    changes = []

    # 1) Async Google Fonts + <noscript> fallback
    if 'media="print" onload' not in s:
        m = FONT_TAG_RE.search(s)
        if m:
            href = m.group(1)
            replacement = (
                '<link href="{0}" rel="stylesheet" media="print" '
                'onload="this.media=\'all\'" />\n'
                '  <noscript><link href="{0}" rel="stylesheet" /></noscript>'
            ).format(href)
            s = s[:m.start()] + replacement + s[m.end():]
            changes.append('google fonts -> async (non-render-blocking)')

    # 2) Remove the second copy of the inline style block, if duplicated
    if s.count(STYLE_TAG) >= 2:
        first = s.find(STYLE_TAG)
        second = s.find(STYLE_TAG, first + 1)
        end = s.find('</style>', second)
        if end != -1:
            end += len('</style>')
            s = s[:second] + s[end:]
            changes.append('duplicate inline <style> block removed')

    if s == orig:
        print('No changes needed (already patched).')
        return

    print('Changes:')
    for c in changes:
        print(' - ' + c)
    if args.write:
        with open(PATH, 'w', encoding='utf-8') as f:
            f.write(s)
        print('WROTE ' + PATH)
    else:
        print('(dry run - use --write to apply)')


if __name__ == '__main__':
    main()
