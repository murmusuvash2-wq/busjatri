#!/usr/bin/env python3
"""add_operator_badges.py — give every operator page the same hero design.

The operator pages (SBSTC / NBSTC / WBTC / Shyamoli Paribahan / Volvo AC) should
look identical: an orange .hero-badge pill, then the title, then an English
description line (and the existing Bengali line). gen_operator_pages.py emits a
plain h1, and only SBSTC gets the badge (via its special-case toggle), so this
brings the rest up to the same design.

Idempotent: a page that already carries .hero-badge is left untouched, so it is
safe to run after every regeneration.
"""

import glob
import re

BADGE_CSS = (
    '.hero-badge{display:inline-flex;align-items:center;'
    'background:linear-gradient(135deg,#c98a2b,#a13b2e);color:#fffcf4;'
    'font-weight:800;letter-spacing:.08em;border-radius:14px;padding:6px 18px;'
    'font-size:.72em;box-shadow:0 3px 14px rgba(184,121,31,.4);text-transform:uppercase}'
)

# stem -> (badge text, English label after the badge, English description)
PAGES = {
    'sbstc-buses': ('SBSTC', 'Buses',
                    'South Bengal State Transport Corporation — routes, time tables &amp; schedules'),
    'nbstc-buses': ('NBSTC', 'Buses',
                    'North Bengal State Transport Corporation — routes, time tables &amp; schedules'),
    'wbtc-buses': ('WBTC', 'Buses',
                   'West Bengal Transport Corporation — routes, time tables &amp; schedules'),
    'shyamoli-paribahan-buses': ('Shyamoli', 'Paribahan Buses',
                                 'Shyamoli Paribahan — routes, time tables &amp; schedules'),
    'volvo-ac-buses': ('Volvo AC', 'Buses',
                       'Volvo AC buses — routes, time tables &amp; schedules'),
}

H1 = re.compile(
    r'<h1 style="font-size:clamp\(1\.8rem,5vw,2\.5rem\);line-height:1\.2;margin:0">'
    r'(.*?)</h1>\s*'
    r'<div class="bn-line only-bn" style="color:var\(--ink-dim\);margin-top:6px">(.*?)</div>',
    re.S,
)


def main():
    changed = skipped = 0
    for stem, (badge, label, desc) in PAGES.items():
        path = f'bus-time-table/{stem}.html'
        try:
            page = open(path, encoding='utf-8').read()
        except FileNotFoundError:
            skipped += 1
            continue
        if '.hero-badge' in page:
            skipped += 1
            continue
        m = H1.search(page)
        if not m:
            skipped += 1
            continue
        bn = m.group(2).strip()
        new = (
            '<h1 style="font-size:clamp(1.8rem,5vw,2.5rem);line-height:1.2;margin:0;'
            'display:flex;align-items:center;gap:12px;flex-wrap:wrap">'
            f'<span class="hero-badge">{badge}</span>'
            f'<span class="label-en">{label}</span><span class="label-bn">বাস</span></h1>\n'
            f'<div class="only-en" style="color:var(--ink-dim);margin-top:8px;font-size:14.5px">{desc}</div>\n'
            f'<div class="bn-line only-bn" style="color:var(--ink-dim);margin-top:8px;font-size:14.5px">{bn}</div>'
        )
        page = page.replace(m.group(0), new, 1)
        if BADGE_CSS not in page:
            i = page.find('</style>')
            if i != -1:
                page = page[:i] + BADGE_CSS + page[i:]
        open(path, 'w', encoding='utf-8').write(page)
        changed += 1
    print(f'operator badges added: {changed}   skipped: {skipped}')


if __name__ == '__main__':
    main()
