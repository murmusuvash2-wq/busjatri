#!/usr/bin/env python3
"""kolkata-to-digha.html — add an official government-services corridor section.

Why: the page carries 41 'Time N/A' cards, 40 of which are WBTC buses whose
route origin is Joka Depot / Karunamoyee / Garia / Baruipur / Newtown — origins
we have no official departure times for (our wbtconline data is Esplanade-origin).
Rather than invent times, we add the official corridor-level data from the redBus
listing (2026-09-30):
  Kolkata -> Digha: 406 services / 65 operators, 00:02-23:59, ~4h 41m, 181 km, from Rs 127
  WBTC (CTC): 04:10 - 23:58, ~4h 30m | SBSTC: 04:00 - 23:45 | NBSTC: 06:30 only
Idempotent: guarded by <!-- digha-official-v1 -->.
"""
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
BT = os.path.join(BASE, "bus-time-table")
MARKER = "<!-- digha-official-v1 -->"

SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
       '<path d="M12 7v5l3 2"/></svg>')


def row(op, route_en, route_bn, dep, mrow_en, mrow_bn, badge_en, badge_bn):
    return f'''<div class="bus-row">
      <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{dep}</span></div></div>
      <div class="bmid">
        <div class="op">{op} <span style="color:var(--amber-ink,#6b4610);font-weight:600">· {route_en}</span></div>
        <div class="mrow">{mrow_en}</div>
      </div>
      <div class="bright"><span class="badge badge-govt"><span class="label-en">{badge_en}</span><span class="label-bn">{badge_bn}</span></span><span class="badge">from ₹127</span></div>
    </div>'''


SECTION = f'''{MARKER}
<section class="seo-section">
    <h3 class="section-title"><span class="label-en">Government Services — Official Listing</span><span class="label-bn">সরকারি পরিষেবা — অফিসিয়াল তালিকা</span></h3>
    {row("WBTC (CTC)", "Kolkata → Digha", "কলকাতা → দীঘা", "4:10 AM",
         '⏱ ~4h 30m · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> 11:58 PM',
         '', "Govt", "সরকারি")}
    {row("SBSTC", "Kolkata → Digha", "কলকাতা → দীঘা", "4:00 AM",
         '⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> 11:45 PM',
         '', "Govt", "সরকারি")}
    <p class="bn-sub"><span class="label-en">Per the official redBus listing, 406 services by 65 operators run this corridor from 12:02 AM to 11:59 PM (181 km, about 4h 41m): WBTC (CTC) 4:10 AM–11:58 PM, SBSTC 4:00 AM–11:45 PM, and one NBSTC service at 6:30 AM. The timetable above lists 121 services. Times can change; verify before travel.</span><span class="label-bn">রেডবাসের অফিসিয়াল তালিকা অনুযায়ী এই রুটে ৬৫টি অপারেটরের ৪০৬টি পরিষেবা চলে রাত ১২:০২ থেকে রাত ১১:৫৯ পর্যন্ত (১৮১ কিমি, প্রায় ৪ ঘণ্টা ৪১ মিনিট): ডব্লিউবিটিসি (সিটিসি) ৪:১০ AM–১১:৫৮ PM, এসবিএসটিসি ৪:০০ AM–১১:৪৫ PM, এবং একটি এনবিএসটিসি পরিষেবা ৬:৩০ AM-এ। উপরের সময়সূচিতে ১২১টি পরিষেবা তালিকাভুক্ত। সময় বদলাতে পারে; যাত্রার আগে যাচাই করুন।</span></p>
  </section>
'''


def main():
    path = os.path.join(BT, "kolkata-to-digha.html")
    h = open(path, encoding="utf-8").read()
    if MARKER in h:
        print("already patched")
        return
    m = h.find("<!-- digha-svc-v1 -->")
    if m == -1:
        raise SystemExit("digha-svc-v1 marker not found")
    e = h.find("</section>", m) + len("</section>")
    h = h[:e] + "\n  " + SECTION + h[e:]
    open(path, "w", encoding="utf-8").write(h)
    print("kolkata-to-digha.html patched")


if __name__ == "__main__":
    main()
