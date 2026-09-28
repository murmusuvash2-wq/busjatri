#!/usr/bin/env python3
"""UI unify patch (2026-09-28) — BusJatri
A. Dark button: ONE design site-wide (38x38 round, sun/moon SVG)
   - route pages (load seo-page.js): style override injected by JS
   - sbstc-buses.html: markup patch (lang-btn pill -> theme-btn round)
   - blog posts: markup patch (◐ pill -> round SVG button) + script rewrite
   - stand/via/static/homepage already use icon-btn design (no change needed)
B. Back button: every non-homepage page gets a top-left back arrow
   - route + sbstc pages: injected by seo-page.js (smart back: internal -> history.back(), else Home)
   - stand (76) / via (2605) / blog (16) / about / contact / privacy / 404 / city-routes / contribute: inline HTML patch (self-contained)
C. SPA (app.js/bus-page.js): EN-only "Back" gets পিছনে Bengali label
D. Cache-bust: seo-page.js refs (route+sbstc), app.js + bus-page.js (index.html)
Idempotent: files already containing bjBackBtn are skipped.
"""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stats = {}

def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()

def write(p, src):
    open(os.path.join(ROOT, p), "w", encoding="utf-8").write(src)

# ---------------------------------------------------------------- back button HTML (inline, self-contained)
BACK_ONCLICK = ("if(history.length>1&&document.referrer.indexOf(location.origin)===0)"
                "{history.back()}else if(location.pathname!=='/'){location.href='/'}")
