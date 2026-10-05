/* BusJatri unified header controller - 2026-10-05 Phase 1
   Supports both legacy header id casing variants during migration.

   
   One language switch + one theme switch, wired the same way on every page.

   Before this, each page family shipped its own header wiring: inline
   setLang()/toggleTheme() handlers on some pages, js/seo-page.js on others,
   and a second "bjThemeBtn" theme button on ~2,900 pages that used a
   different localStorage key and could disagree with the first one.

   This file is the single controller. It is defensive:
     - it clears any legacy .onclick on the three controls before adding its
       own listener, so an older handler cannot double-fire;
     - it marks each click event as handled, so a second listener on the same
       element (e.g. seo-page.js on legacy pages) cannot toggle twice - while
       two different buttons clicked in quick succession still both work;
     - it persists to both the old and new storage keys so a visitor's
       saved preference carries over.
*/
(function () {
  'use strict';
  if (window.__bjHdrCtl) return;
  window.__bjHdrCtl = true;

  var SUN = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.1 5.1l1.6 1.6M17.3 17.3l1.6 1.6M18.9 5.1l-1.6 1.6M6.7 17.3l-1.6 1.6"/></svg>';
  var MOON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z"/></svg>';

  function read(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }
  function write(key, val) {
    try { localStorage.setItem(key, val); } catch (e) {}
  }

  function applyTheme(dark) {
    document.body.classList.toggle('dark', dark);
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    var b = document.getElementById('themeBtn');
    if (b) b.innerHTML = dark ? SUN : MOON;
    write('bj-theme', dark ? 'dark' : 'light');
    write('seo-theme', dark ? 'dark' : 'light');
  }

  function applyLang(bn) {
    document.body.classList.toggle('lang-bn', bn);
    var en = firstById(['langEn', 'langEN']);
    var bnBtn = firstById(['langBn', 'langBN']);
    if (en) {
      en.classList.toggle('on', !bn);
      en.style.background = bn ? 'transparent' : 'var(--amber-soft,#f6e7c6)';
    }
    if (bnBtn) {
      bnBtn.classList.toggle('on', bn);
      bnBtn.style.background = bn ? 'var(--amber-soft,#f6e7c6)' : 'transparent';
    }
    write('bj-lang', bn ? 'bn' : 'en');
    write('seo-lang', bn ? 'bn' : 'en');
  }

  var IDS = ['themeBtn', 'langEn', 'langBn', 'langEN', 'langBN'];
  function firstById(ids) {
    for (var i = 0; i < ids.length; i++) {
      var el = document.getElementById(ids[i]);
      if (el) return el;
    }
    return null;
  }

  /* Some legacy pages load js/seo-page.js, which assigns .onclick to these
     same ids. Clear any handler set by another script so only this
     controller acts - re-checked shortly after load, because that script
     may wire them after we do. */
  function neutralise() {
    for (var i = 0; i < IDS.length; i++) {
      var el = document.getElementById(IDS[i]);
      if (el) el.onclick = null;
    }
  }

  function wire(id, fn) {
    var el = document.getElementById(id);
    if (!el) return;
    el.onclick = null;                      // drop any legacy inline handler
    el.addEventListener('click', function (ev) {
      if (ev.__bjHdrHandled) return;        // another listener already acted on THIS click
      ev.__bjHdrHandled = true;
      ev.preventDefault();
      fn();
    });
  }

  function init() {
    var t = read('bj-theme') || read('seo-theme');
    if (t === 'dark') applyTheme(true);
    else if (t === 'light') applyTheme(false);
    else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) applyTheme(true);
    else applyTheme(false);

    applyLang(read('bj-lang') === 'bn' || read('seo-lang') === 'bn');

    wire('themeBtn', function () { applyTheme(!document.body.classList.contains('dark')); });
    wire(firstById(['langEn', 'langEN']) ? firstById(['langEn', 'langEN']).id : 'langEn', function () { applyLang(false); });
    wire(firstById(['langBn', 'langBN']) ? firstById(['langBn', 'langBN']).id : 'langBn', function () { applyLang(true); });

    neutralise();
    setTimeout(neutralise, 0);
    setTimeout(neutralise, 300);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
