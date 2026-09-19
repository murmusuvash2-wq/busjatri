#!/usr/bin/env python3
"""Fix AM/PM typos in stoppage times (the source sites have them).

Two rules:

1. AM -> PM (original): an AM time whose 12-hour shift up fits cleanly
   with its PM neighbours in journey order. Example: bussathi.in shows a
   Chhatna return time of "2:00 AM" between Kharbona 1:40 PM and Bankura
   2:15 PM - obviously meant to be 2:00 PM.

2. PM -> AM runs (added 2026-09-19): a RUN of consecutive PM times whose
   12-hour shift down makes the whole journey sequence cleanly monotonic,
   while the stored sequence breaks monotonicity. Example: BHARAT LAXMI
   (WB67C2286) Manihara 9:00 PM + Jorehira 9:30 PM followed by Jhantipahari
   10:00 AM, while the header itself says departure 9:00 AM - the stops
   were meant to be 9:00 AM / 9:30 AM. Found on 10 buses (all bussathi.in
   source data), verified 2026-09-19.

Genuine overnight buses (depart 9 PM, arrive 5 AM) are left untouched:
their stored sequence stays monotonic-with-wrap only across midnight, and
the shift-down candidate fails the monotonic / gap checks. Example:
APARAJITA's Haldia 2:00 AM start IS flipped because 2:00 PM would mean a
19h45m return trip (vs 7h45m shifted) - but a real 9 PM -> 5 AM bus reads
as a decreasing sequence, which no PM->AM run shift can make "cleanly
monotonic" without breaking the edge-gap guard.

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

def monotonic(vals):
    return all(vals[k] <= vals[k + 1] for k in range(len(vals) - 1))

MAX_EDGE_GAP = 300  # minutes; guards against bridging unrelated trip legs


def fix_am_to_pm(d, report):
    """Original rule: an AM time between PM neighbours that fits when shifted up."""
    n_fixed = 0
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
    return n_fixed


def fix_pm_runs_to_am(d, report):
    """New rule: a run of PM times that breaks monotonicity, but reads
    cleanly as AM after a 12h shift down. Flips the whole run at once."""
    n_fixed = 0
    for b in d['buses']:
        st = b.get('stoppages') or []
        if not st:
            continue
        for col, rev in (('up_time', False), ('down_time', True)):
            for _pass in range(4):  # re-scan until stable (runs can chain)
                seq = list(reversed(st)) if rev else list(st)
                parsed = [(i, to_min(s.get(col, ''))) for i, s in enumerate(seq)]
                parsed = [(i, m) for (i, m) in parsed if m is not None]
                if len(parsed) < 3 or monotonic([m for _, m in parsed]):
                    break
                flipped = False
                vals = [m for _, m in parsed]
                k = 0
                while k < len(vals) and not flipped:
                    if vals[k] >= 12 * 60:
                        j = k
                        while j + 1 < len(vals) and vals[j + 1] >= 12 * 60:
                            j += 1
                        run = vals[k:j + 1]
                        shifted = [v - 720 for v in run]
                        prev = vals[k - 1] if k > 0 else None
                        nxt = vals[j + 1] if j + 1 < len(vals) else None
                        cand = (vals[:k] + shifted + vals[j + 1:])
                        gaps_ok = True
                        if prev is not None and shifted[0] - prev > MAX_EDGE_GAP:
                            gaps_ok = False
                        if nxt is not None and nxt - shifted[-1] > MAX_EDGE_GAP:
                            gaps_ok = False
                        if monotonic(cand) and gaps_ok:
                            for idx in range(k, j + 1):
                                i, m = parsed[idx]
                                old = seq[i].get(col)
                                new = to_ampm(m - 720)
                                seq[i][col] = new
                                n_fixed += 1
                                report.append(
                                    f"{b.get('reg_no') or b.get('bus_name')} [{b.get('source','')}] "
                                    f"{col} @{seq[i].get('name')}: {old} -> {new}"
                                )
                            flipped = True
                        k = j + 1
                    else:
                        k += 1
                if not flipped:
                    break
    return n_fixed


def fix():
    d = json.loads(DATA.read_text(encoding='utf-8'))
    report = []
    n1 = fix_am_to_pm(d, report)
    n2 = fix_pm_runs_to_am(d, report)
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'AM->PM fixes applied: {n1}')
    print(f'PM->AM run fixes applied: {n2}')
    for r in report:
        print(' ', r)
    return n1 + n2


if __name__ == '__main__':
    fix()
