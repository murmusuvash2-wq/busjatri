#!/usr/bin/env python3
"""SEO fixes for the pages that get Google impressions (GSC 2026-09-30):
1. cooch-behar-to-siliguri.html — trim 205-char meta to ~152 (SERP truncation fix)
2. kolkata-to-asansol.html — add SBSTC corridor section (official redBus operator
   listing: SBSTC First 05:00, Last 17:00, ~5h13m; targets 'sbstc bus timetable'
   queries — 22+ impressions)
3. asansol-to-kolkata.html — add overnight/private corridor section (official
   redBus: corridor 00:30–23:45, Greenline 01:40, Express Line 03:30–17:30,
   Lokenath 04:20+) + soften first-bus FAQ so it does not contradict.
Idempotent: each block is guarded by a marker.
"""
import os, re

BASE = os.path.join(os.path.dirname(__file__), "..")
BT = os.path.join(BASE, "bus-time-table")

SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
       '<path d="M12 7v5l3 2"/></svg>')

# ---------------- 1. CB -> Siliguri meta trim ----------------
CB_OLD = ('<meta name="description" content="Cooch Behar (Coochbehar / Koch Bihar) to Siliguri bus time '
          'table — 54 buses, first 5:00 AM, last 8:45 PM. Distance about 140 km, journey 3-4 hours. '
          'NBSTC + private buses, timings and stoppages on BusJatri.">')
CB_NEW = ('<meta name="description" content="Cooch Behar (Coochbehar/Koch Bihar) to Siliguri bus '
          'timetable — 54 buses, first 5:00 AM, last 8:45 PM. NBSTC & private bus timings, stoppages '
          'on BusJatri.">')

# ---------------- 2. SBSTC section (kolkata-to-asansol) ----------------
SBSTC_SEC = f'''<!-- asansol-sbstc-v1 -->
<section class="seo-section">
    <h3 class="section-title"><span class="label-en">SBSTC (South Bengal State Transport) Service</span><span class="label-bn">এসবিএসটিসি (দক্ষিণবঙ্গ রাষ্ট্রীয় পরিবহণ) পরিষেবা</span></h3>
    <div class="bus-row">
      <div class="dep">{SVG}<div class="depcol"><span class="dep-t">5:00 AM</span></div></div>
      <div class="bmid">
        <div class="op">SBSTC <span style="color:var(--amber-ink,#6b4610);font-weight:600">· Kolkata → Asansol</span></div>
        <div class="mrow">⏱ ~5h 15m · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> 5:00 PM</div>
      </div>
      <div class="bright"><span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span><span class="badge">from ₹165</span></div>
    </div>
    <p class="bn-sub"><span class="label-en">Timings from the official SBSTC operator listing on redBus: SBSTC services on this corridor run 5:00 AM to 5:00 PM. 54 of the 80 services in the timetable above are SBSTC government buses. Times can change; verify before travel.</span><span class="label-bn">রেডবাসে তালিকাভুক্ত অফিসিয়াল এসবিএসটিসি সময়সূচি অনুযায়ী: এই রুটে এসবিএসটিসি বাস সকাল ৫:০০ থেকে বিকেল ৫:০০ পর্যন্ত চলে। উপরের সময়সূচির ৮০টির মধ্যে ৫৪টিই এসবিএসটিসি সরকারি বাস। সময় বদলাতে পারে; যাত্রার আগে যাচাই করুন।</span></p>
  </section>
'''

