#!/usr/bin/env python3
"""
Stand page generator v3 — "X Bus Stand" destination cards + travel guide.

Demo-approved design (2026-09-22, Bankura final demo):
  1. Hero: "X Bus Stand" + Bengali subtitle + chips
     (buses listed / destinations / first / last)
  2. Search filter (filters cards + destination rows)
  3. Popular Routes: top-12 destination cards, time chips (max 8,
     "+N more times"), "N buses with Time N/A" note, route-page links
  4. All Destinations: big A-Z rows, 8 visible + "See more" (+8 per tap)
  5. Travel Guide (only for stands with curated content): attraction
     cards — real bus data from this timetable, Maps links, why go,
     best time, stay (Maps link, never fabricated names)
  6. FAQ: 5 English + 5 Bengali, data-driven
  7. Safe wording: "N buses listed", never "only N buses run";
     more services may exist — ask at the stand

Same URL as before: bus-time-table/buses-from-<slug>.html
(design change only, no page moves, no deletions).

Usage (run from repo root):
  python3 scripts/gen_stand_v2.py --stands "Kolkata,Digha,Bankura"
  python3 scripts/gen_stand_v2.py --all
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_route_v2 as v2

g = v2.g


# ------------------------------------------------------------
# stand discovery + bus list
# ------------------------------------------------------------

def stand_buses(stand):
    """Buses whose ORIGIN matches the stand (strict matcher + aliases,
    same as the homepage 'from' side). Stop-passing buses are not here."""
    return [b for b in g.BUSES if v2.place_matches_strict(b.get("origin"), stand)]


def discover_stands():
    """(display_name, filename) for every existing buses-from-*.html."""
    out = []
    for fname in sorted(os.listdir(g.OUT)):
        if not fname.startswith("buses-from-") or not fname.endswith(".html"):
            continue
        try:
            with open(os.path.join(g.OUT, fname), "r", encoding="utf-8", errors="ignore") as fh:
                head = fh.read(4000)
        except OSError:
            continue
        m = re.search(r"<title>(.*?)\s*[–\-]", head)
        name = m.group(1).strip() if m and m.group(1).strip() else fname[len("buses-from-"):-len(".html")].replace("-", " ").title()
        if name.lower().startswith("buses from "):
            name = name[len("buses from "):]
        name = re.sub(r"\s+bus stand$", "", name, flags=re.I)
        out.append((name, fname))
    return out


def display_name(stand):
    """"Bankura" -> "Bankura Bus Stand"; "Howrah Station" unchanged."""
    if re.search(r"\b(stand|station|depot|terminus)$", stand.strip(), re.I):
        return stand.strip()
    return stand.strip() + " Bus Stand"


# ------------------------------------------------------------
# destination grouping (merge alias names onto one route page)
# ------------------------------------------------------------

def destination_groups(stand, buses):
    """[dict(display, bn, count, times, na, link)] sorted by count desc.

    Each bus destination is resolved against the stand's route_meta pairs
    so 'Kolkata (Esplanade)' and 'Kolkata' merge into one group that
    links to the real route page. times = sorted unique departure times
    (minutes), na = buses in the group without a time.
    """
    routes = [t for (o, t) in g.route_meta if v2.place_matches_strict(o, stand)]
    groups = {}
    for b in buses:
        d = g.clean_text(b.get("destination")) or "?"
        resolved = None
        for t in routes:
            if v2.place_matches_strict(t, d) or v2.place_matches_strict(d, t):
                resolved = t
                break
        if resolved is not None:
            key = "file::" + g.slug(stand) + "-to-" + g.slug(resolved) + ".html"
            display = resolved
            link = "{}-to-{}.html".format(g.slug(stand), g.slug(resolved))
        else:
            key = "name::" + d.lower()
            display = d
            link = None
        if key not in groups:
            groups[key] = {"display": display, "link": link, "count": 0, "times": set(), "na": 0}
        grp = groups[key]
        grp["count"] += 1
        t = g.parse_time(b.get("departure_time"))
        if t is None:
            grp["na"] += 1
        else:
            grp["times"].add(t)
    out = list(groups.values())
    for grp in out:
        grp["times"] = sorted(grp["times"])
    out.sort(key=lambda x: (-x["count"], x["display"].lower()))
    return out


# ------------------------------------------------------------
# FAQ — 5 EN + 5 BN, search-intent questions, data-driven answers
# ------------------------------------------------------------

def faq_pairs_stand(stand, buses, dest_groups):
    disp = display_name(stand)
    stats = g.route_stats(buses)
    first, last = stats["first"], stats["last"]
    count = len(buses)
    operators = [o for o in stats["operators"] if o and o.strip() and o.strip() not in ("—", "-")]
    top = [d["display"] for d in dest_groups[:8]]
    p_bn = v2.bnplace(stand)

    def bus_at(minutes):
        best, best_bus = None, None
        for b in buses:
            t = g.parse_time(b.get("departure_time"))
            if t is None:
                continue
            if minutes is None or abs(t - minutes) < abs((best if best is not None else 99999) - minutes):
                best, best_bus = t, b
        return best_bus

    def dest_of(b):
        return g.clean_text(b.get("destination")) or "its destination"

    first_bus = bus_at(first) if first is not None else None
    last_bus = bus_at(last) if last is not None else None

    if count == 0:
        en = [
            ("Are there any buses from {}?".format(disp),
             "No bus services from {} are listed yet. More services may exist — ask at the stand, or check the route pages for nearby places.".format(disp)),
            ("How do I check bus timings from {}?".format(disp),
             "You can search any route on the BusJatri homepage, or open the route page for your destination — it lists every departure with stoppages."),
            ("Which places are connected to {} by bus?".format(disp),
             "Nearby stands and destinations are shown on the Bus Timetable index. Ask at the stand for the latest connections."),
            ("Which operators run buses from {}?".format(disp),
             "No operator is listed for {} yet. If you know a bus, you can contribute it on the Contribute a Bus page.".format(disp)),
            ("Is there a bus timetable app for {} buses?".format(stand),
             "BusJatri works in any mobile browser — search your route and get timings, stoppages and operators without installing anything."),
        ]
        bn = [
            ("{} থেকে কি কোনো বাস আছে?".format(p_bn),
             "এখনও {} থেকে কোনো বাস তালিকাভুক্ত নেই। আরও বাস থাকতে পারে — স্ট্যান্ডে জেনে নিন।".format(p_bn)),
            ("{} থেকে বাসের সময় কীভাবে জানব?".format(p_bn),
             "হোমপেজে যেকোনো রুট সার্চ করুন, বা গন্তব্যের রুট পেজ খুলুন।"),
            ("{} থেকে কোথায় কোথায় বাস যায়?".format(p_bn),
             "কাছের স্ট্যান্ড ও গন্তব্য বাস টাইম টেবিল ইনডেক্সে দেওয়া আছে।"),
            ("{} থেকে কোন সংস্থার বাস চলে?".format(p_bn),
             "এখনও কোনো অপারেটর তালিকাভুক্ত নেই। খবর জানা থাকলে Contribute a Bus পেজ থেকে জানান।"),
            ("বাসের সময়সূচি অ্যাপে পাওয়া যায়?",
             "BusJatri যেকোনো মোবাইল ব্রাউজারে চলে — কিছু ইনস্টল না করেই রুট সার্চ করা যায়।"),
        ]
        return en, bn

    en = []
    en.append(("What is the first bus from {}?".format(disp),
               "The first listed departure from {} is at {} — {}, to {}. Buses often leave once seats fill up, so arrive a little early.".format(
                   disp, g.format_time(first), g.clean_text(first_bus.get("bus_name")) or "a bus service", dest_of(first_bus))))
    en.append(("What is the last bus from {}?".format(disp),
               "The last listed departure is {} — {}, to {}. More services may exist, so ask at the stand.".format(
                   g.format_time(last), g.clean_text(last_bus.get("bus_name")) or "a bus service", dest_of(last_bus))))
    en.append(("How many buses start from {} daily?".format(disp),
               "{} buses are listed starting from {}, serving {} destinations. More services may exist — ask at the stand.".format(
                   count, disp, len(dest_groups))))
    if top:
        en.append(("Which places can I go from {} by bus?".format(disp),
                   "From {} you can travel to {} — the full destination list with bus counts is on this page.".format(
                       disp, ", ".join(top[:6]) + (" and others" if len(top) > 6 else ""))))
    else:
        en.append(("Where does the bus from {} go?".format(disp),
                   "Destinations from {} are shown on this page with bus counts.".format(disp)))
    if operators:
        en.append(("Which operators run buses from {}?".format(disp),
                   "Listed services include {}. Government (SBSTC/NBSTC/WBTC) and private buses both serve this stand.".format(
                       ", ".join(operators[:4]) + (" and others" if len(operators) > 4 else ""))))
    else:
        en.append(("Do government buses run from {}?".format(disp),
                   "Operator details are not listed for every service. Ask at the stand for the latest SBSTC/NBSTC/WBTC and private bus information."))

    bn = []
    bn.append(("{} থেকে প্রথম বাস কখন ছাড়ে?".format(p_bn),
               "তালিকা অনুযায়ী প্রথম বাস ছাড়ে {} — {}, {} যায়। সিটের জন্য একটু আগে গিয়ে অপেক্ষা করাই ভালো।".format(
                   v2.bn_time(first), g.clean_text(first_bus.get("bus_name")) or "একটি বাস", v2.bnplace(dest_of(first_bus)))))
    bn.append(("{} থেকে দিনের শেষ বাস কতক্ষণে?".format(p_bn),
               "তালিকায় শেষ বাস {} — {}, {} যায়। এর পরেও আরও বাস থাকতে পারে, স্ট্যান্ডে জেনে নিন।".format(
                   v2.bn_time(last), g.clean_text(last_bus.get("bus_name")) or "একটি বাস", v2.bnplace(dest_of(last_bus)))))
    bn.append(("{} থেকে দিনে কতটি বাস ছাড়ে?".format(p_bn),
               "তালিকায় {}টি বাস, {}টি গন্তব্যে। আরও বাস থাকতে পারে, স্ট্যান্ডে জেনে নিন।".format(
                   v2.bn_num(count), v2.bn_num(len(dest_groups)))))
    if top:
        bn.append(("{} থেকে কোথায় কোথায় বাস যায়?".format(p_bn),
                   "{} থেকে যাওয়া যায় {} জায়গায় — বাসের সংখ্যাসহ পুরো তালিকা এই পেজেই দেওয়া আছে।".format(
                       p_bn, ", ".join(v2.bnplace(t) for t in top[:6]) + (" প্রভৃতি" if len(top) > 6 else ""))))
    else:
        bn.append(("{} থেকে বাস কোথায় যায়?".format(p_bn),
                   "{} থেকে যাওয়া গন্তব্যগুলি বাসের সংখ্যাসহ এই পেজে দেওয়া আছে।".format(p_bn)))
    if operators:
        bn.append(("{} থেকে কোন কোন সংস্থার বাস চলে?".format(p_bn),
                   "তালিকায় আছে {}। সরকারি (SBSTC/NBSTC/WBTC) ও বেসরকারি দুই ধরনের বাসই চলে।".format(
                       ", ".join(operators[:4]) + (" প্রভৃতি" if len(operators) > 4 else ""))))
    else:
        bn.append(("{} থেকে সরকারি বাস আছে?".format(p_bn),
                   "সব বাসের অপারেটর তালিকাভুক্ত নয়। সাম্প্রতিক খবর স্ট্যান্ডে জেনে নিন।"))
    return en[:5], bn[:5]


# ------------------------------------------------------------
# travel guides — curated content, REAL bus data only
# ------------------------------------------------------------

def _maps(query):
    return "https://www.google.com/maps/search/?api=1&query=" + query.replace(" ", "+")


GUIDES = {
    "bankura": {
        "intro": "Bankura ke aas-paas",
        "note": "🚉 <b>Rail:</b> Bankura Junction (Howrah–Adra line) · 🛣️ <b>Road:</b> NH-14 to Durgapur/Asansol, SH to Bishnupur–Purulia.",
        "cards": [
            {"icon": "🛕", "name": "Bishnupur", "bn": "বিষ্ণুপুর",
             "desc": "Terracotta temple town of the Malla kings — Rasmancha, Jorbangla and more",
             "bus": "🚌 <b>MUNMUN</b> 8:00 AM · <b>MAA MANASA</b> 9:40 AM — direct from this stand",
             "maps": "Bishnupur+temples+Bankura",
             "why": "terracotta temples, Baluchari sarees, temple architecture walk",
             "when": "October–March, start morning",
             "stay": "hotels+in+Bishnupur+Bankura"},
            {"icon": "🏞️", "name": "Mukutmanipur", "bn": "মুকুটমণিপুর",
             "desc": "Kangsabati dam — one of Bengal's biggest water reservoirs, boat rides at sunset",
             "bus": "🚌 <b>SOUMEN</b> (Ambika Nagar route) — reaches Mukutmanipur 2:15 PM, returns 3:50 PM",
             "maps": "Mukutmanipur+dam",
             "why": "dam viewpoint, boat ride, river confluence (Kangsabati + Kumari)",
             "when": "October–February, afternoon for sunset",
             "stay": "tourist+lodge+Mukutmanipur"},
            {"icon": "🌿", "name": "Susunia", "bn": "শুশুনিয়া",
             "desc": "Hill with a natural spring, ancient rock inscription and rock climbing",
             "bus": "🚌 <b>BABA LOKENATH</b> (Asansol route) — get off at Susunia Hill stop",
             "maps": "Susunia+Hill+Bankura",
             "why": "hill trek, spring water, rock climbing, green forest",
             "when": "October–February, go early morning",
             "stay": None, "stay_extra": "Day trip from Bankura — {LINK}",
             "stay_link": "hotels+in+Bankura+town", "stay_text": "stay in town"},
            {"icon": "⛰️", "name": "Ajodhya Hills", "bn": "অযোধ্যা পাহাড়",
             "desc": "Purulia's hill spot — waterfalls, forests and tribal villages",
             "bus": "🚆 No listed bus from this stand — take a train to Jhalda, then local transport (or ask at the stand)",
             "maps": "Ajodhya+Hills+Purulia",
             "why": "Upper & Lower falls, hill viewpoints, peaceful forest roads",
             "when": "September–February; monsoon for the falls",
             "stay": "stay+Ajodhya+Hills+Purulia"},
        ],
    },
    "kolkata": {
        "intro": "Kolkata se weekend spots",
        "note": "🚉 <b>Rail:</b> Howrah & Sealdah — India's biggest rail hub · 🛣️ <b>Road:</b> NH-16 (Kharagpur) and NH-19 (Dhanbad) start here.",
        "cards": [
            {"icon": "🏖️", "name": "Digha", "bn": "দীঘা",
             "desc": "Bengal's favourite sea beach — 3-4 hours from the city",
             "bus": "🚌 <b>37 buses listed</b> direct — first SBSTC 4:30 AM, BAROMA 6:30 AM, JACKSON 8:00 AM, AC coaches available",
             "maps": "New+Digha+beach",
             "why": "sea beach, marine aquarium & science centre, seafood, sunrise",
             "when": "October–February",
             "stay": "hotels+in+New+Digha"},
            {"icon": "🌊", "name": "Mandarmani & Shankarpur", "bn": "মন্দারমণি",
             "desc": "Long driveable beach with red crabs — quieter than Digha",
             "bus": "🚌 <b>SANTOSH BUS SERVICE</b> 6:00 AM — direct Kolkata–Mandarmani and Kolkata–Shankarpur",
             "maps": "Mandarmani+beach",
             "why": "longest motorable beach drive, red crab colonies, casuarina groves",
             "when": "October–February",
             "stay": "hotels+in+Mandarmani"},
            {"icon": "🛕", "name": "Bishnupur", "bn": "বিষ্ণুপুর",
             "desc": "Terracotta temple town of the Malla kings — a day full of history",
             "bus": "🚌 <b>NOOR TRAVELS</b> 4:30 AM · <b>SBSTC</b> 9:30 AM — direct from Kolkata",
             "maps": "Bishnupur+temples+Bankura",
             "why": "Rasmancha, Jorbangla, Madan Mohan temple, Baluchari sarees",
             "when": "October–March",
             "stay": "hotels+in+Bishnupur+Bankura"},
            {"icon": "🎓", "name": "Shantiniketan", "bn": "শান্তিনিকেতন",
             "desc": "Tagore's university town — Visva-Bharati, Sonajhuri haat",
             "bus": "🚆 Only one bus is listed (time not in timetable) — Howrah→Bolpur trains are frequent; or ask at the stand",
             "maps": "Shantiniketan+Bolpur",
             "why": "Visva-Bharati campus, Sonajhuri forest haat, Tagore heritage",
             "when": "October–March (Poush Mela in December)",
             "stay": "hotels+in+Bolpur+Shantiniketan"},
        ],
    },
    "digha": {
        "intro": "Digha ke aas-paas",
        "note": "🚉 <b>Rail:</b> direct trains from Howrah (check timings) · 🛣️ <b>Road:</b> Kolaghat–Nandakumar–Contai route, about 4 hours from Kolkata. Return: 18 buses listed to Kolkata, first 4:30 AM, last 10:00 PM.",
        "cards": [
            {"icon": "🏖️", "name": "New Digha Beach", "bn": "নিউ দীঘা বীচ",
             "desc": "The main beach — flat, walkable, sunrise point",
             "bus": "🚶 The beach is a short walk or cycle-van ride from the stand",
             "maps": "New+Digha+beach",
             "why": "sea breeze, marine aquarium & science centre, street food stalls",
             "when": "October–February; early morning for sunrise",
             "stay": "hotels+in+New+Digha"},
            {"icon": "🛕", "name": "Chandaneswar Temple", "bn": "চন্ডনেশ্বর মন্দির",
             "desc": "Old Shiva temple, 4 km from Digha — Baba Taraknath route",
             "bus": "🚌 Local vans and buses run from the stand — not yet in the timetable, ask at the stand",
             "maps": "Chandaneswar+Temple+Digha",
             "why": "centuries-old temple, morning aarti, small weekly haat",
             "when": "Year-round; mornings are best",
             "stay": None, "stay_extra": "Day trip from Digha — {LINK}",
             "stay_link": "hotels+in+New+Digha", "stay_text": "stay in Digha"},
            {"icon": "🌊", "name": "Talsari & Udaipur Beach", "bn": "তালসারি",
             "desc": "River-mouth beach with red crabs — olive ridley turtles nest here in season",
             "bus": "🚌 Local transport from the stand (about 10 km) — ask at the stand",
             "maps": "Talsari+Beach+Udaipur",
             "why": "backwaters, quiet beach, boat rides on the river mouth",
             "when": "October–March",
             "stay": "stay+Talsari+Odisha+border"},
            {"icon": "🚙", "name": "Mandarmani", "bn": "মন্দারমণি",
             "desc": "Long motorable beach with red crabs — the quieter Digha",
             "bus": "🚌 Kolkata-bound buses via Contai stop at Kanthi (e.g. <b>SOHANA PARIBAHAN</b>, Kanthi stop 7:20 AM) — from Contai take local transport",
             "maps": "Mandarmani+beach",
             "why": "beach drive, casuarina groves, watersports",
             "when": "October–February",
             "stay": "hotels+in+Mandarmani"},
        ],
    },
}


# ------------------------------------------------------------
# page template (self-contained: inline CSS + JS, dark mode)
# ------------------------------------------------------------

CSS = """:root{--amber:#b8791f;--amber2:#8a5a12;--bg:#fffcf4;--ink:#211c16;--mut:#7a6a4f;--line:#e8dfc8;--card:#fffdf8;--chipbg:#faf1dd}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}
body.dark{--bg:#17130c;--ink:#f3e8d2;--mut:#b8a480;--line:#3a3222;--card:#221c11;--chipbg:#33290f}
.wrap{max-width:760px;margin:0 auto;padding:14px 14px 60px}
header{display:flex;justify-content:space-between;align-items:center;padding:14px 2px}
.logo{font-size:22px;font-weight:900;text-decoration:none;color:inherit}.logo em{color:var(--amber);font-style:normal}
.pills{display:flex;gap:8px;align-items:center;font-size:12px;font-weight:700}
.pill{border:1.5px solid var(--line);border-radius:999px;padding:5px 12px;cursor:pointer}
.crumbs{font-size:12px;color:var(--mut);margin:6px 0 14px}.crumbs a{color:var(--mut)}
.hero{background:linear-gradient(135deg,var(--amber) 0%,var(--amber2) 100%);border-radius:18px;padding:26px 20px;color:#fff;margin-bottom:14px}
.hero h1{font-size:30px;letter-spacing:-.5px;line-height:1.15}
.hero .hbn{font-size:15px;opacity:.92;margin-top:4px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.schip{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:6px 13px;font-size:12.5px;font-weight:700}
.schip.hot{background:#fff;color:var(--amber2)}
.search{display:flex;gap:8px;margin:0 0 18px}
.search input{flex:1;border:1.5px solid var(--line);background:var(--card);color:var(--ink);border-radius:12px;padding:12px 14px;font-size:15px;font-weight:600;outline:none}
.sec{margin:22px 0 10px;display:flex;align-items:baseline;justify-content:space-between}
.sec h3{font-size:17px}.sec .bn{font-size:12px;color:var(--mut);margin-left:8px}
.dgrid{display:grid;grid-template-columns:1fr;gap:10px}
@media(min-width:560px){.dgrid{grid-template-columns:1fr 1fr}}
.dcard{display:block;background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:14px;text-decoration:none;color:inherit;transition:transform .15s,border-color .15s}
.dcard:hover{transform:translateY(-2px);border-color:var(--amber)}
.dhead{display:flex;justify-content:space-between;align-items:center}
.dname{font-size:16.5px;font-weight:800}.dbn{font-size:12.5px;color:var(--mut);font-weight:600;margin-left:6px}
.dcount{font-size:12px;color:var(--amber2);font-weight:700;margin-top:2px}
body.dark .dcount{color:var(--amber)}
.arr{font-size:22px;color:var(--mut)}
.dtimes{margin-top:10px;display:flex;flex-wrap:wrap;gap:6px}
.tchip{background:var(--chipbg);border:1px solid var(--line);border-radius:8px;padding:4px 9px;font-size:13px;font-weight:800;font-variant-numeric:tabular-nums}
.tmore{font-size:12px;color:var(--mut);align-self:center}
.ntime{margin-top:8px;font-size:11.5px;color:var(--mut)}
.mgrid{display:grid;grid-template-columns:1fr;gap:9px}
@media(min-width:520px){.mgrid{grid-template-columns:1fr 1fr}}
.mcard{display:flex;justify-content:space-between;align-items:center;background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:12px 14px;text-decoration:none;color:inherit}
.mcard:hover{border-color:var(--amber);transform:translateY(-1px)}
.mname{font-size:14.5px;font-weight:800}.mbn{font-size:11px;color:var(--mut);margin-left:4px}
.mmeta{font-size:12px;color:var(--mut);margin-top:2px}
.note{background:var(--chipbg);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:13px;color:var(--mut);margin:18px 0}
.morebtn{display:block;width:100%;margin-top:12px;border:1.5px dashed var(--amber);background:transparent;color:var(--amber2);border-radius:12px;padding:11px;font-size:14px;font-weight:800;cursor:pointer}
body.dark .morebtn{color:var(--amber)}
details.faq{background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:13px 15px;margin-bottom:8px}
details.faq summary{font-weight:700;font-size:14px;cursor:pointer}
details.faq p{margin-top:8px;font-size:13.5px;color:var(--mut)}
.tg-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:480px){.tg-grid{grid-template-columns:1fr}}
.tg-card{background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:13px}
.tg-ico{font-size:22px}
.tg-name{font-weight:800;font-size:14.5px;margin-top:4px}
.tg-bn{font-size:11.5px;color:var(--mut);font-weight:600;margin-left:4px}
.tg-desc{font-size:12.5px;color:var(--mut);margin-top:4px}
.tg-rows{margin-top:9px;display:grid;gap:6px}
.tg-row{font-size:12.5px;color:var(--mut);background:var(--chipbg);border:1px solid var(--line);border-radius:10px;padding:7px 10px;line-height:1.45}
.tg-row b{color:var(--ink)}
.tg-row a{color:var(--amber2);font-weight:700;text-decoration:none;border-bottom:1px dashed var(--amber2)}
body.dark .tg-row a{color:var(--amber)}
.tg-note{background:var(--chipbg);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:13px;color:var(--mut);margin-top:10px}
footer{margin-top:30px;border-top:1px solid var(--line);padding-top:14px;font-size:12px;color:var(--mut);text-align:center}
footer a{color:var(--mut);margin:0 6px}"""

JS = """var mstep=8;
function mcards(){return Array.prototype.slice.call(document.querySelectorAll('#minis .mcard'));}
function mrefresh(){
  var cs=mcards();var shown=cs.filter(function(c){return c.style.display!=='none';}).length;
  var b=document.getElementById('mmore');
  if(!b){return;}
  if(shown>=cs.length){b.style.display='none';}else{b.style.display='';b.textContent='See more ('+(cs.length-shown)+' destinations remaining)';}
  document.getElementById('mcnt').textContent=shown+' of '+cs.length;
}
function showMoreDest(){
  var cs=mcards();var shown=cs.filter(function(c){return c.style.display!=='none';}).length;
  var nxt=Math.min(shown+mstep,cs.length);
  cs.forEach(function(c,i){c.style.display=i<nxt?'':'none';});
  mrefresh();
}
mcs=mcards();mcs.forEach(function(c,i){c.style.display=i<mstep?'':'none';});
mrefresh();
function fil(){var q=document.getElementById('q').value.toLowerCase().trim();document.querySelectorAll('#cards .dcard,#minis .mcard').forEach(function(c){c.style.display=!q||c.textContent.toLowerCase().indexOf(q)>-1?'':'none';});}"""


def _head(title, description, canonical):
    return """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{ogimg}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
{schema}
<style>{css}</style></head>""".format(
        title=g.esc(title), desc=g.esc(description), canon=g.esc(canonical),
        ogimg=g.BASE + "/og-image.png", schema="{schema}", css=CSS)


def _popular_card(grp):
    times = grp["times"][:8]
    chips = "".join('<span class="tchip">{}</span>'.format(g.esc(g.format_time(t))) for t in times)
    if len(grp["times"]) > 8:
        chips += '<span class="tmore">+{} more times</span>'.format(len(grp["times"]) - 8)
    na = ""
    if grp["na"]:
        na = '<div class="ntime">⏱ {} bus{} with Time N/A</div>'.format(grp["na"], "es" if grp["na"] > 1 else "")
    bn = v2.bnplace(grp["display"])
    bn_span = ' <span class="dbn">{}</span>'.format(g.esc(bn)) if bn and bn != grp["display"] else ""
    href = grp["link"] if grp["link"] else "#minis"
    return """<a class="dcard" href="{href}">
  <div class="dhead"><div><div class="dname">{name}{bn}</div>
  <div class="dcount">{n} buses listed</div></div><span class="arr">›</span></div>
  <div class="dtimes">{chips}</div>
  {na}
</a>""".format(href=g.esc(href), name=g.esc(grp["display"]), bn=bn_span,
               n=grp["count"], chips=chips, na=na)


def _mini_card(grp):
    first = g.format_time(grp["times"][0]) if grp["times"] else "—"
    bn = v2.bnplace(grp["display"])
    bn_span = ' <span class="mbn">{}</span>'.format(g.esc(bn)) if bn and bn != grp["display"] else ""
    href = grp["link"] if grp["link"] else "#cards"
    return """<a class="mcard" href="{href}">
  <div class="mname">{name}{bn}</div>
  <div class="mmeta"><b>{n}</b> buses · from {first}</div>
</a>""".format(href=g.esc(href), name=g.esc(grp["display"]), bn=bn_span,
               n=grp["count"], first=g.esc(first))


def _guide_section(slug, disp):
    guide = GUIDES.get(slug)
    if not guide:
        return ""
    cards = []
    for c in guide["cards"]:
        if c.get("stay"):
            stay_row = '🏨 <a href="{u}" target="_blank" rel="nofollow">Stay options on Maps</a>'.format(u=_maps(c["stay"]))
        else:
            stay_row = "🏨 " + c["stay_extra"].replace("{LINK}", '<a href="{u}" target="_blank" rel="nofollow">{t}</a>'.format(u=_maps(c["stay_link"]), t=c["stay_text"]))
        cards.append("""<div class="tg-card">
  <div class="tg-ico">{ico}</div>
  <div class="tg-name">{name} <span class="tg-bn">{bn}</span></div>
  <div class="tg-desc">{desc}</div>
  <div class="tg-rows">
    <div class="tg-row">{bus}</div>
    <div class="tg-row">🗺️ <a href="{maps}" target="_blank" rel="nofollow">Open in Google Maps</a></div>
    <div class="tg-row">⭐ Why go: {why}</div>
    <div class="tg-row">🕐 Best time: {when}</div>
    <div class="tg-row">{stay}</div>
  </div>
</div>""".format(ico=c["icon"], name=g.esc(c["name"]), bn=g.esc(c["bn"]),
                 desc=g.esc(c["desc"]), bus=c["bus"],
                 maps=_maps(c["maps"]), why=g.esc(c["why"]), when=g.esc(c["when"]),
                 stay=stay_row))
    return """<div class="sec"><h3>Travel Guide <span class="bn">ভ্রমণ গাইড</span></h3><span style="font-size:12px;color:var(--mut)">{intro}</span></div>
<div class="tg-grid">{cards}</div>
<div class="tg-note">{note}</div>""".format(intro=g.esc(guide["intro"]), cards="".join(cards), note=guide["note"])


def generate_stand_page_v2(stand):
    filename = "buses-from-{}.html".format(g.slug(stand))
    disp = display_name(stand)
    buses = stand_buses(stand)
    dest_groups = destination_groups(stand, buses)
    stats = g.route_stats(buses)
    first, last = stats["first"], stats["last"]
    count = len(buses)

    title = "{} – Bus Time Table | বাস সময়সূচী | {}".format(disp, g.SITE_NAME)
    if count == 0:
        description = "Bus services from {} — destinations, operators and timetable information on {}.".format(disp, g.SITE_NAME)
    else:
        description = "{} — {} buses listed to {} destinations".format(disp, count, len(dest_groups))
        if first is not None:
            description += ", first {}, last {}".format(g.format_time(first), g.format_time(last))
        description += ". Popular routes, all destinations and FAQs on {}.".format(g.SITE_NAME)
    description = description[:300]
    canonical = "{}/bus-time-table/{}".format(g.BASE, filename)

    # ---- hero chips ----
    if count == 0:
        chips = '<span class="schip">🚌 No buses listed yet</span>'
    else:
        chips = ('<span class="schip">🚌 {} buses listed</span>'.format(count)
                 + '<span class="schip">📍 {} destinations</span>'.format(len(dest_groups))
                 + ('<span class="schip hot">⏰ First {}</span>'.format(g.esc(g.format_time(first))) if first is not None else "")
                 + ('<span class="schip hot">⏰ Last {}</span>'.format(g.esc(g.format_time(last))) if last is not None else ""))

    # ---- popular routes (top 12) + all destinations (rest, A-Z) ----
    popular = dest_groups[:12]
    rest = sorted(dest_groups[12:], key=lambda x: x["display"].lower())
    cards_html = "".join(_popular_card(grp) for grp in popular)
    minis_html = "".join(_mini_card(grp) for grp in rest)
    if rest:
        all_section = """<div class="sec"><h3>All Destinations <span class="bn">সব গন্তব্য</span></h3><span style="font-size:12px;color:var(--mut)" id="mcnt"></span></div>
<div class="mgrid" id="minis">{minis}</div>
<button class="morebtn" id="mmore" onclick="showMoreDest()"></button>""".format(minis=minis_html)
        popular_section = """<div class="sec"><h3>Popular Routes <span class="bn">জনপ্রিয় রুট</span></h3></div>
<div class="dgrid" id="cards">{cards}</div>""".format(cards=cards_html)
    else:
        popular_section = """<div class="sec"><h3>All Destinations <span class="bn">সব গন্তব্য</span></h3></div>
<div class="dgrid" id="cards">{cards}</div>""".format(cards=cards_html)
        all_section = '<div class="mgrid" id="minis"></div>'

    note = ('📍 Only buses <b>starting from {}</b> are shown here. For buses that pass through, '
            'see the route pages. More services may exist — ask at the stand.'.format(g.esc(disp)))

    # ---- FAQ ----
    en, bn = faq_pairs_stand(stand, buses, dest_groups)
    faq_html = "".join('<details class="faq"><summary>{}</summary><p>{}</p></details>'.format(g.esc(q), g.esc(a)) for q, a in en)
    faq_html += "".join('<details class="faq"><summary class="bn">📌 {}</summary><p>{}</p></details>'.format(q, a) for q, a in bn)
    faq_section = '<div class="sec"><h3>FAQ <span class="bn">প্রশ্নোত্তর</span></h3></div>' + faq_html

    guide_section = _guide_section(g.slug(stand), disp)

    body = """<div class="wrap">
<header><a class="logo" href="../index.html">Bus<em>Jatri</em></a>
<div class="pills"><span class="pill" onclick="document.body.classList.toggle('dark')">🌙 Dark</span></div></header>
<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">Bus Timetable</a> › <b>{disp}</b></div>
<div class="hero">
  <h1>{disp}</h1>
  <div class="hbn">{bn} — ছাড়ার সময়সূচি</div>
  <div class="chips">{chips}</div>
</div>
<div class="search"><input id="q" type="text" placeholder="🔎 Destination khojo — jaise 'Purulia', 'Kolkata'…" oninput="fil()"></div>
{popular}
{allsec}
<div class="note">{note}</div>
{guide}
{faq}
<footer>{disp} · {n} listed buses · {d} destinations (alias-merged) · <a href="../about.html">About</a><a href="../contribute.html">Contribute</a><a href="../blog/">Blog</a><a href="../privacy-policy.html">Privacy</a></footer>
</div>
<script>{js}</script>
</body></html>""".format(disp=g.esc(disp), bn=g.esc(v2.bnplace(stand)), chips=chips,
                         popular=popular_section, allsec=all_section, note=note,
                         guide=guide_section, faq=faq_section,
                         n=count, d=len(dest_groups), js=JS)

    schema = (g.faq_schema(en + bn) + "\n"
              + g.breadcrumb_schema([
                  ("Home", "/"),
                  ("Bus Timetable", "/bus-time-table/"),
                  (disp, "/bus-time-table/" + filename),
              ]))

    return filename, _head(title, description, canonical).replace("{schema}", schema) + body


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--stands", help="comma list of stand names, e.g. Kolkata,Digha,Khatra")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry", action="store_true", help="report only, don't write")
    args = ap.parse_args()

    known = discover_stands()
    print("loaded {} buses, {} existing stand pages".format(len(g.BUSES), len(known)))

    if args.all:
        targets = [(name, "buses-from-{}.html".format(g.slug(name))) for name, _f in known]
    else:
        wanted = [x.strip() for x in (args.stands or "").split(",") if x.strip()]
        by_slug = {g.slug(name): (name, fname) for name, fname in known}
        targets = []
        for w in wanted:
            hit = by_slug.get(g.slug(w))
            if not hit:
                print("SKIP (no existing stand page): {}".format(w))
                continue
            targets.append(hit)

    for stand, fname in targets:
        filename, page = generate_stand_page_v2(stand)
        assert filename == fname, "filename mismatch: {} != {}".format(filename, fname)
        buses = stand_buses(stand)
        groups = destination_groups(stand, buses)
        total = sum(grp["count"] for grp in groups)
        print("{}: {} buses, {} dest groups (sum {}), size {}KB".format(
            filename, len(buses), len(groups), total, len(page) // 1024))
        if not args.dry:
            with open(os.path.join(g.OUT, filename), "w", encoding="utf-8") as fh:
                fh.write(page)

    print("\ndone: {} stand pages".format(len(targets)))


if __name__ == "__main__":
    main()
