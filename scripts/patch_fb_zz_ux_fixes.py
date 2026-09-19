#!/usr/bin/env python3
"""UX audit fixes (2026-09-19). User-approved items 1-5, nothing else.

1. Route map + chip rows: horizontal slider (scroll + arrow buttons).
2. Invalid times fixed at data level (61 SBSTC "12:65 AM" buses).
3. Dark mode: timetable index + blog get the toggle.
4. Departure-time search on the homepage ("8:15", "8pm", "20:00").
5. Timetable directory search: bus-name fallback.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITE = '--write' in sys.argv


def patch(path, marker, anchor, replacement, count=1):
    p = ROOT / path
    s = p.read_text(encoding='utf-8')
    if marker in s:
        print('ok (already patched): ' + path)
        return
    if s.count(anchor) != count:
        print('FAIL ' + path + ': anchor not found or ambiguous (count=' + str(s.count(anchor)) + '):')
        print(repr(anchor[:180]))
        sys.exit(1)
    s = s.replace(anchor, replacement)
    if WRITE:
        p.write_text(s, encoding='utf-8')
        print('patched ' + path)
    else:
        print('would patch ' + path)


# ---------------------------------------------------------------- 2. data times
TIME_RE = re.compile(r'^\s*(\d{1,2}):(\d{2})\s*(AM|PM)\s*$', re.I)


def fix_data_times():
    p = ROOT / 'data' / 'busjatri_data.json'
    d = json.loads(p.read_text(encoding='utf-8'))
    n = 0

    def norm(t):
        nonlocal n
        if not isinstance(t, str):
            return t
        m = TIME_RE.match(t)
        if not m:
            return t
        h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
        if mi <= 59 and 1 <= h <= 12:
            return t
        h24 = (h % 12) + (12 if ap == 'PM' else 0)
        total = (h24 * 60 + mi) % 1440
        nh, nm = total // 60, total % 60
        out = '{}:{:02d} {}'.format(nh % 12 or 12, nm, 'AM' if nh < 12 else 'PM')
        if out != t.strip():
            n += 1
        return out

    for b in d['buses']:
        for k in ('departure_time', 'arrival_time'):
            if k in b:
                b[k] = norm(b.get(k))
        for s in b.get('stoppages') or []:
            for k in ('up_time', 'down_time'):
                if k in s:
                    s[k] = norm(s.get(k))
    if n:
        if WRITE:
            p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
            print('normalised %d invalid times (data)' % n)
        else:
            print('would normalise %d invalid times (data)' % n)
    else:
        print('ok (no invalid times in data)')


# ---------------------------------------------------------------- 1. slider css
SLIDER_CSS = '''
/* ---- horizontal sliders: route map + chip rows (UX audit 2026-09-19) ---- */
.seo-section{position:relative}
.routemap{position:relative;overflow-x:auto;overflow-y:hidden;padding-bottom:4px}
.rm-track{min-width:100%;width:max-content;box-sizing:border-box}
.rm-stop{width:auto;min-width:58px;padding:0 5px;box-sizing:border-box}
.chip-row.hscroll{flex-wrap:nowrap;overflow-x:auto;overflow-y:hidden;scroll-snap-type:x proximity;padding:2px 0 6px}
.chip-row.hscroll>*{flex:0 0 auto;scroll-snap-align:start}
.hscroll-arr{position:absolute;top:44%;transform:translateY(-50%);width:32px;height:32px;border-radius:50%;border:1px solid var(--line);background:var(--surface);color:var(--ink);cursor:pointer;display:none;align-items:center;justify-content:center;font-size:15px;line-height:1;padding:0;z-index:6;box-shadow:0 2px 8px rgba(33,28,22,.18)}
.hscroll-arr:hover{border-color:var(--amber)}
.hscroll-arr.hsa-prev{left:2px}
.hscroll-arr.hsa-next{right:2px}
@media(max-width:640px){.rm-stop{min-width:46px;padding:0 3px}.hscroll-arr{width:28px;height:28px;font-size:13px}}
'''

# ---------------------------------------------------------------- 1. slider js
SLIDER_JS = '''/* BusJatri route map / chip-row horizontal slider (UX audit 2026-09-19).
   Adds swipe scrolling + prev/next arrow buttons to .routemap and
   .chip-row.hscroll containers. Arrows appear only when the content
   actually overflows. No dependencies. */
(function () {
  function makeArr(el, dir) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'hscroll-arr ' + (dir < 0 ? 'hsa-prev' : 'hsa-next');
    b.setAttribute('aria-label', dir < 0 ? 'Scroll left' : 'Scroll right');
    b.textContent = dir < 0 ? '\\u276E' : '\\u276F';
    b.addEventListener('click', function (e) {
      e.preventDefault();
      el.scrollBy({ left: dir * Math.max(120, el.clientWidth * 0.7), behavior: 'smooth' });
    });
    el.parentNode.insertBefore(b, el);
    return b;
  }
  function initOne(el) {
    if (el.__bjSlider) return;
    el.__bjSlider = 1;
    var prev = makeArr(el, -1);
    var next = makeArr(el, 1);
    function upd() {
      var over = el.scrollWidth - el.clientWidth > 8;
      prev.style.display = (over && el.scrollLeft > 4) ? 'flex' : 'none';
      next.style.display = (over && el.scrollLeft < el.scrollWidth - el.clientWidth - 4) ? 'flex' : 'none';
    }
    el.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('resize', upd);
    if (typeof MutationObserver !== 'undefined') {
      new MutationObserver(upd).observe(el, { childList: true, subtree: true });
    }
    upd();
  }
  function init() {
    document.querySelectorAll('.routemap, .chip-row.hscroll').forEach(initOne);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
'''


def ensure_slider_js():
    p = ROOT / 'js' / 'route-slider.js'
    if p.exists() and p.read_text(encoding='utf-8').strip() == SLIDER_JS.strip():
        print('ok (js/route-slider.js current)')
        return
    if WRITE:
        p.write_text(SLIDER_JS, encoding='utf-8')
        print('wrote js/route-slider.js')
    else:
        print('would write js/route-slider.js')


def main():
    # ---- 1. sliders ----
    p_css = ROOT / 'css' / 'seo.css'
    s_css = p_css.read_text(encoding='utf-8')
    if '.chip-row.hscroll{flex-wrap:nowrap' in s_css:
        print('ok (already patched): css/seo.css')
    else:
        s_css = s_css.rstrip() + '\n' + SLIDER_CSS
        if WRITE:
            p_css.write_text(s_css, encoding='utf-8')
            print('patched css/seo.css')
        else:
            print('would patch css/seo.css')
    ensure_slider_js()

    # gen_seo_pages: via chips hscroll (route pages)
    patch(
        'scripts/gen_seo_pages.py',
        '<div class="chip-row hscroll">{chips}</div>',
        '<div class="chip-row">{chips}</div>',
        '<div class="chip-row hscroll">{chips}</div>',
    )
    # gen_seo_pages: rmChips hscroll (timetable index)
    patch(
        'scripts/gen_seo_pages.py',
        '<div class="chip-row hscroll" id="rmChips"></div>',
        '<div class="chip-row" id="rmChips"></div>',
        '<div class="chip-row hscroll" id="rmChips"></div>',
    )
    # gen_seo_pages: shell() loads route-slider.js (route/place/index pages)
    patch(
        'scripts/gen_seo_pages.py',
        '<script defer src="../js/route-slider.js"></script>',
        '{footer_html()}\n</body>',
        '{footer_html()}\n<script defer src="../js/route-slider.js"></script>\n</body>',
    )
    # polish: place-page destination chips hscroll
    patch(
        'scripts/polish_route_pages.py',
        "chiprow = ('<div class=\"chip-row hscroll\" aria-label=\"All destinations\">'",
        "chiprow = ('<div class=\"chip-row\" aria-label=\"All destinations\">'",
        "chiprow = ('<div class=\"chip-row hscroll\" aria-label=\"All destinations\">'",
    )
    # polish: keep up to 10 stops on the route map (slider handles overflow)
    patch(
        'scripts/polish_route_pages.py',
        'if len(stops) <= 10:',
        'if len(stops) <= 7:',
        'if len(stops) <= 10:',
    )
    # polish: index.html gets the dark toggle too
    patch(
        'scripts/polish_route_pages.py',
        "for p in sorted(PAGES.glob('*.html')):\n        s",
        "for p in sorted(PAGES.glob('*.html')):\n        if p.name == 'index.html':\n            continue\n        s",
        "for p in sorted(PAGES.glob('*.html')):\n        s",
    )
    # gen_stop_network: via-page route chips hscroll + slider js
    patch(
        'scripts/gen_stop_network.py',
        '<div class="chip-row hscroll">{\'\'.join(chips)}</div>',
        '<div class="chip-row">{\'\'.join(chips)}</div>',
        '<div class="chip-row hscroll">{\'\'.join(chips)}</div>',
    )
    patch(
        'scripts/gen_stop_network.py',
        '<script defer src="../js/route-slider.js"></script>',
        '{THEME_JS}\n</body>',
        '{THEME_JS}\n<script defer src="../js/route-slider.js"></script>\n</body>',
        count=2,
    )

    # ---- 2. data time fix ----
    fix_data_times()

    # ---- 3a. timetable index: theme button id sync ----
    patch(
        'scripts/gen_seo_pages.py',
        'if(t==="dark"&&document.getElementById("bjThemeBtn"))document.getElementById("bjThemeBtn")',
        'if(t==="dark"&&document.getElementById("themeBtn"))document.getElementById("themeBtn")',
        'if(t==="dark"&&document.getElementById("bjThemeBtn"))document.getElementById("bjThemeBtn")',
    )

    # ---- 3b. blog: dark mode button + script ----
    patch(
        'scripts/gen_blog.py',
        'id="bjThemeBtn" aria-label="Toggle dark mode"',
        '<a href="../via/" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Stops</a>\n    </nav>',
        '<a href="../via/" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Stops</a>\n'
        '      <button id="bjThemeBtn" aria-label="Toggle dark mode" style="background:var(--surface,#fffcf4);border:1px solid var(--line,#ccc);border-radius:999px;padding:6px 12px;cursor:pointer;font-weight:600;color:var(--ink-dim,#665);font-size:13px;font-family:inherit;line-height:1.2">\u25d0</button>\n'
        '    </nav>',
    )
    patch(
        'scripts/gen_blog.py',
        'd?"dark":"light"',
        '</header>"""',
        '</header>\n'
        '<script>(function(){try{var b=document.getElementById("bjThemeBtn");if(!b)return;'
        'if(localStorage.getItem("seo-theme")==="dark"){document.body.classList.add("dark");b.textContent="\\u2600";}'
        'b.addEventListener("click",function(){var d=document.body.classList.toggle("dark");'
        'try{localStorage.setItem("seo-theme",d?"dark":"light");}catch(e){}b.textContent=d?"\\u2600":"\\u25d0";});}catch(e){}})();</script>\n'
        '"""',
    )

    # ---- 4. time search: app.js ----
    patch(
        'js/app.js',
        'function looksLikeTime(',
        'function doSearch() {',
        '/* Time query support (UX audit 2026-09-19): "8:15", "8pm", "20:00" */\n'
        'function looksLikeTime(q) {\n'
        "  q = String(q || '').trim().toLowerCase();\n"
        '  return /^\\d{1,2}:\\d{2}\\s*(am|pm)?$/.test(q) || /^\\d{1,2}\\s*(am|pm)$/.test(q);\n'
        '}\n'
        'function parseClock(q) {\n'
        "  q = String(q || '').trim().toLowerCase().replace(/\\s+/g, '');\n"
        '  const m = /^(\\d{1,2})(?::(\\d{2}))?(am|pm)?$/.exec(q);\n'
        '  if (!m) return null;\n'
        "  let h = +m[1], mi = m[2] ? +m[2] : 0, ap = m[3];\n"
        '  if (mi > 59) return null;\n'
        "  if (ap) { if (h < 1 || h > 12) return null; h %= 12; if (ap === 'pm') h += 12; }\n"
        '  else if (h > 23) return null;\n'
        '  return h * 60 + mi;\n'
        '}\n'
        'function doSearch() {',
    )
    patch(
        'js/app.js',
        'window.__bjTimeQuery = q;',
        '  } else if (from || to) {\n    const q = from || to;\n    results = results.filter(b =>',
        '  } else if ((from || to) && looksLikeTime(from || to) && parseClock(from || to) != null) {\n'
        '    const q = from || to;\n'
        '    const target = parseClock(q);\n'
        '    const cd = t => { const d = Math.abs(t - target) % 1440; return Math.min(d, 1440 - d); };\n'
        '    results = results.filter(b => parseTime(b.departure_time) != null && cd(parseTime(b.departure_time)) <= 90);\n'
        '    results.sort((a, b) => cd(parseTime(a.departure_time)) - cd(parseTime(b.departure_time)));\n'
        '    window.__bjTimeQuery = q;\n'
        '  } else if (from || to) {\n'
        '    const q = from || to;\n'
        '    results = results.filter(b =>',
    )
    patch(
        'js/app.js',
        'window.__bjTimeQuery = null;',
        'async function renderSearch(el) {\n  const params',
        'async function renderSearch(el) {\n  window.__bjTimeQuery = null;\n  const params',
    )
    patch(
        'js/app.js',
        'Buses departing around',
        '    ${from || to ? `<p style="color:var(--ink-dim);font-size:13.5px;margin-bottom:18px">${esc(from || \'\u2026\')} \u2192 ${esc(to || \'\u2026\')}${stop ? ` <span class="badge badge-ac">stop ${esc(stop)}</span>` : \'\'}</p>` : \'\'}',
        '    ${window.__bjTimeQuery ? `<p style="color:var(--amber);font-size:13.5px;font-weight:600;margin-bottom:18px">${icon(\'clock\')} Buses departing around ${esc(window.__bjTimeQuery)} (\u00b190 min)</p>` : from || to ? `<p style="color:var(--ink-dim);font-size:13.5px;margin-bottom:18px">${esc(from || \'\u2026\')} \u2192 ${esc(to || \'\u2026\')}${stop ? ` <span class="badge badge-ac">stop ${esc(stop)}</span>` : \'\'}</p>` : \'\'}',
    )

    # ---- 4b. time search: stop-search-all.js (the live overlay) ----
    patch(
        'js/stop-search-all.js',
        'function looksLikeTime(',
        '      rebuildCompactStops();',
        '      rebuildCompactStops();\n'
        '      function looksLikeTime(q) {\n'
        "        q = String(q || '').trim().toLowerCase();\n"
        '        return /^\\d{1,2}:\\d{2}\\s*(am|pm)?$/.test(q) || /^\\d{1,2}\\s*(am|pm)$/.test(q);\n'
        '      }\n'
        '      function parseClock(q) {\n'
        "        q = String(q || '').trim().toLowerCase().replace(/\\s+/g, '');\n"
        '        var m = /^(\\d{1,2})(?::(\\d{2}))?(am|pm)?$/.exec(q);\n'
        '        if (!m) return null;\n'
        '        var h = +m[1], mi = m[2] ? +m[2] : 0, ap = m[3];\n'
        '        if (mi > 59) return null;\n'
        "        if (ap) { if (h < 1 || h > 12) return null; h %= 12; if (ap === 'pm') h += 12; }\n"
        '        else if (h > 23) return null;\n'
        '        return h * 60 + mi;\n'
        '      }\n'
        '      window.__bjTimeQuery = null;',
    )
    patch(
        'js/stop-search-all.js',
        'window.__bjTimeQuery = q;',
        '      } else {\n        var q = from || to;\n        rows = all.filter(function (b) {',
        '      } else if ((from || to) && looksLikeTime(from || to) && parseClock(from || to) != null) {\n'
        '        var q = from || to;\n'
        '        var target = parseClock(q);\n'
        '        function bjDist(t) { var d = Math.abs(t - target) % 1440; return Math.min(d, 1440 - d); }\n'
        '        rows = all.filter(function (b) { return parseTime(b.departure_time) != null && bjDist(parseTime(b.departure_time)) <= 90; });\n'
        '        rows.sort(function (x, y) { return bjDist(parseTime(x.b.departure_time)) - bjDist(parseTime(y.b.departure_time)); });\n'
        '        window.__bjTimeQuery = q;\n'
        '      } else {\n'
        '        var q = from || to;\n'
        '        rows = all.filter(function (b) {',
    )
    patch(
        'js/stop-search-all.js',
        'viaHtml + timeHtml +',
        '        viaHtml +',
        '        viaHtml + timeHtml +',
    )
    patch(
        'js/stop-search-all.js',
        'var timeHtml = window.__bjTimeQuery',
        '      el.innerHTML =\n        \'<div class="container"',
        '      var timeHtml = window.__bjTimeQuery ? \'<p style="text-align:center;font-size:12.5px;color:var(--amber);font-weight:600;margin:2px 0 10px">Buses departing around \' + esc(window.__bjTimeQuery) + \' (\u00b190 min)</p>\' : \'\';\n'
        '      el.innerHTML =\n        \'<div class="container"',
    )

    # ---- 5. timetable directory: bus-name fallback search ----
    patch(
        'scripts/gen_seo_pages.py',
        'function bjBusSearch(',
        'if(!shown&&!routeChips.length)empty.style.display="block";else empty.style.display="none";',
        'if(!shown&&!routeChips.length){bjBusSearch(q,rm,rmc,info,empty);}else{empty.style.display="none";}',
    )
    patch(
        'scripts/gen_seo_pages.py',
        'window.__bjBuses=',
        'function countUp(el,target,dur){',
        'function bjBusSearch(q,rm,rmc,info,empty){\n'
        '  if(window.__bjBuses){\n'
        '    var hits=window.__bjBuses.filter(function(b){return (b.bus_name||"").toLowerCase().indexOf(q)>=0;}).slice(0,24);\n'
        '    if(hits.length){\n'
        '      var chips=hits.map(function(b){\n'
        '        return \'<a class="rm-chip" href="../index.html#/bus/\'+encodeURIComponent(b.id)+\'">\'+(b.bus_name||"Bus")+(b.departure_time?\' <span class="n">\'+b.departure_time+\'</span>\':\'\')+(b.origin?\' <span class="n">\'+b.origin+\' \'+(b.destination||"")+\'</span>\':\'\')+\'</a>\';\n'
        '      }).join("");\n'
        '      rmc.innerHTML=chips;\n'
        '      rm.style.display="";\n'
        '      info.textContent="Showing "+hits.length+" bus services matching "+q;\n'
        '      info.style.display="block";\n'
        '      empty.style.display="none";\n'
        '      return;\n'
        '    }\n'
        '  }\n'
        '  if(!window.__bjBuses&&window.fetch){\n'
        '    fetch("../data/app-index.json").then(function(r){return r.json();}).then(function(d){\n'
        '      window.__bjBuses=(d&&d.buses)?d.buses:[];\n'
        '      bjBusSearch(q,rm,rmc,info,empty);\n'
        '    }).catch(function(){});\n'
        '    return;\n'
        '  }\n'
        '  empty.style.display="block";\n'
        '}\n'
        'function countUp(el,target,dur){',
    )


if __name__ == '__main__':
    main()
