#!/usr/bin/env python3
"""Add APURBA (Khatra -> Kharagpur) from FB post (Manbazar Bus Route Update).

Owner: Madhusudan, contact 7602258942, reg WB/49D/0372.
UP: Khatra 6:45 AM -> Kharagpur Station 11:20 AM
DOWN: Kharagpur 12:15 PM -> Khatra 4:55 PM (halt)

KALYAN TRAVEL'S (same FB post) already in data as bussathi-kalyan-322
(Jhalda -> Jhargram, 25 stops) — post is a bussathi repost, no action needed.

Idempotent: skips if (Khatra, Kharagpur, Madhusudan) already present in
community_buses.json adds.
"""
import argparse
import json

PATH = 'data/community_buses.json'

APURBA = {
    "operator": "Madhusudan",
    "bus_name": "APURBA",
    "bus_type": "Private - Non AC",
    "reg_no": "WB 49D 0372",
    "origin": "Khatra",
    "destination": "Kharagpur",
    "departure_time": "6:45 AM",
    "arrival_time": "11:20 AM",
    "route": "Khatra - Ranibandh - Belpahari - Jhargram - Kharagpur",
    "source": "facebook (Manbazar Bus Route Update)",
    "detail_url": "",
    "stops": [
        {"name": "Khatra", "up": "6:45 AM", "down": "4:55 PM"},
        {"name": "Ranibandh", "up": "7:15 AM", "down": "4:25 PM"},
        {"name": "Paradi", "up": "7:55 AM", "down": "3:50 PM"},
        {"name": "Belpahari", "up": "8:40 AM", "down": "2:50 PM"},
        {"name": "Shilda", "up": "9:00 AM", "down": "2:30 PM"},
        {"name": "Binpur", "up": "", "down": ""},
        {"name": "Jhargram", "up": "9:55 AM", "down": "1:40 PM"},
        {"name": "Lodhasuli", "up": "10:25 AM", "down": "1:10 PM"},
        {"name": "Chaurangi", "up": "11:05 AM", "down": "12:30 PM"},
        {"name": "Kharagpur Station", "up": "11:20 AM", "down": "12:15 PM"},
    ],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    d = json.load(open(PATH, encoding='utf-8'))

    dup = any(
        a.get('origin') == APURBA['origin']
        and a.get('destination') == APURBA['destination']
        and a.get('operator') == APURBA['operator']
        for a in d['add']
    )
    if dup:
        print('APURBA already in community_buses.json — nothing to do.')
        return

    d['add'].append(APURBA)
    if args.write:
        json.dump(d, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('WROTE: APURBA appended to', PATH, f"(now {len(d['add'])} adds)")
    else:
        print('(dry run) would append APURBA — use --write')


if __name__ == '__main__':
    main()
