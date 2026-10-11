/* BusJatri cookie consent — simple Accept / Reject (stored in localStorage) */
(function () {
  try {
    var KEY = 'bj-consent';
    if (localStorage.getItem(KEY)) {
      if (localStorage.getItem(KEY) === 'rejected') window['ga-disable-G-L4E3D1YX9X'] = true;
      return;
    }
    var css = document.createElement('style');
    css.textContent =
      '.bj-consent{position:fixed;left:0;right:0;bottom:0;z-index:9999;background:var(--surface,#fffcf4);' +
      'border-top:1px solid var(--line,#e0d6c4);box-shadow:0 -4px 18px rgba(50,35,10,.12);padding:12px 16px;' +
      'font-size:13px;color:var(--ink,#211c16);display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:center}' +
      '.bj-consent p{margin:0;flex:1 1 260px;line-height:1.5}' +
      '.bj-consent a{color:var(--accent,#b8791f);font-weight:700;text-decoration:underline}' +
      '.bj-consent button{min-height:40px;padding:0 18px;border-radius:10px;font-size:13px;font-weight:700;cursor:pointer;border:1px solid var(--line,#e0d6c4)}' +
      '.bj-consent .ok{background:var(--accent,#b8791f);color:#fff;border-color:transparent}' +
      '.bj-consent .no{background:transparent;color:var(--ink,#211c16)}';
    document.head.appendChild(css);
    function decide(v) {
      localStorage.setItem(KEY, v);
      if (v === 'rejected') window['ga-disable-G-L4E3D1YX9X'] = true;
      bar.remove();
    }
    var bar = document.createElement('div');
    bar.className = 'bj-consent';
    bar.setAttribute('role', 'dialog');
    bar.innerHTML =
      '<p>We use cookies for analytics and (where shown) advertising. ' +
      '<a href="/privacy-policy">Privacy Policy</a></p>' +
      '<button class="ok" type="button">Accept</button>' +
      '<button class="no" type="button">Reject</button>';
    bar.querySelector('.ok').onclick = function () { decide('accepted'); };
    bar.querySelector('.no').onclick = function () { decide('rejected'); };
    (document.body || document.documentElement).appendChild(bar);
  } catch (e) { /* no-op */ }
})();
