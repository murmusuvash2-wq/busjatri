#!/usr/bin/env python3
"""
Stand page generator v3 — "X Bus Stand" destination cards + travel guide.

Demo-approved design (2026-09-22/23, Bankura final demo + homepage parity):
  1. SAME look as the homepage: colours, sticky header (logo + theme +
     EN/বাংলা language buttons), fadeUp animation, dark mode via
     data-theme + localStorage (bj-theme / bj-lang, shared with homepage)
  2. Hero: "X Bus Stand" + Bengali subtitle + stat chips
  3. Popular Routes: top-12 destination cards, time chips (max 8),
     "+N more times", "N buses with Time N/A" note, route-page links
  4. All Destinations: big A-Z rows + HOMEPAGE-STYLE search box,
     8 visible + "See more" (+8 per tap)
  5. Travel Guide: only attractions that BELONG to this stand's area
     (Bishnupur on Bankura, Ajodhya on Purulia — never mixed around);
     real bus data from this timetable, Maps links, never fabricated names
  6. FAQ: 5 English + 5 Bengali (language buttons switch them)
  7. Safe wording: "N buses listed", never "only N buses run"

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
L = v2.L
bn_num = v2.bn_num


# ------------------------------------------------------------
# stand discovery + bus list
# ------------------------------------------------------------

def stand_buses(stand):
    """Buses whose ORIGIN matches the stand (strict matcher + aliases,
    same as the homepage 'from' side). Stop-passing buses are not here."""
    key = g.slug(stand)
    if key in UMBRELLA:
        names = set(n.strip().lower() for n in UMBRELLA[key][1])
        out = []
        for b in g.BUSES:
            o = (g.clean_text(b.get("origin")) or "").strip().lower()
            if o in names:
                out.append(b)
        return out
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
        # If the stripped name maps to a DIFFERENT file, trust the filename:
        # e.g. buses-from-garia-bus-stand.html is the "Garia Bus Stand" page,
        # not the alias-merged "Garia" (Kolkata group) page.
        base = fname[len("buses-from-"):-len(".html")]
        if g.slug(name) != base:
            name = base.replace("-", " ").title()
        out.append((name, fname))
    return out


# Kolkata-area stands shown as umbrella entries Kolkata (<stand>).
# filename-base -> (display name, exact origin names whose buses belong)
UMBRELLA = {
    "kolkata": ("Kolkata (Esplanade)", ("kolkata", "esplanade")),
    "karunamoyee": ("Kolkata (Karunamoyee)", ("karunamoyee",)),
    "santragachi": ("Kolkata (Santragachi)", ("santragachi",)),
}

def card_name(stand):
    """Card/label name for a stand (umbrella display for Kolkata area)."""
    key = g.slug(stand)
    if key in UMBRELLA:
        return UMBRELLA[key][0]
    return stand

def display_name(stand):
    """"Bankura" -> "Bankura Bus Stand"; "Howrah Station" unchanged."""
    key = g.slug(stand)
    if key in UMBRELLA:
        return UMBRELLA[key][0]
    if re.search(r"\b(stand|station|depot|terminus)$", stand.strip(), re.I):
        return stand.strip()
    return stand.strip() + " Bus Stand"


# ------------------------------------------------------------
# destination grouping (merge alias names onto one route page)
# ------------------------------------------------------------

def destination_groups(stand, buses):
    """[dict(display, count, times, na, link)] sorted by count desc.

    Each bus destination is resolved against the stand's route_meta pairs
    so 'Kolkata (Esplanade)' and 'Kolkata' merge into one group that
    links to the real route page. times = sorted unique departure times
    (minutes), na = buses in the group without a time.
    """
    routes = [(o, t) for (o, t) in g.route_meta if v2.place_matches_strict(o, stand)]
    groups = {}
    for b in buses:
        d = g.clean_text(b.get("destination")) or "?"
        resolved = None
        origin = None
        bo = (g.clean_text(b.get("origin")) or "").lower()
        for o, t in routes:
            if o.strip().lower() == bo and (v2.place_matches_strict(t, d) or v2.place_matches_strict(d, t)):
                resolved = t
                origin = o
                break
        if resolved is None:
            for o, t in routes:
                if v2.place_matches_strict(t, d) or v2.place_matches_strict(d, t):
                    resolved = t
                    origin = o
                    break
        if resolved is not None:
            key = "file::" + g.slug(origin) + "-to-" + g.slug(resolved) + ".html"
            display = resolved
            link = "{}-to-{}.html".format(g.slug(origin), g.slug(resolved))
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
    if first is not None and first_bus is not None:
        en.append(("What is the first bus from {}?".format(disp),
                   "The first listed departure from {} is at {} — {}, to {}. Buses often leave once seats fill up, so arrive a little early.".format(
                       disp, g.format_time(first), g.clean_text(first_bus.get("bus_name")) or "a bus service", dest_of(first_bus))))
    else:
        en.append(("What time do buses start from {}?".format(disp),
                   "Departure times are not listed for buses from {} yet — the services are on this page without times. Ask at the stand for the current schedule.".format(disp)))
    if last is not None and last_bus is not None:
        en.append(("What is the last bus from {}?".format(disp),
                   "The last listed departure is {} — {}, to {}. More services may exist, so ask at the stand.".format(
                       g.format_time(last), g.clean_text(last_bus.get("bus_name")) or "a bus service", dest_of(last_bus))))
    else:
        en.append(("Till when do buses run from {}?".format(disp),
                   "The last departure time is not listed yet — ask at the stand for the evening schedule. More services may exist.".format(disp)))
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
    if first is not None and first_bus is not None:
        bn.append(("{} থেকে প্রথম বাস কখন ছাড়ে?".format(p_bn),
                   "তালিকা অনুযায়ী প্রথম বাস ছাড়ে {} — {}, {} যায়। সিটের জন্য একটু আগে গিয়ে অপেক্ষা করাই ভালো।".format(
                       v2.bn_time(first), g.clean_text(first_bus.get("bus_name")) or "একটি বাস", v2.bnplace(dest_of(first_bus)))))
    else:
        bn.append(("{} থেকে বাস কখন ছাড়ে?".format(p_bn),
                   "এখনও সময় তালিকাভুক্ত নেই — বর্তমান সময়সূচি স্ট্যান্ডে জেনে নিন।"))
    if last is not None and last_bus is not None:
        bn.append(("{} থেকে দিনের শেষ বাস কতক্ষণে?".format(p_bn),
                   "তালিকায় শেষ বাস {} — {}, {} যায়। এর পরেও আরও বাস থাকতে পারে, স্ট্যান্ডে জেনে নিন।".format(
                       v2.bn_time(last), g.clean_text(last_bus.get("bus_name")) or "একটি বাস", v2.bnplace(dest_of(last_bus)))))
    else:
        bn.append(("{} থেকে সন্ধে পর্যন্ত বাস চলে?".format(p_bn),
                   "শেষ বাসের সময় এখনও তালিকাভুক্ত নয় — সন্ধের সময়সূচি স্ট্যান্ডে জেনে নিন।"))
    bn.append(("{} থেকে দিনে কতটি বাস ছাড়ে?".format(p_bn),
               "তালিকায় {}টি বাস, {}টি গন্তব্যে। আরও বাস থাকতে পারে, স্ট্যান্ডে জেনে নিন।".format(
                   bn_num(count), bn_num(len(dest_groups)))))
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
# travel guides — ONE attraction belongs to ONE stand (its own area).
# Real bus data only, never fabricated lodge/hostel names.
# ------------------------------------------------------------

def _maps(query):
    return "https://www.google.com/maps/search/?api=1&query=" + query.replace(" ", "+")


GUIDES = {
    "bankura": {
        "intro": ("Around Bankura", "বাঁকুড়ার আশপাশ"),
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
        ],
    },
    "kolkata": {
        "intro": ("Around Kolkata", "কলকাতার আশপাশ"),
        "note": "🚉 <b>Rail:</b> Howrah & Sealdah — India's biggest rail hub · 🛣️ <b>Road:</b> NH-16 (Kharagpur) and NH-19 (Dhanbad) start here.",
        "cards": [
            {"icon": "🛕", "name": "Dakshineswar Temple", "bn": "দক্ষিণেশ্বর মন্দির",
             "desc": "Historic Kali temple on the Hooghly — Ramakrishna Paramahansa's seat",
             "bus": "🚌 Route <b>43</b> runs to Dakshineswar — 23 listed buses touch the area",
             "maps": "Dakshineswar+Kali+Temple",
             "why": "riverside temple complex, 12 Shiva shrines, morning aarti",
             "when": "Year-round; early morning for aarti",
             "stay": None, "stay_extra": "Day trip in the city — {LINK}",
             "stay_link": "hotels+near+Dakshineswar+Kolkata", "stay_text": "stay nearby"},
            {"icon": "🕉️", "name": "Belur Math", "bn": "বেলুড় মঠ",
             "desc": "Ramakrishna Mission headquarters across the river at Bally",
             "bus": "🚌 Many listed buses run to <b>Bally</b> (Howrah side) — Belur Math is a short ride from Bally ghat",
             "maps": "Belur+Math+Howrah",
             "why": "serene marble temple, Swami Vivekananda's samadhi, evening arati",
             "when": "Year-round; afternoon for the sunset arati",
             "stay": None, "stay_extra": "Day trip in the city — {LINK}",
             "stay_link": "hotels+in+Howrah+Kolkata", "stay_text": "stay in the city"},
            {"icon": "🌿", "name": "Botanical Garden", "bn": "উদ্ভিদ উদ্যান",
             "desc": "The 200-year-old AJC Bose garden with the Great Banyan tree",
             "bus": "🚌 Route <b>55A</b> to Shibpur (Howrah side) — the garden is a short ride from there",
             "maps": "Acharya+Jagadish+Chandra+Bose+Botanical+Garden",
             "why": "the Great Banyan, palm house, riverside walk",
             "when": "October–March, mornings",
             "stay": None, "stay_extra": "Day trip in the city — {LINK}",
             "stay_link": "hotels+in+Howrah+Kolkata", "stay_text": "stay in the city"},
            {"icon": "🌳", "name": "Eco Park, New Town", "bn": "ইকো পার্ক",
             "desc": "Kolkata's biggest urban park — lake, themed gardens, ice skating",
             "bus": "🚌 27 listed buses to New Town — routes <b>EB-3</b> (Ecospace), <b>AS-3</b> (Newtown), <b>VS-10</b> (Amity)",
             "maps": "Eco+Park+New+Town+Kolkata",
             "why": "480-acre park, boating, butterfly garden, food courts",
             "when": "October–February, late afternoon",
             "stay": None, "stay_extra": "Day trip in the city — {LINK}",
             "stay_link": "hotels+in+New+Town+Kolkata", "stay_text": "stay in New Town"},
        ],
    },
    "digha": {
        "intro": ("Around Digha", "দীঘার আশপাশ"),
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
             "desc": "Old Shiva temple, 4 km from Digha",
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
    "purulia": {
        "intro": ("Around Purulia", "পুরুলিয়ার আশপাশ"),
        "note": "🚉 <b>Rail:</b> Purulia Junction (Howrah–Purulia line) · 🛣️ <b>Road:</b> NH-18 to Ranchi, SH to Bankura–Ajodhya.",
        "cards": [
            {"icon": "⛰️", "name": "Ajodhya Hills", "bn": "অযোধ্যা পাহাড়",
             "desc": "Purulia's hill spot — waterfalls, forests and tribal villages",
             "bus": "🚌 <b>GOUTAM</b> 10:30 AM · <b>KALYAN</b> 2:05 PM — direct to Ajodhya Hills; <b>HILLTOP SUPER</b> 11:05 AM via Baghmundi",
             "maps": "Ajodhya+Hills+Purulia",
             "why": "Upper & Lower falls, hill viewpoints, peaceful forest roads",
             "when": "September–February; monsoon for the falls",
             "stay": "stay+Ajodhya+Hills+Purulia"},
            {"icon": "🏔️", "name": "Joychandi Pahar", "bn": "জয়চণ্ডী পাহাড়",
             "desc": "Rocky hill with a ropeway, 5 km from Purulia town",
             "bus": "🚶 A short local ride from the stand (about 5 km) — ask at the stand",
             "maps": "Joychandi+Pahar+Purulia",
             "why": "Chotanagpur rocks, ropeway, sunset point, picnic spot",
             "when": "October–February, early morning or sunset",
             "stay": None, "stay_extra": "Day trip from Purulia — {LINK}",
             "stay_link": "hotels+in+Purulia+town", "stay_text": "stay in town"},
        ],
    },

    "durgapur": {
        "intro": ("Around Durgapur", "দুর্গাপুরের আশপাশ"),
        "note": "🚉 <b>Rail:</b> Durgapur station on the Howrah–Delhi main line · 🛣️ <b>Road:</b> NH-19 to Asansol–Dhanbad, SH to Bankura · listed buses: Kolkata 20, Nabadwip 9, Kalna 3.",
        "cards": [
            {"icon": "🌊", "name": "Durgapur Barrage", "bn": "দুর্গাপুর ব্যারাজ",
             "desc": "Damodar river barrage with a long tree-lined top road — the town's evening walk",
             "bus": "🚶 Short local ride from the stand — shared autos run all day",
             "maps": "Durgapur+Barrage",
             "why": "river view, sunset walk, 1950s DVC engineering",
             "when": "October–March, evening",
             "stay": None, "stay_extra": "Day trip in Durgapur — {LINK}",
             "stay_link": "hotels+in+Durgapur", "stay_text": "stay in town"},
            {"icon": "🎡", "name": "Troika Park", "bn": "ট্রোইকা পার্ক",
             "desc": "City amusement park by the lake at City Centre — rides and open lawns",
             "bus": "🚶 Walk or short auto from the City Centre stands",
             "maps": "Troika+Park+Durgapur",
             "why": "family rides, lakeside path, street food outside",
             "when": "October–February, afternoon",
             "stay": None, "stay_extra": "Day trip in Durgapur — {LINK}",
             "stay_link": "hotels+in+Durgapur", "stay_text": "stay in town"},
        ],
    },
    "siliguri": {
        "intro": ("Around Siliguri", "শিলিগুড়ির আশপাশ"),
        "note": "🚉 <b>Rail:</b> NJP junction and Siliguri Town station · ✈️ <b>Air:</b> Bagdogra airport 12 km · 🛣️ <b>Road:</b> the gate to Darjeeling, Kalimpong, Sikkim and the Dooars.",
        "cards": [
            {"icon": "⛰️", "name": "Darjeeling", "bn": "দার্জিলিং",
             "desc": "Queen of the hills — toy train, Tiger Hill and tea gardens",
             "bus": "🚌 <b>NBSTC</b> 6:00, 6:30, 7:00, 7:30, 8:30 & 10:30 AM — direct from this stand",
             "maps": "Darjeeling",
             "why": "Tiger Hill sunrise, UNESCO toy train, mall road",
             "when": "March–May & October–December, start early morning",
             "stay": "hotels+in+Darjeeling"},
            {"icon": "🏞️", "name": "Mirik", "bn": "মিরিক",
             "desc": "Lake town wrapped in tea gardens, an hour and a half away",
             "bus": "🚌 <b>NBSTC Siliguri–Mirik</b> 7:00 AM · 11:30 AM · 3:30 PM — direct",
             "maps": "Mirik+lake",
             "why": "Sumendu lake boating, orange orchards, tea estate views",
             "when": "October–April",
             "stay": "hotels+in+Mirik"},
            {"icon": "🏔️", "name": "Kalimpong", "bn": "কালিম্পং",
             "desc": "Hill town above the Teesta — monasteries and valley views",
             "bus": "🚌 <b>NBSTC Siliguri–Kalimpong</b> 6:30, 7:15, 8:45, 10:30, 11:40 AM & 1:15 PM — direct",
             "maps": "Kalimpong",
             "why": "Durpin monastery, Teesta views, flower nurseries",
             "when": "March–May & October–December",
             "stay": "hotels+in+Kalimpong"},
            {"icon": "🌸", "name": "Gangtok (Sikkim)", "bn": "গংটক",
             "desc": "Capital of Sikkim — MG Marg, monasteries and Himalayan views",
             "bus": "🚌 <b>NBSTC Siliguri–Gangtok</b> 5:30 AM & 8:15 AM — direct",
             "maps": "Gangtok",
             "why": "MG Marg walk, Rumtek monastery, hill viewpoints",
             "when": "March–June & October–December; carry photo ID for Sikkim entry",
             "stay": "hotels+in+Gangtok"},
        ],
    },
    "asansol": {
        "intro": ("Around Asansol", "আসানসোলের আশপাশ"),
        "note": "🚉 <b>Rail:</b> Asansol Junction on the Howrah–Delhi main line · 🛣️ <b>Road:</b> NH-19 to Dhanbad, NH-60 to Bankura · 19 listed buses to Kolkata.",
        "cards": [
            {"icon": "🌊", "name": "Maithon Dam", "bn": "মাইথন বাঁধ",
             "desc": "Damodar valley dam and lake — boating and viewpoints",
             "bus": "🚌 <b>Shyamoli Paribahan</b> Dhanbad-route buses (2 daily) pass the Maithon dam road",
             "maps": "Maithon+Dam",
             "why": "lake boating, deer park, dam viewpoint",
             "when": "October–March, morning",
             "stay": "hotels+near+Maithon"},
            {"icon": "🛕", "name": "Kalyaneswari Temple", "bn": "কল্যাণেশ্বরী মন্দির",
             "desc": "Old Kali temple on the Damodar, just before the dam",
             "bus": "🚌 Same Maithon-route buses — get off at Kalyaneswari, before the dam",
             "maps": "Kalyaneswari+Temple",
             "why": "ancient temple by the river, quiet ghat",
             "when": "Year-round, mornings",
             "stay": None, "stay_extra": "Day trip from Asansol — {LINK}",
             "stay_link": "hotels+in+Asansol", "stay_text": "stay in town"},
            {"icon": "⛰️", "name": "Biharinath Hill", "bn": "বিহারীনাথ পাহাড়",
             "desc": "The highest hill of the area — old Shiva temple and forest trails",
             "bus": "🚌 No direct listed bus — take an NH-60 Bankura-side local toward Saltora and ask for Biharinath, or hire a car",
             "maps": "Biharinath+Hill",
             "why": "hill climb, Biharinath Shiva temple, sunrise views",
             "when": "October–February, start early",
             "stay": None, "stay_extra": "Day trip from Asansol — {LINK}",
             "stay_link": "hotels+in+Asansol", "stay_text": "stay in town"},
        ],
    },
    "howrah-station": {
        "intro": ("Around Howrah Station", "হাওড়া স্টেশনের আশপাশ"),
        "note": "🚉 <b>Rail:</b> one of India's biggest stations — every Howrah line starts here · 🛣️ <b>Road:</b> 133 listed buses across 100+ routes.",
        "cards": [
            {"icon": "🌉", "name": "Howrah Bridge & Mullick Ghat", "bn": "হাওড়া ব্রিজ ও মল্লিক ঘাট",
             "desc": "Walk the iconic bridge at sunrise; the flower market roars below",
             "bus": "🚶 Walk out of the station — the bridge is right there",
             "maps": "Howrah+Bridge+Mullick+Ghat+flower+market",
             "why": "Rabindra Setu walk, Mullick Ghat flower market, river views",
             "when": "Year-round, sunrise for the flower market",
             "stay": None, "stay_extra": "Day trip in the city — {LINK}",
             "stay_link": "hotels+in+Howrah", "stay_text": "stay in the city"},
            {"icon": "🦩", "name": "Santragachi Jheel", "bn": "সাঁতরাগাছি জিল",
             "desc": "Big lake beside the rail station — winter migratory birds",
             "bus": "🚉 Two stations down the Howrah–Kharagpur line (10 min), then a short walk",
             "maps": "Santragachi+Jheel+lake",
             "why": "winter waterbirds, lakeside walk, photography",
             "when": "November–February, early morning",
             "stay": None, "stay_extra": "Day trip in the city — {LINK}",
             "stay_link": "hotels+in+Howrah", "stay_text": "stay in the city"},
            {"icon": "🌅", "name": "Gadiara", "bn": "গড়িয়ারা",
             "desc": "River confluence — the Damodar meets the Rupnarayan and the Hooghly",
             "bus": "🚉 Train toward Mecheda, then a short local ride (no direct listed bus from this stand — ask at the stand)",
             "maps": "Gadiara+Howrah",
             "why": "riverside sunset, boat rides, weekend crowds",
             "when": "October–March",
             "stay": "hotels+in+Gadiara"},
        ],
    },
    "bardhaman": {
        "intro": ("Around Bardhaman", "বর্ধমানের আশপাশ"),
        "note": "🚉 <b>Rail:</b> Bardhaman Junction — Howrah main line and Katwa line meet here · 🛣️ <b>Road:</b> GT Road (NH-19) to Durgapur · 26 listed buses to Kolkata.",
        "cards": [
            {"icon": "🏰", "name": "Bardhaman Rajbari", "bn": "বর্ধমান রাজবাড়ি",
             "desc": "Palace of the Maharajas of Burdwan — gateway, tanks and old temples around",
             "bus": "🚶 Short auto-rickshaw ride from the stand",
             "maps": "Bardhaman+Rajbari+palace",
             "why": "royal gateway, Sarbamangala temple nearby, old town walk",
             "when": "October–March, morning",
             "stay": "hotels+in+Bardhaman"},
            {"icon": "🛕", "name": "108 Shiva Temples", "bn": "১০৮ শিবমন্দির",
             "desc": "Two rows of 108 Shiva shrines built by the Burdwan royal family at Nababhat",
             "bus": "🚶 Local auto from the stand (Nababhat area)",
             "maps": "108+Shiva+Temples+Bardhaman+Nababhat",
             "why": "unique double-arc temple courtyard, quiet and photogenic",
             "when": "Year-round, Shivaratri is the big day",
             "stay": None, "stay_extra": "Day trip from Bardhaman — {LINK}",
             "stay_link": "hotels+in+Bardhaman", "stay_text": "stay in town"},
            {"icon": "🏛️", "name": "Kalna Temples", "bn": "কালনার মন্দির",
             "desc": "Temple town 30 km away — Pratapeswar Deul and the 108 Shiva temples of Kalna",
             "bus": "🚉 Frequent Katwa-line locals from Bardhaman Junction (about 30 min) — buses via the Katwa road also run, ask at the stand",
             "maps": "Kalna+terracotta+temples",
             "why": "terracotta Deul, 108-temple complex, riverside town",
             "when": "October–March",
             "stay": "hotels+in+Kalna"},
        ],
    },
    "barasat": {
        "intro": ("Around Barasat", "বারাসাতের আশপাশ"),
        "note": "🚉 <b>Rail:</b> Barasat on the Sealdah–Bongaon line · 🛣️ <b>Road:</b> Jessore Road runs to the Bangladesh border · 10 listed buses to Digha.",
        "cards": [
            {"icon": "🌳", "name": "Mangal Pandey Park", "bn": "মঙ্গল পাণ্ডে উদ্যান",
             "desc": "1857 memorial park on the Hooghly at Barrackpore",
             "bus": "🚌 <b>DS-34</b> · <b>C-29</b> — direct to Barrackpore Court",
             "maps": "Mangal+Pandey+Park+Barrackpore",
             "why": "riverfront park, 1857 history, ferry ghat",
             "when": "October–March, morning",
             "stay": None, "stay_extra": "Day trip from Barasat — {LINK}",
             "stay_link": "hotels+in+Barasat", "stay_text": "stay in town"},
            {"icon": "🌊", "name": "Ichhamati River, Bagdah", "bn": "ইছামতী নদী, বাগদা",
             "desc": "Quiet riverside on the Bangladesh border — boats and open fields",
             "bus": "🚌 <b>D7</b> runs to Bagdah from this stand",
             "maps": "Ichhamati+river+Bagdah",
             "why": "river bank, country boats, border village life",
             "when": "October–March",
             "stay": None, "stay_extra": "Day trip from Barasat — {LINK}",
             "stay_link": "hotels+in+Barasat", "stay_text": "stay in town"},
            {"icon": "⛴️", "name": "Hemnagar", "bn": "হেমনগর",
             "desc": "Riverside town on the Ichhamati — ghats and a lively weekly haat",
             "bus": "🚌 <b>D-34</b> runs to Hemnagar from this stand",
             "maps": "Hemnagar+North+24+Parganas",
             "why": "river ghats, border-area haat, boat rides",
             "when": "October–March, haat days",
             "stay": None, "stay_extra": "Day trip from Barasat — {LINK}",
             "stay_link": "hotels+in+Barasat", "stay_text": "stay in town"},
        ],
    },
}



GUIDES_BN = {
    "bankura": {
        "note": "🚉 <b>রেল:</b> বাঁকুড়া জংশন (হাওড়া–আদ্রা লাইন) · 🛣️ <b>রাস্তা:</b> দুর্গাপুর/আসানসল এনএইচ-১৪, বিষ্ণুপুর–পুরুলিয়া এসএইচ।",
        "cards": [
            {"desc_bn": "মল্ল রাজাদের পোড়ামাটির মন্দিরের শহর — রাসমঞ্চ, জোরবাংলা আরও অনেক মন্দির",
             "bus_bn": "🚌 <b>MUNMUN</b> 8:00 AM · <b>MAA MANASA</b> 9:40 AM — এই স্ট্যান্ড থেকে সরাসরি",
             "why_bn": "পোড়ামাটির মন্দির, বালুচরি শাড়ি, মন্দির-স্থাপত্য ঘোরা",
             "when_bn": "অক্টোবর–মার্চ, সকালে রওনা দিন"},
            {"desc_bn": "কংসাবতী বাঁধ — বাংলার বৃহত্তম জলাধারগুলোর একটি, সূর্যাস্তে নৌকা ভ্রমণ",
             "bus_bn": "🚌 <b>SOUMEN</b> (অম্বিকা নগর রুট) — মুকুটমণিপুরে পৌঁছায় 2:15 PM, ফেরে 3:50 PM",
             "why_bn": "বাঁধের ভিউ পয়েন্ট, নৌকা ভ্রমণ, নদীর সঙ্গম (কংসাবতী + কুমারী)",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, বিকেলে সূর্যাস্তের জন্য"},
            {"desc_bn": "পাহাড়, প্রাকৃতিক ঝরনা, প্রাচীন শিলালিপি ও রক ক্লাইম্বিং",
             "bus_bn": "🚌 <b>BABA LOKENATH</b> (আসানসল রুট) — শুশুনিয়া হিল স্টপে নেমে যান",
             "why_bn": "পাহাড় ট্রেক, ঝরনার জল, রক ক্লাইম্বিং, সবুজ জঙ্গল",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, সকাল সকাল যান",
             "stay_extra_bn": "বাঁকুড়া থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
        ],
    },
    "kolkata": {
        "note": "🚉 <b>রেল:</b> হাওড়া ও শিয়ালদহ — দেশের সবচেয়ে বড় রেল হাব · 🛣️ <b>রাস্তা:</b> এনএইচ-১৬ (খড়্গপুর) আর এনএইচ-১৯ (ধানবাদ) এখান থেকেই শুরু।",
        "cards": [
            {"desc_bn": "হুগলির ধারে ঐতিহাসিক কালীমন্দির — রামকৃষ্ণ পরমহংসের আসন",
             "bus_bn": "🚌 রুট <b>43</b> দক্ষিণেশ্বর যায় — 23টি তালিকাভুক্ত বাস এই এলাকা ছোঁয়",
             "why_bn": "নদীর ধারের মন্দির প্রাঙ্গণ, 12টি শিবমন্দির, ভোরের আরতি",
             "when_bn": "সারা বছর; আরতির জন্য ভোরে যান",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "কাছেই থাকুন"},
            {"desc_bn": "নদীর ওপারে বালিতে রামকৃষ্ণ মিশনের প্রধান কার্যালয়",
             "bus_bn": "🚌 বালির উদ্দেশে অনেক তালিকাভুক্ত বাস (হাওড়া দিক) — বালি ঘাট থেকে বেলুড় মঠ অল্প দূরে",
             "why_bn": "শান্ত মার্বেল মন্দির, স্বামী বিবেকানন্দের সমাধি, সন্ধ্যার আরতি",
             "when_bn": "সারা বছর; সূর্যাস্তের আরতির জন্য বিকেলে",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "দুশো বছরের পুরোনো এ জে সি বসু উদ্যান — বিশাল বটগাছসহ",
             "bus_bn": "🚌 রুট <b>55A</b> শিবপুর পর্যন্ত (হাওড়া দিক) — সেখান থেকে উদ্যান অল্প দূরে",
             "why_bn": "গ্রেট ব্যানিয়ান, পাম হাউস, নদীর ধারে হাঁটা",
             "when_bn": "অক্টোবর–মার্চ, সকালে",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "কলকাতার সবচেয়ে বড় শহর-উদ্যান — হ্রদ, থিম গার্ডেন, আইস স্কেটিং",
             "bus_bn": "🚌 নিউ টাউনে 27টি তালিকাভুক্ত বাস — রুট <b>EB-3</b> (Ecospace), <b>AS-3</b> (Newtown), <b>VS-10</b> (Amity)",
             "why_bn": "480 একরের পার্ক, বোটিং, প্রজাপতি উদ্যান, ফুড কোর্ট",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, বিকেলের দিকে",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "নিউ টাউনে থাকুন"},
        ],
    },
    "digha": {
        "note": "🚉 <b>রেল:</b> হাওড়া থেকে সরাসরি ট্রেন (সময় দেখে নিন) · 🛣️ <b>রাস্তা:</b> কোলাঘাট–নন্দকুমার–কাঁথি রুট, কলকাতা থেকে প্রায় 4 ঘণ্টা। ফেরা: কলকাতায় 18টি বাস তালিকাভুক্ত, প্রথম 4:30 AM, শেষ 10:00 PM।",
        "cards": [
            {"desc_bn": "মূল সমুদ্র সৈকত — সমতল, হাঁটার মতো, সূর্যোদয়ের জায়গা",
             "bus_bn": "🚶 স্ট্যান্ড থেকে অল্প হাঁটা বা সাইকেল-ভ্যানে যাওয়া যায়",
             "why_bn": "সমুদ্রের হাওয়া, মেরিন অ্যাকোয়ারিয়াম ও সায়েন্স সেন্টার, স্ট্রিট ফুড",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি; সূর্যোদয়ের জন্য ভোরে"},
            {"desc_bn": "পুরোনো শিবমন্দির, দীঘা থেকে 4 কিমি",
             "bus_bn": "🚌 স্ট্যান্ড থেকে লোকাল ভ্যান-বাস যায় — তালিকায় নেই, স্ট্যান্ডে জেনে নিন",
             "why_bn": "শত বছরের পুরোনো মন্দির, সকালের আরতি, ছোট সাপ্তাহিক হাট",
             "when_bn": "সারা বছর; সকালের দিকে ভালো",
             "stay_extra_bn": "দীঘা থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "দীঘায় থাকুন"},
            {"desc_bn": "নদী-মোহনার সৈকত, লাল কাঁকড়া — মৌসুমে অলিভ রিডলি কচ্ছপ ডিম পাড়তে আসে",
             "bus_bn": "🚌 স্ট্যান্ড থেকে লোকাল যান (প্রায় 10 কিমি) — স্ট্যান্ডে জেনে নিন",
             "why_bn": "ব্যাকওয়াটার, নিরিবিলি সৈকত, নদীর মোহনায় নৌকা ভ্রমণ",
             "when_bn": "অক্টোবর–মার্চ"},
            {"desc_bn": "লম্বা গাড়ি-চলা সৈকত আর লাল কাঁকড়া — নিরিবিলি দীঘা",
             "bus_bn": "🚌 কলকাতাগামী বাস কাঁথি হয়ে যায় (যেমন <b>SOHANA PARIBAHAN</b>, কাঁথি স্টপ 7:20 AM) — কাঁথি থেকে লোকাল যান ধরুন",
             "why_bn": "সৈকতে গাড়ি চালানো, ঝাউবন, ওয়াটার স্পোর্টস",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি"},
        ],
    },
    "purulia": {
        "note": "🚉 <b>রেল:</b> পুরুলিয়া জংশন (হাওড়া–পুরুলিয়া লাইন) · 🛣️ <b>রাস্তা:</b> রাঁচি এনএইচ-১৮, বাঁকুড়া–অযোধ্যা এসএইচ।",
        "cards": [
            {"desc_bn": "পুরুলিয়ার পাহাড় — ঝরনা, জঙ্গল আর আদিবাসী গ্রাম",
             "bus_bn": "🚌 <b>GOUTAM</b> 10:30 AM · <b>KALYAN</b> 2:05 PM — সরাসরি অযোধ্যা পাহাড়; <b>HILLTOP SUPER</b> 11:05 AM বাঘমুণ্ডি হয়ে",
             "why_bn": "আপার ও লোয়ার ঝরনা, পাহাড়ি ভিউ পয়েন্ট, শান্ত জঙ্গলের রাস্তা",
             "when_bn": "সেপ্টেম্বর–ফেব্রুয়ারি; ঝরনার জন্য বর্ষাকাল"},
            {"desc_bn": "পাথুরে পাহাড় আর রোপ-ওয়ে, পুরুলিয়া শহর থেকে 5 কিমি",
             "bus_bn": "🚶 স্ট্যান্ড থেকে অল্প লোকাল রাইড (প্রায় 5 কিমি) — জেনে নিন",
             "why_bn": "ছোটনাগপুরের পাথর, রোপ-ওয়ে, সূর্যাস্ত পয়েন্ট, পিকনিক স্পট",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, ভোরে বা সূর্যাস্তে",
             "stay_extra_bn": "পুরুলিয়া থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
        ],
    },

    "durgapur": {
        "note": "🚉 <b>রেল:</b> হাওড়া–দিল্লি প্রধান লাইনের দুর্গাপুর স্টেশন · 🛣️ <b>রাস্তা:</b> আসানসল–ধানবাদ এনএইচ-১৯, বাঁকুড়া এসএইচ · তালিকাভুক্ত বাস: কলকাতা ২০টি, নবদ্বীপ ৯টি, কালনা ৩টি।",
        "cards": [
            {"desc_bn": "দামোদর নদীর ওপর ব্যারাজ — ওপরে গাছে ঢাকা লম্বা রাস্তা, শহরের সন্ধ্যার হাঁটার জায়গা",
             "bus_bn": "🚶 স্ট্যান্ড থেকে অল্প লোকাল রাইড — শেয়ারড অটো সারাদিন পাওয়া যায়",
             "why_bn": "নদীর দৃশ্য, সূর্যাস্তে হাঁটা, পঞ্চাশের দশকের ডিভিসি বাঁধ",
             "when_bn": "অক্টোবর–মার্চ, সন্ধ্যায়",
             "stay_extra_bn": "দুর্গাপুরে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "সিটি সেন্টারে হ্রদের ধারে বিনোদন পার্ক — রাইড, খোলা লন",
             "bus_bn": "🚶 সিটি সেন্টার স্ট্যান্ড থেকে হাঁটা দূরত্ব বা অটো",
             "why_bn": "পরিবারের সঙ্গে রাইড, হ্রদের ধারে পথ, বাইরে স্ট্রিট ফুড",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, বিকেলে",
             "stay_extra_bn": "দুর্গাপুরে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
        ],
    },
    "siliguri": {
        "note": "🚉 <b>রেল:</b> এনজেপি জংশন ও শিলিগুড়ি টাউন স্টেশন · ✈️ <b>বিমান:</b> বাগডোগরা, ১২ কিমি · 🛣️ <b>রাস্তা:</b> দার্জিলিং, কালিম্পং, সিকিম ও ডুয়ার্সের পথ এখান থেকেই।",
        "cards": [
            {"desc_bn": "পাহাড়ের রানি — টয় ট্রেন, টাইগার হিল আর চা-বাগান",
             "bus_bn": "🚌 <b>NBSTC</b> 6:00, 6:30, 7:00, 7:30, 8:30 & 10:30 AM — এই স্ট্যান্ড থেকে সরাসরি",
             "why_bn": "টাইগার হিলের সূর্যোদয়, ইউনেস্কো টয় ট্রেন, মল রোড",
             "when_bn": "মার্চ–মে ও অক্টোবর–ডিসেম্বর, ভোরে রওনা দিন"},
            {"desc_bn": "চা-বাগানে ঘেরা হ্রদের শহর, দেড় ঘণ্টার পথ",
             "bus_bn": "🚌 <b>NBSTC শিলিগুড়ি–মিরিক</b> 7:00 AM · 11:30 AM · 3:30 PM — সরাসরি",
             "why_bn": "সুমেন্দু হ্রদে বোটিং, কমলালেবু বাগান, চা-বাগানের দৃশ্য",
             "when_bn": "অক্টোবর–এপ্রিল"},
            {"desc_bn": "তিস্তার ওপরে পাহাড়ের শহর — মঠ আর উপত্যকার দৃশ্য",
             "bus_bn": "🚌 <b>NBSTC শিলিগুড়ি–কালিম্পং</b> 6:30, 7:15, 8:45, 10:30, 11:40 AM & 1:15 PM — সরাসরি",
             "why_bn": "দুরপিন মঠ, তিস্তার দৃশ্য, ফুলের নার্সারি",
             "when_bn": "মার্চ–মে ও অক্টোবর–ডিসেম্বর"},
            {"desc_bn": "সিকিমের রাজধানী — এম জি মার্গ, মঠ আর হিমালয়ের দৃশ্য",
             "bus_bn": "🚌 <b>NBSTC শিলিগুড়ি–গংটক</b> 5:30 AM & 8:15 AM — সরাসরি",
             "why_bn": "এম জি মার্গ, রুমটেক মঠ, পাহাড়ের ভিউ পয়েন্ট",
             "when_bn": "মার্চ–জুন ও অক্টোবর–ডিসেম্বর; সিকিমে ঢোকার জন্য ছবির আই-কার্ড নিন"},
        ],
    },
    "asansol": {
        "note": "🚉 <b>রেল:</b> হাওড়া–দিল্লি প্রধান লাইনের আসানসল জংশন · 🛣️ <b>রাস্তা:</b> ধানবাদ এনএইচ-১৯, বাঁকুড়া এনএইচ-৬০ · কলকাতায় ১৯টি তালিকাভুক্ত বাস।",
        "cards": [
            {"desc_bn": "দামোদর উপত্যকার বাঁধ আর হ্রদ — বোটিং ও ভিউ পয়েন্ট",
             "bus_bn": "🚌 <b>Shyamoli Paribahan</b> ধানবাদ রুটের বাস (দিনে ২টি) মাইথন বাঁধের রাস্তা ছোঁয়",
             "why_bn": "হ্রদে বোটিং, হরিণ পার্ক, বাঁধের ভিউ পয়েন্ট",
             "when_bn": "অক্টোবর–মার্চ, সকালে"},
            {"desc_bn": "দামোদরের ধারে পুরোনো কালীমন্দির, বাঁধের আগে",
             "bus_bn": "🚌 মাইথন রুটের একই বাস — বাঁধের আগে কল্যাণেশ্বরীতে নেমে যান",
             "why_bn": "নদীর ধারে প্রাচীন মন্দির, শান্ত ঘাট",
             "when_bn": "সারা বছর, সকালে",
             "stay_extra_bn": "আসানসল থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "এলাকার সবচেয়ে উঁচু পাহাড় — পুরোনো শিবমন্দির আর জঙ্গলের পথ",
             "bus_bn": "🚌 সরাসরি তালিকাভুক্ত বাস নেই — এনএইচ-৬০ বাঁকুড়া দিকের লোকাল বাস ধরে শালতোড়ার দিকে যান, বিহারীনাথ জিজে নিন; চাইলে গাড়ি ভাড়া করুন",
             "why_bn": "পাহাড় বোয়ানো, বিহারীনাথ শিবমন্দির, সূর্যোদয়ের দৃশ্য",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, ভোরে রওনা দিন",
             "stay_extra_bn": "আসানসল থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
        ],
    },
    "howrah-station": {
        "note": "🚉 <b>রেল:</b> দেশের অন্যতম বড় স্টেশন — হাওড়ার সব লাইন এখান থেকে ছাড়ে · 🛣️ <b>রাস্তা:</b> ১০০-র বেশি রুটে ১৩৩টি তালিকাভুক্ত বাস।",
        "cards": [
            {"desc_bn": "ভোরে সেতু পেরিয়ে হাঁটুন; নিচে মল্লিক ঘাটের ফুলের বাজার",
             "bus_bn": "🚶 স্টেশন থেকে বেরোলেই সেতু",
             "why_bn": "রবীন্দ্র সেতুতে হাঁটা, মল্লিক ঘাটের ফুলের বাজার, নদীর দৃশ্য",
             "when_bn": "সারা বছর, ফুলের বাজারের জন্য ভোরে",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "স্টেশনের পাশে বড় হ্রদ — শীতে পরিযায়ী পাখি",
             "bus_bn": "🚉 হাওড়া–খড়্গপুর লাইনে দু'স্টেশন (১০ মিনিট), তারপর অল্প হাঁটা",
             "why_bn": "শীতের জলপাখি, হ্রদের ধারে হাঁটা, ছবি তোলা",
             "when_bn": "নভেম্বর–ফেব্রুয়ারি, ভোরে",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "নদীর সঙ্গমস্থল — দামোদর রূপনারায়ণ ও হুগলির সাথে মেশে",
             "bus_bn": "🚉 মেচেদা এগিয়ে ট্রেন, তারপর অল্প লোকাল রাইড (এই স্ট্যান্ড থেকে সরাসরি তালিকাভুক্ত বাস নেই — জেনে নিন)",
             "why_bn": "নদীর ধারে সূর্যাস্ত, নৌকা ভ্রমণ, ছুটির দিনের ভিড়",
             "when_bn": "অক্টোবর–মার্চ"},
        ],
    },
    "bardhaman": {
        "note": "🚉 <b>রেল:</b> বর্ধমান জংশন — হাওড়া মেন ও কাটোয়া লাইনের মিলনস্থল · 🛣️ <b>রাস্তা:</b> দুর্গাপুর অভিমুখে জিটি রোড (এনএইচ-১৯) · কলকাতায় ২৬টি তালিকাভুক্ত বাস।",
        "cards": [
            {"desc_bn": "বর্ধমানের মহারাজাদের রাজবাড়ি — ফটক, দিঘি আর চারপাশে পুরোনো মন্দির",
             "bus_bn": "🚶 স্ট্যান্ড থেকে অটো-রিকশায় অল্প পথ",
             "why_bn": "রাজকীয় ফটক, কাছেই সর্বমঙ্গলা মন্দির, পুরোনো শহরে হাঁটা",
             "when_bn": "অক্টোবর–মার্চ, সকালে"},
            {"desc_bn": "নবাবহাটে বর্ধমান রাজপরিবারের তৈরি দু'সারি ১০৮টি শিবমন্দির",
             "bus_bn": "🚶 স্ট্যান্ড থেকে লোকাল অটো (নবাবহাট এলাকা)",
             "why_bn": "অনন্য দু'সারি মন্দিরের উঠান, শান্ত ও ছবির মতো",
             "when_bn": "সারা বছর, শিবরাত্রিতে বিশেষ আয়োজন",
             "stay_extra_bn": "বর্ধমান থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "৩০ কিমি দূরে মন্দিরের শহর কালনা — প্রতাপেশ্বর দেউল আর ১০৮ শিবমন্দির",
             "bus_bn": "🚉 বর্ধমান জংশন থেকে কাটোয়া লাইনের লোকাল (প্রায় ৩০ মিনিট) — কাটোয়া রোডের বাসও চলে, জেনে নিন",
             "why_bn": "পোড়ামাটির দেউল, ১০৮ মন্দিরের কমপ্লেক্স, নদীর ধারে শহর",
             "when_bn": "অক্টোবর–মার্চ"},
        ],
    },
    "barasat": {
        "note": "🚉 <b>রেল:</b> শিয়ালদহ–বনগাঁ লাইনে বারাসাত · 🛣️ <b>রাস্তা:</b> যশোর রোড বাংলাদেশ সীমান্ত পর্যন্ত · দীঘায় ১০টি তালিকাভুক্ত বাস।",
        "cards": [
            {"desc_bn": "ব্যারাকপুরে হুগলির ধারে ১৮৫৭-র স্মৃতিতে উদ্যান",
             "bus_bn": "🚌 <b>DS-34</b> · <b>C-29</b> — ব্যারাকপুর কোর্ট পর্যন্ত সরাসরি",
             "why_bn": "নদীর ধারে পার্ক, ১৮৫৭-র ইতিহাস, ফেরি ঘাট",
             "when_bn": "অক্টোবর–মার্চ, সকালে",
             "stay_extra_bn": "বারাসাত থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "বাংলাদেশ সীমান্তে ইছামতীর শান্ত পাড় — নৌকা আর খোলা মাঠ",
             "bus_bn": "🚌 <b>D7</b> এই স্ট্যান্ড থেকে বাগদা পর্যন্ত চলে",
             "why_bn": "নদীর পাড়, দেশি নৌকা, সীমান্ত গ্রামের জীবন",
             "when_bn": "অক্টোবর–মার্চ",
             "stay_extra_bn": "বারাসাত থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "ইছামতীর ধারে শহর — ঘাট আর সাপ্তাহিক হাট",
             "bus_bn": "🚌 <b>D-34</b> এই স্ট্যান্ড থেকে হেমনগর পর্যন্ত চলে",
             "why_bn": "নদীর ঘাট, সীমান্ত এলাকার হাট, নৌকা ভ্রমণ",
             "when_bn": "অক্টোবর–মার্চ, হাটের দিনে",
             "stay_extra_bn": "বারাসাত থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
        ],
    },
}


def _merge_guide_bn():
    """Fold GUIDES_BN Bengali fields into the GUIDES dict as *_bn keys."""
    for slug, bn in GUIDES_BN.items():
        gd = GUIDES.get(slug)
        if not gd:
            continue
        if "note" in bn:
            gd["note_bn"] = bn["note"]
        for c, cbn in zip(gd["cards"], bn.get("cards", [])):
            for k, v in cbn.items():
                c[k if k.endswith("_bn") else k + "_bn"] = v


_merge_guide_bn()


# ------------------------------------------------------------
# page template — SAME design language as the homepage
# ------------------------------------------------------------

CSS = """:root{--bg:#f5efe1;--surface:#fffcf4;--surface-2:#efe6d3;--ink:#211c16;--ink-dim:#6f6653;--line:rgba(33,28,22,.13);--line-strong:rgba(33,28,22,.24);--amber:#b8791f;--amber-ink:#6b4610;--amber-soft:rgba(184,121,31,.14);--shadow:0 10px 34px -12px rgba(33,28,22,.28);--shadow-sm:0 2px 12px rgba(33,28,22,.1);--radius-lg:20px;--radius:14px;--font-display:'Fraunces',Georgia,serif;--font-body:'IBM Plex Sans','IBM Plex Sans Bengali',system-ui,sans-serif}
[data-theme="dark"]{--bg:#15121d;--surface:#201c2b;--surface-2:#29243570;--ink:#f1ead8;--ink-dim:#a89b87;--line:rgba(241,234,216,.1);--line-strong:rgba(241,234,216,.2);--amber:#eda94a;--amber-ink:#f6cd8f;--amber-soft:rgba(237,169,74,.16);--shadow:0 14px 44px -14px rgba(0,0,0,.5);--shadow-sm:0 2px 12px rgba(0,0,0,.3)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--font-body);background:var(--bg);color:var(--ink);line-height:1.55}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.header{background:var(--surface);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:100;backdrop-filter:blur(14px) saturate(1.1);background:color-mix(in srgb,var(--surface) 88%,transparent)}
.header::after{content:"";position:absolute;left:0;right:0;bottom:-6px;height:6px;background-image:radial-gradient(circle at 10px 0,var(--bg) 5px,transparent 5.5px);background-size:20px 6px;background-repeat:repeat-x}
.header-inner{display:flex;align-items:center;justify-content:space-between;padding:13px 18px;gap:10px;position:relative;z-index:1;max-width:788px;margin:0 auto}
.logo{display:flex;align-items:center;gap:9px;font-family:var(--font-display);font-size:1.32rem;font-weight:700;color:var(--ink);cursor:pointer;letter-spacing:-.2px;text-decoration:none}
.logo .icon{width:1.35rem;height:1.35rem;color:var(--amber);stroke-width:1.6}
.logo span{color:var(--amber-ink)}
.header-actions{display:flex;align-items:center;gap:8px}
.icon-btn{width:38px;height:38px;display:inline-flex;align-items:center;justify-content:center;background:var(--surface-2);border:1px solid var(--line);border-radius:50%;cursor:pointer;color:var(--ink);font-size:15px;transition:border-color .2s,transform .3s}
.icon-btn:hover{border-color:var(--amber)}
.icon-btn:active{transform:scale(.92)}
.icon-btn svg{width:17px;height:17px;transition:transform .4s cubic-bezier(.34,1.56,.64,1),opacity .2s}
.lang-group{display:flex;border:1px solid var(--line);border-radius:999px;padding:3px;gap:2px;background:var(--surface-2)}
.lang-btn{background:transparent;border:none;border-radius:999px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;color:var(--ink-dim);transition:.2s;font-family:var(--font-body)}
.lang-btn.active{background:var(--amber);color:#fff9ee}
[data-theme="dark"] .lang-btn.active{color:#241706}
.wrap{max-width:760px;margin:0 auto;padding:14px 14px 60px}
.crumbs{font-size:12px;color:var(--ink-dim);margin:14px 0 14px}.crumbs a{color:var(--ink-dim)}
.hero{background:linear-gradient(135deg,#b8791f 0%,#8a5a12 100%);border-radius:var(--radius-lg);padding:26px 20px;color:#fff;margin-bottom:14px;animation:fadeUp .5s .05s ease both}
.hero h1{font-size:30px;letter-spacing:-.5px;line-height:1.15;font-family:var(--font-display)}
.hero .hbn{font-size:15px;opacity:.92;margin-top:4px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.schip{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:6px 13px;font-size:12.5px;font-weight:700}
.schip.hot{background:#fff;color:#6b4610}
[data-theme="dark"] .schip.hot{background:rgba(21,18,29,.55);color:var(--amber-ink)}
.sec{margin:22px 0 10px;display:flex;align-items:baseline;justify-content:space-between}
.sec h3{font-size:17px;font-family:var(--font-display)}
.sec .cnt{font-size:12px;color:var(--ink-dim)}
.dsearch{background:var(--surface);border:1px solid var(--line-strong);border-radius:var(--radius);box-shadow:var(--shadow-sm);margin:0 0 12px;animation:fadeUp .6s .15s ease both}
.dsearch input{width:100%;border:none;background:transparent;color:var(--ink);border-radius:var(--radius);padding:13px 16px;font-size:15px;font-weight:600;outline:none;font-family:var(--font-body)}
.dgrid{display:grid;grid-template-columns:1fr;gap:10px;animation:fadeUp .5s .2s ease both}
@media(min-width:560px){.dgrid{grid-template-columns:1fr 1fr}}
.dcard{display:block;background:var(--surface);border:1.5px solid var(--line);border-radius:var(--radius);padding:14px;text-decoration:none;color:inherit;transition:transform .15s,border-color .15s}
.dcard:hover{transform:translateY(-2px);border-color:var(--amber)}
.dhead{display:flex;justify-content:space-between;align-items:center}
.dname{font-size:16.5px;font-weight:800}.dbn{font-size:12.5px;color:var(--ink-dim);font-weight:600;margin-left:6px}
.dcount{font-size:12px;color:var(--amber-ink);font-weight:700;margin-top:2px}
[data-theme="dark"] .dcount{color:var(--amber)}
.arr{font-size:22px;color:var(--ink-dim)}
.dtimes{margin-top:10px;display:flex;flex-wrap:wrap;gap:6px}
.tchip{background:var(--amber-soft);border:1px solid var(--line);border-radius:8px;padding:4px 9px;font-size:13px;font-weight:800;font-variant-numeric:tabular-nums}
.tmore{font-size:12px;color:var(--ink-dim);align-self:center}
.ntime{margin-top:8px;font-size:11.5px;color:var(--ink-dim)}
.mgrid{display:grid;grid-template-columns:1fr;gap:9px}
@media(min-width:520px){.mgrid{grid-template-columns:1fr 1fr}}
.mcard{display:flex;justify-content:space-between;align-items:center;background:var(--surface);border:1.5px solid var(--line);border-radius:12px;padding:12px 14px;text-decoration:none;color:inherit;transition:transform .15s,border-color .15s}
.mcard:hover{border-color:var(--amber);transform:translateY(-1px)}
.mname{font-size:14.5px;font-weight:800}.mbn{font-size:11px;color:var(--ink-dim);margin-left:4px}
.mmeta{font-size:12px;color:var(--ink-dim);margin-top:2px}
.note{background:var(--amber-soft);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:13px;color:var(--ink-dim);margin:18px 0}
.morebtn{display:block;width:100%;margin-top:12px;border:1.5px dashed var(--amber);background:transparent;color:var(--amber-ink);border-radius:12px;padding:11px;font-size:14px;font-weight:800;cursor:pointer}
[data-theme="dark"] .morebtn{color:var(--amber)}
details.faq{background:var(--surface);border:1.5px solid var(--line);border-radius:12px;padding:13px 15px;margin-bottom:8px}
details.faq summary{font-weight:700;font-size:14px;cursor:pointer}
details.faq p{margin-top:8px;font-size:13.5px;color:var(--ink-dim)}
.tg-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:480px){.tg-grid{grid-template-columns:1fr}}
.tg-card{background:var(--surface);border:1.5px solid var(--line);border-radius:var(--radius);padding:13px}
.tg-ico{font-size:22px}
.tg-name{font-weight:800;font-size:14.5px;margin-top:4px}
.tg-bn{font-size:11.5px;color:var(--ink-dim);font-weight:600;margin-left:4px}
.tg-desc{font-size:12.5px;color:var(--ink-dim);margin-top:4px}
.tg-rows{margin-top:9px;display:grid;gap:6px}
.tg-row{font-size:12.5px;color:var(--ink-dim);background:var(--amber-soft);border:1px solid var(--line);border-radius:10px;padding:7px 10px;line-height:1.45}
.tg-row b{color:var(--ink)}
.tg-row a{color:var(--amber-ink);font-weight:700;text-decoration:none;border-bottom:1px dashed var(--amber-ink)}
[data-theme="dark"] .tg-row a{color:var(--amber)}
.tg-note{background:var(--amber-soft);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:13px;color:var(--ink-dim);margin-top:10px}
footer{margin-top:30px;border-top:1px solid var(--line);padding-top:14px;font-size:12px;color:var(--ink-dim);text-align:center}
footer a{color:var(--ink-dim);margin:0 6px}
.label-bn{display:none}
body.lang-bn .label-en{display:none}
body.lang-bn .label-bn{display:inline}
.only-bn{display:none}
body.lang-bn .only-en{display:none}
body.lang-bn .only-bn{display:block}"""

JS = """var mstep=24;
var MOON='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
var SUN='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>';
var PH={en:"\\uD83D\\uDD0E Search destination — e.g. Purulia, Kolkata\\u2026",bn:"\\uD83D\\uDD0E \\u0997\\u09A8\\u09CD\\u09A4\\u09AC\\u09CD\\u09AF \\u0996\\u09C1\\u0981\\u099C\\u09C1\\u09A8 \\u2014 \\u09AF\\u09C7\\u09AE\\u09A8 \\u09AA\\u09C1\\u09B0\\u09C1\\u09B2\\u09BF\\u09AF\\u09BC\\u09BE, \\u0995\\u09B2\\u0995\\u09BE\\u09A4\\u09BE\\u2026"};
function bnd(s){return String(s).replace(/[0-9]/g,function(d){return "\\u09E7\\u09E8\\u09E9\\u09EA\\u09EB\\u09EC\\u09ED\\u09EE\\u09EF\\u09E6"[d];});}
function isBn(){return document.body.className.indexOf('lang-bn')>-1;}
function mcards(){return Array.prototype.slice.call(document.querySelectorAll('#minis .mcard'));}
function mrefresh(){
  var cs=mcards();var shown=cs.filter(function(c){return c.style.display!=='none';}).length;
  var b=document.getElementById('mmore');
  if(b){if(shown>=cs.length){b.style.display='none';}else{b.style.display='';b.textContent=isBn()?'\\u0986\\u09B0\\u0993 \\u09A6\\u09C7\\u0996\\u09C1\\u09A8 ('+bnd(cs.length-shown)+'\\u099F\\u09BF \\u0997\\u09A8\\u09CD\\u09A4\\u09AC\\u09CD\\u09AF \\u09AC\\u09BE\\u0995\\u09BF)':'See more ('+(cs.length-shown)+' destinations remaining)';}}
  var c=document.getElementById('mcnt');
  if(c){c.textContent=isBn()?bnd(shown)+' / '+bnd(cs.length):shown+' of '+cs.length;}
}
function showMoreDest(){
  var cs=mcards();var shown=cs.filter(function(c){return c.style.display!=='none';}).length;
  var nxt=Math.min(shown+mstep,cs.length);
  cs.forEach(function(c,i){c.style.display=i<nxt?'':'none';});
  mrefresh();
}
mcs=mcards();mcs.forEach(function(c,i){c.style.display=i<mstep?'':'none';});mrefresh();
function fil(){
  var q=document.getElementById('q').value.toLowerCase().trim();var cs=mcards();
  var dc=document.querySelectorAll('#cards .dcard');
  if(!q){cs.forEach(function(c,i){c.style.display=i<mstep?'':'none';});dc.forEach(function(c){c.style.display='';});mrefresh();return;}
  cs.forEach(function(c){c.style.display=c.textContent.toLowerCase().indexOf(q)>-1?'':'none';});
  dc.forEach(function(c){c.style.display=c.textContent.toLowerCase().indexOf(q)>-1?'':'none';});
  var shown=cs.filter(function(c){return c.style.display!=='none';}).length;
  document.getElementById('mcnt').textContent=isBn()?bnd(shown)+' / '+bnd(cs.length):shown+' of '+cs.length;
  var b=document.getElementById('mmore');b.style.display=shown>=cs.length?'none':'';
}
function updateThemeIcon(theme){var btn=document.getElementById('themeBtn');if(btn)btn.innerHTML=theme==='dark'?SUN:MOON;}
function toggleTheme(){
  var cur=document.documentElement.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
  var next=cur==='dark'?'light':'dark';
  document.documentElement.setAttribute('data-theme',next);
  localStorage.setItem('bj-theme',next);
  updateThemeIcon(next);
}
function setLang(l){
  document.body.className=l==='bn'?'lang-bn':'';
  localStorage.setItem('bj-lang',l);
  document.getElementById('langEN').classList.toggle('active',l==='en');
  document.getElementById('langBN').classList.toggle('active',l==='bn');
  var q=document.getElementById('q');if(q){q.placeholder=l==='bn'?PH.bn:PH.en;}
  mrefresh();
}
(function(){
  var t=localStorage.getItem('bj-theme');
  if(t)document.documentElement.setAttribute('data-theme',t);
  updateThemeIcon(t||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));
  var l=localStorage.getItem('bj-lang');
  if(l&&l!=='en'){setLang(l);}else{var q=document.getElementById('q');if(q)q.placeholder=PH.en;}
})();"""

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,500;0,600;0,700;0,900;1,500&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Bengali:wght@400;500;600;700&display=swap" rel="stylesheet">"""

HEADER = """<header class="header">
  <div class="header-inner">
    <a class="logo" href="../index.html">
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/><path d="M4 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M17 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M6 10h12"/></svg>
      Bus<span>Jatri</span>
    </a>
    <div class="header-actions">
      <button class="icon-btn" id="themeBtn" onclick="toggleTheme()" title="Toggle theme" aria-label="Toggle dark mode"></button>
      <div class="lang-group">
        <button class="lang-btn active" id="langEN" onclick="setLang('en')">EN</button>
        <button class="lang-btn" id="langBN" onclick="setLang('bn')">বাংলা</button>
      </div>
    </div>
  </div>
</header>"""


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
{fonts}
{schema}
<style>{css}</style></head>""".format(
        title=g.esc(title), desc=g.esc(description), canon=g.esc(canonical),
        ogimg=g.BASE + "/og-image.png", fonts=FONTS, schema="{schema}", css=CSS)


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
            stay_row = '🏨 <a href="{u}" target="_blank" rel="nofollow">{t}</a>'.format(
                u=_maps(c["stay"]),
                t=L("Stay options on Maps", "ম্যাপে থাকার জায়গা"))
        else:
            stay_row = "🏨 " + L(c["stay_extra"], c.get("stay_extra_bn", c["stay_extra"])).replace("{LINK}", '<a href="{u}" target="_blank" rel="nofollow">{t}</a>'.format(u=_maps(c["stay_link"]), t=L(c["stay_text"], c.get("stay_text_bn", c["stay_text"]))))
        cards.append("""<div class="tg-card">
  <div class="tg-ico">{ico}</div>
  <div class="tg-name">{name}</div>
  <div class="tg-desc">{desc}</div>
  <div class="tg-rows">
    <div class="tg-row">{bus}</div>
    <div class="tg-row">🗺️ <a href="{maps}" target="_blank" rel="nofollow">{open_txt}</a></div>
    <div class="tg-row">⭐ {why_txt}: {why}</div>
    <div class="tg-row">🕐 {best_txt}: {when}</div>
    <div class="tg-row">{stay}</div>
  </div>
</div>""".format(ico=c["icon"], name=L(g.esc(c["name"]), g.esc(c["bn"])),
                 desc=L(g.esc(c["desc"]), g.esc(c.get("desc_bn", c["desc"]))),
                 bus=L(c["bus"], c.get("bus_bn", c["bus"])),
                 maps=_maps(c["maps"]),
                 open_txt=L("Open in Google Maps", "গুগল ম্যাপে খুলুন"),
                 why_txt=L("Why go", "কেন যাবেন"),
                 best_txt=L("Best time", "সেরা সময়"),
                 why=L(g.esc(c["why"]), g.esc(c.get("why_bn", c["why"]))),
                 when=L(g.esc(c["when"]), g.esc(c.get("when_bn", c["when"]))),
                 stay=stay_row))
    intro_en, intro_bn = guide["intro"]
    return """<div class="sec"><h3>{tg} <span class="cnt">{intro}</span></h3></div>
<div class="tg-grid">{cards}</div>
<div class="tg-note">{note}</div>""".format(
        tg=L("Travel Guide", "ভ্রমণ গাইড"),
        intro=L(g.esc(intro_en), g.esc(intro_bn)),
        cards="".join(cards), note=L(guide["note"], guide.get("note_bn", guide["note"])))


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

    # ---- hero chips (bilingual) ----
    if count == 0:
        chips = '<span class="schip">🚌 ' + L("No buses listed yet", "এখনও কোনো বাস তালিকাভুক্ত নেই") + "</span>"
    else:
        chips = ('<span class="schip">🚌 ' + L("{} buses listed".format(count), "{}টি বাস তালিকাভুক্ত".format(bn_num(count))) + "</span>"
                 + '<span class="schip">📍 ' + L("{} destinations".format(len(dest_groups)), "{}টি গন্তব্য".format(bn_num(len(dest_groups)))) + "</span>"
                 + ('<span class="schip hot">⏰ ' + L("First", "প্রথম") + " {}</span>".format(g.esc(g.format_time(first))) if first is not None else "")
                 + ('<span class="schip hot">⏰ ' + L("Last", "শেষ") + " {}</span>".format(g.esc(g.format_time(last))) if last is not None else ""))

    # ---- popular routes (top 12) + all destinations (rest, A-Z) ----
    popular = dest_groups[:12]
    rest = sorted(dest_groups[12:], key=lambda x: x["display"].lower())
    cards_html = "".join(_popular_card(grp) for grp in popular)
    minis_html = "".join(_mini_card(grp) for grp in rest)
    if rest:
        all_section = """<div class="sec"><h3>{h}</h3><span class="cnt" id="mcnt"></span></div>
<div class="dsearch"><input id="q" type="text" oninput="fil()" aria-label="Search destinations"></div>
<div class="mgrid" id="minis">{minis}</div>
<button class="morebtn" id="mmore" onclick="showMoreDest()"></button>""".format(
            h=L("All Destinations", "সব গন্তব্য"), minis=minis_html)
        popular_section = """<div class="sec"><h3>{h}</h3></div>
<div class="dgrid" id="cards">{cards}</div>""".format(h=L("Popular Routes", "জনপ্রিয় রুট"), cards=cards_html)
    else:
        popular_section = """<div class="sec"><h3>{h}</h3></div>
<div class="dgrid" id="cards">{cards}</div>
<div class="dsearch"><input id="q" type="text" oninput="fil()" aria-label="Search destinations"></div>""".format(
            h=L("All Destinations", "সব গন্তব্য"), cards=cards_html)
        all_section = '<div class="mgrid" id="minis"></div>'

    note = L("Only buses <b>starting from {}</b> are shown here. For buses that pass through, see the route pages. More services may exist — ask at the stand.".format(g.esc(disp)),
             "এখানে শুধু <b>{}</b> থেকে ছাড়া বাস দেখানো হয়েছে। মাঝপথের বাসের জন্য রুট পেজ দেখুন। আরও বাস থাকতে পারে — স্ট্যান্ডে জেনে নিন।".format(g.esc(v2.bnplace(stand))))

    # ---- FAQ (language buttons switch EN/BN blocks) ----
    en, bn = faq_pairs_stand(stand, buses, dest_groups)
    faq_html = "".join('<details class="faq only-en"><summary>{}</summary><p>{}</p></details>'.format(g.esc(q), g.esc(a)) for q, a in en)
    faq_html += "".join('<details class="faq only-bn"><summary>📌 {}</summary><p>{}</p></details>'.format(q, a) for q, a in bn)
    faq_section = '<div class="sec"><h3>' + L("FAQ", "প্রশ্নোত্তর") + '</h3></div>' + faq_html

    guide_section = _guide_section(g.slug(stand), disp)

    body = """{header}
<div class="wrap">
<div class="crumbs"><a href="../index.html">{home}</a> › <a href="./">{btt}</a> › <b>{disp}</b></div>
<div class="hero">
  <h1>{disp}</h1>
  <div class="hbn">{bn} — ছাড়ার সময়সূচি</div>
  <div class="chips">{chips}</div>
</div>
{popular}
{allsec}
<div class="note">📍 {note}</div>
{guide}
{faq}
<footer>{disp} · {n} listed buses · {d} destinations (alias-merged) · <a href="../about.html">About</a><a href="../contribute.html">Contribute</a><a href="../blog/">Blog</a><a href="../privacy-policy.html">Privacy</a></footer>
</div>
<script>{js}</script>
</body></html>""".format(header=HEADER,
                         home=L("Home", "হোম"), btt=L("Bus Timetable", "বাস টাইম টেবিল"),
                         disp=g.esc(disp), bn=g.esc(v2.bnplace(stand)), chips=chips,
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
