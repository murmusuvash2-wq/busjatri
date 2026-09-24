#!/usr/bin/env python3
# Patch gen_via_stop_v2.py: add "See more buses" button to via stop pages.
# Ported from the route-page pattern in gen_route_v2.py (KEEP=10, STEP=20).
# Backslash-free. Idempotent.

import os

SRC = 'scripts/gen_via_stop_v2.py'
s = open(SRC, encoding='utf-8').read()

if 'SEE_MORE_JS' in s:
    print('already patched')
    raise SystemExit(0)

# bilingual label expression copied verbatim from gen_route_v2.py
route_src = open('scripts/gen_route_v2.py', encoding='utf-8').read()
i = route_src.index('isBn()?(')
j = route_src.index(chr(10), i)
label_expr = route_src[i:j].strip()
if label_expr.endswith(';'):
    label_expr = label_expr[:-1]
assert 'more buses' in label_expr and len(label_expr) < 200

SEE_MORE_JS = '''<script>
(function(){
  var board=document.getElementById('vboard');
  if(!board){return;}
  var els=[].slice.call(board.children);
  var rows=[];
  for(var i=0;i<els.length;i++){if(els[i].classList.contains('bus-row')){rows.push(els[i]);}}
  if(rows.length<=14){return;}
  var KEEP=10,STEP=20,btn=null;
  function bn(n){var d='০১২৩৪৫৬৭৮৯';return String(n).replace(/[0-9]/g,function(c){return d[+c];});}
  function isBn(){return document.body.className.indexOf('lang-bn')>-1;}
  function leftCount(){var n=0;for(var i=0;i<rows.length;i++){if(rows[i].classList.contains('cut')){n++;}}return n;}
  function label(){
    var m=leftCount();
    if(m<1){return;}
    var n=Math.min(STEP,m);
    if(btn){btn.textContent=''' + label_expr + ''';}
  }
  var shown=0;
  for(var i=0;i<els.length;i++){
    var e=els[i];
    if(e.classList.contains('bus-row')){shown++;if(shown>KEEP){e.classList.add('cut');}}
    else{if(shown>=KEEP){e.classList.add('cut');}}
  }
  btn=document.getElementById('seemoreBtn');
  if(!btn){return;}
  btn.addEventListener('click',function(){
    var revealed=0;
    for(var j=0;j<els.length&&revealed<STEP;j++){
      var e=els[j];
      if(e.classList.contains('cut')){e.classList.remove('cut');if(e.classList.contains('bus-row')){revealed++;}}
    }
    if(leftCount()<1){if(btn.parentNode){btn.parentNode.removeChild(btn);}}
    else{label();}
  });
  label();
  if(window.MutationObserver){
    new MutationObserver(function(){if(btn){label();}}).observe(document.body,{attributes:true,attributeFilter:['class']});
  }
})();
</script>'''

# 1) CSS into PAGE_TMPL style block
old_css = ('.day-group{margin:20px 0 8px;font-size:12px;font-weight:800;'
           'letter-spacing:.08em;color:var(--ink-dim);border-bottom:1px solid var(--line-strong);padding-bottom:4px}'
           + chr(10) +
           '</style></head>')
new_css = ('.day-group{margin:20px 0 8px;font-size:12px;font-weight:800;'
           'letter-spacing:.08em;color:var(--ink-dim);border-bottom:1px solid var(--line-strong);padding-bottom:4px}'
           + chr(10) +
           '.seemore-btn{display:block;width:100%;box-sizing:border-box;margin:14px 0 6px;padding:13px 16px;'
           'font:600 15px/1.2 inherit;background:var(--surface);border:1.5px solid var(--line-strong);'
           'border-radius:14px;color:var(--ink);cursor:pointer}'
           + chr(10) +
           '.seemore-btn:hover{border-color:var(--amber-ink)}'
           + chr(10) +
           '.bus-row.cut{display:none!important}'
           + chr(10) +
           '.day-group.cut{display:none!important}'
           + chr(10) +
           '</style></head>')
assert old_css in s, 'css anchor not found'
s = s.replace(old_css, new_css, 1)

# 2) wrap board + button in stop_page()
old_board = '''    board = "".join(parts)
    if len(rows) > len(shown):
        board += ('<div class="note">Showing first ' + str(len(shown)) + " of " + str(len(rows)) +
                  ' departures.</div>')'''
new_board = '''    board = "".join(parts)
    if len(rows) > len(shown):
        board += ('<div class="note">Showing first ' + str(len(shown)) + " of " + str(len(rows)) +
                  ' departures.</div>')
    if len(shown) > 14:
        board = ('<div class="vboard" id="vboard">' + board + '</div>' +
                 '<button type="button" class="seemore-btn" id="seemoreBtn"></button>')
    else:
        board = '<div class="vboard">' + board + '</div>' '''
assert old_board in s, 'board anchor not found'
s = s.replace(old_board, new_board, 1)

# 3) inject SEE_MORE_JS before </body> at write time
old_write = '''        page = stop_page(stop, e, route_pages, f)
        if not args.dry:
            with open(os.path.join(VIA_DIR, f), "w", encoding="utf-8") as fh:
                fh.write(page)'''
new_write = '''        page = stop_page(stop, e, route_pages, f)
        if not args.dry:
            with open(os.path.join(VIA_DIR, f), "w", encoding="utf-8") as fh:
                fh.write(page.replace("</body>", SEE_MORE_JS + "</body>", 1))'''
assert old_write in s, 'write anchor not found'
s = s.replace(old_write, new_write, 1)

# 4) add SEE_MORE_JS constant before def main()
const_block = 'SEE_MORE_JS = """' + SEE_MORE_JS + '"""' + chr(10) + chr(10) + chr(10) + 'def main():'
assert chr(10) + 'def main():' in s
s = s.replace(chr(10) + 'def main():', chr(10) + const_block, 1)

open(SRC, 'w', encoding='utf-8').write(s)
print('patched OK')
