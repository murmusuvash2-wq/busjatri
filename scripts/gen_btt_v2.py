#!/usr/bin/env python3
"""
BTT index generator v2 — bus-time-table/index.html, "all bus timetables" hub.

Demo-approved design (2026-09-23, homepage parity):
  1. SAME look as the homepage: sticky header (logo + theme + EN/বাংলা
     language buttons), fadeUp animation, dark mode via data-theme +
     localStorage (bj-theme / bj-lang, shared with homepage)
  2. Hero: "All Bus Timetables" + Bengali + chips (stands / routes / buses)
  3. Search box filtering stand cards
  4. BIG stand cards: name + Bengali + "N buses listed · M destinations"
     + "⏰ First – Last" (or "Timings on page" when times are unknown)
  5. 8 popular stands first (Kolkata, Digha, Durgapur, Siliguri, Asansol,
     Bankura, Burdwan, Purulia), rest A-Z; 8 visible, "See more" +8 per tap
  6. FAQ: 5 English + 5 Bengali
  7. NO 789-place route dump — route pages cover that

Same URL: bus-time-table/index.html (design change only).

Usage (run from repo root):
  python3 scripts/gen_btt_v2.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_route_v2 as v2
from gen_stand_v2 import stand_buses, destination_groups, discover_stands, display_name, card_name

g = v2.g
L = v2.L
bn_num = v2.bn_num

POPULAR = ["Kolkata", "Digha", "Durgapur", "Siliguri", "Asansol", "Bankura", "Burdwan", "Purulia"]

CSS = """:root{--bg:#f5efe1;--surface:#fffcf4;--surface-2:#efe6d3;--ink:#211c16;--ink-dim:#6f6653;--line:rgba(33,28,22,.13);--line-strong:rgba(33,28,22,.24);--amber:#b8791f;--amber-ink:#6b4610;--amber-soft:rgba(184,121,31,.14);--shadow:0 10px 34px -12px rgba(33,28,22,.28);--shadow-sm:0 2px 12px rgba(33,28,22,.1);--radius-lg:20px;--radius:14px;--font-display:'Fraunces',Georgia,serif;--font-body:'IBM Plex Sans','IBM Plex Sans Bengali',system-ui,sans-serif}
[data-theme="dark"]{--bg:#15121d;--surface:#201c2b;--surface-2:#29243570;--ink:#f1ead8;--ink-dim:#a89b87;--line:rgba(241,234,216,.1);--line-strong:rgba(241,234,216,.2);--amber:#eda94a;--amber-ink:#f6cd8f;--amber-soft:rgba(237,169,74,.16);--shadow:0 14px 44px -14px rgba(0,0,0,.5);--shadow-sm:0 2px 12px rgba(0,0,0,.3)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--font-body);background:var(--bg);color:var(--ink);line-height:1.55}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.header{background:var(--surface);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:100;backdrop-filter:blur(14px) saturate(1.1);background:color-mix(in srgb,var(--surface) 88%,transparent)}
.header::after{content:"";position:absolute;left:0;right:0;bottom:-6px;height:6px;background-image:radial-gradient(circle at 10px 0,var(--bg) 5px,transparent 5.5px);background-size:20px 6px;background-repeat:repeat-x}
.header-inner{display:flex;align-items:center;justify-content:space-between;padding:13px 18px;gap:10px;position:relative;z-index:1;max-width:788px;margin:0 auto}
.logo{display:flex;align-items:center;gap:9px;font-family:var(--font-display);font-size:1.32rem;font-weight:700;color:var(--ink);cursor:pointer;letter-spacing:-.2px;text-decoration:none}
.logo .icon{width:1.35rem;height:1.35rem;color:var(--amber);stroke-width:1.6}
.logo span{color:var(--amber-ink)}
.header-actions{display:flex;align-items:center;gap:8px}
.icon-btn{width:38px;height:38px;display:inline-flex;align-items:center;justify-content:center;background:var(--surface-2);border:1px solid var(--line);border-radius:50%;cursor:pointer;color:var(--ink);font-size:15px;transition:border-color .2s,transform .3s}
.icon-btn:hover{border-color:var(--amber)}
.icon-btn:active{transform:scale(.92)}
.icon-btn svg{width:17px;height:17px;transition:transform .4s cubic-bezier(.34,1.56,.64,1),opacity .2s}
.lang-group{display:flex;border:1px solid var(--line);border-radius:999px;padding:3px;gap:2px;background:var(--surface-2)}
.lang-btn{background:transparent;border:none;border-radius:999px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;color:var(--ink-dim);transition:.2s;font-family:var(--font-body)}
.lang-btn.active{background:var(--amber);color:#fff9ee}
[data-theme="dark"] .lang-btn.active{color:#241706}
.wrap{max-width:760px;margin:0 auto;padding:14px 14px 60px}
.crumbs{font-size:12px;color:var(--ink-dim);margin:14px 0 14px}.crumbs a{color:var(--ink-dim)}
.hero{background:linear-gradient(135deg,#b8791f 0%,#8a5a12 100%);border-radius:var(--radius-lg);padding:26px 20px;color:#fff;margin-bottom:14px;animation:fadeUp .5s .05s ease both}
.hero h1{font-size:30px;letter-spacing:-.5px;line-height:1.15;font-family:var(--font-display)}
.hero .hbn{font-size:15px;opacity:.92;margin-top:4px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.schip{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:6px 13px;font-size:12.5px;font-weight:700}
.dsearch{background:var(--surface);border:1px solid var(--line-strong);border-radius:var(--radius);box-shadow:var(--shadow-sm);margin:0 0 12px;animation:fadeUp .6s .15s ease both}
.dsearch input{width:100%;border:none;background:transparent;color:var(--ink);border-radius:var(--radius);padding:13px 16px;font-size:15px;font-weight:600;outline:none;font-family:var(--font-body)}
.sec{margin:22px 0 10px;display:flex;align-items:baseline;justify-content:space-between}
.sec h3{font-size:17px;font-family:var(--font-display)}
.sec .cnt{font-size:12px;color:var(--ink-dim)}
.sgrid{display:grid;grid-template-columns:1fr;gap:10px;animation:fadeUp .5s .2s ease both}
@media(min-width:560px){.sgrid{grid-template-columns:1fr 1fr}}
.scard{display:block;background:var(--surface);border:1.5px solid var(--line);border-radius:var(--radius);padding:14px;text-decoration:none;color:inherit;transition:transform .15s,border-color .15s}
.scard:hover{transform:translateY(-2px);border-color:var(--amber)}
.sname{font-size:16.5px;font-weight:800}.sbn{font-size:12.5px;color:var(--ink-dim);font-weight:600;margin-left:6px}
.smeta{font-size:12px;color:var(--amber-ink);font-weight:700;margin-top:4px}
[data-theme="dark"] .smeta{color:var(--amber)}
.stime{font-size:12px;color:var(--ink-dim);margin-top:4px}
.morebtn{display:block;width:100%;margin-top:12px;border:1.5px dashed var(--amber);background:transparent;color:var(--amber-ink);border-radius:12px;padding:11px;font-size:14px;font-weight:800;cursor:pointer}
[data-theme="dark"] .morebtn{color:var(--amber)}
details.faq{background:var(--surface);border:1.5px solid var(--line);border-radius:12px;padding:13px 15px;margin-bottom:8px}
details.faq summary{font-weight:700;font-size:14px;cursor:pointer}
details.faq p{margin-top:8px;font-size:13.5px;color:var(--ink-dim)}
.note{background:var(--amber-soft);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:13px;color:var(--ink-dim);margin:18px 0}
footer{margin-top:30px;border-top:1px solid var(--line);padding-top:14px;font-size:12px;color:var(--ink-dim);text-align:center}
footer a{color:var(--ink-dim);margin:0 6px}
.label-bn{display:none}
body.lang-bn .label-en{display:none}
body.lang-bn .label-bn{display:inline}
.only-bn{display:none}
body.lang-bn .only-en{display:none}
body.lang-bn .only-bn{display:block}
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



JS = """var mstep=24;
var MOON='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
var SUN='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>';
var PH={en:"\\uD83D\\uDD0E Search bus stand — e.g. Bankura, Digha\\u2026",bn:"\\uD83D\\uDD0E \\u09AC\\u09BE\\u09B8 \\u09B8\\u09CD\\u099F\\u09CD\\u09AF\\u09BE\\u09A8\\u09CD\\u09A1 \\u0996\\u09C1\\u0981\\u099C\\u09C1\\u09A8 \\u2014 \\u09AF\\u09C7\\u09AE\\u09A8 \\u09AC\\u09BE\\u0981\\u0995\\u09C1\\u09A1\\u09BC\\u09BE, \\u09A6\\u09C0\\u0998\\u09BE\\u2026"};
function bnd(s){return String(s).replace(/[0-9]/g,function(d){return "\\u09E7\\u09E8\\u09E9\\u09EA\\u09EB\\u09EC\\u09ED\\u09EE\\u09EF\\u09E6"[d];});}
function isBn(){return document.body.className.indexOf('lang-bn')>-1;}
function scards(){return Array.prototype.slice.call(document.querySelectorAll('#stands .scard'));}
function srefresh(){
  var cs=scards();var shown=cs.filter(function(c){return c.style.display!=='none';}).length;
  var b=document.getElementById('smore');
  if(b){if(shown>=cs.length){b.style.display='none';}else{b.style.display='';b.textContent=isBn()?'\\u0986\\u09B0\\u0993 \\u09A6\\u09C7\\u0996\\u09C1\\u09A8 ('+bnd(cs.length-shown)+'\\u099F\\u09BF \\u09B8\\u09CD\\u099F\\u09CD\\u09AF\\u09BE\\u09A8\\u09CD\\u09A1 \\u09AC\\u09BE\\u0995\\u09BF)':'See more ('+(cs.length-shown)+' stands remaining)';}}
  var c=document.getElementById('scnt');
  if(c){c.textContent=isBn()?bnd(shown)+' / '+bnd(cs.length):shown+' of '+cs.length;}
}
function showMore(){
  var cs=scards();var shown=cs.filter(function(c){return c.style.display!=='none';}).length;
  var nxt=Math.min(shown+mstep,cs.length);
  cs.forEach(function(c,i){c.style.display=i<nxt?'':'none';});
  srefresh();
}
sc=scards();sc.forEach(function(c,i){c.style.display=i<mstep?'':'none';});srefresh();
function fil(){
  var q=document.getElementById('q').value.toLowerCase().trim();
  scards().forEach(function(c){c.style.display=!q||c.textContent.toLowerCase().indexOf(q)>-1?'':'none';});
  var cs=scards();var shown=cs.filter(function(c){return c.style.display!=='none';}).length;
  document.getElementById('scnt').textContent=isBn()?bnd(shown)+' / '+bnd(cs.length):shown+' of '+cs.length;
  var b=document.getElementById('smore');if(b){b.style.display=shown>=cs.length?'none':'';}
}
function updateThemeIcon(theme){var btn=document.getElementById('themeBtn');if(btn)btn.innerHTML=theme==='dark'?SUN:MOON;}
function toggleTheme(){
  var cur=document.documentElement.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
  var next=cur==='dark'?'light':'dark';
  document.documentElement.setAttribute('data-theme',next);
  localStorage.setItem('bj-theme',next);
  updateThemeIcon(next);
}
function setLang(l){
  document.body.className=l==='bn'?'lang-bn':'';
  localStorage.setItem('bj-lang',l);
  document.getElementById('langEN').classList.toggle('active',l==='en');
  document.getElementById('langBN').classList.toggle('active',l==='bn');
  var q=document.getElementById('q');if(q){q.placeholder=l==='bn'?PH.bn:PH.en;}if(window.rtPH){rtPH();}
  srefresh();
}
(function(){
  var t=localStorage.getItem('bj-theme');
  if(t)document.documentElement.setAttribute('data-theme',t);
  updateThemeIcon(t||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));
  var l=localStorage.getItem('bj-lang');
  if(l&&l!=='en'){setLang(l);}else{var q=document.getElementById('q');if(q)q.placeholder=PH.en;}
})();"""




def stand_stats():
    """[(name, filename, n, dests, first, last)] for every existing stand page."""
    out = []
    for name, fname in discover_stands():
        buses = stand_buses(name)
        stats = g.route_stats(buses)
        dests = len(destination_groups(name, buses))
        out.append((name, fname, len(buses), dests, stats["first"], stats["last"]))
    return out


def _card(name, fname, n, dests, first, last):
    bn = v2.bnplace(name)
    bn_span = ' <span class="sbn">{}</span>'.format(g.esc(bn)) if bn and bn != name else ""
    if first is not None and last is not None:
        time_row = "⏰ " + L("First", "প্রথম") + " " + g.esc(g.format_time(first)) + " – " + L("Last", "শেষ") + " " + g.esc(g.format_time(last))
    else:
        time_row = "⏰ " + L("Timings on page", "সময়সূচি পেজে")
    return """<a class="scard" href="{href}">
  <div class="sname">{name}{bn}</div>
  <div class="smeta"><b>{n}</b> buses listed · {d} destinations</div>
  <div class="stime">{t}</div>
</a>""".format(href=g.esc(fname), name=g.esc(card_name(name)), bn=bn_span, n=n, d=dests, t=time_row)



# ------------------------------------------------------------------
# Search box (From / via / To / Bus Stand) — demo v7 approved 2026-09-23
# ------------------------------------------------------------------

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

def generate_btt_page():
    stats = stand_stats()
    n_stands = len(stats)
    n_routes = len(g.route_meta)
    n_buses = len(g.BUSES)

    # popular first (by name), rest A-Z
    by_name = {}
    for row in stats:
        by_name.setdefault(row[0], row)
    popular = [by_name[n] for n in POPULAR if n in by_name]
    rest = sorted((r for r in stats if r[0] not in POPULAR), key=lambda r: r[0].lower())
    ordered = popular + rest
    cards = "".join(_card(*row) for row in ordered)

    title = "West Bengal Bus Time Table – All Routes | BusJatri"
    description = ("Complete West Bengal bus time table: {} routes from {} stands. "
                   "Find SBSTC, WBTC, NBSTC and private bus timings with departure times, "
                   "operators and stoppages.".format(n_routes, n_stands))[:300]
    canonical = "{}/bus-time-table/".format(g.BASE)

    chips = ('<span class="schip">🚏 ' + L("{} bus stands".format(n_stands), "{}টি বাস স্ট্যান্ড".format(bn_num(n_stands))) + "</span>"
             + '<span class="schip">🛣 ' + L("{:,} routes".format(n_routes), "{}টি রুট".format(bn_num(n_routes))) + "</span>"
             + '<span class="schip">🚌 ' + L("{:,} buses".format(n_buses), "{}টি বাস".format(bn_num(n_buses))) + "</span>")

    # ---- FAQ (5 EN + 5 BN) ----
    # top-3 from the popular stands only — alias groups (Kolkata/Esplanade/Garia
    # all list the same 687 buses) would otherwise show up as duplicates
    top3 = sorted(popular, key=lambda r: -r[2])[:3]
    top3_txt = ", ".join("{} ({} listed)".format(r[0], r[2]) for r in top3)
    en = [
        ("Where can I find all West Bengal bus time tables?",
         "This page lists every major bus stand in West Bengal — {} stands covering {:,} route pages. Open your stand to see departures, popular routes and all destinations.".format(n_stands, n_routes)),
        ("How do I find a bus from my city or stand?",
         "Type your stand name in the search box above (e.g. 'Bankura' or 'Digha'), open its page and check Popular Routes — times, operators and route links are all there."),
        ("Which bus stands have the most buses listed?",
         "The busiest stands on BusJatri are {}. Every stand page shows the exact number of listed buses.".format(top3_txt)),
        ("Do you have SBSTC, NBSTC and WBTC government bus timings?",
         "Yes — government (SBSTC, NBSTC, WBTC) and private buses are listed together on every stand and route page, with departure times and stoppages."),
        ("Are these bus timings guaranteed?",
         "No — timetables change often. BusJatri lists what is published; always verify with the operator or depot before travelling, especially for early-morning and long routes."),
    ]
    bn = [
        ("সব বাসের সময়সূচী কোথায় পাব?",
         "এই পেজে পশ্চিমবঙ্গের প্রধান প্রতিটি বাস স্ট্যান্ড — {}টি স্ট্যান্ড, {:,}টি রুট পেজ — দেওয়া আছে। নিজের স্ট্যান্ড খুলে ছাড়ার সময় ও গন্তব্য দেখুন।".format(n_stands, n_routes)),
        ("আমার শহর বা স্ট্যান্ডের বাস কীভাবে খুঁজব?",
         "উপরের সার্চ বক্সে স্ট্যান্ডের নাম লিখুন (যেমন 'বাঁকুড়া'), পেজ খুলুন — জনপ্রিয় রুট, সময় ও অপারেটর সব সেখানেই।"),
        ("কোন কোন স্ট্যান্ডে সবচেয়ে বেশি বাস আছে?",
         "BusJatri-তে সবচেয়ে ব্যস্ত স্ট্যান্ডগুলি হল {}। প্রতিটি স্ট্যান্ড পেজে তালিকাভুক্ত বাসের সংখ্যা দেওয়া আছে।".format(top3_txt)),
        ("সরকারি SBSTC, NBSTC, WBTC বাসের সময় পাওয়া যায়?",
         "হ্যাঁ — সরকারি (SBSTC, NBSTC, WBTC) ও বেসরকারি বাস একসঙ্গে প্রতিটি স্ট্যান্ড ও রুট পেজে সময়সহ দেওয়া আছে।"),
        ("এই সময়সূচি কি নিশ্চিত?",
         "না — সময়সূচি প্রায়ই বদলায়। ভ্রমণের আগে অপারেটর বা ডিপোতে জেনে নিন, বিশেষ করে ভোরের ও দূরের রুটে।"),
    ]
    faq_html = "".join('<details class="faq only-en"><summary>{}</summary><p>{}</p></details>'.format(g.esc(q), g.esc(a)) for q, a in en)
    faq_html += "".join('<details class="faq only-bn"><summary>📌 {}</summary><p>{}</p></details>'.format(q, a) for q, a in bn)

    note = L("Every stand page shows buses <b>starting</b> from that stand. For buses that pass through a place, open the route page. More services may exist — ask at the stand.",
             "প্রতিটি স্ট্যান্ড পেজে শুধু সেই স্ট্যান্ড থেকে <b>ছাড়া</b> বাস দেখানো হয়। মাঝপথের বাসের জন্য রুট পেজ খুলুন। আরও বাস থাকতে পারে — স্ট্যান্ডে জেনে নিন।")

    header_html = """<header class="header">
  <div class="header-inner">
    <a class="logo" href="../index.html">
      <img class="brand-logo" src="/logo.png" alt="BusJatri" style="width:30px;height:30px;border-radius:50%">
      Bus<span>Jatri</span>
    </a>
    <div class="header-actions">
      <button class="icon-btn" id="themeBtn" onclick="toggleTheme()" title="Toggle theme" aria-label="Toggle dark mode"></button>
      <div class="lang-group">
        <button class="lang-btn active" id="langEN" onclick="setLang('en')">EN</button>
        <button class="lang-btn" id="langBN" onclick="setLang('bn')">বাংলা</button>
      </div>
    </div>
  </div>
</header>"""
    body = """{header}
<div class="wrap">
<div class="crumbs"><a href="../index.html">{home}</a> › <b>{btt}</b></div>
<div class="hero">
  <h1>{h1}</h1>
  <div class="hbn">সব বাসের সময়সূচী — বাস স্ট্যান্ড অনুযায়ী</div>
  <div class="chips">{chips}</div>
</div>
{search_html}
<div class="sec"><h3>{stands_h}</h3><span class="cnt" id="scnt"></span></div>
<div class="sgrid" id="stands">{cards}</div>
<button class="morebtn" id="smore" onclick="showMore()"></button>
<div class="note">📍 {note}</div>
<div class="sec"><h3>{faq_h}</h3></div>
{faq}
<footer>{n} bus stands · {r:,} routes · {b:,} buses · <a href="../about.html">About</a><a href="../contribute.html">Contribute</a><a href="../blog/">Blog</a><a href="../privacy-policy.html">Privacy</a></footer>
</div>
<script>{js}</script>
</body></html>""".format(header=header_html,
                         home=L("Home", "হোম"), btt=L("All Bus Timetables", "সব বাসের সময়সূচী"),
                         h1=L("All Bus Timetables", "সব বাসের সময়সূচী"),
                         stands_h=L("Bus Stands", "বাস স্ট্যান্ড"), faq_h=L("FAQ", "প্রশ্নোত্তর"),
                         chips=chips, search_html=render_search_html(), cards=cards, note=note, faq=faq_html,
                         n=n_stands, r=n_routes, b=n_buses, js=JS)

    head = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{ogimg}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#b8791f">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,500;0,600;0,700;0,900;1,500&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Bengali:wght@400;500;600;700&display=swap" rel="stylesheet">
{schema}
<style>{css}</style></head>""".format(
        title=g.esc(title), desc=g.esc(description), canon=g.esc(canonical),
        ogimg=g.BASE + "/og-image.png", schema="{schema}", css=CSS)

    schema = (g.faq_schema(en + bn) + "\n"
              + g.breadcrumb_schema([
                  ("Home", "/"),
                  ("Bus Timetable", "/bus-time-table/"),
              ]))
    return head.replace("{schema}", schema) + body


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="report only, don't write")
    args = ap.parse_args()
    page = generate_btt_page()
    n_stands = page.count('class="scard"')
    print("btt index: {} stand cards, {} KB".format(n_stands, len(page) // 1024))
    if not args.dry:
        with open(os.path.join(g.OUT, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page)


if __name__ == "__main__":
    main()
