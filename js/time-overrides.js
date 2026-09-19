/* BusJatri — runtime time overrides
 * Loads data/time-overrides.json and patches bus-data responses at fetch
 * level so corrected times show everywhere (search, bus page) without
 * regenerating any build artifacts. Keep this script FIRST in index.html.
 * Format: { "<bus-id>": { "<stop name>": {"up": "9:30 AM", "down": "…"} } }
 */
(function () {
  'use strict';
  var OVERRIDES = {};
  var ready = fetch('data/time-overrides.json', { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : {}; })
    .then(function (o) { OVERRIDES = o || {}; })
    .catch(function () { OVERRIDES = {}; });

  function t2m(t) {
    if (!t) return 0;
    var m = /^(\d{1,2}):(\d{2})\s*(AM|PM)$/i.exec(String(t).trim());
    if (!m) return 0;
    var h = +m[1], mi = +m[2], ap = m[3].toUpperCase();
    if (ap === 'AM') h = h === 12 ? 0 : h; else h = h === 12 ? 12 : h + 12;
    return h * 60 + mi;
  }

  function patchBusDetail(d) { // {id, stoppages:[...]}
    if (!d || !d.id || !d.stoppages) return d;
    var ov = OVERRIDES[d.id]; if (!ov) return d;
    d.stoppages.forEach(function (s) {
      var t = ov[s.name]; if (!t) return;
      if (t.up) s.up_time = t.up;
      if (t.down) s.down_time = t.down;
    });
    return d;
  }

  function patchIndex(d) { // {buses:[{id,sx,ux,dx}], sn:[...]}
    if (!d || !d.buses) return d;
    d.buses.forEach(function (b) {
      var ov = b.id && OVERRIDES[b.id]; if (!ov || !b.sx) return;
      b.sx.forEach(function (si, i) {
        var nm = d.sn && d.sn[si]; if (!nm) return;
        var t = ov[nm]; if (!t) return;
        if (t.up) b.ux[i] = t2m(t.up);
        if (t.down) b.dx[i] = t2m(t.down);
      });
    });
    return d;
  }

  var orig = window.fetch;
  window.fetch = function () {
    var url = String(arguments[0] || '');
    var self = this, args = arguments;
    return orig.apply(self, args).then(function (resp) {
      if (!resp.ok) return resp;
      var isDetail = /data\/bus-details\/([^\/?]+)\.json/.test(url) && !/bus-details\.json/.test(url.match(/([^\/?]+)\.json/)[0]);
      var isAgg = /data\/bus-details\.json/.test(url);
      var isIndex = /data\/app-index(-lite)?\.json/.test(url);
      if (!(isDetail || isAgg || isIndex)) return resp;
      return ready.then(function () {
        return resp.clone().json().then(function (j) {
          var out = j;
          try {
            if (isDetail) out = patchBusDetail(j);
            else if (isAgg) { Object.keys(j).forEach(function (k) { patchBusDetail(j[k]); }); }
            else if (isIndex) out = patchIndex(j);
          } catch (e) { /* never break the app */ }
          return new Response(JSON.stringify(out), {
            status: 200, statusText: 'OK',
            headers: { 'Content-Type': 'application/json' }
          });
        });
      }).catch(function () { return resp; });
    });
  };
})();
