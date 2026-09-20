#!/usr/bin/env python3
"""Bus page action row redesign: 4 clean buttons with real brand SVGs.
Map (pin) | WhatsApp (logo) | Facebook (logo) | Report issue (flag).
Removes the 'Share on X' button. 2x2 grid on mobile via ux-fixes.css."""
import io

SVG_COMMON = 'viewBox="0 0 24 24" style="width:15px;height:15px;flex:0 0 auto" aria-hidden="true"'
SVG_MAP = ('<svg ' + SVG_COMMON + ' fill="none" stroke="currentColor" stroke-width="2">'
           '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>'
           '<circle cx="12" cy="10" r="3"/></svg>')
SVG_WA = ('<svg ' + SVG_COMMON + ' fill="currentColor">'
          '<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-'
          '.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-'
          '.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.347-.347.52-.52.'
          '174-.174.232-.298.347-.497.115-.198.057-.371-.058-.52-.115-.148-.669-1.611-.916-2.207-'
          '.244-.579-.487-.5-.669-.51l-.57-.01c-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 '
          '0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.263.489 1.694.626.'
          '712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414-'
          '.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-'
          '3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 '
          '2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 '
          '9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 '
          '4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 '
          '11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413"/></svg>')
SVG_FB = ('<svg ' + SVG_COMMON + ' fill="currentColor">'
          '<path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 '
          '11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 '
          '2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 '
          '23.027 24 18.062 24 12.073z"/></svg>')
SVG_FLAG = ('<svg ' + SVG_COMMON + ' fill="none" stroke="currentColor" stroke-width="2">'
            '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>'
            '<line x1="4" y1="22" x2="4" y2="15"/></svg>')

def rep(s, old, new, label):
    n = s.count(old)
    assert n == 1, 'expected 1 of %s, found %d' % (label, n)
    return s.replace(old, new)

def main():
    s = io.open('js/bus-page.js', encoding='utf-8').read()

    if 'fb-btn' in s:
        print('bus-page.js: already patched')
    else:
        # Map: real pin svg + short label
        s = rep(s, "icon('map')", "'" + SVG_MAP + "'", 'icon map')
        s = rep(s, 'Route on Google Maps</span>', 'Map</span>', 'map label')
        s = rep(s, '\u0997\u09c1\u0997\u09b2 \u09ae\u09cd\u09af\u09be\u09aa\u09c7 \u09b0\u09c1\u099f \u09a6\u09c7\u0996\u09c1\u09a8',
                '\u09ae\u09cd\u09af\u09be\u09aa', 'map label bn')
        # WhatsApp: real logo + short label
        s = rep(s, "icon('waves')", "'" + SVG_WA + "'", 'icon waves')
        s = rep(s, 'Share on WhatsApp</span>', 'WhatsApp</span>', 'wa label')
        # Facebook: own class + short label (keep inline f svg)
        s = rep(s, 'class="wa-btn" href="javascript:void(0)" onclick="shareBusFacebook()"',
                'class="fb-btn" href="javascript:void(0)" onclick="shareBusFacebook()"', 'fb class')
        s = rep(s, 'Share on Facebook</span>', 'Facebook</span>', 'fb label')
        # remove the Share on X line entirely (from its opening quote to end of line)
        i = s.find('<a class="share-x-btn"')
        assert i > 0, 'share-x line not found'
        i2 = s.rfind("'", 0, i)          # opening quote of that string literal
        assert i2 > 0 and s[i2:i] == "'"
        j = s.find('\n', i)
        s = s[:i2].rstrip().rstrip('+').rstrip() + '\n' + s[j+1:]
        assert 'share-x-btn' not in s and 'shareTwitter(this' not in s
        # Report: flag svg instead of pencil emoji
        s = rep(s, '\u270f <span class="label-en">Report issue</span>',
                SVG_FLAG + ' <span class="label-en">Report issue</span>', 'report flag')
        io.open('js/bus-page.js', 'w', encoding='utf-8').write(s)
        print('bus-page.js: action row rebuilt (4 brand buttons)')

    # CSS: grid layout + brand colors (append to ux-fixes.css)
    css = io.open('css/ux-fixes.css', encoding='utf-8').read()
    if '.wa-row .fb-btn' in css:
        print('ux-fixes.css: already patched')
    else:
        css += ('\n/* ==== Action row redesign: 4 brand buttons, 2x2 grid on mobile (2026-09-20) ==== */\n'
                '.wa-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}\n'
                '.wa-row .map-btn,.wa-row .wa-btn,.wa-row .fb-btn,.wa-row .report-btn{'
                'display:flex;align-items:center;justify-content:center;gap:6px;min-width:0;'
                'padding:11px 6px;font-size:12.5px;font-weight:600;border-radius:10px;'
                'text-decoration:none;line-height:1.15;white-space:nowrap}\n'
                '.wa-row .map-btn svg,.wa-row .wa-btn svg,.wa-row .fb-btn svg,.wa-row .report-btn svg{'
                'width:15px;height:15px;flex:0 0 auto}\n'
                '.wa-row .map-btn{background:var(--amber,#b8791f);color:#fff;border:1.5px solid var(--amber,#b8791f)}\n'
                '.wa-row .map-btn:hover{background:#a06a1a;border-color:#a06a1a;color:#fff}\n'
                '.wa-row .wa-btn{background:#25D366;color:#fff;border:1.5px solid #25D366}\n'
                '.wa-row .wa-btn:hover{background:#1fbf5a;border-color:#1fbf5a;color:#fff}\n'
                '.wa-row .fb-btn{background:#1877F2;color:#fff;border:1.5px solid #1877F2}\n'
                '.wa-row .fb-btn:hover{background:#1667d9;border-color:#1667d9;color:#fff}\n'
                '.wa-row .report-btn{background:#fff;color:#c0392b;border:1.5px solid #d8dee9;'
                'font-family:var(--font-body);cursor:pointer}\n'
                '.wa-row .report-btn:hover{background:#fdf0ee;border-color:#e5b7b1}\n'
                '@media(max-width:560px){.wa-row{grid-template-columns:repeat(2,1fr)}'
                '.wa-row .map-btn,.wa-row .wa-btn,.wa-row .fb-btn,.wa-row .report-btn{'
                'padding:12px 6px;font-size:13px}}\n')
        io.open('css/ux-fixes.css', 'w', encoding='utf-8').write(css)
        print('ux-fixes.css: action row CSS added')

    # cache-busts in index.html
    h = io.open('index.html', encoding='utf-8').read()
    h2 = h.replace('bus-page.js?v=bj20260920c', 'bus-page.js?v=bj20260920d')
    h2 = h2.replace('ux-fixes.css?v=ux20260916k', 'ux-fixes.css?v=ux20260920b')
    if h2 != h:
        io.open('index.html', 'w', encoding='utf-8').write(h2)
        print('index.html: cache-busts updated')

if __name__ == '__main__':
    main()
