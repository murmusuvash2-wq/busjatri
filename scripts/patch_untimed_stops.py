#!/usr/bin/env python3
"""Show untimed buses in stop searches + stop pages (BusJatri).

Problem: a bus whose stop has no up/down time was COMPLETELY HIDDEN when the
user searched that stop (Stoppage field) or opened the stop page — even though
the bus actually halts there. ~46,500 hidden (bus, stop) pairs / ~2,800 places.

Fix: such buses now appear with a "Time not listed" pill instead of vanishing.

Patches js/ux-fixes.js:
 1. stop-only search: push an untimed row when both directions lack a time
 2. renderSearch row: "Time not listed" pill when depMin is null
 3. stop page (renderStop) allDeps: push untimed buses too
 4. stop page sort: null-safe (untimed sort last)
 5. stop page dd/near: null-safe
 6. stop page pill: "Time not listed" when t is null
Also bumps the js/ux-fixes.js cache-bust version in index.html.

Idempotent; use --write to apply.
"""
import argparse

UX = 'js/ux-fixes.js'
IDX = 'index.html'
NEW_V = 'untimed20260920a'
MDOT = '\u00b7'          # ·
BN_NOT_LISTED = '<span class="label-en">Time not listed</span><span class="label-bn">\u09b8\u09ae\u09df \u099c\u09be\u09a8\u09be \u09a8\u09c7\u0987</span>'

R = []


def rep(old, new):
    R.append((old, new))


# 1) stop-only search: also push an untimed row
rep(
    "          if (tU != null) rows.push({ b: b, fwd: true, depMin: tU });\n"
    "          if (tD != null) rows.push({ b: b, fwd: false, depMin: tD });\n",
    "          if (tU != null) rows.push({ b: b, fwd: true, depMin: tU });\n"
    "          if (tD != null) rows.push({ b: b, fwd: false, depMin: tD });\n"
    "          if (tU == null && tD == null) rows.push({ b: b, fwd: true, depMin: null });\n",
)

# 2) renderSearch row: pill for untimed rows
rep(
    "          var tPill = r.depMin != null ? '<span class=\"time-pill\">' + icon('clock') + ' ' + fmtTime(r.depMin) + (isNear ? ' " + MDOT + " <b style=\"color:var(--amber)\">' + countdownText(rel(r.depMin)) + '</b>' : '') + '</span>' : '';",
    "          var tPill = r.depMin != null ? '<span class=\"time-pill\">' + icon('clock') + ' ' + fmtTime(r.depMin) + (isNear ? ' " + MDOT + " <b style=\"color:var(--amber)\">' + countdownText(rel(r.depMin)) + '</b>' : '') + '</span>' : '<span class=\"time-pill\" style=\"opacity:.7\">' + icon('clock') + ' " + BN_NOT_LISTED + "</span>';",
)

# 3) stop page allDeps: push untimed too
rep(
    "            if (tU != null) allDeps.push({ b: b, t: tU, fwd: true });\n"
    "            if (tD != null) allDeps.push({ b: b, t: tD, fwd: false });\n",
    "            if (tU != null) allDeps.push({ b: b, t: tU, fwd: true });\n"
    "            if (tD != null) allDeps.push({ b: b, t: tD, fwd: false });\n"
    "            if (tU == null && tD == null) allDeps.push({ b: b, t: null, fwd: true });\n",
)

# 4) stop page sort: null-safe
rep(
    "          allDeps.sort(function (x, y) {\n"
    "            var ax = x.t < nowM ? x.t + 1440 : x.t;\n"
    "            var ay = y.t < nowM ? y.t + 1440 : y.t;\n"
    "            return ax - ay;\n"
    "          });",
    "          allDeps.sort(function (x, y) {\n"
    "            var ax = x.t == null ? Infinity : (x.t < nowM ? x.t + 1440 : x.t);\n"
    "            var ay = y.t == null ? Infinity : (y.t < nowM ? y.t + 1440 : y.t);\n"
    "            return ax - ay;\n"
    "          });",
)

# 5) stop page dd/near: null-safe
rep(
    "            var dd = n.t - nowM; if (dd < 0) dd += 1440;\n"
    "            var near = dd <= 180 ? ' " + MDOT + " <b style=\"color:var(--amber)\">' + countdownText(dd) + '</b>' : '';",
    "            var dd = n.t == null ? null : n.t - nowM; if (dd != null && dd < 0) dd += 1440;\n"
    "            var near = dd != null && dd <= 180 ? ' " + MDOT + " <b style=\"color:var(--amber)\">' + countdownText(dd) + '</b>' : '';",
)

# 6) stop page pill: "Time not listed"
rep(
    "              '<span class=\"time-pill\">' + icon('clock') + ' ' + fmtTime(n.t) + near + '</span></div>';",
    "              '<span class=\"time-pill\">' + icon('clock') + ' ' + (n.t == null ? '" + BN_NOT_LISTED + "' : fmtTime(n.t)) + near + '</span></div>';",
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    s = open(UX, encoding='utf-8').read()
    if 'Time not listed' in s:
        print('ux-fixes.js already patched — nothing to do.')
        return

    n_applied = 0
    for old, new in R:
        if s.count(old) != 1:
            raise SystemExit(f'ABORT: expected exactly 1 match, got {s.count(old)} for:\n{old[:80]}...')
        s = s.replace(old, new)
        n_applied += 1
    print(f'applied {n_applied}/{len(R)} replacements to {UX}')

    # bump cache-bust for ux-fixes.js in index.html
    idx = open(IDX, encoding='utf-8').read()
    if 'js/ux-fixes.js?v=' + NEW_V not in idx:
        old_ref = 'js/ux-fixes.js?v=mob20260918b'
        if old_ref in idx:
            idx = idx.replace(old_ref, 'js/ux-fixes.js?v=' + NEW_V)
            print(f'bumped index.html ux-fixes ref -> v={NEW_V}')
        else:
            print('WARN: ux-fixes.js ref not found in index.html (version string changed?)')
    if args.write:
        open(UX, 'w', encoding='utf-8').write(s)
        open(IDX, 'w', encoding='utf-8').write(idx)
        print('WROTE', UX, 'and', IDX)
    else:
        print('(dry run - use --write)')


if __name__ == '__main__':
    main()
