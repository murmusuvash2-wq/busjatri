#!/usr/bin/env python3
"""Add 'WBTC online bookable services (AC Volvo)' sections to the
Kolkata <-> Malda route pages.

Data source: wbtconline.in official booking search
(Kolkata Esplanade -> Malda and Malda -> Kolkata Esplanade,
travel date 01-10-2026), complete cards pasted so pairings are unambiguous.
Times are the departure from the searched boarding stoppage (Esplanade /
Malda). BE7 continues to Balurghat after Malda; BE7M runs via Krishnanagar.
Idempotent: skips a page if the <!-- malda-svc-v1 --> marker exists.
"""
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
MARKER = "<!-- malda-svc-v1 -->"

SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
       '<path d="M12 7v5l3 2"/></svg>')

AC_BADGE = ('<span class="badge badge-ac"><span class="label-en">AC</span>'
            '<span class="label-bn">এসি</span></span>')

# (time, code+name, route, via, fare, seats)
FROM_KOLKATA = [
    ("7:00 PM", "BE7 Banglashree Express", "Kolkata &ndash; Malda &ndash; Balurghat (AC Volvo)",
     "continues to Balurghat after Malda", "610", "43"),
    ("9:00 PM", "BE7M Banglashree Express", "Kolkata &ndash; Krishnanagar &ndash; Malda (AC Volvo)",
     "via Krishnanagar", "610", "42"),
]

FROM_MALDA = [
    ("9:00 PM", "BE7 Banglashree Express", "Kolkata &ndash; Malda &ndash; Balurghat (AC Volvo)",
     "Malda leg of the Balurghat service, ends at Esplanade", "610", "43"),
    ("10:00 PM", "BE7M Banglashree Express", "Kolkata &ndash; Krishnanagar &ndash; Malda (AC Volvo)",
     "via Krishnanagar, ends at Esplanade", "610", "42"),
]


def row(t, code, route, via, fare, seats):
    return f'''<div class="bus-row">
    <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{t}</span></div></div>
    <div class="bmid">
      <div class="op">{code} <span style="color:var(--amber-ink,#6b4610);font-weight:600">&middot; {route}</span></div>
      <div class="mrow">🛣 {via} &middot; 💺 {seats} <span class="label-en">seats</span><span class="label-bn">আসন</span></div>
    </div>
    <div class="bright"><span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span>{AC_BADGE}<span class="badge">₹{fare}</span></div>
  </div>'''


def section(services, from_en, from_bn, note_en, note_bn):
    rows = "\n  ".join(row(*s) for s in services)
    return f'''{MARKER}
<section class="seo-section">
  <h3 class="section-title"><span class="label-en">WBTC Online Bookable Services &middot; from {from_en}</span><span class="label-bn">ডাব্লুবিটিসি অনলাইন বুকিং সেবা &middot; {from_bn} থেকে</span></h3>
  <p class="alt-note" style="margin-bottom:10px"><span class="label-en">{note_en}</span><span class="label-bn">{note_bn}</span></p>
  {rows}
</section>
'''


KOLKATA_SEC = section(
    FROM_KOLKATA, "Esplanade", "এসপ্ল্যানেড",
    "These WBTC AC Volvo services on the Kolkata&ndash;Malda corridor can be booked online at "
    "wbtconline.in (official WBTC booking). Times below are the departure from Esplanade. "
    "The BE7 Banglashree Express continues to Balurghat after Malda; BE7M runs via Krishnanagar.",
    "কলকাতা&ndash;মালদা রুটের এই ডাব্লুবিটিসি এসি ভলভো পরিষেবাগুলি wbtconline.in-এ অনলাইনে বুক করা যায় (সরকারি বুকিং)। "
    "সময়গুলি এসপ্ল্যানেড থেকে ছাড়ার সময়। BE7 বঙ্গশ্রী এক্সপ্রেস মালদার পরে বালুরঘাট পর্যন্ত যায়; BE7M কৃষ্ণনগর হয়ে চলে।")

MALDA_SEC = section(
    FROM_MALDA, "Malda", "মালদা",
    "These WBTC AC Volvo services on the Malda&ndash;Kolkata corridor can be booked online at "
    "wbtconline.in (official WBTC booking). Times below are the departure from Malda, "
    "headed for Esplanade (Kolkata).",
    "মালদা&ndash;কলকাতা রুটের এই ডাব্লুবিটিসি এসি ভলভো পরিষেবাগুলি wbtconline.in-এ অনলাইনে বুক করা যায় (সরকারি বুকিং)। "
    "সময়গুলি মালদা থেকে ছাড়ার সময় — গন্তব্য এসপ্ল্যানেড (কলকাতা)।")


def patch(page, sec_html):
    path = os.path.join(BASE, "bus-time-table", page)
    with open(path, encoding="utf-8") as fh:
        h = fh.read()
    if MARKER in h:
        print(page, "already patched, skipping")
        return
    vi = h.find("Via Stoppages")
    if vi == -1:
        raise SystemExit("Via Stoppages anchor not found in " + page)
    ins = h.rfind("<section", 0, vi)
    h = h[:ins] + sec_html + h[ins:]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(h)
    print("patched", page)


def main():
    patch("kolkata-to-malda.html", KOLKATA_SEC)
    patch("malda-to-esplanade.html", MALDA_SEC)


if __name__ == "__main__":
    main()