BACK_BTN = ('<button type="button" id="bjBackBtn" class="back-nav" aria-label="Back" title="Back" '
            'onclick="' + BACK_ONCLICK + '" '
            'style="width:38px;height:38px;border-radius:50%;border:1px solid var(--line,rgba(33,28,22,.12));'
            'background:var(--surface-2,#f6efe0);display:inline-flex;align-items:center;justify-content:center;'
            'cursor:pointer;color:var(--ink,#211c16);padding:0;margin-right:10px;flex:0 0 auto;transition:border-color .2s,transform .3s">'
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true" style="width:18px;height:18px"><path d="M15 18l-6-6 6-6"/></svg></button>')

def insert_back_before(path, anchor_re, anchor_group=0):
    """insert BACK_BTN right after the header-inner opening tag (before its first child)."""
    src = read(path)
    if 'id="bjBackBtn"' in src:
        stats.setdefault("skipped", []).append(path); return 0
    m = re.search(anchor_re, src)
    if not m:
        stats.setdefault("noanchor", []).append(path); return 0
    out = src[:m.end()] + "\n    " + BACK_BTN + src[m.end():]
    write(path, out); return 1

# ---------------------------------------------------------------- 1. seo-page.js (route + sbstc pages)
def patch_seo_page_js():
    p = "js/seo-page.js"
    src = read(p)
    if "addBackBtn" in src:
        stats.setdefault("skipped", []).append(p); return 0
    n = 0
    # 1a. CSS + chevron constants after MOON
    moon = ("  var MOON = '<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" "
            "stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z\"/></svg>';")
    assert moon in src, "MOON anchor missing"
    consts = moon + """
  var CHEV = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>';
  var BJ_UI_CSS = '<style>'
    + '.back-nav{width:38px;height:38px;border-radius:50%;border:1px solid var(--line);background:var(--surface-2);display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:var(--ink);padding:0;margin-right:10px;flex:0 0 auto;transition:border-color .2s,transform .3s}'
    + '.back-nav svg{width:18px;height:18px}'
    + '.back-nav:hover{border-color:var(--amber,#b8791f)}'
    + '.back-nav:active{transform:scale(.92)}'
    + '#themeBtn.theme-btn{width:38px;height:38px;border-radius:50%;border:1px solid var(--line);background:var(--surface-2);display:inline-flex;align-items:center;justify-content:center;cursor:pointer;padding:0;font-size:15px;line-height:1;transition:border-color .2s,transform .3s}'
    + '#themeBtn.theme-btn svg{width:17px;height:17px}'
    + '#themeBtn.theme-btn:hover{border-color:var(--amber,#b8791f)}'
    + '#themeBtn.theme-btn:active{transform:scale(.92)}'
    + '</style>';"""
    src = src.replace(moon, consts); n += 1
    # 1b. addBackBtn function before init()
    init_anchor = "  function init() {"
    assert init_anchor in src
    fn = """  function addBackBtn() {
    var host = document.querySelector('.header-inner');
    if (!host || document.getElementById('bjBackBtn')) return;
    var b = document.createElement('button');
    b.type = 'button'; b.id = 'bjBackBtn'; b.className = 'back-nav';
    b.setAttribute('aria-label', 'Back'); b.title = 'Back';
    b.innerHTML = CHEV;
    b.onclick = function () {
      if (history.length > 1 && document.referrer.indexOf(location.origin) === 0) history.back();
      else if (location.pathname !== '/') location.href = '/';
    };
    host.insertBefore(b, host.firstChild);
  }

"""
    src = src.replace(init_anchor, fn + init_anchor); n += 1
    # 1c. call in init()
    call_anchor = "    if (bnBtn) bnBtn.onclick = function () { setLang(true); };"
    assert call_anchor in src
    src = src.replace(call_anchor, call_anchor + "\n    addBackBtn();\n    document.head.insertAdjacentHTML('beforeend', BJ_UI_CSS);"); n += 1
    write(p, src); return n

stats["seo-page.js"] = patch_seo_page_js()

# ---------------------------------------------------------------- 2. app.js + bus-page.js (Bengali Back label)
def patch_app_js():
    p = "js/app.js"
    src = read(p)
    new, n = re.subn(r"\$\{icon\('chevronLeft'\)\} Back</div>",
                     "${icon('chevronLeft')} <span class=\"label-en\">Back</span><span class=\"label-bn\">পিছনে</span></div>", src)
    if n: write(p, new)
    return n

def patch_bus_page_js():
    p = "js/bus-page.js"
    src = read(p)
    n = 0
    new, k = re.subn(r"\+ ' Back</div>",
                     "+ ' <span class=\\\"label-en\\\">Back</span><span class=\\\"label-bn\\\">পিছনে</span></div>", src); n += k
    if "Back</span></div>' +" in new:
        new = new.replace("Back</span></div>' +", 'Back</span><span class="label-bn">পিছনে</span></div>\' +'); n += 1

    if n: write(p, new)
    return n

stats["app.js"] = patch_app_js()
stats["bus-page.js"] = patch_bus_page_js()

# ---------------------------------------------------------------- 3. route pages (bus-time-table/*.html minus stand/sbstc): bump seo-page.js version
route = [f for f in glob.glob("bus-time-table/*.html")
         if not os.path.basename(f).startswith("buses-from-") and f != "bus-time-table/sbstc-buses.html"]
bumped = 0
for f in route:
    src = read(f)
    new, k = re.subn(r"(seo-page\.js\?v=)[\w-]+", r"\g<1>uifix20260928a", src)
    if new != src: write(f, new); bumped += 1
stats["route-pages-bumped"] = bumped

# ---------------------------------------------------------------- 4. sbstc: bump + themeBtn markup -> round
p = "bus-time-table/sbstc-buses.html"
src = read(p)
if 'id="themeBtn" class="lang-btn"' in src:
    src, k = re.subn(r'<button id="themeBtn" class="lang-btn"[^>]*>',
                     '<button type="button" id="themeBtn" class="theme-btn" aria-label="Toggle dark mode" title="Toggle dark mode">', src)
    src, k2 = re.subn(r"(seo-page\.js\?v=)[\w-]+", r"\g<1>uifix20260928a", src)
    if "bjBackBtn" not in src:
        m = re.search(r'<div class="container header-inner">', src)
        if m:
            src = src[:m.end()] + "\n    " + BACK_BTN + src[m.end():]
    write(p, src); stats["sbstc"] = k + k2

# ---------------------------------------------------------------- 5. stand pages (76): back button
n = 0
for f in glob.glob("bus-time-table/buses-from-*.html"):
    n += insert_back_before(f, r'<div class="header-inner">')
stats["stand-back"] = n

# ---------------------------------------------------------------- 6. via pages (2605): back button
n = 0
for f in glob.glob("via/*.html"):
    n += insert_back_before(f, r'<div class="header-inner">')
stats["via-back"] = n

# ---------------------------------------------------------------- 7. blog (16): back button + theme button + script
SUN_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
           'aria-hidden="true" style="width:17px;height:17px"><circle cx="12" cy="12" r="4.5"/>'
           '<path d="M12 2v2.2M12 19.8V22M2 12h2.2M19.8 12H22M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M19.4 4.6l-1.6 1.6M6.2 17.8l-1.6 1.6"/></svg>')
MOON_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true" style="width:17px;height:17px">'
            '<path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z"/></svg>')
