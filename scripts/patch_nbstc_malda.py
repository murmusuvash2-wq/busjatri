#!/usr/bin/env python3
"""Add NBSTC corridor sections to the Kolkata <-> Malda route pages and fix
the 'first bus' FAQs (NBSTC runs from 6:30 AM / 5:00 AM per the official
redBus listing; the pages previously claimed the first bus was 5:00 PM).

Data source (2026-09-30, official redBus listing pages):
  Kolkata -> Malda: NBSTC First 06:30, Last 20:45, ~7h22m, from INR 258
  Malda   -> Kolkata: NBSTC First 05:00, Last 23:15, ~8h37m, from INR 258
Idempotent: skips a page if the <!-- nbstc-malda-v1 --> marker exists.
"""
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
MARKER = "<!-- nbstc-malda-v1 -->"

SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
       '<path d="M12 7v5l3 2"/></svg>')


def section(dep, route_en, route_bn, mrow_en, mrow_bn, note_en, note_bn):
    return f'''{MARKER}
<section class="seo-section">
    <h3 class="section-title"><span class="label-en">NBSTC (North Bengal State Transport) Service</span><span class="label-bn">এনবিএসটিসি (উত্তরবঙ্গ রাষ্ট্রীয় পরিবহণ) পরিষেবা</span></h3>
    <div class="bus-row">
      <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{dep}</span></div></div>
      <div class="bmid">
        <div class="op">NBSTC <span style="color:var(--amber-ink,#6b4610);font-weight:600">· {route_en}</span></div>
        <div class="mrow">⏱ {mrow_en} · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> {mrow_bn}</div>
      </div>
      <div class="bright"><span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span><span class="badge">from ₹258</span></div>
    </div>
    <p class="bn-sub"><span class="label-en">{note_en}</span><span class="label-bn">{note_bn}</span></p>
  </section>
'''


KOL_SEC = section(
    "6:30 AM",
    "Kolkata → Malda",
    "কলকাতা → মালদা",
    "~7h 20m",
    "8:45 PM",
    "Timings from the official NBSTC listing on redBus. NBSTC services on this corridor run from early morning "
    "(first departure 6:30 AM) to night (last departure 8:45 PM). Times can change; verify before travel.",
    "রেডবাসে তালিকাভুক্ত অফিসিয়াল এনবিএসটিসি সময়সূচি অনুযায়ী। এই রুটে এনবিএসটিসি বাস ভোর থেকে রাত পর্যন্ত চলে "
    "(প্রথম ছাড়ে সকাল ৬:৩০, শেষ ছাড়ে রাত ৮:৪৫)। সময় বদলাতে পারে; যাত্রার আগে যাচাই করুন।")

MAL_SEC = section(
    "5:00 AM",
    "Malda → Kolkata (Esplanade)",
    "মালদা → কলকাতা (এসপ্ল্যানেড)",
    "~8h 35m",
    "11:15 PM",
    "Timings from the official NBSTC listing on redBus. NBSTC services on this corridor run from early morning "
    "(first departure 5:00 AM) to late night (last departure 11:15 PM). Times can change; verify before travel.",
    "রেডবাসে তালিকাভুক্ত অফিসিয়াল এনবিএসটিসি সময়সূচি অনুযায়ী। এই রুটে এনবিএসটিসি বাস ভোর থেকে গভীর রাত পর্যন্ত চলে "
    "(প্রথম ছাড়ে সকাল ৫:০০, শেষ ছাড়ে রাত ১১:১৫)। সময় বদলাতে পারে; যাত্রার আগে যাচাই করুন।")

OLD_EN_KOL = ("The first bus listed leaves Kolkata at <b>5:00 PM</b> — "
              "Shyamoli Paribahan (Shyamoli Paribahan). Arrive a little early, "
              "as buses often depart once seats fill up.")
NEW_EN_KOL = ("The earliest service on this corridor is the <b>NBSTC</b> bus, departing at "
              "<b>6:30 AM</b> (per the official redBus listing). Among the timetable services listed "
              "above, the first leaves Kolkata at <b>5:00 PM</b> — Shyamoli Paribahan. Arrive a little "
              "early, as buses often depart once seats fill up.")

OLD_EN_MAL = ("The first bus listed leaves Malda at <b>5:00 PM</b> — "
              "Shyamoli Paribahan (Shyamoli Paribahan). Arrive a little early, "
              "as buses often depart once seats fill up.")
NEW_EN_MAL = ("The earliest service on this corridor is the <b>NBSTC</b> bus, departing at "
              "<b>5:00 AM</b> (per the official redBus listing). Among the timetable services listed "
              "above, the first leaves Malda at <b>5:00 PM</b> — Shyamoli Paribahan. Arrive a little "
              "early, as buses often depart once seats fill up.")

OLD_BN = ("তালিকা অনুযায়ী প্রথম বাস ছাড়ে <b>বিকেল ৫:০০</b> — Shyamoli Paribahan (Shyamoli Paribahan)। "
          "সিটের জন্য একটু আগে গিয়ে অপেক্ষা করাই ভালো।")
NEW_BN_KOL = ("এই রুটে সবচেয়ে আগের পরিষেবা হল <b>এনবিএসটিসি</b> বাস — সকাল <b>৬:৩০</b>-এ ছাড়ে "
              "(রেডবাসের অফিসিয়াল তালিকা অনুযায়ী)। উপরের সময়সূচির তালিকায় প্রথম বাস ছাড়ে <b>বিকেল ৫:০০</b> — "
              "Shyamoli Paribahan। সিটের জন্য একটু আগে গিয়ে অপেক্ষা করাই ভালো।")
NEW_BN_MAL = ("এই রুটে সবচেয়ে আগের পরিষেবা হল <b>এনবিএসটিসি</b> বাস — ভোর <b>৫:০০</b>-এ ছাড়ে "
              "(রেডবাসের অফিসিয়াল তালিকা অনুযায়ী)। উপরের সময়সূচির তালিকায় প্রথম বাস ছাড়ে <b>বিকেল ৫:০০</b> — "
              "Shyamoli Paribahan। সিটের জন্য একটু আগে গিয়ে অপেক্ষা করাই ভালো।")


def patch(page, sec_html, old_en, new_en, new_bn):
    path = os.path.join(BASE, "bus-time-table", page)
    with open(path, encoding="utf-8") as fh:
        h = fh.read()
    if MARKER in h:
        print(page, "already patched, skipping")
        return
    m = h.find("<!-- malda-svc-v1 -->")
    if m == -1:
        raise SystemExit("malda-svc-v1 marker not found in " + page)
    e = h.find("</section>", m) + len("</section>")
    h = h[:e] + "\n  " + sec_html + h[e:]
    n_en = h.count(old_en)
    n_bn = h.count(OLD_BN)
    h = h.replace(old_en, new_en).replace(OLD_BN, new_bn)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(h)
    print(f"patched {page} | EN FAQ replaced: {n_en} | BN FAQ replaced: {n_bn}")


def main():
    patch("kolkata-to-malda.html", KOL_SEC, OLD_EN_KOL, NEW_EN_KOL, NEW_BN_KOL)
    patch("malda-to-esplanade.html", MAL_SEC, OLD_EN_MAL, NEW_EN_MAL, NEW_BN_MAL)


if __name__ == "__main__":
    main()
