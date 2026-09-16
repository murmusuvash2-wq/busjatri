/* ============================================================
   BusJatri UX fixes overlay (2026-09-16) — loaded LAST.
   DOM-level patches that survive SPA re-renders:
   1. "Live Departures" wording -> "Bus Stand Departure Times"
      (pulsing dot removed too — no live-tracking impression)
   2. "Browse all timetables" link removed from under search
   3. Custom stop autocomplete replaces the native datalist
      overlay that blocked the fields below
   4. Show-all-stops uses history.replaceState so the browser
      BACK button always leaves the page (no history pollution)
   ============================================================ */
(function () {
  'use strict';

  function escHtml(s) {
    var A = String.fromCharCode(38);
    var M = {};
    M[A] = A + 'amp;';
    M['<'] = A + 'lt;';
    M['>'] = A + 'gt;';
    M['"'] = A + 'quot;';
    M["'"] = A + '#39;';
    return String(s).replace(/[&<>"']/g, function (c) {
      return M[c];
    });
  }

  /* ---- 1. Wording: no "live" impression ---- */
  function fixWording() {
    document.querySelectorAll('.label-en').forEach(function (el) {
      if (el.textContent.trim() === 'Live Departures') el.textContent = 'Bus Stand Departure Times';
    });
    document.querySelectorAll('.label-bn').forEach(function (el) {
      if (el.textContent.trim() === 'লাইভ ছাড়ার তালিকা') el.textContent = 'বাস স্ট্যান্ডের ছাড়ার সময়';
    });
    document.querySelectorAll('.lv-clock-label .ldot').forEach(function (d) { d.remove(); });
  }

  /* ---- 2. Remove "Browse all timetables" under search ---- */
  function removeBrowseBtn() {
    document.querySelectorAll('.search-actions .browse-btn').forEach(function (b) { b.remove(); });
  }

  /* ---- 3. Custom autocomplete (replaces datalist overlay) ---- */
  var LIMIT = 8;
  var NAMES = null;
  function stopNames() {
    if (!NAMES) {
      var src = (typeof STOPS !== 'undefined' && STOPS) || {};
      NAMES = Object.values(src).map(function (s) { return s && s.name; }).filter(Boolean);
    }
    return NAMES;
  }
  function findMatches(q) {
    var t = (q || '').toLowerCase().trim();
    if (!t) return [];
    var starts = [], has = [];
    var names = stopNames();
    for (var i = 0; i < names.length; i++) {
      var ln = names[i].toLowerCase();
      if (ln.indexOf(t) === 0) {
        starts.push(names[i]);
        if (starts.length >= LIMIT) break;
      } else if (ln.indexOf(t) !== -1) {
        has.push(names[i]);
      }
    }
    return starts.concat(has).slice(0, LIMIT);
  }
  function isSearchInput(el) {
    return !!(el && (el.id === 'fromInput' || el.id === 'toInput' || el.id === 'stopInput'));
  }
  function hideDrop() {
    document.querySelectorAll('.ac-drop').forEach(function (d) { d.remove(); });
  }
  function showDrop(input) {
    hideDrop();
    var m = findMatches(input.value);
    if (!m.length) return;
    var field = input.closest('.search-field');
    if (!field) return;
    var d = document.createElement('div');
    d.className = 'ac-drop';
    d.innerHTML = m.map(function (n) {
      return '<div class="ac-item">' + escHtml(n) + '</div>';
    }).join('');
    field.appendChild(d);
  }
  document.addEventListener('input', function (e) {
    if (isSearchInput(e.target)) showDrop(e.target);
  });
  document.addEventListener('click', function (e) {
    var item = e.target.closest ? e.target.closest('.ac-item') : null;
    if (item) {
      var field = item.closest('.search-field');
      var input = field && field.querySelector('input');
      if (input) {
        input.value = item.textContent;
        hideDrop();
        input.focus();
      }
      return;
    }
    if (isSearchInput(e.target)) { showDrop(e.target); return; }
    hideDrop();
  });
  /* native datalist off — custom dropdown does not block other fields */
  function stripDatalist() {
    ['fromInput', 'toInput', 'stopInput'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.removeAttribute('list');
    });
    var dl = document.getElementById('stopList');
    if (dl) dl.remove();
  }

  /* ---- 4. Show-all-stops without history pollution ---- */
  function fixShowAll() {
    document.querySelectorAll('.show-all, .show-more-btn').forEach(function (b) {
      if (b.dataset.uxFixed) return;
      var h = b.getAttribute('onclick') || '';
      var i = h.indexOf("location.hash='");
      if (i === -1) return;
      var rest = h.slice(i + 15);
      var j = rest.indexOf("'");
      if (j === -1) return;
      var target = rest.slice(0, j);
      b.removeAttribute('onclick');
      b.dataset.uxFixed = '1';
      b.addEventListener('click', function () {
        try {
          history.replaceState(null, '', target);
          window.dispatchEvent(new HashChangeEvent('hashchange'));
        } catch (err) {
          location.hash = target;
        }
      });
    });
  }

  function runAll() {
    fixWording();
    removeBrowseBtn();
    stripDatalist();
    fixShowAll();
  }

  /* app.js renders async (7MB data fetch) + on every hashchange —
     observe DOM and patch after each render, debounced */
  var t = null;
  var mo = new MutationObserver(function () {
    clearTimeout(t);
    t = setTimeout(runAll, 60);
  });
  mo.observe(document.body, { childList: true, subtree: true });
  runAll();
})();
