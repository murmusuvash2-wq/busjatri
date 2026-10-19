#!/usr/bin/env python3
"""fix_duplicate_faq_and_routes.py

1. Cleans redundant duplicate English-only FAQ blocks (<section class="bj-faq">)
   on pages that already have the modern bilingual FAQ section.
2. Cleans up string corruption in Related Routes headings and reverse chips where
   Bengali script got accidentally concatenated into English place names.
"""

import glob
import html
import os
import re
import sys

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(root, 'bus-time-table')
    html_files = glob.glob(os.path.join(target_dir, '*.html'))

    print(f'Auditing and cleaning {len(html_files)} pages in {target_dir}...')

    bj_faq_re = re.compile(r'<style>\.bj-faq\{.*?</style>\s*<section class=\"bj-faq\"[^>]*>.*?</section>\s*', re.S)
    h1_en_re = re.compile(r'<h1[^>]*>.*?<span class=\"label-en\">(.*?)(?:<span class=\"arr\"[^>]*>.*?</span>|&rarr;|→)(.*?)</span>', re.S)

    n_faq_cleaned = 0
    n_routes_cleaned = 0
    n_modified = 0

    for idx, f in enumerate(html_files):
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            orig_content = fp.read()

        content = orig_content
        changed = False

        # 1. Remove duplicate bj-faq if modern seo-section FAQ exists
        if 'class="seo-section"' in content and 'Frequently Asked Questions' in content:
            if 'class="bj-faq"' in content:
                new_content = bj_faq_re.sub('', content)
                if new_content != content:
                    content = new_content
                    n_faq_cleaned += 1
                    changed = True

        # 2. Fix corrupted related-routes headings / chips
        if 'class="related-routes"' in content:
            # Check if there is corruption (Bengali character concatenated after Latin text or before '|')
            if re.search(r'[\w]+[\u0980-\u09ff]+\s*\|', content) or 'Related routes &amp; operators' in content:
                m = h1_en_re.search(content)
                if m:
                    orig_name = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                    dest_name = re.sub(r'<[^>]+>', '', m.group(2)).strip()

                    if orig_name and dest_name:
                        # Fix H2 in related-routes
                        def sub_h2(match):
                            return f'<section class="related-routes"{match.group(1)}><h2{match.group(2)}>Related routes &amp; operators — {orig_name} to {dest_name}</h2>'

                        new_content = re.sub(
                            r'<section class="related-routes"([^>]*)><h2([^>]*)>Related routes &amp; operators — .*?</h2>',
                            sub_h2,
                            content
                        )
                        if new_content != content:
                            content = new_content
                            n_routes_cleaned += 1
                            changed = True

                        # Fix reverse chip text
                        def sub_rel(match):
                            sec = match.group(0)
                            def fix_chip(cm):
                                href = cm.group(1)
                                text = cm.group(2)
                                if '|' in text and '→' in text:
                                    return f'<a class="rel-chip" href="{href}">{dest_name} → {orig_name}</a>'
                                return cm.group(0)
                            return re.sub(r'<a class="rel-chip" href="([^"]+)">([^<]+)</a>', fix_chip, sec)

                        new_content = re.sub(r'<section class="related-routes"[^>]*>.*?</section>', sub_rel, content, flags=re.S)
                        if new_content != content:
                            content = new_content
                            changed = True

        if changed and content != orig_content:
            with open(f, 'w', encoding='utf-8') as fp:
                fp.write(content)
            n_modified += 1

    print(f'Done! Summary:')
    print(f'  Duplicate FAQs removed: {n_faq_cleaned}')
    print(f'  Corrupted related routes headings/chips fixed: {n_routes_cleaned}')
    print(f'  Total files updated: {n_modified}')

if __name__ == '__main__':
    main()
