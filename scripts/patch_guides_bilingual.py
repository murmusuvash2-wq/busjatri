#!/usr/bin/env python3
"""
Travel guides bilingual (2026-09-23) — full Bengali support for stand-page
travel guides.

Before: guide intro was bilingual but note, card desc/why/when/bus text were
English-only; the Bengali place name under the card title showed in BOTH
languages (Bengali leak in EN mode).

After: every guide element renders via the L(en, bn) span pair —
EN selected = English only, Bangla selected = Bengali. Buses keep their
real names and clock times in both languages (English fallback per site rule).

Adds: note_bn, and per-card desc_bn/why_bn/when_bn/bus_bn/stay_extra_bn/
stay_text_bn. Content falls back to English if a _bn field is missing
(the daily guide cron will fill these for new guides).

Idempotent, backslash-free. Run from repo root.
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)

OLD_FUNC = '''def _guide_section(slug, disp):
    guide = GUIDES.get(slug)
    if not guide:
        return ""
    cards = []
    for c in guide["cards"]:
        if c.get("stay"):
            stay_row = '🏨 <a href="{u}" target="_blank" rel="nofollow">{t}</a>'.format(
                u=_maps(c["stay"]),
                t=L("Stay options on Maps", "ম্যাপে থাকার জায়গা"))
        else:
            stay_row = "🏨 " + c["stay_extra"].replace("{LINK}", '<a href="{u}" target="_blank" rel="nofollow">{t}</a>'.format(u=_maps(c["stay_link"]), t=c["stay_text"]))
        cards.append("""<div class="tg-card">
  <div class="tg-ico">{ico}</div>
  <div class="tg-name">{name} <span class="tg-bn">{bn}</span></div>
  <div class="tg-desc">{desc}</div>
  <div class="tg-rows">
    <div class="tg-row">{bus}</div>
    <div class="tg-row">🗺️ <a href="{maps}" target="_blank" rel="nofollow">{open_txt}</a></div>
    <div class="tg-row">⭐ {why_txt}: {why}</div>
    <div class="tg-row">🕐 {best_txt}: {when}</div>
    <div class="tg-row">{stay}</div>
  </div>
</div>""".format(ico=c["icon"], name=g.esc(c["name"]), bn=g.esc(c["bn"]),
                 desc=g.esc(c["desc"]), bus=c["bus"],
                 maps=_maps(c["maps"]),
                 open_txt=L("Open in Google Maps", "গুগল ম্যাপে খুলুন"),
                 why_txt=L("Why go", "কেন যাবেন"),
                 best_txt=L("Best time", "সেরা সময়"),
                 why=g.esc(c["why"]), when=g.esc(c["when"]),
                 stay=stay_row))
    intro_en, intro_bn = guide["intro"]
    return """<div class="sec"><h3>{tg} <span class="cnt">{intro}</span></h3></div>
<div class="tg-grid">{cards}</div>
<div class="tg-note">{note}</div>""".format(
        tg=L("Travel Guide", "ভ্রমণ গাইড"),
        intro=L(g.esc(intro_en), g.esc(intro_bn)),
        cards="".join(cards), note=guide["note"])'''

NEW_FUNC = '''def _guide_section(slug, disp):
    guide = GUIDES.get(slug)
    if not guide:
        return ""
    cards = []
    for c in guide["cards"]:
        if c.get("stay"):
            stay_row = '🏨 <a href="{u}" target="_blank" rel="nofollow">{t}</a>'.format(
                u=_maps(c["stay"]),
                t=L("Stay options on Maps", "ম্যাপে থাকার জায়গা"))
        else:
            stay_row = "🏨 " + L(c["stay_extra"], c.get("stay_extra_bn", c["stay_extra"])).replace("{LINK}", '<a href="{u}" target="_blank" rel="nofollow">{t}</a>'.format(u=_maps(c["stay_link"]), t=L(c["stay_text"], c.get("stay_text_bn", c["stay_text"]))))
        cards.append("""<div class="tg-card">
  <div class="tg-ico">{ico}</div>
  <div class="tg-name">{name}</div>
  <div class="tg-desc">{desc}</div>
  <div class="tg-rows">
    <div class="tg-row">{bus}</div>
    <div class="tg-row">🗺️ <a href="{maps}" target="_blank" rel="nofollow">{open_txt}</a></div>
    <div class="tg-row">⭐ {why_txt}: {why}</div>
    <div class="tg-row">🕐 {best_txt}: {when}</div>
    <div class="tg-row">{stay}</div>
  </div>
