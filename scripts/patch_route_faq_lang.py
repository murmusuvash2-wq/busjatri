#!/usr/bin/env python3
"""
Route pages FAQ language fix (2026-09-23) — audit fix #1.

Problem: route pages showed BOTH English and Bengali FAQ always (no
only-en/only-bn classes), plus small EN-mode Bengali leaks (hero sub,
alt-route wait/duration). Violated the EN = zero Bengali rule.

This patcher (idempotent, backslash-free):
  1. Fixes scripts/gen_route_v2.py source (FAQ classes, title, hero sub,
     alt-wait, alt-total, CSS cache bump) for future regenerations.
  2. Surgically patches EXISTING route pages that still carry the old
     faq-lang-tag markup (route pairs not in route_meta).
  3. Appends only-en/only-bn CSS rules to css/seo-v2.css.
  4. Fixes broken link in blog/burdwan-to-karunamoyee.html.

Run from repo root:  python3 scripts/patch_route_faq_lang.py
"""

import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BTT = os.path.join(ROOT, "bus-time-table")
NL = chr(10)

BN_DIGITS = "০১২৩৪৫৬৭৮৯"


def bn_to_en(s):
    out = []
    for ch in s:
        i = BN_DIGITS.find(ch)
        out.append(str(i) if i >= 0 else ch)
    return "".join(out)


NEW_FAQ_FUNC = """def faq_html_v2(en, bn):
    def det(q, a, cls, i):
        return f'<details class="{cls}"{" open" if i == 0 else ""}><summary>{q}</summary><div class="fa-body">{a}</div></details>'

    parts = [det(q, a, "faq only-en", i) for i, (q, a) in enumerate(en)]
    parts += [det(q, a, "faq only-bn", i) for i, (q, a) in enumerate(bn)]
    return "".join(parts)
"""


def replace_block(src, start_marker, new_block):
    """Replace from start_marker line to the start of the next top-level def/comment."""
    i = src.find(start_marker)
    assert i >= 0, "marker not found: " + start_marker[:40]
    j = src.find(NL + NL + "# ", i)
    assert j > i, "block end not found"
    return src[:i] + new_block.rstrip(NL) + src[j:]


def patch_generator():
    p = os.path.join(ROOT, "scripts", "gen_route_v2.py")
    src = open(p, encoding="utf-8").read()
    if 'det(q, a, "faq only-en"' in src:
        print("gen_route_v2.py: already patched")
        return

    src = replace_block(src, "def faq_html_v2(en, bn):", NEW_FAQ_FUNC)

    fixes = [
        ('<h3 class="section-title">FAQ · সাধারণ প্রশ্ন</h3>',
         '<h3 class="section-title">{L("FAQs", "সাধারণ প্রশ্ন")}</h3>'),
        ('CSS_V2 = "seov2a"', 'CSS_V2 = "seov2b"'),
        ("""    <span class="alt-wait">{bn_num(o['wait'])} {L('min wait', 'মিনিট অপেক্ষা')}</span>""",
         """    <span class="alt-wait">{L(str(o['wait']), bn_num(o['wait']))} {L('min wait', 'মিনিট অপেক্ষা')}</span>"""),
        ("""· {bn_dur(o['total'])} ({g.fmt_duration(o['total'])})</b></div>""",
         """· {L(g.fmt_duration(o['total']), bn_dur(o['total']) + ' (' + g.fmt_duration(o['total']) + ')')}</b></div>"""),
        ("""    bn_sub = f'<p class="bn-sub">{g.esc(route_bn)} বাসের সময়সূচী</p>' if route_bn else "" """.rstrip(),
         """    bn_sub = f'<p class="bn-sub"><span class="label-en">{g.esc(origin)} → {g.esc(destination)} — bus timings & stoppages</span><span class="label-bn">{g.esc(route_bn)} বাসের সময়সূচী</span></p>' if route_bn else "" """.rstrip()),
    ]
    for old, new in fixes:
        assert old in src, "MISS in generator: " + old[:60]
        src = src.replace(old, new)

    open(p, "w", encoding="utf-8").write(src)
    ast.parse(src)
    print("gen_route_v2.py: patched (6 changes)")


def patch_css():
    p = os.path.join(ROOT, "css", "seo-v2.css")
    css = open(p, encoding="utf-8").read()
    if "only-bn" in css:
        print("seo-v2.css: already patched")
        return
    if not css.endswith(NL):
        css += NL
    css += (NL + "/* FAQ language toggle (2026-09-23) */" + NL
            + ".only-bn{display:none}" + NL
            + "body.lang-bn .only-en{display:none}" + NL
            + "body.lang-bn .only-bn{display:block}" + NL)
    open(p, "w", encoding="utf-8").write(css)
    print("seo-v2.css: language toggle rules appended")


