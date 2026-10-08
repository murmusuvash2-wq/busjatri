#!/usr/bin/env python3
"""add_operator_to_titles.py — put the operator name into route-page <title>.

Search Console shows people search things like
    "asansol to kolkata sbstc bus timetable"
    "sbstc durgapur to kolkata time table today"
but our route pages were titled
    "Asansol to Kolkata Bus Time Table | BusJatri"
— no operator, so the snippet never matched the query. This rewrites

    <title>{A} to {B} Bus Time Table | BusJatri</title>

into

    <title>{A} to {B} Bus Time Table ({Operator}) | BusJatri</title>

using the operator already listed in the page's own meta description
("... Run by SBSTC, Shyamoli Paribahan. ...").

Idempotent: only pages still carrying the exact old title are touched, and a
page whose title already contains "(...)" is skipped. Safe to re-run.
"""

import os
import re
import glob

TITLE_OLD = re.compile(
    r'<title>([^<]*?) to ([^<]*?) Bus Time Table \| BusJatri</title>'
)
RUNBY = re.compile(r'Run by ([^.]+)\.')
SITE = 'BusJatri'


def operator_for(html):
    m = RUNBY.search(html)
    if not m:
        return None
    ops = [o.strip() for o in m.group(1).split(',')]
    ops = [o for o in ops if o and o not in ('—', '-')]
    return ops[0] if ops else None


def main():
    changed = skipped = 0
    for path in sorted(glob.glob('bus-time-table/*.html')):
        html = open(path, encoding='utf-8').read()
        m = TITLE_OLD.search(html)
        if not m:
            skipped += 1
            continue
        op = operator_for(html)
        if not op:
            skipped += 1
            continue
        origin, dest = m.group(1), m.group(2)
        new_title = f'{origin} to {dest} Bus Time Table ({op}) | {SITE}'
        old_title = f'{origin} to {dest} Bus Time Table | {SITE}'
        out = html.replace(
            f'<title>{old_title}</title>', f'<title>{new_title}</title>', 1
        )
        # keep social titles in sync where they mirror the page title
        out = out.replace(
            f'<meta property="og:title" content="{old_title}">',
            f'<meta property="og:title" content="{new_title}">',
        )
        out = out.replace(
            f'<meta name="twitter:title" content="{old_title}">',
            f'<meta name="twitter:title" content="{new_title}">',
        )
        if out != html:
            open(path, 'w', encoding='utf-8').write(out)
            changed += 1
    print(f'route titles updated: {changed}   skipped: {skipped}')


if __name__ == '__main__':
    main()