NEW_BLOG_BTN = ('<button id="bjThemeBtn" aria-label="Toggle dark mode" title="Toggle dark mode" '
                'style="width:38px;height:38px;border-radius:50%;border:1px solid var(--line,#ccc);'
                'background:var(--surface-2,#f6efe0);display:inline-flex;align-items:center;justify-content:center;'
                'cursor:pointer;color:var(--ink,#211c16);padding:0;font-family:inherit;line-height:1">' + MOON_SVG + '</button>')
NEW_BLOG_SCRIPT = ('<script>(function(){try{var SUN=\'' + SUN_SVG + '\';var MOON=\'' + MOON_SVG + '\';'
                   'var b=document.getElementById("bjThemeBtn");if(!b)return;'
                   'if(localStorage.getItem("seo-theme")==="dark"){document.body.classList.add("dark");b.innerHTML=SUN;}'
                   'else{b.innerHTML=MOON;}'
                   'b.addEventListener("click",function(){var d=document.body.classList.toggle("dark");'
                   'try{localStorage.setItem("seo-theme",d?"dark":"light");}catch(e){}b.innerHTML=d?SUN:MOON;});}catch(e){}})();</script>')

n = 0
for f in glob.glob("blog/*.html"):
    src = read(f)
    if 'id="bjBackBtn"' in src and "uifix" in src: stats.setdefault("skipped", []).append(f); continue
    changed = 0
    src, k = re.subn(r'<button id="bjThemeBtn"[^>]*>◐</button>', NEW_BLOG_BTN, src); changed += k
    src, k = re.subn(r'<script>\(function\(\)\{try\{var b=document\.getElementById\("bjThemeBtn"\);.*?</script>',
                     NEW_BLOG_SCRIPT, src, flags=re.S); changed += k
    if 'id="bjBackBtn"' not in src:
        m = re.search(r'<div class="container header-inner">', src)
        if m: src = src[:m.end()] + "\n    " + BACK_BTN + src[m.end():]; changed += 1
    if changed: write(f, src); n += 1
stats["blog-patched"] = n

# ---------------------------------------------------------------- 8. static pages
n = 0
for f, pat in [("about.html", r'<div class="container header-inner">\s*<div class="logo"'),
               ("contact.html", r'<div class="container header-inner">\s*<div class="logo"'),
               ("privacy-policy.html", r'<div class="container header-inner">\s*<div class="logo"')]:
    src = read(f)
    if 'id="bjBackBtn"' in src: stats.setdefault("skipped", []).append(f); continue
    m = re.search(pat, src)
    if m:
        src = src[:m.start()] + '<div class="container header-inner">\n    ' + BACK_BTN + src[m.start()+len('<div class="container header-inner">'):]
        write(f, src); n += 1
stats["static-back"] = n

n = 0
for f in ["404.html", "kolkata-city-routes.html"]:
    src = read(f)
    if 'id="bjBackBtn"' in src: stats.setdefault("skipped", []).append(f); continue
    m = re.search(r'<div class="header-inner">', src)
    if m:
        src = src[:m.end()] + "\n    " + BACK_BTN + src[m.end():]; write(f, src); n += 1
stats["404-cityroutes-back"] = n

# contribute.html (no dark support on this page - back button only)
src = read("contribute.html")
if 'id="bjBackBtn"' not in src:
    m = re.search(r'(<header>\s*<div>)(<a class="logo" href="/">)', src)
    if m:
        src = src[:m.end(1)] + BACK_BTN + " " + src[m.end(1):]
        write("contribute.html", src); stats["contribute-back"] = 1
    else: stats["contribute-back"] = 0
else: stats["contribute-back"] = 0

# ---------------------------------------------------------------- 9. index.html version bumps (app.js, bus-page.js)
src = read("index.html")
new, k1 = re.subn(r"(app\.js\?v=)[\w-]+", r"\g<1>uifix20260928a", src)
new, k2 = re.subn(r"(bus-page\.js\?v=)[\w-]+", r"\g<1>uifix20260928a", new)
if new != src: write("index.html", new)
stats["index-bumps"] = k1 + k2

# ---------------------------------------------------------------- report
print("PATCH SUMMARY")
for k, v in stats.items():
    if isinstance(v, list):
        print(f"  {k}: {len(v)} files ({v[:3]})")
    else:
        print(f"  {k}: {v}")
if stats.get("noanchor"):
    print("WARNING noanchor:", stats["noanchor"][:10])
