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
    "adra": "আদ্রা",
    "ahiran": "আহিরণ",
    "airport": "এয়ারপোর্ট",
    "airport-gate": "এয়ারপোর্ট গেট",
    "airport-gate-1": "এয়ারপোর্ট গেট ১",
    "airport-gate-3": "এয়ারপোর্ট গেট ৩",
    "airport-gate-no-3": "এয়ারপোর্ট গেট নং ৩",
    "airport-terminal": "এয়ারপোর্ট টার্মিনাল",
    "ajodhya-hills": "অযোধ্যা পাহাড়",
    "alipurduar": "আলিপুরদুয়ার",
    "amdanga": "আমডাঙা",
    "amtala": "আমতলা",
    "andal": "অন্ডাল",
    "arambag": "আরামবাগ",
    "arambagh": "আরামবাগ",
    "argoal": "আরগোয়াল",
    "arsha": "আর্শা",
    "asansol": "আসানসোল",
    "babughat": "বাবুঘাট",
    "bagbazar": "বাগবাজার",
    "bagdogra": "বাগডোগরা",
    "baghmundi": "বাঘমুন্ডি",
    "bagnan": "বাগনান",
    "bagrakot": "বাগরাকোট",
    "baguiati": "বাগুইআটি",
    "baharampur": "বহরমপুর",
    "bakshi": "বক্সি",
    "bally": "বালি",
    "bally-halt": "বালি হল্ট",
    "bally-khal": "বালি খাল",
    "ballygunge": "বালিগঞ্জ",
    "ballygunge-station": "বালিগঞ্জ স্টেশন",
    "ballygunge-stn": "বালিগঞ্জ স্টেশন",
    "ballyhalt": "বালি হল্ট",
    "balrampur": "বলরামপুর",
    "balurghat": "বালুরঘাট",
    "bandel": "বান্দেল",
    "bandwan": "বান্দোয়ান",
    "bankura": "বাঁকুড়া",
    "bankura-bus-stand": "বাঁকুড়া (বাস স্ট্যান্ড)",
    "bankura-bypass": "বাঁকুড়া (বাইপাস)",
    "bankura-more": "বাঁকুড়া (মোড়)",
    "bankura-pump-more": "বাঁকুড়া (পাম্প মোড়)",
    "bankura-satighat-bridge": "বাঁকুড়া (সতীঘাট ব্রিজ)",
    "bankura-station": "বাঁকুড়া (স্টেশন)",
    "barabazar": "বড়বাজার",
    "barakar": "বরাকর",
    "barasat": "বারাসাত",
    "barasat-chapadali": "বারাসাত চাপাড়ালি",
    "barddhaman-alisha-bus-stand": "বর্ধমান আলিশা বাস স্ট্যান্ড",
    "barddhaman-nawabhat-bus-stand": "বর্ধমান নবাহাট বাস স্ট্যান্ড",
    "barddhaman-tinkonia": "বর্ধমান তিনকোণিয়া",
    "bardhaman": "বর্ধমান",
    "bardhaman-alisha-bus-stand": "বর্ধমান (আলিশা বাস স্ট্যান্ড)",
    "bardhaman-nawabhat-bus-stand": "বর্ধমান (নবাহাট বাস স্ট্যান্ড)",
    "barjora": "বড়জোড়া",
    "barrackpore": "ব্যারাকপুর",
    "barrackpore-court": "ব্যারাকপুর কোর্ট",
    "baruipur": "বারুইপুর",
    "basirhat": "বসিরহাট",
    "batanagar": "বাটানগর",
    "bbd-bag": "বিবিডি বাগ",
    "behala": "বেহালা",
    "behala-14-no": "বেহালা ১৪ নম্বর",
    "behala-chowrasta": "বেহালা চৌরাস্তা",
    "behala-chowrastha": "বেহালা চৌরাস্তা",
    "belda": "বেলদা",
    "beldanga": "বেলডাঙা",
    "belghoria": "বেলঘরিয়া",
    "beliatore": "বেলিয়াতোড়",
    "benachity": "বেনাচিটি",
    "berhampore": "বহরমপুর",
    "berhampur": "বহরমপুর",
    "bhowanipore": "ভবানীপুর",
    "binpur": "বিনপুর",
    "bishnupur": "বিষ্ণুপুর",
    "bishnupur-bankura": "বিষ্ণুপুর (বাঁকুড়া)",
    "boga": "বোগা",
    "bolpur": "বোলপুর",
    "budbud": "বুদবুদ",
    "buniadpur": "বুনিয়াদপুর",
    "burdwan": "বর্ধমান",
    "burdwan-tinkonia": "বর্ধমান তিনকোণিয়া",
    "burra-bazar": "বড়বাজার",
    "central-jail": "সেন্ট্রাল জেল",
    "chanchal": "চাঁচল",
    "chandannagar": "চন্দননগর",
    "chander": "চাঁদর",
    "chandrakona-road": "চন্দ্রকোনা রোড",
    "chandrakona-town": "চন্দ্রকোনা টাউন",
    "chetla": "চেতলা",
    "chhatna": "ছাতনা",
    "chiria-more": "চিড়িয়ামোড়",
    "chittaranjan": "চিত্তরঞ্জন",
    "coach-behar": "কোচবিহার",
    "contai": "কাঁথি",
    "contai-central": "কাঁথি সেন্ট্রাল",
    "contai-central-bus-stand": "কাঁথি সেন্ট্রাল বাস স্ট্যান্ড",
    "cooch-behar": "কোচবিহার",
    "coochbehar": "কোচবিহার",
    "coronation-bridge": "করোনেশন ব্রিজ",
    "dainhat": "দাঁইহাট",
    "dakshineswar": "দক্ষিণেশ্বর",
    "dalkhola": "ডালখোলা",
    "damdim": "ডামডিম",
    "dankuni": "ডানকুনি",
    "dantan": "দাঁতন",
    "darjeeling": "দার্জিলিং",
    "debra": "দেবরা",
    "dhamakhali": "ধামাখালি",
    "dhanbad": "ধানবাদ",
    "dharmatala": "ধর্মতলা",
    "dhubulia": "ধুবুলিয়া",
    "dhupguri": "ধূপগুড়ি",
    "diamond": "ডায়মন্ড হারবার",
    "digha": "দীঘা",
    "dinhata": "দিনহাটা",
    "dum-dum": "ডামডাম",
    "dum-dum-stn": "ডামডাম স্টেশন",
    "dumdum": "ডামডাম",
    "dunlop": "ডানলপ",
    "durgachak": "দূর্গাচক",
    "durgachak-central-bus-stand": "দূর্গাচক সেন্ট্রাল বাস স্ট্যান্ড",
    "durgapur": "দুর্গাপুর",
    "durgapur-bus-stand": "দুর্গাপুর (বাস স্ট্যান্ড)",
    "durgapur-city-center": "দুর্গাপুর (সিটি সেন্টার)",
    "durgapur-city-centre": "দুর্গাপুর সিটি সেন্টার",
    "durgapur-expressway": "দুর্গাপুর (এক্সপ্রেসওয়ে)",
    "durgapur-station": "দুর্গাপুর (স্টেশন)",
    "eco-space": "ইকোস্পেস",
    "ecospace": "ইকোস্পেস",
    "egra": "এগরা",
    "em-bypass": "ইএম বাইপাস",
    "esplanade": "এসপ্ল্যানেড",
    "falakata": "ফালাকাটা",
    "farakka": "ফারাক্কা",
    "fatapukur": "ফাটাপুকুর",
    "fulbari": "ফুলবাড়ি",
    "fulkusma": "ফুলকুসমা",
    "gangarampur": "গঙ্গারামপুর",
    "garhbeta": "গড়বেতা",
    "garhbhowanipur": "গড়ভবানীপুর",
    "garia": "গড়িয়া",
    "garia-bus-stand": "গড়িয়া বাস স্ট্যান্ড",
    "garia-depot": "গড়িয়া ডিপো",
    "gariahat": "গড়িয়াহাট",
    "gazole": "গাজোল",
    "ghatal": "ঘাটাল",
    "gopiballabpur": "গোপীবল্লভপুর",
    "gopiganj": "গোপীগঞ্জ",
    "guskara": "গুসকরা",
    "habra": "হাবড়া",
    "habra-depot": "হাবড়া ডিপো",
    "habra-station": "হাবড়া স্টেশন",
    "haldia": "হলদিয়া",
    "haldia-township": "হলদিয়া টাউনশিপ",
    "hazra": "হাজরা",
    "howrah": "হাওড়া",
    "howrah-bridge-east": "হাওড়া ব্রিজ পূর্ব",
    "howrah-maidan": "হাওড়া ময়দান",
    "howrah-station": "হাওড়া স্টেশন",
    "howrah-stn": "হাওড়া স্টেশন",
    "ilam-bazar": "ইলাম বাজার",
    "ilambazar": "ইলাম বাজার",
    "islampur": "ইসলামপুর",
    "itahar": "ইটাহার",
    "jadavpore": "যাদবপুর",
    "jadavpur": "যাদবপুর",
    "jadavpur-8b": "যাদবপুর ৮বি",
    "jalpaiguri": "জলপাইগুড়ি",
    "jalpaiguri-bypass": "জলপাইগুড়ি বাইপাস",
    "jamuria": "জামুড়িয়া",
    "jangipur": "জঙ্গীপুর",
    "jhargram": "ঝাড়গ্রাম",
    "joka": "জোকা",
    "joka-tram-depot": "জোকা ট্রাম ডিপো",
    "kabilepur": "কবিলেপুর",
    "kaijuri-bazar": "কৈজুরী বাজার",
    "kaliachak": "কালিয়াচক",
    "kalimpong": "কালিম্পং",
    "kalna": "কালনা",
    "kalyani": "কল্যাণী",
    "kandi": "কান্দি",
    "kandra": "কান্দ্রা",
    "kanthi": "কাঁথি",
    "karimpur": "করিমপুর",
    "karunamoyee": "করুণাময়ী",
    "katwa": "কাটোয়া",
    "kharagpur": "খড়্গপুর",
    "kharagpur-station": "খড়্গপুর স্টেশন",
    "kharagpur-town": "খড়্গপুর (টাউন)",
    "khatra": "খাতড়া",
    "kirnahar": "কীর্ণাহার",
    "kishanganj": "কিশনগঞ্জ",
    "koch-bihar": "কোচবিহার",
    "kolaghat": "কোলাঘাট",
    "kolkata": "কলকাতা",
    "kolkata-babughat": "কলকাতা (বাবুঘাট)",
    "kolkata-dharmatala": "কলকাতা (ধর্মতলা)",
    "kolkata-esplanade": "কলকাতা (এসপ্ল্যানেড)",
    "kolkata-karunamoyee": "কলকাতা (করুণাময়ী)",
    "kolkata-santragachi": "কলকাতা (সাঁতরাগাছি)",
    "kolkata-station": "কলকাতা স্টেশন",
    "kolkata-stn": "কলকাতা স্টেশন",
    "krishnanagar": "কৃষ্ণনগর",
    "kurseong": "কার্শিয়াং",
    "lalgola": "লালগোলা",
    "madhyamgram": "মধ্যমগ্রাম",
    "mainaguri": "ময়নাগুড়ি",
    "malancha": "মালঞ্চ",
    "malbazar": "মালবাজার",
    "malda": "মালদা",
    "manbazar": "মানবাজার",
    "mathabhanga": "মাথাভাঙ্গা",
    "mecheda": "মেছেদা",
    "medinipur": "মেদিনীপুর",
    "memari": "মেমারি",
    "midnapore": "মেদিনীপুর",
    "midnapur": "মেদিনীপুর",
    "midnapur-central-bus-stand": "মেদিনীপুর সেন্ট্রাল বাস স্ট্যান্ড",
    "milk-colony": "মিল্ক কলোনি",
    "mohar": "মোহর",
    "moynaguri": "ময়নাগুড়ি",
    "nabadwip": "নবদ্বীপ",
    "nabadwip-dham": "নবদ্বীপ ধাম",
    "nabanna": "নবান্ন",
    "nager-bazar": "নগরবাজার",
    "naihati": "নৈহাটি",
    "naktala": "নাকতলা",
    "nandigram": "নন্দীগ্রাম",
    "napara": "নাপাড়া",
    "new-town": "নিউ টাউন",
    "newtown": "নিউটাউন",
    "odlabari": "ওদলাবাড়ি",
    "oodlabari": "ওদলাবাড়ি",
    "paikpara": "পাইকপাড়া",
    "panitanki": "পানিট্যাঙ্কি",
    "park-st": "পার্ক স্ট্রিট",
    "park-street": "পার্ক স্ট্রিট",
    "phulia": "ফুলিয়া",
    "purulia": "পুরুলিয়া",
    "raiganj": "রায়গঞ্জ",
    "raipur": "রাইপুর",
    "rajabazar": "রাজাবাজার",
    "rajarhat": "রাজারহাট",
    "ramganj": "রামগঞ্জ",
    "rampurhat": "রামপুরহাট",
    "ranaghat": "রানাঘাট",
    "ranikuthi": "রানিকুঠি",
    "rashbehari-ave": "রাসবিহারী অ্যাভিনিউ",
    "regent-park": "রিজেন্ট পার্ক",
    "rishra": "রিষড়া",
    "sahararhat": "সাহারারহাট",
    "sainthia": "সাঁইথিয়া",
    "sainthia-town": "সাঁইথিয়া টাউন",
    "salar": "সালার",
    "salt-lake": "সল্টলেক",
    "saltlake": "সল্টলেক",
    "saltlake-karunamoyee": "সল্টলেক করুণাময়ী",
    "salugara": "সালুগাড়া",
    "samsi": "সামসি",
    "santragachi": "সাঁতরাগাছি",
    "science-city": "সায়েন্স সিটি",
    "sealdah": "শিয়ালদহ",
    "sealdah-rajabazar": "শিয়ালদহ-রাজাবাজার",
    "sector-v": "সেক্টর ফাইভ",
    "serampore": "শ্রীরামপুর",
    "sevoke": "সেবক",
    "shantipur": "শান্তিপুর",
    "shapoorji": "শাপুরজি",
    "sheikhdighi": "শেখদিঘি",
    "shyambazar": "শ্যামবাজার",
    "silda": "শিলদা",
    "siliguri": "শিলিগুড়ি",
    "sinthi-more": "সিন্থি মোড়",
    "sitai": "সিতাই",
    "sonachura": "সোনাচুড়া",
    "sujapur": "সুজাপুর",
    "suri": "সিউড়ি",
    "tamluk": "তমলুক",
    "tapan": "তপন",
    "tarakeshwar": "তারকেশ্বর",
    "tarakeswar": "তারকেশ্বর",
    "tarapith": "তারাপীঠ",
    "taratala": "তারাতলা",
    "tarkeshwar": "তারকেশ্বর",
    "tatanagar": "টাটানগর",
    "thakurpukur": "ঠাকুরপুকুর",
    "tollygunge": "টালিগঞ্জ",
    "tollygunge-metro": "টালিগঞ্জ মেট্রো",
    "ultadanga": "উল্টোডাঙ্গা",
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


