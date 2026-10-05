#!/usr/bin/env python3
"""Fill STOPS/LEGS on Kolkata city-route pages + SEO/interlinking + bilingual journey labels.

1. 29 routes (58 pages) get stop-wise STOPS + LEGS data (stop-wise journey view).
   Sources: official WBTC/wbtconline route paths (direct matches) + corridor-
   composites built from official paths of sibling routes.
   Times: official first/last per trip; mid-stop times interpolated (≈ in UI). Departure-only routes remain departure-only until official arrival data exists.
2. Static crawlable stop list added to every city route page (124 pages).
3. Related-routes internal links on every city route page.
4. /bus-time-table/ index links to the Kolkata city bus hub.
5. Major stand pages link to their city routes.

Idempotent: markers city-stops-v1 / city-rel-v1 / city-hub-v1 / city-stand-v1.
DRY by default; pass --write to apply.
"""
import json, re, sys, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv  # route-page rebuild runs through CI
WRITE = not DRY

# ---------------------------------------------------------------- Bengali ----
BN = {
 "Airport Gate-1":"এয়ারপোর্ট গেট-১", "Howrah Stn":"হাওড়া স্টেশন", "Howrah Bridge East":"হাওড়া ব্রিজ ইস্ট", "BBD Bag":"বিবিডি বাগ", "Esplanade":"এসপ্ল্যানেড", "Lalbazar":"লালবাজার", "Manicktala":"মানিকতলা", "Kankurgachi":"কাঁকুড়গাছি", "Kaikhali":"কৈখালি", "Tobin Rd":"টোবিন রোড", "Sinthi More":"সিঁথি মোড়", "Chiriamore":"চিড়িয়ামোড়", "Shyambazar":"শ্যামবাজার", "Grey St":"গ্রে স্ট্রিট", "Vivekananda Rd":"বিবেকানন্দ রোড", "Colutala St":"কলুটোলা স্ট্রিট", "C.R. Ave":"সি আর অ্যাভিনিউ", "Park Street":"পার্ক স্ট্রিট", "Hazra":"হাজরা", "Rashbehari Ave":"রাসবিহারী অ্যাভিনিউ", "Deshapriya Park":"দেশপ্রিয় পার্ক", "Gariahat":"গড়িয়াহাট", "Howrah Station":"হাওড়া স্টেশন", "Garia Depot":"গড়িয়া ডিপো", "Ballygunge Stn":"বালিগঞ্জ স্টেশন", "Ballygunge":"বালিগঞ্জ", "Dunlop":"ডানলপ", "New Town":"নিউ টাউন", "Ecospace":"ইকোস্পেস", "Ultadanga":"উল্টোডাঙ্গা", "Karunamayee":"করুণাময়ী","Ajoynagar":"অজয়নগর","Akra Rabindranagar":"আকরা রবীন্দ্রনগর",
 "Alipore Zoo":"আলিপুর চিড়িয়াখানা","Amtala":"আমতলা","Baguihati":"বাগুইয়াটি","Bakultala":"বকুলতলা",
 "Bally Khal":"বালি খাল","Bantala IT Park":"বানতলা আইটি পার্ক","Baranagar":"বরানগর","Baruipur":"বারুইপুর",
 "Batamore":"বাটামোড়","Beckbagan":"বেকবাগান","Behala 3A Stand":"বেহালা ৩এ স্ট্যান্ড","Behala P.S":"বেহালা থানা",
 "Belghoria Expressway":"বেলঘরিয়া এক্সপ্রেসওয়ে","Beliaghata Xing":"বেলেঘাটা ক্রসিং","Belur":"বেলুড়",
 "Betore More":"বেতোর মোড়","Bijan Setu":"বিজন সেতু","Bondel Gate":"বন্দেল গেট","Casurina Ave":"ক্যাসুরিনা অ্যাভিনিউ",
 "Colutola Xing":"কলুটোলা ক্রসিং","Cossipore":"কাশীপুর","Dakghar":"ডাকঘর","Dhalai Bridge":"ধলাই ব্রিজ",
 "Dum Dum 7 Tanks":"দমদম সাত ট্যাংক","Durganagar":"দুর্গানগর","E.M. Bypass":"ইএম বাইপাস",
 "Eden City Gate":"এডেন সিটি গেট","Esplanade East":"এসপ্ল্যানেড ইস্ট","Garia Depot":"গড়িয়া ডিপো",
 "Garia Stn":"গড়িয়া স্টেশন","Garia-6":"গড়িয়া-৬","Girish Park":"গিরিশ পার্ক","Haridevpur":"হরিদেবপুর",
 "Harinavi":"হরিণাভি","Hidco Bhavan":"হিডকো ভবন","Howrah Maidan":"হাওড়া ময়দান","Jalkol":"জলকল",
 "Jingirabazar":"জিঙ্গিরাবাজার","KBKC":"কেবিকেসি","Kadapara":"কাদাপাড়া","Kalighat":"কালীঘাট",
 "Kamalgazi More":"কামালগাজি মোড়","Karunamayee":"করুণাময়ী","Khidirpore":"খিদিরপুর",
 "Kolkata Stn":"কলকাতা স্টেশন","Laketown":"লেকটাউন","Lalbazar":"লালবাজার","M.G. Rd":"এম জি রোড",
 "Malancha Bazar":"মালাঞ্চা বাজার","Mandirtala":"মন্দিরতলা","Minto Park":"মিন্টো পার্ক",
 "Mission Gate":"মিশন গেট","Mollar Gate":"মল্লার গেট","Momonpore":"মোমনপুর","Nabadiganta":"নবদিগন্ত",
 "Narkelbagan":"নারকেলবাগান","Nayabad Bus Stand":"নয়াবাদ বাস স্ট্যান্ড","New Town Bus Stand":"নিউ টাউন বাস স্ট্যান্ড",
 "New Town Central Stand":"নিউ টাউন সেন্ট্রাল স্ট্যান্ড","Nungimore":"নুঙ্গি মোড়","Nutan Para":"নতুন পাড়া",
 "PTS":"পিটিএস","PTS More":"পিটিএস মোড়","Paharpur":"পাহাড়পুর","Paikpara":"পাইকপাড়া","Pailan":"পাইলান",
 "Panchasayar":"পঞ্চসায়র","Panchayat Bhawan":"পঞ্চায়েত ভবন","Paribesh Bhaban":"পরিবেশ ভবন",
 "Park Circus":"পার্ক সার্কাস","R.B. Ave":"আর বি অ্যাভিনিউ","R.B. Ave Xing":"আর বি অ্যাভিনিউ ক্রসিং",
 "R.B. Avenue":"আর বি অ্যাভিনিউ","Raidighi":"রাইদিঘি","Rampur":"রামপুর","Sahapur":"সাহাপুর",
 "Sakuntala Park":"শকুন্তলা পার্ক","Santoshpur Stn":"সন্তোষপুর স্টেশন","Santragachi":"সাঁতরাগাছি",
 "Taratala Depot":"তারাতলা ডিপো","Tata Medical Centre":"টাটা মেডিক্যাল সেন্টার","Techno India":"টেকনো ইন্ডিয়া",
 "Ultadanga":"উল্টোডাঙ্গা","VIP Road":"ভিআইপি রোড","Vidyasagar Setu":"বিদ্যাসাগর সেতু",
 "Wipro More":"উইপ্রো মোড়","Wipro Xing":"উইপ্রো ক্রসিং","Kasba Depot gate":"কসবা ডিপো গেট","Dakgarh":"ডাকগড়",
}

