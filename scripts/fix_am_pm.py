#!/usr/bin/env python3
"""Fix AM/PM typos in stoppage times (both directions), DP-based repair.

The old version only flipped AM->PM and had a risky rule that turned a
correct first stop into PM when the *next* stop was a PM typo (e.g.
BHARAT LAXMI WB67C2286: source Jorehira 9:30 PM typo made it flip a
correct Manihara 9:00 AM into 9:00 PM).

New approach:
- A stop sequence is flagged when any two consecutive timed stops go
  backwards (next < prev) or jump more than MAX_GAP (8h) forward.
- For each flagged bus/column we search for the minimum number of
  12-hour flips (AM<->PM) that makes the timed subsequence monotonic
  non-decreasing with all gaps <= MAX_GAP.
- Only repairs needing <= MAX_FLIPS (2) flips are applied; anything
  harder is left untouched and logged for manual review.
- Genuine overnight buses are safe: their sequences are already
  monotonic with sane gaps, so they are never flagged.
Run with no arguments; edits data/busjatri_data.json in place.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'busjatri_data.json'

MAX_GAP = 8 * 60      # max minutes between consecutive timed stops
MAX_FLIPS = 2         # only auto-apply simple repairs

TIME_RE = re.compile(r'^(\d{1,2}):(\d{2})\s*(AM|PM)$', re.I)

def to_min(t):
    m = TIME_RE.match((t or '').strip())
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
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

def is_broken(seq):
    """seq: [(stop_dict, minutes_or_None)] in journey order.
    Only ADJACENT stops (both timed) are compared - we never infer a
    problem across a stop with a missing time, because a long stretch
    between two timed stops with untimed stops between them is common
    on sparse rural routes and is usually genuine."""
    for i in range(len(seq) - 1):
        a, b = seq[i][1], seq[i + 1][1]
        if a is None or b is None:
            continue
        if b < a or b - a > MAX_GAP:
            return True
    return False

def repair(seq):
    """seq: [(stop_dict, minutes_or_None)] in journey order.
    Returns (n_flips, {stop_index: new_minutes}) or (INF, None)."""
    idxs = [i for i, (_, m) in enumerate(seq) if m is not None]
    cands = []
    for i, (_, m) in enumerate(seq):
        c = [] if m is None else sorted({m - 720, m, m + 720} & set(range(0, 24 * 60)))
        cands.append(c)
    INF = 10 ** 9

    def rec(k, prev_m):
        if k == len(idxs):
            return 0, {}
        i = idxs[k]
        best = (INF, None)
        for c in cands[i]:
            if prev_m is not None and (c < prev_m or c - prev_m > MAX_GAP):
                continue
            sub, chosen = rec(k + 1, c)
            if sub == INF:
                continue
            flips = sub + (0 if c == seq[i][1] else 1)
            if flips < best[0]:
                merged = {i: c}
                if chosen:
                    merged.update(chosen)
                best = (flips, merged)
        return best

    return rec(0, None)

def fix():
    d = json.loads(DATA.read_text(encoding='utf-8'))
    n_fixed = 0
    report = []
    manual = []
    for b in d['buses']:
        st = b.get('stoppages') or []
        if not st:
            continue
        # up trip: stops in listed order; down trip: reverse
        for col, seqst in (('up_time', st), ('down_time', list(reversed(st)))):
            seq = [(s, to_min(s.get(col))) for s in seqst]
            if not is_broken(seq):
                continue
            flips, chosen = repair(seq)
            if flips > MAX_FLIPS:
                manual.append(f"{b.get('reg_no') or b.get('bus_name')} [{col}]: "
                              f"{flips} flips needed - left for manual review")
                continue
            for i, new_m in sorted(chosen.items()):
                s = seq[i][0]
                if seq[i][1] != new_m:
                    old = s[col]
                    s[col] = to_ampm(new_m)
                    n_fixed += 1
                    report.append(
                        f"{b.get('reg_no') or b.get('bus_name')} [{col}] "
                        f"@{s.get('name')}: {old} -> {s[col]}"
                    )
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'AM/PM fixes applied: {n_fixed}')
    for r in report:
        print(' ', r)
    if manual:
        print(f'Left for manual review: {len(manual)}')
        for r in manual:
            print('  ?', r)
    return n_fixed

if __name__ == '__main__':
    fix()
