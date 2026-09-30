#!/usr/bin/env python3
"""Add the 14 redBus-sourced WBTC (CTC) long routes (found 2026-09-30).

6 already have pages -> insert a WBTC (CTC) corridor card section.
8 have no page       -> build a new page with the same structure/CSS as the
                        existing bus-time-table pages (hero + WBTC section +
                        FAQs + related links + script tail), and add to sitemap.

Source: redBus WBTC (CTC) operator pages (redBus is an official WBTC booking
partner). Every card carries the source note.
"""
import json, os, re

BASE = os.path.join(os.path.dirname(__file__), "..")
BT = os.path.join(BASE, "bus-time-table")
SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
       'aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>')

# from, to, via, buses, first, last, fare, dur, dur_bn
ROUTES = [
    ("Habra", "Bakkhali", "via Bally", 1, "4:50 AM", "4:50 AM", 143, "6h 40m", "৬ ঘণ্টা ৪০ মিনিট"),
    ("Habra", "Namkhana", "", 4, "4:25 AM", "6:25 AM", 123, "5h 25m", "৫ ঘণ্টা ২৫ মিনিট"),
    ("Habra", "Midnapore", "", 5, "4:20 AM", "7:20 AM", 138, "3h 50m", "৩ ঘণ্টা ৫০ মিনিট"),
    ("Habra", "Haldia", "via Barasat", 2, "5:35 AM", "6:10 AM", 132, "4h 30m", "৪ ঘণ্টা ৩০ মিনিট"),
    ("Habra", "Bankura", "via Barasat", 1, "5:25 AM", "5:25 AM", 207, "6h 05m", "৬ ঘণ্টা ০৫ মিনিট"),
    ("Habra", "Asansol", "via Barasat > Durgapur", 2, "4:40 AM", "5:05 AM", 195, "4h 55m", "৪ ঘণ্টা ৫৫ মিনিট"),
    ("Habra", "Durgapur", "via Barasat > Dunlop", 3, "4:40 AM", "5:30 AM", 165, "3h 40m", "৩ ঘণ্টা ৪০ মিনিট"),
    ("Habra", "Bishnupur", "via Barasat > Joyrambati", 1, "5:45 AM", "5:45 AM", 141, "5h 40m", "৫ ঘণ্টা ৪০ মিনিট"),
    ("Habra", "Tarapith", "via Barasat", 1, "6:45 AM", "6:45 AM", 192, "5h 45m", "৫ ঘণ্টা ৪৫ মিনিট"),
    ("Habra", "Jhargram", "via Barasat > Midnapur", 1, "4:20 AM", "4:20 AM", 172, "5h 05m", "৫ ঘণ্টা ০৫ মিনিট"),
    ("Kolkata", "Bishnupur", "via Joyrambati", 1, "6:00 AM", "6:00 AM", 120, "4h 30m", "৪ ঘণ্টা ৩০ মিনিট"),
    ("Kolkata", "Balurghat", "via Malda", 1, "7:00 PM", "7:00 PM", 800, "10h 30m", "১০ ঘণ্টা ৩০ মিনিট"),
    ("Kolkata", "Malda", "via Krishnanagar", 2, "7:00 PM", "9:00 PM", 610, "7h 25m", "৭ ঘণ্টা ২৫ মিনিট"),
    ("Kolkata", "Siliguri", "via Raiganj", 3, "5:50 PM", "7:00 PM", 1355, "11h 45m", "১১ ঘণ্টা ৪৫ মিনিট"),
]


def slug(a, b):
    f = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return f"{f(a)}-to-{f(b)}"


def card(a, b, via, buses, first, last, fare, dur, dur_bn):
    bn = ('দৈনিক একটি পরিষেবা' if buses == 1 else f'{buses}টি পরিষেবা প্রতিদিন')
    en_n = ('single daily service' if buses == 1 else f'{buses} services daily')
    v = f' <span style="color:var(--amber-ink,#6b4610);font-weight:600">· {via}</span>' if via else ''
    return f'''<div class="bus-row">
      <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{first}</span></div></div>
      <div class="bmid">
        <div class="op">WBTC (CTC) <span style="color:var(--amber-ink,#6b4610);font-weight:600">· {a} → {b}</span>{v}</div>
        <div class="mrow">⏱ ~{dur} · 🚌 {en_n} <span class="label-bn">{bn}</span> · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> {last}</div>
      </div>
      <div class="bright"><span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span><span class="badge">from ₹{fare}</span></div>
    </div>'''


def section(a, b, via, buses, first, last, fare, dur, dur_bn):
    return f'''<section class="seo-section">
  <h3 class="section-title"><span class="label-en">WBTC (CTC) Government Service</span><span class="label-bn">ডাব্লুবিটিসি (সিটিসি) সরকারি পরিষেবা</span></h3>
  {card(a, b, via, buses, first, last, fare, dur, dur_bn)}
  <p class="bn-sub"><span class="label-en">Timings from the official WBTC (CTC) listing on redBus (an official WBTC booking partner). Buses can run late. Spotted a change? Report it on our <a href="../contribute.html">Contribute page</a>.</span><span class="label-bn">সময়সূচি রেডবাসে তালিকাভুক্ত অফিসিয়াল ডাব্লুবিটিসি (সিটিসি) তথ্য অনুযায়ী। বাস দেরিতে চলতে পারে। সময় বদলে থাকলে আমাদের <a href="../contribute.html">Contribute পেজে</a> জানান।</span></p>
</section>'''