# ------------------------------------------------- canonical route stops ----
# key: route number. value: (stops_en [...], legs or None for equal)
# Direction = canonical as listed (first stop -> last stop).
ROUTE_STOPS = {
 "AC-39": (["Howrah Stn","Howrah Bridge East","BBD Bag","Esplanade East","Lalbazar","Colutola Xing","M.G. Rd","Girish Park","Manicktala","Kankurgachi","Ultadanga","Laketown","Baguihati","Kaikhali","Airport Gate-1"],
           [10,5,4,3,3,4,6,5,5,5,6,7,5,5]),
 "S-12E": (["Howrah Stn","Howrah Bridge East","BBD Bag","Esplanade","Moulali","Sealdah","Beliaghata Xing","KBKC","Panchayat Bhawan","Techno India","Technopolis","New Town","Narkelbagan","Ecospace"], None),
 "S-22": (["Karunamayee","Wipro Xing","College More","SDF","Nicco Park","Sukanta Nagar","Chingrighata","Science City","Ruby","Kasba P.S","Gariahat","R.B. Ave","Chetla","New Alipore","Taratala Xing","Behala P.S","Behala Chowrasta","Nutan Para","Bakultala","Raidighi","Sakuntala Park"], None),
 "S-23A": (["Bally Khal","Dakshineswar","Dunlop","Durganagar","Airport Gate-1","Chinar Park","City Centre 1","Nabadiganta","Eco Park","Narkelbagan","New Town Central Stand","College More","SLD Gate"], None),
 "S-46": (["Karunamayee","Central Park","Paribesh Bhaban","Science City","Ruby","Bijan Setu","Gariahat","R.B. Ave Xing","Chetla","Sahapur","Taratala Xing","Taratala Depot","Paharpur","Santoshpur Stn","Akra Rabindranagar"], None),
 "S-47": (["Eden City Gate","Nungimore","Batamore","Dakghar","Jalkol","Mollar Gate","Rampur","Jingirabazar","Taratala Depot","Taratala Xing","Momonpore","Khidirpore","Casurina Ave","Esplanade","BBD Bag","Howrah Bridge East","Howrah Stn"], None),
 "S-5C": (["Howrah Stn","Howrah Bridge East","BBD Bag","Esplanade","Park Street","Elgin Rd","Hazra","R.B. Avenue","Deshapriya Park","Gariahat","Dhakuria","Jadavpur","Sukanta Setu","Ajoynagar","Peerless Hospital","Panchasayar","Garia Stn","Nayabad Bus Stand"], None),
 "S-30": (["Ecospace","Tata Medical Centre","Hidco Bhavan","New Town Bus Stand","Technopolis","College More","Nicco Park","Chingrighata","Kadapara","Ultadanga"], None),
 "AC-45": (["Sakuntala Park","Bakultala","Behala Chowrasta","Behala P.S","Taratala Xing","Mominpur","Alipore Zoo","Rabindra Sadan","Esplanade","Moulali","Sealdah","Rajabazar","Manicktala","Khanna","Shyambazar","Kolkata Stn"], None),
 "AC-41": (["Ecospace","Narkelbagan","New Town","Technopolis","College More","Swasthya Bhawan","Nicco Park","Chingrighata","Science City","Topsia","Beckbagan","Rabindra Sadan","PTS","Mandirtala","Betore More","Santragachi"], None),
 "S-44": (["Ecospace","College More","Wipro More","Chingrighata","Science City","Park Circus","Beckbagan","Minto Park","Rabindra Sadan","PTS More","Vidyasagar Setu","Mandirtala","Nabanna"], None),
 "AC-37B": (["Airport Gate-1","Chinar Park","City Centre 1","Nabadiganta More","Eco Park","Narkelbagan","Home Town","New Town","Technopolis","SDF","Swasthya Bhawan","Nicco Park","Chingrighata","Science City","VIP Bazar","Ruby","Kalikapur","Peerless","Patuli","Garia Depot"], None),
 "S-37A": (["Airport Gate-1","Chinar Park","City Centre 1","Nabadiganta More","Eco Park","Narkelbagan","Home Town","New Town","Technopolis","SDF","Swasthya Bhawan","Nicco Park","Chingrighata","Science City","VIP Bazar","Ruby","Kalikapur","Peerless","Patuli","Garia-6"], None),
 "AC-3": (["Kolkata Stn","Khanna","Manicktala","Sealdah","Beliaghata Xing","KBKC","Panchayat Bhawan","Chingrighata","Nicco Park","College More","Nabadiganta","Unitech"], None),
 "S-53": (["Kolkata Stn","Khanna","Manicktala","Sealdah","Beliaghata Xing","KBKC","Panchayat Bhawan","Chingrighata","Nicco Park","College More","Nabadiganta","Unitech"], None),
 "AC-15": (["Bantala IT Park","Chingrighata","Science City","Park Circus","Minto Park","Esplanade","BBD Bag","Howrah Bridge East","Howrah Stn"], None),
 "AC-42": (["Behala 3A Stand","Behala Chowrasta","Behala P.S","Taratala Xing","Mominpur","Khidirpore","Howrah Stn","Howrah Maidan","Santragachi"], None),
 "AC-48": (["Bantala IT Park","Chingrighata","Science City","Ruby","Gariahat","Rashbehari Xing","Tollygunge Tram Depot","Kudghat"], None),
 "AC-50": (["Belur","Bally Khal","Dakshineswar","Durganagar","Airport Gate-1","Kaikhali","VIP Road","Chingrighata","Science City","E.M. Bypass","Patuli","Garia-6"], None),
 "AC-9A": (["Dakshineswar","Dunlop","Baranagar","Cossipore","Shyambazar","Girish Park","Esplanade","Rabindra Sadan","Alipore Zoo","Golf Green"], None),
 "S-12C": (["Dum Dum 7 Tanks","Nager Bazar","Ultadanga","Kadapara","Chingrighata","Science City","Ruby","Peerless Hospital","Panchasayar","Garia Stn","Nayabad Bus Stand"], None),
 "S-13": (["Amtala","Pailan","Joka","Thakurpukur","Behala Chowrasta","Taratala Xing","New Alipore","Rabindra Sadan","Park Circus","Science City","Kadapara","Ultadanga"], None),
 "S-14C": (["Dunlop","Durganagar","Airport Gate-1","Chinar Park","City Centre 1","Nabadiganta","College More","Karunamayee"], None),
 "S-15G": (["Baruipur","Malancha Bazar","Harinavi","Mission Gate","Kamalgazi More","Dhalai Bridge","Patuli","Ruby","Science City","Chingrighata","Nicco Park","College More","VIP Road","Kaikhali","Airport Gate-1","Durganagar","Belghoria Expressway","Dakshineswar"], None),
 "S-2A": (["Ballygunge Stn","Gariahat","Deshapriya Park","Rashbehari Ave","Hazra","Kalighat","Bondel Gate","Moulali","Sealdah","Manicktala","Khanna","Shyambazar","Paikpara"], None),
 "S-2B": (["Bagbazar","Shyambazar","Khanna","Manicktala","Sealdah","Moulali","Park Circus","Beckbagan","Kasba P.S","Kasba Depot gate"], None),
 "S-22A": (["Dakgarh","Raidighi","Bakultala","Behala Chowrasta","Behala P.S","Taratala Xing","New Alipore","Chetla","R.B. Ave","Gariahat","Ruby","Science City","Chingrighata","Nicco Park","College More","Karunamayee"], None),
 "S-4B": (["Haridevpur","Rashbehari","Gariahat","Park Circus","Science City","Chingrighata","Nicco Park","College More","New Town"], None),
 "S-51": (["Eden City Gate","Mollar Gate","Taratala Xing","New Alipore","Chetla","R.B. Avenue","Gariahat","Dhakuria","Jadavpur","Garia Depot"], None),
}

