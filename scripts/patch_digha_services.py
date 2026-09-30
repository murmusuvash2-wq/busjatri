#!/usr/bin/env python3
"""Add 'WBTC online bookable services (Esplanade -> Digha)' section to
bus-time-table/kolkata-to-digha.html.

Data source: wbtconline.in official booking search (Kolkata -> Digha),
cross-verified across two searches on different dates (30 Sep & 1 Oct 2026) -
identical services and times, so treated as the stable daily schedule.
Times are DEPARTURE FROM ESPLANADE (the boarding stoppage searched).
Idempotent: skips if the <!-- digha-svc-v1 --> marker is already present.
"""
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
PAGE = os.path.join(BASE, "bus-time-table", "kolkata-to-digha.html")
MARKER = "<!-- digha-svc-v1 -->"

SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
       '<path d="M12 7v5l3 2"/></svg>')

# (time, code, route, ac, fare, seats)
SERVICES = [
    ("2:00 PM",  "—",     "Kolkata &ndash; Digha (online express)",               False, "145", "54"),
    ("2:40 PM",  "E40/1", "Kolkata &ndash; Digha",                                  False, "145", "54"),
    ("3:45 PM",  "E19D",  "Belgachia &ndash; Digha via Esplanade",                 False, "145", "54"),
    ("3:45 PM",  "ACT6A", "Shyambazar &ndash; Digha via Esplanade",                True,  "370", "42"),
    ("4:45 PM",  "E40",   "Khidderpur &ndash; Digha",                               False, "145", "54"),
    ("5:45 PM",  "E45",   "Joka &ndash; Tollygunge &ndash; Digha",                  False, "145", "54"),
    ("11:10 PM", "E19A",  "Habra &ndash; Digha via Esplanade",                     False, "145", "54"),
    ("11:45 PM", "ACT5",  "Barasat &ndash; Digha via Esplanade",                   True,  "370", "42"),
    ("11:55 PM", "E17",   "Barasat &ndash; Digha via Esplanade",                   False, "145", "54"),
    ("11:58 PM", "E17",   "Barasat &ndash; Digha via Esplanade",                   False, "145", "54"),
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
      <div class="mrow">💺 {seats} <span class="label-en">seats &middot; departs Esplanade</span><span class="label-bn">আসন &middot; এসপ্ল্যানেড থেকে ছাড়ে</span></div>
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
  <h3 class="section-title"><span class="label-en">WBTC Online Bookable Services &middot; from Esplanade</span><span class="label-bn">ডাব্লুবিটিসি অনলাইন বুকিং সেবা &middot; এসপ্ল্যানেড থেকে</span></h3>
  <p class="alt-note" style="margin-bottom:10px"><span class="label-en">These WBTC Digha services can be booked online at wbtconline.in (official WBTC booking). Times below are the departure from Esplanade. Morning buses from 4:10 AM run as counter / depot services and are not online-bookable.</span><span class="label-bn">নিচের ডাব্লুবিটিসি দীঘা পরিষেবাগুলি wbtconline.in-এ অনলাইনে বুক করা যায় (সরকারি বুকিং)। সময়গুলি এসপ্ল্যানেড থেকে ছাড়ার সময়। সকাল ৪:১০ থেকে প্রথম বাসগুলি কাউন্টার/ডিপো পরিষেবা — অনলাইনে বুক হয় না।</span></p>
  {rows}
</section>
'''
    anchor = "</section>\n<section class=\"seo-section alt-route\">"
    idx = h.find(anchor)
    if idx == -1:
        raise SystemExit("anchor not found")
    h = h[: idx] + "</section>\n" + section + h[idx + len("</section>\n"):]
    with open(PAGE, "w", encoding="utf-8") as fh:
        fh.write(h)
    print("patched kolkata-to-digha.html with", len(SERVICES), "services")


if __name__ == "__main__":
    main()
