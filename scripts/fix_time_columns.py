#!/usr/bin/env python3
# Time-column fix for BusJatri data (2026-09-24 audit follow-up). v2 - guarded.
#
# Problem: in many records a time that belongs to the RETURN (down) column
# was recorded in the OUTBOUND (up) column, and vice versa. This makes
# timetables run backwards (e.g. PALLY DUTH's Karunamoyee "3:45 PM" in the
# outbound column while arrival is 10:30 AM).
#
# Guarded repair rules (no values are invented - existing times are only
# moved between columns or cleared when duplicated):
#
# R1 up-backslide: stop's up_time is EARLIER than the last kept up time
#    (within 6h, so genuine overnight chains are untouched).
#      - down_time already set  -> clear up_time (contradictory duplicate)
#      - down_time empty AND the value fits between the neighbouring down
#        times (or the stop is the chain's last timed stop) -> move it to
#        down_time
#      - otherwise -> leave, report for review
# R2 down-backslide (mirror): down_time LATER than the previous down time
#    (within 6h). Only acted on when the value is the single odd one
#    (removing it restores the monotonic run):
#      - up_time empty AND fits the up sequence -> move to up_time
#      - up_time already set -> clear down_time
#      - otherwise -> leave, report for review
#    (a whole increasing run is NEVER touched - those look like second
#    daily trips, e.g. BABA BIHARINATH)
# R3 arrival-mismatch: the last timed stop's up_time is LATER than the
#    bus's arrival_time (within 6h) and fits the down sequence -> move to
#    down_time if empty, else clear up_time.
#
# "Return time before outbound at the same stop" (38 buses) is NOT touched:
# legitimate overnight round trips (out in the morning, return next morning).
#
# Writes a change report to data-time-fix-report.csv.
# Backslash-free source. Idempotent: re-running makes no changes.

import csv
import json

SRC = 'data/busjatri_data.json'
REPORT = 'data-time-fix-report.csv'


def tmin(s):
    if not s or ':' not in str(s):
        return None
    try:
        hh, rest = str(s).strip().split(':', 1)
        ru = rest.upper()
        ap = ''
        if 'AM' in ru:
            ap = 'AM'
        elif 'PM' in ru:
            ap = 'PM'
        rest2 = ru.replace('AM', '').replace('PM', '').strip()
        h = int(hh)
        mm = int(rest2)
    except Exception:
        return None
    if mm > 59:
        return None
    if ap:
        if h < 1 or h > 12:
            return None
        h = h % 12
        if ap == 'PM':
            h += 12
    else:
        if h > 23:
            return None
    return h * 60 + mm


def tfmt(m):
    if m is None:
        return '?'
    h = m // 60
    mm = m % 60
    ap = 'AM' if h < 12 else 'PM'
    hh = h % 12
    if hh == 0:
        hh = 12
    return '%d:%02d %s' % (hh, mm, ap)


def prev_val(arr, i):
    for j in range(i - 1, -1, -1):
        if arr[j] is not None:
            return arr[j]
    return None


def next_val(arr, i):
    for j in range(i + 1, len(arr)):
        if arr[j] is not None:
            return arr[j]
    return None


