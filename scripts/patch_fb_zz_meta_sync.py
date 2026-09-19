#!/usr/bin/env python3
"""meta.total_buses drift fix (found 2026-09-19).

busjatri_data.json meta.total_buses said 4,018 while the bus list had
4,009 - the count is only refreshed by full data rebuilds, so the
add-community and dedup steps let it drift. finalize_pages.py copies it
into page copy ("X listed bus services"), so the site was over-claiming.

This patches (idempotently, with --write):
1. add_community_buses.py - sync meta.total_buses when writing the data file.
2. dedup_buses.py         - same sync after removing duplicates.
3. gen_daily_blog.py      - remove the 12:00 AM -> noon workaround (the
                           NBSTC entry is now corrected at data level via
                           community enrich, and real midnight buses exist).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITE = "--write" in sys.argv


def patch(path, marker, anchor, replacement):
    p = ROOT / path
    s = p.read_text(encoding="utf-8")
    if marker in s:
        print(f"ok (already patched): {path}")
        return
    if s.count(anchor) != 1:
        print(f"FAIL {path}: anchor not found or ambiguous:")
        print(anchor[:160])
        sys.exit(1)
    s = s.replace(anchor, replacement)
    if WRITE:
        p.write_text(s, encoding="utf-8")
        print(f"patched {path}")
    else:
        print(f"would patch {path}")


def main():
    # 1. add_community_buses.py - sync inside the write block
    patch(
        "scripts/add_community_buses.py",
        'data.setdefault("meta", {})["total_buses"] = len(buses)',
        '        data.setdefault("meta", {})["last_updated"] = "2026-09-18"',
        '        data.setdefault("meta", {})["total_buses"] = len(buses)\n'
        '        data.setdefault("meta", {})["last_updated"] = "2026-09-18"',
    )
    # 2. dedup_buses.py - sync right before the data write
    patch(
        "scripts/dedup_buses.py",
        'd.setdefault("meta", {})["total_buses"] = len(d["buses"])',
        '    path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")',
        '    d.setdefault("meta", {})["total_buses"] = len(d["buses"])\n'
        '    path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")',
    )
    # 3. gen_daily_blog.py - remove the 12:00 AM -> noon workaround; the
    # NBSTC entry is now corrected at data level (community enrich), and
    # real midnight buses exist (e.g. Haldia-Durgapur departs 12:05 AM).
    quirk = ('    # NBSTC source data quirk: one bus shows "12:00 AM" sandwiched between\n'
             '    # 11:40 AM and 12:20 PM \u2014 it is noon, not midnight.\n'
             '    if h == 12 and ap == "AM":\n'
             '        return 720\n')
    p = ROOT / "scripts/gen_daily_blog.py"
    s = p.read_text(encoding="utf-8")
    if quirk in s:
        if WRITE:
            p.write_text(s.replace(quirk, ""), encoding="utf-8")
            print("patched scripts/gen_daily_blog.py (noon workaround removed)")
        else:
            print("would patch scripts/gen_daily_blog.py")
    else:
        print("ok (already patched): scripts/gen_daily_blog.py")


if __name__ == "__main__":
    main()
