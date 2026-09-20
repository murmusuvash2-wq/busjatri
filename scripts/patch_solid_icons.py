#!/usr/bin/env python3
"""Icon style consistency: make Map + Report icons SOLID/FILLED like
WhatsApp and Facebook logos (outline icons looked visually thinner)."""
import io

OLD_MAP = ('<svg viewBox="0 0 24 24" style="width:18px;height:18px;flex:0 0 auto" aria-hidden="true" '
           'fill="none" stroke="currentColor" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>'
           '<circle cx="12" cy="10" r="3"/></svg>')
NEW_MAP = ('<svg viewBox="0 0 24 24" style="width:18px;height:18px;flex:0 0 auto" aria-hidden="true" '
           'fill="currentColor"><path fill-rule="evenodd" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13'
           'c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>')

OLD_FLAG = ('<svg viewBox="0 0 24 24" style="width:18px;height:18px;flex:0 0 auto" aria-hidden="true" '
            'fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>'
            '<line x1="4" y1="22" x2="4" y2="15"/></svg>')
NEW_FLAG = ('<svg viewBox="0 0 24 24" style="width:18px;height:18px;flex:0 0 auto" aria-hidden="true" '
            'fill="currentColor"><path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z"/></svg>')

def main():
    s = io.open('js/bus-page.js', encoding='utf-8').read()
    if NEW_MAP in s:
        print('already patched (solid icons)')
    else:
        assert s.count(OLD_MAP) == 1, 'map outline svg not found'
        assert s.count(OLD_FLAG) == 1, 'flag outline svg not found'
        s = s.replace(OLD_MAP, NEW_MAP).replace(OLD_FLAG, NEW_FLAG)
        n16 = s.count('style="width:16px;height:16px;flex:0 0 auto"')
        if n16 == 1:
            s = s.replace('style="width:16px;height:16px;flex:0 0 auto"',
                          'style="width:18px;height:18px;flex:0 0 auto"')
        io.open('js/bus-page.js', 'w', encoding='utf-8').write(s)
        print('bus-page.js: solid filled icons (map pin, report flag) + fb icon 18px')

    h = io.open('index.html', encoding='utf-8').read()
    h2 = h.replace('bus-page.js?v=bj20260920e', 'bus-page.js?v=bj20260920f')
    if h2 != h:
        io.open('index.html', 'w', encoding='utf-8').write(h2)
        print('index.html: cache-bust updated')

if __name__ == '__main__':
    main()
