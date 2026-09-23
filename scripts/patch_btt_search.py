#!/usr/bin/env python3
"""
BTT hub search patch (2026-09-23, demo v7 approved).

Adds to bus-time-table/index.html (via gen_btt_v2.py):
  1. Compact hero (All Bus Timetables) — smaller title/padding/chips
  2. Search box: From / via (right-shifted, optional) / To / Bus Stand
     - From + To           -> opens <from>-to-<to>.html (direct route)
     - via filled          -> opens <from>-to-<to>-via-<via>.html if it exists,
                              else falls back with a note + direct-page button
     - reverse direction   -> panel with open button for the existing direction
     - Bus Stand only      -> opens buses-from-<stand>.html
     - From only (a stand) -> opens that stand page
  3. Old bottom stand filter (#q dsearch) removed
  4. Clean i18n: EN = zero Bengali (.hbn/.sbn hidden), BN = Bengali labels,
     placeholders, panel text; times untouched; keep-en fallback for cards
     without a Bengali name
  5. Enter-key submit on all four inputs

Data: route/via/stand index is computed at generation time by scanning the
bus-time-table directory + discover_stands() — nothing hardcoded, nothing
fabricated. Bengali input is mapped back to English place names via bnplace.

Idempotent: skips if already applied. Run from repo root:
  python3 scripts/patch_btt_search.py && python3 scripts/gen_btt_v2.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN_PATH = os.path.join(ROOT, "scripts", "gen_btt_v2.py")

with open(GEN_PATH, "r", encoding="utf-8") as fh:
    src = fh.read()

if "rt-search-js" in src or "function rtSearch" in src:
    print("gen_btt_v2.py already patched - nothing to do")
    sys.exit(0)

NEW_CSS = """
/* ---- compact hero ---- */
.hero{padding:14px 16px !important;border-radius:16px !important;margin-bottom:10px !important}
.hero h1{font-size:20px !important;letter-spacing:-.3px !important}
.hero .hbn{font-size:11px !important;margin-top:2px !important}
.hero .chips{margin-top:8px !important;gap:4px !important}
.hero .schip{font-size:10px !important;padding:3px 8px !important}
.sec{margin:12px 0 6px !important}
.sec h3{font-size:15px !important}
/* ---- clean i18n ---- */
body:not(.lang-bn) .hbn{display:none}
body:not(.lang-bn) .sbn{display:none}
body.lang-bn .sname{display:none}
body.lang-bn .keep-en .sname{display:inline}
/* ---- search box ---- */
.rt-search{background:var(--surface);border:1px solid var(--line-strong);border-radius:14px;padding:8px 10px 8px;box-shadow:var(--shadow-sm);margin:10px 0 2px;animation:fadeUp .5s .15s ease both}
.rt-search .rt-f,.rt-search .rt-go,.rt-search .rt-viarow{animation:fadeUp .4s ease both;animation-delay:calc(.15s + var(--i,0)*.06s)}
.rt-f{padding:5px 8px 3px;position:relative}
.rt-f+.rt-f,.rt-viarow+.rt-f{border-top:1px dashed var(--line)}
.rt-f label{display:flex;align-items:center;gap:4px;font-family:var(--font-mono,monospace);font-size:9px;font-weight:600;color:var(--amber-ink);margin-bottom:2px;text-transform:uppercase;letter-spacing:.06em}
.rt-f label svg{width:10px;height:10px;stroke-width:2.2;flex:none;color:var(--amber)}
.rt-f label em{font-style:normal;opacity:.65;text-transform:none;letter-spacing:0}
.rt-f input{width:100%;padding:3px 0 4px;border:none;border-bottom:1.5px solid transparent;font-size:14px;font-family:inherit;background:transparent;color:var(--ink);transition:.2s}
.rt-f input:focus{outline:none;border-bottom-color:var(--amber)}
.rt-f input::placeholder{color:var(--ink-dim);opacity:.5;font-size:12.5px}
.rt-viarow{display:flex;justify-content:flex-end;margin:3px 0}
.rt-via{flex:0 0 60%;background:var(--amber-soft);border-radius:8px;padding:4px 10px 2px}
.rt-go{margin-top:7px;width:100%;border:none;border-radius:9px;background:var(--amber);color:#fff9ee;font-size:13px;font-weight:700;font-family:inherit;padding:9px 16px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px}
.rt-go svg{width:13px;height:13px;stroke-width:2.6}
.rt-go:active{transform:scale(.985)}
.rt-result{margin-top:8px;border-radius:10px;border:1px solid var(--line);overflow:hidden}
.rt-rhead{padding:6px 10px;font-size:10px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;background:var(--amber-soft);color:var(--amber-ink)}
.rt-result.ok .rt-rhead{background:rgba(77,124,15,.13);color:#4d7c0f}
.rt-rbody{padding:8px 10px;border-top:1px solid var(--line)}
.rt-rroute{font-family:var(--font-display);font-size:13px;font-weight:700;line-height:1.3}
.rt-open{display:inline-flex;align-items:center;gap:5px;margin-top:7px;background:var(--amber);color:#fff9ee !important;text-decoration:none;font-size:11.5px;font-weight:700;padding:7px 12px;border-radius:8px}
.rt-open svg{width:11px;height:11px;stroke-width:2.5}
.rt-open:active{transform:scale(.97)}
.rt-rnote{font-size:11px;color:var(--ink-dim);margin-top:4px;line-height:1.45}
[data-theme="dark"] .rt-go{background:#eda94a;color:#241706}
[data-theme="dark"] .rt-open{background:#eda94a;color:#241706 !important}
[data-theme="dark"] .rt-result.ok .rt-rhead{color:#a3c76d}
"""

SEARCH_BOX_TMPL = """<div class="rt-search" id="rtsearch">
  <div class="rt-f" style="--i:0">
    <label><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg><span class="label-en">From</span><span class="label-bn">কোথা থেকে</span></label>
    <input id="rtfrom" list="rtplaces" autocomplete="off">
  </div>
  <div class="rt-viarow" style="--i:1">
    <div class="rt-f rt-via">
      <label><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/></svg><span class="label-en">Via <em>(optional)</em></span><span class="label-bn">স্টপেজ <em>(ঐচ্ছিক)</em></span></label>
      <input id="rtvia" list="rtplaces" autocomplete="off">
    </div>
  </div>
  <div class="rt-f" style="--i:2">
    <label><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><path d="m16.2 7.8-2.9 6.5-6.5 2.9 2.9-6.5 6.5-2.9Z"/></svg><span class="label-en">To</span><span class="label-bn">কোথায়</span></label>
    <input id="rtto" list="rtplaces" autocomplete="off">
  </div>
  <div class="rt-f" style="--i:3">
    <label><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/></svg><span class="label-en">Bus Stand</span><span class="label-bn">বাস স্ট্যান্ড</span></label>
    <input id="rtstand" list="rtstands" autocomplete="off">
  </div>
  <button class="rt-go" style="--i:4" onclick="rtSearch()" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg><span class="label-en">Search</span><span class="label-bn">খুঁজুন</span></button>
  <div class="rt-result" id="rtresult" style="display:none">
    <div class="rt-rhead" id="rtrhead"></div>
    <div class="rt-rbody">
      <div class="rt-rroute" id="rtrroute"></div>
      <a class="rt-open" id="rtropen" style="display:none"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><path d="M15 3h6v6"/><path d="M10 14 21 3"/></svg><span class="label-en">Open page</span><span class="label-bn">পেজ খুলুন</span></a>
      <div class="rt-rnote" id="rtrnote"></div>
    </div>
  </div>
</div>
<script id="rt-search-js">
(function(){
var RT={},VT={};
'@ROUTES@'.split(',').forEach(function(k){if(k){RT[k]=1;}});
'@VIA@'.split(',').forEach(function(k){if(k){VT[k]=1;}});
var RT_S=@STANDS@;
var RT_BN=@BNMAP@;
var RT_A=@ALIASES@;
var RT_SA=@STANDALIAS@;
function el(i){return document.getElementById(i);}
function isBn(){return document.body.className.indexOf('lang-bn')>-1;}
function T(en,bn){return isBn()?bn:en;}
var PH={from:{en:'e.g. Asansol',bn:'যেমন আসানসোল'},via:{en:'e.g. Durgapur',bn:'যেমন দুর্গাপুর'},to:{en:'e.g. Digha',bn:'যেমন দীঘা'},stand:{en:'e.g. Bankura',bn:'যেমন বাঁকুড়া'}};
function rtSlug(s){return String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');}
function rtRaw(v){var s=String(v||'').trim().toLowerCase();if(RT_BN[s]){s=RT_BN[s];}if(RT_A[s]){s=RT_A[s];}return s;}
function rtNorm(v){return rtSlug(rtRaw(v));}
function rtGo(f){window.location.href=f;}
function panel(head,route,file,note,ok){
  var R=el('rtresult');
  R.className='rt-result'+(ok?' ok':'');
  el('rtrhead').textContent=head;
  el('rtrroute').textContent=route;
  var B=el('rtropen');
  if(file){B.href=file;B.style.display='inline-flex';}else{B.style.display='none';}
  el('rtrnote').textContent=note||'';
  R.style.display='block';
  if(R.scrollIntoView){try{R.scrollIntoView({behavior:'smooth',block:'nearest'});}catch(e){}}
}
window.rtSearch=function(){
  var fl=el('rtfrom').value,vl=el('rtvia').value,tl=el('rtto').value,sl=el('rtstand').value;
  if(fl.trim()===''&&tl.trim()===''&&vl.trim()===''&&sl.trim()===''){
    panel(T('Type something first','আগে কিছু লিখুন'),T('From + To, or a Bus Stand','কোথা থেকে ও কোথায়, অথবা বাস স্ট্যান্ড'),'',T('Fill any box and tap Search.','যেকোনো ঘরে লিখে খুঁজুন চাপুন।'));
    return;
  }
  var f=rtNorm(fl),t=rtNorm(tl),v=rtNorm(vl);
  var st=rtSlug(rtRaw(sl));if(RT_SA[st]){st=RT_SA[st];}
  if(fl.trim()!==''&&tl.trim()!==''){
    if(vl.trim()!==''){
      var vk=f+'|'+t+'|'+v;
      if(VT[vk]){rtGo(f+'-to-'+t+'-via-'+v+'.html');return;}
      if(RT[f+'|'+t]){
        panel(T('No via page - direct route','ভায়া পেজ নেই - সরাসরি রুট'),fl+' to '+tl,f+'-to-'+t+'.html',T('No separate page for via '+vl+'. The direct page includes through buses.','ভায়া '+vl+' এর আলাদা পেজ নেই। সরাসরি পেজে মাঝপথের বাসও আছে।'),true);
        return;
      }
    }
    if(RT[f+'|'+t]){rtGo(f+'-to-'+t+'.html');return;}
    if(RT[t+'|'+f]){
      panel(T('Route runs the other way','রুট উল্টো দিকে'),tl+' to '+fl,t+'-to-'+f+'.html',T('The page is listed '+tl+' to '+fl+' - open it.','পেজটি '+tl+' থেকে '+fl+' হিসেবে আছে - খুলুন।'),true);
      return;
    }
    panel(T('No page for this route yet','এই রুটের পেজ এখনও নেই'),fl+' to '+tl,'',T('Check the spelling, or open a stand page below. More routes are being added.','বানান দেখে নিন, বা নিচের স্ট্যান্ড পেজ খুলুন। আরও রুট যোগ হচ্ছে।'));
    return;
  }
  var one=st||f||t;
  var disp=sl.trim()!==''?sl:(fl.trim()!==''?fl:tl);
  if(one&&RT_S[one]){rtGo(RT_S[one]);return;}
  panel(T('No stand page found','স্ট্যান্ড পেজ পাওয়া যায়নি'),disp,'',T('Check the spelling, or pick a stand card below.','বানান দেখে নিন, বা নিচের স্ট্যান্ড কার্ড বেছে নিন।'));
};
['rtfrom','rtvia','rtto','rtstand'].forEach(function(i){el(i).addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();rtSearch();}});});
window.rtPH=function(){
  el('rtfrom').placeholder=T(PH.from.en,PH.from.bn);
  el('rtvia').placeholder=T(PH.via.en,PH.via.bn);
  el('rtto').placeholder=T(PH.to.en,PH.to.bn);
  el('rtstand').placeholder=T(PH.stand.en,PH.stand.bn);
};
rtPH();
document.addEventListener('DOMContentLoaded',function(){
  Array.prototype.forEach.call(document.querySelectorAll('.scard'),function(card){
    if(!card.querySelector('.sbn')){card.classList.add('keep-en');}
  });
});
})();
</script>
"""

NEW_FUNCS_HEAD = '''
# ------------------------------------------------------------------
# Search box (From / via / To / Bus Stand) — demo v7 approved 2026-09-23
# ------------------------------------------------------------------

SEARCH_BOX_TMPL = """'''

NEW_FUNCS_TAIL = '''"""


def render_search_html():
    import json

    routes = []
    vias = []
    skip = ("index", "buses-from", "nbstc-", "sbstc-", "wbtc-", "volvo-", "shyamoli-")
    for fname in sorted(os.listdir(g.OUT)):
        if not fname.endswith(".html") or fname.startswith(skip):
            continue
        stem = fname[:-5]
        if "-via-" in stem:
            left, v = stem.split("-via-", 1)
            parts = left.split("-to-")
            if len(parts) == 2 and parts[0] and parts[1] and v:
                vias.append(parts[0] + "|" + parts[1] + "|" + v)
            continue
        parts = stem.split("-to-")
        if len(parts) == 2 and parts[0] and parts[1]:
            routes.append(parts[0] + "|" + parts[1])

    stands = {}
    stand_names = []
    for name, fname in discover_stands():
        stands[g.slug(name)] = fname
        stands[g.slug(card_name(name))] = fname
        stand_names.append(name)

    cnt = {}
    for b in g.BUSES:
        for p in (b.get("origin"), b.get("destination")):
            p = (p or "").strip()
            if p:
                cnt[p] = cnt.get(p, 0) + 1
    places = sorted(cnt, key=lambda p: (-cnt[p], p))

    bnmap = {}
    for p in places + stand_names:
        bp = v2.bnplace(p)
        if bp and bp != p:
            bp = bp.strip().lower()
            if bp not in bnmap:
                bnmap[bp] = p

    aliases = {
        "calcutta": "Kolkata",
        "burdwan": "Bardhaman",
        "midnapore": "Medinipur",
        "midnapur": "Medinipur",
        "medinipore": "Medinipur",
    }
    stand_alias = {"esplanade": "kolkata"}

    places_opts = "".join('<option value="' + g.esc(p) + '">' for p in places)
    stands_opts = "".join('<option value="' + g.esc(card_name(n)) + '">' for n in stand_names)

    js = SEARCH_BOX_TMPL
    js = js.replace("@ROUTES@", ",".join(sorted(set(routes))))
    js = js.replace("@VIA@", ",".join(sorted(set(vias))))
    js = js.replace("@STANDS@", json.dumps(stands, ensure_ascii=False, sort_keys=True))
    js = js.replace("@BNMAP@", json.dumps(bnmap, ensure_ascii=False, sort_keys=True))
    js = js.replace("@ALIASES@", json.dumps(aliases, ensure_ascii=False, sort_keys=True))
    js = js.replace("@STANDALIAS@", json.dumps(stand_alias, ensure_ascii=False, sort_keys=True))
    assert chr(92) not in js, "backslash leaked into BTT search JS"

    return (js
            + '<datalist id="rtplaces">' + places_opts + "</datalist>"
            + '<datalist id="rtstands">' + stands_opts + "</datalist>")

'''

NL = chr(10)

# ---- apply patches ----

# 1. CSS append
needle_css = 'body.lang-bn .only-bn{display:block}"""'
assert src.count(needle_css) == 1, "CSS tail anchor not found"
src = src.replace(needle_css, 'body.lang-bn .only-bn{display:block}' + NEW_CSS + '"""')

# 2. search box goes right above the Bus Stands section; old dsearch removed
needle_sec = '<div class="sec"><h3>{stands_h}</h3><span class="cnt" id="scnt"></span></div>'
assert src.count(needle_sec) == 1, "sec anchor not found"
src = src.replace(needle_sec, '{search_html}' + NL + needle_sec)
needle_dsearch = '<div class="dsearch"><input id="q" type="text" oninput="fil()" aria-label="Search bus stands"></div>' + NL
assert src.count(needle_dsearch) == 1, "dsearch anchor not found"
src = src.replace(needle_dsearch, '')

# 3. format kwargs
needle_fmt = "chips=chips, cards=cards,"
assert src.count(needle_fmt) == 1, "format kwargs anchor not found"
src = src.replace(needle_fmt, "chips=chips, search_html=render_search_html(), cards=cards,")

# 4. new constants + function before generate_btt_page
needle_gen = "def generate_btt_page():"
assert src.count(needle_gen) == 1, "generate_btt_page anchor not found"
src = src.replace(needle_gen, NEW_FUNCS_HEAD + SEARCH_BOX_TMPL + NEW_FUNCS_TAIL + "def generate_btt_page():")

# 5. setLang calls rtPH so placeholders switch language too
needle_sl = "var q=document.getElementById('q');if(q){q.placeholder=l==='bn'?PH.bn:PH.en;}"
assert src.count(needle_sl) == 1, "setLang anchor not found"
src = src.replace(needle_sl, needle_sl + "if(window.rtPH){rtPH();}")

payload = NEW_CSS + NEW_FUNCS_HEAD + SEARCH_BOX_TMPL + NEW_FUNCS_TAIL
assert chr(92) not in payload, "backslash in patch payload"

with open(GEN_PATH, "w", encoding="utf-8") as fh:
    fh.write(src)

print("patched gen_btt_v2.py: search box + compact hero + clean i18n")
