#!/usr/bin/env python3
"""WBTC long-route upgrade: fill Time-N/A WBTC cards + route-level WBTC sections
+ 12 new route pages + sitemap/interlinks. Design-safe (existing classes only).

1. Global card fill: every WBTC "Time N/A" bus card whose corridor matches a
   known redBus WBTC pair gets "First X · Last Y" + duration.
2. WBTC info section on existing route pages (after Today's Departures).
3. JSON-LD FAQ question appended (proper json parse/dump).
4. 12 new route pages (barasat-to-durgapur.html as visual template).
5. sitemap.xml entries + "More Routes" interlinks.

Idempotent: markers wbtc-long-v1 / wbtc-card-v1. DRY by default; --write applies.
Source: redBus WBTC/CTC listings (first/last bus, buses/day, fare, duration).
"""
import json, re, sys, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv
WRITE = not DRY

# key "from|to" -> (from, to, buses/day, first, last, fare, dur, dist)
WBTC_DATA = {
    "Asansol|Kolkata Airport": ("Asansol", "Kolkata Airport", 14, "05:45", "17:05", 165, "3h 45m", None),
    "Barasat|Asansol": ("Barasat", "Asansol", 4, "05:40", "07:30", 177, "4h 00m", None),
    "Barasat|Contai": ("Barasat", "Contai", 27, "03:45", "15:50", 131, "2h 45m", "164 Km"),
    "Barasat|Digha": ("Barasat", "Digha", 35, "03:45", "22:35", 161, "3h 20m", "198 Km"),
    "Barasat|Durgapur": ("Barasat", "Durgapur", 5, "05:40", "07:30", 147, "2h 40m", None),
    "Barasat|Kolaghat": ("Barasat", "Kolaghat", 32, "03:45", "15:50", 69, "1h 10m", "87 Km"),
    "Barasat|Midnapore": ("Barasat", "Midnapore", 8, "05:15", "15:45", 120, "2h 15m", "145 Km"),
    "Barasat|Nandakumar": ("Barasat", "Nandakumar", 28, "03:45", "15:50", 89, "1h 45m", "112 Km"),
    "Chowrangee|Barasat": ("Chowrangee", "Barasat", 9, "05:15", "17:05", 114, "1h 55m", "140 Km"),
    "Chowrangee|Kolkata Airport": ("Chowrangee", "Kolkata Airport", 9, "05:15", "17:05", 105, "1h 40m", None),
    "Digha|Barasat": ("Digha", "Barasat", 34, "04:00", "23:30", 161, "3h 25m", "200 Km"),
    "Digha|Kolkata": ("Digha", "Kolkata", 84, "04:00", "23:30", 145, "3h 00m", "181 Km"),
    "Durgapur|Kolkata": ("Durgapur", "Kolkata", 19, "06:45", "18:00", 135, "2h 15m", "168 Km"),
    "Durgapur|Kolkata Airport": ("Durgapur", "Kolkata Airport", 15, "06:45", "18:00", 135, "2h 25m", None),
    "Habra|Digha": ("Habra", "Digha", 10, "03:45", "20:15", 179, "4h 35m", None),
    "Kolkata Airport|Digha": ("Kolkata Airport", "Digha", 36, "04:00", "22:50", 153, "3h 25m", None),
    "Kolkata|Arambagh": ("Kolkata", "Arambagh", 1, "06:00", "06:00", 69, "3h 00m", None),
    "Kolkata|Asansol": ("Kolkata", "Asansol", 16, "06:00", "16:15", 165, "3h 35m", "234 Km"),
    "Kolkata|Bakkhali": ("Kolkata", "Bakkhali", 3, "06:30", "08:15", 102, "3h 15m", None),
    "Kolkata|Bolpur": ("Kolkata", "Bolpur", 15, "06:40", "16:20", 340, "2h 25m", None),
    "Kolkata|Burdwan": ("Kolkata", "Burdwan", 21, "06:05", "16:20", 81, None, "102 Km"),
    "Kolkata|Digha": ("Kolkata", "Digha", 84, "04:10", "23:58", 127, "2h 45m", "181 Km"),
    "Kolkata|Durgapur": ("Kolkata", "Durgapur", 17, "06:00", "16:15", 135, "2h 15m", "191 Km"),
    "Kolkata|Krishnanagar": ("Kolkata", "Krishnanagar", 4, "06:15", "15:30", 210, "3h 35m", None),
    "Kolkata|Mayapur ISKCON": ("Kolkata", "Mayapur ISKCON", 6, "06:15", "15:30", 108, "4h 20m", None),
    "Kolkata|Midnapore": ("Kolkata", "Midnapore", 4, "05:40", "16:10", 105, None, "127 Km"),
    "Kolkata|Purulia": ("Kolkata", "Purulia", 3, "06:00", "15:00", 595, "6h 10m", None),
    "Kolkata|Suri": ("Kolkata", "Suri", 16, "06:40", "16:30", 400, "3h 25m", "202 Km"),
    "Midnapore|Barasat": ("Midnapore", "Barasat", 8, "05:00", "16:50", 120, "2h 10m", "146 Km"),
    "Midnapore|Kolkata": ("Midnapore", "Kolkata", 8, "05:00", "16:50", 105, "1h 45m", "126 Km"),
    "Midnapore|Kolkata Airport": ("Midnapore", "Kolkata Airport", 8, "05:00", "16:50", 111, "1h 55m", None),
}

