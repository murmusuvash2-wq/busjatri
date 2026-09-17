#!/usr/bin/env python3
"""Fix AM/PM typos in stoppage times (the source sites have them).

Example: bussathi.in shows a Chhatna return time of "2:00 AM" between
Kharbona 1:40 PM and Bankura 2:15 PM — obviously meant to be 2:00 PM.

A time is only flipped when there is strong evidence: an AM time whose
12-hour shift fits cleanly with its PM neighbours in journey order
(up trip reads the stop list forward, down trip reads it in reverse).
Genuine overnight buses (depart 9 PM, arrive 5 AM) are left untouched.
Run with no arguments; edits data/busjatri_data.json in place.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'busjatri_data.json'

TIME_RE = re.compile(r'^(\d{1,2}):(\d{2})\s*(AM|PM)$')

def to_min(t):
    m = TIME_RE.match((t or '').strip())
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap == 'AM':
        h = 0 if h == 12 else h
    else:
        h = 12 if h == 12 else h + 12
    return h * 60 + mi

def to_ampm(m):
    h, mi = divmod(m, 60)
    ap = 'AM' if h < 12 else 'PM'
    h12 = h % 12 or 12
    return f'{h12}:{mi:02d} {ap}'

def is_pm(x):
    return x is not None and x >= 12 * 60

def fix():
    d = json.loads(DATA.read_text(encoding='utf-8'))
    n_fixed = 0
    report = []
    for b in d['buses']:
        st = b.get('stoppages') or []
        if not st:
            continue
        for col, rev in (('up_time', False), ('down_time', True)):
            seq = list(reversed(st)) if rev else list(st)
            parsed = [(i, s.get(col, ''), to_min(s.get(col, ''))) for i, s in enumerate(seq)]
            parsed = [(i, t, m) for (i, t, m) in parsed if m is not None]
            for k, (i, t, m) in enumerate(parsed):
                if m >= 12 * 60:  # only AM times are flip candidates
                    continue
                prev = parsed[k - 1][2] if k > 0 else None
                nxt = parsed[k + 1][2] if k < len(parsed) - 1 else None
                flip = False
                if is_pm(prev) and is_pm(nxt) and prev <= m + 720 <= nxt:
                    flip = True
                elif is_pm(prev) and nxt is None and abs((m + 720) - prev) <= 150:
                    flip = True
                elif is_pm(nxt) and prev is None and abs((m + 720) - nxt) <= 150:
                    flip = True
                if flip:
                    new = to_ampm(m + 720)
                    seq[i][col] = new
                    n_fixed += 1
                    report.append(
                        f"{b.get('reg_no') or b.get('bus_name')} [{b.get('source','')}] "
                        f"{col} @{seq[i].get('name')}: {t} -> {new}"
                    )
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'AM/PM fixes applied: {n_fixed}')
    for r in report:
        print(' ', r)
    return n_fixed

if __name__ == '__main__':
    fix()
