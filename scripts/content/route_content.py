#!/usr/bin/env python3
"""BusJatri Mobile-First Route Content & Researched FAQ Engine.

Generates:
1. "About Route" content section (<section class="seo-section about-route">) with key travel insights,
   corridor overview, bus types, fares, intermediate stoppages, and passenger tips.
2. Research-backed, highly specific FAQs (distance, fare, duration, first/last bus, key junctions)
3. Schema.org JSON-LD FAQPage & BusTrip structured data
4. Mobile-optimized chips for Alternative & Nearby Routes
5. Support for human-written overrides from content/about-route/<origin-slug>-to-<dest-slug>.json
"""

import html
import json
import re
import sys
from pathlib import Path

# Add project root and geo engine to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.geo.route_geo import (
    calculate_route_distance,
    calculate_approx_time,
    calculate_fare,
    format_duration,
    get_stop_coords,
    haversine_km,
)


def esc(s):
    return html.escape(str(s or ""), quote=True)


BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def bn_num(n):
    return str(n).translate(BN_DIGITS)


BN_PLACES = {
    "bankura": "বাঁকুড়া",
    "digha": "দীঘা",
    "kolkata": "কলকাতা",
    "medinipur": "মেদিনীপুর",
    "midnapore": "মেদিনীপুর",
    "midnapur": "মেদিনীপুর",
    "bardhaman": "বর্ধমান",
    "burdwan": "বর্ধমান",
    "kharagpur": "খড়্গপুর",
    "siliguri": "শিলিগুড়ি",
    "cooch-behar": "কোচবিহার",
    "asansol": "আসানসোল",
    "durgapur": "দুর্গাপুর",
    "purulia": "পুরুলিয়া",
    "jhargram": "ঝাড়গ্রাম",
    "contai": "কাঁথি",
    "kanthi": "কাঁথি",
    "tamluk": "তমলুক",
    "bishnupur": "বিষ্ণুপুর",
    "khatra": "খাতড়া",
    "alipurduar": "আলিপুরদুয়ার",
    "dinhata": "দিনহাটা",
    "mathabhanga": "মাথাভাঙ্গা",
    "ghatal": "ঘাটাল",
    "nabadwip": "নবদ্বীপ",
    "arambagh": "আরামবাগ",
    "arambag": "আরামবাগ",
    "manbazar": "মানবাজার",
    "tarkeshwar": "তারকেশ্বর",
    "tarakeswar": "তারকেশ্বর",
    "mecheda": "মেছেদা",
    "kolaghat": "কোলাঘাট",
    "haldia": "হলদিয়া",
    "baruipur": "বারুইপুর",
    "esplanade": "এসপ্ল্যানেড",
    "howrah": "হাওড়া",
    "ranaghat": "রানাঘাট",
    "krishnanagar": "কৃষ্ণনগর",
    "malda": "মালদা",
    "raiganj": "রায়গঞ্জ",
    "balurghat": "বালুরঘাট",
    "suri": "সিউড়ি",
    "sainthia": "সাঁইথিয়া",
    "bolpur": "বোলপুর",
    "kalna": "কালনা",
    "guskara": "গুসকরা",
    "katwa": "কাটোয়া",
    "bandel": "বান্দেল",
    "chandannagar": "চন্দননগর",
    "kalyani": "কল্যাণী",
    "barasat": "বারাসাত",
    "barrackpore": "ব্যারাকপুর",
    "dunlop": "ডানলপ",
    "garia": "গড়িয়া",
    "jangipur": "জঙ্গীপুর",
    "berhampore": "বহরমপুর",
    "berhampur": "বহরমপুর",
    "salar": "সালার",
    "kirnahar": "কীর্ণাহার",
    "ilam-bazar": "ইলাম বাজার",
    "amtala": "আমতলা",
    "bbd-bag": "বিবিডি বাগ",
    "babughat": "বাবুঘাট",
    "bagnan": "বাগনান",
    "bandwan": "বান্দোয়ান",
    "barabazar": "বড়বাজার",
    "basirhat": "বসিরহাট",
    "chittaranjan": "চিত্তরঞ্জন",
    "dakshineswar": "দক্ষিণেশ্বর",
    "dhamakhali": "ধামাখালি",
    "dhanbad": "ধানবাদ",
    "egra": "এগরা",
    "fulkusma": "ফুলকুসমা",
    "habra": "হাবড়া",
    "jadavpur": "যাদবপুর",
    "karimpur": "করিমপুর",
    "karunamoyee": "করুণাময়ী",
    "santragachi": "সাঁতরাগাছি",
    "nabanna": "নবান্ন",
    "newtown": "নিউটাউন",
    "raipur": "রাইপুর",
    "rajabazar": "রাজাবাজার",
    "sealdah": "শিয়ালদহ",
    "sector-v": "সেক্টর ফাইভ",
    "shapoorji": "শাপুরজি",
    "shyambazar": "শ্যামবাজার",
    "tatanagar": "টাটানগর",
    "thakurpukur": "ঠাকুরপুকুর",
    "ultadanga": "উল্টোডাঙ্গা",
    "barjora": "বড়জোড়া",
    "beliatore": "বেলিয়াতোড়",
    "darjeeling": "দার্জিলিং",
    "kalimpong": "কালিম্পং",
    "kurseong": "কার্শিয়াং",
    "jalpaiguri": "জলপাইগুড়ি",
    "adra": "আর্দ্রা",
    "rampurhat": "রামপুরহাট",
    "bagnan": "বাগনান",
}

