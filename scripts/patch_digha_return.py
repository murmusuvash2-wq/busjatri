#!/usr/bin/env python3
"""Add 'WBTC online bookable services (Digha -> Kolkata)' section to
bus-time-table/digha-to-kolkata.html.

Data source: wbtconline.in official booking search (Digha -> Kolkata),
complete cards pasted (route + seats + fare/time together), so pairings are
unambiguous. Times are DEPARTURE FROM DIGHA. Last entry (E19A 11:30 PM)
matches the official corridor last bus 23:30.
Idempotent: skips if the <!-- digha-ret-v1 --> marker is already present.
"""
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
PAGE = os.path.join(BASE, "bus-time-table", "digha-to-kolkata.html")
MARKER = "<!-- digha-ret-v1 -->"

SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
       '<path d="M12 7v5l3 2"/></svg>')

# (time, code, route, ac, fare, seats)
SERVICES = [
    ("1:10 PM",  "ACT5",  "Barasat &ndash; Digha via Esplanade",                     True,  "370", "42"),
    ("1:45 PM",  "ACT6A", "Shyambazar &ndash; Digha via Esplanade",                   True,  "370", "42"),
    ("1:50 PM",  "E40/1", "Kolkata &ndash; Digha",                                     False, "145", "54"),
    ("2:15 PM",  "E17K",  "Barasat &ndash; Digha via Airport, Karunamoyee, Esplanade", False, "145", "47"),
    ("2:30 PM",  "E45",   "Joka &ndash; Tollygunge &ndash; Digha",                     False, "145", "54"),
    ("2:46 PM",  "ACT6A", "Shyambazar &ndash; Digha via Esplanade",                    True,  "370", "42"),
    ("3:00 PM",  "E40",   "Khidderpur &ndash; Digha",                                   False, "145", "54"),
    ("3:30 PM",  "E45",   "Joka &ndash; Tollygunge &ndash; Digha",                     False, "145", "54"),
    ("3:50 PM",  "E45A",  "Tollygunge &ndash; Digha",                                   False, "145", "54"),
    ("4:30 PM",  "E45A",  "Tollygunge &ndash; Digha",                                   False, "145", "54"),
    ("10:20 PM", "E17",   "Barasat &ndash; Digha via Esplanade",                       False, "145", "54"),
    ("11:30 PM", "E19A",  "Habra &ndash; Digha via Esplanade",                         False, "145", "54"),
]


def row(t, code, route, ac, fare, seats):
    ac_badge = ('<span class="badge badge-ac"><span class="label-en">AC</span>'
                '<span class="label-bn">এসি</span></span>') if ac else (
                '<span class="badge badge-nonac"><span class="label-en">Non-AC</span>'
                '<span class="label-bn">নন-এসি</span></span>')
    return f'''<div class="bus-row">
    <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{t}</span></div></div>
    <div class="bmid">
      <div class="op">{code} <span style="color:var(--amber-ink,#6b4610);font-weight:600">&middot; {route}</span></div>
      <div class="mrow">💺 {seats} <span class="label-en">seats &middot; departs Digha</span><span class="label-bn">আসন &middot; দীঘা থেকে ছাড়ে</span></div>
    </div>
    <div class="bright"><span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span>{ac_badge}<span class="badge">₹{fare}</span></div>
  </div>'''


def main():
    with open(PAGE, encoding="utf-8") as fh:
        h = fh.read()
    if MARKER in h:
        print("already patched, skipping")
        return
    rows = "\n  ".join(row(*s) for s in SERVICES)
    section = f'''{MARKER}
<section class="seo-section">
  <h3 class="section-title"><span class="label-en">WBTC Online Bookable Services &middot; from Digha</span><span class="label-bn">ডাব্লুবিটিসি অনলাইন বুকিং সেবা &middot; দীঘা থেকে</span></h3>
  <p class="alt-note" style="margin-bottom:10px"><span class="label-en">These WBTC Kolkata-bound services can be booked online at wbtconline.in (official WBTC booking). Times below are the departure from Digha. Morning buses from 4:00 AM run as counter / depot services and are not online-bookable.</span><span class="label-bn">নিচের ডাব্লুবিটিসি কলকাতাগামী পরিষেবাগুলি wbtconline.in-এ অনলাইনে বুক করা যায় (সরকারি বুকিং)। সময়গুলি দীঘা থেকে ছাড়ার সময়। সকাল ৪:০০ থেকে প্রথম বাসগুলি কাউন্টার/ডিপো পরিষেবা — অনলাইনে বুক হয় না।</span></p>
  {rows}
</section>
'''
    anchor = '</section>\n<section class="seo-section alt-route">'
    idx = h.find(anchor)
    if idx == -1:
        raise SystemExit("anchor not found")
    h = h[: idx] + "</section>\n" + section + h[idx + len("</section>\n"):]
    with open(PAGE, "w", encoding="utf-8") as fh:
        fh.write(h)
    print("patched digha-to-kolkata.html with", len(SERVICES), "services")


if __name__ == "__main__":
    main()
