/* BusJatri service worker - offline support + instant repeat visits.
   /js, /css  -> cache-first (files carry ?v= cache busters, so new
                 deploys are new URLs; old entries are simply unused).
   /data/     -> stale-while-revalidate: serve cache instantly, refresh
                 in the background for next visit.
   HTML pages -> network-first, offline falls back to cached index.html.
   Cross-origin requests (analytics, fonts) are never intercepted. */
var SHELL = 'bj-shell-20260925a';
var DATA_CACHE = 'bj-data-20260925a';

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(SHELL).then(function (c) {
    return c.add('/index.html').catch(function () {});
  }));
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  var isData = url.pathname.indexOf('/data/') === 0;
  var isStatic = url.pathname.indexOf('/js/') === 0 || url.pathname.indexOf('/css/') === 0;

  if (isData) {
    /* stale-while-revalidate */
    e.respondWith(
      caches.open(DATA_CACHE).then(function (c) {
        return c.match(req).then(function (hit) {
          var net = fetch(req).then(function (res) {
            if (res && res.ok) c.put(req, res.clone());
            return res;
          }).catch(function () { return hit; });
          return hit || net;
        });
      })
    );
  } else if (isStatic) {
    /* cache-first for versioned assets */
    e.respondWith(
      caches.open(SHELL).then(function (c) {
        return c.match(req).then(function (hit) {
          return hit || fetch(req).then(function (res) {
            if (res && res.ok) c.put(req, res.clone());
            return res;
          });
        });
      })
    );
  } else if (req.mode === 'navigate') {
    /* network-first HTML, offline fallback */
    e.respondWith(
      fetch(req).catch(function () {
        return caches.match(req).then(function (hit) {
          return hit || caches.match('/index.html');
        });
      })
    );
  }
});