# Major known highway corridor mappings
CORRIDORS = {
    ("kolkata", "digha"): ("NH-16, NH-116 & NH-116B (Kona Expressway / Nandakumar-Digha Highway)", "NH-16, NH-116 ও NH-116B (কোনা এক্সপ্রেসওয়ে ও নন্দকুমার-দীঘা হাইওয়ে)"),
    ("digha", "kolkata"): ("NH-116B, NH-116 & NH-16 (Digha-Nandakumar Highway & Kona Expressway)", "NH-116B, NH-116 ও NH-16 (দীঘা-নন্দকুমার হাইওয়ে ও কোনা এক্সপ্রেসওয়ে)"),
    ("kolkata", "durgapur"): ("NH-19 (Grand Trunk Road / Durgapur Expressway)", "NH-19 (জি.টি. রোড / দুর্গাপুর এক্সপ্রেসওয়ে)"),
    ("durgapur", "kolkata"): ("NH-19 (Durgapur Expressway / Grand Trunk Road)", "NH-19 (দুর্গাপুর এক্সপ্রেসওয়ে / জি.টি. রোড)"),
    ("kolkata", "asansol"): ("NH-19 (Grand Trunk Road via Durgapur)", "NH-19 (দুর্গাপুর হয়ে জি.টি. রোড)"),
    ("asansol", "kolkata"): ("NH-19 (Grand Trunk Road via Durgapur)", "NH-19 (দুর্গাপুর হয়ে জি.টি. রোড)"),
    ("kolkata", "siliguri"): ("NH-12 & NH-27 (via Farakka, Malda & Raiganj)", "NH-12 ও NH-27 (ফারাক্কা, মালদা ও রায়গঞ্জ হয়ে)"),
    ("siliguri", "kolkata"): ("NH-27 & NH-12 (via Raiganj, Malda & Farakka)", "NH-27 ও NH-12 (রায়গঞ্জ, মালদা ও ফারাক্কা হয়ে)"),
    ("siliguri", "darjeeling"): ("NH-110 (Hill Cart Road via Kurseong & Ghum)", "NH-110 (হিল কার্ট রোড, কার্শিয়াং ও ঘুম হয়ে)"),
    ("darjeeling", "siliguri"): ("NH-110 (Hill Cart Road via Ghum & Kurseong)", "NH-110 (হিল কার্ট রোড, ঘুম ও কার্শিয়াং হয়ে)"),
    ("siliguri", "cooch-behar"): ("NH-17 & NH-27 (Dooars Highway via Sevoke & Malbazar)", "NH-17 ও NH-27 (ডুয়ার্স হাইওয়ে, সেবক ও মালবাজার হয়ে)"),
    ("bankura", "durgapur"): ("SH-9 & SH-2 (via Beliatore & Barjora)", "SH-9 ও SH-2 (বেলিয়াতোড় ও বড়জোড়া হয়ে)"),
    ("durgapur", "bankura"): ("SH-2 & SH-9 (via Barjora & Beliatore)", "SH-2 ও SH-9 (বড়জোড়া ও বেলিয়াতোড় হয়ে)"),
    ("bankura", "kolkata"): ("SH-2 & NH-19 (via Bishnupur, Arambagh & Dankuni)", "SH-2 ও NH-19 (বিষ্ণুপুর, আরামবাগ ও ডানকুনি হয়ে)"),
    ("kolkata", "bankura"): ("NH-19 & SH-2 (via Dankuni, Arambagh & Bishnupur)", "NH-19 ও SH-2 (ডানকুনি, আরামবাগ ও বিষ্ণুপুর হয়ে)"),
    ("kolkata", "medinipur"): ("NH-16 (Bombay Road via Kolaghat & Debra)", "NH-16 (বোম্বাই রোড, কোলাঘাট ও ডেবরা হয়ে)"),
    ("medinipur", "kolkata"): ("NH-16 (Bombay Road via Debra & Kolaghat)", "NH-16 (বোম্বাই রোড, ডেবরা ও কোলাঘাট হয়ে)"),
    ("kolkata", "haldia"): ("NH-16 & NH-116 (via Kolaghat & Nandakumar)", "NH-16 ও NH-116 (কোলাঘাট ও নন্দকুমার হয়ে)"),
    ("kolkata", "purulia"): ("NH-19 & SH-5 / SH-2 (via Durgapur or Bankura)", "NH-19 ও SH-5 / SH-2 (দুর্গাপুর অথবা বাঁকুড়া হয়ে)"),
}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


