#!/usr/bin/env python3
"""Action row v3: fix broken concatenation (missing + after Facebook button
that killed the report button + timetable) and make buttons ICON-ONLY.
4 equal square buttons in one row: Map | WhatsApp | Facebook | Report."""
import io, re

SVG_COMMON = 'viewBox="0 0 24 24" style="width:18px;height:18px;flex:0 0 auto" aria-hidden="true"'
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

NEW_BLOCK = (
    "'<div class=\"wa-row\">' +\n"
    "        (mapUrl ? '<a class=\"map-btn\" href=\"' + mapUrl + '\" target=\"_blank\" rel=\"noopener\" "
    "title=\"Open route in Google Maps\" aria-label=\"Open route in Google Maps\">' + '" + SVG_MAP + "' + '</a>' : '') +\n"
    "        '<a class=\"wa-btn\" href=\"javascript:void(0)\" onclick=\"shareBusWhatsApp()\" "
    "title=\"Share on WhatsApp\" aria-label=\"Share on WhatsApp\">' + '" + SVG_WA + "' + '</a>' +\n"
    "        '<a class=\"fb-btn\" href=\"javascript:void(0)\" onclick=\"shareBusFacebook()\" "
    "title=\"Share on Facebook\" aria-label=\"Share on Facebook\">' + '" + SVG_FB + "' + '</a>' +\n"
    "        '<a class=\"report-btn\" href=\"javascript:void(0)\" onclick=\"toggleReport(this)\" "
    "title=\"Report issue\" aria-label=\"Report issue\""
    " data-id=\"' + esc(id) + '\" data-bus=\"' + esc(b.bus_name) + '\" data-reg=\"' + esc(b.reg_no || '') + '\""
    " data-org=\"' + esc(pn(b.origin)) + '\" data-dest=\"' + esc(pn(b.destination)) + '\""
    " data-dep=\"' + esc(b.departure_time || '') + '\">' + '" + SVG_FLAG + "' + '</a>' +\n"
    "      '</div>' +")

CSS_V3 = """/* ==== Action row v3: icon-only brand buttons, one row (2026-09-20) ==== */
.wa-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px}
.wa-row .map-btn,.wa-row .wa-btn,.wa-row .fb-btn,.wa-row .report-btn{display:flex;align-items:center;justify-content:center;min-width:0;padding:12px 0;border-radius:10px;text-decoration:none;line-height:1;cursor:pointer;font-family:var(--font-body)}
.wa-row .map-btn svg,.wa-row .wa-btn svg,.wa-row .fb-btn svg,.wa-row .report-btn svg{width:18px;height:18px;flex:0 0 auto}
.wa-row .map-btn{background:var(--amber,#b8791f);color:#fff;border:1.5px solid var(--amber,#b8791f)}
.wa-row .map-btn:hover{background:#a06a1a;border-color:#a06a1a;color:#fff}
.wa-row .wa-btn{background:#25D366;color:#fff;border:1.5px solid #25D366}
.wa-row .wa-btn:hover{background:#1fbf5a;border-color:#1fbf5a;color:#fff}
.wa-row .fb-btn{background:#1877F2;color:#fff;border:1.5px solid #1877F2}
.wa-row .fb-btn:hover{background:#1667d9;border-color:#1667d9;color:#fff}
.wa-row .report-btn{background:#fff;color:#c0392b;border:1.5px solid #d8dee9}
.wa-row .report-btn:hover{background:#fdf0ee;border-color:#e5b7b1}
"""

def main():
    s = io.open('js/bus-page.js', encoding='utf-8').read()

    if 'title="Report issue"' in s:
        print('bus-page.js: already patched (v3)')
    else:
        i = s.find('<div class="wa-row">')
        assert i > 0, 'wa-row not found'
        i2 = s.rfind("'", 0, i)          # opening quote of the wa-row string literal
        assert i2 > 0 and s[i2:i] == "'"
        endmark = "</div>' +"
        j = s.find(endmark, i)
        assert j > 0, 'wa-row closing div not found'
        s = s[:i2] + NEW_BLOCK + s[j + len(endmark):]
        # structural sanity: no quote-newline-quote ASI hazard anywhere
        assert not re.search(r"'\s*\n\s*'", s), 'ASI hazard present'
        io.open('js/bus-page.js', 'w', encoding='utf-8').write(s)
        print('bus-page.js: action row v3 (icon-only) written')

    css = io.open('css/ux-fixes.css', encoding='utf-8').read()
    if 'Action row v3' in css:
        print('ux-fixes.css: already patched (v3)')
    else:
        old = css.find('/* ==== Action row redesign: 4 brand buttons')
        if old >= 0:
            css = css[:old]          # drop v2 block (it ran to EOF)
        css += CSS_V3
        io.open('css/ux-fixes.css', 'w', encoding='utf-8').write(css)
        print('ux-fixes.css: v3 CSS written')

    h = io.open('index.html', encoding='utf-8').read()
    h2 = h.replace('bus-page.js?v=bj20260920d', 'bus-page.js?v=bj20260920e')
    h2 = h2.replace('ux-fixes.css?v=ux20260920b', 'ux-fixes.css?v=ux20260920c')
    if h2 != h:
        io.open('index.html', 'w', encoding='utf-8').write(h2)
        print('index.html: cache-busts updated')

if __name__ == '__main__':
    main()
