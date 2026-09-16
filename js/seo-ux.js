/* BusJatri shared SEO-page controls (2026-09-16)
   Injected into every bus-time-table/*.html page:
   1. EN/বাংলা toggle + dark mode button in the header (listing page already
      injects its own বাংলা button — we skip that one and only add the theme one)
   2. Translates the common English-only labels on route pages when বাংলা is on
   3. Shortens the listing tagline to one line mentioning SBSTC/NBSTC/private
   4. Adds an amber Search button next to the listing search box
   State keys match the existing inline code: bj-lang, seo-theme. */
(function () {
  'use strict';

  var SUN_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2.2M12 19.8V22M2 12h2.2M19.8 12H22M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M19.4 4.6l-1.6 1.6M6.2 17.8l-1.6 1.6"/></svg>';
  var MOON_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z"/></svg>';
  var SEARCH_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.8-3.8"/></svg>';

  /* exact-string translations for route pages (English-only markup) */
  var MAP = {
    'Home': 'হোম',
    'Routes': 'রুট',
    'Bus Timetable': 'বাস টাইম টেবিল',
    'Bus Time Table': 'বাস টাইম টেবিল',
    'Scheduled Departures': 'নির্ধারিত ছাড়ার সময়',
    'Time N/A': 'সময় নেই',
    'Route Map': 'রুট ম্যাপ',
    'FAQ': 'সাধারণ প্রশ্ন',
    'stops': 'স্টপ',
    'bus': 'বাস',
    'buses': 'বাস',
    'First': 'প্রথম',
    'Last': 'শেষ',
    'return': 'ফেরার',
    'About Us': 'আমাদের সম্পর্কে',
    'Contact Us': 'যোগাযোগ',
    'Privacy Policy': 'গোপনীয়তা নীতি',
    'Credits': 'ক্রেডিট',
    'All Bus Timetables': 'সব বাস টাইম টেবিল',
    'full timetable below': 'নিচে সম্পূর্ণ সময়সূচি',
    'Listed schedules can change; confirm with the operator before travel.': 'সময়সূচি বদলাতে পারে। যাত্রার আগে যাচাই করে নিন।'
  };

  function isBn() { return document.body.classList.contains('lang-bn'); }

  function collectMapped() {
    var out = [];
    var main = document.querySelector('main') || document.body;
    var w = document.createTreeWalker(main, NodeFilter.SHOW_TEXT, null);
    var n;
    while ((n = w.nextNode())) {
      var t = (n.nodeValue || '').replace(/\s+/g, ' ').trim();
      if (!t) continue;
      var t2 = t.replace(/^[·\u203a\s]+/, '');
      var pre = t.slice(0, t.length - t2.length);
      if (t2 && MAP[t2]) out.push({ node: n, bn: pre + MAP[t2] });
      else if (t.indexOf('Schedule data refreshed') === 0) out.push({ node: n, bn: t.replace('Schedule data refreshed', 'শেষ হালনাগাদ') });
    }
    var foot = document.querySelector('footer');
    if (foot) {
      var w2 = document.createTreeWalker(foot, NodeFilter.SHOW_TEXT, null);
      while ((n = w2.nextNode())) {
        var t2 = (n.nodeValue || '').replace(/\s+/g, ' ').trim();
        if (t2 && MAP[t2]) out.push({ node: n, bn: MAP[t2] });
      }
    }
    out.forEach(function (m) { m.en = m.node.nodeValue; });
    return out;
  }

  function applyLang(mapped) {
    var bn = isBn();
    mapped.forEach(function (m) {
      m.node.nodeValue = bn ? m.bn : m.en;
    });
    var q = document.getElementById('q');
    if (q) q.placeholder = bn ? 'যেমন: এসপ্লেন্ড, দীঘা, বাঁকুড়া...' : 'e.g. Esplanade, Digha, Bankura...';
  }

  function init() {
    /* 3. shorter tagline (listing page only) */
    var tg = document.querySelector('.hero .tagline');
    if (tg) {
      var en = tg.querySelector('.label-en');
      var bn2 = tg.querySelector('.label-bn');
        if (en && en.textContent.indexOf('Complete bus timings') === 0) {
        en.textContent = 'Bus time table — SBSTC × NBSTC × WBTC & private buses.';
      }
      if (bn2) bn2.textContent = 'বাস টাইম টেবিল — SBSTC · NBSTC · WBTC ও প্রাই৭েট বাস���',;
    }

    var mapped = collectMapped();
    applyLang(mapped);

    var nav = document.querySelector('.header-inner nav');

    /* 1. header buttons */
    if (nav) {
      if (!document.getElementById('themeBtn')) {
        var tb = document.createElement('button');
        tb.id = 'themeBtn';
        tb.type = 'button';
        tb.className = 'sjx-btn';
        tb.title = 'Toggle theme';
        tb.setAttribute('aria-label', 'Toggle dark mode');
        tb.onclick = function () {
          var dark = document.body.classList.toggle('dark');
          try { localStorage.setItem('seo-theme', dark ? 'dark' : 'light'); } catch (e) {}
          tb.innerHTML = dark ? SUN_SVG : MOON_SVG;
        };
        nav.appendChild(tb);
      }
      var lb = document.getElementById('langBtn');
      if (!lb) {
        lb = document.createElement('button');
        lb.id = 'langBtn';
        lb.type = 'button';
        lb.className = 'sjx-btn';
        nav.appendChild(lb);
      }
      lb.onclick = function () {
        document.body.classList.toggle('lang-bn');
        var bn = isBn();
        try { localStorage.setItem('bj-lang', bn ? 'bn' : 'en'); } catch (e) {}
        lb.textContent = bn ? 'English' : 'বাংলা';
        applyLang(mapped);
      };
      var tb2 = document.getElementById('themeBtn');
      var lb2 = document.getElementById('langBtn');
      if (tb2) tb2.innerHTML = document.body.classList.contains('dark') ? SUN_SVG : MOON_SVG;
      if (lb2) lb2.textContent = isBn() ? 'English' : 'বাংলা';
    }

    /* 4. search button on the listing page */
    var q = document.getElementById('q');
    if (q && !document.getElementById('sjxGo')) {
      var row = q.closest('.search-row');
      if (row && typeof window.doSearch === 'function') {
        var gb = document.createElement('button');
        gb.id = 'sjxGo';
        gb.type = 'button';
        gb.className = 'sjx-go';
        gb.innerHTML = SEARCH_SVG + '<span class="label-en">Search</span><span class="label-bn">খুঁজুন</span>';
        gb.onclick = function () { window.doSearch(); };
        row.appendChild(gb);
      }
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
