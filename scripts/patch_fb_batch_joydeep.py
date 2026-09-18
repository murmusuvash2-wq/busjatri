#!/usr/bin/env python3
"""FB community batch update (Joydeep + Bus Detailer reports, 2026-09-18).

NEW buses (appended to data/community_buses.json):
  1. MAA KAJAL TRAVELS  Digha <-> Medinipur (5:20 AM / 11:40 AM)
  2. SHINJINI PARIBAHAN AC  Kolkata (Dharmatala) -> Digha Border (6:30 AM /
     return New Digha 11:20 PM)
  3. DROUPADI TRAVELS (Baba Lokenath)  Durgachak -> Medinipur (9:45 AM /
     4:40 PM)
  4. KRISHNA  Supa <-> Baruipur (4:00 AM / 12:00 PM)
  5. SBSTC Kalna-Bardhaman-Digha (WB 39B 9153, 5:30 AM / 10:15 AM)

UPDATES (same buses already in data, enriched):
  6. GOBINDA  (wbbustime-gobinda-0) Medinipur <-> Mandarmani AC, 8:55 AM
  7. JOY MAA DURGA (wbbustime-jai-maa-durga-0) Bandwan <-> Siliguri 3:05 PM
  8. MAJOR    (bussathi-major-467)  Durgapur <-> Bokaro, 5:50 AM (FB)
  9. AADRIKA  (bussathi-aadrika-5)  Durgachak <-> Jhargram 6:55 AM
 10. DEBJIT   (bussathi-debjit-0)   Keshargarh <-> Santaldih 6:00 AM

Idempotent: re-running makes no changes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv


def st(*rows):
    return [{"name": n, "up": u, "down": d} for n, u, d in rows]


def sp(*rows):
    return [{"no": i + 1, "name": n, "up_time": u, "down_time": d} for i, (n, u, d) in enumerate(rows)]


NEW_BUSES = [
    {
        "operator": "Maa Kajal Travels",
        "bus_name": "Maa Kajal Travels Digha-Medinipur",
        "bus_type": "Private",
        "reg_no": "",
        "origin": "Digha",
        "destination": "Medinipur",
        "departure_time": "5:20 AM",
        "arrival_time": "",
        "route": "Digha - Medinipur",
        "source": "facebook (community report)",
        "detail_url": "",
        "contact_number": "",
        "stops": st(
            ("Digha Border", "5:20 AM", ""),
            ("Old Digha", "5:50 AM", ""),
            ("Ramnagar", "6:15 AM", ""),
            ("Paniparul", "", ""),
            ("Egra", "7:20 AM", "2:20 PM"),
            ("Belda", "8:05 AM", "1:40 PM"),
            ("Kharagpur", "", "12:40 PM"),
            ("Medinipur", "", "11:40 AM"),
        ),
    },
    {
        "operator": "Shinjini Paribahan",
        "bus_name": "Shinjini Paribahan Kolkata-Digha Border (AC Coach)",
        "bus_type": "Private - AC Seater/Sleeper",
        "reg_no": "",
        "origin": "Kolkata (Dharmatala)",
        "destination": "Digha Border (Udaypur)",
        "departure_time": "6:30 AM",
        "arrival_time": "11:15 AM",
        "route": "Kolkata (Dharmatala) - Digha Border (Udaypur)",
        "source": "facebook (community report)",
        "detail_url": "",
        "contact_number": "9932158181, 8967949294",
        "stops": st(
            ("Kolkata (Dharmatala)", "6:30 AM", ""),
            ("Park Street", "", ""),
            ("PTI", "", ""),
            ("Hastings", "", ""),
            ("Second Hooghly Bridge", "", ""),
            ("Nabanna", "", ""),
            ("Carry Road", "", ""),
            ("Belepole", "", ""),
            ("Santragachi", "", ""),
            ("Ankurhati", "", ""),
            ("Alampur", "", ""),
            ("Dhulagarh", "7:30 AM", ""),
            ("Ranihati", "", ""),
            ("Panchla", "", ""),
            ("Uluberia (Nimidighi)", "", ""),
            ("Bagnan", "", ""),
            ("Kolaghat", "", ""),
            ("Mecheda", "8:30 AM", "2:00 AM"),
            ("Radhamani", "", ""),
            ("Nimtouri", "", ""),
            ("Nandakumar (Highroad)", "9:00 AM", ""),
            ("Norghat", "", ""),
            ("Chandipur", "", ""),
            ("Bajkul", "", ""),
            ("Heria", "9:35 AM", "12:55 AM"),
            ("Kalingar", "", ""),
            ("Nachinda", "", ""),
            ("Marishda", "", ""),
            ("Kanthi Rupsi Bypass", "", ""),
            ("Kanthi Central Bus Stand", "10:05 AM", "12:25 AM"),
            ("Ghatua", "", ""),
            ("Pichabani", "", ""),
            ("Chaulkhola (Mandarmani)", "", ""),
            ("Balisai (Tajpur)", "", ""),
            ("Chhodomile (Shankarpur)", "", ""),
            ("Thikra More", "", ""),
            ("Alankarpur", "", ""),
            ("Old Digha", "", ""),
            ("New Digha", "", "11:20 PM"),
            ("Digha Border (Udaypur)", "11:15 AM", ""),
        ),
    },
    {
        "operator": "Droupadi Travels",
        "bus_name": "Droupadi Travels (Baba Lokenath) Durgachak-Medinipur",
        "bus_type": "Private",
        "reg_no": "WB 31 N 0044",
        "origin": "Durgachak",
        "destination": "Medinipur",
        "departure_time": "9:45 AM",
        "arrival_time": "",
        "route": "Durgachak - Medinipur",
        "source": "facebook (community report)",
        "detail_url": "",
        "contact_number": "8001103038, 8001102022",
        "stops": st(
            ("Durgachak", "9:45 AM", ""),
            ("Manjushree More", "", ""),
            ("Hazra More", "", ""),
            ("Sutahata", "", ""),
            ("Chaitanyapur", "", ""),
            ("Dwariberia", "", ""),
            ("Lakshya", "", ""),
            ("Baburhat", "", ""),
            ("Terpeksha More", "", ""),
            ("Mahishadal", "", ""),
            ("Namlaksha Bazar", "", ""),
            ("Nandakumar Bazar", "", ""),
            ("Puiyada", "", ""),
            ("Byabattarhat", "", ""),
            ("Nimtala", "", ""),
            ("Tamluk", "", ""),
            ("Maniktala", "", ""),
            ("Radhaballavpur", "", ""),
            ("Dimari", "", ""),
            ("Kanktiya", "", ""),
            ("Santipur", "", ""),
            ("Mecheda", "", ""),
            ("Siddha Bazar", "", ""),
            ("Deulia Bazar", "", ""),
            ("Mechogram", "", ""),
            ("Panskura", "", ""),
            ("Ashari", "", ""),
            ("Debra", "", ""),
            ("Basantpur", "", ""),
            ("Madpur", "", ""),
            ("Medinipur", "", "4:40 PM"),
        ),
    },
    {
        "operator": "Krishna",
        "bus_name": "Krishna Supa-Baruipur (Super Fast)",
        "bus_type": "Private",
        "reg_no": "WB 39C 2142",
        "origin": "Supa",
        "destination": "Baruipur",
        "departure_time": "4:00 AM",
        "arrival_time": "",
        "route": "Supa - Baruipur",
        "source": "facebook (community report)",
        "detail_url": "",
        "contact_number": "8653947098, 9903121330",
        "stops": st(
            ("Supa", "4:00 AM", ""),
            ("Neredeul", "4:15 AM", ""),
            ("Mugbasan", "", ""),
            ("Keshpur", "4:40 AM", ""),
            ("Nadajol", "5:05 AM", ""),
            ("Rajnagar", "", ""),
            ("Bakultala", "5:45 AM", "4:05 PM"),
            ("Goura", "6:00 AM", ""),
            ("Mechogram", "", "3:45 PM"),
            ("Siddha Bazar", "", ""),
            ("Haldia More", "", ""),
            ("Bagnan", "", ""),
            ("Ranihati", "", ""),
            ("Dhulagarh", "", ""),
            ("Santragachi", "", "2:05 PM"),
            ("Second Hooghly Bridge", "", ""),
            ("PG", "", "1:45 PM"),
            ("Minto Park", "", "1:35 PM"),
            ("Moulali", "", "1:25 PM"),
            ("CIT Road", "", "1:15 PM"),
            ("Science City", "", "12:50 PM"),
            ("Ruby", "", "12:30 PM"),
            ("Kamalgazi", "", "12:15 PM"),
            ("Baruipur", "", "12:00 PM"),
        ),
    },
    {
        "operator": "SBSTC",
        "bus_name": "SBSTC Kalna-Bardhaman-Digha",
        "bus_type": "Government",
        "reg_no": "WB 39B 9153",
        "origin": "Kalna",
        "destination": "Digha",
        "departure_time": "5:30 AM",
        "arrival_time": "",
        "route": "Kalna - Digha",
        "source": "facebook (community report)",
        "detail_url": "",
        "contact_number": "",
        "stops": st(
            ("Kalna", "5:30 AM", ""),
            ("Dhatrighram", "", ""),
            ("Madhupur", "", ""),
            ("Bohar", "", ""),
            ("Bulbulitala", "", ""),
            ("Satgachia", "", ""),
            ("Hatgobindpur", "", ""),
            ("Paharhati", "", ""),
            ("Kalna Gate", "", ""),
            ("Bardhaman Station", "", ""),
            ("Golapbag", "", ""),
            ("Bardhaman Nawabhat Bus Stand", "7:45 AM", "6:10 PM"),
            ("Bardhaman Bypass", "", ""),
            ("Bardhaman Alisha Bus Stand", "8:15 AM", ""),
            ("Telipukur", "", ""),
            ("Bankura More", "", ""),
            ("Seharabazar", "", ""),
            ("Uchalan", "", ""),
            ("Pollishree", "", ""),
            ("Arambagh", "", ""),
            ("Goghat", "", ""),
            ("Kamarpukur", "", ""),
            ("Ramjivanpur", "", ""),
            ("Kshirpai", "", ""),
            ("Radhanagar", "", ""),
            ("Ghatal", "", ""),
            ("Daspur", "", ""),
            ("Sultannagar", "", ""),
            ("Goura", "", ""),
            ("Sonamui", "", ""),
            ("Khukurdah", "", ""),
            ("Keshapat", "", ""),
            ("Mechgram", "", ""),
            ("Siddha", "", ""),
            ("Deulia Bazar", "", ""),
            ("Haldia More", "", ""),
            ("Mecheda", "", ""),
            ("Radhamani", "", ""),
            ("Nimtouri", "", ""),
            ("Nandakumar", "", ""),
            ("Norghat", "", ""),
            ("Chandipur", "", ""),
            ("Bajkul", "", ""),
            ("Heria", "", ""),
            ("Kalingar", "", ""),
            ("Nachinda", "", ""),
            ("Morishda", "", ""),
            ("Kanthi", "", "11:10 AM"),
            ("Chaulkhola", "", ""),
            ("Balisai", "", ""),
            ("Ramnagar", "", ""),
            ("Digha", "", "10:15 AM"),
        ),
    },
]

UPDATES = [
    {
        "id": "wbbustime-gobinda-0",
        "marker": "Mandarmani",
        "fields": {
            "bus_name": "GOBINDA (AC Coach)",
            "operator": "Gobinda",
            "bus_type": "Private - AC (3/2 Seat)",
            "origin": "Medinipur",
            "destination": "Mandarmani",
            "departure_time": "8:55 AM",
            "arrival_time": "",
            "contact_number": "9635410808, 8777451638",
            "route": "Medinipur - Mandarmani",
            "total_stoppages": 12,
        },
        "stoppages": sp(
            ("Medinipur", "8:55 AM", ""),
            ("Mohonpur", "", ""),
            ("Kharagpur Chowringhee", "", "5:20 PM"),
            ("Kharagpur Station", "9:45 AM", ""),
            ("Belda", "10:40 AM", "4:40 PM"),
            ("Khakurda", "", ""),
            ("Egra", "11:30 AM", "3:50 PM"),
            ("Satmile", "", ""),
            ("Kanthi", "12:15 PM", "3:10 PM"),
            ("Pichabani", "", ""),
            ("Chaulkhola", "", ""),
            ("Mandarmani", "", "2:05 PM"),
        ),
    },
    {
        "id": "wbbustime-jai-maa-durga-0",
        "marker": "Kishanganj",
        "fields": {
            "bus_name": "JOY MAA DURGA",
            "operator": "Joy Maa Durga",
            "bus_type": "Private",
            "origin": "Bandwan",
            "destination": "Siliguri",
            "departure_time": "3:05 PM",
            "arrival_time": "7:00 AM",
            "contact_number": "9933726130",
            "route": "Bandwan - Siliguri",
            "total_stoppages": 14,
        },
        "stoppages": sp(
            ("Bandwan", "3:05 PM", "8:00 AM"),
            ("Manbazar", "4:05 PM", "7:20 AM"),
            ("Hatirampur", "", ""),
            ("Bangla", "", ""),
            ("Puabagan", "", ""),
            ("Bankura", "5:45 PM", "5:30 AM"),
            ("Durgapur (City Center)", "7:25 PM", "4:00 AM"),
            ("Bolpur", "8:50 PM", ""),
            ("Morgram", "", "11:10 PM"),
            ("Farakka", "", ""),
            ("Malda", "", "9:20 PM"),
            ("Dalkhola", "", ""),
            ("Kishanganj", "5:25 AM", ""),
            ("Siliguri", "", "3:05 PM"),
        ),
    },
    {
        "id": "bussathi-major-467",
        "marker": "Biringi More",
        "fields": {
            "bus_name": "MAJOR",
            "operator": "Major",
            "bus_type": "Private - Interstate",
            "origin": "Durgapur (Station)",
            "destination": "Bokaro",
            "departure_time": "5:50 AM",
            "arrival_time": "10:30 AM",
            "contact_number": "9332870587",
            "route": "Durgapur (Station) - Bokaro",
            "total_stoppages": 17,
        },
        "stoppages": sp(
            ("Durgapur (Station)", "5:50 AM", "5:05 PM"),
            ("Durgapur (City Center)", "6:00 AM", "4:50 PM"),
            ("Biringi More", "", ""),
            ("Raniganj (Punjabi More)", "", ""),
            ("Asansol", "7:15 AM", "3:45 PM"),
            ("Magama", "", ""),
            ("Nirsa", "", ""),
            ("Tetulia", "", ""),
            ("Ratanpur", "", ""),
            ("Govindpur", "", ""),
            ("Dhanbad", "8:15 AM", "2:00 PM"),
            ("Kusunda", "", ""),
            ("Kapuria", "", ""),
            ("Mahuda More", "", ""),
            ("Kalapathar", "", ""),
            ("Chas", "10:15 AM", "12:25 PM"),
            ("Bokaro", "10:30 AM", "12:10 PM"),
        ),
    },
    {
        "id": "bussathi-aadrika-5",
        "marker": "Panchrulia",
        "fields": {
            "bus_name": "AADRIKA (KARGIL)",
            "operator": "Aadrika",
            "bus_type": "Private",
            "origin": "Durgachak",
            "destination": "Jhargram",
            "departure_time": "6:55 AM",
            "arrival_time": "",
            "contact_number": "8250013993",
            "route": "Durgachak - Jhargram",
            "total_stoppages": 30,
        },
        "stoppages": sp(
            ("Durgachak", "6:55 AM", ""),
            ("Manjushree More", "", ""),
            ("Chaitanyapur", "", ""),
            ("Mahishadal", "7:40 AM", "5:35 PM"),
            ("Nandakumar Bazar", "", ""),
            ("Tamluk", "8:10 AM", "4:50 PM"),
            ("Maniktala", "", ""),
            ("Mecheda", "8:50 AM", "4:20 PM"),
            ("Siddha Bazar", "", ""),
            ("Deulia Bazar", "", ""),
            ("Mechogram", "", ""),
            ("Panskura", "", ""),
            ("Ashari", "", ""),
            ("Debra", "9:50 AM", "3:15 PM"),
            ("Basantpur", "", ""),
            ("Madpur", "", ""),
            ("Kharagpur Chowringhee", "", ""),
            ("Kharagpur Station", "10:50 AM", "2:20 PM"),
            ("Reshmi Metallic", "", ""),
            ("Panchrulia", "", ""),
            ("Sahachak", "", ""),
            ("Nimpura", "", ""),
            ("Bombay Road", "", ""),
            ("Guptamani", "", ""),
            ("Balibhasa", "", ""),
            ("Gazashimukh", "", ""),
            ("Lodhashuli", "11:50 AM", "1:25 PM"),
            ("Garo", "", ""),
            ("Kalabuni", "", ""),
            ("Jhargram", "", "1:00 PM"),
        ),
    },
    {
        "id": "bussathi-debjit-0",
        "marker": "Amlatora",
        "fields": {
            "bus_name": "DEBJIT (OLISHA)",
            "operator": "Debjit",
            "bus_type": "Private",
            "origin": "Keshargarh",
            "destination": "Santaldih",
            "departure_time": "6:00 AM",
            "arrival_time": "",
            "contact_number": "",
            "route": "Keshargarh - Santaldih",
            "total_stoppages": 16,
        },
        "stoppages": sp(
            ("Keshargarh", "6:00 AM", ""),
            ("Chatumadar", "", ""),
            ("Amlatora", "", ""),
            ("Hijuli", "", ""),
            ("Daldali", "", ""),
            ("Lalpur", "6:40 AM", "3:40 PM"),
            ("Hura", "7:00 AM", "3:35 PM"),
            ("Damankiari", "", ""),
            ("Simla", "", ""),
            ("Gamarcuri", "", ""),
            ("Kashipur", "7:30 AM", "3:00 PM"),
            ("Adra", "8:00 AM", "2:30 PM"),
            ("Raghunathpur", "8:50 AM", "2:05 PM"),
            ("Dubra", "", ""),
            ("Paharigora", "", ""),
            ("Santaldih", "", "12:40 PM"),
        ),
    },
]


def main():
    changed = False

    p = ROOT / "data" / "busjatri_data.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    by_id = {b["id"]: b for b in d["buses"]}

    for u in UPDATES:
        b = by_id.get(u["id"])
        assert b, f"missing {u['id']}"
        names = [s.get("name") for s in b.get("stoppages") or []]
        if u["marker"] in names:
            print(f"{u['id']}: already updated - skip")
            continue
        b.update(u["fields"])
        b["stoppages"] = u["stoppages"]
        changed = True
        print(f"{u['id']}: updated ({b['bus_name']}, {b['total_stoppages']} stops)")

    pc = ROOT / "data" / "community_buses.json"
    cb = json.loads(pc.read_text(encoding="utf-8"))
    for e in NEW_BUSES:
        if any(e["bus_name"] in (x.get("bus_name") or "") for x in cb.get("add", [])):
            print(f"{e['bus_name']}: already present - skip")
            continue
        cb["add"].append(e)
        changed = True
        print(f"{e['bus_name']}: appended")

    if DRY or not changed:
        print("dry run or no changes - nothing written")
        return
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    pc.write_text(json.dumps(cb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written")


main()
