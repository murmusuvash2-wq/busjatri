#!/usr/bin/env python3
"""Add 2 buses from FB community post (2026-09-20):

1. SHIVAM (PRIYANKA) - Bhutshahar <-> Bankura via Simlapal, Khatra
   UP:   Bhutshahar 7:50 AM -> Bankura 11:50 AM
   DOWN: Bankura 1:55 PM -> Bhutshahar 6:10 PM
   (no reg no / contact in post)

2. RBN TRAVELS - Barabazar <-> Bishnupur via Manbazar, Taldangra
   reg WB 55B 5418, contact 7384329324
   UP:   Barabazar 7:15 AM -> Bishnupur 11:30 AM
   DOWN: Bishnupur 12:50 PM -> Barabazar 5:40 PM

Idempotent: skips each bus if (origin, destination, operator) already
present in community_buses.json adds.
"""
import argparse
import json

PATH = 'data/community_buses.json'

SHIVAM = {
    "operator": "Priyanka",
    "bus_name": "SHIVAM (PRIYANKA)",
    "bus_type": "Private - Non AC",
    "reg_no": "",
    "origin": "Bhutshahar",
    "destination": "Bankura",
    "departure_time": "7:50 AM",
    "arrival_time": "11:50 AM",
    "route": "Bhutshahar - Simlapal - Khatra - Bankura",
    "source": "facebook (community report)",
    "detail_url": "",
    "stops": [
        {"name": "Bhutshahar", "up": "7:50 AM", "down": "6:10 PM"},
        {"name": "Simlapal", "up": "8:50 AM", "down": "5:20 PM"},
        {"name": "Lakshmisagar", "up": "", "down": ""},
        {"name": "Khatra", "up": "10:00 AM", "down": "4:00 PM"},
        {"name": "Hatirampur", "up": "", "down": ""},
        {"name": "Bangla", "up": "", "down": ""},
        {"name": "Dholdanga", "up": "", "down": ""},
        {"name": "Bankura", "up": "11:50 AM", "down": "1:55 PM"},
    ],
}

RBN = {
    "operator": "RBN Travels",
    "bus_name": "RBN TRAVELS",
    "bus_type": "Private - Non AC",
    "reg_no": "WB 55B 5418",
    "origin": "Barabazar",
    "destination": "Bishnupur",
    "departure_time": "7:15 AM",
    "arrival_time": "11:30 AM",
    "route": "Barabazar - Manbazar - Taldangra - Bishnupur",
    "source": "facebook (community report)",
    "detail_url": "",
    "stops": [
        {"name": "Barabazar", "up": "7:15 AM", "down": "5:40 PM"},
        {"name": "Sindri", "up": "7:45 AM", "down": "5:10 PM"},
        {"name": "Duarsini", "up": "", "down": ""},
        {"name": "Manbazar", "up": "8:30 AM", "down": "4:45 PM"},
        {"name": "Payrachali", "up": "8:50 AM", "down": "4:00 PM"},
        {"name": "Hatirampur", "up": "9:20 AM", "down": "3:40 PM"},
        {"name": "Biborda", "up": "9:45 AM", "down": "3:15 PM"},
        {"name": "Taldangra", "up": "10:10 AM", "down": "2:40 PM"},
        {"name": "Panchmura", "up": "10:25 AM", "down": "1:30 PM"},
        {"name": "Sabrakon", "up": "", "down": ""},
        {"name": "Bankadah", "up": "11:00 AM", "down": "1:00 PM"},
        {"name": "Dhadika", "up": "", "down": ""},
        {"name": "Bishnupur", "up": "11:30 AM", "down": "12:50 PM"},
    ],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    d = json.load(open(PATH, encoding='utf-8'))

    for bus in (SHIVAM, RBN):
        dup = any(
            a.get('origin') == bus['origin']
            and a.get('destination') == bus['destination']
            and a.get('operator') == bus['operator']
            for a in d['add']
        )
        if dup:
            print(f"{bus['bus_name']} already in community_buses.json — skipped.")
            continue
        d['add'].append(bus)
        if args.write:
            print(f"WROTE: {bus['bus_name']} ({bus['origin']} -> {bus['destination']})")

    if args.write:
        json.dump(d, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f"total adds now: {len(d['add'])}")
    else:
        print('(dry run - use --write)')


if __name__ == '__main__':
    main()
