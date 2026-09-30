#!/usr/bin/env python3
"""Audit-driven fixes for two impression-earning pages (GSC 2026-09-30).

durgapur-to-kolkata.html  (86 imp-earning route; 42 Time N/A cards)
  - meta 170 -> ~150 chars
  - add WBTC (CTC) official section. Source: redBus WBTC-CTC operator listing
    (user-supplied batch JSONs + live page): Durgapur->Kolkata 19 buses,
    06:45-18:00, ~2h15m (min), from Rs 135; Durgapur->Kolkata Airport 15 buses.

bankura-to-karunamoyee.html (34 imp; 17 Time N/A cards, 0 fillable per-service)
  - meta 167 -> ~150 chars
  - add Bankura->Kolkata official listing section (redBus live page):
    16 services / 3 operators, 04:45-23:59, ~3h31m, 171 km, from Rs 180;
    City Queen 21:55-22:15, Yatri Vihar 23:59, SBSTC serves the route.
    Karunamoyee is among the listed Kolkata drop points.

Idempotent: guarded by markers.
"""
import os, re

BASE = os.path.join(os.path.dirname(__file__), "..")
BT = os.path.join(BASE, "bus-time-table")

SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
       '<path d="M12 7v5l3 2"/></svg>')


def row(op, route, dep, mrow_en, mrow_bn, govt, fare):
    badge = ('<span class="badge badge-govt"><span class="label-en">Govt</span>'
             '<span class="label-bn">সরকারি</span></span>' if govt else
             '<span class="badge"><span class="label-en">Private</span>'
             '<span class="label-bn">বেসরকারি</span></span>')
    return f'''<div class="bus-row">
      <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{dep}</span></div></div>
      <div class="bmid">
        <div class="op">{op} <span style="color:var(--amber-ink,#6b4610);font-weight:600">· {route}</span></div>
        <div class="mrow">{mrow_en}</div>
      </div>
      <div class="bright">{badge}<span class="badge">from ₹{fare}</span></div>
    </div>'''


DUR_SECTION = f'''<!-- durgapur-wbtc-official-v1 -->
<section class="seo-section">
    <h3 class="section-title"><span class="label-en">WBTC (CTC) — Official Listing</span><span class="label-bn">ডব্লিউবিটিসি (সিটিসি) — অফিসিয়াল তালিকা</span></h3>
    {row("WBTC (CTC)", "Durgapur → Kolkata", "6:45 AM",
         '⏱ ~2h 15m · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> 6:00 PM', '', True, 135)}
    {row("WBTC (CTC)", "Durgapur → Kolkata Airport", "6:45 AM",
         '⏱ ~2h 25m · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> 6:00 PM', '', True, 135)}
    <p class="bn-sub"><span class="label-en">Per the official WBTC (CTC) operator listing on redBus: 19 WBTC buses run Durgapur to Kolkata daily — first 6:45 AM, last 6:00 PM, about 2h 15m, from ₹135; 15 of them continue to Kolkata Airport. The timetable above lists 153 services including private operators. Times can change; verify before travel.</span><span class="label-bn">রেডবাসে তালিকাভুক্ত অফিসিয়াল ডব্লিউবিটিসি (সিটিসি) তথ্য অনুযায়ী: দৈনিক ১৯টি ডব্লিউবিটিসি বাস দুর্গাপুর থেকে কলকাতা যায় — প্রথম ৬:৪৫ AM, শেষ ৬:০০ PM, প্রায় ২ ঘণ্টা ১৫ মিনিট, ১৩৫ টাকা থেকে; এর মধ্যে ১৫টি কলকাতা বিমানবন্দর পর্যন্ত যায়। উপরের সময়সূচিতে বেসরকারি বাস মিলিয়ে ১৫৩টি পরিষেবা তালিকাভুক্ত। সময় বদলাতে পারে; যাত্রার আগে যাচাই করুন।</span></p>
  </section>
'''

