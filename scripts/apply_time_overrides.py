#!/usr/bin/env python3
"""Merge data/time-overrides.json into data/busjatri_data.json.

Overrides come from the admin panel (admin.html) and are applied at
runtime by js/time-overrides.js; this script makes them permanent by
merging them into the source data during rebuilds (auto-update /
apply-overrides workflows), so scheduled re-scrapes cannot revert them.

Format: { "<bus-id>": { "<stop name>": {"up": "9:30 AM", "down": "…"} } }
Run with no arguments; edits data/busjatri_data.json in place.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'busjatri_data.json'
OVR = ROOT / 'data' / 'time-overrides.json'


def fix():
    if not OVR.exists():
        print('No time-overrides.json — nothing to do')
        return 0
    overrides = json.loads(OVR.read_text(encoding='utf-8'))
    if not overrides:
        print('time-overrides.json is empty — nothing to do')
        return 0

    d = json.loads(DATA.read_text(encoding='utf-8'))
    n_fixed = 0
    report = []
    for b in d['buses']:
        ov = overrides.get(b.get('id'))
        if not ov:
            continue
        for s in b.get('stoppages') or []:
            t = ov.get(s.get('name'))
            if not t:
                continue
            if t.get('up') and s.get('up_time') != t['up']:
                report.append(f"{b.get('reg_no') or b.get('bus_name')} @{s.get('name')}: "
                               f"up {s.get('up_time')} -> {t['up']}")
                s['up_time'] = t['up']
                n_fixed += 1
            if t.get('down') and s.get('down_time') != t['down']:
                report.append(f"{b.get('reg_no') or b.get('bus_name')} @{s.get('name')}: "
                               f"down {s.get('down_time')} -> {t['down']}")
                s['down_time'] = t['down']
                n_fixed += 1

    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Time overrides merged: {n_fixed} changes across '
          f'{len(overrides)} bus(es)')
    for r in report:
        print(' ', r)
    return n_fixed


if __name__ == '__main__':
    fix()
