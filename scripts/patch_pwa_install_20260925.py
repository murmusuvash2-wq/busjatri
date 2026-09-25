#!/usr/bin/env python3
"""
2026-09-25 patch: PWA install experience ("install" banner on visit).

What the user asked for: when someone opens the website on a phone, an
Install-type option should appear (so the site can be added to the
home screen like an app).

What this adds:
  A. manifest.json - name, icons, standalone display, theme colors
     (Chrome/Android needs this + a service worker + HTTPS before it
     will offer install; the service worker already shipped today).
  B. js/pwa-install.js - captures Chrome's beforeinstallprompt event and
     shows a small bottom banner: app icon + "Install BusJatri" +
     Install button + dismiss (X). Dismissal is remembered for 7 days.
     EN + BN text via the site's existing label-en/label-bn CSS pattern.
  C. index.html - manifest link, apple-touch-icon + iOS standalone meta,
     and the script tag. Busted with pwa20260925a.

Icons come from scripts/make_pwa_icons.py (run by the workflow before
this patcher - PIL required).

Idempotent. Backslash-free source.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as fh:
        return fh.read()

def write(rel, content):
    with open(os.path.join(ROOT, rel), 'w', encoding='utf-8') as fh:
        fh.write(content)

# ---------------------------------------------------------- A. manifest ----

MANIFEST = """{
  "name": "BusJatri - West Bengal Bus Timetable",
  "short_name": "BusJatri",
  "description": "West Bengal bus timetables: routes, stops and departure times for 4,100+ buses. Works offline.",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#fffcf4",
  "theme_color": "#b8791f",
  "lang": "en",
  "dir": "ltr",
  "categories": ["travel", "navigation"],
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "/icons/icon-maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable" },
    { "src": "/icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
"""

if os.path.exists(os.path.join(ROOT, 'manifest.json')):
    print('SKIP manifest.json (already exists)')
else:
    write('manifest.json', MANIFEST)
    print('CREATED manifest.json')

# ------------------------------------------------------ B. install JS ------

PWajs = """/* BusJatri PWA install banner: catches Chrome's beforeinstallprompt
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
"""

if os.path.exists(os.path.join(ROOT, 'js', 'pwa-install.js')):
    print('SKIP js/pwa-install.js (already exists)')
else:
    write('js/pwa-install.js', PWajs)
    print('CREATED js/pwa-install.js')

# ------------------------------------------------------ C. index.html ------

idx = read('index.html')

MANIFEST_LINK = '  <link rel="manifest" href="manifest.json" />'
NL = chr(10)
APPLE = ('  <link rel="apple-touch-icon" href="apple-touch-icon.png" />' + NL +
         '  <meta name="apple-mobile-web-app-capable" content="yes" />' + NL +
         '  <meta name="apple-mobile-web-app-status-bar-style" content="default" />' + NL +
         '  <meta name="apple-mobile-web-app-title" content="BusJatri" />')

if 'rel="manifest"' in idx:
    print('SKIP index.html (manifest link already present)')
elif '<meta name="theme-color"' in idx:
    anchor = '  <meta name="theme-color" content="#b8791f" />'
    assert anchor in idx, 'theme-color meta not found'
    idx = idx.replace(anchor, anchor + NL + MANIFEST_LINK + NL + APPLE, 1)
    print('PATCHED index.html (manifest + apple meta)')
else:
    print('ERROR: theme-color anchor not found')
    sys.exit(1)

SCRIPT_TAG = '  <script defer src="js/pwa-install.js?v=pwa20260925a"></script>'
if 'pwa-install.js' in idx:
    print('SKIP index.html (script tag already present)')
elif '</body>' in idx:
    idx = idx.replace('</body>', SCRIPT_TAG + NL + '</body>', 1)
    print('PATCHED index.html (pwa-install.js script)')
else:
    print('ERROR: </body> not found')
    sys.exit(1)

write('index.html', idx)

# ------------------------------------------------------------ validate ----
errors = []

m = json.loads(read('manifest.json'))
if m.get('display') != 'standalone':
    errors.append('manifest: display != standalone')
if len(m.get('icons', [])) < 4:
    errors.append('manifest: fewer than 4 icons')

for f in ['icons/icon-192.png', 'icons/icon-512.png',
          'icons/icon-maskable-192.png', 'icons/icon-maskable-512.png',
          'apple-touch-icon.png']:
    if not os.path.exists(os.path.join(ROOT, f)):
        errors.append('missing ' + f)

idx2 = read('index.html')
for needle in ['rel="manifest"', 'apple-touch-icon', 'pwa-install.js', 'apple-mobile-web-app-title']:
    if needle not in idx2:
        errors.append('index.html: missing ' + needle)

if chr(92) in read('js/pwa-install.js'):
    errors.append('pwa-install.js: backslash found')

if errors:
    print('VALIDATION FAILED:')
    for e in errors:
        print('  -', e)
    sys.exit(1)

print('VALIDATION OK')