BANK_SECTION = f'''<!-- bankura-official-v1 -->
<section class="seo-section">
    <h3 class="section-title"><span class="label-en">Bankura → Kolkata (incl. Karunamoyee) — Official Listing</span><span class="label-bn">বাঁকুড়া → কলকাতা (করুণাময়ী সহ) — অফিসিয়াল তালিকা</span></h3>
    {row("City Queen Bus Service", "Bankura → Kolkata", "9:55 PM",
         '⏱ ~6h 25m · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> 10:15 PM', '', False, 180)}
    {row("Yatri Vihar Travels", "Bankura → Kolkata", "11:59 PM",
         '⏱ ~5h 11m', '', False, 180)}
    <p class="bn-sub"><span class="label-en">Per the official redBus listing, 16 services by 3 operators run Bankura to Kolkata (171 km, about 3h 31m, from ₹180) — the first at 4:45 AM and the last at 11:59 PM; Karunamoyee is one of the listed Kolkata drop points. City Queen runs 9:55 PM–10:15 PM, Yatri Vihar at 11:59 PM, and SBSTC also serves the route. Times can change; verify before travel.</span><span class="label-bn">রেডবাসের অফিসিয়াল তালিকা অনুযায়ী ৩টি অপারেটরের ১৬টি পরিষেবা বাঁকুড়া থেকে কলকাতা চলে (১৭১ কিমি, প্রায় ৩ ঘণ্টা ৩১ মিনিট, ১৮০ টাকা থেকে) — প্রথম ৪:৪৫ AM, শেষ ১১:৫৯ PM; করুণাময়ী কলকাতার তালিকাভুক্ত ড্রপ পয়েন্টগুলির একটি। সিটি কুইন ৯:৫৫ PM–১০:১৫ PM, যাত্রী বিহার ১১:৫৯ PM-এ চলে এবং এসবিএসটিসিও এই রুটে চলে। সময় বদলাতে পারে; যাত্রার আগে যাচাই করুন।</span></p>
  </section>
'''

METAS = {
    "durgapur-to-kolkata.html": (
        "Durgapur to Kolkata bus time table — 153 buses listed, first 2:00 AM, last 11:15 PM. Run by Express Line, Greenline, MONALISHA TRAVELS. Timings and stoppages on BusJatri.",
        "Durgapur to Kolkata bus timetable — 153 buses, first 2:00 AM, last 11:15 PM. WBTC (CTC), SBSTC & private buses, timings, stoppages on BusJatri."),
    "bankura-to-karunamoyee.html": (
        "Bankura to Karunamoyee bus time table — 48 buses listed, first 3:40 AM, last 11:55 PM. Run by MONALISHA TRAVELS, Mahamaya, Mini Bus. Timings and stoppages on BusJatri.",
        "Bankura to Karunamoyee (Kolkata) bus timetable — 48 buses, first 3:40 AM, last 11:55 PM. Private & SBSTC buses, timings, stoppages on BusJatri."),
}


def main():
    # 1. metas
    for page, (old, new) in METAS.items():
        p = os.path.join(BT, page)
        h = open(p, encoding="utf-8").read()
        assert new != old
        if new not in h:
            if old not in h:
                raise SystemExit(f"meta anchor not found in {page}")
            h = h.replace(old, new)
            open(p, "w", encoding="utf-8").write(h)
        m = re.search(r'<meta name="description" content="([^"]*)"', h)
        print(f"{page}: meta {len(m.group(1))} chars")

    # 2. durgapur section after wbtc-long-v1
    p = os.path.join(BT, "durgapur-to-kolkata.html")
    h = open(p, encoding="utf-8").read()
    if "durgapur-wbtc-official-v1" not in h:
        m = h.find("<!-- wbtc-long-v1 -->")
        if m == -1:
            raise SystemExit("wbtc-long-v1 marker not found")
        e = h.find("</section>", m) + len("</section>")
        h = h[:e] + "\n  " + DUR_SECTION + h[e:]
        open(p, "w", encoding="utf-8").write(h)
        print("durgapur-to-kolkata.html: section added")

    # 3. bankura section before the Via Stoppages section
    p = os.path.join(BT, "bankura-to-karunamoyee.html")
    h = open(p, encoding="utf-8").read()
    if "bankura-official-v1" not in h:
        vs = h.find("Via Stoppages")
        if vs == -1:
            raise SystemExit("Via Stoppages not found")
        e = h.rfind("</section>", 0, vs) + len("</section>")
        h = h[:e] + "\n  " + BANK_SECTION + h[e:]
        open(p, "w", encoding="utf-8").write(h)
        print("bankura-to-karunamoyee.html: section added")


if __name__ == "__main__":
    main()
