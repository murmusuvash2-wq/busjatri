/* ============================================================
   BusJatri — Alternative Route finder (v1, 2026-09-22)
   ------------------------------------------------------------
   1-change journey suggestions for route searches
   (#/search?from=X&to=Y). Wraps renderSearch; must load AFTER
   stop-search-all.js.

   Trigger A - no direct bus found: alternatives appear below the
   empty state (no more dead end).
   Trigger B - next direct departure is > 3 hours away: amber note
   + alternatives below the results list.

   Everything is computed client-side from the compact index that
   search already loads (BUSES). No new data file, no server, no
   new pages. Untimed legs are skipped - times are never invented.
   ============================================================ */
(function () {
  'use strict';
  if (window.__bjAltRouteV1) return;
  window.__bjAltRouteV1 = true;
  if (typeof renderSearch !== 'function' || typeof BUSES === 'undefined') return;
  var prevRender = renderSearch;

  renderSearch = async function (el) {
    await prevRender(el);
    try { mount(el); } catch (e) { /* never break search */ }
  };

  /* ---- helpers (same semantics as stop-search-all.js closures) ---- */
  function posIn(b, q) {
    if (placeMatches(b.origin, q)) return 0;
    var sts = b.stoppages || [];
    for (var i = 0; i < sts.length; i++) if (placeMatches(sts[i].name, q)) return i + 1;
    if (placeMatches(b.destination, q)) return sts.length + 2;
    return -1;
  }
  function fromStop(s, dir) {
    if (!s) return null;
    if (dir === 'up') { if (s.um != null) return s.um || null; return parseTime(s.up_time); }
    if (s.dm != null) return s.dm || null;
    return parseTime(s.down_time);
  }
  function stopAt(b, pos, dir) {
    var sts = b.stoppages || [];
    if (pos === 0) return dir === 'up' ? parseTime(b.departure_time) : fromStop(sts.length ? sts[sts.length - 1] : null, 'down');
    if (pos >= 1 && pos <= sts.length) return fromStop(sts[pos - 1], dir);
    if (pos === sts.length + 2) return dir === 'up' ? parseTime(b.arrival_time) : fromStop(sts.length ? sts[sts.length - 1] : null, 'down');
    return null;
  }
  function posName(b, pos) {
    var sts = b.stoppages || [];
    if (pos === 0) return b.origin;
    if (pos >= 1 && pos <= sts.length) return sts[pos - 1].name;
    if (pos === sts.length + 2) return b.destination;
    return null;
  }
  function bnNum(n) { return String(n).replace(/[0-9]/g, function (d) { return '০১২৩৪৫৬৭৮৯'[+d]; }); }
  function durTxt(min) {
    var h = Math.floor(min / 60), m = Math.round(min % 60);
    return (h ? h + 'h ' : '') + m + 'm';
  }
  function durTxtBn(min) {
    var h = Math.floor(min / 60), m = Math.round(min % 60);
    return (h ? bnNum(h) + ' ঘণ্টা ' : '') + (m ? bnNum(m) + ' মিনিট' : (h ? '' : '—'));
  }

  /* ---- core: find 1-change options from -> to ---- */
  function findAlt(from, to, now) {
    var buses = Object.values(BUSES);
    var i, b, p;

    /* deliverers: buses that can reach `to` (boarded somewhere before) */
    var deliverers = [];
    for (i = 0; i < buses.length; i++) {
      b = buses[i];
      if (!b.stoppages && b.sx && window.DATA && DATA.sn) {
        b.stoppages = b.sx.map(function (x, k) { return { name: DATA.sn[x] || '', um: (b.ux && b.ux[k]) || 0, dm: (b.dx && b.dx[k]) || 0 }; });
      }
      if (b.stoppages && b.stoppages.length) {
        var t = posIn(b, to);
        if (t >= 1 && posIn(b, from) < 0) deliverers.push({ b: b, tPos: t });
      }
    }

    /* hub index: hub slug -> deliverer board points */
    var hubIndex = {};
    for (i = 0; i < deliverers.length; i++) {
      var d = deliverers[i];
      var maxPos = (d.b.stoppages || []).length + 2;
      for (p = 0; p <= maxPos; p++) {
        if (p === (d.b.stoppages || []).length + 1) continue; /* unreachable pos */
        if (p === d.tPos) continue;
        var nm = posName(d.b, p);
        if (!nm) continue;
        var key = slug(nm);
        if (!hubIndex[key]) hubIndex[key] = [];
        hubIndex[key].push({ b: d.b, tPos: d.tPos, hPos: p });
      }
    }

    var options = [];
    var best = {}; /* key -> option, keep earliest arrival */
    for (i = 0; i < buses.length; i++) {
      var b1 = buses[i];
      var fPos = posIn(b1, from);
      if (fPos < 0 || posIn(b1, to) >= 0) continue;
      if (!b1.stoppages) continue;
      var lastHubPos = b1.stoppages.length + 2;
      for (var hp = fPos + 1; hp <= lastHubPos; hp++) {
        var hub = posName(b1, hp);
        if (!hub) continue;
        if (placeMatches(hub, from) || placeMatches(hub, to)) continue;
        var arrHub1 = stopAt(b1, hp, 'up');
        var depFrom1 = stopAt(b1, fPos, 'up');
        if (depFrom1 == null || arrHub1 == null) continue;
        var arr1 = arrHub1; if (arr1 < depFrom1) arr1 += 1440;
        var cands = hubIndex[slug(hub)];
        if (!cands) continue;
        for (var c = 0; c < cands.length; c++) {
          var e = cands[c], b2 = e.b;
          if (b2 === b1 || b2.id === b1.id) continue;
          var brd2, arr2;
          if (e.hPos < e.tPos) { brd2 = stopAt(b2, e.hPos, 'up'); arr2 = stopAt(b2, e.tPos, 'up'); }
          else { brd2 = stopAt(b2, e.hPos, 'down'); arr2 = stopAt(b2, e.tPos, 'down'); }
          if (brd2 == null || arr2 == null) continue;
          var b2n = brd2; while (b2n < arr1 + 5) b2n += 1440;
          var wait = b2n - arr1;
          if (wait < 5 || wait > 240) continue;
          var a2n = arr2; while (a2n <= b2n) a2n += 1440;
          var start = depFrom1; if (start < now - 15) { start += 1440; arr1 += 1440; b2n += 1440; a2n += 1440; }
          if (a2n - start > 36 * 60) continue;
          var okey = slug(hub) + '|' + b1.id + '|' + b2.id;
          var opt = { b1: b1, b2: b2, hub: hub, depFrom: start, arrHub: arr1, boardHub: b2n, arriveTo: a2n, wait: wait, arrivalRel: a2n - now };
          if (!best[okey] || opt.arrivalRel < best[okey].arrivalRel) best[okey] = opt;
        }
      }
    }

    /* best option per hub, then top 3 hubs by earliest arrival */
    var perHub = {};
    Object.keys(best).forEach(function (k) {
      var o = best[k], hk = slug(o.hub);
      if (!perHub[hk] || o.arrivalRel < perHub[hk].arrivalRel) perHub[hk] = o;
    });
    Object.keys(perHub).forEach(function (k) { options.push(perHub[k]); });
    options.sort(function (x, y) { return x.arrivalRel - y.arrivalRel; });
    return options.slice(0, 3);
  }

  /* ---- rendering ---- */
  function optCard(o, n) {
    var b1 = o.b1, b2 = o.b2;
    function leg(b, fromLbl, toLbl, depMin, pillNote) {
      return '<div class="result-item" style="--i:0;margin:0" onclick="location.hash=\'#/bus/' + encodeURIComponent(b.id) + '\'">' +
        '<div class="ri-main">' +
        '<div class="name">' + esc(b.bus_name) + (b.reg_no ? ' <span class="reg">' + esc(b.reg_no) + '</span>' : '') + ' ' + busTypeBadge(b.bus_type) + '</div>' +
        '<div class="route">' + esc(pn(fromLbl)) + ' <span class="rarr">→</span> ' + esc(pn(toLbl)) + '</div>' +
        '<div style="font-size:12px;color:var(--amber);font-weight:600;margin-top:2px"><span class="label-en">' + pillNote.en + '</span><span class="label-bn">' + pillNote.bn + '</span></div>' +
        '</div>' +
        '<span class="time-pill">' + icon('clock') + ' ' + fmtTime(depMin) + '</span></div>';
    }
    return '<div style="margin:0 0 14px;border:1.5px solid var(--line,rgba(33,28,22,.13));border-radius:14px;padding:12px;background:var(--surface,#fffcf4)">' +
      '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;font-size:12px;color:var(--ink-dim,#665)">' +
      '<span style="background:rgba(46,125,50,.09);color:#2e7d32;border-radius:99px;padding:2px 10px;font-weight:700;white-space:nowrap"><span class="label-en">Route ' + n + ' · via </span><span class="label-bn">রুট ' + bnNum(n) + ' · </span>' + esc(pn(o.hub)) + '</span>' +
      '<span class="label-en">1 change</span><span class="label-bn">১ বার বাস বদল</span></div>' +
      leg(b1, o.fromLbl, o.hub, o.depFrom, { en: 'arrives ' + esc(pn(o.hub)) + ' ' + fmtTime(o.arrHub % 1440), bn: esc(pn(o.hub)) + ' পৌঁছায় ' + bnTime(o.arrHub) }) +
      '<div style="display:flex;align-items:center;gap:10px;margin:8px 0;padding:8px 12px;border-radius:10px;background:rgba(46,125,50,.08)">' +
      '<span style="color:#2e7d32;font-weight:800;line-height:1">⇅</span>' +
      '<span style="flex:1;min-width:0;font-size:12.5px;color:#2e7d32;font-weight:600"><span class="label-en">Change at </span><span class="label-bn">বাস বদলান: </span>' + esc(pn(o.hub)) + '</span>' +
      '<span style="font-size:11px;color:#2e7d32;border:1px solid rgba(46,125,50,.35);border-radius:99px;padding:1px 8px;white-space:nowrap">' + bnNum(o.wait) + ' <span class="label-en">min wait</span><span class="label-bn">মিনিট অপেক্ষা</span></span></div>' +
      leg(b2, o.hub, o.toLbl, o.boardHub % 1440, { en: 'arrives ' + esc(pn(o.toLbl)) + ' ' + fmtTime(o.arriveTo % 1440), bn: esc(pn(o.toLbl)) + ' পৌঁছায় ' + bnTime(o.arriveTo) }) +
      '<div style="font-size:11.5px;color:var(--ink-dim,#665);margin-top:8px;text-align:right"><span class="label-en">Total: </span><span class="label-bn">মোট যাত্রা: </span><b>' + fmtTime(o.depFrom % 1440) + ' → ' + fmtTime(o.arriveTo % 1440) + ' · ' + durTxtBn(o.arriveTo - o.depFrom) + ' (' + durTxt(o.arriveTo - o.depFrom) + ')</b></div>' +
      '</div>';
  }
  function bnTime(min) {
    var t = fmtTime(min % 1440);
    return t.replace(/[0-9]/g, function (d) { return '০১২৩৪৫৬৭৮৯'[+d]; });
  }

  function sectionHtml(opts, mode, gapHrs, fromLbl, toLbl) {
    var head, note;
    if (mode === 'A') {
      head = '<span class="label-en">Alternative route · 1 change</span><span class="label-bn">বিকল্প পথ · ১ বার বাস বদল</span>';
      note = '<span class="label-en">No direct bus on this route — but you can get there with one bus change:</span><span class="label-bn">এই পথে সরাসরি কোনো বাস নেই — কিন্তু এক বার বাস বদলে যাওয়া যায়:</span>';
    } else {
      head = '<span class="label-en">Alternative route · 1 change</span><span class="label-bn">বিকল্প পথ · ১ বার বাস বদল</span>';
      note = '<span class="label-en">The next direct bus is about <b>' + gapHrs + 'h away</b> — these routes may get you there sooner:</span><span class="label-bn">পরের সরাসরি বাস প্রায় <b>' + bnNum(gapHrs) + ' ঘণ্টা পরে</b> — এই পথগুলোতে আগে পৌঁছানো যেতে পারে:</span>';
    }
    return '<div id="bj-alt-route" style="margin:26px 0 4px;border-top:1.5px dashed var(--line,rgba(33,28,22,.13));padding-top:18px">' +
      '<h3 style="font-size:15px;font-weight:800;margin:0 0 4px;color:var(--ink)">' + head + '</h3>' +
      '<p style="font-size:12.5px;color:var(--ink-dim,#665);margin:0 0 14px;line-height:1.5">' + note + '</p>' +
      opts.map(function (o, i) { o.fromLbl = fromLbl; o.toLbl = toLbl; return optCard(o, i + 1); }).join('') +
      '</div>';
  }

  /* ---- mount: decide trigger + inject ---- */
  function mount(el) {
    var params = new URLSearchParams(location.hash.split('?')[1] || '');
    var from = (params.get('from') || '').toLowerCase().trim();
    var to = (params.get('to') || '').toLowerCase().trim();
    if (!from || !to) return;
    if ((params.get('stop') || '').trim()) return;
    var container = el.querySelector && el.querySelector('.container');
    if (!container) return;

    var now = minutesNow();
    var direct = [], minRel = Infinity;
    var buses = Object.values(BUSES);
    for (var i = 0; i < buses.length; i++) {
      var b = buses[i];
      if (!b.stoppages && b.sx && window.DATA && DATA.sn) {
        b.stoppages = b.sx.map(function (x, k) { return { name: DATA.sn[x] || '', um: (b.ux && b.ux[k]) || 0, dm: (b.dx && b.dx[k]) || 0 }; });
      }
      if (!b.stoppages) continue;
      var fi = posIn(b, from), ti = posIn(b, to);
      if (fi < 0 || ti < 0 || fi === ti) continue;
      direct.push(b);
      var dm = fi < ti ? stopAt(b, fi, 'up') : stopAt(b, fi, 'down');
      if (dm != null) { if (dm < now) dm += 1440; if (dm - now < minRel) minRel = dm - now; }
    }

    var mode = null;
    if (!direct.length) mode = 'A';
    else if (minRel !== Infinity && minRel > 180) mode = 'B';
    if (!mode) return;

    var opts = findAlt(from, to, now);
    if (!opts.length) return;

    var fromLbl = from.charAt(0).toUpperCase() + from.slice(1);
    var toLbl = to.charAt(0).toUpperCase() + to.slice(1);
    var gapHrs = Math.round(minRel / 60);
    var html = sectionHtml(opts, mode, gapHrs, fromLbl, toLbl);

    var footer = container.querySelector('p[style*="border-top"]') || container.lastElementChild;
    if (footer && footer !== container.firstElementChild) footer.insertAdjacentHTML('beforebegin', html);
    else container.insertAdjacentHTML('beforeend', html);
  }
})();
