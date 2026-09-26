/* BusJatri operator pages: search card + depo departure board (2026-09-25).
   Page config and bus data are injected inline by scripts/gen_operator_pages.py
   (window.bjOpCfg / window.bjOpData); this script renders both widgets.
   Honest wording: 'Depo Departure Time' - daily schedule data, not live tracking. */
(function () {
  'use strict';
  var Q = String.fromCharCode(39);
  function esc(s) {
    return String(s == null ? '' : s)
      .split('&').join('&' + 'amp;')
      .split('<').join('&' + 'lt;')
      .split('>').join('&' + 'gt;')
      .split(String.fromCharCode(34)).join('&' + 'quot;');
  }
  function parseTime(s) {
    s = String(s || '').trim().toLowerCase();
    var ap = '';
    if (s.length > 2) {
      var l2 = s.slice(-2);
      if (l2 === 'am' || l2 === 'pm') { ap = l2; s = s.slice(0, -2).trim(); }
    }
    var parts = s.split(':');
    if (parts.length !== 2) return null;
    var h = parseInt(parts[0], 10);
    var mi = parseInt(parts[1], 10);
    if (isNaN(h) || isNaN(mi) || mi > 59 || mi < 0) return null;
    if (ap) {
      if (h < 1 || h > 12) return null;
      h %= 12;
      if (ap === 'pm') h += 12;
    } else if (h > 23) return null;
    return h * 60 + mi;
  }
  function minutesNow() { var d = new Date(); return d.getHours() * 60 + d.getMinutes(); }
  function fmtTime(t) {
    var h = Math.floor(t / 60) % 24, m = t % 60, ap = h >= 12 ? 'PM' : 'AM';
    h = h % 12 || 12;
    return h + ':' + String(m).padStart(2, '0') + ' ' + ap;
  }

  /* ---- search card ---- */
  var fromI = document.getElementById('bjFrom');
  var toI = document.getElementById('bjTo');
  var dateI = document.getElementById('bjDate');
  if (dateI) {
    var d0 = new Date();
    dateI.value = d0.getFullYear() + '-' + String(d0.getMonth() + 1).padStart(2, '0') + '-' + String(d0.getDate()).padStart(2, '0');
  }
  window.bjSwap = function () { if (!fromI || !toI) return; var v = fromI.value; fromI.value = toI.value; toI.value = v; };
  window.bjSearchGo = function () {
    var f = fromI ? fromI.value.trim() : '';
    var t = toI ? toI.value.trim() : '';
    if (!f && !t) { alert(document.body.classList.contains('lang-bn') ? '\u09b6\u09c1\u09b0\u09c1 \u09ac\u09be \u0997\u09a8\u09cd\u09a4\u09ac\u09cd\u09af \u09aa\u09c2\u09b0\u09a3 \u0995\u09b0\u09c1\u09a8' : 'Fill From or To'); return; }
    location.href = '../index.html#/search?from=' + encodeURIComponent(f) + '&to=' + encodeURIComponent(t);
  };

  /* ---- depo departure board ---- */
  var cfg = window.bjOpCfg || {};
  var OP_DATA = window.bjOpData || [];
  var lvEl = document.getElementById('bjLive');
  if (!lvEl) return;
  var OP_NAME = cfg.name || '';
  var OP_NAME_BN = cfg.bn || OP_NAME;
  var OP_TOKEN = cfg.token || '';
  var OP_COUNT = cfg.count || OP_DATA.length;
  var lvOps = {};
  OP_DATA.forEach(function (b) { if (b[2]) lvOps[b[2]] = (lvOps[b[2]] || 0) + 1; });
  var origins = Object.keys(lvOps).map(function (n) { return { name: n, n: lvOps[n] }; })
    .sort(function (a, b) { return b.n - a.n; }).slice(0, 6);
  var lvOrigin = '';
  for (var oi = 0; oi < origins.length; oi++) if (origins[oi].name === 'Kolkata') lvOrigin = origins[oi].name;
  if (!lvOrigin && origins.length) lvOrigin = origins[0].name;
  var lvQ = '';
  /* v2 (SBSTC page): bn stop names + time-of-day / tomorrow filters */
  var STOPS = window.bjStops || null;
  var STKEYS = STOPS ? Object.keys(STOPS).sort(function (a, b) { return b.length - a.length; }) : [];
  var RSTOPS = {};
  if (STOPS) for (var sk in STOPS) { RSTOPS[STOPS[sk]] = sk; }
  var TOD = 'any', DAY = '';
  function bnName(s) {
    if (!STOPS || !document.body.classList.contains('lang-bn')) return String(s == null ? '' : s);
    var r = String(s);
    for (var si = 0; si < STKEYS.length; si++) {
      if (r.indexOf(STKEYS[si]) > -1) r = r.split(STKEYS[si]).join(STOPS[STKEYS[si]]);
    }
    return r;
  }
  function bjTodayStr() {
    function p(n) { return (n < 10 ? '0' : '') + n; }
    var d = new Date();
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  }
  function dateIsToday() { return !DAY || DAY === bjTodayStr(); }
  function todOK(t) {
    if (TOD === 'any') return true;
    return Math.floor(t / 60) === TOD;
  }
  window.bjLvSet = function (n) { lvOrigin = n; lvQ = ''; var inp = document.getElementById('bjLvSearch'); if (inp) inp.value = ''; renderRows(); };
  window.bjLvSearchDo = function (v) { lvQ = String(v || '').trim().toLowerCase(); renderRows(); };
  lvEl.innerHTML = '<div class="lv-clock-wrap"><div>' +
    '<div class="lv-clock-label"><span class="ldot"></span> <span class="label-en">' + esc(OP_NAME) + ' Depo Departure Time</span><span class="label-bn">' + esc(OP_NAME_BN) + ' ডিপোর ছাড়ার সময়</span></div>' +
    '<div class="lv-clock-big" id="bjLvClock"></div></div>' +
    '<div class="lv-geo"><span class="label-en">daily schedule</span><span class="label-bn">দৈনিক সময়সূচি</span></div></div>' +
    '<div class="lv-board">' +
    '<input id="bjLvSearch" type="text" oninput="bjLvSearchDo(this.value)" style="width:100%;box-sizing:border-box;background:var(--surface-2,#f4eee0);border:1px solid var(--line,#d8cdb8);border-radius:999px;padding:9px 16px;font:inherit;font-size:13px;margin-bottom:11px;outline:none">' +
    '<div class="lv-tabs" id="bjLvTabs"></div>' +
    '<div id="lvRows"></div>' +
    '<div style="border-top:1px dashed var(--line-strong,rgba(33,28,22,.2));margin-top:10px;padding-top:11px;text-align:center">' +
    '<a href="../index.html#/search?op=' + encodeURIComponent(OP_TOKEN) + '" style="color:var(--amber,#b8791f);font-weight:800;text-decoration:none;font-size:13.5px">' +
    '<span class="label-en">View all ' + OP_COUNT + ' ' + esc(OP_NAME) + ' buses</span><span class="label-bn">সব ' + OP_COUNT + ' ' + esc(OP_NAME_BN) + ' বাস দেখুন</span> ↗</a></div></div>';
  function lvTag(t, now) {
    if (t < now) return '';
    var r = t - now;
    if (r <= 1) return '<span class="ltag">now</span>';
    if (r <= 180) return '<span class="ltag">' + (r < 60 ? r + 'm' : Math.floor(r / 60) + 'h ' + (r % 60) + 'm') + '</span>';
    return '';
  }
  function originOf(b) {
    if (!lvQ) return b[2] === lvOrigin;
    return String(b[2] || '').toLowerCase().indexOf(lvQ) > -1 || String(b[3] || '').toLowerCase().indexOf(lvQ) > -1;
  }
  function renderRows() {
    var now = minutesNow();
    var tabs = document.getElementById('bjLvTabs');
    if (tabs) tabs.innerHTML = origins.map(function (o) {
      return '<button class="lv-tab' + (o.name === lvOrigin && !lvQ ? ' on' : '') + '" onclick="bjLvSet(' + Q + o.name.split(Q).join('') + Q + ')">' + esc(o.name) + '</button>';
    }).join('');
    var inp = document.getElementById('bjLvSearch');
    if (inp) inp.placeholder = document.body.classList.contains('lang-bn') ? 'স্টপ বা গন্তব্য লিখুন' : 'Search origin / stop';
    var rows = OP_DATA.filter(function (b) { return originOf(b) && parseTime(b[4]) != null && todOK(parseTime(b[4])); })
      .map(function (b) { return { b: b, t: parseTime(b[4]) }; })
      .sort(!dateIsToday()
      ? function (x, y) { return x.t - y.t; }
      : function (x, y) { return ((x.t < now - 30 ? x.t + 1440 : x.t) - now) - ((y.t < now - 30 ? y.t + 1440 : y.t) - now); })
      .slice(0, 9);
    var el2 = document.getElementById('lvRows');
    if (el2) el2.innerHTML = rows.length ? rows.map(function (r) {
      return '<div class="lv-row" onclick="location.href=' + Q + '../index.html#/bus/' + encodeURIComponent(r.b[0]) + Q + '">' +
        '<span class="lt">' + fmtTime(r.t).replace(' ', '') + '</span>' +
        '<span class="lnm">' + esc(bnName(r.b[1])) + '</span>' +
        '<span class="ldst">' + String.fromCharCode(8594) + ' ' + esc(bnName(r.b[3])) + '</span>' +
        lvTag(r.t, now) + '</div>';
    }).join('') : '<div class="lv-row"><span class="lnm"><span class=\"label-en\">No departures found</span><span class=\"label-bn\">\u0995\u09cb\u09a8\u09cb \u099b\u09be\u09dc\u09be\u09b0 \u09b8\u09ae\u09df \u09a8\u09c7\u0987</span></span></div>';
  }
  function tick() {
    var d = new Date();
    var c = document.getElementById('bjLvClock');
    if (c) c.innerHTML = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0') + ':' + String(d.getSeconds()).padStart(2, '0') + '<small>IST</small>';
  }
  /* ---- v2 (SBSTC only, gated on window.bjStops) ---- */
  if (STOPS) {
    function updPh() {
      var isBn = document.body.classList.contains('lang-bn');
      var hs0 = document.getElementById('bjHour');
      if (hs0 && hs0.options.length) hs0.options[0].text = isBn ? '\u09af\u09c7\u0995\u09cb\u09a8\u09cb \u09b8\u09ae\u09df' : 'Any time';
      if (fromI) fromI.placeholder = isBn ? '\u09af\u09c7\u09ae\u09a8: ' + bnName('Burdwan') : 'e.g. Burdwan';
      if (toI) toI.placeholder = isBn ? '\u09af\u09c7\u09ae\u09a8: ' + bnName('Kolkata') : 'e.g. Kolkata';
    }
    updPh();
    if (window.MutationObserver) {
      new MutationObserver(function () {
        updPh();
        renderRows();
        var rs = document.getElementById('bjOpResults');
        if (rs && rs.getAttribute('data-q') === '1') window.bjSearchGo();
      }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
    }
    var bjDateI = document.getElementById('bjDate');
    var bjHourS = document.getElementById('bjHour');
    if (bjDateI && !bjDateI.value) bjDateI.value = bjTodayStr();
    function syncFilters() {
      DAY = bjDateI ? bjDateI.value : '';
      TOD = (bjHourS && bjHourS.value !== 'any') ? parseInt(bjHourS.value, 10) : 'any';
      renderRows();
      var rs = document.getElementById('bjOpResults');
      if (rs && rs.getAttribute('data-q') === '1') window.bjSearchGo();
    }
    if (bjDateI) bjDateI.addEventListener('change', syncFilters);
    if (bjHourS) bjHourS.addEventListener('change', syncFilters);
    window.bjSearchGo = function () {
      var f = fromI ? fromI.value.trim() : '';
      var t = toI ? toI.value.trim() : '';
      var isBn = document.body.classList.contains('lang-bn');
      if (!f && !t) { alert(isBn ? '\u09b6\u09c1\u09b0\u09c1 \u09ac\u09be \u0997\u09a8\u09cd\u09a4\u09ac\u09cd\u09af \u09aa\u09c2\u09b0\u09a3 \u0995\u09b0\u09c1\u09a8' : 'Fill From or To'); return; }
      var fl = (RSTOPS[f] || f).toLowerCase();
      var tl = (RSTOPS[t] || t).toLowerCase();
      var hits = OP_DATA.filter(function (b) {
        var o = String(b[2] || '').toLowerCase(), d = String(b[3] || '').toLowerCase();
        var of = !fl || o.indexOf(fl) > -1 || bnName(b[2]).indexOf(f) > -1;
        var dt = !tl || d.indexOf(tl) > -1 || bnName(b[3]).indexOf(t) > -1;
        return of && dt && parseTime(b[4]) != null && todOK(parseTime(b[4]));
      });
      hits.sort(function (x, y) {
        var a = parseTime(x[4]), c = parseTime(y[4]);
        return dateIsToday() ? ((a < minutesNow() - 30 ? a + 1440 : a) - minutesNow()) - ((c < minutesNow() - 30 ? c + 1440 : c) - minutesNow()) : a - c;
      });
      var el = document.getElementById('bjOpResults');
      if (!el) return;
      el.setAttribute('data-q', '1');
      var H = '<div class="op-res-card"><div class="op-res-h">';
      if (hits.length) {
        H += isBn ? '\u098f\u0987 \u09b0\u09c1\u099f\u09c7 ' + hits.length + '\u099f\u09bf SBSTC \u09ac\u09be\u09b8' : hits.length + ' SBSTC buses on this route';
        H += '</div>' + hits.slice(0, 24).map(function (r) {
          return '<div class="op-res-row" onclick="location.href=\'../index.html#/bus/' + encodeURIComponent(r[0]) + '\'">' +
            '<span class="t">' + fmtTime(parseTime(r[4])).replace(' ', '') + '</span>' +
            '<span class="nm">' + esc(bnName(r[1])) + '</span>' +
            '<span class="dst">' + String.fromCharCode(8594) + ' ' + esc(bnName(r[3])) + '</span></div>';
        }).join('');
        if (hits.length > 24) H += '<div class="op-res-alt" style="text-align:center;color:var(--ink-dim,#665)">' + (isBn ? '\u0986\u09b0\u0993 ' + (hits.length - 24) + '\u099f\u09bf \u09ac\u09be\u09b8 \u09b8\u09be\u09b0\u09cd\u099a\u09c7' : '+' + (hits.length - 24) + ' more in search') + '</div>';
      } else {
        var lk = '../index.html#/search?from=' + encodeURIComponent(f) + '&to=' + encodeURIComponent(t);
        H += (isBn ? '\u098f\u0987 \u09b0\u09c1\u099f\u09c7 SBSTC \u09ac\u09be\u09b8 \u09aa\u09be\u0993\u09df\u09be \u09af\u09be\u09df\u09a8\u09bf\u0964' : 'No SBSTC bus found for this route.') + '</div>' +
          '<div class="op-res-alt" id="bjOpAlt">' + (isBn ? '\u0985\u09a8\u09cd\u09af \u09ac\u09bf\u0995\u09b2\u09cd\u09aa \u0996\u09c1\u0981\u099b\u099b\u09bf...' : 'Looking for other options...') + '</div>';
        H += '<div class="op-res-alt"><a href="' + lk + '" style="color:var(--amber,#b8791f);font-weight:800;text-decoration:none">' + (isBn ? '\u09b8\u09be\u09b0\u09cd\u099a\u09c7 \u09a6\u09c7\u0996\u09c1\u09a8' : 'Open in search') + ' \u2197</a></div>';
        (function () {
          var fx = document.getElementById('bjOpAlt');
          fetch('../data/app-index.json').then(function (r) { return r.json(); }).then(function (dx) {
            var buses = (dx && dx.buses) || [], tot = 0, pvt = 0, ac = 0;
            buses.forEach(function (b2) {
              var o = (b2.origin || '').toLowerCase(), d = (b2.destination || '').toLowerCase();
              if (fl && o.indexOf(fl) === -1) return;
              if (tl && d.indexOf(tl) === -1) return;
              tot++;
              var bt = String(b2.bus_type || '');
              if (/private/i.test(bt)) pvt++;
              if (/AC/.test(bt) && !/NON/i.test(bt.toUpperCase())) ac++;
            });
            if (fx) fx.innerHTML = tot
              ? (isBn ? '\u0985\u09a8\u09cd\u09af \u09ac\u09bf\u0995\u09b2\u09cd\u09aa: \u098f\u0987 \u09b0\u09c1\u099f\u09c7 ' + tot + '\u099f\u09bf \u09ac\u09be\u09b8 \u0986\u099b\u09c7 \u2014 \u09ac\u09c7\u09b8\u09b0\u0995\u09be\u09b0\u09c0: ' + pvt + ', \u098f\u09b8\u09bf: ' + ac : 'Other options: ' + tot + ' buses on this route \u2014 private: ' + pvt + ', AC: ' + ac)
              : (isBn ? '\u098f\u0987 \u09b0\u09c1\u099f\u09c7 \u0995\u09cb\u09a8\u09cb \u09ac\u09be\u09b8\u09c7\u09b0 \u09a4\u09a5\u09cd\u09af \u09a8\u09c7\u0987\u0964' : 'No bus data found for this route yet.');
          }).catch(function () { if (fx) fx.innerHTML = ''; });
        })();
      }
      H += '</div>';
      if (window.BJ_SEAT_URL) {
        H += '<a class="op-cta-big" style="margin:14px 0 2px" href="' + window.BJ_SEAT_URL + '" target="_blank" rel="noopener">' + '\ud83c\udfab <span class="label-en">Check Seat on SBSTC official site</span><span class="label-bn">' + '\u098f\u09b8\u09ac\u09bf\u098f\u09b8\u099f\u09bf\u09b8\u09bf \u0985\u09ab\u09bf\u09b8\u09bf\u09af\u09bc\u09be\u09b2 \u09b8\u09be\u0987\u099f\u09c7 \u09b8\u09bf\u099f \u09a6\u09c7\u0996\u09c1\u09a8' + '</span> \u2197</a>';
      }
      el.innerHTML = H;
    };
  }

  renderRows();
  tick();
  setInterval(tick, 1000);
  setInterval(renderRows, 30000);
})();
