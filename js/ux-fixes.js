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
   7. Departures know directions too: stop pages and the departure
      board list return (down) services, not just outbound ones —
      and stop pages work again (they relied on removed bus_ids).
   8. ONE TIME PER ROW, SERIALLY: no side-by-side up+down pairs.
      Stop searches / stop pages show a single chronological
      departure list — every service in time order, each row one
      departure (up or down), like a real bus-stand board.
   9. Compact share row (Map / WhatsApp / X) and a better route
      map link: waypoints are spread EVENLY across the whole bus
      route (not just the first stops), so Google Maps follows the
      actual road route even for 60+ stop services.
  10. Compact bus page: Stops/Operator/Depot boxes removed (route
      timetable already shows all that), "Via ..." line under the
      route, return journey moved below the timetable, smaller
      weather card, perfect-fit timetable rows, and "Show all
      stops" expands in place (no scroll jump). "+ Add time" is
      now a tiny + that opens a mini box right there — with AM/PM
      defaulting to the OPPOSITE of the other direction's saved
      time (and 0:00 is rejected).
  11. Bus page round 2: schedule legend (From/Return) removed,
      railway badge compact (train icon + name/code/km, no
      "Railway:" word), weather card small with a per-condition
      inline SVG icon (sun/cloud/rain/storm — no image files),
      X button replaced by Facebook share, and same-route buses
      listed right under the return journey box. ux-fixes.css now
      loads AFTER bus-page.css so its overrides actually win.
  12. Place pages (destination cards): proper centered title with
      (total), times run through parseTime+fmtTime (raw "12:65 AM"
      style data garbage can no longer appear), rows sorted from now,
      and the data-refresh line lives at the BOTTOM (was a box on top).
  13. Home page board v3: tabs (Kolkata/Digha/Burdwan) replaced by ONE
      search line — type any bus stand, pick a match, the board shows
      that stand's departures. Duplicate section heading removed (label
      stays inside the box only), clock smaller, "Popular stops" text
      gone, and Popular Routes is now a compact single-line horizontal
      scroller with more routes (14).
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
        var y = window.scrollY || window.pageYOffset || 0;
        try {
          history.replaceState(null, '', target);
          window.dispatchEvent(new HashChangeEvent('hashchange'));
        } catch (err) {
          location.hash = target;
          return;
        }
        var n = 0;
        var restore = function () { window.scrollTo(0, y); if (++n < 8) setTimeout(restore, 40); };
        restore();
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
  function canonName(q) {
    var best = null;
    Object.values(STOPS || {}).forEach(function (s) {
      if (!best && slug(s.name) === slug(q)) best = s.name;
    });
    if (!best) {
      Object.values(BUSES).forEach(function (b) {
        if (!best) {
          if (slug(b.origin) === slug(q)) best = b.origin;
          else if (slug(b.destination) === slug(q)) best = b.destination;
        }
      });
    }
    return best || q;
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
          rows.push({ b: b, fwd: fwd, depMin: depMin });
        });
      } else if (stop) {
        var seenIds = {};
        var nBuses = 0;
        all.forEach(function (b) {
          var mS = null;
          (b.stoppages || []).forEach(function (s) {
            if (!mS && (s.name || '').toLowerCase().includes(stop)) mS = s;
          });
          var isO = (b.origin || '').toLowerCase().includes(stop);
          var isD = (b.destination || '').toLowerCase().includes(stop);
          if (!mS && !isO && !isD) return;
          if (!seenIds[b.id]) { seenIds[b.id] = 1; nBuses++; }
          var tU = mS ? bjFromStop(mS, 'up') : null;
          var tD = mS ? bjFromStop(mS, 'down') : null;
          if (isO) {
            var dO = parseTime(b.departure_time);
            if (dO != null) tU = dO;
          }
          if (tU != null) rows.push({ b: b, fwd: true, depMin: tU });
          if (tD != null) rows.push({ b: b, fwd: false, depMin: tD });
        });
        window.__bjStopCount = nBuses;
        window.__bjDepCount = rows.length;
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

      var titleTxt = routeMode ? canonName(from) + ' → ' + canonName(to)
        : (stop ? canonName(stop) : (from || to || ''));
      var viaHtml = '';
      if (routeMode) {
        var viaCount = {};
        rows.forEach(function (r) {
          var fi2 = bjPosIn(r.b, from), ti2 = bjPosIn(r.b, to);
          if (fi2 < 0 || ti2 < 0) return;
          var lo = Math.min(fi2, ti2), hi = Math.max(fi2, ti2);
          var sts2 = r.b.stoppages || [];
          for (var vi = 0; vi < sts2.length; vi++) {
            if (vi + 1 > lo && vi + 1 < hi && sts2[vi].name) {
              viaCount[sts2[vi].name] = (viaCount[sts2[vi].name] || 0) + 1;
            }
          }
        });
        var viaTop = Object.keys(viaCount).sort(function (a, b) { return viaCount[b] - viaCount[a]; })
          .filter(function (n) { return slug(n) !== slug(from) && slug(n) !== slug(to); }).slice(0, 4);
        if (viaTop.length) {
          viaHtml = '<p style="text-align:center;font-size:12px;color:var(--ink-dim);margin:2px 0 0"><span class="label-en">via </span><span class="label-bn">হয়ে </span>' + esc(viaTop.join(' · ')) + '</p>';
        }
      }
      el.innerHTML =
        '<div class="container" style="padding-top:22px;padding-bottom:40px">' +
        '<div class="back-btn" onclick="location.hash=' + String.fromCharCode(39) + '#/' + String.fromCharCode(39) + '">' + icon('chevronLeft') + ' <span class="label-en">Back</span><span class="label-bn">পিছনে</span></div>' +
        '<h2 class="page-title" style="text-align:center;margin-bottom:2px">' + esc(titleTxt) + ' <span style="color:var(--ink-dim);font-family:var(--font-mono);font-size:1rem">(' + rows.length + ')</span></h2>' +
        viaHtml +
        (stop && !from && !to && window.__bjDepCount ? '<p style="text-align:center;font-size:12px;color:var(--ink-dim);margin:2px 0 0">' + window.__bjStopCount + ' <span class="label-en">buses · </span><span class="label-bn">বাস · </span>' + window.__bjDepCount + ' <span class="label-en">departures today</span><span class="label-bn">আজকের ছাড়ার সময়</span></p>' : '') +
        (stop && !from && !to && window.__bjDepCount ? '<p style="text-align:center;font-size:11px;color:var(--ink-dim);margin:2px 0 10px"><span class="label-en">all in time order</span><span class="label-bn">সময় অনুযায়ী সাজানো</span></p>' : '') +
        (near.length ? '<p class="near-label">' + icon('clock') + ' <span class="label-en">' + near.length + ' buses around current time</span><span class="label-bn">' + near.length + ' বাস বর্তমান সময়ের কাছাকাছি</span></p>' : '') +
        (routeMode || (stop && !from && !to) ? '<p style="font-size:11.5px;color:var(--ink-dim);margin:0 0 10px"><b style="color:var(--amber)">⇗</b> <span class="label-en">outward · </span><span class="label-bn">যাত্রা · </span><b style="color:var(--maroon)">⇙</b> <span class="label-en">return service</span><span class="label-bn">ফেরার বাস</span></p>' : '') +
        (rows.length ? rows.map(function (r, i) {
          var b = r.b;
          var isNear = r.depMin != null && rel(r.depMin) <= 180;
          var isRet = (routeMode || (stop && !from && !to)) && !r.fwd;
          var revBadge = isRet ? '<span style="font-size:10px;font-weight:700;color:var(--maroon);border:1px solid var(--maroon);border-radius:6px;padding:2px 7px;margin-left:6px;white-space:nowrap"><span class="label-en">RETURN</span><span class="label-bn">ফেরার বাস</span></span>' : '';
          var ro = isRet ? b.destination : b.origin;
          var rd = isRet ? b.origin : b.destination;
          var tPill = r.depMin != null ? '<span class="time-pill">' + icon('clock') + ' ' + fmtTime(r.depMin) + (isNear ? ' · <b style="color:var(--amber)">' + countdownText(rel(r.depMin)) + '</b>' : '') + '</span>' : '';
          return '<div class="result-item ' + (isNear ? 'near' : '') + '" style="--i:' + i + '" onclick="location.hash=' + String.fromCharCode(39) + '#/bus/' + encodeURIComponent(b.id) + String.fromCharCode(39) + '">' +
            '<div class="ri-main">' +
            (isNear ? '<div class="near-label">' + icon('clock') + ' <span class="label-en">Coming up</span><span class="label-bn">আসছে</span></div>' : '') +
            '<div class="name">' + esc(b.bus_name) + (b.reg_no ? ' <span class="reg">' + esc(b.reg_no) + '</span>' : '') + ' ' + busTypeBadge(b.bus_type) + revBadge + '</div>' +
            '<div class="route">' + esc(pn(ro)) + ' <span class="rarr">→</span> ' + esc(pn(rd)) + '</div>' +
            '<div class="meta"><span>' + icon('stops') + ' ' + (b.total_stoppages || (b.stoppages || []).length) + ' stops</span>' +
            (b.operator ? '<span>' + esc(b.operator) + '</span>' : '') +
            (b.fare ? '<span>' + esc(b.fare) + '</span>' : '') + '</div>' +
            '</div>' + tPill + '</div>';
        }).join('') : emptyState) +
        '<p style="text-align:center;font-size:11px;color:var(--ink-dim);margin:18px 0 0;border-top:1px solid var(--line,rgba(33,28,22,.13));padding-top:10px"><span class="label-en">Data last refreshed: </span><span class="label-bn">শেষ হালনাগাদ: </span><strong>' + esc((DATA.meta || {}).last_updated || '—') + '</strong> · <span class="label-en">Schedules may change. Verify with the operator before travel.</span><span class="label-bn">সময়সূচি বদলাতে পারে। যাত্রার আগে যাচাই করে নিন।</span></p>' +
        '</div>';
    };
  }

  /* ---- 6b. Place pages (destination cards): clean header, safe times ---- */
  if (typeof renderPlace === 'function' && !window.__bjPlaceV2) {
    window.__bjPlaceV2 = true;
    renderPlace = function (el, placeName) {
      rebuildCompactStops();
      var q = placeName.toLowerCase();
      var related = Object.values(BUSES).filter(function (b) {
        return (b.origin || '').toLowerCase().includes(q) ||
               (b.destination || '').toLowerCase().includes(q) ||
               (b.stoppages || []).some(function (s) { return (s.name || '').toLowerCase().includes(q); });
      });
      var nowM = minutesNow();
      related.sort(function (x, y) {
        var tx = parseTime(x.departure_time), ty = parseTime(y.departure_time);
        if (tx == null && ty == null) return 0;
        if (tx == null) return 1;
        if (ty == null) return -1;
        var ax = tx < nowM ? tx + 1440 : tx;
        var ay = ty < nowM ? ty + 1440 : ty;
        return ax - ay;
      });
      var near2 = related.filter(function (b) {
        var t = parseTime(b.departure_time);
        return t != null && (t < nowM ? t + 1440 : t) - nowM <= 180;
      }).length;
      el.innerHTML =
        '<div class="container" style="padding-top:22px;padding-bottom:40px">' +
        '<div class="back-btn" onclick="location.hash=' + String.fromCharCode(39) + '#/' + String.fromCharCode(39) + '">' + icon('chevronLeft') + ' <span class="label-en">Back</span><span class="label-bn">পিছনে</span></div>' +
        '<h2 class="page-title" style="text-align:center;margin-bottom:2px">' + esc(placeName) + ' <span style="color:var(--ink-dim);font-family:var(--font-mono);font-size:1rem">(' + related.length + ')</span></h2>' +
        '<p style="text-align:center;font-size:12px;color:var(--ink-dim);margin:2px 0 0">' + related.length + ' <span class="label-en">buses · </span><span class="label-bn">বাস · </span>' + near2 + ' <span class="label-en">around current time</span><span class="label-bn">বর্তমান সময়ের কাছাকাছি</span></p>' +
        (near2 ? '<p class="near-label">' + icon('clock') + ' <span class="label-en">' + near2 + ' buses around current time</span><span class="label-bn">' + near2 + ' বাস বর্তমান সময়ের কাছাকাছি</span></p>' : '') +
        related.map(function (b, i) {
          var t = parseTime(b.departure_time);
          var dd = t == null ? null : (t < nowM ? t + 1440 : t) - nowM;
          var tPill = t != null ? '<span class="time-pill">' + icon('clock') + ' ' + fmtTime(t) + (dd != null && dd <= 180 ? ' · <b style="color:var(--amber)">' + countdownText(dd) + '</b>' : '') + '</span>' : '';
          return '<div class="result-item' + (dd != null && dd <= 180 ? ' near' : '') + '" style="--i:' + i + '" onclick="location.hash=' + String.fromCharCode(39) + '#/bus/' + encodeURIComponent(b.id) + String.fromCharCode(39) + '">' +
            '<div class="ri-main">' +
            (dd != null && dd <= 180 ? '<div class="near-label">' + icon('clock') + ' <span class="label-en">Coming up</span><span class="label-bn">আসছে</span></div>' : '') +
            '<div class="name">' + esc(b.bus_name) + ' ' + busTypeBadge(b.bus_type) + '</div>' +
            '<div class="route">' + esc(pn(b.origin)) + ' <span class="rarr">→</span> ' + esc(pn(b.destination)) + '</div>' +
            '<div class="meta"><span>' + icon('stops') + ' ' + (b.total_stoppages || (b.stoppages || []).length || 0) + ' stops</span></div>' +
            '</div>' + tPill + '</div>';
        }).join('') +
        '<p style="text-align:center;font-size:11px;color:var(--ink-dim);margin:18px 0 0;border-top:1px solid var(--line,rgba(33,28,22,.13));padding-top:10px"><span class="label-en">Data last refreshed: </span><span class="label-bn">শেষ হালনাগাদ: </span><strong>' + esc((DATA.meta || {}).last_updated || '—') + '</strong> · <span class="label-en">Schedules may change. Verify with the operator before travel.</span><span class="label-bn">সময়সূচি বদলাতে পারে। যাত্রার আগে যাচাই করে নিন।</span></p>' +
        '</div>';
    };
  }

  /* ---- 7. Direction-aware departures: board + stop pages ---- */
  function bjBusesAt(slugKey) {
    var out = [];
    Object.values(BUSES).forEach(function (b) {
      var sts = b.stoppages || [];
      for (var k = 0; k < sts.length; k++) {
        if (slug(sts[k].name) === slugKey) { out.push(b); return; }
      }
      if (slug(b.origin) === slugKey || slug(b.destination) === slugKey) out.push(b);
    });
    return out;
  }
  function bjDepsAt(slugKey, limit) {
    var now = minutesNow();
    var out = [];
    Object.values(BUSES).forEach(function (b) {
      var sts = b.stoppages || [];
      for (var k = 0; k < sts.length; k++) {
        if (slug(sts[k].name) !== slugKey) continue;
        var tu = bjFromStop(sts[k], 'up');
        var td = bjFromStop(sts[k], 'down');
        if (tu != null) { var d = tu - now; if (d < 0) d += 1440; out.push({ b: b, t: tu, diff: d, dir: 'up' }); }
        if (td != null) { var d2 = td - now; if (d2 < 0) d2 += 1440; out.push({ b: b, t: td, diff: d2, dir: 'down' }); }
        break;
      }
      if (slug(b.origin) === slugKey) {
        var tu2 = parseTime(b.departure_time);
        if (tu2 != null) { var d3 = tu2 - now; if (d3 < 0) d3 += 1440; out.push({ b: b, t: tu2, diff: d3, dir: 'up' }); }
      }
    });
    out.sort(function (x, y) { return x.diff - y.diff; });
    return out.slice(0, limit || 10);
  }

  if (typeof stopDepartures === 'function' && !window.__bjDepsV2) {
    window.__bjDepsV2 = true;
    stopDepartures = function (slugKey, busIds, limit) {
      return bjDepsAt(slugKey, limit);
    };
  }

  if (typeof renderBoard === 'function' && !window.__bjBoardV2) {
    window.__bjBoardV2 = true;
    renderBoard = function () {
      rebuildCompactStops();
      var wrap = document.getElementById('lvBoard');
      if (!wrap) return;
      if (!lvOrigin) lvOrigin = lvGetOrigins()[0].name;
      var origins = lvGetOrigins();
      var now = minutesNow();
      var clockT = new Date().toLocaleTimeString('en-IN', { hour12: false, timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit' });
      var deps = bjDepsAt(slug(lvOrigin), 10);
      var rows = '';
      if (deps.length) {
        var nextIdx = -1;
        for (var z = 0; z < deps.length; z++) { if (deps[z].diff > 0) { nextIdx = z; break; } }
        var allPast = nextIdx < 0;
        var idx = allPast ? 0 : nextIdx;
        rows = deps.map(function (n, i) {
          var cls = '', right = '';
          if (i === idx) {
            cls = 'next';
            right = '<span class="ltag">' + (allPast ? (LANG === 'bn' ? 'কাল +' : 'tmrw +') : (LANG === 'bn' ? 'এখন +' : 'in ')) + countdownText(n.diff) + '</span>';
          } else if (i > idx && !allPast) {
            right = '<span class="lgone">+' + countdownText(n.diff) + '</span>';
          } else {
            cls = 'past';
            right = '<span class="lgone">✓ ' + (LANG === 'bn' ? 'চলে গেছে' : 'departed') + '</span>';
          }
          var head = n.dir === 'down' ? n.b.origin : n.b.destination;
          var ret = n.dir === 'down' ? ' <span style="color:var(--maroon);font-weight:700">⇙</span>' : '';
          return '<div class="lv-row ' + cls + '" style="animation-delay:' + (i * 0.07) + 's" onclick="location.hash=' + String.fromCharCode(39) + '#/bus/' + encodeURIComponent(n.b.id) + String.fromCharCode(39) + '">' +
            '<span class="lt">' + fmtTime(n.t).replace(' ', '') + '</span>' +
            '<span class="lnm">' + esc(n.b.bus_name) + ret + '</span>' +
            '<span class="ldst">→ ' + esc(pn(head)) + '</span>' +
            right + '</div>';
        }).join('');
      } else {
        rows = '<div class="lv-row"><span class="lnm">' + (LANG === 'bn' ? 'সময়ের তথ্য নেই' : 'No timed departures listed') + '</span></div>';
      }
      var geoHtml = lvNear.length
        ? '<div class="lv-geo"><span class="label-en">Detected near</span><span class="label-bn">কাছাকাছি শনাক্ত</span><b>' + esc(lvNear[0].name) + '</b>' + (lvNear[0].dist != null ? '<span>' + Math.round(lvNear[0].dist) + ' km</span>' : '') + '</div>'
        : '';
      var savedQ = window.__bjLvQ || '';
      wrap.innerHTML =
        '<div class="lv-clock-wrap">' +
        '<div><div class="lv-clock-label"><span class="label-en">Bus Stand Departure Times</span><span class="label-bn">বাস স্ট্যান্ডের ছাড়ার সময়</span></div>' +
        '<div class="lv-clock-big">' + clockT + '<small>IST</small></div></div>' + geoHtml + '</div>' +
        '<div class="lv-board">' +
        '<div class="lv-search"><input id="lvSearchInput" type="text" autocomplete="off" placeholder="' + (LANG === 'bn' ? 'বাস স্ট্যান্ড লিখুন…' : 'Type a bus stand…') + '" value="' + escHtml(savedQ) + '" aria-label="Search bus stand"></div>' +
        '<div id="lvRows">' + rows + '</div></div>';
    };
  }

  if (typeof renderStop === 'function' && !window.__bjStopV2) {
    window.__bjStopV2 = true;
    renderStop = function (el, slugKey) {
      rebuildCompactStops();
      var stop = null;
      Object.values(STOPS).forEach(function (s) {
        if (!stop && slug(s.name) === slugKey) stop = s;
      });
      if (!stop) {
        el.innerHTML = '<div class="container" style="padding:40px"><div class="empty-state">' + icon('alert') + '<p>Stop not found.</p></div></div>';
        return;
      }
      var buses = bjBusesAt(slugKey);
      var stn = stop.nearest_station;
      var next = bjDepsAt(slugKey, 6);
      el.innerHTML =
        '<div class="container" style="padding-top:22px;padding-bottom:40px">' +
        '<div class="back-btn" onclick="location.hash=' + String.fromCharCode(39) + '#/' + String.fromCharCode(39) + '">' + icon('chevronLeft') + ' <span class="label-en">Back</span><span class="label-bn">পিছনে</span></div>' +
        '<h2 class="page-title">' + esc(LANG === 'bn' ? pn(stop.name) : stop.name) + '</h2>' +
        '<p style="color:var(--ink-dim);margin-bottom:14px">' + buses.length + ' <span class="label-en">buses pass through</span><span class="label-bn">বাস চলাচল করে</span></p>' +
        (stn ? '<div class="info-item" style="margin:0 0 16px"><div class="lbl">' + icon('train') + ' <span class="label-en">Nearest railway station</span><span class="label-bn">নিকটতম রেলওয়ে স্টেশন</span></div><div class="val">' + esc(stn.name) + (stn.code ? ' (' + esc(stn.code) + ')' : '') + (stn.km != null ? ' · ~' + stn.km + ' km' : '') + '</div></div>' : '') +
        (next.length ? '<h3 class="timetable-title" style="margin-top:8px">' + icon('clock') + ' <span class="label-en">Next buses from ' + esc(stop.name) + '</span><span class="label-bn">' + esc(stop.name) + ' থেকে পরবর্তী বাস</span></h3>' +
          '<p style="font-size:11.5px;color:var(--ink-dim);margin:0 0 10px"><b style="color:var(--amber)">⇗</b> <span class="label-en">outward · </span><span class="label-bn">যাত্রা · </span><b style="color:var(--maroon)">⇙</b> <span class="label-en">return</span><span class="label-bn">ফেরার বাস</span></p>' +
          next.map(function (n) {
            var head = n.dir === 'down' ? n.b.origin : n.b.destination;
            var ret = n.dir === 'down' ? ' <span style="color:var(--maroon);font-weight:700">⇙</span>' : ' <span style="color:var(--amber);font-weight:700">⇗</span>';
            return '<div class="result-item" onclick="location.hash=' + String.fromCharCode(39) + '#/bus/' + encodeURIComponent(n.b.id) + String.fromCharCode(39) + '">' +
              '<div class="ri-main"><div class="name">' + esc(n.b.bus_name) + ret + '</div>' +
              '<div class="route">' + esc(pn(head)) + '</div></div>' +
              '<span class="time-pill">' + icon('clock') + ' ' + fmtTime(n.t) + ' · <span style="color:var(--amber);font-weight:700" data-nbdep="' + n.t + '">' + countdownText(n.diff) + '</span></span></div>';
          }).join('') : '') +
        '<a class="map-btn" href="https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(stop.name + ', West Bengal, India') + '" target="_blank" rel="noopener">' + icon('map') + ' View on Google Maps</a>' +
        (function () {
          var allDeps = [];
          buses.forEach(function (b) {
            var m = null;
            (b.stoppages || []).forEach(function (s) { if (!m && slug(s.name) === slugKey) m = s; });
            var tU = m ? bjFromStop(m, 'up') : null;
            var tD = m ? bjFromStop(m, 'down') : null;
            if (slug(b.origin) === slugKey) {
              var dO = parseTime(b.departure_time);
              if (dO != null) tU = dO;
            }
            if (tU != null) allDeps.push({ b: b, t: tU, fwd: true });
            if (tD != null) allDeps.push({ b: b, t: tD, fwd: false });
          });
          var nowM = minutesNow();
          allDeps.sort(function (x, y) {
            var ax = x.t < nowM ? x.t + 1440 : x.t;
            var ay = y.t < nowM ? y.t + 1440 : y.t;
            return ax - ay;
          });
          return allDeps.map(function (n, i) {
            var isRet = !n.fwd;
            var head = isRet ? n.b.origin : n.b.destination;
            var tail = isRet ? n.b.destination : n.b.origin;
            var dd = n.t - nowM; if (dd < 0) dd += 1440;
            var near = dd <= 180 ? ' · <b style="color:var(--amber)">' + countdownText(dd) + '</b>' : '';
            var badge = isRet ? ' <span style="font-size:10px;font-weight:700;color:var(--maroon);border:1px solid var(--maroon);border-radius:6px;padding:2px 7px;white-space:nowrap"><span class="label-en">RETURN</span><span class="label-bn">ফেরার বাস</span></span>' : '';
            return '<div class="result-item" style="--i:' + i + '" onclick="location.hash=' + String.fromCharCode(39) + '#/bus/' + encodeURIComponent(n.b.id) + String.fromCharCode(39) + '">' +
              '<div class="ri-main"><div class="name">' + esc(n.b.bus_name) + badge + '</div>' +
              '<div class="route">' + esc(pn(tail)) + ' <span class="rarr">→</span> ' + esc(pn(head)) + '</div>' +
              '<div class="meta"><span>' + icon('stops') + ' ' + ((n.b.stoppages || []).length || n.b.total_stoppages || 0) + ' stops</span></div></div>' +
              '<span class="time-pill">' + icon('clock') + ' ' + fmtTime(n.t) + near + '</span></div>';
          }).join('');
        })() +
        '</div>';
      startNextBusTicker();
    };
  }

  /* ---- 8b. Compact share row + full-route map link ---- */
  var BJ_LABELS = {
    'Route on Google Maps': 'Map',
    'View route on Google Maps': 'Map',
    'গুগল ম্যাপে রুট দেখুন': 'ম্যাপ',
    'Share on WhatsApp': 'WhatsApp',
    'শেয়ার করুন': 'শেয়ার',
    'Share on X': 'X'
  };
  var FB_SVG = '<svg viewBox="0 0 24 24" style="width:14px;height:14px" fill="currentColor" aria-hidden="true"><path d="M13.5 21v-8h2.7l.4-3.1h-3.1V7.9c0-.9.25-1.5 1.55-1.5h1.65V3.6c-.3-.04-1.3-.13-2.45-.13-2.4 0-4.05 1.47-4.05 4.15v2.3H7.4V13h2.75v8h3.35z"/></svg>';
  function compactShareRow() {
    document.querySelectorAll('.wa-row .map-btn, .wa-row .wa-btn, .wa-row .share-x-btn').forEach(function (btn) {
      if (btn.classList.contains('share-x-btn') && !btn.dataset.bjFb) {
        btn.dataset.bjFb = '1';
        btn.removeAttribute('onclick');
        btn.innerHTML = FB_SVG + ' <span class="label-en">Share</span><span class="label-bn">শেয়ার</span>';
        btn.addEventListener('click', function () {
          window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(location.href), '_blank', 'noopener');
        });
      }
      btn.querySelectorAll('.label-en, .label-bn').forEach(function (sp) {
        var t = (sp.textContent || '').trim();
        if (BJ_LABELS[t]) sp.textContent = BJ_LABELS[t];
      });
    });
  }
  function fixMapLink() {
    if (location.hash.indexOf('#/bus/') !== 0) return;
    var links = document.querySelectorAll('.wa-row a.map-btn[href*="google.com/maps/dir"]');
    if (!links.length) return;
    var id = decodeURIComponent(location.hash.split('?')[0].slice(6));
    var b = (typeof FULL_BUSES !== 'undefined' && FULL_BUSES && FULL_BUSES[id]) || BUSES[id];
    if (!b) return;
    var seq = [];
    function push(n) { if (n && seq[seq.length - 1] !== n) seq.push(n); }
    push(b.origin);
    (b.stoppages || []).forEach(function (s) { if (s && s.name) push(s.name); });
    push(b.destination);
    if (seq.length < 3) return;
    var inter = seq.slice(1, -1);
    var MAXW = 9;
    var wp = [];
    if (inter.length <= MAXW) {
      wp = inter;
    } else {
      for (var i = 0; i < MAXW; i++) {
        var k = Math.round(i * (inter.length - 1) / (MAXW - 1));
        if (wp.indexOf(inter[k]) === -1) wp.push(inter[k]);
      }
    }
    var url = 'https://www.google.com/maps/dir/?api=1&origin=' +
      encodeURIComponent(seq[0] + ', West Bengal') +
      '&destination=' + encodeURIComponent(seq[seq.length - 1] + ', West Bengal') +
      (wp.length ? '&waypoints=' + wp.map(function (n2) { return encodeURIComponent(n2 + ', West Bengal'); }).join('|') : '') +
      '&travelmode=driving';
    links.forEach(function (a) {
      a.href = url;
      a.dataset.mapFixed = '1';
    });
  }

  /* ---- 10. Compact bus page + mini add-time box ---- */
  function compactBusPage() {
    if (location.hash.indexOf('#/bus/') !== 0) return;
    var head = document.querySelector('.bus-head');
    if (!head) return;
    head.querySelectorAll('.info-item').forEach(function (it) {
      var lbl = ((it.querySelector('.lbl') || {}).textContent || '').trim().toLowerCase();
      if (lbl === 'stops' || lbl === 'operator' || lbl === 'depot') it.remove();
    });
    var grid = head.querySelector('.info-grid');
    if (grid && !grid.querySelector('.info-item')) grid.remove();
    var rl = head.querySelector('.route-line');
    if (rl && !head.querySelector('.via-line')) {
      var id = decodeURIComponent(location.hash.split('?')[0].slice(6));
      var b = (typeof FULL_BUSES !== 'undefined' && FULL_BUSES && FULL_BUSES[id]) || BUSES[id];
      var sts = (b && b.stoppages) || [];
      var via = [];
      for (var i = 1; i < sts.length - 1 && via.length < 6; i++) {
        var nm = sts[i] && sts[i].name;
        if (nm && via.indexOf(nm) === -1) via.push(nm);
      }
      if (via.length) {
        var extra = sts.length - 2 > via.length ? ' …' : '';
        var d = document.createElement('div');
        d.className = 'via-line';
        d.innerHTML = '<span class="label-en">Via: </span><span class="label-bn">হয়ে: </span>' + escHtml(via.join(' · ')) + extra;
        rl.parentNode.insertBefore(d, rl.nextSibling);
      }
    }
    var rj = head.querySelector('.return-journey');
    var table = document.querySelector('.schedule-table');
    if (rj && table && rj.parentNode !== table.parentNode) {
      table.parentNode.insertBefore(rj, table.nextSibling);
    }
    document.querySelectorAll('.add-time-btn').forEach(function (btn) {
      if (btn.textContent.indexOf('+ Add time') === 0) {
        btn.textContent = '+';
        btn.title = 'Add time';
      }
    });
    document.querySelectorAll('.schedule-legend').forEach(function (lg) { lg.remove(); });
    document.querySelectorAll('.rail').forEach(function (el) {
      if (el.dataset.bjRail) return;
      el.dataset.bjRail = '1';
      var t = el.textContent.replace('Railway:', '').replace('~', '').replace(/ +/g, ' ').trim();
      el.innerHTML = icon('train') + ' ' + escHtml(t);
    });
    fixWeatherIcon();
    if (rj && !document.querySelector('.bj-relbuses')) {
      var rid = decodeURIComponent(location.hash.split('?')[0].slice(6));
      var rb = (typeof FULL_BUSES !== 'undefined' && FULL_BUSES && FULL_BUSES[rid]) || BUSES[rid];
      if (rb) {
        var rel = [];
        Object.values(BUSES).forEach(function (o) {
          if (o.id === rb.id || rel.length >= 4) return;
          if ((o.origin === rb.origin && o.destination === rb.destination) ||
              (o.origin === rb.destination && o.destination === rb.origin)) {
            rel.push({ o: o, t: parseTime(o.departure_time) });
          }
        });
        rel.sort(function (x, y) { return (x.t == null ? 9999 : x.t) - (y.t == null ? 9999 : y.t); });
        if (rel.length) {
          var sec = document.createElement('div');
          sec.className = 'bj-relbuses';
          sec.innerHTML = '<div class="bj-rel-title">' + icon('bus') + ' <span class="label-en">More buses on this route</span><span class="label-bn">এই রুটের আরও বাস</span></div>' +
            rel.map(function (r) {
              var tt = r.t != null ? fmtTime(r.t) : '—';
              return '<a class="bj-rel-item" href="#/bus/' + encodeURIComponent(r.o.id) + '"><b>' + tt + '</b> ' + escHtml(r.o.bus_name || '') + '</a>';
            }).join('');
          rj.parentNode.insertBefore(sec, rj.nextSibling);
        }
      }
    }
  }

  var WX_ICONS = {
    thunder: '<svg viewBox="0 0 24 24" style="width:20px;height:20px;flex:0 0 auto" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.5 13a4.5 4.5 0 0 0-1-8.9 6 6 0 0 0-11.4 2A3.5 3.5 0 0 0 6 13h11.5z" fill="rgba(122,34,48,.15)"/><path d="m12.5 13-2.2 4h3l-2.2 4.5" stroke="#7a2230"/></svg>',
    rain: '<svg viewBox="0 0 24 24" style="width:20px;height:20px;flex:0 0 auto" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.5 14a4.5 4.5 0 0 0-1-8.9 6 6 0 0 0-11.4 2A3.5 3.5 0 0 0 6 14h11.5z" fill="rgba(60,90,150,.15)"/><path d="M8 17.5v2.5M12 16.5v3M16 17.5v2.5"/></svg>',
    snow: '<svg viewBox="0 0 24 24" style="width:20px;height:20px;flex:0 0 auto" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.5 14a4.5 4.5 0 0 0-1-8.9 6 6 0 0 0-11.4 2A3.5 3.5 0 0 0 6 14h11.5z" fill="rgba(120,140,160,.18)"/><path d="M8 17v3M12 16.5v3.5M16 17v3"/></svg>',
    cloud: '<svg viewBox="0 0 24 24" style="width:20px;height:20px;flex:0 0 auto" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.5 15a4.5 4.5 0 0 0-1-8.9 6 6 0 0 0-11.4 2A3.5 3.5 0 0 0 6 15h11.5z" fill="rgba(120,120,120,.15)"/></svg>',
    sun: '<svg viewBox="0 0 24 24" style="width:20px;height:20px;flex:0 0 auto" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4" fill="rgba(230,160,30,.25)"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.6 4.6l1.8 1.8M17.6 17.6l1.8 1.8M19.4 4.6l-1.8 1.8M6.4 17.6l-1.8 1.8"/></svg>',
    fog: '<svg viewBox="0 0 24 24" style="width:20px;height:20px;flex:0 0 auto" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M17.5 11a4.5 4.5 0 0 0-1-8.9 6 6 0 0 0-11.4 2A3.5 3.5 0 0 0 6 11h11.5z" fill="rgba(120,120,120,.12)"/><path d="M5 15h14M7 18.5h10"/></svg>'
  };
  function fixWeatherIcon() {
    var card = document.getElementById('weatherCard');
    if (!card) return;
    var val = card.querySelector('.val');
    if (!val || val.dataset.bjWx) return;
    var txt = (val.textContent || '').toLowerCase();
    var key = null;
    if (txt.indexOf('thunder') > -1) key = 'thunder';
    else if (txt.indexOf('drizzle') > -1 || txt.indexOf('rain') > -1 || txt.indexOf('shower') > -1) key = 'rain';
    else if (txt.indexOf('snow') > -1) key = 'snow';
    else if (txt.indexOf('fog') > -1 || txt.indexOf('mist') > -1) key = 'fog';
    else if (txt.indexOf('clear') > -1) key = 'sun';
    else if (txt.indexOf('cloud') > -1 || txt.indexOf('overcast') > -1) key = 'cloud';
    if (!key) return;
    val.dataset.bjWx = '1';
    val.innerHTML = WX_ICONS[key] + '<span>' + escHtml(val.textContent.trim()) + '</span>';
  }

  if (typeof addCommunityTime === 'function' && !window.__bjAddTimeV2) {
    window.__bjAddTimeV2 = true;
    addCommunityTime = function (busId, stopIndex, direction) {
      document.querySelectorAll('.bj-timebox').forEach(function (x) { x.remove(); });
      var other = communityTimes()[communityTimeKey(busId, stopIndex, direction === 'up' ? 'down' : 'up')];
      var otherMer = other ? (other.indexOf('PM') > -1 ? 'PM' : 'AM') : null;
      var mer = otherMer === 'AM' ? 'PM' : 'AM';
      var box = document.createElement('div');
      box.className = 'bj-timebox';
      box.innerHTML = '<input type="tel" placeholder="11:30" maxlength="5" aria-label="time">' +
        '<button type="button" class="bj-mer"></button>' +
        '<button type="button" class="bj-ok">✓</button>' +
        '<button type="button" class="bj-no">✕</button>';
      var input = box.querySelector('input');
      var merBtn = box.querySelector('.bj-mer');
      function paint() {
        merBtn.textContent = mer;
        merBtn.className = 'bj-mer' + (mer === 'PM' ? ' pm' : '') + (otherMer && mer === otherMer ? ' warn' : '');
      }
      paint();
      merBtn.addEventListener('click', function () { mer = mer === 'AM' ? 'PM' : 'AM'; paint(); input.focus(); });
      function save() {
        var v = normalizeCommunityTime(input.value + ' ' + mer);
        if (!v) { input.value = ''; input.placeholder = '11:30?'; input.focus(); return; }
        var times = communityTimes();
        times[communityTimeKey(busId, stopIndex, direction)] = v;
        try { localStorage.setItem(COMMUNITY_TIME_KEY, JSON.stringify(times)); } catch (e) {}
        box.remove();
        render();
      }
      box.querySelector('.bj-ok').addEventListener('click', save);
      box.querySelector('.bj-no').addEventListener('click', function () { box.remove(); });
      input.addEventListener('keydown', function (e) { if (e.key === 'Enter') save(); });
      document.body.appendChild(box);
      setTimeout(function () { input.focus(); }, 60);
    };
  }

  /* ---- 13b. Board stand-search wiring (delegated, survives re-renders) ---- */
  document.addEventListener('input', function (e) {
    if (e.target.id !== 'lvSearchInput') return;
    var q = e.target.value;
    window.__bjLvQ = q;
    var dr = document.querySelector('.lv-mdrop');
    if (dr) dr.remove();
    if (!q.trim() || q.trim().length < 2) return;
    var m = findMatches(q).slice(0, 6);
    if (!m.length) return;
    var box = e.target.closest('.lv-search');
    if (!box) return;
    var d = document.createElement('div');
    d.className = 'lv-mdrop';
    d.innerHTML = m.map(function (n) { return '<div class="lv-m-item">' + escHtml(n) + '</div>'; }).join('');
    box.appendChild(d);
  });
  document.addEventListener('click', function (e) {
    var it = e.target.closest ? e.target.closest('.lv-m-item') : null;
    if (it) {
      window.__bjLvQ = it.textContent;
      lvOrigin = it.textContent;
      var dr0 = document.querySelector('.lv-mdrop');
      if (dr0) dr0.remove();
      renderBoard();
      return;
    }
    var dr2 = document.querySelector('.lv-mdrop');
    if (dr2 && !(e.target.closest && e.target.closest('.lv-search'))) dr2.remove();
  });

  /* ---- 13c. More popular routes (14) ---- */
  if (typeof computePopularRoutes === 'function' && !window.__bjPopRoutesV2) {
    window.__bjPopRoutesV2 = true;
    computePopularRoutes = function () {
      var pair = {};
      Object.values(BUSES).forEach(function (b) {
        var o = (b.origin || '').trim(), d = (b.destination || '').trim();
        if (o && d && o !== d) {
          var key = o + '||' + d;
          pair[key] = (pair[key] || 0) + 1;
        }
      });
      return Object.entries(pair).sort(function (a, b) { return b[1] - a[1]; }).slice(0, 14)
        .map(function (e2) { var p2 = e2[0].split('||'); return { from: p2[0], to: p2[1], n: e2[1] }; });
    };
  }

  function runAll() {
    fixWording();
    removeBrowseBtn();
    stripDatalist();
    fixShowAll();
    rebuildCompactStops();
    compactShareRow();
    fixMapLink();
    compactBusPage();
    document.querySelectorAll('.section-title').forEach(function (t) {
      var x = t.textContent || '';
      if (x.indexOf('Bus Stand Departure Times') > -1 || x.indexOf('বাস স্ট্যান্ডের ছাড়ার সময়') > -1) t.remove();
    });
    document.querySelectorAll('.container .data-trust').forEach(function (dt) {
      var c = dt.closest('.container');
      if (c && c.lastElementChild !== dt) c.appendChild(dt);
    });
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