ALIAS = {  # normalised card-corridor name -> WBTC_DATA key part.
    # STRICT: only same-service origins. Garia/Joka/Karunamoyee/Baruipur/Jhargram
    # originate elsewhere with their own (unknown) timings -> NOT mapped.
    "esplanade": "kolkata",
    "barasatchapadali": "barasat", "barasat": "barasat",
    "habrastation": "habra", "habradepot": "habra",
    "medinipur": "midnapore", "midnaporetown": "midnapore",
    "kolkataairport": "kolkataairport", "airport": "kolkataairport",
    "dumdumairport": "kolkataairport", "airportterminal": "kolkataairport",
    "airportdomesticterminus": "kolkataairport", "airportgate1": "kolkataairport",
    "airportgate2": "kolkataairport", "nscbiairport": "kolkataairport",
    "chowrangee": "chowrangee", "chowrangeekharagpur": "chowrangee", "kharagpur": "chowrangee",
    "kolkata": "kolkata", "digha": "digha", "durgapur": "durgapur", "asansol": "asansol",
    "habra": "habra", "midnapore": "midnapore",
    "kolaghat": "kolaghat", "nandakumar": "nandakumar", "contai": "contai", "kanthi": "contai",
}

BN_PLACE = {"Kolkata": "কলকাতা", "Esplanade": "এসপ্ল্যানেড", "Digha": "দীঘা", "Barasat": "বারাসাত",
    "Durgapur": "দুর্গাপুর", "Asansol": "আসানসোল", "Suri": "সিউড়ি", "Bolpur": "বোলপুর",
    "Purulia": "পুরুলিয়া", "Bakkhali": "বকখালি", "Krishnanagar": "কৃষ্ণনগর",
    "Arambagh": "আরামবাগ", "Mayapur ISKCON": "মায়াপুর ইসকন", "Habra": "হাবড়া",
    "Kolaghat": "কোলাঘাট", "Nandakumar": "নন্দকুমার", "Contai": "কাঁথি", "Burdwan": "বর্ধমান",
    "Midnapore": "মেদিনীপুর", "Medinipur": "মেদিনীপুর", "Kolkata Airport": "কলকাতা এয়ারপোর্ট",
    "Kharagpur (Chowrangee)": "খড়্গপুর (চৌরঙ্গী)", "Kharagpur": "খড়্গপুর"}

def nkey(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())

