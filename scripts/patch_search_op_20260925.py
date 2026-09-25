#!/usr/bin/env python3
# stop-search-all.js (the ACTIVE v3 search): support ?op= deep links
# (operator auto-fill, e.g. #/search?op=sbstc) with a removable amber chip.
# Also bumps the stop-search-all.js cache buster in index.html.
# Idempotent, line-based, no regex.
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)
Q = chr(39)
DQ = chr(34)

DEFS = '''
      window.bjOpChipClear = function () {
        var h = location.hash.split('?');
        var p = new URLSearchParams(h[1] || '');
        p.delete('op');
        location.hash = h[0] + (p.toString() ? '?' + p.toString() : '');
      };
      var opHtml = opq ? ('<p style="text-align:center;font-size:13px;margin:4px 0 12px"><span onclick="bjOpChipClear()" ' +
        'style="display:inline-flex;align-items:center;gap:8px;background:var(--amber-soft,#f6e7c6);border:1.5px solid var(--amber,#b8791f);border-radius:999px;padding:8px 14px;font-weight:700;cursor:pointer">' +
        icon('bus') + ' ' + esc(opq.toUpperCase()) + ' <span style="font-weight:800;color:var(--ink-dim,#665)">' + String.fromCharCode(10005) + '</span></span></p>') : '';
'''

FILT = '''
      if (opq) {
        rows = rows.filter(function (r) {
          var bb = r.b || {};
          if (opq === 'volvo-ac' || opq === 'ac') {
            var bt = (bb.bus_type || '').toUpperCase();
            return bt.indexOf('AC') > -1 && bt.indexOf('NON') == -1;
         }
          var hay = ((bb.operator || '') + ' ' + (bb.bus_name || '') + ' ' + (bb.bus_type || '') + ' ' + (bb.source || '')).toLowerCase();
          return hay.indexOf(opq) > -1;
        });
      }
'''


def block(s):
    out = s.split(NL)
    if out and out[0] == '':
        out = out[1:]
    while out and out[-1] == '':
        out = out[:-1]
    return out


def main():
    js_path = os.path.join(ROOT, 'js', 'stop-search-all.js')
    lines = open(js_path, encoding='utf-8').read().split(NL)

    def idx(pred, start=0):
        for i in range(start, len(lines)):
            if pred(lines[i]:
                return i
        return None

    if any("params.get('op')" in l for l in lines):
        print('stop-search-all.js: op support already present')
    else:
        # 1. read op param after stop param
        i = idx(lambda l: "var stop = (params.get('stop')" in l)
        if i is None:
            print('stop param line not found'); sys.exit(1)
        lines.insert(i + 1, "      var opq = (params.get('op') || '').toLowerCase().trim();")

        # 2. filter rows before the now/sort section
        j = idx(lambda l: 'window.__bjTimeQuery = q;' in l)
        if j is None:
            print('time query line not found'); sys.exit(1)
        k = idx(lambda l: l.strip() == 'var now = minutesNow();', j)
        if k is None:
            print('now line not found'); sys.exit(1)
        lines[k:k] = block(FILT)

        # 3. title shows operator name when op-only
        i = idx(lambda l: 'var titleTxt = routeMode' in l)
        if i is None:
            print('title line not found'); sys.exit(1)
        if "(from || to || '')" in lines[i]:
            lines[i] = lines[i].replace("(from || to || '')", "(from || to || (opq ? opq.toUpperCase() : ''))")
        elif "(from || to || '')" in lines[i + 1]:
            lines[i + 1] = lines[i + 1].replace("(from || to || '')", "(from || to || (opq ? opq.toUpperCase() : ''))")
        else:
            print('title fallback pattern missing'); sys.exit(1)

        # 4. amber chip html (after timeHtml) + include in header
        i = idx(lambda l: 'var timeHtml = window.__bjTimeQuery' in l)
        if i is None:
            print('timeHtml line not found'); sys.exit(1)
        lines[i + 1:i + 1] = block(DEFS)
        i = idx(lambda l: 'viaHtml + timeHtml +' in l)
        if i is None:
            print('innerHTML header line not found'); sys.exit(1)
        lines[i] = lines[i].replace('viaHtml + timeHtml +', 'viaHtml + timeHtml + opHtml +')

        open(js_path, 'w', encoding='utf-8').write(NL.join(lines))
        print('stop-search-all.js: op param support added')

    idx_path = os.path.join(ROOT, 'index.html')
    itext = open(idx_path, encoding='utf-8').read()
    old = 'stop-search-all.js?v=bj20260924a'
    new = 'stop-search-all.js?v=bj20260925a'
    if old in itext:
        itext = itext.replace(old, new)
        open(idx_path, 'w', encoding='utf-8').write(itext)
        print('index.html: stop-search-all buster bumped to bj20260925a')
    elif new in itext:
        print('index.html: stop-search-all buster already bj20260925a')
    else:
        print('index.html: stop-search-all buster not found'); sys.exit(1)
    print('done')


if __name__ == '__main__':
    main()