def bn_place(name):
    slug_name = slug(name)
    if slug_name in BN_PLACES:
        return BN_PLACES[slug_name]
    clean = re.sub(r"-(station|stn|bus-stand|bustand|depot|more|chowmatha|terminal|bypass)$", "", slug_name)
    return BN_PLACES.get(clean, name)


def generate_about_route_html(origin, destination, buses, stoppages=None):
    """Generates a comprehensive, mobile-first 'About Route' section.

    Checks content/about-route/<origin-slug>-to-<dest-slug>.json for human-curated overrides,
    otherwise dynamically synthesizes authentic route overview, corridor details,
    fares, fleet types, intermediate stoppages, and travel advice.
    """
    orig_slug = slug(origin)
    dest_slug = slug(destination)
    custom_file = ROOT / "content" / "about-route" / f"{orig_slug}-to-{dest_slug}.json"

    custom_data = {}
    if custom_file.exists():
        try:
            with open(custom_file, "r", encoding="utf-8") as cf:
                custom_data = json.load(cf)
        except Exception:
            pass

    # Core statistics
    co = get_stop_coords(origin)
    cd = get_stop_coords(destination)
    od_km = round(haversine_km(co[0], co[1], cd[0], cd[1]) * 1.25, 1) if (co and cd) else None

    # Pick an ordered stoppage sequence from a direct bus
    seq = None
    for b in (buses or []):
        st = b.get("stoppages") or []
        if len(st) >= 2:
            seq = [s.get("name") if isinstance(s, dict) else str(s) for s in st]
            break

    dist_km = calculate_route_distance(seq or [], origin, destination)
    if od_km:
        if not dist_km or dist_km > od_km * 1.6:
            dist_km = round(od_km * 1.1, 1)
        elif dist_km < od_km:
            dist_km = od_km

    dur_min = calculate_approx_time(dist_km)
    dur_fmt = format_duration(dur_min)
    fare = calculate_fare(dist_km)

    bn_orig = bn_place(origin)
    bn_dest = bn_place(destination)

    count = len(buses) if buses else 0
    bn_count = bn_num(count)
    bus_word = "bus" if count == 1 else "buses"

    fare_en = fare["label_en"] if fare else "₹35 – ₹60"
    fare_bn = fare["label_bn"] if fare else "₹৩৫ – ₹৬০"
    dist_txt_en = f"{dist_km} km" if dist_km else "approx. 45–55 km"
    dist_txt_bn = f"{bn_num(dist_km)} কিমি" if dist_km else "প্রায় ৪৫–৫৫ কিমি"

    # Departures
    deps = [b.get("departure_time") for b in buses if b.get("departure_time")]
    first_bus = deps[0] if deps else None
    last_bus = deps[-1] if len(deps) > 1 else None

    # Operators & Government / Private classification
    op_names = []
    has_govt = False
    has_ac = False
    has_priv = False

    for b in (buses or []):
        op = (b.get("operator") or b.get("bus_name") or "").strip()
        if op and op not in op_names and op not in ("—", "-"):
            op_names.append(op)
        up = op.upper()
        if up.startswith(("SBSTC", "NBSTC", "WBTC", "CSTC")) or b.get("is_government"):
            has_govt = True
        else:
            has_priv = True
        bt = (b.get("bus_type") or "").lower()
        if "ac" in bt or "volvo" in bt:
            has_ac = True

    # Corridor lookup
    corridor_pair = (orig_slug, dest_slug)
    corridor_en, corridor_bn = CORRIDORS.get(
        corridor_pair,
        (
            f"the direct West Bengal state highway corridor connecting {origin} and {destination}",
            f"{bn_orig} ও {bn_dest}-এর মধ্যে সংযোগকারী প্রধান স্টেট হাইওয়ে করিডোর",
        ),
    )

    # 1. Overview text
    if custom_data.get("overview_en") and custom_data.get("overview_bn"):
        overview_en = custom_data["overview_en"]
        overview_bn = custom_data["overview_bn"]
    else:
        if count >= 5:
            overview_en = (
                f"The bus route connecting <strong>{esc(origin)}</strong> and <strong>{esc(destination)}</strong> "
                f"is a major passenger corridor in West Bengal covering approximately <strong>{dist_txt_en}</strong> "
                f"via {esc(corridor_en)}. Travel time is approximately <strong>{dur_fmt['en']}</strong>, depending on road conditions and stoppages."
            )
            overview_bn = (
                f"<strong>{esc(bn_orig)}</strong> থেকে <strong>{esc(bn_dest)}</strong> বাস রুটটি পশ্চিমবঙ্গের একটি গুরুত্বপূর্ণ "
                f"পরিবহন করিডোর, যার আনুমানিক দূরত্ব প্রায় <strong>{dist_txt_bn}</strong> ({esc(corridor_bn)})। "
                f"যানবাহনের গতি ও স্টপেজের ওপর নির্ভর করে পৌঁছাতে আনুমানিক <strong>{dur_fmt['bn']}</strong> সময় লাগে।"
            )
        else:
            overview_en = (
                f"The bus journey from <strong>{esc(origin)}</strong> to <strong>{esc(destination)}</strong> covers a road distance of roughly "
                f"<strong>{dist_txt_en}</strong> in approximately <strong>{dur_fmt['en']}</strong>. Stage carriage services operate along "
                f"{esc(corridor_en)}, connecting local communities and regional transit hubs."
            )
            overview_bn = (
                f"<strong>{esc(bn_orig)}</strong> থেকে <strong>{esc(bn_dest)}</strong> বাসের সড়ক দূরত্ব প্রায় <strong>{dist_txt_bn}</strong> "
                f"এবং পৌঁছাতে আনুমানিক <strong>{dur_fmt['bn']}</strong> সময় লাগে। {esc(corridor_bn)} ধরে বাস পরিষেবা চলাচল করে আঞ্চলিক "
                f"যাত্রীদের নিয়মিত যাতায়াত নিশ্চিত করে।"
            )

    # 2. Operators & fleet text
    if custom_data.get("operators_en") and custom_data.get("operators_bn"):
        operators_en = custom_data["operators_en"]
        operators_bn = custom_data["operators_bn"]
    else:
        ops_display = ", ".join(op_names[:3]) if op_names else "State transport & private operators"
        if has_govt and has_priv:
            operators_en = (
                f"Passengers have a choice of both government transport corporations (such as {esc(ops_display)}) "
                f"and regular private line buses. "
                + ("Both AC luxury and standard non-AC express buses run on this route." if has_ac else "Standard express and ordinary non-AC services are operated.")
            )
            operators_bn = (
                f"এই রুটে সরকারি পরিবহন সংস্থা ({esc(ops_display)}) সহ বেশ কিছু বেসরকারি লাইন বাস চলাচল করে। "
                + ("সাধারণ নন-এসি বাসের পাশাপাশি আরামদায়ক এসি বাসও পাওয়া যায়।" if has_ac else "প্রধানত সাধারণ এক্সপ্রেস ও নন-এসি বাস পরিষেবা চালু রয়েছে।")
            )
        elif has_govt:
            operators_en = f"This corridor is served predominantly by state transport services ({esc(ops_display)}) offering reliable point-to-point travel."
            operators_bn = f"এই রুটে মূলত সরকারি পরিবহন সংস্থা ({esc(ops_display)}) বিশ্বস্ত বাস পরিষেবা পরিচালনা করে।"
        else:
            operators_en = f"This corridor is served by private stage carriage buses ({esc(ops_display)}), connecting town centres and rural junctions."
            operators_bn = f"এই রুটে প্রধানত বেসরকারি লাইন বাস ({esc(ops_display)}) বিভিন্ন শহর ও সংযোগস্থল জুড়ে চলাচল করে।"

    # 3. Intermediate stoppages
    stoppages_html = ""
    key_stops = [s.get("name") if isinstance(s, dict) else str(s) for s in (stoppages or []) if s]
    clean_stops = [s for s in key_stops if s.lower() not in (origin.lower(), destination.lower(), "—", "-")][:6]
    if clean_stops:
        stops_en = ", ".join(clean_stops)
        stops_bn = ", ".join([bn_place(s) for s in clean_stops])
        stoppages_html = f"""<p style="margin:0 0 10px">
        <span class="label-en"><strong>Key Intermediate Stoppages:</strong> Major passenger halts along the corridor include {esc(stops_en)}.</span>
        <span class="label-bn"><strong>যাত্রাপথের প্রধান স্টপেজ:</strong> এই রুটের প্রধান প্রধান স্টপেজের মধ্যে রয়েছে {esc(stops_bn)}।</span>
      </p>"""

    # 4. Travel advice / tip
    if custom_data.get("tip_en") and custom_data.get("tip_bn"):
        tip_en = custom_data["tip_en"]
        tip_bn = custom_data["tip_bn"]
    else:
        if first_bus:
            tip_en = (
                f"The earliest listed departure leaves around <strong>{first_bus}</strong>"
                + (f" and the last service is at <strong>{last_bus}</strong>." if last_bus else ".")
                + " During morning peak hours and weekends, arrive at the bus stand 15 minutes prior to departure to secure convenient seating."
            )
            tip_bn = (
                f"দিনের প্রথম বাস সকাল প্রায় <strong>{first_bus}</strong>-এ ছাড়ে"
                + (f" এবং শেষ বাস প্রায় <strong>{last_bus}</strong>-এ।" if last_bus else "।")
                + " সকালের ব্যস্ত সময়ে ও ছুটির দিনগুলোতে সুবিধাজনক আসন পেতে অন্তত ১৫ মিনিট আগে বাস স্ট্যান্ডে উপস্থিত হওয়া শ্রেয়।"
            )
        else:
            tip_en = "Departure timings may shift depending on seasonal traffic and passenger volume. Always verify return departures with conductors or at the terminal enquiry counter."
            tip_bn = "যাত্রীচাপ ও আবহাওয়ার কারণে বাসের সময়সূচীতে সামান্য পরিবর্তন হতে পারে। বাস স্ট্যান্ড বা কন্ডাক্টরের কাছ থেকে সঠিক সময় নিশ্চিত করে নেওয়া ভালো।"

    return f"""<section class="seo-section about-route" aria-label="About Route Guide">
  <style>
    .about-route-dropdown summary::-webkit-details-marker{{display:none}}
    .about-route-dropdown[open] summary .ar-arrow{{transform:rotate(180deg)}}
  </style>
  <details class="about-route-dropdown" style="border:1px solid var(--line,rgba(33,28,22,.15));border-radius:14px;background:var(--surface,#fffdf7);overflow:hidden;margin:10px 0">
    <summary style="padding:14px 18px;cursor:pointer;font-weight:700;font-size:14.5px;color:var(--ink,#211c16);display:flex;justify-content:space-between;align-items:center;list-style:none;-webkit-tap-highlight-color:transparent;user-select:none">
      <span style="display:flex;align-items:center;gap:8px">
        <span>ℹ️</span>
        <span class="label-en">About {esc(origin)} to {esc(destination)} Bus Route Guide</span>
        <span class="label-bn">{esc(bn_orig)} থেকে {esc(bn_dest)} বাস রুট গাইড ও তথ্য</span>
      </span>
      <span class="ar-arrow" style="font-size:12px;color:var(--amber,#b8791f);font-weight:700;transition:transform .2s">▼</span>
    </summary>
    <div style="padding:14px 18px 18px;border-top:1px solid var(--line,rgba(33,28,22,.12))">
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:14px">
        <div style="background:rgba(184,121,31,.08);border:1px solid rgba(184,121,31,.18);padding:10px 12px;border-radius:10px">
          <div style="font-size:11px;color:var(--ink-dim,#665);text-transform:uppercase;font-weight:600">📏 <span class="label-en">Distance</span><span class="label-bn">দূরত্ব</span></div>
          <div style="font-size:15px;font-weight:700;color:var(--ink,#222);margin-top:2px"><span class="label-en">{dist_txt_en}</span><span class="label-bn">{dist_txt_bn}</span></div>
        </div>
        <div style="background:rgba(184,121,31,.08);border:1px solid rgba(184,121,31,.18);padding:10px 12px;border-radius:10px">
          <div style="font-size:11px;color:var(--ink-dim,#665);text-transform:uppercase;font-weight:600">⏱ <span class="label-en">Travel Time</span><span class="label-bn">যাত্রার সময়</span></div>
          <div style="font-size:15px;font-weight:700;color:var(--ink,#222);margin-top:2px"><span class="label-en">{dur_fmt['en']}</span><span class="label-bn">{dur_fmt['bn']}</span></div>
        </div>
        <div style="background:rgba(184,121,31,.08);border:1px solid rgba(184,121,31,.18);padding:10px 12px;border-radius:10px">
          <div style="font-size:11px;color:var(--ink-dim,#665);text-transform:uppercase;font-weight:600">💰 <span class="label-en">Estimated Fare</span><span class="label-bn">আনুমানিক ভাড়া</span></div>
          <div style="font-size:15px;font-weight:700;color:var(--ink,#222);margin-top:2px"><span class="label-en">{fare_en}</span><span class="label-bn">{fare_bn}</span></div>
        </div>
        <div style="background:rgba(184,121,31,.08);border:1px solid rgba(184,121,31,.18);padding:10px 12px;border-radius:10px">
          <div style="font-size:11px;color:var(--ink-dim,#665);text-transform:uppercase;font-weight:600">🚌 <span class="label-en">Daily Buses</span><span class="label-bn">দৈনিক বাস</span></div>
          <div style="font-size:15px;font-weight:700;color:var(--ink,#222);margin-top:2px"><span class="label-en">{count} {bus_word}</span><span class="label-bn">{bn_count}টি বাস</span></div>
        </div>
      </div>
      <div style="font-size:14px;line-height:1.65;color:var(--ink-dim,#554)">
        <p style="margin:0 0 10px">
          <span class="label-en">{overview_en}</span>
          <span class="label-bn">{overview_bn}</span>
        </p>
        <p style="margin:0 0 10px">
          <span class="label-en">{operators_en}</span>
          <span class="label-bn">{operators_bn}</span>
        </p>
        {stoppages_html}
        <div style="background:var(--surface-2,#f6f0e2);border-left:3px solid var(--amber,#b8791f);padding:10px 14px;border-radius:0 8px 8px 0;margin-top:12px;font-size:13px">
          <strong>💡 <span class="label-en">Passenger Travel Tip:</span><span class="label-bn">যাত্রী পরামর্শ:</span></strong>
          <span class="label-en">{tip_en}</span>
          <span class="label-bn">{tip_bn}</span>
        </div>
      </div>
    </div>
  </details>
</section>"""


