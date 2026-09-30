#!/usr/bin/env python3
"""Round 3 (GSC audit follow-up): the WBTC (CTC) corridor cards generated from the
batch JSONs already exist on 20 pages (verified against the JSON — all accurate).
What is still open:

1. midnapur-to-kolkata.html — missing the WBTC (CTC) card. Source: redBus WBTC-CTC
   operator listing (batch JSON): Midnapore -> Kolkata, 8 buses, 05:00-16:50,
   ~1h 45m, from Rs 105.
2. Seven pages have metas over 165 chars (SERP truncation) — trim to <=155.

Idempotent: card guarded by marker; meta trims are string replaces.
"""
import os, re

BASE = os.path.join(os.path.dirname(__file__), "..")
BT = os.path.join(BASE, "bus-time-table")
MARKER = "<!-- midnapur-wbtc-v1 -->"

SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
       '<path d="M12 7v5l3 2"/></svg>')

CARD = f'''{MARKER}
<section class="seo-section">
    <h3 class="section-title"><span class="label-en">WBTC (CTC) Government Service</span><span class="label-bn">ডাব্লুবিটিসি (সিটিসি) সরকারি পরিষেবা</span></h3>
    <div class="bus-row">
      <div class="dep">{SVG}<div class="depcol"><span class="dep-t">5:00 AM</span></div></div>
      <div class="bmid">
        <div class="op">WBTC (CTC) <span style="color:var(--amber-ink,#6b4610);font-weight:600">· Midnapur → Kolkata</span></div>
        <div class="mrow">⏱ ~1h 45m · 🚌 8 <span class="label-en">buses daily</span><span class="label-bn">টি বাস প্রতিদিন</span> · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> 4:50 PM</div>
      </div>
      <div class="bright"><span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span><span class="badge">from ₹105</span></div>
    </div>
    <p class="bn-sub"><span class="label-en">Timings from the official WBTC/CTC listing on redBus. Buses run through the day — arrive 10 minutes early. Times can change; verify before travel.</span><span class="label-bn">সময়সূচি রেডবাসে তালিকাভুক্ত অফিসিয়াল ডাব্লুবিটিসি/সিটিসি থেকে। দিনভর বাস চলে — ১০ মিনিট আগে পৌঁছান। সময় বদলাতে পারে; যাত্রার আগে যাচাই করুন।</span></p>
  </section>
'''

METAS = {
    "kolkata-to-durgapur.html": (
        "Kolkata to Durgapur bus time table — 153 buses listed, first 2:00 AM, last 9:10 PM. Run by Express Line, Greenline, MONALISHA TRAVELS. Timings and stoppages on BusJatri.",
        "Kolkata to Durgapur bus timetable — 153 buses, first 2:00 AM, last 9:10 PM. WBTC (CTC), SBSTC & private buses, timings on BusJatri."),
    "kolkata-to-purulia.html": (
        "Kolkata to Purulia bus time table — 22 buses listed, first 4:45 AM, last 10:00 PM. Run by SBSTC, South Bengal State Transport Corporation, WBTC. Timings and stoppages on BusJatri.",
        "Kolkata to Purulia bus timetable — 22 buses, first 4:45 AM, last 10:00 PM. WBTC (CTC), SBSTC & private buses, timings on BusJatri."),
    "digha-to-kolkata.html": (
        "Digha to Kolkata bus time table — 121 buses listed, first 2:50 AM, last 11:30 PM. Run by ANUSKA TRAVELS, Ayush Riya, BAROMA TRANSPORT. Timings and stoppages on BusJatri.",
        "Digha to Kolkata bus timetable — 121 buses, first 2:50 AM, last 11:30 PM. Private & SBSTC buses, timings, stoppages on BusJatri."),
    "barasat-to-contai.html": (
        "Barasat to Contai bus time table — 30 buses listed, first 5:55 AM, last 6:50 PM. Run by Ayush Riya, Santosh Bus Service, Sohana Paribahan. Timings and stoppages on BusJatri.",
        "Barasat to Contai (Kanthi) bus timetable — 30 buses, first 5:55 AM, last 6:50 PM. Private & WBTC buses, timings, stoppages on BusJatri."),
    "esplanade-to-arambagh.html": (
        "Esplanade to Arambagh bus time table — 26 buses listed, first 4:30 AM, last 10:00 PM. Run by ABIR TRAVELS, MDG Paribahan, MONALISHA TRAVELS. Timings and stoppages on BusJatri.",
        "Esplanade to Arambagh bus timetable — 26 buses, first 4:30 AM, last 10:00 PM. Private & WBTC buses, timings, stoppages on BusJatri."),
    "kharagpur-to-barasat.html": (
        "Kharagpur (Chowrangee) to Barasat WBTC bus time table — 9 govt buses daily, first 5:15 AM, last 5:05 PM. Fare from ₹114. Journey ~1h 55m. Timings and FAQs on BusJatri.",
        "Kharagpur (Chowrangee) to Barasat WBTC bus timetable — 9 govt buses daily, first 5:15 AM, last 5:05 PM, from ₹114, ~1h 55m. BusJatri."),
    "kharagpur-to-kolkata-airport.html": (
        "Kharagpur (Chowrangee) to Kolkata Airport WBTC bus time table — 9 govt buses daily, first 5:15 AM, last 5:05 PM. Fare from ₹105. Journey ~1h 40m. Timings and FAQs on BusJatri.",
        "Kharagpur (Chowrangee) to Kolkata Airport WBTC bus timetable — 9 govt buses daily, first 5:15 AM, last 5:05 PM, from ₹105, ~1h 40m. BusJatri."),
}


def main():
    # 1. midnapur-to-kolkata WBTC card, after the Today's Departures section
    p = os.path.join(BT, "midnapur-to-kolkata.html")
    h = open(p, encoding="utf-8").read()
    if MARKER not in h:
        vs = h.find("Via Stoppages")
        if vs == -1:
            raise SystemExit("Via Stoppages not found")
        e = h.rfind("</section>", 0, vs) + len("</section>")
        h = h[:e] + "\n  " + CARD + h[e:]
        open(p, "w", encoding="utf-8").write(h)
        print("midnapur-to-kolkata.html: WBTC card added")

    # 2. meta trims
    for page, (old, new) in METAS.items():
        assert len(new) <= 155, (page, len(new))
        p = os.path.join(BT, page)
        h = open(p, encoding="utf-8").read()
        if new in h:
            pass
        elif old in h:
            h = h.replace(old, new)
            open(p, "w", encoding="utf-8").write(h)
        else:
            raise SystemExit(f"meta anchor not found in {page}")
        m = re.search(r'<meta name="description" content="([^"]*)"', h)
        print(f"{page}: meta {len(m.group(1))} chars")


if __name__ == "__main__":
    main()
