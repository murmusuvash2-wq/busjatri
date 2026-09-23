# Design batch: compact cards + card-click + See More on route pages.
# 1) css/seo.css: append compact + interaction override block (idempotent, marker comment)
# 2) scripts/gen_route_v2.py: bump css version + inject inline JS before </body>
#    (injected at write time, NOT inside the f-string template, so JS braces are safe)
# Backslash-free source. Safe to re-run.

import io

MARK = '/* ==== design batch 2026-09-24 ==== */'

CSS_BLOCK = MARK + '''
.bus-row{padding:8px 11px;gap:8px;margin-bottom:6px;border-radius:12px}
.bus-row .dep{min-width:62px;font-size:15px}
.bus-row .op{font-size:13.5px}
.bus-row .mrow{gap:6px;font-size:11px;margin-top:2px}
.via-chip,.rel-chip{padding:5px 12px;min-height:31px;font-size:12.5px}
.seo-section{margin-top:15px}
.seo-hero{padding:8px 0 10px}
details{margin-top:6px}
.bus-row{cursor:pointer;-webkit-tap-highlight-color:rgba(184,121,31,.18)}
.bus-row:active{transform:scale(.985)}
.bd-link{display:none}
.bus-row.cut{display:none}
.see-more-btn{display:block;width:100%;margin:10px 0 18px;padding:12px;border-radius:12px;border:1.5px dashed var(--border-strong);background:var(--surface);color:var(--ink);font-weight:700;font-size:14px;cursor:pointer;font-family:inherit}
.see-more-btn:active{transform:scale(.99)}
'''

JS_BLOCK = """<script>
(function(){
  var rows=[].slice.call(document.querySelectorAll('.bus-row'));
  var KEEP=10,STEP=20,btn=null;
  function bn(n){var d='০১২৩৪৫৬৭৮৯';return String(n).replace(/[0-9]/g,function(c){return d[+c];});}
  function isBn(){return document.body.className.indexOf('lang-bn')>-1;}
  function leftCount(){var n=0;for(var i=0;i<rows.length;i++){if(rows[i].classList.contains('cut')){n++;}}return n;}
  function label(){
    var m=leftCount();
    if(m<1){return;}
    var n=Math.min(STEP,m);
    btn.textContent=isBn()?('আরও '+bn(n)+'টি বাস দেখুন ('+bn(m)+'টি বাকি)'):('See '+n+' more buses ('+m+' left)');
  }
  if(rows.length>14){
    for(var i=KEEP;i<rows.length;i++){rows[i].classList.add('cut');}
    btn=document.createElement('button');
    btn.type='button';
    btn.className='see-more-btn';
    btn.addEventListener('click',function(){
      var shown=0;
      for(var j=0;j<rows.length&&shown<STEP;j++){
        if(rows[j].classList.contains('cut')){rows[j].classList.remove('cut');shown++;}
      }
      if(leftCount()<1){if(btn.parentNode){btn.parentNode.removeChild(btn);}}
      else{label();}
    });
    label();
    rows[rows.length-1].parentNode.appendChild(btn);
    if(window.MutationObserver){
      new MutationObserver(function(){if(btn){label();}}).observe(document.body,{attributes:true,attributeFilter:['class']});
    }
  }
  document.addEventListener('click',function(e){
    var t=e.target;
    if(!t||!t.closest){return;}
    if(t.closest('a')){return;}
    var row=t.closest('.bus-row');
    if(!row){return;}
    var sel=window.getSelection?window.getSelection():null;
    if(sel&&String(sel)){return;}
    var a=row.querySelector('a.bd-link');
    if(a&&a.getAttribute('href')){window.location.href=a.getAttribute('href');}
  });
})();
</script>"""


def patch_css():
    P = 'css/seo.css'
    s = io.open(P, encoding='utf-8').read()
    if MARK in s:
        print('css: already patched')
        return
    if not s.endswith(chr(10)):
        s += chr(10)
    s += CSS_BLOCK + chr(10)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('css: patched')


def patch_generator():
    P = 'scripts/gen_route_v2.py'
    s = io.open(P, encoding='utf-8').read()
    changed = False

    # 1. css version bump
    old_v = 'seo.css?v=rt20260920'
    new_v = 'seo.css?v=rt20260924'
    if old_v in s:
        s = s.replace(old_v, new_v)
        changed = True
        print('gen: css version bumped')
    elif new_v in s:
        print('gen: css version already bumped')
    else:
        print('gen: CSS VERSION PATTERN NOT FOUND')
        raise SystemExit(1)

    # 2. INLINE_JS definition before def main()
    marker = 'INLINE_JS = """<script>'
    if marker not in s:
        anchor = 'def main():'
        if anchor not in s:
            print('gen: MAIN ANCHOR NOT FOUND')
            raise SystemExit(1)
        inject = 'INLINE_JS = """' + JS_BLOCK + '"""' + chr(10) + chr(10) + chr(10) + anchor
        s = s.replace(anchor, inject, 1)
        changed = True
        print('gen: INLINE_JS defined')
    else:
        print('gen: INLINE_JS already defined')

    # 3. inject at write time
    old_w = 'fh.write(page)'
    new_w = "fh.write(page.replace('</body>', INLINE_JS + '</body>', 1))"
    if old_w in s:
        s = s.replace(old_w, new_w, 1)
        changed = True
        print('gen: write hook patched')
    elif new_w in s:
        print('gen: write hook already patched')
    else:
        print('gen: WRITE ANCHOR NOT FOUND')
        raise SystemExit(1)

    if changed:
        io.open(P, 'w', encoding='utf-8').write(s)
        print('gen: file written')


if __name__ == '__main__':
    patch_css()
    patch_generator()
    print('design batch patch done')