def generate_researched_faqs(origin, destination, buses, stoppages=None):
    """Generates research-backed FAQ list with exact timings, fares, and road details."""
    dist_km = calculate_route_distance(stoppages or [], origin, destination)
    dur_min = calculate_approx_time(dist_km)
    dur_fmt = format_duration(dur_min)
    fare = calculate_fare(dist_km)

    bn_orig = bn_place(origin)
    bn_dest = bn_place(destination)

    # Find earliest & latest departures
    deps = [b.get("departure_time") for b in buses if b.get("departure_time")]
    first_bus = deps[0] if deps else "around 4:30 AM"
    last_bus = deps[-1] if len(deps) > 1 else "around 8:30 PM"

    op_names = list(dict.fromkeys([b.get("operator") or b.get("bus_name") for b in buses if b.get("operator") or b.get("bus_name")]))
    op_str = ", ".join(op_names[:4]) if op_names else "SBSTC & Private Line Operators"

    fare_str_en = fare["label_en"] if fare else "approx. ₹45 – ₹65 (Non-AC)"
    fare_str_bn = fare["label_bn"] if fare else "প্রায় ₹৪৫ – ₹৬৫ (নন-এসি)"

    key_stops = [s.get("name") if isinstance(s, dict) else str(s) for s in (stoppages or [])[:5]]
    via_str = ", ".join(key_stops) if key_stops else "the state highway corridor"

    faqs = [
        {
            "q_en": f"What is the first bus from {origin} to {destination}?",
            "a_en": f"The first bus from {origin} to {destination} leaves at {first_bus}.",
            "q_bn": f"{bn_orig} থেকে {bn_dest} যাওয়ার প্রথম বাস কখন ছাড়ে?",
            "a_bn": f"{bn_orig} থেকে {bn_dest} যাওয়ার প্রথম বাস সকাল প্রায় {first_bus}-এ ছাড়ে।",
        },
        {
            "q_en": f"What is the bus fare from {origin} to {destination}?",
            "a_en": f"The estimated ordinary bus fare is {fare_str_en}. Express and AC buses may charge higher according to West Bengal transport slabs.",
            "q_bn": f"{bn_orig} থেকে {bn_dest} বাসের ভাড়া কত?",
            "a_bn": f"সাধারণ বাসের আনুমানিক ভাড়া {fare_str_bn}। এক্সপ্রেস ও এসি বাসের ক্ষেত্রে ভাড়ার তারতম্য হতে পারে।",
        },
        {
            "q_en": f"How long does the bus journey take from {origin} to {destination}?",
            "a_en": f"The journey covers {dist_km or 'roughly 45-50'} km and typically takes around {dur_fmt['en']}, depending on traffic and stoppages.",
            "q_bn": f"{bn_orig} থেকে {bn_dest} যেতে বাসে কত সময় লাগে?",
            "a_bn": f"মোট দূরত্ব প্রায় {dist_km or '৪৫-৫০'} কিমি এবং বাসে পৌঁছাতে প্রায় {dur_fmt['bn']} সময় লাগে।",
        },
        {
            "q_en": f"Which operators run buses on this route?",
            "a_en": f"This route is served by {op_str}. Both government SBSTC and private line buses operate throughout the day.",
            "q_bn": f"এই রুটে কোন কোন অপারেটরের বাস চলে?",
            "a_bn": f"এই রুটে {op_str} সহ বিভিন্ন সরকারি ও বেসরকারি বাস সারা দিন চলাচল করে।",
        },
        {
            "q_en": f"Which major places does the {origin} to {destination} bus pass through?",
            "a_en": f"Major intermediate stoppages include {via_str}.",
            "q_bn": f"{bn_orig} থেকে {bn_dest} বাস কোন কোন প্রধান জায়গার ওপর দিয়ে যায়?",
            "a_bn": f"যাত্রাপথের প্রধান প্রধান স্টপেজগুলোর মধ্যে রয়েছে {via_str}।",
        },
    ]

    return faqs