# -------------------------------------- official terminal timetables ----
# Source: published CSTC/CTC timetable supplied for the Kolkata city-bus
# rollout. First/last terminal times are official; intermediate stop times
# are calculated only when STOPS/LEGS data exists.
OFFICIAL_TRIPS = {
    "AC-10": {
        "howrah-to-madhyamgram": [
            ["07:00","08:18"],["07:30","08:48"],["08:00","09:18"],["08:48","10:06"],
            ["09:18","10:36"],["09:48","11:06"],["10:36","11:54"],["10:48","12:06"],
            ["11:06","12:24"],["11:36","12:54"],["12:24","13:42"],["12:54","14:12"],
            ["13:24","14:42"],["14:00","15:18"],["14:24","15:42"],["14:30","15:48"],
            ["15:00","16:18"],["15:48","17:06"],["16:18","17:36"],["16:48","18:06"],
            ["17:18","18:36"],["17:36","18:54"],["18:06","19:24"],["18:36","19:54"],
            ["19:24","20:42"],["19:54","21:12"],["20:24","21:42"],["20:54","22:12"]
        ],
        "madhyamgram-to-howrah": [
            ["07:00","08:18"],["07:30","08:48"],["08:00","09:18"],["08:48","10:06"],
            ["09:00","10:18"],["09:18","10:36"],["09:48","11:06"],["10:36","11:54"],
            ["11:06","12:24"],["11:36","12:54"],["12:24","13:42"],["12:36","13:54"],
            ["12:54","14:12"],["13:24","14:42"],["14:00","15:18"],["14:30","15:48"],
            ["15:00","16:18"],["15:30","16:48"],["15:48","17:06"],["16:18","17:36"],
            ["16:48","18:06"],["17:36","18:54"],["18:06","19:24"],["18:36","19:54"],
            ["19:06","20:24"],["19:24","20:42"],["19:54","21:12"],["20:24","21:42"]
        ]
    }
}