def corridor_key(a, b):
    ka = ALIAS.get(nkey(re.sub(r"\s*\([^)]*\)\s*", " ", a).strip()), nkey(a))
    kb = ALIAS.get(nkey(re.sub(r"\s*\([^)]*\)\s*", " ", b).strip()), nkey(b))
    if not ka or not kb: return None
    kk = f"{ka}|{kb}"
    for dk in WBTC_DATA:
        if dk.lower() == kk: return dk
    return None

def t12(t):
    if not t: return None
    h, m = int(t[:2]), int(t[3:5])
    ap = "AM" if h < 12 else "PM"
    return f"{h % 12 or 12}:{m:02d} {ap}"

def fare_str(f):
    if f is None: return None
    return f"₹{int(f)}"

SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'

def wbtc_section(kk, page_from, page_to):
    f, t, buses, first, last, fare, dur, dist = WBTC_DATA[kk]
    disp_f = page_from if page_from else f
    disp_t = page_to if page_to else t
    mrow = f"⏱ ~{dur} · 🚌 {buses} " if dur else f"🚌 {buses} "
    sec = f'''
<!-- wbtc-long-v1 -->
<section class="seo-section">
  <h3 class="section-title"><span class="label-en">WBTC (CTC) Government Service</span><span class="label-bn">ডাব্লুবিটিসি (সিটিসি) সরকারি পরিষেবা</span></h3>
  <div class="bus-row">
    <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{t12(first)}</span></div></div>
    <div class="bmid">
      <div class="op">WBTC (CTC) <span style="color:var(--amber-ink,#6b4610);font-weight:600">· {disp_f} → {disp_t}</span></div>
      <div class="mrow">{mrow}<span class="label-en">buses daily</span><span class="label-bn">টি বাস প্রতিদিন</span> · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> {t12(last)}{(' · 🛣 ' + dist) if dist else ''}</div>
    </div>
    <div class="bright"><span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span>{f'<span class="badge">from {fare_str(fare)}</span>' if fare else ''}</div>
  </div>
</section>
'''
    return sec

def faq_jsonld(kk):
    f, t, buses, first, last, fare, dur, dist = WBTC_DATA[kk]
    q = f"What are the timings of the WBTC bus from {f} to {t}?"
    a = f"WBTC (CTC) runs {buses} buses daily from {f} to {t}. The first bus departs at {t12(first)} and the last bus at {t12(last)}."
    if fare: a += f" Fares start from {fare_str(fare)}."
    if dur: a += f" The journey takes about {dur}."
    return {"@type": "Question", "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a}}

# ---------------------------------------------------------------- card fill --
NOTIME = re.compile(r'(<span class="no-time">)<span class="label-en">Time N/A</span><span class="label-bn">সময় নেই</span>(</span>)')
OPCORR = re.compile(r'<div class="op">([^<]*WBTC[^<]*)<span[^>]*>·\s*([^<·]+?)\s*→\s*([^<·]+?)</span>')

def fill_cards(h):
    """Chunk-based: each bus-row block has dep(no-time) FIRST, then op line."""
    out = []
    pos = 0
    n = 0
    for chunk in re.split(r'(?=<div class="bus-row">)', h):
        if 'WBTC' not in chunk or 'Time N/A' not in chunk:
            out.append(chunk); continue
        om = OPCORR.search(chunk)
        nm = NOTIME.search(chunk)
        if not om or not nm:
            out.append(chunk); continue
        kk = corridor_key(om.group(2).strip(), om.group(3).strip())
        if not kk:
            out.append(chunk); continue
        f, t, buses, first, last, fare, dur, dist = WBTC_DATA[kk]
        repl = (nm.group(1)
                + f'<span class="label-en">First {t12(first)} · Last {t12(last)}</span>'
                + f'<span class="label-bn">প্রথম {t12(first)} · শেষ {t12(last)}</span>'
                + nm.group(2))
        chunk = chunk[:nm.start()] + repl + chunk[nm.end():]
        if dur and "~\u2014" in chunk or "~—" in chunk:
            chunk = chunk.replace("\u23f1 ~\u2014", f"\u23f1 ~{dur}", 1).replace("⏱ ~—", f"⏱ ~{dur}", 1)
        n += 1
        out.append(chunk)
    return "".join(out), n

# re-do card fill robustly: iterate since positions shift
def fill_cards_iter(h):
    total = 0
    while True:
        h2, n = fill_cards(h)
        if n == 0: return h, total
        h = h2
        total += n

def append_faq_jsonld(h, kk):
    blocks = list(re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S))
    for m in blocks:
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        if d.get("@type") == "FAQPage":
            if any("WBTC" in (q.get("name") or "") for q in d.get("mainEntity", [])):
                continue  # already added
            d["mainEntity"].append(faq_jsonld(kk))
            new = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
            return h[:m.start(1)] + new + h[m.end(1):]
    return h