# ---------------- 3. Overnight corridor section (asansol-to-kolkata) ----------------
PRIV_SEC = f'''<!-- asansol-priv-v1 -->
<section class="seo-section">
    <h3 class="section-title"><span class="label-en">Overnight & Private Bus Services</span><span class="label-bn">রাতের ও বেসরকারি বাস পরিষেবা</span></h3>
    <div class="bus-row">
      <div class="dep">{SVG}<div class="depcol"><span class="dep-t">12:30 AM</span></div></div>
      <div class="bmid">
        <div class="op">Greenline · Express Line · Lokenath <span style="color:var(--amber-ink,#6b4610);font-weight:600">· Asansol → Kolkata</span></div>
        <div class="mrow">⏱ ~4h 20m · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> 11:45 PM</div>
      </div>
      <div class="bright"><span class="badge"><span class="label-en">Private</span><span class="label-bn">বেসরকারি</span></span><span class="badge">from ₹165</span></div>
    </div>
    <p class="bn-sub"><span class="label-en">Per the official redBus listing, this corridor runs from 12:30 AM to 11:45 PM — 146 daily services by 15 operators: Greenline from 1:40 AM, Express Line 3:30 AM to 5:30 PM, Lokenath from 4:20 AM. The timetable above covers the 80 listed services (5:00 AM to 5:00 PM); these overnight private services run in addition. Times can change; verify before travel.</span><span class="label-bn">রেডবাসের অফিসিয়াল তালিকা অনুযায়ী এই রুটে বাস চলে রাত ১২:৩০ থেকে রাত ১১:৪৫ পর্যন্ত — ১৫টি অপারেটরের ১৪৬টি দৈনিক পরিষেবা: গ্রিনলাইন ভোর ১:৪০ থেকে, এক্সপ্রেস লাইন ভোর ৩:৩০ থেকে বিকেল ৫:৩০, লোকনাথ ভোর ৪:২০ থেকে। উপরের সময়সূচিতে ৮০টি বাস তালিকাভুক্ত (সকাল ৫:০০ থেকে বিকেল ৫:০০); এই রাতের বেসরকারি বাসগুলো তার অতিরিক্ত। সময় বদলাতে পারে; যাত্রার আগে যাচাই করুন।</span></p>
  </section>
'''

FAQ_EN_OLD = ("first bus leaves at 5:00 AM and the last one at 5:00 PM. Schedules can change without "
              "notice - check at the counter before you set out. 54 of them are SBSTC government buses.")
FAQ_EN_NEW = ("first bus in the timetable above leaves at 5:00 AM and the last one at 5:00 PM (54 of them "
              "are SBSTC government buses). Overnight private services also run on this corridor — see the "
              "overnight section below. Schedules can change without notice - check at the counter before you set out.")

def patch_page(page, marker, sec_html):
    path = os.path.join(BT, page)
    h = open(path, encoding="utf-8").read()
    if marker in h:
        print(page, "already patched, skipping")
        return
    m = h.find("<!-- asansol-svc-v1 -->")
    if m == -1:
        raise SystemExit("asansol-svc-v1 marker missing in " + page)
    e = h.find("</section>", m) + len("</section>")
    h = h[:e] + "\n  " + sec_html + h[e:]
    open(path, "w", encoding="utf-8").write(h)
    print(page, "section added")

def main():
    # 1. CB meta trim
    p = os.path.join(BT, "cooch-behar-to-siliguri.html")
    h = open(p, encoding="utf-8").read()
    if CB_NEW not in h:
        if CB_OLD not in h:
            raise SystemExit("CB meta old text not found")
        h = h.replace(CB_OLD, CB_NEW)
        open(p, "w", encoding="utf-8").write(h)
    meta = re.search(r'<meta name="description" content="([^"]*)"', h)
    print("CB meta len:", len(meta.group(1)))

    # 2/3. asansol sections
    patch_page("kolkata-to-asansol.html", "asansol-sbstc-v1", SBSTC_SEC)
    patch_page("asansol-to-kolkata.html", "asansol-priv-v1", PRIV_SEC)

    # 4. asansol-to-kolkata FAQ sync (EN 2x + BN 2x)
    p = os.path.join(BT, "asansol-to-kolkata.html")
    h = open(p, encoding="utf-8").read()
    n = h.count(FAQ_EN_OLD)
    h = h.replace(FAQ_EN_OLD, FAQ_EN_NEW)
    # BN: order-neutral prefix + overnight mention, exact substring replace-all
    BN_OLD = "প্রথম বাস সকাল ৫:০০ টায় ছাড়ে এবং শেষ বাস বিকেল ৫:০০ টায়।"
    BN_NEW = "তালিকা অনুযায়ী প্রথম বাস সকাল ৫:০০ টায় ছাড়ে এবং শেষ বাস বিকেল ৫:০০ টায়; এই রুটে রাতের বেসরকারি বাসও চলে (নিচে দেখুন)।"
    nbn = h.count(BN_OLD)
    h = h.replace(BN_OLD, BN_NEW)
    open(p, "w", encoding="utf-8").write(h)
    print("asansol-to-kolkata FAQ EN replaced:", n, "| BN replaced:", nbn)

if __name__ == "__main__":
    main()
