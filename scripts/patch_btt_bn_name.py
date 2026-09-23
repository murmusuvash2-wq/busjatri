# Fixes the BTT page Bengali-mode bug: body.lang-bn hid the whole .sname div
# (which contains the Bengali .sbn span inside it), so stand names vanished
# in Bangla mode. Now the English text is wrapped in span.sen at page load
# and only that span is hidden; the Bengali name becomes the card title.
# Idempotent: safe to re-run. Backslash-free source.
import io

P = 'bus-time-table/index.html'
s = io.open(P, encoding='utf-8').read()

# --- 1. CSS fix ---
old_css = 'body.lang-bn .sname{display:none}'
new_css = ('body.lang-bn .sen{display:none}'
           'body.lang-bn .sbn{font-size:16.5px;font-weight:800;color:inherit;margin-left:0}'
           'body.lang-bn .keep-en .sen{display:inline}')
if old_css in s:
    s = s.replace(old_css, new_css)
    print('css: patched')
elif 'body.lang-bn .sen{display:none}' in s:
    print('css: already patched')
else:
    print('css: PATTERN NOT FOUND')
    raise SystemExit(1)

# --- 2. JS fix: wrap English text nodes of .sname in span.sen ---
anchor = ("    if(!card.querySelector('.sbn')){card.classList.add('keep-en');}" + chr(10) +
          '  });' + chr(10) + '});')
addition = ("    if(!card.querySelector('.sbn')){card.classList.add('keep-en');}" + chr(10) +
            '  });' + chr(10) +
            "  Array.prototype.forEach.call(document.querySelectorAll('.scard .sname'),function(el){" + chr(10) +
            '    Array.prototype.slice.call(el.childNodes).forEach(function(n){' + chr(10) +
            '      if(n.nodeType===3 && n.textContent.trim()){' + chr(10) +
            "        var sp=document.createElement('span');" + chr(10) +
            "        sp.className='sen';" + chr(10) +
            '        sp.textContent=n.textContent;' + chr(10) +
            '        el.replaceChild(sp,n);' + chr(10) +
            '      }' + chr(10) +
            '    });' + chr(10) +
            '  });' + chr(10) +
            '});')
if "sp.className='sen'" not in s:
    if anchor in s:
        s = s.replace(anchor, addition)
        print('js: patched')
    else:
        print('js: ANCHOR NOT FOUND')
        raise SystemExit(1)
else:
    print('js: already patched')

if s != io.open(P, encoding='utf-8').read():
    io.open(P, 'w', encoding='utf-8').write(s)
    print('file: written')
else:
    print('file: no change needed')
