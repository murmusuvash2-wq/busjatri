/* BusJatri SEO page controls v2 (2026-09-22)
   Works with the unified header baked into the generated pages:
   - theme button (#themeBtn): toggles body.dark, persists to bj-theme
     (falls back to seo-theme key used by older pages)
   - language pills (#langEn / #langBn): toggles body.lang-bn, persists to
     bj-lang (same key as the homepage app — one switch, whole site) */
(function () {
  'use strict';

  var SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2.2M12 19.8V22M2 12h2.2M19.8 12H22M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M19.4 4.6l-1.6 1.6M6.2 17.8l-1.6 1.6"/></svg>';
  var MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z"/></svg>';
  var CHEV = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>';
  var BJ_UI_CSS = '<style>'
    + '.back-nav{width:38px;height:38px;border-radius:50%;border:1px solid var(--line);background:var(--surface-2);display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:var(--ink);padding:0;margin-right:10px;flex:0 0 auto;transition:border-color .2s,transform .3s}'
    + '.back-nav svg{width:18px;height:18px}'
    + '.back-nav:hover{border-color:var(--amber,#b8791f)}'
    + '.back-nav:active{transform:scale(.92)}'
    + '#themeBtn.theme-btn{width:38px;height:38px;border-radius:50%;border:1px solid var(--line);background:var(--surface-2);display:inline-flex;align-items:center;justify-content:center;cursor:pointer;padding:0;font-size:15px;line-height:1;transition:border-color .2s,transform .3s}'
    + '#themeBtn.theme-btn svg{width:17px;height:17px}'
    + '#themeBtn.theme-btn:hover{border-color:var(--amber,#b8791f)}'
    + '#themeBtn.theme-btn:active{transform:scale(.92)}'
    + '</style>';

  function readKey(keys) {
    for (var i = 0; i < keys.length; i++) {
      try { var v = localStorage.getItem(keys[i]); if (v) return v; } catch (e) {}
    }
    return null;
  }

  function setTheme(dark) {
    document.body.classList.toggle('dark', dark);
    var b = document.getElementById('themeBtn');
    if (b) b.innerHTML = dark ? SUN : MOON;
    try { localStorage.setItem('bj-theme', dark ? 'dark' : 'light'); } catch (e) {}
    try { localStorage.setItem('seo-theme', dark ? 'dark' : 'light'); } catch (e) {}
  }

  function setLang(bn) {
    if (window.BJLang) {
      window.BJLang.setLang(bn ? 'bn' : 'en');
      return;
    }
    document.body.classList.toggle('lang-bn', bn);
    var en = document.getElementById('langEn');
    var bnBtn = document.getElementById('langBn');
    if (en) en.classList.toggle('on', !bn);
    if (bnBtn) bnBtn.classList.toggle('on', bn);
    try { localStorage.setItem('bj-lang', bn ? 'bn' : 'en'); } catch (e) {}
  }

  function addBackBtn() { return; /* 2026-09-29: back button removed from all pages per user */
    if (document.body.getAttribute('data-noback') === '1') return;
    var host = document.querySelector('.header-inner');
    if (!host || document.getElementById('bjBackBtn')) return;
    var b = document.createElement('button');
    b.type = 'button'; b.id = 'bjBackBtn'; b.className = 'back-nav';
    b.setAttribute('aria-label', 'Back'); b.title = 'Back';
    b.innerHTML = CHEV;
    b.onclick = function () {
      if (history.length > 1 && document.referrer.indexOf(location.origin) === 0) history.back();
      else if (location.pathname !== '/') location.href = '/';
    };
    host.insertBefore(b, host.firstChild);
  }

  function init() {
    var t = readKey(['bj-theme', 'seo-theme']);
    if (t === 'dark') setTheme(true);
    else if (t === 'light') setTheme(false);
    else if (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches) setTheme(true);

    setLang(readKey(['bj-lang']) === 'bn');

    var tb = document.getElementById('themeBtn');
    if (tb) tb.onclick = function () { setTheme(!document.body.classList.contains('dark')); };
    var en = document.getElementById('langEn');
    if (en) en.onclick = function () { setLang(false); };
    var bnBtn = document.getElementById('langBn');
    if (bnBtn) bnBtn.onclick = function () { setLang(true); };
    addBackBtn();
    document.head.insertAdjacentHTML('beforeend', BJ_UI_CSS);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();

/* 2026-09-28 interlinking: reverse-link chips injected into existing chip-rows
   (All buses from X / Buses via Y) — same .rel-chip style, idempotent. */
(function () {
  'use strict';
  var STAND = new Set(['alipurduar', 'amtala', 'asansol', 'babughat', 'bagnan', 'bandwan', 'bankura', 'barabazar', 'barasat', 'barasat-chapadali', 'barddhaman-alisha-bus-stand', 'barddhaman-nawabhat-bus-stand', 'bardhaman', 'baruipur', 'basirhat', 'bbd-bag', 'benachity', 'berhampore', 'bishnupur', 'boga', 'bolpur', 'burdwan', 'chandrakona-road', 'chittaranjan', 'contai', 'cooch-behar', 'dakshineswar', 'dhamakhali', 'dhanbad', 'digha', 'dinhata', 'durgapur', 'durgapur-station', 'egra', 'esplanade', 'fulkusma', 'garia', 'garia-bus-stand', 'ghatal', 'habra', 'habra-depot', 'habra-station', 'haldia', 'howrah-maidan', 'howrah-station', 'jadavpur-8b', 'jhargram', 'kalna', 'karimpur', 'karunamoyee', 'kharagpur', 'khatra', 'kolkata', 'krishnanagar', 'manbazar', 'mathabhanga', 'medinipur', 'midnapur', 'nabadwip', 'nabanna', 'newtown', 'purulia', 'raipur', 'rajabazar', 'santragachi', 'sealdah', 'sector-v', 'shapoorji', 'shyambazar', 'siliguri', 'suri', 'tarakeshwar', 'tarkeshwar', 'tatanagar', 'thakurpukur', 'ultadanga']);
  var VIA = new Set(['arambagh', 'asansol', 'bandwan', 'bankura', 'barasat', 'belpahari', 'burdwan', 'dhumsai', 'digha', 'durgapur', 'durgapur-station', 'esplanade', 'garia', 'habra', 'habra-depot', 'haldia', 'jhargram', 'karunamoyee', 'katwa', 'kolkata', 'medinipur', 'midnapore', 'purulia', 'siliguri', 'suri', 'tarakeswar']);
  function slug(s) { return String(s).toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, ''); }
  function nextChipRow(el) {
    var n = el.nextElementSibling;
    while (n) { if (n.classList && n.classList.contains('chip-row')) return n; n = n.nextElementSibling; }
    return null;
  }
  function inject() {
    var titles = document.querySelectorAll('.section-title');
    for (var i = 0; i < titles.length; i++) {
      var t = titles[i], en = t.querySelector('.label-en');
      if (!en) continue;
      var txt = (en.textContent || '').trim();
      var m = txt.match(/^More Routes from (.+)$/) || txt.match(/^More Buses to (.+)$/);
      if (!m) continue;
      var row = nextChipRow(t);
      if (!row) continue;
      var isFrom = txt.indexOf('More Routes from') === 0;
      var sl = slug(m[1]);
      var target = isFrom ? 'buses-from-' + sl + '.html' : '../via/' + sl + '.html';
      var has = isFrom ? STAND.has(sl) : VIA.has(sl);
      if (!has || row.querySelector('a[href="' + target + '"]')) continue;
      var a = document.createElement('a');
      a.className = 'rel-chip';
      a.href = target;
      a.textContent = (isFrom ? 'All buses from ' : 'Buses via ') + m[1].trim() + ' \u2192';
      row.insertBefore(a, row.firstChild);
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', inject);
  else inject();
})();
