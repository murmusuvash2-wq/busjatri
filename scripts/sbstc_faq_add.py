#!/usr/bin/env python3
"""#2 — Add research-backed FAQs (SEO).

From GSC (real searches hitting the site) the missing question patterns are:
  "today" · "distance by bus" · "booking/online" · "volvo/AC" · first/last bus ·
  "timetable pdf" · "fare"
Competitor FAQ sections (redBus/AbhiBus) answer exactly these.

A. sbstc-buses hub: +6 FAQs (EN+BN) and a FAQPage JSON-LD (the page only had a
   BreadcrumbList before).
B. each SBSTC route page (55): +3 FAQs (EN+BN) — distance, daily service, AC —
   with matching FAQPage JSON-LD entries.

Idempotent: guarded by <!-- sbstc-faq-v2 --> on pages.
"""
import json, os, re

BASE = os.path.join(os.path.dirname(__file__), "..")
BT = os.path.join(BASE, "bus-time-table")
MARK = "<!-- sbstc-faq-v2 -->"

ALIAS = {'midnapur': 'midnapur', 'midnapore': 'midnapur', 'arambag': 'arambagh',
         'goyespur': 'gayespur', 'garhbhowanipur': 'garbhawanipur'}


def norm(s):
    s = s.lower()
    s = re.sub(r'\s*\b(a\.c\.?|ac)\b\s*$', '', s)
    return re.sub(r'\s+via[-\s].*$', '', s).strip()


def title(s):
    return ' '.join(w.capitalize() if w not in ('to', 'via') else w for w in s.split())


def load_routes():
    d = json.load(open(os.path.join(BASE, 'data/sbstc-official-times.json'), encoding='utf-8'))
    out = {}
    for r in d['routes']:
        rt = norm(r['route'])
        if ' to ' not in rt:
            continue
        a, b = [x.strip() for x in rt.split(' to ', 1)]
        a = ALIAS.get(a, a); b = ALIAS.get(b, b)
        slug = f"{a.replace(' ','-')}-to-{b.replace(' ','-')}"
        out.setdefault(slug, []).append(r)
    return out


# ---------- route page FAQs ----------
def route_faqs(a, b, rec):
    km = rec['km']; fare = rec['fare_inr']
    ac = 'A.C' in rec['route'].upper() or 'AC' in rec['route'].upper()
    en = [
        (f"What is the distance from {a} to {b} by bus?",
         f"About <b>{km} km</b> — the official SBSTC route length."),
        (f"Does the SBSTC {a} to {b} bus run every day?",
         f"Yes — SBSTC runs this route daily. The official departure times are listed above; buses can run late, so verify before travel."),
        (f"Are there AC buses on the {a} to {b} route?",
         ("Yes — an AC service is listed on this route." if ac else
          "The SBSTC service on this route is non-AC. AC / Volvo services may run on the wider corridor — check the operator when booking.")),
    ]
    bn = [
        (f"{a} থেকে {b} বাসে কত কিলোমিটার?",
         f"প্রায় <b>{km} কিমি</b> — এসবিএসটিসি রুটের সরকারি দৈর্ঘ্য।"),
        (f"{a} থেকে {b} এসবিএসটিসি বাস কি প্রতিদিন চলে?",
         "হ্যাঁ — এসবিএসটিসি এই রুটে প্রতিদিন বাস চালায়। সরকারি ছাড়ার সময় উপরে দেওয়া আছে; বাস দেরিতে চলতে পারে, তাই যাত্রার আগে যাচাই করুন।"),
        (f"{a} থেকে {b} রুটে এসি বাস আছে?",
         ("হ্যাঁ — এই রুটে একটি এসি পরিষেবা আছে।" if ac else
          "এই রুটের এসবিএসটিসি বাস নন-এসি। আশপাশের রুটে এসি / ভলভো থাকতে পারে — বুকিংয়ের সময় অপারেটরকে জেনে নিন।")),
    ]
    return en, bn


