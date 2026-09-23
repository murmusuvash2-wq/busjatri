#!/usr/bin/env python3
"""
Audit fixes part 2 (2026-09-23) — remaining small audit items.

1. robots.txt: block /admin.html from crawlers; admin.html gets noindex.
2. contribute.html: add missing canonical tag.
3. css/seo.css: add only-en/only-bn toggle rules (shared by blog/operator pages).
4. gen_operator_pages.py: language toggle (EN/bn) + FAQ 5 EN + 5 BN
   (data-driven) + FAQPage schema; pages regenerate via its own main().
5. gen_blog.py: FAQ (5 EN + 5 BN) for the 4 posts that had none.
6. 404.html: site-style not-found page (CSS/JS from the via stop pages).

Idempotent, backslash-free. Run from repo root.
"""

import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)
BSN = chr(92) + "n"


def rep(src, old, new, label):
    assert old in src, "MISS: " + label
    return src.replace(old, new, 1)


def patch_robots():
    p = os.path.join(ROOT, "robots.txt")
    s = open(p, encoding="utf-8").read()
    if "/admin.html" in s:
        print("robots.txt: already patched")
        return
    s = s.replace("User-agent: *" + NL + "Allow: /" + NL,
                  "User-agent: *" + NL + "Allow: /" + NL + "Disallow: /admin.html" + NL, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("robots.txt: admin.html disallowed")


def patch_admin():
    p = os.path.join(ROOT, "admin.html")
    s = open(p, encoding="utf-8").read()
    if 'name="robots" content="noindex"' in s:
        print("admin.html: already noindex")
        return
    i = s.find("<meta ")
    assert i > 0, "admin.html: no meta tag found"
    s = s[:i] + '<meta name="robots" content="noindex">' + NL + s[i:]
    open(p, "w", encoding="utf-8").write(s)
    print("admin.html: noindex meta added")


def patch_contribute():
    p = os.path.join(ROOT, "contribute.html")
    s = open(p, encoding="utf-8").read()
    if 'rel="canonical"' in s:
        print("contribute.html: already has canonical")
        return
    i = s.find("<meta ")
    assert i > 0, "contribute.html: no meta tag found"
    s = s[:i] + '<link rel="canonical" href="https://busjatri.in/contribute.html">' + NL + s[i:]
    open(p, "w", encoding="utf-8").write(s)
    print("contribute.html: canonical added")


def patch_seo_css():
    p = os.path.join(ROOT, "css", "seo.css")
    c = open(p, encoding="utf-8").read()
    if ".only-bn{display:none}" in c:
        print("seo.css: already patched")
        return
    if not c.endswith(NL):
        c += NL
    c += (NL + "/* language toggle for only-en/only-bn blocks (2026-09-23) */" + NL
          + ".only-bn{display:none}" + NL
          + "body.lang-bn .only-en{display:none}" + NL
          + "body.lang-bn .only-bn{display:block}" + NL)
    open(p, "w", encoding="utf-8").write(c)
    print("seo.css: only-en/only-bn rules appended")


# ---------------------------------------------------------------- operator --

OPS_INFO = {
    "sbstc-buses": ("government (South Bengal State Transport Corporation)",
                    "সরকারি — দক্ষিণবঙ্গ রাজ্য পরিবহণ সংস্থা"),
    "nbstc-buses": ("government (North Bengal State Transport Corporation)",
                    "সরকারি — উত্তরবঙ্গ রাজ্য পরিবহণ সংস্থা"),
    "wbtc-buses": ("government (West Bengal Transport Corporation)",
                   "সরকারি — পশ্চিমবঙ্গ পরিবহণ নিগম"),
    "shyamoli-paribahan-buses": ("a private operator",
                                 "একটি বেসরকারি পরিবহন সংস্থা"),
    "volvo-ac-buses": ("AC coach services — both government and private operators run Volvo AC buses",
                       "এসি কোচ পরিষেবা — সরকারি ও বেসরকারি দুই ধরনের অপারেটরই ভলভো এসি বাস চালায়"),
}

NAV_OLD = """      <a href="../index.html" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Home</a>
      <a href="./" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Routes</a>
    </nav>"""

NAV_NEW = """      <a href="../index.html" style="color:var(--ink-dim);text-decoration:none;font-weight:600"><span class="label-en">Home</span><span class="label-bn">হোম</span></a>
      <a href="./" style="color:var(--ink-dim);text-decoration:none;font-weight:600"><span class="label-en">Routes</span><span class="label-bn">রুট</span></a>
      <span class="lang-group" style="display:flex;gap:4px;margin-left:4px">
        <button class="lang-btn" id="langEN" onclick="setLang('en')" style="background:var(--amber-soft,#f6e7c6);border:1px solid var(--line,#ccc);border-radius:999px;padding:4px 10px;cursor:pointer;font-weight:700;font-size:12px;font-family:inherit">EN</button>
        <button class="lang-btn" id="langBN" onclick="setLang('bn')" style="background:transparent;border:1px solid var(--line,#ccc);border-radius:999px;padding:4px 10px;cursor:pointer;font-weight:700;font-size:12px;font-family:inherit">বাংলা</button>
      </span>
    </nav>"""

LANG_JS = """<script>(function(){function setLang(l){document.body.classList.toggle('lang-bn',l==='bn');var a=document.getElementById('langEN'),b=document.getElementById('langBN');if(a)a.style.background=l==='en'?'var(--amber-soft,#f6e7c6)':'transparent';if(b)b.style.background=l==='bn'?'var(--amber-soft,#f6e7c6)':'transparent';try{localStorage.setItem('seo-lang',l);}catch(e){}}window.setLang=setLang;var sv=null;try{sv=localStorage.getItem('seo-lang');}catch(e){}setLang(sv||'en');})();</script>"""

FAQ_BUILD = '''    op_info = OPS_INFO.get(op["stem"], ("bus services", "বাস পরিষেবা"))
    top_fr, top_to, top_n = "", "", 0
    if top:
        (top_fr, top_to), top_n = top[0]
    dest_names = [d for d, _ in dests.most_common(8) if d]
    nb = op["bn"]
    DET_STYLE = ' style="border:1px solid var(--line,rgba(33,28,22,.15));border-radius:10px;padding:10px 14px;margin:8px 0;background:var(--surface,#fffcf4)"'
    SUM_STYLE = '<summary style="cursor:pointer;font-weight:600;font-size:.95rem">'
    ANS_STYLE = '<p style="margin:8px 0 0;font-size:.9rem;line-height:1.7;color:var(--ink-dim,#665)">'
    faq_en = [
        ("How many " + op["name"] + " bus services are listed?",
         str(len(buses)) + " " + op["name"] + " services are listed on BusJatri, covering " + str(len(routes)) + " routes."),
        ("Which is the busiest " + op["name"] + " route?",
         (esc(top_fr) + " to " + esc(top_to) + ", with " + str(top_n) + " listed buses." if top_n else "Open the route list below for currently listed services.")),
        ("Where do " + op["name"] + " buses go?",
         ("Popular destinations include " + ", ".join(esc(d) for d in dest_names) + "." if dest_names else "See the destinations listed below.")),
        ("Are " + op["name"] + " buses government or private?",
         op["name"] + " buses are " + op_info[0] + "."),
        ("How do I check departure times for a " + op["name"] + " bus?",
         "Open any route page from the lists above for the full timetable. Times can change — confirm at the bus stand counter before travel."),
    ]
    faq_bn = [
        (op["name"] + " বাস কতটি তালিকাভুক্ত?",
         "BusJatri-তে " + str(len(buses)) + "টি " + op["name"] + " বাস তালিকাভুক্ত, " + str(len(routes)) + "টি রুট জুড়ে।"),
        (op["name"] + "-এর সবচেয়ে ব্যস্ত রুট কোনটি?",
         (esc(top_fr) + " থেকে " + esc(top_to) + " — " + str(top_n) + "টি বাস।" if top_n else "নিচের রুট তালিকা দেখুন।")),
        (op["name"] + " বাস কোথায় যায়?",
         ("জনপ্রিয় গন্তব্য: " + ", ".join(esc(d) for d in dest_names) + "।" if dest_names else "নিচের গন্তব্যের তালিকা দেখুন।")),
        (op["name"] + " কি সরকারি না বেসরকারি?",
         nb + " — " + op_info[1] + "।"),
        (op["name"] + " বাসের সময় কোথায় দেখব?",
         "উপরের যেকোনো রুট পেজ খুললে সম্পূর্ণ সময়সূচি পাবেন। সময় বদলাতে পারে — যাত্রার আগে কাউন্টারে নিশ্চিত করে নিন।"),
    ]
    faq_items = "".join(
        ('<details' + (' open' if i == 0 else '') + DET_STYLE + SUM_STYLE + q + "</summary>"
         + ANS_STYLE + a + "</p></details>")
        for i, (q, a) in enumerate(faq_en))
    faq_items += "".join(
        ('<details class="only-bn"' + (' open' if i == 0 else '') + DET_STYLE + SUM_STYLE + q + "</summary>"
         + ANS_STYLE + a + "</p></details>")
        for i, (q, a) in enumerate(faq_bn))
    faq_section = '<h2 class="op-h2" style="margin-top:26px">FAQ</h2>' + faq_items
    import json as _j
    faq_schema = ('<script type="application/ld+json">' + _j.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q,
                         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq_en + faq_bn]},
        ensure_ascii=False) + "</script>")

'''


def patch_operator_gen():
    p = os.path.join(ROOT, "scripts", "gen_operator_pages.py")
    s = open(p, encoding="utf-8").read()
    if "lang-btn" in s:
        print("gen_operator_pages.py: already patched")
        return

    s = rep(s, NAV_OLD, NAV_NEW, "operator nav")
    s = rep(s, '<div class="bn-line" style="color:var(--ink-dim);margin-top:6px">{bn}</div>',
            '<div class="bn-line only-bn" style="color:var(--ink-dim);margin-top:6px">{bn}</div>',
            "bn-line")
    s = rep(s, "</head>" + NL + "<body>",
            "{faq_schema}" + NL + "</head>" + NL + "<body>", "faq schema head anchor")

    BODY_ANCHOR = "    body = HEAD.format(title=esc(op['title'])"
    s = rep(s, BODY_ANCHOR, FAQ_BUILD + BODY_ANCHOR, "faq build block")

    # pass faq_schema into the format call
    FORMAT_OLD = ("                       BASE=BASE, h1=esc(op['h1']), bn=op['bn'], intro=esc(op['intro']))")
    FORMAT_NEW = ("                       BASE=BASE, h1=esc(op['h1']), bn=op['bn'], intro=esc(op['intro']), faq_schema=faq_schema)")
    s = rep(s, FORMAT_OLD, FORMAT_NEW, "format call")

    # append FAQ section to the page body
    ASSEMBLE_OLD = "    body += stats + popular + chiprow + '" + BSN + "</main>" + BSN + "' + FOOT"
    ASSEMBLE_NEW = "    body += stats + popular + chiprow + faq_section + '" + BSN + "</main>" + BSN + "' + FOOT"
    s = rep(s, ASSEMBLE_OLD, ASSEMBLE_NEW, "body assembly")

    # setLang JS before </body> in FOOT
    s = rep(s, "</body>" + NL + "</html>" + NL + "'''",
            LANG_JS + NL + "</body>" + NL + "</html>" + NL + "'''", "foot lang js")

    # OPS_INFO constant before OPERATORS list
    s = rep(s, "OPERATORS = [", "OPS_INFO = " + repr(OPS_INFO) + NL + NL + "OPERATORS = [", "ops info")

    open(p, "w", encoding="utf-8").write(s)
    ast.parse(s)
    print("gen_operator_pages.py: patched (lang toggle + FAQ)")


# ---------------------------------------------------------------- blog ------

BLOG_FAQS = {
    "kolkata-to-digha-bus-guide": [
        ("What time do morning buses leave Kolkata for Digha?",
         "SBSTC buses leave around 6:30, 7:00 and 7:30 AM from the Esplanade area; private AC coaches such as Jackson leave around 8:00 AM."),
        ("How long does the Kolkata to Digha bus journey take?",
         "About four to four and a half hours, depending on Bombay Road traffic."),
        ("Are there AC buses from Kolkata to Digha?",
         "Yes — private AC coaches run on this route alongside SBSTC government buses."),
        ("Do I need to book tickets in advance?",
         "Advance booking is not required; reach the counter about 30 minutes early on Fridays, Saturdays and holiday seasons."),
        ("When do return buses leave Digha?",
         "Return buses start very early in the morning; confirm the last bus time at the Digha stand counter before evening."),
        ("কলকাতা থেকে দীঘার সকালের বাস কটায় ছাড়ে?",
         "এসপ্ল্যানেড এলাকা থেকে SBSTC বাস প্রায় ৬:৩০, ৭:০০ ও ৭:৩০-এ ছাড়ে; বেসরকারি এসি কোচ (যেমন Jackson) ৮টার দিকে ছাড়ে।"),
        ("কলকাতা থেকে দীঘা যেতে কত সময় লাগে?",
         "বোম্বে রোডের ট্রাফিকের ওপর নির্ভর করে প্রায় চার থেকে সাড়ে চার ঘণ্টা।"),
        ("কলকাতা থেকে দীঘায় কি এসি বাস আছে?",
         "হ্যাঁ — SBSTC সরকারি বাসের পাশাপাশি বেসরকারি এসি কোচও চলে।"),
        ("আগে থেকে টিকিট বুক করতে হবে কি?",
         "তেমন দরকার নেই; শুক্র-শনিবার ও ছুটির মৌসুমে কাউন্টারে আধ ঘণ্টা আগে পৌঁছান।"),
        ("দীঘা থেকে ফেরার বাস কখন?",
         "ফেরার বাস খুব সকালেই ছাড়ে; বিকেলের আগেই কাউন্টার থেকে শেষ বাসের সময় নিশ্চিত করে নিন।"),
    ],
    "jangalmahal-bus-routes": [
        ("When do morning buses leave Jhargram for Manbazar and Khatra?",
         "Around 4:50 AM (Badsha) and 5:00 AM (Monami Travels); an AC bus leaves around 5:30 AM."),
        ("Are there direct buses from Kolkata to the Jangalmahal area?",
         "Yes — Mahamaya Super Fast style buses leave Kolkata around 4:30 AM for Khatra, Ranibandh and Manbazar."),
        ("Why is Khatra a useful junction?",
         "Buses towards Bankura, Purulia, Medinipur and Bardhaman pass through Khatra — change there if you miss a direct village bus."),
        ("How is bus travel in the monsoon?",
         "Forest roads can be slow in the rains; keep extra time and confirm schedules locally."),
        ("Where can I check timings for Jangalmahal routes?",
         "BusJatri route pages and the Khatra stop page list every bus with its arrival time at each stop."),
        ("ঝাড়গ্রাম থেকে মানবাজার/খাতড়ার সকালের বাস কখন?",
         "প্রায় ৪:৫০-এ বাদশা, ৫:০০-এ মনামী ট্রাভেলস; সাড়ে ৫টার দিকে একটি এসি বাসও ছাড়ে।"),
        ("কলকাতা থেকে জঙ্গলমহলে সরাসরি বাস আছে কি?",
         "হ্যাঁ — মহামায়া সুপার ফাস্ট ধরনের বাস ভোর ৪:৩০-এর দিকে কলকাতা থেকে ছাড়ে।"),
        ("খাতড়া জংশন কেন গুরুত্বপূর্ণ?",
         "বাঁকুড়া, পুরুলিয়া, মেদিনীপুর ও বর্ধমানের বাস খাতড়া দিয়েই যায় — সরাসরি বাস মিস হলে খাতড়ায় বাস বদলান।"),
        ("বর্ষাকালে যাত্রা কেমন?",
         "জঙ্গলের রাস্তা ধীরগতির হতে পারে; বাড়তি সময় হাতে রাখুন, স্থানীয়ভাবে সময় জেনে নিন।"),
        ("এই রুটগুলোর সময়সূচি কোথায় দেখব?",
         "BusJatri-র রুট পেজ ও খাতড়া স্টপ পেজে প্রতিটি বাসের সময় দেওয়া আছে।"),
    ],
    "how-to-find-bus-timings": [
        ("How do I search for a bus route on BusJatri?",
         "Type your start or destination in the homepage search box — suggestions appear in Bengali and English, and tapping a route shows every bus with times, operator and bus type."),
        ("What is a stop page?",
         "Every stop has its own page: a departure board of every bus passing that stop from early morning to late night. Over 2,600 stop pages are live."),
        ("Can I search in Bengali?",
         "Yes — search and suggestions work in both Bengali and English."),
        ("Does BusJatri need an account or payment?",
         "No — it is free, login-free, and light enough to work on slow connections."),
        ("What if I find a wrong time or a missing bus?",
         "Tell us on our Facebook page or by email — most corrections come from passengers, drivers and bus stand staff."),
        ("BusJatri-তে বাসের রুট কীভাবে খুঁজব?",
         "হোমপেজের সার্চ বক্সে যাত্রা শুরু বা গন্তব্যের নাম লিখুন — বাংলা ও ইংরেজি দুই ভাষাতেই সাজেশন আসবে, রুটে ট্যাপ করলেই সময় সহ সব বাসের তালিকা।"),
        ("স্টপ পেজ কী?",
         "প্রতিটি স্টপের নিজস্ব পেজ — ভোর থেকে গভীর রাত পর্যন্ত ওই স্টপ দিয়ে যাওয়া সব বাসের ডিপারচার বোর্ড। এখনই ২,৬০০-র বেশি স্টপ পেজ চালু।"),
        ("বাংলায় সার্চ করা যায়?",
         "হ্যাঁ — বাংলা ও ইংরেজি দুই ভাষাতেই সার্চ ও সাজেশন কাজ করে।"),
        ("অ্যাকাউন্ট বা টাকা লাগে কি?",
         "না — সাইট সম্পূর্ণ বিনামূল্যে, লগইন ছাড়াই, আর ধীর ইন্টারনেটেও ভালো চলে।"),
        ("ভুল সময় বা বাদ পড়া বাস দেখলে?",
         "ফেসবুক পেজ বা ইমেলে জানান — বেশিরভাগ সংশোধন যাত্রী, চালক ও স্ট্যান্ডের কর্মীদের কাছ থেকেই আসে।"),
    ],
    "purulia-to-manbazar-bus-timetable": [
        ("What is the first bus from Manbazar to Purulia?",
         "The Rajput service starts around 5:40 AM, followed by Sourav around 6:40 AM."),
        ("Which buses run between 8 and 9 AM?",
         "Bhabhalakshmi (~8:20 AM), Sri Shyam (~8:25 AM) and Maa Basanti (~8:50 AM)."),
        ("Are there buses later in the day?",
         "Yes — Maa Chhinnamasta around 11:10 AM, Rajput at 12:15 PM and Monalisha at 1:50 PM."),
        ("When does the first bus leave Purulia for Manbazar?",
         "The Suman bus leaves Purulia around 7:00 AM; returning Manbazar-Purulia buses also pick up passengers in the evening."),
        ("Are market days crowded?",
         "Yes — Mondays and other haat days fill up early with little luggage space; plan accordingly."),
        ("মানবাজার থেকে পুরুলিয়ার প্রথম বাস কটায়?",
         "রাজপুত সার্ভিস প্রায় ৫:৪০-এ, এরপর সৌরভ প্রায় ৬:৪০-এ ছাড়ে।"),
        ("সকাল ৮টা থেকে ৯টার মধ্যে কোন কোন বাস?",
         "ভাগ্যলক্ষ্মী (প্রায় ৮:২০), শ্রী শ্যাম (প্রায় ৮:২৫) এবং মা বাসন্তী (প্রায় ৮:৫০)।"),
        ("দুপুরের দিকে কি বাস আছে?",
         "হ্যাঁ — মা ছিন্নমস্তা প্রায় ১১:১০-এ, রাজপুত ১২:১৫-এ এবং মনালিষা ১:৫০-এ।"),
        ("পুরুলিয়া থেকে মানবাজারের প্রথম বাস কটায়?",
         "সুমন বাস সকাল ৭টার দিকে ছাড়ে; ফেরার পথে সন্ধ্যায়ও বাস পাওয়া যায়।"),
        ("বাজারের দিনে ভিড় বেশি হয়?",
         "হ্যাঁ — সোমবার ও অন্য হাটের দিনে বাস তাড়াতাড়ি ভরে যায়, মালপত্রের জায়গা কম থাকে।"),
    ],
}

FAQ_CALC = """    faq_html = ""
    faq_schema = ""
    if a.get("faq"):
        import json as _j
        items = "".join(
            "<details" + (" open" if i == 0 else "") + ' style="border:1px solid var(--line,rgba(33,28,22,.15));border-radius:10px;padding:10px 14px;margin:8px 0;background:var(--surface,#fffcf4)">' + '<summary style="cursor:pointer;font-weight:600;font-size:.95rem">' + q + "</summary>" + '<p style="margin:8px 0 0;font-size:.9rem;line-height:1.7;color:var(--ink-dim,#665)">' + ans + "</p></details>"
            for i, (q, ans) in enumerate(a["faq"]))
        faq_html = ('<section class="seo-section" style="margin-top:26px"><h3 class="section-title">FAQ</h3>' + items + "</section>")
        faq_schema = ('<script type="application/ld+json">' + _j.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": an}} for q, an in a["faq"]]}, ensure_ascii=False) + "</script>")
"""


def patch_blog_gen():
    p = os.path.join(ROOT, "scripts", "gen_blog.py")
    s = open(p, encoding="utf-8").read()
    if "BLOG_FAQ_DONE" in s:
        print("gen_blog.py: already patched")
        return

    # 1. add faq key to the 4 articles (before their "body" key)
    for slug, faq in BLOG_FAQS.items():
        anchor = '"slug": "' + slug + '"'
        i = s.find(anchor)
        assert i > 0, "article not found: " + slug
        j = s.find('        "body":', i)
        assert j > i, "body key not found for " + slug
        faq_lit = '        "faq": ' + repr(faq) + "," + NL
        s = s[:j] + faq_lit + s[j:]

    # 2. faq computation before the article_page return
    CALC_ANCHOR = '    return f"""<!DOCTYPE html>'
    i = s.find(CALC_ANCHOR)
    assert i > 0, "article_page return not found"
    s = s[:i] + FAQ_CALC + s[i:]

    # 3. placeholders in the article template
    s = rep(s, '<section class="seo-section" style="margin-top:26px">' + NL
            + '  <h3 class="section-title">Related Pages</h3>',
            "{faq_html}" + NL
            + '<section class="seo-section" style="margin-top:26px">' + NL
            + '  <h3 class="section-title">Related Pages</h3>',
            "faq placeholder")
    s = rep(s, "{GA4}<style>.article-body p{{line-height:1.85",
            "{faq_schema}{GA4}<style>.article-body p{{line-height:1.85",
            "faq schema placeholder")

    s = rep(s, "ARTICLES = [", "BLOG_FAQ_DONE = True" + NL + "ARTICLES = [", "marker")
    open(p, "w", encoding="utf-8").write(s)
    ast.parse(s)
    print("gen_blog.py: patched (4 posts FAQ + render)")


def build_404():
    """Site-style 404.html, CSS/JS taken from the via stop pages."""
    out = os.path.join(ROOT, "404.html")
    if os.path.exists(out):
        print("404.html: already present")
        return
    ref = open(os.path.join(ROOT, "via", "digha.html"), encoding="utf-8").read()
    i = ref.find("<style>")
    j = ref.find("</style>", i)
    css = ref[i + len("<style>"):j]
    i = ref.find("<script>")
    j = ref.find("</script>", i)
    js = ref[i + len("<script>"):j]
    parts = [
        "<!DOCTYPE html>", '<html lang="en">',
        '<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Page Not Found | BusJatri</title>',
        '<meta name="description" content="This page does not exist. Search West Bengal bus timetables, routes and stops on BusJatri.">',
        '<meta name="robots" content="noindex">',
        '<meta name="theme-color" content="#b8791f">',
    ]
    FAV = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E"
    FONTS = "https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,500;0,600;0,700;0,900&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Bengali:wght@400;500;600;700&display=swap"
    parts += [
        '<link rel="icon" href="' + FAV + '">',
        '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="' + FONTS + '" rel="stylesheet">',
        "<style>" + css + "</style></head>", "<body>",
    ]
    parts += [
        '<header class="header">',
        '  <div class="header-inner">',
        '    <a class="logo" href="index.html">',
        '      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/><path d="M4 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M17 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M6 10h12"/></svg>',
        "      Bus<span>Jatri</span>", "    </a>",
        '    <div class="header-actions">',
        '      <button class="icon-btn" id="themeBtn" onclick="toggleTheme()" title="Toggle theme" aria-label="Toggle dark mode"></button>',
        '      <div class="lang-group">',
        "        " + '<button class="lang-btn active" id="langEN" onclick="setLang(' + chr(39) + 'en' + chr(39) + ')">EN</button>',
        "        " + '<button class="lang-btn" id="langBN" onclick="setLang(' + chr(39) + 'bn' + chr(39) + ')">বাংলা</button>',
        "      </div>", "    </div>", "  </div>", "</header>",
        '<div class="wrap">',
        '<div class="crumbs"><a href="index.html"><span class="label-en">Home</span><span class="label-bn">হোম</span></a> › <b><span class="label-en">Page not found</span><span class="label-bn">পেজ পাওয়া যায়নি</span></b></div>',
        '<div class="hero">',
        '  <h1 class="routeline"><span class="rnode"><span class="rdot rdot-via"></span><span class="label-en">404 — Page not found</span><span class="label-bn">৪০৪ — পেজ পাওয়া যায়নি</span></span></h1>',
        '  <div class="hbn hbn-sub"><span class="label-en">This page does not exist. Search bus timings below.</span><span class="label-bn">এই পেজটি নেই। নিচে বাসের সময়সূচি খুঁজুন।</span></div>',
        "</div>",
        '<div class="sec"><h3><span class="label-en">Try these instead</span><span class="label-bn">এগুলো দেখুন</span></h3></div>',
        '<div class="chip-row">',
        '  <a class="rel-chip" href="index.html">🏠 <span class="label-en">Home — search buses</span><span class="label-bn">হোম — বাস খুঁজুন</span></a>',
        '  <a class="rel-chip" href="bus-time-table/">🚌 <span class="label-en">All bus timetables</span><span class="label-bn">সব বাস টাইম টেবিল</span></a>',
        '  <a class="rel-chip" href="via/">🚏 <span class="label-en">Bus stops A–Z</span><span class="label-bn">বাস স্টপ</span></a>',
        "</div>",
        '<div class="note">🚌 <span class="label-en"><b>Tip:</b> open the home page and type your start and destination in the search box — BusJatri covers 4,000+ bus services across West Bengal.</span><span class="label-bn"><b>টিপ:</b> হোম পেজে সার্চ বক্সে আপনার যাত্রা শুরু আর গন্তব্য লিখুন — পশ্চিমবঙ্গের ৪,০০০-এর বেশি বাস পাবেন।</span></div>',
        '<footer><a href="about.html">About</a><a href="contribute.html">Contribute</a><a href="blog/">Blog</a><a href="privacy-policy.html">Privacy</a></footer>',
        "</div>",
        "<script>" + js + "</script>", "</body></html>",
    ]
    html = NL.join(parts)
    open(out, "w", encoding="utf-8").write(html)
    print("404.html: built (" + str(len(html) // 1024) + "KB)")

def main():
    patch_robots()
    patch_admin()
    patch_contribute()
    patch_seo_css()
    patch_operator_gen()
    patch_blog_gen()
    build_404()
    print("audit fixes part 2 patcher done")


if __name__ == "__main__":
    main()
