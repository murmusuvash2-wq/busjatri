#!/usr/bin/env python3
"""Add 'WBTC online bookable services (AC Volvo)' sections to the
Kolkata <-> Siliguri route pages.

Data source: wbtconline.in official booking search
(Kolkata Esplanade -> Siliguri and Siliguri -> Kolkata Esplanade,
travel date 01-10-2026), complete cards pasted so pairings are unambiguous.
Times are the departure from the searched boarding stoppage (Esplanade /
Siliguri). Via-route taken from the official wbtconline route list.
Idempotent: skips a page if the <!-- siliguri-svc-v1 --> marker exists.
"""
import os

BASE = os.path.join(os.path.dirname(__file__), "..")

SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
       '<path d="M12 7v5l3 2"/></svg>')

MARKER = "<!-- siliguri-svc-v1 -->"

# (time, code, route, via, fare, seats)
FROM_KOLKATA = [
    ("5:50 PM", "ACT17", "Kolkata &ndash; Raiganj &ndash; Siliguri (AC Volvo)",
     "Malda &middot; Raiganj &middot; Dalkhola &middot; Kishanganj &middot; Islampur"),
    ("6:30 PM", "ACT17", "Kolkata &ndash; Raiganj &ndash; Siliguri (AC Volvo)",
     "Malda &middot; Raiganj &middot; Dalkhola &middot; Kishanganj &middot; Islampur"),
    ("7:00 PM", "ACT19", "Baruipur &ndash; Kolkata &ndash; Raiganj &ndash; Siliguri (AC Volvo)",
     "Garia &middot; Esplanade &middot; Airport &middot; Barasat &middot; Raiganj"),
]

FROM_SILIGURI = [
    ("6:30 PM", "ACT17", "Kolkata &ndash; Raiganj &ndash; Siliguri (AC Volvo)",
     "Islampur &middot; Kishanganj &middot; Dalkhola &middot; Raiganj &middot; Malda"),
    ("7:00 PM", "ACT17", "Kolkata &ndash; Raiganj &ndash; Siliguri (AC Volvo)",
     "Islampur &middot; Kishanganj &middot; Dalkhola &middot; Raiganj &middot; Malda"),
    ("7:30 PM", "ACT19", "Baruipur &ndash; Kolkata &ndash; Raiganj &ndash; Siliguri (AC Volvo)",
     "Raiganj &middot; Barasat &middot; Airport &middot; Esplanade &middot; Garia"),
]

AC_BADGE = ('<span class="badge badge-ac"><span class="label-en">AC</span>'
            '<span class="label-bn">এসি</span></span>')


def row(t, code, route, via, fare="1355", seats="42"):
    return f'''<div class="bus-row">
    <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{t}</span></div></div>
    <div class="bmid">
      <div class="op">{code} <span style="color:var(--amber-ink,#6b4610);font-weight:600">&middot; {route}</span></div>
      <div class="mrow">🛣 via {via} &middot; 💺 {seats} <span class="label-en">seats</span><span class="label-bn">আসন</span></div>
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
    "These WBTC AC Volvo services on the Kolkata&ndash;Siliguri corridor can be booked online at "
    "wbtconline.in (official WBTC booking). Times below are the departure from Esplanade. "
    "The ACT19 service starts from Baruipur and picks up at Garia, Jadavpur, Esplanade and Barasat.",
    "কলকাতা&ndash;শিলিগুড়ি রুটের এই ডাব্লুবিটিসি এসি ভলভো পরিষেবাগুলি wbtconline.in-এ অনলাইনে বুক করা যায় (সরকারি বুকিং)। "
    "সময়গুলি এসপ্ল্যানেড থেকে ছাড়ার সময়। ACT19 পরিষেবাটি বারুইপুর থেকে ছাড়ে — গড়িয়া, যাদবপুর, এসপ্ল্যানেড ও বারাসাত থেকেও ওঠা যায়।")

SILIGURI_SEC = section(
    FROM_SILIGURI, "Siliguri", "শিলিগুড়ি",
    "These WBTC AC Volvo services on the Siliguri&ndash;Kolkata corridor can be booked online at "
    "wbtconline.in (official WBTC booking). Times below are the departure from Siliguri, "
    "headed for Esplanade (Kolkata).",
    "শিলিগুড়ি&ndash;কলকাতা রুটের এই ডাব্লুবিটিসি এসি ভলভো পরিষেবাগুলি wbtconline.in-এ অনলাইনে বুক করা যায় (সরকারি বুকিং)। "
    "সময়গুলি শিলিগুড়ি থেকে ছাড়ার সময় — গন্তব্য এসপ্ল্যানেড (কলকাতা)।")


def patch(page, sec_html):
    path = os.path.join(BASE, "bus-time-table", page)
    with open(path, encoding="utf-8") as fh:
        h = fh.read()
    if MARKER in h:
        print(page, "already patched, skipping")
        return
    # insert before the 2nd seo-section (Via Stoppages), i.e. right after Today's Departures
    first = h.find('<section class="seo-section">')
    second = h.find('<section class="seo-section">', first + 1)
    if first == -1 or second == -1:
        raise SystemExit("anchors not found in " + page)
    h = h[:second] + sec_html + h[second:]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(h)
    print("patched", page)


def main():
    patch("kolkata-to-siliguri.html", KOLKATA_SEC)
    patch("siliguri-to-kolkata.html", SILIGURI_SEC)


if __name__ == "__main__":
    main()
