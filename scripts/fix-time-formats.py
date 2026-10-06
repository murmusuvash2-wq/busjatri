#!/usr/bin/env python3
"""Normalize time strings in BusJatri data files to the canonical `h:mm AM/PM`.

Idempotent. Run from the repository root:

    python3 scripts/fix-time-formats.py

Rewrites these files in place (only when something changes):
  data/busjatri_data.json
  data/bus-details.json
  data/app-index.json

Only the *representation* of a time changes (e.g. "17:00" -> "5:00 PM",
"12:00 Noon" -> "12:00 PM"). No time is invented and no empty value is filled.
"""
import json, re, os, sys, collections

TIME_FIELDS = {"departure_time", "arrival_time", "up_time", "down_time"}
FILES = ["data/busjatri_data.json", "data/bus-details.json", "data/app-index.json"]


def normalize(value):
    """Return (new_value, changed, tag)."""
    if not isinstance(value, str):
        return value, False, None
    s = value.strip()
    if not s:
        return value, False, None

    # already canonical: h:mm AM/PM
    m = re.fullmatch(r"(\d{1,2}):(\d{2})\s*(AM|PM)", s, flags=re.I)
    if m:
        h = int(m.group(1))
        if 1 <= h <= 12:
            new = f"{h}:{m.group(2)} {m.group(3).upper()}"
            return (new, new != value, None if new == value else "canonicalised")

    # bare 24-hour clock: HH:MM
    if re.fullmatch(r"\d{1,2}:\d{2}", s):
        h, mi = map(int, s.split(":"))
        if 0 <= h <= 23 and 0 <= mi <= 59:
            ap = "AM" if h < 12 else "PM"
            return (f"{h % 12 or 12}:{mi:02d} {ap}", True, "24h->12h")

    # "12:00 Noon"
    if re.fullmatch(r"12:00\s*Noon", s, flags=re.I):
        return ("12:00 PM", True, "noon")

    # trailing qualifier, e.g. "8:20 AM (2nd day)"
    m = re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM)\b.*$", s, flags=re.I)
    if m:
        return (f"{int(m.group(1))}:{m.group(2)} {m.group(3).upper()}", True, "strip-qualifier")

    return value, False, None


def walk(node, stats):
    if isinstance(node, dict):
        for key, val in node.items():
            if key in TIME_FIELDS and isinstance(val, str):
                new, changed, tag = normalize(val)
                if changed:
                    stats[tag] += 1
                    node[key] = new
            else:
                walk(val, stats)
    elif isinstance(node, list):
        for item in node:
            walk(item, stats)


def main():
    total = 0
    for path in FILES:
        if not os.path.exists(path):
            print(f"skip (missing): {path}")
            continue
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        stats = collections.Counter()
        walk(data, stats)
        n = sum(stats.values())
        if n:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print(f"{path}: {n} time value(s) normalised {dict(stats)}")
        total += n
    print(f"done. {total} value(s) changed.")


if __name__ == "__main__":
    sys.exit(main())
