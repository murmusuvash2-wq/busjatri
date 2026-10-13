/* BusJatri PWA install banner: catches Chrome's beforeinstallprompt
   and shows a small bottom banner with an Install button. Dismissal
   is remembered for 7 days. Text follows the site's label-en /
   label-bn pattern (see css/style.css). */
(function () {
  var KEY = 'bj-pwa-dismissed';
  var deferred = null;

  function dismissed() {
    try {
      var t = parseInt(localStorage.getItem(KEY) || '0', 10);
      return t > 0 && (Date.now() - t < 7 * 24 * 60 * 60 * 1000);
    } catch (e) { return false; }
  }

  function standalone() {
    return window.matchMedia('(display-mode: standalone)').matches
      || window.navigator.standalone === true;
  }

  function hide() {
    var d = document.getElementById('pwaInstall');
    if (d) d.remove();
  }

  function show() {
    if (document.getElementById('pwaInstall')) return;
    var d = document.createElement('div');
    d.id = 'pwaInstall';
    d.setAttribute('role', 'dialog');
    d.setAttribute('aria-label', 'Install BusJatri');
    d.style.cssText = 'position:fixed;left:12px;right:12px;bottom:14px;z-index:9999;display:flex;align-items:center;gap:12px;background:#211c16;color:#fffcf4;border:1px solid rgba(255,252,244,.15);border-radius:16px;padding:12px 14px;box-shadow:0 10px 34px rgba(0,0,0,.4);font-family:inherit';
    d.innerHTML =
      '<img src="icons/icon-192.png" alt="" width="44" height="44" style="width:44px;height:44px;border-radius:12px;flex:0 0 auto">' +
      '<div style="flex:1;min-width:0">' +
      '<div style="font-weight:700;font-size:14px;line-height:1.25"><span class="label-en">Install BusJatri</span><span class="label-bn">BusJatri ইনস্টল করুন</span></div>' +
      '<div style="font-size:12px;opacity:.82;line-height:1.35"><span class="label-en">Works offline - one tap from your home screen</span><span class="label-bn">অফলাইনেও চলবে - হোম স্ক্রিন থেকে এক ট্যাপে</span></div>' +
      '</div>' +
      '<button id="pwaInstallBtn" style="background:#b8791f;color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:700;font-size:13px;flex:0 0 auto"><span class="label-en">Install</span><span class="label-bn">ইনস্টল</span></button>' +
      '<button id="pwaInstallClose" aria-label="Close" style="background:transparent;color:#fffcf4;border:0;font-size:19px;padding:4px 2px;flex:0 0 auto;line-height:1">×</button>';
    document.body.appendChild(d);
  }

  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferred = e;
    if (standalone() || dismissed()) return;
    show();
  });

  document.addEventListener('click', function (ev) {
    var t = ev.target;
    if (t && (t.id === 'pwaInstallBtn' || (t.parentNode && t.parentNode.id === 'pwaInstallBtn')) && deferred) {
      var btn = document.getElementById('pwaInstallBtn');
      if (btn) { btn.disabled = true; btn.style.opacity = '.6'; }
      deferred.prompt();
      if (deferred.userChoice) {
        deferred.userChoice.then(function () { deferred = null; hide(); });
      } else { deferred = null; hide(); }
    } else if (t && (t.id === 'pwaInstallClose' || (t.parentNode && t.parentNode.id === 'pwaInstallClose'))) {
      try { localStorage.setItem(KEY, String(Date.now())); } catch (e) {}
      hide();
    }
  });

  window.addEventListener('appinstalled', hide);
})();
