#!/usr/bin/env python3
# Home section order: Popular Operators UP (right after hero), Popular Destinations below.
# index.html: move static operators section inside #app (after hero) + data-keep="1" + app.js buster bump.
# app.js: add operators section to homeHTML + hero-keep preserves it. Idempotent, no regex.
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)

OPS_BLOCK = NL.join([
    '  <section data-keep="1" style="max-width:720px;margin:0 auto 8px;padding:0 18px 18px">',
    '    <div style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--amber-ink,#6b4610);font-weight:600;margin-bottom:10px">Popular Operators</div>',
    '    <div style="display:flex;flex-wrap:wrap;gap:8px">',
    '      <a href="bus-time-table/sbstc-buses.html" style="background:var(--surface,#fffcf4);border:1px solid var(--line,#ccc);border-radius:999px;padding:9px 16px;font-size:13px;font-weight:700;color:var(--ink,#211c16);text-decoration:none;min-height:40px;display:inline-flex;align-items:center">SBSTC</a>',
    '      <a href="bus-time-table/nbstc-buses.html" style="background:var(--surface,#fffcf4);border:1px solid var(--line,#ccc);border-radius:999px;padding:9px 16px;font-size:13px;font-weight:700;color:var(--ink,#211c16);text-decoration:none;min-height:40px;display:inline-flex;align-items:center">NBSTC</a>',
    '      <a href="bus-time-table/wbtc-buses.html" style="background:var(--surface,#fffcf4);border:1px solid var(--line,#ccc);border-radius:999px;padding:9px 16px;font-size:13px;font-weight:700;color:var(--ink,#211c16);text-decoration:none;min-height:40px;display:inline-flex;align-items:center">WBTC</a>',
    '      <a href="bus-time-table/shyamoli-paribahan-buses.html" style="background:var(--surface,#fffcf4);border:1px solid var(--line,#ccc);border-radius:999px;padding:9px 16px;font-size:13px;font-weight:700;color:var(--ink,#211c16);text-decoration:none;min-height:40px;display:inline-flex;align-items:center">Shyamoli Paribahan</a>',
    '      <a href="bus-time-table/volvo-ac-buses.html" style="background:var(--surface,#fffcf4);border:1px solid var(--line,#ccc);border-radius:999px;padding:9px 16px;font-size:13px;font-weight:700;color:var(--ink,#211c16);text-decoration:none;min-height:40px;display:inline-flex;align-items:center">Volvo AC</a>',
    '    </div>',
    '  </section>',
])

OLD_SIB = NL.join([
    '    var sib = keepHero.nextElementSibling;',
    '    while (sib) { var nx2 = sib.nextElementSibling; sib.remove(); sib = nx2; }',
])
NEW_SIB = NL.join([
    '    /* keep the static Popular Operators section (data-keep) when re-rendering home */',
    '    var keepOps = el.querySelector(' + chr(39) + '[data-keep=' + chr(34) + '1' + chr(34) + ']' + chr(39) + ');',
    '    var freshOps = tmp.querySelector(' + chr(39) + '[data-keep=' + chr(34) + '1' + chr(34) + ']' + chr(39) + ');',
    '    if (keepOps && freshOps) freshOps.remove();',
    '    var sib = keepHero.nextElementSibling;',
    '    while (sib) { var nx2 = sib.nextElementSibling; if (sib.getAttribute && sib.getAttribute(' + chr(39) + 'data-keep' + chr(39) + ') === ' + chr(39) + '1' + chr(39) + ') break; sib.remove(); sib = nx2; }',
])

def patch_index(path):
    lines = open(path, encoding='utf-8').read().split(NL)
    if any('data-keep="1"' in l for l in lines):
        print('index.html: already patched')
        return False
    sec_start = None
    for i, l in enumerate(lines):
        if '<section style="max-width:720px;margin:0 auto 8px;padding:0 18px 18px">' in l:
            sec_start = i
            break
    if sec_start is None:
        print('index.html: operators section not found')
        sys.exit(1)
    sec_end = None
    for j in range(sec_start, len(lines)):
        if '</section>' in lines[j]:
            sec_end = j
            break
    stats_i = None
    for i, l in enumerate(lines):
        if 'class="stats-inline"' in l:
            stats_i = i
            break
    if stats_i is None or stats_i + 3 >= len(lines):
        print('index.html: stats anchor bad')
        sys.exit(1)
    app_close = stats_i + 3
    if lines[stats_i + 1].strip() != '</div>' or lines[stats_i + 2].strip() != '</div>' or lines[app_close].strip() != '</div>':
        print('index.html: unexpected closing structure')
        sys.exit(1)
    del_end = sec_end + 1
    if del_end < len(lines) and lines[del_end].strip() == '':
        del_end += 1
    del lines[sec_start:del_end]
    insert_at = app_close
    lines[insert_at:insert_at] = OPS_BLOCK.split(NL) + ['']
    text = NL.join(lines)
    if 'js/app.js?v=perf20260925e' in text:
        text = text.replace('js/app.js?v=perf20260925e', 'js/app.js?v=brand20260925f')
    else:
        print('index.html: app.js buster not found')
        sys.exit(1)
    open(path, 'w', encoding='utf-8').write(text)
    print('index.html: patched')
    return True

def patch_app(path):
    text = open(path, encoding='utf-8').read()
    if 'data-keep' in text:
        print('app.js: already patched')
        return False
    idx = text.find('total_stops || 0')
    if idx == -1:
        print('app.js: stats anchor not found')
        sys.exit(1)
    dest_i = text.find('<div class="section">', idx)
    if dest_i == -1:
        print('app.js: destinations section not found')
        sys.exit(1)
    between = text[idx:dest_i]
    if between.count('</div>') != 2:
        print('app.js: unexpected hero closings:', between.count('</div>'))
        sys.exit(1)
    text = text[:dest_i] + OPS_BLOCK + NL + text[dest_i:]
    if OLD_SIB not in text:
        print('app.js: sib loop anchor not found')
        sys.exit(1)
    text = text.replace(OLD_SIB, NEW_SIB, 1)
    open(path, 'w', encoding='utf-8').write(text)
    print('app.js: patched')
    return True

def main():
    changed = False
    changed |= patch_index(os.path.join(ROOT, 'index.html'))
    changed |= patch_app(os.path.join(ROOT, 'js', 'app.js'))
    print('done, changed:', changed)

if __name__ == '__main__':
    main()
