#!/usr/bin/env python3
"""Clean junk bus names: 'ABHISHEK Registration WB55F6221 Type — Op' -> 'ABHISHEK'.

Scraped names carried a ' Registration <regno> Type <trailing>' suffix, often
truncated at 40 chars. Extract the real operator name, move a genuine
registration into reg_no when empty, and drop junk 'govtb*' placeholder regs.
Idempotent; run with --write to modify data.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "busjatri_data.json"

JUNK_RE = re.compile(r"^(?P<name>.+?)\s+Registration\s+(?P<reg>\S+).*$", re.S)
GOVT_JUNK = re.compile(r"^govtb?\d+$", re.I)


def clean_name(raw):
    m = JUNK_RE.match(raw)
    if not m:
        return None
    name = m.group("name").strip()
    reg = m.group("reg").strip()
    if not name:
        return None
    if GOVT_JUNK.match(reg):
        reg = ""
    return name, reg


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    buses = d["buses"]
    changed = 0
    for b in buses:
        raw = b.get("bus_name") or ""
        if " Registration " not in raw:
            continue
        res = clean_name(raw)
        if not res:
            continue
        name, reg = res
        b["bus_name"] = name
        if reg and not (b.get("reg_no") or "").strip():
            b["reg_no"] = reg
        changed += 1

    print(f"junk names cleaned: {changed}")
    if changed and "--write" in sys.argv:
        DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("written")
    # report leftovers
    left = [b["bus_name"] for b in buses if " Registration " in (b.get("bus_name") or "")]
    print(f"leftover junk: {len(left)}")
    for n in left[:5]:
        print("  -", n)


if __name__ == "__main__":
    main()
