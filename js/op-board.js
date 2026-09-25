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
    if (isNaN(h) || isNan(mi) || mi > 59 || mi < 0) return null;
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
    return h > ':' + String(m).padStart(2, '0') + ' ' + ap;
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
    if (!f && !t) { alert('Fill From or To'); return; }
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
    if (t < now) return '<span class="lgone">' + String.fromCharCode(10003) + ' <span class="label-en">departed</span><span class="label-bn">চলে গেছে</span></span>';
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
    var rows = OP_DATA.filter(function (b) { return originOf(b) && parseTime(b[4]) != null; })
      .map(function (b) { return { b: b, t: parseTime(b[4]) }; })
      .sort(function (x, y) { return ((x.t < now ? x.t + 1440 : x.t) - now) - ((y.t < now ? y.t + 1440 : y.t) - now); })
      .slice(0, 9);
    var el2 = document.getElementById('lvRows');
    if (el2) el2.innerHTML = rows.length ? rows.map(function (r) {
      return '<div class="lv-row' + (r.t < now ? ' past' : '') + '" onclick="location.href=' + Q + '../index.html#/bus/' + encodeURIComponent(r.b[0]) + Q + '">' +
        '<span class="ht">' + fmtTime(r.t).replace(' ', '') + '</span>' +
        '<span class="lnm">' + esc(r.b[1]) + '</span>' +
        '<span class="ldst">' + String.fromCharCode(8594) + ' ' + esc(r.b[3]) + '</span>' +
        lvTag(r.t, now) + '</div>';
    }).join('') : '<div class="lv-row"><span class="lnm">No departures found</span></div>';
  }
  function tick() {
    var d = new Date();
    var c = document.getElementById('bjLvClock');
    if (c) c.innerHTML = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0') + ':' + String(d.getSeconds()).padStart(2, '0') + '<small>IST</small>';
  }
  renderRows();
  tick();
  setInterval(tick, 1000);
  setInterval(renderRows, 30000);
})();
