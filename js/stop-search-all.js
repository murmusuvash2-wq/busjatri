/* ============================================================
   BusJatri search overlay (2026-09-18) - loaded LAST, after ux-fixes.js
   Search v3 + Autocomplete v2.
   1. Stop searches list ALL buses serving the stop - untimed services
      render after the timed ones with a "Time not listed" pill
      (ux-fixes v2 showed only timed rows: Mallarpur said "10 buses"
      but rendered 2).
   2. Header reads "N buses - M with timings"; times already past
      today get an explicit "tomorrow" tag.
   3. Autocomplete v2: ranked prefix -> substring -> fuzzy/alias
      (placeMatches), sourced from STOPS + sn + origins/destinations,
      so typos like "mollarpur" and aliases like "kanthi" suggest
      results instead of an empty box (374 names were never suggested).
   4. canonName resolves titles through the same fuzzy tiers, so the
      page title shows "Mallarpur" even when the query was misspelled.
   Helpers below are copies of closure-local functions from ux-fixes.js.
   ============================================================ */
(function () {
  'use strict';
  if (typeof renderSearch !== 'function' || window.__bjSearchV3) return;
  window.__bjSearchV3 = true;

  function rebuildCompactStops() {
    if (typeof DATA === 'undefined' || !DATA || !DATA.buses || !DATA.sn) return;
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
    if (!best) {
      /* fuzzy tiers: prefix, then placeMatches (typos + aliases), so a
         misspelled query still gets the real place name in the title */
      var t = String(q || '').toLowerCase();
      acNames().forEach(function (n) {
        if (!best) {
          if (n.toLowerCase().indexOf(t) === 0) best = n;
          else if (t.length >= 4 && placeMatches(n, t)) best = n;
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

    /* ---- 4. Autocomplete v2: fuzzy + alias aware, full name coverage ----
     ux-fixes.js autocomplete does prefix/substring only and reads just the
     STOPS dict (2,740 names; 374 real names are never suggested, and any
     typo or alias input gets an empty box). This replacement ranks:
       tier 1 - prefix matches
       tier 2 - substring matches
       tier 3 - placeMatches (compact + consonant-skeleton typo tolerance
                + alias groups), only when the query has 4+ letters
     and sources names from STOPS + DATA.sn + all origins/destinations.
     Registered after ux-fixes.js, so its dropdown wins (last write). */
  var AC_LIMIT = 10;
  var AC_NAMES = null;
  function acNames() {
    if (AC_NAMES) return AC_NAMES;
    var seen = Object.create(null);
    var out = [];
    function add(n) { if (n && !seen[n]) { seen[n] = 1; out.push(n); } }
    Object.values(STOPS || {}).forEach(function (s) { if (s && s.name) add(s.name); });
    if (typeof DATA !== 'undefined' && DATA && DATA.sn) DATA.sn.forEach(add);
    Object.values(BUSES).forEach(function (b) { add(b.origin); add(b.destination); });
    AC_NAMES = out;
    return out;
  }
  function acFind(q) {
    var t = (q || '').toLowerCase().trim();
    if (!t) return [];
    var t1 = [], t2 = [], t3 = [];
    var names = acNames();
    for (var i = 0; i < names.length; i++) {
      var n = names[i], ln = n.toLowerCase();
      if (ln.indexOf(t) === 0) t1.push(n);
      else if (ln.indexOf(t) !== -1) t2.push(n);
      else if (t.length >= 4 && placeMatches(n, t)) t3.push(n);
    }
    var rank = function (a, b) {
      var la = a.toLowerCase(), lb = b.toLowerCase();
      if (la === t && lb !== t) return -1;
      if (lb === t && la !== t) return 1;
      if (a.length !== b.length) return a.length - b.length;
      return la < lb ? -1 : (la > lb ? 1 : 0);
    };
    var res = t1.sort(rank).concat(t2.sort(rank));
    if (res.length < AC_LIMIT) res = res.concat(t3);
    return res.slice(0, AC_LIMIT);
  }
  function acHtml(s) {
    var A = String.fromCharCode(38);
    var M = {};
    M[A] = A + 'amp;';
    M[String.fromCharCode(60)] = A + 'lt;';
    M[String.fromCharCode(62)] = A + 'gt;';
    M['"'] = A + 'quot;';
    M["'"] = A + '#39;';
    return String(s).replace(/[&<>"']/g, function (c) { return M[c]; });
  }
  function acHide() {
    document.querySelectorAll('.ac-drop').forEach(function (d) { d.remove(); });
  }
  function acShow(input) {
    acHide();
    var m = acFind(input.value);
    if (!m.length) return;
    var field = input.closest('.search-field');
    if (!field) return;
    var d = document.createElement('div');
    d.className = 'ac-drop';
    d.innerHTML = m.map(function (n) {
      return '<div class="ac-item">' + acHtml(n) + '</div>';
    }).join('');
    field.appendChild(d);
  }
  function acIsInput(el) {
    return !!(el && (el.id === 'fromInput' || el.id === 'toInput' || el.id === 'stopInput'));
  }
  var acTimer = null;
  document.addEventListener('input', function (e) {
    if (!acIsInput(e.target)) return;
    if (acTimer) clearTimeout(acTimer);
    acTimer = setTimeout(function () { acShow(e.target); }, 160);
  });
  document.addEventListener('click', function (e) {
    var item = e.target.closest ? e.target.closest('.ac-item') : null;
    if (item) {
      var field = item.closest('.search-field');
      var input = field && field.querySelector('input');
      if (input) {
        input.value = item.textContent;
        acHide();
        input.focus();
      }
      return;
    }
    if (acIsInput(e.target)) { acShow(e.target); return; }
    acHide();
  });

  renderSearch = async function (el) {
      rebuildCompactStops();
      function looksLikeTime(q) {
        q = String(q || '').trim().toLowerCase();
        return /^\d{1,2}:\d{2}\s*(am|pm)?$/.test(q) || /^\d{1,2}\s*(am|pm)$/.test(q);
      }
      function parseClock(q) {
        q = String(q || '').trim().toLowerCase().replace(/\s+/g, '');
        var m = /^(\d{1,2})(?::(\d{2}))?(am|pm)?$/.exec(q);
        if (!m) return null;
        var h = +m[1], mi = m[2] ? +m[2] : 0, ap = m[3];
        if (mi > 59) return null;
        if (ap) { if (h < 1 || h > 12) return null; h %= 12; if (ap === 'pm') h += 12; }
        else if (h > 23) return null;
        return h * 60 + mi;
      }
      window.__bjTimeQuery = null;
      var params = new URLSearchParams(location.hash.split('?')[1] || '');
      var from = (params.get('from') || '').toLowerCase().trim();
      var to = (params.get('to') || '').toLowerCase().trim();
      var stop = (params.get('stop') || '').toLowerCase().trim();
      var routeMode = !!(from && to);

      var all = (FULL_BUSES && Object.keys(FULL_BUSES).length >= Object.keys(BUSES).length) ? Object.values(FULL_BUSES) : Object.values(BUSES);
      var rows = [];

      if (routeMode) {
        /* compact index has full stop coverage — no 5MB download, instant results */
        all = Object.values(BUSES);
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
            if (!mS && placeMatches(s.name, stop)) mS = s;
          });
          var isO = placeMatches(b.origin, stop);
          var isD = placeMatches(b.destination, stop);
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
          if (tU == null && tD == null) rows.push({ b: b, fwd: true, depMin: null, untimed: true });
        });
        window.__bjStopCount = nBuses;
        window.__bjDepCount = rows.filter(function (r) { return r.depMin != null; }).length;
      } else if ((from || to) && looksLikeTime(from || to) && parseClock(from || to) != null) {
        var q = from || to;
        var target = parseClock(q);
        function bjDist(t) { var d = Math.abs(t - target) % 1440; return Math.min(d, 1440 - d); }
        rows = all.filter(function (b) { return parseTime(b.departure_time) != null && bjDist(parseTime(b.departure_time)) <= 90; });
        rows.sort(function (x, y) { return bjDist(parseTime(x.b.departure_time)) - bjDist(parseTime(y.b.departure_time)); });
        window.__bjTimeQuery = q;
      } else {
        var q = from || to;
        rows = all.filter(function (b) {
          return placeMatches(b.origin, q) || placeMatches(b.destination, q) ||
                 (b.bus_name || '').toLowerCase().includes(q) ||
                 (b.route || '').toLowerCase().includes(q) ||
                 (b.stoppages || []).some(function (s) { return placeMatches(s.name, q); });
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
      var timeHtml = window.__bjTimeQuery ? '<p style="text-align:center;font-size:12.5px;color:var(--amber);font-weight:600;margin:2px 0 10px">Buses departing around ' + esc(window.__bjTimeQuery) + ' (±90 min)</p>' : '';
      el.innerHTML =
        '<div class="container" style="padding-top:22px;padding-bottom:40px">' +
        '<div class="back-btn" onclick="location.hash=' + String.fromCharCode(39) + '#/' + String.fromCharCode(39) + '">' + icon('chevronLeft') + ' <span class="label-en">Back</span><span class="label-bn">পিছনে</span></div>' +
        '<h2 class="page-title" style="text-align:center;margin-bottom:2px">' + esc(titleTxt) + ' <span style="color:var(--ink-dim);font-family:var(--font-mono);font-size:1rem">(' + rows.length + ')</span></h2>' +
        viaHtml + timeHtml +
        (stop && !from && !to && window.__bjStopCount ? '<p style="text-align:center;font-size:12px;color:var(--ink-dim);margin:2px 0 0">' + window.__bjStopCount + ' <span class="label-en">buses · </span><span class="label-bn">বাস · </span>' + window.__bjDepCount + ' <span class="label-en">with timings</span><span class="label-bn">সময় সহ</span></p>' : '') +
        (stop && !from && !to && window.__bjStopCount ? '<p style="text-align:center;font-size:11px;color:var(--ink-dim);margin:2px 0 10px"><span class="label-en">timed departures first · rest listed below</span><span class="label-bn">সময় সহ বাস আগে · বাকি নিচে</span></p>' : '') +
        (near.length ? '<p class="near-label">' + icon('clock') + ' <span class="label-en">' + near.length + ' buses around current time</span><span class="label-bn">' + near.length + ' বাস বর্তমান সময়ের কাছাকাছি</span></p>' : '') +
        (routeMode || (stop && !from && !to) ? '<p style="font-size:11.5px;color:var(--ink-dim);margin:0 0 10px"><b style="color:var(--amber)">⇗</b> <span class="label-en">outward · </span><span class="label-bn">যাত্রা · </span><b style="color:var(--maroon)">⇙</b> <span class="label-en">return service</span><span class="label-bn">ফেরার বাস</span></p>' : '') +
        (rows.length ? rows.map(function (r, i) {
          var b = r.b;
          var isNear = r.depMin != null && rel(r.depMin) <= 180;
          var isRet = (routeMode || (stop && !from && !to)) && !r.fwd;
          var revBadge = isRet ? '<span style="font-size:10px;font-weight:700;color:var(--maroon);border:1px solid var(--maroon);border-radius:6px;padding:2px 7px;margin-left:6px;white-space:nowrap"><span class="label-en">RETURN</span><span class="label-bn">ফেরার বাস</span></span>' : '';
          var ro = isRet ? b.destination : b.origin;
          var rd = isRet ? b.origin : b.destination;
          var tPill = r.depMin != null ? '<span class="time-pill">' + icon('clock') + ' ' + fmtTime(r.depMin) + (r.depMin < now ? ' · <span class="label-en">tomorrow</span><span class="label-bn">আগামীকাল</span>' : '') + (isNear ? ' · <b style="color:var(--amber)">' + countdownText(rel(r.depMin)) + '</b>' : '') + '</span>' : '<span class="time-pill" style="opacity:.55"><span class="label-en">Time not listed</span><span class="label-bn">সময় জানা নেই</span></span>';
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
})();