# ---------- hub FAQs ----------
HUB_EN = [
    ("How many SBSTC routes and buses are there?",
     "The official WB Transport (SBSTC) route listing covers <b>68 major routes</b>, and BusJatri lists <b>537 SBSTC services across 163 routes</b>. SBSTC runs a fleet of about 660 buses across South Bengal."),
    ("What is the first and last SBSTC bus from Kolkata?",
     "SBSTC runs through the day — for example <b>Kolkata → Asansol from 5:30 AM</b> and <b>Kolkata → Digha from 6:30 AM</b>, with the last buses well into the evening and night. See each route page for the exact official times."),
    ("How do I book an SBSTC bus ticket online?",
     "Book on the official portal <b>online.sbstcbooking.co.in</b>, on the SBSTC mobile app, or through authorised partners such as redBus and AbhiBus. Carry the SMS/e-ticket as proof."),
    ("Are there AC or Volvo buses on SBSTC routes?",
     "Yes — several SBSTC routes run <b>AC / Volvo services</b>, e.g. the Kolkata–Asansol and Kolkata–Malda Banglashree Express. Look for the AC badge on the route cards above."),
    ("Where can I download the SBSTC timetable?",
     "The official West Bengal Transport Department publishes the SBSTC route timetable (PDF) at <b>transport.wb.gov.in</b>. Every route's departure times are also listed on this page and on each route page."),
    ("What is the SBSTC fare structure?",
     "SBSTC fares are distance-based — from about <b>₹47</b> for short hops up to <b>₹610</b> for the longest AC routes. Ordinary fares are roughly ₹0.65 per km beyond the first 6 km."),
]
HUB_BN = [
    ("এসবিএসটিসি-র কতগুলি রুট ও বাস আছে?",
     "অফিসিয়াল পশ্চিমবঙ্গ পরিবহণ (এসবিএসটিসি) রুট তালিকায় <b>৬৮টি প্রধান রুট</b> আছে, এবং বাসযাত্রী-তে <b>১৬৩টি রুটে ৫৩৭টি এসবিএসটিসি পরিষেবা</b> তালিকাভুক্ত। এসবিএসটিসি-র প্রায় ৬৬০টি বাস দক্ষিণবঙ্গে চলে।"),
    ("কলকাতা থেকে প্রথম ও শেষ এসবিএসটিসি বাস কখন?",
     "এসবিএসটিসি সারা দিন চলে — যেমন <b>কলকাতা → আসানসোল সকাল ৫:৩০</b> থেকে এবং <b>কলকাতা → দীঘা সকাল ৬:৩০</b> থেকে, শেষ বাস সন্ধ্যা ও রাত পর্যন্ত। সঠিক সরকারি সময় প্রতিটি রুট পেজে দেখুন।"),
    ("এসবিএসটিসি বাসের টিকিট অনলাইনে কীভাবে বুক করব?",
     "অফিসিয়াল পোর্টাল <b>online.sbstcbooking.co.in</b>, এসবিএসটিসি মোবাইল অ্যাপ, বা redBus / AbhiBus-এর মতো অনুমোদিত পার্টনার দিয়ে বুক করুন। SMS / ই-টিকিট সঙ্গে রাখুন।"),
    ("এসবিএসটিসি রুটে এসি বা ভলভো বাস আছে?",
     "হ্যাঁ — কয়েকটি এসবিএসটিসি রুটে <b>এসি / ভলভো পরিষেবা</b> চলে, যেমন কলকাতা–আসানসোল ও কলকাতা–মালদা বঙ্গশ্রী এক্সপ্রেস। উপরের রুট কার্ডে AC ব্যাজ দেখুন।"),
    ("এসবিএসটিসি টাইমটেবিল কোথায় ডাউনলোড করব?",
     "অফিসিয়াল পশ্চিমবঙ্গ পরিবহণ দফতর এসবিএসটিসি রুট টাইমটেবিল (PDF) <b>transport.wb.gov.in</b>-এ প্রকাশ করে। প্রতিটি রুটের ছাড়ার সময় এই পেজে ও রুট পেজেও দেওয়া আছে।"),
    ("এসবিএসটিসি-র ভাড়ার নিয়ম কী?",
     "ভাড়া দূরত্ব অনুযায়ী — ছোট রুটে প্রায় <b>₹৪৭</b> থেকে দীর্ঘ এসি রুটে <b>₹৬১০</b> পর্যন্ত। সাধারণ ভাড়া প্রথম ৬ কিমি-র পরে প্রায় ₹০.৬৫ প্রতি কিমি।"),
]


def faq_ld(name, text):
    return {"@type": "Question", "name": name,
            "acceptedAnswer": {"@type": "Answer", "text": re.sub(r'<[^>]+>', '', text)}}


def add_hub():
    p = os.path.join(BT, 'sbstc-buses.html')
    h = open(p, encoding='utf-8').read()
    if MARK in h:
        return
    en_html = ''.join(f'<details class="op-faq only-en"><summary>{q}</summary><div class="fa-body">{a}</div></details>'
                      for q, a in HUB_EN)
    bn_html = ''.join(f'<details class="op-faq only-bn"><summary>{q}</summary><div class="fa-body">{a}</div></details>'
                      for q, a in HUB_BN)
    # insert before the closing of the FAQ block (after the last op-faq details)
    idx = h.rfind('</details>')
    if idx == -1:
        print('hub: anchor not found'); return
    ins = idx + len('</details>')
    h = h[:ins] + MARK + en_html + bn_html + h[ins:]
    # FAQPage JSON-LD
    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [faq_ld(q, a) for q, a in HUB_EN + HUB_BN]}
    tag = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>'
    h = h.replace('</head>', tag + '\n</head>', 1)
    open(p, 'w', encoding='utf-8').write(h)
    print('hub: +6 EN +6 BN FAQs, FAQPage schema added')


def add_routes():
    routes = load_routes()
    done = 0
    for f in sorted(os.listdir(BT)):
        if not f.endswith('.html'):
            continue
        slug = f[:-5]
        recs = routes.get(slug)
        if not recs:
            continue
        p = os.path.join(BT, f)
        h = open(p, encoding='utf-8').read()
        if '<!-- sbstc-official-v1 -->' not in h or MARK in h:
            continue
        r = recs[0]
        rt = norm(r['route'])
        a, b = [title(x.strip()) for x in rt.split(' to ', 1)]
        en, bn = route_faqs(a, b, r)
        en_html = ''.join(f'<details class="faq only-en"><summary>{q}</summary><div class="fa-body">{x}</div></details>' for q, x in en)
        bn_html = ''.join(f'<details class="faq only-bn"><summary>{q}</summary><div class="fa-body">{x}</div></details>' for q, x in bn)
        m = re.search(r'(<section class="seo-section faq-v2">.*?)(</section>)', h, re.S)
        if not m:
            continue
        h = h[:m.end(1)] + MARK + en_html + bn_html + h[m.end(1):]
        # JSON-LD
        ml = re.search(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
        if ml:
            try:
                ld = json.loads(ml.group(1))
                if ld.get('@type') == 'FAQPage':
                    ld['mainEntity'] += [faq_ld(q, x) for q, x in en + bn]
                    h = h[:ml.start(1)] + json.dumps(ld, ensure_ascii=False) + h[ml.end(1):]
            except Exception as e:
                print(f, 'ld err', e)
        open(p, 'w', encoding='utf-8').write(h)
        done += 1
    print(f'route pages: +3 EN +3 BN FAQs on {done} pages')


if __name__ == "__main__":
    add_hub()
    add_routes()