</div>""".format(ico=c["icon"], name=L(g.esc(c["name"]), g.esc(c["bn"])),
                 desc=L(g.esc(c["desc"]), g.esc(c.get("desc_bn", c["desc"]))),
                 bus=L(c["bus"], c.get("bus_bn", c["bus"])),
                 maps=_maps(c["maps"]),
                 open_txt=L("Open in Google Maps", "গুগল ম্যাপে খুলুন"),
                 why_txt=L("Why go", "কেন যাবেন"),
                 best_txt=L("Best time", "সেরা সময়"),
                 why=L(g.esc(c["why"]), g.esc(c.get("why_bn", c["why"]))),
                 when=L(g.esc(c["when"]), g.esc(c.get("when_bn", c["when"]))),
                 stay=stay_row))
    intro_en, intro_bn = guide["intro"]
    return """<div class="sec"><h3>{tg} <span class="cnt">{intro}</span></h3></div>
<div class="tg-grid">{cards}</div>
<div class="tg-note">{note}</div>""".format(
        tg=L("Travel Guide", "ভ্রমণ গাইড"),
        intro=L(g.esc(intro_en), g.esc(intro_bn)),
        cards="".join(cards), note=L(guide["note"], guide.get("note_bn", guide["note"])))'''

GUIDES_BN = '''
GUIDES_BN = {
    "bankura": {
        "note": "🚉 <b>রেল:</b> বাঁকুড়া জংশন (হাওড়া–আদ্রা লাইন) · 🛣️ <b>রাস্তা:</b> দুর্গাপুর/আসানসল এনএইচ-১৪, বিষ্ণুপুর–পুরুলিয়া এসএইচ।",
        "cards": [
            {"desc_bn": "মল্ল রাজাদের পোড়ামাটির মন্দিরের শহর — রাসমঞ্চ, জোরবাংলা আরও অনেক মন্দির",
             "bus_bn": "🚌 <b>MUNMUN</b> 8:00 AM · <b>MAA MANASA</b> 9:40 AM — এই স্ট্যান্ড থেকে সরাসরি",
             "why_bn": "পোড়ামাটির মন্দির, বালুচরি শাড়ি, মন্দির-স্থাপত্য ঘোরা",
             "when_bn": "অক্টোবর–মার্চ, সকালে রওনা দিন"},
            {"desc_bn": "কংসাবতী বাঁধ — বাংলার বৃহত্তম জলাধারগুলোর একটি, সূর্যাস্তে নৌকা ভ্রমণ",
             "bus_bn": "🚌 <b>SOUMEN</b> (অম্বিকা নগর রুট) — মুকুটমণিপুরে পৌঁছায় 2:15 PM, ফেরে 3:50 PM",
             "why_bn": "বাঁধের ভিউ পয়েন্ট, নৌকা ভ্রমণ, নদীর সঙ্গম (কংসাবতী + কুমারী)",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, বিকেলে সূর্যাস্তের জন্য"},
            {"desc_bn": "পাহাড়, প্রাকৃতিক ঝরনা, প্রাচীন শিলালিপি ও রক ক্লাইম্বিং",
             "bus_bn": "🚌 <b>BABA LOKENATH</b> (আসানসল রুট) — শুশুনিয়া হিল স্টপে নেমে যান",
             "why_bn": "পাহাড় ট্রেক, ঝরনার জল, রক ক্লাইম্বিং, সবুজ জঙ্গল",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, সকাল সকাল যান",
             "stay_extra_bn": "বাঁকুড়া থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
        ],
    },
    "kolkata": {
        "note": "🚉 <b>রেল:</b> হাওড়া ও শিয়ালদহ — দেশের সবচেয়ে বড় রেল হাব · 🛣️ <b>রাস্তা:</b> এনএইচ-১৬ (খড়্গপুর) আর এনএইচ-১৯ (ধানবাদ) এখান থেকেই শুরু।",
        "cards": [
            {"desc_bn": "হুগলির ধারে ঐতিহাসিক কালীমন্দির — রামকৃষ্ণ পরমহংসের আসন",
             "bus_bn": "🚌 রুট <b>43</b> দক্ষিণেশ্বর যায় — 23টি তালিকাভুক্ত বাস এই এলাকা ছোঁয়",
             "why_bn": "নদীর ধারের মন্দির প্রাঙ্গণ, 12টি শিবমন্দির, ভোরের আরতি",
             "when_bn": "সারা বছর; আরতির জন্য ভোরে যান",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "কাছেই থাকুন"},
            {"desc_bn": "নদীর ওপারে বালিতে রামকৃষ্ণ মিশনের প্রধান কার্যালয়",
             "bus_bn": "🚌 বালির উদ্দেশে অনেক তালিকাভুক্ত বাস (হাওড়া দিক) — বালি ঘাট থেকে বেলুড় মঠ অল্প দূরে",
             "why_bn": "শান্ত মার্বেল মন্দির, স্বামী বিবেকানন্দের সমাধি, সন্ধ্যার আরতি",
             "when_bn": "সারা বছর; সূর্যাস্তের আরতির জন্য বিকেলে",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "দুশো বছরের পুরোনো এ জে সি বসু উদ্যান — বিশাল বটগাছসহ",
             "bus_bn": "🚌 রুট <b>55A</b> শিবপুর পর্যন্ত (হাওড়া দিক) — সেখান থেকে উদ্যান অল্প দূরে",
             "why_bn": "গ্রেট ব্যানিয়ান, পাম হাউস, নদীর ধারে হাঁটা",
             "when_bn": "অক্টোবর–মার্চ, সকালে",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "কলকাতার সবচেয়ে বড় শহর-উদ্যান — হ্রদ, থিম গার্ডেন, আইস স্কেটিং",
             "bus_bn": "🚌 নিউ টাউনে 27টি তালিকাভুক্ত বাস — রুট <b>EB-3</b> (Ecospace), <b>AS-3</b> (Newtown), <b>VS-10</b> (Amity)",
             "why_bn": "480 একরের পার্ক, বোটিং, প্রজাপতি উদ্যান, ফুড কোর্ট",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, বিকেলের দিকে",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "নিউ টাউনে থাকুন"},
        ],
    },
    "digha": {
        "note": "🚉 <b>রেল:</b> হাওড়া থেকে সরাসরি ট্রেন (সময় দেখে নিন) · 🛣️ <b>রাস্তা:</b> কোলাঘাট–নন্দকুমার–কাঁথি রুট, কলকাতা থেকে প্রায় 4 ঘণ্টা। ফেরা: কলকাতায় 18টি বাস তালিকাভুক্ত, প্রথম 4:30 AM, শেষ 10:00 PM।",
        "cards": [
            {"desc_bn": "মূল সমুদ্র সৈকত — সমতল, হাঁটার মতো, সূর্যোদয়ের জায়গা",
             "bus_bn": "🚶 স্ট্যান্ড থেকে অল্প হাঁটা বা সাইকেল-ভ্যানে যাওয়া যায়",
             "why_bn": "সমুদ্রের হাওয়া, মেরিন অ্যাকোয়ারিয়াম ও সায়েন্স সেন্টার, স্ট্রিট ফুড",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি; সূর্যোদয়ের জন্য ভোরে"},
            {"desc_bn": "পুরোনো শিবমন্দির, দীঘা থেকে 4 কিমি",
             "bus_bn": "🚌 স্ট্যান্ড থেকে লোকাল ভ্যান-বাস যায় — তালিকায় নেই, স্ট্যান্ডে জেনে নিন",
             "why_bn": "শত বছরের পুরোনো মন্দির, সকালের আরতি, ছোট সাপ্তাহিক হাট",
             "when_bn": "সারা বছর; সকালের দিকে ভালো",
             "stay_extra_bn": "দীঘা থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "দীঘায় থাকুন"},
            {"desc_bn": "নদী-মোহনার সৈকত, লাল কাঁকড়া — মৌসুমে অলিভ রিডলি কচ্ছপ ডিম পাড়তে আসে",
             "bus_bn": "🚌 স্ট্যান্ড থেকে লোকাল যান (প্রায় 10 কিমি) — স্ট্যান্ডে জেনে নিন",
             "why_bn": "ব্যাকওয়াটার, নিরিবিলি সৈকত, নদীর মোহনায় নৌকা ভ্রমণ",
             "when_bn": "অক্টোবর–মার্চ"},
            {"desc_bn": "লম্বা গাড়ি-চলা সৈকত আর লাল কাঁকড়া — নিরিবিলি দীঘা",
             "bus_bn": "🚌 কলকাতাগামী বাস কাঁথি হয়ে যায় (যেমন <b>SOHANA PARIBAHAN</b>, কাঁথি স্টপ 7:20 AM) — কাঁথি থেকে লোকাল যান ধরুন",
             "why_bn": "সৈকতে গাড়ি চালানো, ঝাউবন, ওয়াটার স্পোর্টস",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি"},
        ],
    },
    "purulia": {
        "note": "🚉 <b>রেল:</b> পুরুলিয়া জংশন (হাওড়া–পুরুলিয়া লাইন) · 🛣️ <b>রাস্তা:</b> রাঁচি এনএইচ-১৮, বাঁকুড়া–অযোধ্যা এসএইচ।",
        "cards": [
            {"desc_bn": "পুরুলিয়ার পাহাড় — ঝরনা, জঙ্গল আর আদিবাসী গ্রাম",
             "bus_bn": "🚌 <b>GOUTAM</b> 10:30 AM · <b>KALYAN</b> 2:05 PM — সরাসরি অযোধ্যা পাহাড়; <b>HILLTOP SUPER</b> 11:05 AM বাঘমুণ্ডি হয়ে",
             "why_bn": "আপার ও লোয়ার ঝরনা, পাহাড়ি ভিউ পয়েন্ট, শান্ত জঙ্গলের রাস্তা",
             "when_bn": "সেপ্টেম্বর–ফেব্রুয়ারি; ঝরনার জন্য বর্ষাকাল"},
            {"desc_bn": "পাথুরে পাহাড় আর রোপ-ওয়ে, পুরুলিয়া শহর থেকে 5 কিমি",
             "bus_bn": "🚶 স্ট্যান্ড থেকে অল্প লোকাল রাইড (প্রায় 5 কিমি) — জেনে নিন",
             "why_bn": "ছোটনাগপুরের পাথর, রোপ-ওয়ে, সূর্যাস্ত পয়েন্ট, পিকনিক স্পট",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, ভোরে বা সূর্যাস্তে",
             "stay_extra_bn": "পুরুলিয়া থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
        ],
    },
}


def _merge_guide_bn():
    """Fold GUIDES_BN Bengali fields into the GUIDES dict as *_bn keys."""
    for slug, bn in GUIDES_BN.items():
        gd = GUIDES.get(slug)
        if not gd:
            continue
        if "note" in bn:
            gd["note_bn"] = bn["note"]
        for c, cbn in zip(gd["cards"], bn.get("cards", [])):
            for k, v in cbn.items():
                c[k if k.endswith("_bn") else k + "_bn"] = v


_merge_guide_bn()
'''


def main():
    p = os.path.join(ROOT, "scripts", "gen_stand_v2.py")
    s = open(p, encoding="utf-8").read()
    if "GUIDES_BN" in s:
        print("gen_stand_v2.py: already bilingual")
        return

    if OLD_FUNC not in s:
        raise SystemExit("old _guide_section not found - review gen_stand_v2.py")
    s = s.replace(OLD_FUNC, NEW_FUNC, 1)

    anchor = "# ------------------------------------------------------------" + NL + "# page template — SAME design language as the homepage"
    if anchor not in s:
        raise SystemExit("page template anchor not found")
    s = s.replace(anchor, GUIDES_BN.rstrip() + NL + NL + NL + anchor, 1)

    open(p, "w", encoding="utf-8").write(s)
    import ast
    ast.parse(s)
    print("gen_stand_v2.py: guides now fully bilingual (EN + BN)")


if __name__ == "__main__":
    main()
