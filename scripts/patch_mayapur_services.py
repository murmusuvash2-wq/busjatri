#!/usr/bin/env python3
"""Add 'WBTC online bookable services' sections to the Kolkata <-> Mayapur
route pages.

Data source: wbtconline.in official booking search
(Kolkata Esplanade -> Mayapur and Mayapur -> Kolkata Esplanade,
travel date 01-10-2026), complete cards pasted so pairings are unambiguous.
Times are the departure from the searched boarding stoppage (Esplanade /
Mayapur). BE19 is the AC service via Krishnanagar; E38 is the non-AC direct
service.
Idempotent: skips a page if the <!-- mayapur-svc-v1 --> marker exists.
"""
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
MARKER = "<!-- mayapur-svc-v1 -->"

SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
       '<path d="M12 7v5l3 2"/></svg>')

AC_BADGE = ('<span class="badge badge-ac"><span class="label-en">AC</span>'
            '<span class="label-bn">এসি</span></span>')
NONAC_BADGE = ('<span class="badge badge-nonac"><span class="label-en">Non-AC</span>'
               '<span class="label-bn">নন-এসি</span></span>')


def row(t, code, route, ac, via, fare, seats):
    badge = AC_BADGE if ac else NONAC_BADGE
    return f'''<div class="bus-row">
    <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{t}</span></div></div>
    <div class="bmid">
      <div class="op">{code} <span style="color:var(--amber-ink,#6b4610);font-weight:600">&middot; {route}</span></div>
      <div class="mrow">🛣 {via} &middot; 💺 {seats} <span class="label-en">seats</span><span class="label-bn">আসন</span></div>
    </div>
    <div class="bright"><span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span>{badge}<span class="badge">₹{fare}</span></div>
  </div>'''


# (time, code, route, ac, via, fare, seats)
FROM_KOLKATA = [
    ("6:15 AM",  "BE19", "Kolkata &ndash; Krishnanagar &ndash; Mayapur (AC)", True,
     "via Krishnanagar", "255", "42"),
    ("6:15 AM",  "E38",  "Kolkata &ndash; Mayapur", False,
     "direct", "108", "54"),
    ("7:00 AM",  "BE19", "Kolkata &ndash; Krishnanagar &ndash; Mayapur (AC)", True,
     "via Krishnanagar", "255", "42"),
    ("7:30 AM",  "BE19", "Kolkata &ndash; Krishnanagar &ndash; Mayapur (AC)", True,
     "via Krishnanagar", "255", "42"),
    ("7:35 AM",  "E38",  "Kolkata &ndash; Mayapur", False,
     "direct", "108", "54"),
    ("3:30 PM",  "BE19", "Kolkata &ndash; Krishnanagar &ndash; Mayapur (AC)", True,
     "via Krishnanagar", "255", "42"),
]

FROM_MAYAPUR = [
    ("3:00 PM",  "BE19", "Kolkata &ndash; Krishnanagar &ndash; Mayapur (AC)", True,
     "via Krishnanagar, ends at Esplanade", "255", "42"),
    ("3:30 PM",  "BE19", "Kolkata &ndash; Krishnanagar &ndash; Mayapur (AC)", True,
     "via Krishnanagar, ends at Esplanade", "255", "42"),
    ("3:30 PM",  "E38",  "Kolkata &ndash; Mayapur", False,
     "direct, ends at Esplanade", "108", "54"),
    ("4:00 PM",  "BE19", "Kolkata &ndash; Krishnanagar &ndash; Mayapur (AC)", True,
     "via Krishnanagar, ends at Esplanade", "255", "42"),
    ("4:15 PM",  "E38",  "Kolkata &ndash; Mayapur", False,
     "direct, ends at Esplanade", "108", "54"),
]


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
    "These WBTC Mayapur services can be booked online at wbtconline.in (official WBTC booking). "
    "Times below are the departure from Esplanade. BE19 is the AC service via Krishnanagar (₹255); "
    "E38 is the direct non-AC service (₹108).",
    "মায়াপুরগামী এই ডাব্লুবিটিসি পরিষেবাগুলি wbtconline.in-এ অনলাইনে বুক করা যায় (সরকারি বুকিং)। "
    "সময়গুলি এসপ্ল্যানেড থেকে ছাড়ার সময়। BE19 কৃষ্ণনগর হয়ে এসি পরিষেবা (২৫৫ টাকা); E38 সরাসরি নন-এসি পরিষেবা (১০৮ টাকা)।")

MAYAPUR_SEC = section(
    FROM_MAYAPUR, "Mayapur", "মায়াপুর",
    "These WBTC Kolkata-bound services can be booked online at wbtconline.in (official WBTC booking). "
    "Times below are the departure from Mayapur, headed for Esplanade (Kolkata).",
    "কলকাতাগামী এই ডাব্লুবিটিসি পরিষেবাগুলি wbtconline.in-এ অনলাইনে বুক করা যায় (সরকারি বুকিং)। "
    "সময়গুলি মায়াপুর থেকে ছাড়ার সময় — গন্তব্য এসপ্ল্যানেড (কলকাতা)।")


def patch_before(page, sec_html, anchor_text):
    path = os.path.join(BASE, "bus-time-table", page)
    with open(path, encoding="utf-8") as fh:
        h = fh.read()
    if MARKER in h:
        print(page, "already patched, skipping")
        return
    a = h.find(anchor_text)
    if a == -1:
        raise SystemExit("anchor not found in " + page)
    ins = h.rfind("<section", 0, a)
    h = h[:ins] + sec_html + h[ins:]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(h)
    print("patched", page)


def main():
    # forward page: insert before the 'About this route' section
    patch_before("kolkata-to-mayapur.html", KOLKATA_SEC, "About this route")
    # return page: insert before the 'Via Stoppages' section
    patch_before("mayapur-to-esplanade.html", MAYAPUR_SEC, "Via Stoppages")


if __name__ == "__main__":
    main()