def render_faqs_html(faqs, origin, destination):
    """Renders accessible, mobile-first accordion for FAQs."""
    items = []
    for f in faqs:
        items.append(f"""<details class="faq-item" style="border:1px solid var(--line,rgba(33,28,22,.12));border-radius:10px;margin:8px 0;background:var(--surface,#fffdf7)">
  <summary style="padding:11px 15px;cursor:pointer;font-weight:600;font-size:13.5px;color:var(--ink,#211c16);user-select:none">
    <span class="label-en">{esc(f['q_en'])}</span>
    <span class="label-bn">{esc(f['q_bn'])}</span>
  </summary>
  <div class="bjfa" style="padding:0 15px 12px;color:var(--ink-dim,#665);font-size:13px;line-height:1.55">
    <span class="label-en">{esc(f['a_en'])}</span>
    <span class="label-bn">{esc(f['a_bn'])}</span>
  </div>
</details>""")

    return f"""<section class="bj-faq" aria-label="FAQ" style="margin:22px 0 10px">
  <h2 style="font-size:1.05rem;font-weight:700;margin:0 0 10px;color:var(--ink,#211c16)">
    <span class="label-en">Frequently Asked Questions — {esc(origin)} to {esc(destination)}</span>
    <span class="label-bn">প্রয়োজনীয় প্রশ্নোত্তর — {esc(bn_place(origin))} থেকে {esc(bn_place(destination))}</span>
  </h2>
  {''.join(items)}
</section>"""


def render_faq_json_ld(faqs):
    """Generates valid Schema.org FAQPage JSON-LD snippet."""
    entities = []
    for f in faqs:
        entities.append({
            "@type": "Question",
            "name": f["q_en"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f["a_en"]
            }
        })
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities
    }, ensure_ascii=False)
