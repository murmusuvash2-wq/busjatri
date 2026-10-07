#!/usr/bin/env python3
"""Add Kolkata city (CSTC) route stoppages researched from the official WBTC
source (wbtconline.in/wbtc-city-bus-routes).

The CSTC timetable data (data/cstc_city_bus_timetable.json) has departure/arrival
times but no stoppages, so the 73 CSTC route pages render without a stop list.
This script adds a `stops` array to each CSTC route that matches a WBTC route,
parsed from the official stoppage chains below. Idempotent.

Usage: python3 scripts/add_cstc_stops.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSTC = ROOT / "data" / "cstc_city_bus_timetable.json"

# Official WBTC city-route stoppage chains (wbtconline.in/wbtc-city-bus-routes).
# key = WBTC route no., value = raw stoppage chain.
WBTC = {
    "3": "Khidderpur-Mominpur-Hazra-Elgin Road-Park street-Esplanade-Subod Mallick Squre-Moulali",
    "15": "Ultadanga, Khanna, Hatibagan, Grey St, Nimtala Ghat St., B.K.Paul Ave., Howrah Bridge East, Howrah Stn",
    "33": "Paikpara-Shyambazar-Khanna-Manicktala-Sealdha-Moulali-Padmapukur-Darga Rd.-Bondel Gate-Hazra-Kalighat-Alipur Rd.-Chetla",
    "7A": "Sarsuna-Bakultala-Chowrasta-Manton Xing-Behala Tram Depot-Taratala Xing-Mominpor-Khidirpor-Casurina Ave.-Esplanade-B.B.D.Bag-Howrah Stn",
    "11A": "Dum Dum Stn.-Chria-Shyambazar-Manicktala-Bedon Squre-Howrah Bridge East/Barabazar-Howrah Stn",
    "14A": "Bichalighat-HMG College/Metiabruj-Halder Para-Abestors More-Ramnagar More-Dockyard-Khiderpore-Fancy Market-Hastings-J.K.Island-Mayo Rd.-Esplanade-S.K.Mallick Rd.-Moulali-Sealdah-Cannel Bridge-Rashmoni Bazar-Jora Mandir-Beliaghata Main Road-Central Park-Karunamoyee-Unnayan Bhavan",
    "5-N": "Garia-Ganguli Bagan-Baghajatin-Jadavpur-dhakuria-Golpark-D.Park-R.B.Ave.-Hazra-Elgin-Exide-P.T.S-Nabanna",
    "6-N": "Garia-Naktala-Regentpark-Ranikhuti-Tolligunge Metro-Tollygunge Phari-R.B.Ave.-Hazra-Elgin-Exide-PTS-Nabanna",
    "12N": "Thakurpukur 3A-D.H Road-Taratala Xing-Moninpor-Khidderpore-Hestings-Vidhya Sagar Satu-Nabanna",
    "AC-1": "Jadavpur P.S.-Prince A.Saha Rd.-Tollygunge Phari-Hazra-Elgin-Espl.",
    "AC-2": "Hridaypur-Madhyamgram Chowrasta Xing-Doltala-New Barrackpur B.T. College-Michael Nagar-Bankra More-Birati More-Airport Gate No. 1-Kaikhali/Haldiram-Teghoria-Kestopur/Baguihati-Bangur/Dum Dum Park-Lake Town Xing-HUDCO/Ultadanga-Kankurgachi-Manicktala-Girish Park/C.R. Avn. Xing-M.G.Road Xing-Satyanarayan Park-Howrah Bridge (East)",
    "AC-4": "Taratala Xing-Mominpur-Khiddirpur-Hestings-PTS-Rabindra Sadan-Park Street-Esplanade-BBD Bag-Howrah Bridge South",
    "AC-4A": "Parnasree-T.Depot-Marine College-T.T.Xing-New Alipore-Mahabirtala-I-P A Sha Rd-Lake Gardens-Jadavpur P.S.-Sapuipara-Kalikapur-Ruby-S.City-Chingrighata-Sukanta Nagar-Nicco Park-Swastha Bhavan-College More-Technopolis-Newtown-Hometown-Narkelbagan-Unitech-Sapoorji",
    "AC-4B": "Thakurpukur-Cancer Hospital-Kabardanga-Haridevpur-Karunamoyee-Tollygunge Metro-Rashbehari Xing.-Gariahat-Ruby-Chingrihata-SDF-College More-Technopolis",
    "AC-5": "Garia-Raipur Club-Baghajatin-Jadavpur-Golpark-Gariahat-R.B.Ave.-Hazra-Chakraberia-Elgin-Birla Taramondal-Park St.-Espl.-BBD Bag-Howrah Bridge",
    "AC-6": "Howrah Stn.-Howrah Bridge East-B.B.D. Bag-Espl.-Park St-Elgin-Hazra-Rashbehari Ave.-Tollygunj Phari-T.T.Depot-Rani Kuthi-Regent Park-Naktala-Garia",
    "AC-9": "Ajoynagar-Ruby-Chingrihata-Beliaghata Con.-Central Park",
    "AC-9B": "Sukanta Setu-Ajoynagar-E M Byepass-Sc. City-Chingrihata-SDF-College More-New Town-Narkel Bagan",
    "AC-12": "Narkel Bagan-Newtown-SDF-Chingrihata-SC City-Topsia-Exide-Esplanade-BBD Bag",
    "AC-12D": "Thakurpukur-Behala-Mominpur-Zoo-PTS-Rabindra Sadan-Esplanade-Mission Row Xing-BBD Bag",
    "AC-14": "Shibanipit-Baruipur/Padmapukur-Malancha Bazar-Harinavi-Mission Gate-Kamalgazi More-Dhalai Bridge-Patuli-Peerless Hospital-Ajay Nagar-Ruby-Sc. City-Metropolitan-KBKC More-Central Park",
    "AC-20": "PTS-Esplanade-CR Avenue-Shyambazar-BT Road-Dunlop-Sodpur-Titagarh",
    "AC-23A": "College More-New Town-Unitech-Eco Space-Aliah University-Daber More-ECO Park-City Centre II-Haldiram-Airport Gate No. 1-Belghoria Exp. Way-Dakshineswar-Ballyhalt",
    "AC-24": "Ruby-Gariahat-Hazra-Exide-Park Street-Espl.",
    "AC-24A": "Dhalai Bridge-Patuli-Peerless Hospital-Ajay Nagar-Kalikapur-Ruby Hospital-Gariahat-Rashbehari Xing-Hazra Park-Rabindrasadan-Park Street-Esplanade-BBD Bag-Howrah Bridge East",
    "AC-30": "HUDCO/Ultadanga-Kankurgachi-Manicktala-Girish Park/C.R. Avn. Xing./M.G.Road Xing-Barrabazar",
    "AC-30S": "Kadapara/Beliaghata Xing.-Chingrihata-SDF-College More-New Town Bus Terminus-Narkel Bagan-Unitech",
    "AC-31": "James long Sarani-Ramkrishna Ashram-Motilal Gupta Road-Siriti More-Karunamoyee-Lake Gardens",
}


def split_stops(chain):
    out = []
    for p in re.split(r"\s*[-\u2013\u2014]\s*|\s*,\s*", chain):
        p = re.sub(r"\s+", " ", p).strip(" .,-;")
        if len(p) > 1:
            out.append(p)
    return out


def norm_route(r):
    return re.sub(r"[^A-Z0-9]", "", str(r).upper())


def main():
    data = json.loads(CSTC.read_text(encoding="utf-8"))
    routes = data.get("routes", data)
    idx = {norm_route(k): v for k, v in WBTC.items()}
    n = 0
    for code, obj in routes.items():
        hit = idx.get(norm_route(code))
        if not hit:
            continue
        stops = split_stops(hit)
        obj["stops"] = stops
        obj["stops_source"] = "wbtconline.in/wbtc-city-bus-routes (official WBTC)"
        for di, d in enumerate(obj.get("directions") or []):
            d["stoppages"] = list(reversed(stops)) if di else list(stops)
        n += 1
    CSTC.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"CSTC routes given stoppages: {n} / {len(routes)}")


if __name__ == "__main__":
    main()