# ------------------------------------------------------------ new pages -----
NEW_PAGES = [  # (slug, from, to, data_key, extra_link_pairs)
    ("kolkata-to-krishnanagar", "Kolkata", "Krishnanagar", "Kolkata|Krishnanagar"),
    ("kolkata-to-mayapur", "Kolkata", "Mayapur ISKCON", "Kolkata|Mayapur ISKCON"),
    ("kolkata-to-medinipur", "Kolkata", "Midnapore", "Kolkata|Midnapore"),
    ("durgapur-to-kolkata-airport", "Durgapur", "Kolkata Airport", "Durgapur|Kolkata Airport"),
    ("medinipur-to-kolkata", "Midnapore", "Kolkata", "Midnapore|Kolkata"),
    ("medinipur-to-kolkata-airport", "Midnapore", "Kolkata Airport", "Midnapore|Kolkata Airport"),
    ("kharagpur-to-barasat", "Kharagpur (Chowrangee)", "Barasat", "Chowrangee|Barasat"),
    ("kharagpur-to-kolkata-airport", "Kharagpur (Chowrangee)", "Kolkata Airport", "Chowrangee|Kolkata Airport"),
    ("barasat-to-kolaghat", "Barasat", "Kolaghat", "Barasat|Kolaghat"),
    ("barasat-to-nandakumar", "Barasat", "Nandakumar", "Barasat|Nandakumar"),
    ("kolkata-airport-to-digha", "Kolkata Airport", "Digha", "Kolkata Airport|Digha"),
    ("asansol-to-kolkata-airport", "Asansol", "Kolkata Airport", "Asansol|Kolkata Airport"),
]

def slugify(x): return re.sub(r"[^a-z0-9]+", "-", x.lower()).strip("-")