HEAD_TPL = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta}">
<link rel="canonical" href="https://busjatri.in/bus-time-table/{slug}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://busjatri.in/bus-time-table/{slug}">
<meta property="og:image" content="https://busjatri.in/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{meta}">
<meta name="theme-color" content="#b8791f">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700;9..144,800&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Bengali:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../css/seo.css?v=rt20260924">
<link rel="stylesheet" href="../css/seo-v2.css?v=seov2b">
<script type="application/ld+json">{jsonld}</script>
</head>
<body>
<header class="header">
  <div class="container header-inner">
    <a href="../index.html" class="logo" aria-label="BusJatri home">
      <img class="brand-logo" src="/logo.png" alt="BusJatri" style="width:30px;height:30px;border-radius:50%">
      Bus<span>Jatri</span>
    </a>
    <div class="hdr-ctrl">
      <div class="lang-switch" role="group" aria-label="Language">
        <button type="button" id="langEn" class="pill pill-en on">EN</button>
        <button type="button" id="langBn" class="pill pill-bn">বাংলা</button>
      </div>
      <button type="button" id="themeBtn" class="theme-btn" aria-label="Toggle dark mode"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z"/></svg></button>
    </div>
  </div>
</header>
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:860px">
<div class="crumbs"><a href="../index.html"><span class="label-en">Home</span><span class="label-bn">হোম</span></a> › <a href="./"><span class="label-en">Bus Timetable</span><span class="label-bn">বাস টাইম টেবিল</span></a> › <span>{a} → {b}</span></div>
<div class="seo-hero">
  <h1>{a} <span class="arr">→</span> {b}</h1>
  <div class="stat-chips"><span class="schip">🚌 {buses} <span class="label-en">WBTC buses daily</span><span class="label-bn">টি ডব্লুবিটিসি বাস প্রতিদিন</span></span><span class="schip hot">⏰ <span class="label-en">First</span><span class="label-bn">প্রথম</span> {first}</span><span class="schip">⏰ <span class="label-en">Last</span><span class="label-bn">শেষ</span> {last}</span><span class="schip">⏱ ~{dur}</span><span class="schip">₹{fare} <span class="label-en">onwards</span><span class="label-bn">থেকে</span></span></div>
  <p class="seo-intro" style="margin:12px 0 0;color:var(--ink-dim,#5c544a);font-size:14.5px;line-height:1.6;max-width:72ch"><span class="label-en">{intro_en}</span><span class="label-bn">{intro_bn}</span></p>
</div>
{wbtc_sec}
{faq_sec}
{links_sec}
</main>
<script defer src="../js/seo-page.js?v=noback20260930"></script>
<script defer src="../js/route-slider.js"></script>
<script>
(function(){{
  var rows=[].slice.call(document.querySelectorAll('.bus-row'));
  var KEEP=10,STEP=50,btn=null;
  function bn(n){{var d='০১২৩৪৫৬৭৮৯';return String(n).replace(/[0-9]/g,function(c){{return d[+c];}});}}
  function isBn(){{return document.body.className.indexOf('lang-bn')>-1;}}
  function leftCount(){{var n=0;for(var i=0;i<rows.length;i++){{if(rows[i].classList.contains('cut')){{n++;}}}}return n;}}
  if(leftCount()>0){{}}
}})();
</script>
</body>
</html>
'''


def faq_block(a, b, buses, first, last, fare, dur, dur_bn, via):
    en1 = f"What is the first bus from {a} to {b}?"
    an1 = (f"The WBTC (CTC) service leaves {a} at <b>{first}</b> — the only daily service on this route."
           if buses == 1 else f"The first WBTC (CTC) bus leaves {a} at <b>{first}</b>; the last is at {last}.")
    en2 = f"How long does the {a} to {b} journey take and what is the fare?"
    an2 = f"About <b>{dur}</b>, with fares from <b>₹{fare}</b>. Times are from the official WBTC (CTC) listing on redBus — buses can run late."
    jsonld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": en1, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r'<[^>]+>', '', an1)}},
        {"@type": "Question", "name": en2, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r'<[^>]+>', '', an2)}},
    ]}
    bn1 = f"{a} থেকে {b} প্রথম বাস কখন ছাড়ে?"
    abn1 = f"ডব্লুবিটিসি (সিটিসি) বাস {a} থেকে ছাড়ে <b>{first}</b>-এ।"
    bn2 = f"{a} থেকে {b} যেতে কত সময় লাগে?"
    abn2 = f"প্রায় <b>{dur_bn}</b>। ভাড়া <b>₹{fare}</b> থেকে। সময় রেডবাসে তালিকাভুক্ত অফিসিয়াল তথ্য অনুযায়ী — বাস দেরিতে চলতে পারে।"
    sec = f'''<section class="seo-section faq-v2">
  <h3 class="section-title"><span class="label-en">FAQs</span><span class="label-bn">সাধারণ প্রশ্ন</span></h3>
  <details class="faq only-en" open><summary>{en1}</summary><div class="fa-body">{an1}</div></details>
  <details class="faq only-en"><summary>{en2}</summary><div class="fa-body">{an2}</div></details>
  <details class="faq only-bn" open><summary>{bn1}</summary><div class="fa-body">{abn1}</div></details>
  <details class="faq only-bn"><summary>{bn2}</summary><div class="fa-body">{abn2}</div></details>
