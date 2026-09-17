#!/usr/bin/env python3
"""Polish every generated route/place page (idempotent):

1. LINK BUS ROWS: the generator emits plain <div class="bus-row"> cards with
   no link, so the flow home -> timetable -> route dead-ends there. This
   wraps each row (when it can be confidently matched to a bus in the data)
   in <a class="bus-row" href="../index.html#/bus/<id>"> so users can reach
   the full stop-by-stop timetable page.
2. DARK MODE TOGGLE: css/seo.css already ships a full `body.dark` palette —
   this adds a small toggle button to the header and remembers the choice
   in localStorage under the same "seo-theme" key the timetable index uses,
   so dark mode stays in sync across all pages.
3. PLACE PAGE DESIGN: buses-from-* pages get their plain dot-separated
   destination paragraph converted to pill-chip links (matching route-page
   chip design) and their popular-route rows get hover polish.
4. ONE STAT BOX: place/operator pages merge the two stat boxes (Listed
   services + Destinations) into a single box.
5. ROUTE MAP TRIM: route pages with many stops get the middle stops
   collapsed into a '+N more' marker so names don't overlap on phones.

Run with no arguments. (rev 2026-09-18b)
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / 'bus-time-table'
DATA = json.loads((ROOT / 'data' / 'busjatri_data.json').read_text(encoding='utf-8'))

TIME_RE = re.compile(r'^(?:PRE\s+)?(\d{1,2})[:.](\d{2})(?:\s*(AM|PM))?$', re.I)

def to_min(t):
    m = TIME_RE.match((t or '').strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    ap = (m.group(3) or '').upper()
    if ap == 'AM':
        h = 0 if h == 12 else h
    elif ap == 'PM':
        h = 12 if h == 12 else h + 12
    if h > 23:
        return None
    v = h * 60 + mi
    return None if v == 0 else v

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', (s or '').lower()).strip('-')

# route-page slug -> up-direction buses
route_buses = {}
for b in DATA['buses']:
    route_buses.setdefault(slug(f"{b.get('origin','')}-to-{b.get('destination','')}"), []).append(b)

ROW_OPEN_RE = re.compile(r'<div class="bus-row">')
DEP_RE = re.compile(r'<div class="dep">\s*([^<]*?)\s*(?:<small>|</div>)')
OP_RE = re.compile(r'<div class="op">\s*([^<\u00b7]*?)\s*(?:\u00b7|<)')

def find_row_end(s, start):
    depth = 1
    for m in re.finditer(r'<div\b|</div>', s[start:]):
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0:
            return start + m.end()
    return -1

def link_rows(s, key):
    buses = route_buses.get(key) or []
    out, pos, linked, total = [], 0, 0, 0
    while True:
        m = ROW_OPEN_RE.search(s, pos)
        if not m:
            out.append(s[pos:])
            break
        row_start = m.start()
        row_end = find_row_end(s, m.end())
        if row_end == -1:
            out.append(s[pos:])
            break
        out.append(s[pos:row_start])
        row = s[row_start:row_end]
        total += 1
        href = None
        if 'data-bjlinked' not in row:
            dm = DEP_RE.search(row)
            om = OP_RE.search(row)
            dep = to_min(dm.group(1)) if dm else None
            op = (om.group(1).strip() if om else '').lower()
            cands = [b for b in buses if dep is not None and to_min(b.get('departure_time')) == dep]
            if len(cands) > 1 and op:
                cands2 = [b for b in cands if op in (b.get('bus_name') or '').lower()]
                if cands2:
                    cands = cands2
            if not cands and dep is not None and op:
                # place/via pages: no route-keyed list; match globally by time+operator
                cands = [b for b in DATA['buses']
                         if to_min(b.get('departure_time')) == dep and op in (b.get('bus_name') or '').lower()]
            if len(cands) >= 1:
                href = '../index.html#/bus/' + cands[0]['id']
        if href:
            new_row = row.replace('<div class="bus-row">', f'<a class="bus-row" href="{href}" data-bjlinked="1">', 1)
            # the row's own closing tag is the last </div> of the row
            k = new_row.rfind('</div>')
            new_row = new_row[:k] + '</a>' + new_row[k + 6:]
            out.append(new_row)
            linked += 1
        else:
            out.append(row)
        pos = row_end
    return ''.join(out), linked, total

THEME_BTN = ('<button id="bjThemeBtn" aria-label="Toggle dark mode" '
             'style="background:var(--surface,#fffcf4);border:1px solid var(--line,#ccc);border-radius:999px;'
             'padding:6px 12px;cursor:pointer;font-weight:600;color:var(--ink-dim,#665);font-size:13px;'
             'font-family:inherit;line-height:1.2">\u25d0</button>')
LINK_CSS = '<style>a.bus-row,a.bus-row:visited{color:inherit;text-decoration:none}</style>'
PLACE_CSS = '<style>.bj-pop-row{transition:background .15s}.bj-pop-row:hover{background:var(--amber-soft)}.bj-pop-row span:first-child{font-weight:600}.bj-pop-row:last-of-type{border-bottom-color:transparent}</style>'
THEME_JS = ('<script>(function(){try{var b=document.getElementById("bjThemeBtn");if(!b)return;'
            'if(localStorage.getItem("seo-theme")==="dark"){document.body.classList.add("dark");b.textContent="\\u2600";}'
            'b.addEventListener("click",function(){var d=document.body.classList.toggle("dark");'
            'localStorage.setItem("seo-theme",d?"dark":"light");b.textContent=d?"\\u2600":"\\u25d0";});}catch(e){}})();</script>')

AMP = chr(38)
def esc_h(s):
    return (s or '').replace(AMP, AMP + 'amp;').replace('<', AMP + 'lt;').replace('>', AMP + 'gt;')

DEST_P_RE = re.compile(r'<p style="\s*line-height:1\.9;\s*color:var\(--ink-dim\);\s*">\s*([^<]+?)\s*</p>', re.S)
POP_ROW_RE = re.compile(r'<a href="([^"]+)"(\s+)style="([^"]*justify-content:space-between[^"]*)"')

def beautify_place_page(s, stem, stems):
    """Place pages: turn the plain dot-separated destination paragraph into
    pill-chip links (route-page design language) and class up the popular
    route rows for hover polish."""
    changed = False
    m = DEST_P_RE.search(s)
    if m:
        place = stem[len('buses-from-'):] if stem.startswith('buses-from-') else None
        entries = [e.strip() for e in m.group(1).split('\u00b7') if e.strip()]
        chips = []
        for i, e in enumerate(entries):
            cm = re.match(r'^(.*?)\s*\((\d+)\)$', e)
            name, cnt = (cm.group(1), cm.group(2)) if cm else (e, None)
            label = f'{name} ({cnt})' if cnt else name
            style_i = f' style="--i:{min(i, 15)}"'
            href = None
            if place:
                target = f'{place}-to-{slug(name)}'
                if target in stems:
                    href = target + '.html'
            if href:
                chips.append(f'<a class="via-chip"{style_i} href="{href}">{esc_h(label)}</a>')
            else:
                chips.append(f'<span class="via-chip"{style_i}>{esc_h(label)}</span>')
        chiprow = ('<div class="chip-row" aria-label="All destinations">'
                   + ''.join(chips) + '</div>')
        s = s[:m.start()] + chiprow + s[m.end():]
        changed = True
    s2 = POP_ROW_RE.sub(lambda mm: f'<a href="{mm.group(1)}"{mm.group(2)}class="bj-pop-row" style="{mm.group(3)}"', s)
    if s2 != s:
        s = s2
        changed = True
    return s, changed

STATS_RE = re.compile(
    r'<section style="\s*display:flex;\s*gap:10px;\s*flex-wrap:wrap;\s*margin-bottom:32px;?\s*">\s*'
    r'<div style="\s*flex:1 1 170px;\s*background:var\(-\-panel\);\s*border:1px solid var\(-\-border\);\s*border-radius:14px;\s*padding:15px;?\s*">\s*'
    r'<div style="font-size:12px;color:var\(-\-ink-dim\)">\s*([^<]+?)\s*</div>\s*'
    r'<strong[^>]*>\s*([^<]+?)\s*</strong>\s*</div>\s*'
    r'<div style="\s*flex:1 1 170px;\s*background:var\(-\-panel\);\s*border:1px solid var\(-\-border\);\s*border-radius:14px;\s*padding:15px;?\s*">\s*'
    r'<div style="font-size:12px;color:var\(-\-ink-dim\)">\s*([^<]+?)\s*</div>\s*'
    r'<strong[^>]*>\s*([^<]+?)\s*</strong>\s*</div>\s*</section>', re.S)

ONE_BOX_T = ('<section style="display:flex;gap:30px;flex-wrap:wrap;margin-bottom:32px;'
             'background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:15px 18px">'
             '<div><div style="font-size:12px;color:var(--ink-dim)">{l1}</div>'
             '<strong style="font-size:1.25rem">{v1}</strong></div>'
             '<div><div style="font-size:12px;color:var(--ink-dim)">{l2}</div>'
             '<strong style="font-size:1.25rem">{v2}</strong></div>'
             '</section>')

def merge_stats(s):
    """Place/operator pages: merge the two stat boxes into a single box."""
    m = STATS_RE.search(s)
    if not m:
        return s, False
    box = ONE_BOX_T.format(l1=m.group(1), v1=m.group(2), l2=m.group(3), v2=m.group(4))
    return s[:m.start()] + box + s[m.end():], True

RM_STOP_RE = re.compile(r'<div class="rm-stop[^">]*">.*?</div></div>', re.S)

def trim_routemap(s):
    """Route map: with many stops the names overlap on phones. Keep the first
    4 and last 2 stops and collapse the middle into a '+N more' marker."""
    if 'rm-dot" style="opacity:.35' in s:  # already trimmed (idempotency guard)
        return s, False
    stops = RM_STOP_RE.findall(s)
    if len(stops) <= 7:
        return s, False
    more = len(stops) - 6
    marker = ('<div class="rm-stop"><div class="rm-dot" style="opacity:.35;border-style:dashed"></div>'
              f'<div class="rm-name" style="color:var(--ink-dim)">+{more} more</div></div>')
    keep = stops[:4] + [marker] + stops[-2:]
    inner_old = ''.join(stops)
    inner_new = ''.join(keep)
    i = s.find(inner_old)
    if i == -1:
        return s, False
    return s[:i] + inner_new + s[i + len(inner_old):], True

def main():
    n_pages = n_linked = n_rows = 0
    stems = None
    for p in sorted(PAGES.glob('*.html')):
        if p.name == 'index.html':
            continue
        s = p.read_text(encoding='utf-8')
        orig = s
        if 'bus-row' in s:
            key = p.stem
            s, linked, total = link_rows(s, key)
            n_linked += linked
            n_rows += total
        if DEST_P_RE.search(s) or ('buses-from-' in p.stem and 'bj-pop-row' not in s):
            if stems is None:
                stems = {q.stem for q in PAGES.glob('*.html')}
            s2, changed = beautify_place_page(s, p.stem, stems)
            if changed:
                s = s2
                if PLACE_CSS not in s and '</head>' in s:
                    s = s.replace('</head>', PLACE_CSS + '\n</head>', 1)
        s2, ch = merge_stats(s)
        if ch:
            s = s2
        s2, ch = trim_routemap(s)
        if ch:
            s = s2
        if 'id="bjThemeBtn"' not in s and '</nav>' in s:
            s = s.replace('</nav>', THEME_BTN + '\n</nav>', 1)
        if 'a.bus-row' in s and LINK_CSS not in s and '</head>' in s:
            s = s.replace('</head>', LINK_CSS + '\n</head>', 1)
        if 'id="bjThemeBtn"' in s and 'bjThemeBtn.addEventListener' not in s and '</body>' in s:
            s = s.replace('</body>', THEME_JS + '\n</body>', 1)
        if s != orig:
            p.write_text(s, encoding='utf-8')
            n_pages += 1
    print(f'linked {n_linked}/{n_rows} bus rows on {n_pages} pages; dark toggle ensured on all')

if __name__ == '__main__':
    main()