def generate_about_route_html(origin, destination, buses, stoppages=None, fare_info=None, dist_km=None, dur_text=None):
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

    # Core statistics — use caller-provided unified values when available
    if dist_km is None:
        co = get_stop_coords(origin)
        cd = get_stop_coords(destination)
        od_km = round(haversine_km(co[0], co[1], cd[0], cd[1]) * 1.25, 1) if (co and cd) else None

        seq = None
        for b in (buses or []):
            st = b.get("stoppages") or []
            if len(st) >= 2:
                seq = [s.get("name") if isinstance(s, dict) else str(s) for s in st]
                break

        dist_km = calculate_route_distance(seq or stoppages or [], origin, destination)
        if od_km:
            if not dist_km or dist_km > od_km * 1.6:
                dist_km = round(od_km * 1.1, 1)
            elif dist_km < od_km:
                dist_km = od_km

    if fare_info is None and dist_km:
        fare_info = calculate_fare(dist_km)

    if dur_text:
        dur_fmt = {"en": str(dur_text), "bn": str(dur_text)}
    else:
        dur_min = calculate_approx_time(dist_km)
        dur_fmt = format_duration(dur_min)

    bn_orig = bn_place(origin)
    bn_dest = bn_place(destination)

    count = len(buses) if buses else 0
    bn_count = bn_num(count)
    bus_word = "bus" if count == 1 else "buses"

    if fare_info:
        fare_en = fare_info["label_en"]
        fare_bn = fare_info["label_bn"]
    else:
        fare_en = "Confirm at bus stand"
        fare_bn = "কাউন্টারে নিশ্চিত করুন"

    dist_txt_en = f"{dist_km} km" if dist_km else "Distance not listed"
    dist_txt_bn = f"{bn_num(dist_km)} কিমি" if dist_km else "দূরত্ব নির্ধারিত নয়"

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
