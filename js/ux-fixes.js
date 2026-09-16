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
   5. Rebuilds stoppages (names + up/down times) from the compact
      app-index tables (complete results without the 5MB download)
   6. Search v2: matches BOTH directions of every service — a bus
      running Bankura->Jorehira in the morning also serves the
      Jorehira->Bankura return trip (down times). Evening/return
      services now appear, sorted by time at the user's stop.
      5s budget for the full-data upgrade, then instant compact.
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

  /* ---- 5. Compact search completeness: rebuild stoppages from index ---- */
  function rebuildCompactStops() {
    if (window.__bjStopsRebuilt) return;
    if (typeof DATA === 'undefined' || !DATA || !DATA.buses || !DATA.sn) return;
    window.__bjStopsRebuilt = true;
    DATA.buses.forEach(function (b) {
      if (b.sx && !b.stoppages) {
        b.stoppages = b.sx.map(function (i, k) {
          return { name: DATA.sn[i] || '', um: (b.ux && b.ux[k]) || 0, dm: (b.dx && b.dx[k]) || 0 };
        });
        delete b.sx;
        delete b.ux;
        delete b.dx;
      }
    });
  }

  /* ---- 6. Search v2: both directions of every service ---- */
  function bjTimedLoad() {
    return new Promise(function (resolve, reject) {
      var settled = false;
      var to = setTimeout(function () {
        if (!settled) { settled = true; reject(new Error('full data slow, using compact index')); }
      }, 5000);
      loadFullBusData().then(
        function (j) { if (!settled) { settled = true; clearTimeout(to); resolve(j); } },
        function (e) { if (!settled) { settled = true; clearTimeout(to); reject(e); } }
      );
    });
  }
  function bjPosIn(b, q) {
    if (placeMatches(b.origin, q)) return 0;
    var sts = b.stoppages || [];
    for (var i = 0; i < sts.length; i++) {
      if (placeMatches(sts[i].name, q)) return i + 1;
    }
    if (placeMatches(b.destination, q)) return sts.length + 2;
    return -1;
  }
  function bjFromStop(s, dir) {
    if (!s) return null;
    if (dir === 'up') {
      if (s.um != null) return s.um || null;
      return parseTime(s.up_time);
    }
    if (s.dm != null) return s.dm || null;
    return parseTime(s.down_time);
  }
  function bjStopMin(b, posIdx, dir) {
    var sts = b.stoppages || [];
    if (posIdx === 0) {
      if (dir === 'up') return parseTime(b.departure_time);
      return sts.length ? bjFromStop(sts[sts.length - 1], 'down') : null;
    }
    if (posIdx >= 1 && posIdx <= sts.length) return bjFromStop(sts[posIdx - 1], dir);
    if (dir === 'down') return sts.length ? bjFromStop(sts[sts.length - 1], 'down') : null;
    return sts.length ? bjFromStop(sts[0], 'up') : parseTime(b.arrival_time);
  }
  function bjStopName(b, posIdx) {
    var sts = b.stoppages || [];
    if (posIdx === 0) return b.origin;
    if (posIdx >= 1 && posIdx <= sts.length) return sts[posIdx - 1].name;
    return b.destination;
  }

  if (typeof renderSearch === 'function' && !window.__bjSearchV2) {
    window.__bjSearchV2 = true;
    renderSearch = async function (el) {
      rebuildCompactStops();
      var params = new URLSearchParams(location.hash.split('?')[1] || '');
      var from = (params.get('from') || '').toLowerCase().trim();
      var to = (params.get('to') || '').toLowerCase().trim();
      var stop = (params.get('stop') || '').toLowerCase().trim();
      var routeMode = !!(from && to);

      var all = Object.values(FULL_BUSES || BUSES);
      var rows = [];

      if (routeMode) {
        el.innerHTML = '<div class="container" style="padding:40px"><div class="loading">Searching the full timetable…</div></div>';
        try { await bjTimedLoad(); } catch (e) {}
        all = Object.values(FULL_BUSES || BUSES);
        all.forEach(function (b) {
          var fi = bjPosIn(b, from), ti = bjPosIn(b, to);
          if (fi < 0 || ti < 0 || fi === ti) return;
          if (stop && bjPosIn(b, stop) < 0) return;
          var fwd = fi < ti;
          var depMin = fwd ? bjStopMin(b, fi, 'up') : bjStopMin(b, fi, 'down');
          if (depMin == null && fwd) depMin = parseTime(b.departure_time);
          rows.push({ b: b, fwd: fwd, depMin: depMin, stopName: fwd ? bjStopName(b, fi) : null,
                      atMin: fwd ? bjStopMin(b, fi, 'up') : null });
        });
      } else if (stop) {
        rows = all.filter(function (b) {
          return (b.stoppages || []).some(function (s) { return (s.name || '').toLowerCase().includes(stop); }) ||
                 (b.origin || '').toLowerCase().includes(stop) ||
                 (b.destination || '').toLowerCase().includes(stop);
        }).map(function (b) { return { b: b, fwd: true, depMin: parseTime(b.departure_time) }; });
      } else {
        var q = from || to;
        rows = all.filter(function (b) {
          return placeMatches(b.origin, q) || placeMatches(b.destination, q) ||
                 (b.bus_name || '').toLowerCase().includes(q) ||
                 (b.route || '').toLowerCase().includes(q) ||
                 (b.stoppages || []).some(function (s) { return (s.name || '').toLowerCase().includes(q); });
        }).map(function (b) { return { b: b, fwd: true, depMin: parseTime(b.departure_time) }; });
        if (!rows.length && q.length >= 3) {
          var partial = q.slice(0, 5);
          rows = Object.values(BUSES).filter(function (b) {
            return (b.origin || '').toLowerCase().startsWith(partial) ||
                   (b.destination || '').toLowerCase().startsWith(partial) ||
                   (b.stoppages || []).some(function (s) { return (s.name || '').toLowerCase().startsWith(partial); });
          }).map(function (b) { return { b: b, fwd: true, depMin: parseTime(b.departure_time) }; });
        }
      }

      var now = minutesNow();
      var rel = function (t) { return t == null ? Infinity : (t < now ? t + 1440 : t) - now; };
      rows.sort(function (x, y) { return rel(x.depMin) - rel(y.depMin); });
      var near = rows.filter(function (r) { return r.depMin != null && rel(r.depMin) <= 180; });

      var emptyState = '<div class="empty-state">' + icon('bus') +
        '<p><span class="label-en">No buses found for that route. Try a nearby town instead.</span><span class="label-bn">কোনো বাস পাওয়া যায়নি। কাছাকাছি কোনো শহর চেষ্টা করুন।</span></p>' +
        '<div class="chip-row">' +
        ['Bankura', 'Digha', 'Kolkata', 'Durgapur'].map(function (n) {
          return '<span class="sugg-chip" onclick="quickSearch(' + String.fromCharCode(39) + n + String.fromCharCode(39) + ')">' + esc(n) + '</span>';
        }).join('') + '</div></div>';

      el.innerHTML =
        '<div class="container" style="padding-top:22px;padding-bottom:40px">' +
        freshnessNote() +
        '<div class="back-btn" onclick="location.hash=' + String.fromCharCode(39) + '#/' + String.fromCharCode(39) + '">' + icon('chevronLeft') + ' <span class="label-en">Back</span><span class="label-bn">পিছনে</span></div>' +
        '<h2 class="page-title"><span class="label-en">Search Results</span><span class="label-bn">সার্চ ফলাফল</span> <span style="color:var(--ink-dim);font-family:var(--font-mono);font-size:1rem">(' + rows.length + ')</span></h2>' +
        '<p style="font-size:12px;color:var(--ink-dim);margin:2px 0 4px">Data updated: ' + esc((DATA.meta || {}).last_updated || '') + '</p>' +
        (from || to ? '<p style="color:var(--ink-dim);font-size:13.5px;margin-bottom:18px">' + esc(from || '…') + ' → ' + esc(to || '…') + (stop ? ' <span class="badge badge-ac">stop ' + esc(stop) + '</span>' : '') + '</p>' : '') +
        (stop && !from && !to ? '<p style="color:var(--ink-dim);font-size:13.5px;margin-bottom:18px"><span class="label-en">Buses halting at</span><span class="label-bn">এই স্টপেজে থামে</span> ' + esc(stop) + '</p>' : '') +
        (near.length ? '<p class="near-label">' + icon('clock') + ' <span class="label-en">' + near.length + ' buses around current time</span><span class="label-bn">' + near.length + ' বাস বর্তমান সময়ের কাছাকাছি</span></p>' : '') +
        (rows.length ? rows.map(function (r, i) {
          var b = r.b;
          var isNear = r.depMin != null && rel(r.depMin) <= 180;
          var stopInfo = '';
          if (routeMode && r.fwd && r.atMin != null && r.atMin !== parseTime(b.departure_time)) {
            stopInfo = '<div style="font-size:12.5px;color:var(--amber);font-weight:600;margin-top:2px"><span class="label-en">at your stop (' + esc(r.stopName || '') + '): ' + fmtTime(r.atMin) + '</span><span class="label-bn">আপনার স্টপ (' + esc(pn(r.stopName || '')) + '): ' + fmtTime(r.atMin) + '</span></div>';
          }
          var revBadge = routeMode && !r.fwd ? '<span style="font-size:10px;font-weight:700;color:var(--maroon);border:1px solid var(--maroon);border-radius:6px;padding:2px 7px;margin-left:6px;white-space:nowrap"><span class="label-en">RETURN</span><span class="label-bn">ফেরার বাস</span></span>' : '';
          var tPill = r.depMin != null ? '<span class="time-pill">' + icon('clock') + ' ' + fmtTime(r.depMin) + '</span>' : '';
          return '<div class="result-item ' + (isNear ? 'near' : '') + '" style="--i:' + i + '" onclick="location.hash=' + String.fromCharCode(39) + '#/bus/' + encodeURIComponent(b.id) + String.fromCharCode(39) + '">' +
            '<div class="ri-main">' +
            (isNear ? '<div class="near-label">' + icon('clock') + ' <span class="label-en">Coming up</span><span class="label-bn">আসছে</span></div>' : '') +
            '<div class="name">' + esc(b.bus_name) + (b.reg_no ? ' <span class="reg">' + esc(b.reg_no) + '</span>' : '') + ' ' + busTypeBadge(b.bus_type) + revBadge + '</div>' +
            '<div class="route">' + esc(pn(b.origin)) + ' <span class="rarr">→</span> ' + esc(pn(b.destination)) + '</div>' +
            stopInfo +
            '<div class="meta"><span>' + icon('stops') + ' ' + (b.total_stoppages || (b.stoppages || []).length) + ' stops</span>' +
            (b.operator ? '<span>' + esc(b.operator) + '</span>' : '') +
            (b.fare ? '<span>' + esc(b.fare) + '</span>' : '') + '</div>' +
            '</div>' + tPill + '</div>';
        }).join('') : emptyState) +
        '</div>';
    };
  }

  function runAll() {
    fixWording();
    removeBrowseBtn();
    stripDatalist();
    fixShowAll();
    rebuildCompactStops();
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
