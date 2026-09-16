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
      Every row shows BOTH times at the from-stop: out + return.
   7. Departures know directions too: stop pages and the departure
      board list return (down) services, not just outbound ones —
      and stop pages work again (they relied on removed bus_ids).
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
          var upMin = null, dnMin = null;
          var stL = (b.stoppages || []).length;
          if (fi >= 1 && fi <= stL) {
            upMin = bjFromStop(b.stoppages[fi - 1], 'up');
            dnMin = bjFromStop(b.stoppages[fi - 1], 'down');
          }
          rows.push({ b: b, fwd: fwd, depMin: depMin, upMin: upMin, dnMin: dnMin,
                      stopName: bjStopName(b, fi) });
        });
      } else if (stop) {
        rows = all.filter(function (b) {
          return (b.stoppages || []).some(function (s) { return (s.name || '').toLowerCase().includes(stop); }) ||
                 (b.origin || '').toLowerCase().includes(stop) ||
                 (b.destination || '').toLowerCase().includes(stop);
        }).map(function (b) {
          var m = null;
          (b.stoppages || []).forEach(function (s) {
            if (!m && (s.name || '').toLowerCase().includes(stop)) m = s;
          });
          return { b: b, fwd: true, depMin: parseTime(b.departure_time),
                   upMin: m ? bjFromStop(m, 'up') : null, dnMin: m ? bjFromStop(m, 'down') : null };
        });
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
        (routeMode || stop ? '<p style="font-size:11.5px;color:var(--ink-dim);margin:0 0 10px"><b style="color:var(--amber)">⇗</b> <span class="label-en">outward · </span><span class="label-bn">যাত্রা · </span><b style="color:var(--maroon)">⇙</b> <span class="label-en">return, at your stop</span><span class="label-bn">ফেরার বাস, আপনার স্টপে</span></p>' : '') +
        (rows.length ? rows.map(function (r, i) {
          var b = r.b;
          var isNear = r.depMin != null && rel(r.depMin) <= 180;
          var stopInfo = '';
          if ((routeMode || stop) && (r.upMin != null || r.dnMin != null)) {
            var tU = r.upMin != null ? fmtTime(r.upMin) : null;
            var tD = r.dnMin != null ? fmtTime(r.dnMin) : null;
            var em = function (t, hot) { return hot ? '<b style="color:var(--amber)">' + t + '</b>' : t; };
            stopInfo = '<div style="font-size:12.5px;font-weight:600;margin-top:2px;color:var(--ink-dim)">' +
              (tU ? '<b style="color:var(--amber)">⇗</b> ' + em(tU, r.fwd) : '') +
              (tU && tD ? ' · ' : '') +
              (tD ? '<b style="color:var(--maroon)">⇙</b> ' + em(tD, !r.fwd) : '') +
              '</div>';
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
        : '<div class="lv-geo"><span class="label-en">Popular stops</span><span class="label-bn">জনপ্রিয় স্টপ</span></div>';
      wrap.innerHTML =
        '<div class="lv-clock-wrap">' +
        '<div><div class="lv-clock-label"><span class="label-en">Bus Stand Departure Times</span><span class="label-bn">বাস স্ট্যান্ডের ছাড়ার সময়</span></div>' +
        '<div class="lv-clock-big">' + clockT + '<small>IST</small></div></div>' + geoHtml + '</div>' +
        '<div class="lv-board"><div class="lv-tabs">' + origins.map(function (o) {
          return '<button class="lv-tab' + (o.name === lvOrigin ? ' on' : '') + '" onclick="lvOrigin=' + String.fromCharCode(39) + o.name.replace(/'/g, '') + String.fromCharCode(39) + ';renderBoard()">' + esc(o.name) + (o.dist != null ? '<span class="dist">' + Math.round(o.dist) + 'km</span>' : '') + '</button>';
        }).join('') + '</div><div id="lvRows">' + rows + '</div></div>';
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
        buses.map(function (b, i) {
          var m = null;
          (b.stoppages || []).forEach(function (s) { if (!m && slug(s.name) === slugKey) m = s; });
          var tU = m ? bjFromStop(m, 'up') : null;
          var tD = m ? bjFromStop(m, 'down') : null;
          var pills = '';
          if (tU != null) pills += '<span class="time-pill">' + icon('clock') + ' ⇗ ' + fmtTime(tU) + '</span> ';
          if (tD != null) pills += '<span class="time-pill">' + icon('clock') + ' ⇙ ' + fmtTime(tD) + '</span>';
          if (!pills && b.departure_time) pills = '<span class="time-pill">' + icon('clock') + ' ' + esc(b.departure_time) + '</span>';
          return '<div class="result-item" style="--i:' + i + '" onclick="location.hash=' + String.fromCharCode(39) + '#/bus/' + encodeURIComponent(b.id) + String.fromCharCode(39) + '">' +
            '<div class="ri-main"><div class="name">' + esc(b.bus_name) + '</div>' +
            '<div class="route">' + esc(pn(b.origin)) + ' <span class="rarr">→</span> ' + esc(pn(b.destination)) + '</div>' +
            '<div class="meta"><span>' + icon('stops') + ' ' + ((b.stoppages || []).length || b.total_stoppages || 0) + ' stops</span></div></div>' + pills + '</div>';
        }).join('') +
        '</div>';
      startNextBusTicker();
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
