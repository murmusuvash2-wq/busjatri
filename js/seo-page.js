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
    document.body.classList.toggle('lang-bn', bn);
    var en = document.getElementById('langEn');
    var bnBtn = document.getElementById('langBn');
    if (en) en.classList.toggle('on', !bn);
    if (bnBtn) bnBtn.classList.toggle('on', bn);
    try { localStorage.setItem('bj-lang', bn ? 'bn' : 'en'); } catch (e) {}
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
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