# --------------------------------------------- hub ROUTES db (for related) --
def load_hub_routes():
    h = (ROOT / "kolkata-city-bus-timetable.html").read_text(encoding="utf-8")
    m = re.search(r"var ROUTES=(\[.*?\]);", h, re.S)
    routes = json.loads(m.group(1))
    links = {}
    lm = re.search(r"var LINKS=(\{.*?\});", h, re.S)
    links = json.loads(lm.group(1))
    return routes, links

def norm_tokens(s):
    return set(t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if t)

def fuzzy(a, b):
    ta, tb = norm_tokens(a), norm_tokens(b)
    if not ta or not tb: return False
    return bool(ta & tb)

def find_pages(routes_links):
    """route_no -> list of (path, from, to) parsed from page titles."""
    out = {}
    for f in sorted(glob.glob(str(ROOT / "bus-time-table" / "*.html"))):
        h = Path(f).read_text(encoding="utf-8")
        tm = re.search(r"<title>(.+?) Bus Time Table \(([A-Za-z0-9\-/ .]+)\) \| BusJatri</title>", h)
        if not tm: continue
        frm, rno = tm.group(1), tm.group(2).strip()
        if rno not in routes_links: continue
        out.setdefault(rno, []).append((f, frm))
    return out

def bn_for(stop, existing_map):
    if stop in existing_map: return existing_map[stop]
    if stop in BN: return BN[stop]
    raise SystemExit(f"NO BENGALI for stop: {stop!r}")

def stops_payload(en_list, existing_map):
    return [[s, bn_for(s, existing_map)] for s in en_list]