</section>'''
    return sec, json.dumps(jsonld, ensure_ascii=False)


def links_block(a, b, existing):
    def chips(items, label_en, label_bn):
        c = ''.join(f'<a class="via-chip" href="./{s}.html">{t}</a>' for s, t in items)
        return (f'<div class="link-chips">{c}</div>') if items else ''
    from_items = [(s, s.replace('-to-', ' → ').replace('.html', '')) for s in existing if s.startswith(slug(a, 'x').split('-to-')[0] + '-to-')][:10]
    to_items = [(s, s.replace('-to-', ' → ').replace('.html', '')) for s in existing if s.endswith('-to-' + slug('x', b).split('-to-')[1] + '.html')][:10]
    out = ''
    if from_items:
        out += f'''<section class="seo-section">
  <h3 class="section-title"><span class="label-en">More Routes from {a}</span><span class="label-bn">{a} থেকে আরও রুট</span></h3>
  <div class="via-list">{chips(from_items, '', '')}</div>
</section>'''
    if to_items:
        out += f'''<section class="seo-section">
  <h3 class="section-title"><span class="label-en">More Buses to {b}</span><span class="label-bn">{b} যাওয়ার আরও বাস</span></h3>
  <div class="via-list">{chips(to_items, '', '')}</div>
</section>'''
    return out


def main():
    existing = sorted(f[:-5] for f in os.listdir(BT) if f.endswith('.html'))
    exset = set(existing)
    made_new, updated = [], []
    for (a, b, via, buses, first, last, fare, dur, dur_bn) in ROUTES:
        s = slug(a, b)
        wbtc = section(a, b, via, buses, first, last, fare, dur, dur_bn)
        if s in exset:
            p = os.path.join(BT, s + '.html')
            h = open(p, encoding='utf-8').read()
            if '<!-- wbtc-corridor-new -->' in h:
                continue
            marker = '<section class="seo-section faq-v2">'
            if marker in h:
                h = h.replace(marker, '<!-- wbtc-corridor-new -->\n' + wbtc + '\n' + marker, 1)
            else:
                h = h.replace('</main>', '<!-- wbtc-corridor-new -->\n' + wbtc + '\n</main>', 1)
            open(p, 'w', encoding='utf-8').write(h)
            updated.append(s)
        else:
            intro_en = (f"WBTC (CTC) runs {buses} bus{'es' if buses > 1 else ''} daily from {a} to {b}"
                        + (f", {via}" if via else "") + f" — the first at {first}, the last at {last}. "
                        f"Journey time is about {dur}; fares start at ₹{fare}. "
                        "Times are from the official WBTC (CTC) listing on redBus; verify before you travel.")
            intro_bn = (f"ডব্লুবিটিসি (সিটিসি) দৈনিক {buses}টি বাস {a} থেকে {b} চলে"
                        + (f", {via}" if via else "") + f" — প্রথম {first}, শেষ {last}। "
                        f"যাত্রার সময় প্রায় {dur}; ভাড়া ₹{fare} থেকে। "
                        "সময় রেডবাসে তালিকাভুক্ত অফিসিয়াল তথ্য অনুযায়ী; যাত্রার আগে যাচাই করুন।")
            faq_sec, jsonld = faq_block(a, b, buses, first, last, fare, dur, dur_bn, via)
            links_sec = links_block(a, b, existing)
            html = HEAD_TPL.format(
                title=f"{a} to {b} Bus Time Table (WBTC, first {first})",
                meta=f"{a} to {b} WBTC (CTC) bus timetable — {buses} bus{'es' if buses>1 else ''} daily, first {first}, last {last}, ~{dur}, from ₹{fare}. Timings on BusJatri.",
                slug=s, a=a, b=b, buses=buses, first=first, last=last, dur=dur, fare=fare,
                intro_en=intro_en, intro_bn=intro_bn, wbtc_sec=wbtc, faq_sec=faq_sec,
                links_sec=links_sec, jsonld=jsonld)
            open(os.path.join(BT, s + '.html'), 'w', encoding='utf-8').write(html)
            made_new.append(s)
    print("updated existing:", len(updated), updated)
    print("new pages:", len(made_new), made_new)


if __name__ == "__main__":
    main()