def build_new_page(slug, frm, to, kk):
    base = (ROOT / "bus-time-table" / "barasat-to-durgapur.html").read_text(encoding="utf-8")
    f, t, buses, first, last, fare, dur, dist = WBTC_DATA[kk]
    bn_f = BN_PLACE.get(frm, frm); bn_t = BN_PLACE.get(to, to)
    title = f"{frm} to {to} Bus Time Table"
    desc = (f"{frm} to {to} WBTC bus time table — {buses} govt buses daily, first {t12(first)}, last {t12(last)}."
            + (f" Fare from {fare_str(fare)}." if fare else "")
            + (f" Journey ~{dur}." if dur else "") + " Timings and FAQs on BusJatri.")
    # head replacements
    h = base
    h = re.sub(r"<title>.*?</title>", f"<title>{title} | BusJatri</title>", h, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{desc}"', h)
    h = re.sub(r'<link rel="canonical" href="[^"]*"', f'<link rel="canonical" href="https://busjatri.in/bus-time-table/{slug}"', h)
    h = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{title} | BusJatri"', h)
    h = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{desc}"', h)
    h = re.sub(r'<meta property="og:url" content="[^"]*"', f'<meta property="og:url" content="https://busjatri.in/bus-time-table/{slug}"', h)
    # main content
    chips = [f'<span class="schip">🚌 {buses} <span class="label-en">govt buses daily</span><span class="label-bn">সরকারি বাস প্রতিদিন</span></span>',
             f'<span class="schip hot">⏰ <span class="label-en">First</span><span class="label-bn">প্রথম</span> {t12(first)}</span>',
             f'<span class="schip">🌙 <span class="label-en">Last</span><span class="label-bn">শেষ</span> {t12(last)}</span>']
    if fare: chips.append(f'<span class="schip">🎟 <span class="label-en">from</span><span class="label-bn">থেকে</span> {fare_str(fare)}</span>')
    if dur: chips.append(f'<span class="schip">⏱ ~{dur}</span>')
    if dist: chips.append(f'<span class="schip">🛣 {dist}</span>')
    main = f'''<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:860px">
  <div class="crumbs"><a href="../index.html"><span class="label-en">Home</span><span class="label-bn">হোম</span></a> › <a href="./"><span class="label-en">Bus Timetable</span><span class="label-bn">বাস টাইম টেবিল</span></a> › <span>{frm} → {to}</span></div>
  <div class="seo-hero">
    <h1>{frm} <span class="arr">→</span> {to}</h1>
    <p class="bn-sub"><span class="label-en">{frm} → {to} — WBTC government bus timings</span><span class="label-bn">{bn_f} থেকে {bn_t} সরকারি বাসের সময়সূচী</span></p>
    <div class="stat-chips">{''.join(chips)}</div>
  </div>
  <section class="seo-section">
    <h3 class="section-title"><span class="label-en">WBTC (CTC) Government Service</span><span class="label-bn">ডাব্লুবিটিসি (সিটিসি) সরকারি পরিষেবা</span></h3>
    <div class="bus-row">
      <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{t12(first)}</span></div></div>
      <div class="bmid">
        <div class="op">WBTC (CTC) <span style="color:var(--amber-ink,#6b4610);font-weight:600">· {frm} → {to}</span></div>
        <div class="mrow">{'⏱ ~' + dur + ' · ' if dur else ''}🚌 {buses} <span class="label-en">buses daily</span><span class="label-bn">টি বাস প্রতিদিন</span> · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> {t12(last)}</div>
      </div>
      <div class="bright"><span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span>{f'<span class="badge">from {fare_str(fare)}</span>' if fare else ''}</div>
    </div>
    <p class="bn-sub"><span class="label-en">Timings from the official WBTC/CTC listing on redBus. Buses run throughout the day — arrive 10 minutes early. Times can change; verify before travel.</span><span class="label-bn">সময়সূচি রেডবাসে তালিকাভুক্ত অফিসিয়াল ডাব্লুবিটিসি/সিটিসি থেকে। দিনভর বাস চলে — ১০ মিনিট আগে পৌঁছান। সময় বদলাতে পারে; যাত্রার আগে যাচাই করুন।</span></p>
  </section>
  <section class="seo-section">
    <h3 class="section-title"><span class="label-en">About this route</span><span class="label-bn">এই রুট সম্পর্কে</span></h3>
    <p class="bn-sub"><span class="label-en">WBTC (Calcutta State Transport Corporation) runs {buses} government buses daily from {frm} to {to}. The first bus leaves at {t12(first)} and the last at {t12(last)}{f", and the journey takes about {dur}" if dur else ""}{f" — a distance of {dist}" if dist else ""}.{f" Fares start from {fare_str(fare)}." if fare else ""} Government buses are a reliable, low-cost option on this route.</span><span class="label-bn">ডাব্লুবিটিসি (ক্যালকাটা স্টেট ট্রান্সপোর্ট কর্পোরেশন) {bn_f} থেকে {bn_t} প্রতিদিন {buses} টি সরকারি বাস চালায়। প্রথম বাস {t12(first)}-এ ছাড়ে, শেষ বাস {t12(last)}-এ। সরকারি বাস এই রুটে নির্ভরযোগ্য ও সাশ্রয়ী বিকল্প।</span></p>
  </section>
  <section class="seo-section">
    <h3 class="section-title"><span class="label-en">FAQs</span><span class="label-bn">সাধারণ প্রশ্ন</span></h3>
    <details class="faq only-en" open><summary>What is the first bus from {frm} to {to}?</summary><div class="fa-body">The first WBTC government bus departs at <b>{t12(first)}</b>. {buses} buses run daily on this route.</div></details>
    <details class="faq only-en"><summary>What is the last bus from {frm} to {to}?</summary><div class="fa-body">The last WBTC bus leaves at <b>{t12(last)}</b>. Arrive early — government buses depart on schedule.</div></details>
    <details class="faq only-en"><summary>What is the fare from {frm} to {to}?</summary><div class="fa-body">{f"Fares start from <b>{fare_str(fare)}</b> for the WBTC bus." if fare else "Check the fare with the conductor or WBTC counter."}{" The journey takes about " + dur + "." if dur else ""}</div></details>
    <details class="faq only-bn"><summary>{frm} থেকে {to} প্রথম বাস কখন?</summary><div class="fa-body">প্রথম ডাব্লুবিটিসি সরকারি বাস <b>{t12(first)}</b>-এ ছাড়ে। এই রুটে প্রতিদিন {buses} টি বাস চলে।</div></details>
    <details class="faq only-bn"><summary>{frm} থেকে {to} শেষ বাস কখন?</summary><div class="fa-body">শেষ বাস <b>{t12(last)}</b>-এ ছাড়ে। আগে পৌঁছে যান — সরকারি বাস সময় মেনে ছাড়ে।</div></details>
    <details class="faq only-bn"><summary>ভাড়া কত?</summary><div class="fa-body">{f"ভাড়া শুরু <b>{fare_str(fare)}</b> থেকে।" if fare else "কন্ডাক্টর বা ডাব্লুবিটিসি কাউন্টারে জেনে নিন।"}</div></details>
  </section>
</main>'''
    # splice: everything before <main ...> + new main + footer part
    # (indices computed on the FINAL string h, after head replacements)
    mi = h.find('<main class="container seo-main"')
    me = h.find('</main>')
    h = h[:mi] + main + h[me + len("</main>"):]
    # JSON-LD: replace the FAQPage and Dataset blocks
    h = re.sub(r'<script type="application/ld\+json">\s*\{[^<]*?"@type":\s*"FAQPage".*?</script>',
               '<script type="application/ld+json">' + json.dumps({
                   "@context": "https://schema.org", "@type": "FAQPage",
                   "mainEntity": [
                       {"@type": "Question", "name": f"What is the first bus from {frm} to {to}?",
                        "acceptedAnswer": {"@type": "Answer", "text": f"The first WBTC government bus departs at {t12(first)}. {buses} buses run daily."}},
                       {"@type": "Question", "name": f"What is the last bus from {frm} to {to}?",
                        "acceptedAnswer": {"@type": "Answer", "text": f"The last WBTC bus leaves at {t12(last)}."}},
                       {"@type": "Question", "name": f"What is the WBTC bus fare from {frm} to {to}?",
                        "acceptedAnswer": {"@type": "Answer", "text": (f"Fares start from {fare_str(fare)}." if fare else "Check with the conductor.") + (f" Journey takes about {dur}." if dur else "")}},
                   ]}, ensure_ascii=False, separators=(",", ":")) + '</script>', h, flags=re.S, count=1)
    h = re.sub(r'<script type="application/ld\+json">\s*\{[^<]*?"@type":\s*"Dataset".*?</script>',
               '<script type="application/ld+json">' + json.dumps({
                   "@context": "https://schema.org", "@type": "Dataset",
                   "name": f"{frm} to {to} WBTC Bus Timetable",
                   "description": desc, "creator": {"@type": "Organization", "name": "BusJatri"},
                   "isAccessibleForFree": True}, ensure_ascii=False, separators=(",", ":")) + '</script>', h, flags=re.S, count=1)
    return h

def main():
    changed = {}

    # ---- 1. global card fill on all route pages
    print("== 1. WBTC Time-N/A card fill ==")
    total_cards = 0; total_pages = 0
    for fp in sorted(glob.glob(str(ROOT / "bus-time-table" / "*.html"))):
        h = Path(fp).read_text(encoding="utf-8")
        if "Time N/A" not in h or "WBTC" not in h: continue
        h2, n = fill_cards_iter(h)
        if n:
            changed[fp] = h2; total_cards += n; total_pages += 1
    print(f"  cards filled: {total_cards} on {total_pages} pages")

    # ---- 2. WBTC section + FAQ on existing mapped pages
    print("== 2. WBTC route sections ==")
    fullmap = json.load(open(ROOT / "scripts" / "wbtc_fullmap.json")) if (ROOT / "scripts" / "wbtc_fullmap.json").exists() else None
    PAGEMAP = {
      "kolkata-to-digha.html": ("Kolkata", "Digha", "Kolkata|Digha"),
      "esplanade-to-digha.html": ("Esplanade", "Digha", "Kolkata|Digha"),
      "kolkata-to-durgapur.html": ("Kolkata", "Durgapur", "Kolkata|Durgapur"),
      "esplanade-to-durgapur.html": ("Esplanade", "Durgapur", "Kolkata|Durgapur"),
      "kolkata-to-asansol.html": ("Kolkata", "Asansol", "Kolkata|Asansol"),
      "esplanade-to-asansol.html": ("Esplanade", "Asansol", "Kolkata|Asansol"),
      "kolkata-to-suri.html": ("Kolkata", "Suri", "Kolkata|Suri"),
      "esplanade-to-suri.html": ("Esplanade", "Suri", "Kolkata|Suri"),
      "esplanade-to-bolpur.html": ("Esplanade", "Bolpur", "Kolkata|Bolpur"),
      "kolkata-to-purulia.html": ("Kolkata", "Purulia", "Kolkata|Purulia"),
      "esplanade-to-purulia.html": ("Esplanade", "Purulia", "Kolkata|Purulia"),
      "esplanade-to-bakkhali.html": ("Esplanade", "Bakkhali", "Kolkata|Bakkhali"),
      "esplanade-to-arambagh.html": ("Esplanade", "Arambagh", "Kolkata|Arambagh"),
      "digha-to-barasat.html": ("Digha", "Barasat", "Digha|Barasat"),
      "digha-to-barasat-chapadali.html": ("Digha", "Barasat Chapadali", "Digha|Barasat"),
      "durgapur-to-kolkata.html": ("Durgapur", "Kolkata", "Durgapur|Kolkata"),
      "durgapur-to-esplanade.html": ("Durgapur", "Esplanade", "Durgapur|Kolkata"),
      "medinipur-to-barasat.html": ("Midnapore", "Barasat", "Midnapore|Barasat"),
      "barasat-to-digha.html": ("Barasat", "Digha", "Barasat|Digha"),
      "barasat-chapadali-to-digha.html": ("Barasat Chapadali", "Digha", "Barasat|Digha"),
      "barasat-to-medinipur.html": ("Barasat", "Midnapore", "Barasat|Midnapore"),
      "barasat-to-contai.html": ("Barasat", "Contai", "Barasat|Contai"),
      "barasat-to-durgapur.html": ("Barasat", "Durgapur", "Barasat|Durgapur"),
      "barasat-chapadali-to-asansol.html": ("Barasat Chapadali", "Asansol", "Barasat|Asansol"),
      "digha-to-kolkata.html": ("Digha", "Kolkata", "Digha|Kolkata"),
      "digha-to-esplanade.html": ("Digha", "Esplanade", "Digha|Kolkata"),
      "habra-to-digha.html": ("Habra", "Digha", "Habra|Digha"),
      "kolkata-to-burdwan.html": ("Kolkata", "Burdwan", "Kolkata|Burdwan"),
    }
    nsec = 0
    for fname, (pf, pt, kk) in PAGEMAP.items():
        fp = ROOT / "bus-time-table" / fname
        if not fp.exists(): continue
        h = changed.get(str(fp)) or fp.read_text(encoding="utf-8")
        if "wbtc-long-v1" in h: continue
        # insert after the Today's Departures section close
        ti = h.find("Today's Departures")
        if ti < 0: print(f"  !! no TD anchor: {fname}"); continue
        se = h.find("</section>", ti)
        if se < 0: continue
        ins = se + len("</section>")
        h = h[:ins] + wbtc_section(kk, pf, pt) + h[ins:]
        h = append_faq_jsonld(h, kk)
        changed[str(fp)] = h; nsec += 1
    print(f"  sections added: {nsec}")

    # ---- 3. new pages
    print("== 3. new route pages ==")
    npg = 0
    for slug, frm, to, kk in NEW_PAGES:
        fp = ROOT / "bus-time-table" / f"{slug}.html"
        if fp.exists(): print(f"  -- exists: {slug}"); continue
        h = build_new_page(slug, frm, to, kk)
        changed[str(fp)] = h; npg += 1
    print(f"  pages created: {npg}")

    # ---- 4. sitemap
    print("== 4. sitemap ==")
    sp = ROOT / "sitemap.xml"
    sm = changed.get(str(sp)) or sp.read_text(encoding="utf-8")
    added = 0
    for slug, frm, to, kk in NEW_PAGES:
        url = f"https://busjatri.in/bus-time-table/{slug}"
        if url in sm: continue
        sm = sm.replace("</urlset>", f"<url><loc>{url}</loc><changefreq>weekly</changefreq><priority>0.7</priority></url></urlset>")
        added += 1
    if added: changed[str(sp)] = sm
    print(f"  sitemap urls added: {added}")

    # ---- 5. interlinks: add new pages to More Routes chip rows on related existing pages
    print("== 5. interlinks ==")
    LINKS = {
      "kolkata-to-digha.html": [("kolkata-to-krishnanagar.html", "Kolkata → Krishnanagar"), ("kolkata-to-mayapur.html", "Kolkata → Mayapur")],
      "esplanade-to-digha.html": [("kolkata-to-krishnanagar.html", "Kolkata → Krishnanagar")],
      "barasat-to-digha.html": [("barasat-to-kolaghat.html", "Barasat → Kolaghat"), ("barasat-to-nandakumar.html", "Barasat → Nandakumar")],
      "digha-to-kolkata.html": [("kolkata-airport-to-digha.html", "Kolkata Airport → Digha")],
      "durgapur-to-kolkata.html": [("durgapur-to-kolkata-airport.html", "Durgapur → Kolkata Airport")],
      "barasat-to-medinipur.html": [("barasat-to-kolaghat.html", "Barasat → Kolaghat")],
      "kolkata-to-durgapur.html": [("kolkata-to-mayapur.html", "Kolkata → Mayapur")],
      "kolkata-to-asansol.html": [("asansol-to-kolkata-airport.html", "Asansol → Kolkata Airport")],
      "esplanade-to-bolpur.html": [("kolkata-to-krishnanagar.html", "Kolkata → Krishnanagar")],
      "barasat-to-contai.html": [("barasat-to-kolaghat.html", "Barasat → Kolaghat")],
    }
    nl = 0
    for fname, links in LINKS.items():
        fp = ROOT / "bus-time-table" / fname
        if not fp.exists(): continue
        h = changed.get(str(fp)) or fp.read_text(encoding="utf-8")
        # find the LAST chip-row (More Buses to X section comes last)
        m = list(re.finditer(r'<div class="chip-row">', h))
        if not m: continue
        last = m[-1]
        add = "".join(f'<a class="rel-chip" href="{p}">{t}</a>' for p, t in links if f'href="{p}"' not in h)
        if not add:
            continue
        h = h[:last.end()] + add + h[last.end():]
        changed[str(fp)] = h; nl += 1
    print(f"  interlink rows patched: {nl}")

    print(f"\n== files changed: {len(changed)} ({'WRITE' if WRITE else 'DRY'}) ==")
    if DRY:
        for p in sorted(changed): print("  ~", Path(p).name)
        return
    for p, h in changed.items():
        Path(p).write_text(h, encoding="utf-8")
    print("done.")

if __name__ == "__main__":
    main()
