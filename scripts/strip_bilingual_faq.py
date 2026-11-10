#!/usr/bin/env python3
"""strip_bilingual_faq.py

Each route page currently renders TWO FAQ sections:

  A) the bilingual one emitted by gen_seo_pages.py
     <section class="seo-section"> <h3>Frequently Asked Questions / সাধারণ প্রশ্নোত্তর</h3> ...
  B) the route-guide one emitted by scripts/content/route_content.py
     <section class="bj-faq"> <h2>Frequently Asked Questions — A to B</h2> ...

We keep (B) — it lives inside the "About ... Bus Route Guide" section together
with distance, travel time and tips — and drop (A).

SAFETY RULE: block (A) is removed ONLY when block (B) is present on the same
page. A page is never left without a FAQ.

The FAQPage JSON-LD is emitted separately from `faqs` in gen_seo_pages.py and
is not touched by this script.

Idempotent: re-running changes nothing.
"""

import glob
import os
import re
import sys


BLOCK_A = re.compile(
    r'<section class="seo-section">\s*'
    r'<h3 class="section-title">\s*'
    r'<span class="label-en">Frequently Asked Questions</span>'
    r'.*?</section>\s*',
    re.S,
)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(root, 'bus-time-table')
    files = sorted(glob.glob(os.path.join(target, '*.html')))
    print(f'Scanning {len(files)} pages in {target}...')

    stripped = 0
    skipped_no_b = 0
    modified = 0

    for f in files:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            html = fp.read()

        if 'class="bj-faq"' not in html:
            # no route-guide FAQ on this page -> keep whatever FAQ it has
            skipped_no_b += 1
            continue

        new = BLOCK_A.sub('', html, count=1)
        if new != html:
            with open(f, 'w', encoding='utf-8') as fp:
                fp.write(new)
            stripped += 1
            modified += 1

    print('Summary:')
    print(f'  bilingual FAQ blocks removed      : {stripped}')
    print(f'  pages kept as-is (no route-guide) : {skipped_no_b}')
    print(f'  files written                     : {modified}')

    # hard check: no page may carry two FAQ headings now
    bad = []
    for f in files:
        h = open(f, encoding='utf-8', errors='ignore').read()
        if h.count('Frequently Asked Questions') >= 2:
            bad.append(os.path.basename(f))
    if bad:
        print(f'ERROR: {len(bad)} pages still have 2+ FAQ headings: {bad[:5]}')
        sys.exit(1)
    print('OK - every route page has at most one FAQ heading')


if __name__ == '__main__':
    main()
