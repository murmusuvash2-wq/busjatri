#!/usr/bin/env python3
"""Wrap place-name route labels in label-en/label-bn spans so the site
language toggle switches them. Idempotent: already-wrapped labels are skipped.
Usage: python3 fix_bilingual.py <file.html> [...]
"""
import re, json, sys, pathlib

DICT = json.load(open(pathlib.Path(__file__).parent / 'bn_dict.json'))

ARROW = r'<span class="arr">→</span>'


def bn(name):
    n = re.sub(r'\s+', ' ', name).strip()
    if n in DICT:
        return DICT[n]
    parts = n.split()
    if parts and all(p in DICT for p in parts):
        return ' '.join(DICT[p] for p in parts)
    return None


def wrap_pair(en_from, en_to, inner=None):
    """Return label-en/label-bn HTML for 'X → Y'. inner = original EN html."""
    bf, bt = bn(en_from), bn(en_to)
    if not bf or not bt:
        return None
    en_html = inner if inner is not None else f'{en_from} {ARROW} {en_to}'
    bn_html = f'{bf} {ARROW} {bt}'
    return (f'<span class="label-en">{en_html}</span>'
            f'<span class="label-bn">{bn_html}</span>')


def already(block):
    return 'label-en' in block or 'label-bn' in block


def split_arrow(inner):
    """Split an inner html like 'Digha <span class="arr">→</span> Kolkata'."""
    parts = re.split(r'<span class="arr">→</span>', inner)
    if len(parts) != 2:
        return None
    return parts[0].strip(), parts[1].strip()


def fix_h1(h):
    """Wrap <h1>X → Y</h1>."""
    def r(m):
        inner = m.group(1)
        if already(inner):
            return m.group(0)
        sp = split_arrow(inner)
        if not sp:
            return m.group(0)
        pair = wrap_pair(sp[0], sp[1], inner=inner)
        return f'<h1>{pair}</h1>' if pair else m.group(0)
    return re.sub(r'<h1[^>]*>(.*?)</h1>', r, h, flags=re.S)


def fix_crumb(h):
    """Wrap the <span>X → Y</span> (with nested arr span) inside div.crumbs."""
    def r(m):
        block = m.group(0)
        if already(block):
            return block
        def rs(mm):
            inner = mm.group(1)
            if already(inner):
                return mm.group(0)
            sp = split_arrow(inner)
            if not sp:
                return mm.group(0)
            pair = wrap_pair(sp[0], sp[1], inner=inner)
            return f'<span>{pair}</span>' if pair else mm.group(0)
        # match a <span> whose content contains the arrow span
        h2 = re.sub(r'<span>((?:(?!</span>).)*?<span class="arr">→</span>(?:(?!</span>).)*?)</span>',
                    rs, block)
        # also handle a plain-text arrow inside a bare <span>
        def rs_plain(mm):
            inner = mm.group(1)
            if already(inner) or '→' not in inner:
                return mm.group(0)
            a, b = [x.strip() for x in inner.split('→', 1)]
            pair = wrap_pair(a, b, inner=inner)
            return f'<span>{pair}</span>' if pair else mm.group(0)
        return re.sub(r'<span>([A-Za-z0-9 .()]+ → [A-Za-z0-9 .()]+)</span>', rs_plain, h2)
    return re.sub(r'<div class="crumbs">.*?</div>', r, h, flags=re.S)


def fix_cards(h):
    """Wrap route cards: <span class="rt">X <arr> Y</span> (nested arr span)."""
    def r(m):
        inner = m.group(1)
        if already(inner):
            return m.group(0)
        sp = split_arrow(inner)
        if not sp:
            return m.group(0)
        pair = wrap_pair(sp[0], sp[1], inner=inner)
        return f'<span class="rt">{pair}</span>' if pair else m.group(0)
    # anchor on the closing followed by the sibling <span class="meta">
    h = re.sub(r'<span class="rt">((?:(?!</span>).)*?<span class="arr">→</span>(?:(?!</span>).)*?)</span>\s*(?=<span class="meta">)',
               r, h)
    return h


def process(path):
    p = pathlib.Path(path)
    h = p.read_text(encoding='utf-8')
    orig = h
    h = fix_h1(h)
    h = fix_crumb(h)
    h = fix_cards(h)
    if h != orig:
        p.write_text(h, encoding='utf-8')
        return True
    return False


if __name__ == '__main__':
    changed = 0
    for f in sys.argv[1:]:
        if process(f):
            changed += 1
    print(f'changed {changed}/{len(sys.argv)-1} files')
