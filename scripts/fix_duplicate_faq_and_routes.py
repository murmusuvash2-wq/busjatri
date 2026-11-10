#!/usr/bin/env python3
"""fix_duplicate_faq_and_routes.py

DEPRECATED for FAQ removal.

History: this script used to strip the redundant English-only FAQ block
(<section class="bj-faq">) whenever the bilingual generator FAQ was present.

That direction was reversed: the bilingual block is no longer rendered at all
(see gen_seo_pages.py - the route-guide section carries the visible FAQ), so
<b>the bj-faq block is now the single FAQ we want to keep</b>. Running the old
removal logic would delete every page's FAQ.

The script is kept only for the related-routes heading repair, which is still
useful. It performs NO FAQ removal.
"""

import glob
import os
import re


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(root, 'bus-time-table')
    html_files = glob.glob(os.path.join(target_dir, '*.html'))

    print(f'Auditing {len(html_files)} pages in {target_dir}...')

    h1_en_re = re.compile(
        r'<h1[^>]*>.*?<span class="label-en">(.*?)(?:<span class="arr"[^>]*>.*?</span>|&rarr;|→)(.*?)</span>',
        re.S,
    )

    n_routes_cleaned = 0
    n_modified = 0

    for f in html_files:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            orig_content = fp.read()

        content = orig_content
        changed = False

        if 'class="related-routes"' in content:
            if re.search(r'[\w]+[\u0980-\u09ff]+\s*\|', content) or 'Related routes &amp; operators' in content:
                m = h1_en_re.search(content)
                if m:
                    orig_name = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                    dest_name = re.sub(r'<[^>]+>', '', m.group(2)).strip()

                    if orig_name and dest_name:
                        def sub_h2(match):
                            return (
                                f'<section class="related-routes"{match.group(1)}><h2{match.group(2)}>'
                                f'Related routes &amp; operators — {orig_name} to {dest_name}</h2>'
                            )

                        new_content = re.sub(
                            r'<section class="related-routes"([^>]*)><h2([^>]*)>Related routes &amp; operators — .*?</h2>',
                            sub_h2,
                            content,
                        )
                        if new_content != content:
                            content = new_content
                            n_routes_cleaned += 1
                            changed = True

        if changed and content != orig_content:
            with open(f, 'w', encoding='utf-8') as fp:
                fp.write(content)
            n_modified += 1

    print('Done! Summary:')
    print('  Duplicate FAQs removed: 0 (disabled - bj-faq is the FAQ we keep)')
    print(f'  Corrupted related routes headings fixed: {n_routes_cleaned}')
    print(f'  Total files updated: {n_modified}')


if __name__ == '__main__':
    main()
