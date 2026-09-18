#!/usr/bin/env python3
"""FB community batch 3 (2026-09-18 evening):

NEW buses (appended to data/community_buses.json):
  1. BISHWABHARATI RAY TRAVELS  Bolpur <-> Bardhaman (WB 41F 9125)
  2. MDG PARIBAHAN  Bishnupur -> Karunamoyee (WB 18AP 8592, Sun closed)
  3. KULPI-NEWTOWN new BS6 bus (WB 07AA 1323, via Esplanade/Sealdah)

UPDATES (same buses already in data, enriched):
  4. ANNESWA TRAVELS (bussathi-annesha-46) Majhdia <-> Bardhaman -
     new chassis WB 51L 8889 (Eicher LPO 3016L) + full stops/times
  5. MAHARAJA (bussathi-maharaja-1) Purulia <-> Durgapur -
     AC 3x2 pushback, full route + times + contacts

MERGE + DELETE:
  6. bussathi-jai-maa-durga-265 (JAI MAA DURGA) is the same physical
     bus as wbbustime-jai-maa-durga-0 (JOY MAA DURGA) - same route,
     same 3:05 PM departure. Extra stops merged into the kept entry,
     duplicate removed.

SKIP: Shree Krishna Travels (added earlier today, data already
complete) and the Joy Maa Durga update itself (done earlier today).

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
        "operator": "Bishwabharati Ray Travels",
        "bus_name": "Bishwabharati Ray Travels Bolpur-Bardhaman",
        "bus_type": "Private",
        "reg_no": "WB 41F 9125",
        "origin": "Bolpur",
        "destination": "Bardhaman",
        "departure_time": "7:20 AM",
        "arrival_time": "",
        "route": "Bolpur - Bardhaman",
        "source": "facebook (community report)",
        "detail_url": "",
        "contact_number": "",
        "stops": st(
            ("Bolpur", "7:20 AM", "3:45 PM"),
            ("Supur", "", ""),
            ("Bhediya", "7:50 AM", "2:30 PM"),
            ("Kalidah", "", ""),
            ("Kurumba", "", ""),
            ("Dinnathpur", "", ""),
            ("Uttar Ramnagar", "", ""),
            ("Morbandh", "8:30 AM", "2:10 PM"),
            ("Banbagram", "", ""),
            ("Ausgram", "", ""),
            ("Somaipur", "", ""),
            ("Alutia", "", ""),
            ("Guskara Railgate", "", ""),
            ("Guskara Bus Stand", "9:25 AM", "1:05 PM"),
            ("Bolgona More", "", ""),
            ("Shibda More", "", ""),
            ("Odgram", "", ""),
            ("Jhnapur", "", ""),
            ("Barachaumatha", "", ""),
            ("Kayrapur", "", ""),
            ("Natungram", "", ""),
            ("Mainagar", "", ""),
            ("Haldi", "", ""),
            ("Alampur", "", ""),
            ("Talit", "", ""),
            ("Talit Railgate", "", ""),
            ("Jhinguti More", "", ""),
            ("108 Shiva Mandir", "", "12:10 PM"),
        ),
    },
    {
        "operator": "MDG Paribahan",
        "bus_name": "MDG Paribahan Bishnupur-Karunamoyee",
        "bus_type": "Private",
        "reg_no": "WB 18AP 8592",
        "origin": "Bishnupur",
        "destination": "Karunamoyee",
        "departure_time": "5:10 AM",
        "arrival_time": "",
        "route": "Bishnupur - Karunamoyee",
        "source": "facebook (community report)",
        "detail_url": "",
        "contact_number": "9093202629",
        "stops": st(
            ("Bishnupur", "5:10 AM", ""),
            ("Birai More", "", ""),
            ("Jaypur", "", ""),
            ("Chatra", "", ""),
            ("Kotulpur", "", ""),
            ("Khatul", "", ""),
            ("Bengai", "", ""),
            ("Arambagh", "6:35 AM", "4:30 PM"),
            ("Mayapur", "", ""),
            ("Champadanga", "", ""),
            ("Haripal More", "", ""),
            ("Siyakhala", "", ""),
            ("Mashat", "", ""),
            ("Chanditala", "", ""),
            ("Dankuni", "", ""),
            ("Dakshineswar", "", ""),
            ("Dunlop", "", ""),
            ("Belgharia Expressway", "", ""),
            ("Airport", "", ""),
            ("Kaikhali", "", ""),
            ("Chinar Park", "", ""),
            ("Akanksha More", "", ""),
            ("Eco Park", "", ""),
            ("Narkelbagan", "", ""),
            ("Biswabangla Gate", "", ""),
            ("Newtown", "", ""),
            ("DLF", "", ""),
            ("Mahishbathan", "", ""),
            ("College More", "", ""),
            ("Sector V", "", ""),
            ("Karunamoyee", "", "1:50 PM"),
        ),
    },
    {
        "operator": "",
        "bus_name": "Kulpi-Newtown (Shapoorji) New BS6 Bus",
        "bus_type": "Private - New BS6",
        "reg_no": "WB 07AA 1323",
        "origin": "Kulpi",
        "destination": "Newtown (Shapoorji)",
        "departure_time": "7:15 AM",
        "arrival_time": "11:00 AM",
        "route": "Kulpi - Newtown (Shapoorji)",
        "source": "facebook (community report)",
        "detail_url": "",
        "contact_number": "",
        "stops": st(
            ("Kulpi", "7:15 AM", "6:00 PM"),
            ("Hatugung", "", ""),
            ("Netra", "", ""),
            ("Usthi", "", ""),
            ("Sirakole", "", ""),
            ("Amtala", "8:15 AM", "5:00 PM"),
            ("Thakurpukur", "8:45 AM", "4:30 PM"),
            ("Behala", "", ""),
            ("Taratala", "", ""),
            ("Majerhat", "", "4:05 PM"),
            ("Mominpur", "9:10 AM", ""),
            ("Bhawani Bhawan", "9:20 AM", ""),
            ("Alipore", "", ""),
            ("PG/PTS", "9:25 AM", "3:55 PM"),
            ("Rabindra Sadan", "", ""),
            ("Esplanade", "9:40 AM", "3:45 PM"),
            ("Moulali", "", ""),
            ("Sealdah", "10:00 AM", "3:30 PM"),
            ("Beleghata", "10:10 AM", "3:20 PM"),
            ("Building More", "", ""),
            ("Chingrighata", "10:20 AM", "3:10 PM"),
            ("Nicco Park", "", ""),
            ("Sector V", "10:35 AM", "2:55 PM"),
            ("Technopolis", "", ""),
            ("Newtown", "10:50 AM", "2:40 PM"),
            ("Biswabangla Gate", "", ""),
            ("Candor Gate", "", ""),
            ("UEM IEM Campus", "", ""),
            ("Karigari Bhawan", "10:55 AM", "2:35 PM"),
            ("Shapoorji", "11:00 AM", "2:30 PM"),
        ),
    },
]

ANNESWA_STOPS = sp(
    ("Majhdia", "7:10 AM", "7:20 PM"),
    ("Krishnaganj", "", ""),
    ("Bhimpur", "", ""),
    ("Asannagar", "", ""),
    ("Krishnanagar", "8:40 AM", "5:50 PM"),
    ("Highroad", "", ""),
    ("Gouranga Setu", "", ""),
    ("Nabadwip Railgate", "9:20 AM", "5:00 PM"),
    ("Hematpur More", "", ""),
    ("Nadanghat More", "", ""),
    ("Nadanghat", "", ""),
    ("Kusumgram", "10:25 AM", "4:00 PM"),
    ("Malamba", "", ""),
    ("Bhandardighi", "", ""),
    ("Kurmun", "", ""),
    ("Dewandighi More", "", ""),
    ("Bardhaman Rail Station", "", ""),
    ("College More", "", ""),
    ("Bardhaman Nawabhat", "11:45 AM", "2:40 PM"),
)

MAHARAJA_STOPS = sp(
    ("Purulia", "4:35 AM", "8:00 PM"),
    ("Ladhurka", "", ""),
    ("Lakshanpur", "", ""),
    ("Lalpur", "5:20 AM", "7:10 PM"),
    ("Hura", "", ""),
    ("Bishpuria", "5:30 AM", "7:00 PM"),
    ("Payrachali", "", ""),
    ("Hatgram", "", ""),
    ("Shaluni", "", ""),
    ("Bhagwanpur", "", ""),
    ("Kalapathar", "", ""),
    ("Kumidya", "", ""),
    ("Puabagan", "", ""),
    ("Rajgram", "", ""),
    ("Bankura Pump More", "6:35 AM", "6:00 PM"),
    ("Bankura Satighat Bridge", "6:55 AM", ""),
    ("Beliatore", "", ""),
    ("Barjora", "", ""),
    ("Lakhyatora Bridge", "", "5:45 PM"),
    ("Durgapur (Station)", "8:00 AM", "4:35 PM"),
    ("Durgapur (City Center)", "8:15 AM", "4:00 PM"),
)

# merged JOY MAA DURGA stop list (own FB report + bussathi-265 extra stops)
JOY_MAA_DURGA_STOPS = sp(
    ("Bandwan", "3:05 PM", "8:00 AM"),
    ("Boro", "", ""),
    ("Manbazar", "4:05 PM", "7:20 AM"),
    ("Hatirampur", "", ""),
    ("Bangla", "5:00 PM", "6:00 AM"),
    ("Puabagan", "", ""),
    ("Bankura", "5:45 PM", "5:30 AM"),
    ("Beliatore", "", ""),
    ("Barjora", "", ""),
    ("Durgapur (Station)", "", ""),
    ("Durgapur (City Center)", "7:25 PM", "4:00 AM"),
    ("Durgapur (Muchipara)", "", ""),
    ("Illambazar", "", ""),
    ("Bolpur", "8:50 PM", "2:20 AM"),
    ("Suri", "9:40 PM", ""),
    ("Morgram", "", "11:10 PM"),
    ("Farakka", "", ""),
    ("Malda", "1:40 AM", "9:20 PM"),
    ("Gozole", "", ""),
    ("Dalkhola", "", ""),
    ("Raiganj", "3:40 AM", ""),
    ("Islampur", "", ""),
    ("Kishanganj", "5:25 AM", ""),
    ("Siliguri", "7:00 AM", "3:05 PM"),
)

DELETE_IDS = ["bussathi-jai-maa-durga-265"]


def main():
    changed = False

    p = ROOT / "data" / "busjatri_data.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    by_id = {b["id"]: b for b in d["buses"]}

    # --- merge JOY MAA DURGA, delete duplicate ---
    joy = by_id.get("wbbustime-jai-maa-durga-0")
    assert joy, "missing wbbustime-jai-maa-durga-0"
    if any(s.get("name") == "Raiganj" for s in joy.get("stoppages") or []):
        print("JOY MAA DURGA: already merged - skip")
    else:
        joy["stoppages"] = JOY_MAA_DURGA_STOPS
        joy["total_stoppages"] = len(JOY_MAA_DURGA_STOPS)
        changed = True
        print("JOY MAA DURGA: merged with bussathi copy (24 stops)")

    if DELETE_IDS[0] in by_id:
        d["buses"] = [b for b in d["buses"] if b["id"] not in DELETE_IDS]
        changed = True
        print("removed duplicate:", ", ".join(DELETE_IDS))
    else:
        print("duplicate already removed - skip")

    # --- enrich ANNESWA ---
    b = by_id.get("bussathi-annesha-46")
    assert b, "missing bussathi-annesha-46"
    if "Gouranga Setu" in [s.get("name") for s in b.get("stoppages") or []]:
        print("ANNESWA: already updated - skip")
    else:
        b.update(
            {
                "bus_name": "ANNESWA TRAVELS",
                "operator": "Anneswa Travels",
                "bus_type": "Private",
                "reg_no": "WB 51L 8889",
                "origin": "Majhdia",
                "destination": "Bardhaman",
                "departure_time": "7:10 AM",
                "arrival_time": "11:45 AM",
                "contact_number": "",
                "route": "Majhdia - Bardhaman",
                "stoppages": ANNESWA_STOPS,
                "total_stoppages": len(ANNESWA_STOPS),
            }
        )
        changed = True
        print("ANNESWA TRAVELS: enriched (new chassis WB 51L 8889, 19 stops)")

    # --- enrich MAHARAJA ---
    b = by_id.get("bussathi-maharaja-1")
    assert b, "missing bussathi-maharaja-1"
    if "Shaluni" in [s.get("name") for s in b.get("stoppages") or []]:
        print("MAHARAJA: already updated - skip")
    else:
        b.update(
            {
                "bus_name": "MAHARAJA (AC)",
                "operator": "Maharaja",
                "bus_type": "Private - AC Pushback (3x2)",
                "reg_no": "WB 55E 8111",
                "origin": "Purulia",
                "destination": "Durgapur (City Center)",
                "departure_time": "4:35 AM",
                "arrival_time": "8:15 AM",
                "contact_number": "9933623594, 8927432206 (Purulia); 9851510678 (Bankura); 8509081145 (Durgapur)",
                "route": "Purulia - Durgapur (City Center)",
                "stoppages": MAHARAJA_STOPS,
                "total_stoppages": len(MAHARAJA_STOPS),
            }
        )
        changed = True
        print("MAHARAJA (AC): enriched (21 stops + times + contacts)")

    # --- new community buses ---
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
