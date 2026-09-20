#!/usr/bin/env python3
"""Fetch user reports from the published Google Sheet CSV and merge into
data/time-reports.json (read by the admin panel and by
scripts/apply_approved_reports.py).

Setup (one-time): open the BusJatri Time Reports sheet ->
File > Share > Publish to web -> select Sheet1 -> CSV -> Publish,
then paste that URL into CSV_URL below (or set CSV_URL env var).

Sheet columns (A..N): Timestamp, Bus, Reg No, Route, Current Time,
Correct Time, Note, Page URL, Bus ID, Type, Stop, Direction, Name, Status.
Submissions come from the site via the Apps Script receiver; approve a row
by writing 'approved' in the Status column (or 'rejected').
"""
import csv
import io
import json
import os
import urllib.request
from pathlib import Path

CSV_URL = os.environ.get('CSV_URL', '')  # e.g. https://docs.google.com/spreadsheets/d/e/aaaa/pub?output=csv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'time-reports.json'
COLS = ['ts', 'bus', 'reg', 'route', 'current', 'time', 'note', 'page', 'bus_id',
        'type', 'stop', 'dir', 'name', 'status']
HEADERS = {
    'Timestamp': 'ts', 'Bus': 'bus', 'Reg No': 'reg', 'Route': 'route',
    'Current Time': 'current', 'Correct Time': 'time', 'Note': 'note',
    'Page URL': 'page', 'Bus ID': 'bus_id', 'Type': 'type', 'Stop': 'stop',
    'Direction': 'dir', 'Name': 'name', 'Status': 'status',
}


def main():
    if not CSV_URL:
        print('CSV_URL not configured yet - nothing to do')
        return 0
    req = urllib.request.Request(CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
    raw = urllib.request.urlopen(req, timeout=30).read().decode('utf-8-sig')
    rows = list(csv.reader(io.StringIO(raw)))
    if len(rows) < 2:
        print('CSV empty - nothing to do')
        return 0
    header = [h.strip() for h in rows[0]]
    idx = {v: header.index(k) for k, v in HEADERS.items() if k in header}

    reports = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else []
    known = {(r.get('ts', ''), r.get('bus', ''), r.get('time', ''), r.get('stop', ''),
              r.get('type', '')) for r in reports}
    by_key = {(r.get('ts', ''), r.get('bus', ''), r.get('time', ''), r.get('stop', ''),
              r.get('type', '')): r for r in reports}
    added = 0
    for r in rows[1:]:
        if len(r) < len(header):
            r = r + [''] * (len(header) - len(r))
        rec = {c: '' for c in COLS}
        rec['status'] = 'new'
        for col, key in idx.items():
            rec[col] = r[key].strip()
        if not rec['ts'].startswith('(') and not rec['time'] and not rec['type']:
            continue  # skip rows with no time and no type
        if rec['ts'].startswith('('):
            continue  # example row
        k = (rec['ts'], rec['bus'], rec['time'], rec['stop'], rec['type'])
        if k in known:
            # keep the local copy but refresh the status from the sheet
            if rec['status']:
                by_key[k]['status'] = rec['status']
            continue
        known.add(k)
        reports.append(rec)
        added += 1

    OUT.write_text(json.dumps(reports, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'time reports: {added} new, {len(reports)} total')
    return added


if __name__ == '__main__':
    main()