def patch_blog():
    p = os.path.join(ROOT, "blog", "burdwan-to-karunamoyee.html")
    if not os.path.exists(p):
        print("blog: file missing, skipped")
        return
    src = open(p, encoding="utf-8").read()
    if "buses-from-burdwan.html" in src:
        src = src.replace("buses-from-burdwan.html", "buses-from-bardhaman.html")
        open(p, "w", encoding="utf-8").write(src)
        print("blog: broken stand link fixed (burdwan -> bardhaman)")
    else:
        print("blog: already fixed")


def patch_alt_wait_numbers(src):
    out = []
    pos = 0
    tag = '<span class="alt-wait">'
    while True:
        i = src.find(tag, pos)
        if i < 0:
            out.append(src[pos:])
            break
        j = src.find("<span", i + len(tag))
        num_txt = src[i + len(tag):j].strip()
        if not num_txt or any(c in BN_DIGITS for c in num_txt) is False:
            out.append(src[pos:j])
            pos = j
            continue
        out.append(src[pos:i])
        out.append(tag + '<span class="label-en">' + bn_to_en(num_txt)
                   + '</span><span class="label-bn">' + num_txt + "</span> ")
        pos = j
    return "".join(out)


def patch_alt_totals(src):
    out = []
    pos = 0
    marker = 'class="alt-total"'
    tail = "</b></div>"
    while True:
        i = src.find(marker, pos)
        if i < 0:
            out.append(src[pos:])
            break
        kb = src.find(tail, i)
        if kb < 0:
            out.append(src[pos:])
            break
        seg = src[i:kb]
        k = seg.find("· ")
        op = seg.rfind(" (")
        if k < 0 or op < k:
            out.append(src[pos:kb])
            pos = kb
            continue
        bn_only = seg[k + 2:op]
        en_part = seg[op + 2:]
        if not en_part.endswith(")"):
            en_part = en_part + ")"
        if not bn_only or not en_part:
            out.append(src[pos:kb])
            pos = kb
            continue
        out.append(src[pos:i])
        out.append(seg[:k] + "· " + '<span class="label-en">' + en_part
                   + '</span><span class="label-bn">' + bn_only + " (" + en_part + ")</span>")
        pos = kb
    return "".join(out)


def patch_page_html(path):
    """Surgical fix of one old-style route page."""
    src = open(path, encoding="utf-8").read()
    if "faq-lang-tag" not in src:
        return False

    # 1. FAQ section title -> bilingual
    src = src.replace('<h3 class="section-title">FAQ · সাধারণ প্রশ্ন</h3>',
                      '<h3 class="section-title"><span class="label-en">FAQs</span>'
                      '<span class="label-bn">সাধারণ প্রশ্ন</span></h3>')

    # 2. FAQ details -> only-en / only-bn classes
    src = src.replace('<p class="faq-lang-tag">English</p>', "")
    src = src.replace('<p class="faq-lang-tag">বাংলা</p>', "")
    start = src.find('class="seo-section faq-v2"')
    assert start > 0, "faq section not found: " + path
    end = src.find("</section>", start)
    assert end > start, "faq section end not found: " + path
    seg = src[start:end]
    assert seg.count("<details") == 10, "unexpected details count in " + path
    chunks = seg.split("<details")
    rebuilt = [chunks[0]]
    for i, chunk in enumerate(chunks[1:]):
        # chunk begins with the old tag remainder, e.g. ' open><summary>...' or '><summary>...'
        gt = chunk.find(">")
        body = chunk[gt:]
        if i < 5:
            cls = "faq only-en" + ('" open' if i == 0 else "")
        else:
            cls = "faq only-bn" + ('" open' if i == 5 else "")
        rebuilt.append('<details class="' + cls + body)
    src = src[:start] + "".join(rebuilt) + src[end:]

    # 3. hero bn-sub -> bilingual
    i = src.find('<p class="bn-sub">')
    if i >= 0:
        j = src.find("</p>", i)
        inner = src[i + len('<p class="bn-sub">'):j]
        src = (src[:i] + '<p class="bn-sub"><span class="label-en">Bus timings & stoppages</span>'
               + '<span class="label-bn">' + inner + "</span></p>" + src[j + 4:])

    # 4 + 5. alt-route Bengali numbers/durations -> bilingual
    src = patch_alt_wait_numbers(src)
    src = patch_alt_totals(src)

    # 6. css cache buster
    src = src.replace("seo-v2.css?v=seov2a", "seo-v2.css?v=seov2b")

    open(path, "w", encoding="utf-8").write(src)
    return True


def main():
    patch_generator()
    patch_css()
    patch_blog()

    fixed = 0
    checked = 0
    skip = ("index.html", "nbstc-buses.html", "sbstc-buses.html",
            "wbtc-buses.html", "volvo-ac-buses.html", "shyamoli-paribahan-buses.html")
    for f in sorted(os.listdir(BTT)):
        if not f.endswith(".html") or f.startswith("buses-from-") or "-via-" in f:
            continue
        if f in skip:
            continue
        checked += 1
        if patch_page_html(os.path.join(BTT, f)):
            fixed += 1
    print("route pages checked: %d, old-style patched: %d" % (checked, fixed))


if __name__ == "__main__":
    main()