def main():
    # existing translations from pages that already have stops
    existing_map = {}
    for f in glob.glob(str(ROOT / "bus-time-table" / "*.html")):
        h = Path(f).read_text(encoding="utf-8")
        m = re.search(r"var STOPS=(\[.*?\]);", h, re.S)
        if m and m.group(1).strip() != "[]":
            try:
                for en, bn in json.loads(m.group(1)): existing_map.setdefault(en, bn)
            except Exception: pass

    routes, links = load_hub_routes()
    by_no = {r["n"]: r for r in routes}
    pages = find_pages(links)

    changed = {}
    def edit(path, old, new, label):
        h = changed.get(path)
        if h is None:
            h = Path(path).read_text(encoding="utf-8"); changed[path] = h
        if old not in h:
            print(f"  !! {label}: anchor not found in {Path(path).name}"); return False
        h = h.replace(old, new, 1)
        changed[path] = h
        return True

    # ---- 1. inject STOPS/LEGS on the 58 empty pages
    print("== 1. STOPS/LEGS injection ==")
    done = fail = 0
    for rno, (stops_en, legs) in ROUTE_STOPS.items():
        plist = pages.get(rno, [])
        if len(plist) != 2:
            print(f"  !! {rno}: expected 2 pages, found {len(plist)}"); fail += 1; continue
        payload = stops_payload(stops_en, existing_map)
        legs = legs or [1] * (len(stops_en) - 1)
        c0, c1 = stops_en[0], stops_en[-1]
        for path, frm in plist:
            h = changed.get(path) or Path(path).read_text(encoding="utf-8")
            m = re.search(r"<title>(.+?) Bus Time Table", h)
            a_to_b = m.group(1)
            if " to " not in a_to_b:
                print(f"  !! {rno}: bad title {a_to_b!r}"); fail += 1; continue
            A, B = [x.strip() for x in a_to_b.split(" to ", 1)]
            asis = (fuzzy(A, c0) and fuzzy(B, c1)) or A.strip() == c0
            revd = (fuzzy(A, c1) and fuzzy(B, c0)) or A.strip() == c1
            if asis and revd:
                asis = True  # both ends same names; keep canonical
                revd = False
            if not (asis or revd):
                print(f"  !! {rno}: termini mismatch on {Path(path).name}: A={A!r} B={B!r} c0={c0!r} c1={c1!r}")
                fail += 1; continue
            use = payload if asis else payload[::-1]
            stops_js = json.dumps(use, ensure_ascii=False, separators=(",", ":"))
            legs_js = json.dumps(legs if asis else legs[::-1], separators=(",", ":"))
            if f"var STOPS={stops_js};" in h:
                continue  # already patched
            if "var STOPS=[];" not in h:
                print(f"  !! {rno}: no empty STOPS in {Path(path).name} (already has stops?)")
                continue
            ok1 = edit(path, "var STOPS=[];", f"var STOPS={stops_js};", f"{rno} STOPS")
            ok2 = edit(path, "var LEGS=[];", f"var LEGS={legs_js};", f"{rno} LEGS")
            if ok1 and ok2: done += 1
            else: fail += 1
    print(f"  pages patched: {done}, failures: {fail}")


    # ---- 1.5 journey panel markup on pages missing it
    print("== 1.5 journey panel markup ==")
    JOURNEY = """<div class="journey" id="journey">
          <div class="j-title" id="jTitle"></div>
          <div class="j-route" id="jRoute"></div>
          <div class="j-stops-wrap"><div class="j-stops" id="jStops"></div></div>
          <div class="j-note"><span class="label-en">First & last stop times are official. Mid-route times (\u2248) are approximate estimates. Tap the selected time again to close.</span><span class="label-bn">\u09aa\u09cd\u09b0\u09a5\u09ae \u0993 \u09b6\u09c7\u09b7 \u09b8\u09cd\u099f\u09aa\u09c7\u09b0 \u09b8\u09ae\u09df \u0985\u09ab\u09bf\u09b6\u09bf\u09df\u09be\u09b2\u0964 \u09ae\u09be\u099d\u09c7\u09b0 \u09b8\u09ae\u09df\u0997\u09c1\u09b2\u09bf (\u2248) \u0986\u09a8\u09c1\u09ae\u09be\u09a8\u09bf\u0995\u0964 \u09ac\u09a8\u09cd\u09a7 \u0995\u09b0\u09a4\u09c7 \u0986\u09ac\u09be\u09b0 \u099f\u09cd\u09af\u09be\u09aa \u0995\u09b0\u09c1\u09a8\u0964</span></div>
        </div>
        <div class="j-hint" id="jHint"><span class="label-en">\u2191 Tap a time above \u2014 stop-wise timings will appear here</span><span class="label-bn">\u2191 \u0989\u09aa\u09b0\u09c7\u09b0 \u09af\u09c7\u0995\u09cb\u09a8\u09cb \u09b8\u09ae\u09df\u09c7 \u099f\u09cd\u09af\u09be\u09aa \u0995\u09b0\u09c1\u09a8 \u2014 \u09b8\u09cd\u099f\u09aa-\u09ad\u09bf\u09a4\u09cd\u09a4\u09bf\u0995 \u09b8\u09ae\u09df \u098f\u0996\u09be\u09a8\u09c7 \u09a6\u09c7\u0996\u09be \u09af\u09be\u09ac\u09c7</span></div>"""
    import codecs
    JOURNEY = codecs.decode(JOURNEY, 'unicode_escape')
    pat = re.compile(r'(rail-fade bot"></div>\s*</div>\s*<div>)\s*(</div>\s*</div>\s*<p class="tt-note")')
    n = 0
    for path in list(changed.keys()) + [str(p) for p in (ROOT / "bus-time-table").glob("*.html")]:
        h = changed.get(path) or Path(path).read_text(encoding="utf-8")
        if "var TRIPS" not in h: continue
        if 'id="journey"' in h: continue
        h2, k = pat.subn(lambda m: m.group(1) + "\n" + JOURNEY + "\n      " + m.group(2), h, count=1)
        if k:
            changed[path] = h2; n += 1
        else:
            print(f"  !! no empty placeholder: {Path(path).name}")
    print(f"  journey panels injected: {n}")

    # ---- 2. static crawlable stop list (all pages with stop data)
    print("== 2. static stop lists ==")
    n = 0
    for f in sorted(glob.glob(str(ROOT / "bus-time-table" / "*.html"))):
        path = Path(f).name
        h = changed.get(f) or Path(f).read_text(encoding="utf-8")
        if "var TRIPS" not in h: continue
        if "city-stops-v1" in h: continue
        m = re.search(r"var STOPS=(\[.*?\]);", h, re.S)
        if not m: continue
        try: stops = json.loads(m.group(1))
        except Exception: continue
        if not stops: continue
        en = " → ".join(s[0] for s in stops)
        bn = " → ".join(s[1] for s in stops)
        block = (f'\n<!-- city-stops-v1 -->\n<p class="tt-note"><span class="label-en">'
                 f'<b>Route stops:</b> {en}</span><span class="label-bn">'
                 f'<b>রুটের স্টপ:</b> {bn}</span></p>\n')
        anchor = '<h3 class="section-title"><span class="label-en">Other Direction</span>'
        if anchor not in h:
            print(f"  !! no OD anchor: {path}"); continue
        if edit(f, anchor, block + anchor, f"stops-list {path}"): n += 1
    print(f"  static stop lists added: {n}")

    # ---- 3. related routes links (all city pages)
    print("== 3. related routes links ==")
    n = 0
    for f in sorted(glob.glob(str(ROOT / "bus-time-table" / "*.html"))):
        h = changed.get(f) or Path(f).read_text(encoding="utf-8")
        if "var TRIPS" not in h: continue
        if "city-rel-v1" in h: continue
        tm = re.search(r"Bus Time Table \(([A-Za-z0-9\-/ .]+)\) \| BusJatri", h)
        if not tm: continue
        rno = tm.group(1).strip()
        me = by_no.get(rno)
        if not me: continue
        ta = norm_tokens(me["a"]) | norm_tokens(me["b"])
        rel = [r for r in routes if r["n"] != rno and (norm_tokens(r["a"]) | norm_tokens(r["b"])) & ta]
        rel.sort(key=lambda r: -r.get("t", 0))
        rel = rel[:5]
        if not rel: continue
        def mk(r, bn_mode):
            p = links.get(r["n"], "#")
            # Route pages live inside /bus-time-table/, so related links must be page-relative.
            p = p.split("bus-time-table/", 1)[-1]
            lab = f"{r['n']} {r['a']} ⟷ {r['b']}"
            if bn_mode:
                # Use the same verified Bengali stop dictionary used by STOPS.
                aa = existing_map.get(r["a"], BN.get(r["a"], r["a"]))
                bb = existing_map.get(r["b"], BN.get(r["b"], r["b"]))
                lab = f"{r['n']} {aa} ⟷ {bb}"
            return f'<a href="{p}">{lab}</a>'
        en = " · ".join(mk(r, False) for r in rel)
        bn = " · ".join(mk(r, True) for r in rel)
        block = (f'\n<!-- city-rel-v1 -->\n<p class="tt-note" style="margin-top:10px">'
                 f'<span class="label-en"><b>Related city routes:</b> {en}</span>'
                 f'<span class="label-bn"><b>সম্পর্কিত সিটি রুট:</b> {bn}</span></p>\n')
        anchor = '<h3 class="section-title"><span class="label-en">FAQs</span>'
        if anchor not in h:
            print(f"  !! no FAQ anchor on {Path(f).name}"); continue
        if edit(f, anchor, block + anchor, f"rel {Path(f).name}"): n += 1
    print(f"  related-links blocks added: {n}")

    # ---- 4. meta description upgrade on injected pages
    print("== 4. meta desc upgrade ==")
    n = 0
    for path, h in changed.items():
        if "city-stops-v1" in h or path in [p for p in changed]:
            old = "Official timings and FAQs on BusJatri."
            new = "Official timings, stop-wise times and FAQs on BusJatri."
            if old in h:
                changed[path] = h.replace(old, new)
                n += 1
    print(f"  meta descriptions updated: {n}")

    # ---- 5. BTT index -> city hub link
    print("== 5. BTT index hub link ==")
    idx = ROOT / "bus-time-table" / "index.html"
    h = changed.get(str(idx)) or idx.read_text(encoding="utf-8")
    if "city-hub-v1" not in h:
        anchor = '</div> <div class="rt-search"' if '</div> <div class="rt-search"' in h else None
        if anchor is None:
            m = re.search(r'(<div class="chips">.*?</div>)', h, re.S)
            anchor = m.group(1) if m else None
        if anchor:
            block = (anchor + """
<!-- city-hub-v1 -->
<div style="margin:14px 0 4px;display:flex;flex-wrap:wrap;gap:8px">
<a href="../kolkata-city-bus-timetable.html" style="display:inline-flex;align-items:center;gap:6px;background:#f6efe2;border:1px solid #d8c9a8;border-radius:999px;padding:9px 16px;font-size:13px;font-weight:700;color:#211c16;text-decoration:none">
<span class="label-en">🚌 Kolkata City Bus (WBTC) — 73 routes with stop-wise times</span><span class="label-bn">🚌 কলকাতা সিটি বাস (ডাব্লুবিটিসি) — ৭৩ রুট, স্টপ-ভিত্তিক সময় সহ</span></a></div>""")
            changed[str(idx)] = h.replace(anchor, block, 1)
            print("  added hub link card to BTT index")
        else:
            print("  !! BTT index anchor not found")
    else:
        print("  already present")

    # ---- 6. stand pages -> city routes
    print("== 6. stand page links ==")
    STANDS = {
        "buses-from-howrah-station.html": ["AC-39","S-12","S-10A","AC-6","AC-4","11A","15","AC-12D"],
        "buses-from-esplanade.html": ["S-11","AC-15","S-5C","AC-45","S-44"],
        "buses-from-garia-bus-stand.html": ["AC-37A","AC-5","AC-6","S-7","S-21","AC-37B"],
        "buses-from-karunamoyee.html": ["AC-9","S-9","S-14","AC-14","S-22","S-14C"],
        "buses-from-howrah-maidan.html": ["AC-45","S-45","AC-42","AC-20"],
        "buses-from-ultadanga.html": ["15","S-30","S-13"],
        "buses-from-jadavpur-8b.html": ["AC-1","S-9","S-31","AC-9"],
        "buses-from-santragachi.html": ["AC-20","AC-41","AC-42"],
    }
    for name, rlist in STANDS.items():
        p = ROOT / "bus-time-table" / name
        if not p.exists():
            print(f"  -- skip (no page): {name}"); continue
        h = changed.get(str(p)) or p.read_text(encoding="utf-8")
        if "city-stand-v1" in h:
            print(f"  already: {name}"); continue
        items = []
        for rno in rlist:
            r = by_no.get(rno)
            if not r: continue
            lp = links.get(rno)
            if not lp: continue
            lp = "../" + lp if not lp.startswith("../") else lp
            items.append(f'<a href="{lp}">{rno} ({r["a"]} ⟷ {r["b"]})</a>')
        if not items: continue
        block = f"""
<!-- city-stand-v1 -->
<div style="margin:22px 0;padding:14px 16px;background:#f6efe2;border:1px solid #e2d5b4;border-radius:12px">
<h3 style="margin:0 0 8px;font-size:15px"><span class="label-en">Kolkata city bus routes — with stop-wise timings</span><span class="label-bn">কলকাতা সিটি বাস রুট — স্টপ-ভিত্তিক সময় সহ</span></h3>
<p style="margin:0;font-size:13.5px;line-height:1.9">{' · '.join(items)}<br>
<a href="../kolkata-city-bus-timetable.html" style="font-weight:700"><span class="label-en">All 73 city routes →</span><span class="label-bn">সব ৭৩টি সিটি রুট →</span></a></p></div>
"""
        fi = h.find("<footer")
        if fi < 0:
            print(f"  !! no footer in {name}"); continue
        changed[str(p)] = h[:fi] + block + h[fi:]
        print(f"  patched stand page: {name}")

    # ---- 7. repair existing city-page internal links + bilingual wording
    print("== 7. repair existing city-page links/wording ==")
    n = 0
    for f in sorted(glob.glob(str(ROOT / "bus-time-table" / "*.html"))):
        h = changed.get(f) or Path(f).read_text(encoding="utf-8")
        if "var TRIPS" not in h: continue
        original = h
        # These pages live inside /bus-time-table/, so related city links must be page-relative.
        h = h.replace('href="bus-time-table/', 'href="')
        # Route pages should return to the Kolkata City Bus hub, not the generic timetable index.
        h = h.replace('<a href="./">All Bus Timetables</a>', '<a href="../kolkata-city-bus-timetable.html"><span class="label-en">Kolkata City Bus Timetable</span><span class="label-bn">কলকাতা সিটি বাস টাইম টেবিল</span></a>')
        # Keep the language toggle clean: English stays English, Bengali stays Bengali.
        h = h.replace('<span class="label-bn">Kolkata City Bus Timetable</span>', '<span class="label-bn">কলকাতা সিটি বাস টাইম টেবিল</span>')
        if h != original:
            changed[f] = h
            n += 1
    print(f"  existing city pages repaired: {n}")

    # ---- 7.5 bilingual journey/stop labels (all Kolkata city route pages)
    print("== 7.5 bilingual journey/stop labels ==")
    n = 0
    I18N = '''<script id="city-i18n-v1">
(function(){
  function syncJourneyLang(){
    if(typeof STOPS === 'undefined' || !Array.isArray(STOPS) || !STOPS.length) return;
    var bn=document.body.classList.contains('lang-bn');
    var first=STOPS[0], last=STOPS[STOPS.length-1];
    var rows=document.querySelectorAll('#jStops .j-stop');
    rows.forEach(function(row,i){
      if(STOPS[i]){
        var name=row.querySelector('.s-name');
        if(name) name.textContent=bn ? STOPS[i][1] : STOPS[i][0];
      }
    });
    var route=(bn ? first[1] : first[0])+' → '+(bn ? last[1] : last[0]);
    var jr=document.getElementById('jRoute');
    if(jr) jr.textContent=route;
    var h1=document.querySelector('.seo-hero h1');
    if(h1) h1.innerHTML='<span class="label-en">'+first[0]+' <span class="arr">→</span> '+last[0]+'</span><span class="label-bn">'+first[1]+' <span class="arr">→</span> '+last[1]+'</span>';
    var cr=document.querySelector('.crumbs');
    if(cr) cr.innerHTML='<a href="../"><span class="label-en">Home</span><span class="label-bn">হোম</span></a> › <a href="./"><span class="label-en">Bus Timetable</span><span class="label-bn">বাস টাইম টেবিল</span></a> › <span>'+route+'</span>';
  }
  window.bjSyncJourneyLang=syncJourneyLang;
  var obs=new MutationObserver(function(){syncJourneyLang()});
  obs.observe(document.body,{attributes:true,attributeFilter:['class']});
  document.addEventListener('click',function(e){
    if(e.target && (e.target.id==='langBn' || e.target.id==='langEn')) setTimeout(syncJourneyLang,0);
  });
  setTimeout(syncJourneyLang,50);
})();
</script>
'''
    for f in sorted(glob.glob(str(ROOT / "bus-time-table" / "*.html"))):
        h = changed.get(f) or Path(f).read_text(encoding="utf-8")
        if "var TRIPS" not in h or 'id="city-i18n-v1"' in h: continue
        if '</body>' not in h: continue
        changed[f] = h.replace('</body>', I18N + '</body>', 1)
        n += 1
    print(f"  bilingual journey runtime added: {n}")

    # ---- 8. official terminal arrival times (no estimated terminal times)
    print("== 8. official terminal arrival times ==")
    n = 0
    for rno, directions in OFFICIAL_TRIPS.items():
        for path in sorted(glob.glob(str(ROOT / "bus-time-table" / "*.html"))):
            h = changed.get(path) or Path(path).read_text(encoding="utf-8")
            if f"({rno})" not in h:
                continue
            name = Path(path).name.lower()
            direction = None
            if rno == "AC-10":
                direction = "howrah-to-madhyamgram" if "howrah-to-madhyamgram" in name else (
                    "madhyamgram-to-howrah" if "madhyamgram-to-howrah" in name else None
                )
            trips = directions.get(direction) if direction else None
            if not trips:
                continue

            new_trips = "var TRIPS=" + json.dumps(trips, separators=(",", ":")) + ";"
            h2, k = re.subn(r"var TRIPS=\[.*?\];", new_trips, h, count=1, flags=re.S)
            if not k:
                print(f"  !! no TRIPS anchor: {Path(path).name}")
                continue

            h2 = h2.replace('class="tt-card deponly"', 'class="tt-card"', 1)
            h2 = h2.replace("official departure times", "official departure & arrival times", 1)
            h2 = h2.replace("অফিসিয়াল সময়সূচি", "অফিসিয়াল ছাড়ার ও পৌঁছানোর সময়সূচি", 1)
            h2 = h2.replace(
                "departure times only. Times auto-scroll",
                "official departure & terminal arrival times. Times auto-scroll", 1
            )
            h2 = h2.replace(
                "শুধু ছাড়ার সময়। আপনার আগামী বাসে স্ক্রল",
                "অফিসিয়াল ছাড়ার ও টার্মিনাল পৌঁছানোর সময়। আপনার আগামী বাসে স্ক্রল", 1
            )

            h2 = re.sub(
                r'<script id="bj-derived-arrival">.*?</script>\s*<p class="tt-note">.*?</p>',
                "",
                h2, count=1, flags=re.S
            )

            renderer = r'''<script id="bj-official-arrival-v1">
(function(){
  var rail=document.getElementById('rail');
  if(!rail || typeof TRIPS==='undefined') return;
  function m(t){return +t.slice(0,2)*60 + +t.slice(3)}
  function t12(mm){mm=(mm+1440)%1440;var h=Math.floor(mm/60),mi=mm%60,ap=h<12?'AM':'PM',h12=h%12||12;return h12+':'+(mi<10?'0':'')+mi+' '+ap}
  function dur(a,b){var d=m(b)-m(a);if(d<0)d+=1440;var h=Math.floor(d/60),mi=d%60;return h?h+'h '+(mi?mi+'m':''):mi+'m'}
  var html='';
  TRIPS.forEach(function(t,i){
    html+='<div class="tr" data-i="'+i+'"><div class="dep">'+t12(m(t[0]))+'</div><div class="mid"><span class="ln"></span>'+dur(t[0],t[1])+'<span class="ln"></span></div><div class="arr">'+t12(m(t[1]))+'</div></div>';
  });
  rail.innerHTML=html;
  var rows=rail.querySelectorAll('.tr'),now=new Date(),nm=now.getHours()*60+now.getMinutes(),ni=-1;
  for(var i=0;i<rows.length;i++){if(m(TRIPS[i][0])>=nm){rows[i].classList.add('next');ni=i;break;}}
  if(ni<0&&rows.length){rows[0].classList.add('next');ni=0;}
  if(rows[ni]) rail.scrollTop=Math.max(0,rows[ni].offsetTop-rail.clientHeight/2+rows[ni].offsetHeight/2);
  var pill=document.getElementById('nextPill');
  if(pill&&rows[ni]){pill.innerHTML='<span class="label-en">Next '+t12(m(TRIPS[ni][0]))+'</span><span class="label-bn">আগামী '+t12(m(TRIPS[ni][0]))+'</span>';pill.style.display='inline-flex';}
})();
</script>
'''
            h2 = h2.replace("</body>", renderer + "</body>", 1)
            if h2 != h:
                changed[path] = h2
                n += 1
    print(f"  official terminal timetable pages patched: {n}")

    # ---- write out
    print(f"\n== files changed: {len(changed)} ({'WRITE' if WRITE else 'DRY-RUN'}) ==")
    if DRY:
        for p in sorted(changed): print("  ~", Path(p).name)
        return
    for p, h in changed.items():
        Path(p).write_text(h, encoding="utf-8")
    print("done.")

if __name__ == "__main__":
    main()
