#!/usr/bin/env python3
"""Regenerate legacy orphan route pages in the v2 design.

Orphan = a bus-time-table/*-to-*.html file whose (origin, destination)
pair is no longer in route_meta (its direct buses left the current data).
Their direct list is empty, but through-services (homepage search parity)
and alt-route sections still apply, so nearly all of them stay useful.

Discovers the pair names from each legacy page's <title>, then re-renders
it with generate_route_page_v2. Run from the repo root:

    python3 scripts/gen_orphans.py [--dry]
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_route_v2 as v2

g = v2.g


def main():
    dry = "--dry" in sys.argv
    expected = {f"{g.slug(o)}-to-{g.slug(d)}.html" for (o, d) in g.route_meta}
    pairs = []
    for fname in sorted(os.listdir(g.OUT)):
        if not fname.endswith(".html") or "-to-" not in fname or "-via-" in fname:
            continue
        if fname in expected:
            continue
        try:
            with open(os.path.join(g.OUT, fname), "r", encoding="utf-8", errors="ignore") as fh:
                head = fh.read(4000)
        except OSError:
            continue
        m = re.search(r"<title>(.*?) to (.*?) Bus Time Table", head)
        if not m or not m.group(1).strip() or not m.group(2).strip():
            print(f"SKIP (unparseable title): {fname}")
            continue
        pairs.append((m.group(1).strip(), m.group(2).strip()))

    print(f"loaded {len(g.BUSES)} buses, {len(g.route_meta)} route pairs")
    print(f"discovered {len(pairs)} orphan route pages")

    alt_index = v2.AltIndex(g.BUSES)
    n_alt = 0
    for o, d in pairs:
        filename, page = v2.generate_route_page_v2(o, d, [], alt_index)
        has_alt = "alt-card" in page
        n_alt += 1 if has_alt else 0
        print(f"{filename}: alt={'Y' if has_alt else 'N'} faq={page.count('<details')}")
        if not dry:
            with open(os.path.join(g.OUT, filename), "w", encoding="utf-8") as fh:
                fh.write(page)

    print(f"\ndone: {len(pairs)} orphan pages, {n_alt} with alternative-route section")


if __name__ == "__main__":
    main()