def fix_bus(b, changes, review):
    sts = b.get('stoppages') or []
    if not sts:
        return
    bid = b.get('id') or '?'
    label = (b.get('bus_name') or '?') + ' ' + (b.get('reg_no') or '')
    route = (b.get('origin') or '?') + ' -> ' + (b.get('destination') or '?')

    def log(stop, action, detail):
        changes.append([bid, label, route, stop.get('no'), stop.get('name'),
                        action, detail])

    ups = [tmin(s.get('up_time')) for s in sts]
    dns = [tmin(s.get('down_time')) for s in sts]

    # R1: up backslides
    for i, s in enumerate(sts):
        t = ups[i]
        if t is None:
            continue
        pv = prev_val(ups, i)
        if pv is None or t >= pv or (pv - t) > 360:
            continue
        # t is earlier than the previous up time - wrong column
        if (s.get('down_time') or '').strip():
            old = s.get('up_time')
            s['up_time'] = ''
            ups[i] = None
            log(s, 'cleared up_time',
                'up %s < up %s at previous stop (down already %s)' %
                (old, tfmt(pv), s.get('down_time')))
            continue
        nv = next_val(ups, i)
        last_timed = nv is None
        pd = prev_val(dns, i)
        nd = next_val(dns, i)
        fits_down = (pd is None or t <= pd) and (nd is None or t >= nd)
        if last_timed or fits_down:
            s['down_time'] = s['up_time']
            s['up_time'] = ''
            ups[i] = None
            dns[i] = t
            log(s, 'moved up_time -> down_time',
                'up %s < up %s at previous stop' % (s.get('down_time'), tfmt(pv)))
        else:
            review.append([bid, label, route, s.get('no'), s.get('name'),
                            'up %s < up %s at previous stop; does not fit down neighbours' %
                            (s.get('up_time'), tfmt(pv))])

    # R3: arrival mismatch at the last timed stop
    arr = tmin(b.get('arrival_time'))
    if arr is not None:
        idx = None
        for i, s in enumerate(sts):
            if (s.get('up_time') or '').strip():
                idx = i
        if idx is not None:
            s = sts[idx]
            t = tmin(s.get('up_time'))
            if t is not None and t > arr and (t - arr) <= 360:
                pd = prev_val(dns, idx)
                nd = next_val(dns, idx)
                fits_down = (pd is None or t <= pd) and (nd is None or t >= nd)
                if not fits_down:
                    review.append([bid, label, route, s.get('no'), s.get('name'),
                                   'last stop up %s > arrival %s but does not fit down neighbours' %
                                   (s.get('up_time'), b.get('arrival_time'))])
                elif not (s.get('down_time') or '').strip():
                    s['down_time'] = s['up_time']
                    s['up_time'] = ''
                    log(s, 'moved up_time -> down_time',
                        'last stop up %s > arrival %s' % (s.get('down_time'),
                                                          b.get('arrival_time')))
                else:
                    old = s.get('up_time')
                    s['up_time'] = ''
                    log(s, 'cleared up_time',
                        'last stop up %s > arrival %s (down already %s)' %
                        (old, b.get('arrival_time'), s.get('down_time')))

    # R2: down backslides (only the single odd value is touched)
    for i, s in enumerate(sts):
        t = dns[i]
        if t is None:
            continue
        pv = prev_val(dns, i)
        if pv is None or t <= pv or (t - pv) > 360:
            continue
        # t is later than the previous down time - wrong column candidate
        nv = next_val(dns, i)
        single_odd = nv is None or nv <= pv
        if not single_odd:
            review.append([bid, label, route, s.get('no'), s.get('name'),
                           'down %s > down %s at previous stop (increasing run - possible 2nd trip, left as-is)' %
                           (s.get('down_time'), tfmt(pv))])
            continue
        if not (s.get('up_time') or '').strip():
            pu = prev_val(ups, i)
            nu = next_val(ups, i)
            fits_up = (pu is None or t >= pu) and (nu is None or t <= nu)
            if fits_up:
                s['up_time'] = s['down_time']
                s['down_time'] = ''
                ups[i] = t
                dns[i] = None
                log(s, 'moved down_time -> up_time',
                    'down %s > down %s at previous stop' % (s.get('up_time'), tfmt(pv)))
            else:
                review.append([bid, label, route, s.get('no'), s.get('name'),
                               'down %s > down %s at previous stop; does not fit up neighbours' %
                               (s.get('down_time'), tfmt(pv))])
        else:
            old = s.get('down_time')
            s['down_time'] = ''
            dns[i] = None
            log(s, 'cleared down_time',
                'down %s > down %s at previous stop (up already %s)' %
                (old, tfmt(pv), s.get('up_time')))


def main():
    with open(SRC, encoding='utf-8') as fh:
        d = json.load(fh)
    orig = json.loads(json.dumps(d['buses']))
    changes = []
    review = []
    for _ in range(12):
        changes = []
        review = []
        for b in d['buses']:
            fix_bus(b, changes, review)
        if not changes:
            break
    # cumulative report: original vs final, stop by stop
    rows = []
    byid = {b.get('id'): b for b in orig}
    for b in d['buses']:
        ob = byid.get(b.get('id'))
        if not ob:
            continue
        osts = ob.get('stoppages') or []
        nsts = b.get('stoppages') or []
        if osts == nsts:
            continue
        label = (b.get('bus_name') or '?') + ' ' + (b.get('reg_no') or '')
        route = (b.get('origin') or '?') + ' -> ' + (b.get('destination') or '?')
        for i in range(max(len(osts), len(nsts))):
            os_ = osts[i] if i < len(osts) else {}
            ns_ = nsts[i] if i < len(nsts) else {}
            if os_.get('up_time') != ns_.get('up_time') or os_.get('down_time') != ns_.get('down_time'):
                rows.append([b.get('id'), label, route, ns_.get('no'), ns_.get('name'),
                             'up: %s -> %s' % (os_.get('up_time') or '-', ns_.get('up_time') or '-'),
                             'down: %s -> %s' % (os_.get('down_time') or '-', ns_.get('down_time') or '-')])
    with open(SRC, 'w', encoding='utf-8') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    if rows:
        with open(REPORT, 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(['bus_id', 'bus', 'route', 'stop_no', 'stop', 'up_time change', 'down_time change'])
            for row in rows:
                w.writerow(row)
            w.writerow([])
            w.writerow(['--- LEFT FOR REVIEW (not changed, possible 2nd daily trips / ambiguous) ---'])
            for row in review:
                w.writerow(row)
    print('buses changed:', len(set(r[0] for r in rows)))
    print('total stops changed:', len(rows))
    print('left for review:', len(set(r[0] for r in review)), 'buses /', len(review), 'stops')


if __name__ == '__main__':
    main()
