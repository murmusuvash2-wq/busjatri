#!/usr/bin/env python3
"""Kolkata umbrella stands: Kolkata (Esplanade) / (Karunamoyee) / (Santragachi).

Restores buses-from-karunamoyee.html and buses-from-santragachi.html and
renames the main Kolkata stand page display to Kolkata (Esplanade).

Route pages are origin-specific (no alias merging), so each umbrella page
shows ONLY buses whose data origin matches:

  kolkata      -> origins Kolkata + Esplanade  (main Kolkata page)
  karunamoyee  -> origins Karunamoyee
  santragachi  -> origins Santragachi

Steps (idempotent):
  1. patch gen_stand_v2.py  (UMBRELLA table, display_name, stand_buses,
     bus-own-origin link preference in destination_groups)
  2. patch gen_btt_v2.py    (cards show card_name)
  3. regenerate the 3 stand pages + the BTT hub
  4. sitemap.xml: add the 2 restored URLs
  5. _redirects: drop the karunamoyee / santragachi 301 rules
     (esplanade -> kolkata stays: that page remains deleted)

No backslashes anywhere in this file (byte-exact re-typing safety).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'scripts')
OUTDIR = os.path.join(ROOT, 'bus-time-table')

NL = chr(10)
Q = chr(34)   # double quote
TRIPLE = Q * 3

UMBRELLA_BLOCK = (
    '# Kolkata-area stands shown as umbrella entries Kolkata (<stand>).' + NL +
    '# filename-base -> (display name, exact origin names whose buses belong)' + NL +
    'UMBRELLA = {' + NL +
    '    ' + Q + 'kolkata' + Q + ': (' + Q + 'Kolkata (Esplanade)' + Q + ', (' + Q + 'kolkata' + Q + ', ' + Q + 'esplanade' + Q + ')),' + NL +
    '    ' + Q + 'karunamoyee' + Q + ': (' + Q + 'Kolkata (Karunamoyee)' + Q + ', (' + Q + 'karunamoyee' + Q + ',)),' + NL +
    '    ' + Q + 'santragachi' + Q + ': (' + Q + 'Kolkata (Santragachi)' + Q + ', (' + Q + 'santragachi' + Q + ',)),' + NL +
    '}' + NL + NL +
    'def card_name(stand):' + NL +
    '    ' + TRIPLE + 'Card/label name for a stand (umbrella display for Kolkata area).' + TRIPLE + NL +
    '    key = g.slug(stand)' + NL +
    '    if key in UMBRELLA:' + NL +
    '        return UMBRELLA[key][0]' + NL +
    '    return stand' + NL + NL
)

DISPLAY_ANCHOR = '    ' + TRIPLE + Q + 'Bankura' + Q + ' -> ' + Q + 'Bankura Bus Stand' + Q + '; ' + Q + 'Howrah Station' + Q + ' unchanged.' + TRIPLE + NL
DISPLAY_INSERT = (
    DISPLAY_ANCHOR +
    '    key = g.slug(stand)' + NL +
    '    if key in UMBRELLA:' + NL +
    '        return UMBRELLA[key][0]' + NL
)

BUSES_ANCHOR = '    return [b for b in g.BUSES if v2.place_matches_strict(b.get(' + Q + 'origin' + Q + '), stand)]'
BUSES_NEW = (
    '    key = g.slug(stand)' + NL +
    '    if key in UMBRELLA:' + NL +
    '        names = set(n.strip().lower() for n in UMBRELLA[key][1])' + NL +
    '        out = []' + NL +
    '        for b in g.BUSES:' + NL +
    '            o = (g.clean_text(b.get(' + Q + 'origin' + Q + ')) or ' + Q + Q + ').strip().lower()' + NL +
    '            if o in names:' + NL +
    '                out.append(b)' + NL +
    '        return out' + NL +
    '    return [b for b in g.BUSES if v2.place_matches_strict(b.get(' + Q + 'origin' + Q + '), stand)]'
)

LINK_ANCHOR = (
    '        for o, t in routes:' + NL +
    '            if v2.place_matches_strict(t, d) or v2.place_matches_strict(d, t):' + NL +
    '                resolved = t' + NL +
    '                origin = o' + NL +
    '                break'
)
LINK_NEW = (
    '        bo = (g.clean_text(b.get(' + Q + 'origin' + Q + ')) or ' + Q + Q + ').lower()' + NL +
    '        for o, t in routes:' + NL +
    '            if o.strip().lower() == bo and (v2.place_matches_strict(t, d) or v2.place_matches_strict(d, t)):' + NL +
    '                resolved = t' + NL +
    '                origin = o' + NL +
    '                break' + NL +
    '        if resolved is None:' + NL +
    '            for o, t in routes:' + NL +
    '                if v2.place_matches_strict(t, d) or v2.place_matches_strict(d, t):' + NL +
    '                    resolved = t' + NL +
    '                    origin = o' + NL +
    '                    break'
)


def patch(path, pairs):
    with open(path, encoding='utf-8') as fh:
        src = fh.read()
    for old, new in pairs:
        if new in src and old not in src:
            continue
        if src.count(old) != 1:
            raise SystemExit('anchor not unique in {}: {!r} (count {})'.format(
                os.path.basename(path), old[:60], src.count(old)))
        src = src.replace(old, new)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(src)


def main():
    # ---- 1. gen_stand_v2.py ----
    patch(os.path.join(SCRIPTS, 'gen_stand_v2.py'), [
        ('def display_name(stand):' + NL, UMBRELLA_BLOCK + 'def display_name(stand):' + NL),
        (DISPLAY_ANCHOR, DISPLAY_INSERT),
        (BUSES_ANCHOR, BUSES_NEW),
        (LINK_ANCHOR, LINK_NEW),
    ])
    print('gen_stand_v2.py patched')

    # ---- 2. gen_btt_v2.py ----
    patch(os.path.join(SCRIPTS, 'gen_btt_v2.py'), [
        ('from gen_stand_v2 import stand_buses, destination_groups, discover_stands, display_name',
         'from gen_stand_v2 import stand_buses, destination_groups, discover_stands, display_name, card_name'),
        ('name=g.esc(name),', 'name=g.esc(card_name(name)),'),
    ])
    print('gen_btt_v2.py patched')

    # ---- 3. regenerate the 3 pages + BTT (fresh process, patched modules) ----
    code = (
        'import os, sys' + NL +
        'sys.path.insert(0, ' + repr(SCRIPTS) + ')' + NL +
        'import gen_stand_v2 as s2' + NL +
        "for base in ('kolkata', 'karunamoyee', 'santragachi'):" + NL +
        '    fname, page = s2.generate_stand_page_v2(base)' + NL +
        "    with open(os.path.join(" + repr(OUTDIR) + ", fname), 'w', encoding='utf-8') as fh:" + NL +
        '        fh.write(page)' + NL +
        '    buses = s2.stand_buses(base)' + NL +
        "    print(fname, len(buses), 'buses', len(page) // 1024, 'KB')"
    )
    subprocess.run([sys.executable, '-c', code], check=True)
    subprocess.run([sys.executable, os.path.join(SCRIPTS, 'gen_btt_v2.py')],
                   cwd=ROOT, check=True)

    # ---- 4. sitemap.xml: add the 2 restored URLs ----
    SM = os.path.join(ROOT, 'sitemap.xml')
    with open(SM, encoding='utf-8') as fh:
        sm = fh.read()
    i = sm.find('buses-from-kolkata.html</loc>')
    if i == -1:
        raise SystemExit('kolkata block not found in sitemap.xml')
    start = sm.rfind('<url>', 0, i)
    end = sm.find('</url>', i) + len('</url>')
    while end < len(sm) and sm[end] in chr(13) + NL:
        end += 1
    kblock = sm[start:end]
    add = ''
    for base in ('karunamoyee', 'santragachi'):
        if 'buses-from-' + base + '.html</loc>' in sm:
            continue
        nb = kblock.replace('buses-from-kolkata.html', 'buses-from-' + base + '.html')
        li = nb.find('<lastmod>')
        if li != -1:
            lj = nb.find('</lastmod>', li)
            nb = nb[:li + len('<lastmod>')] + '2026-09-23' + nb[lj:]
        add += nb + NL
    if add:
        sm = sm[:end] + NL + add.rstrip(NL) + sm[end:]
        with open(SM, 'w', encoding='utf-8') as fh:
            fh.write(sm)
    print('sitemap.xml: restored URLs added')

    # ---- 5. _redirects: drop karunamoyee / santragachi rules ----
    RD = os.path.join(ROOT, '_redirects')
    with open(RD, encoding='utf-8') as fh:
        lines = fh.read().split(NL)
    keep = [l for l in lines if 'buses-from-karunamoyee' not in l and 'buses-from-santragachi' not in l]
    if len(keep) != len(lines):
        with open(RD, 'w', encoding='utf-8') as fh:
            fh.write(NL.join(keep))
        print('_redirects: removed', len(lines) - len(keep), 'rules')
    else:
        print('_redirects: nothing to remove')

    print('kolkata umbrella complete')


if __name__ == '__main__':
    main()
