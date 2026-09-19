#!/usr/bin/env python3
"""Full-site audit fixes (2026-09-19). Verified findings, user-approved.

Applies (idempotently, with --write):
1. dedup_buses.py          - rule 3: same reg_no + route + departure time =
                             same physical service listed by two sources
                             (found: WB29G9687 KALOSONA Asansol->Digha
                             listed by both wbbus.in and bussathi.in).
2. data/busjatri_data.json - newline/control chars collapsed in string
                             fields (37 fields had embedded newlines, e.g.
                             Karunamoyee + newline + (Salt Lake), which
                             broke the FAQ JSON-LD on ultadanga-to-eco-space
                             and ultadanga-to-sapoorji). Runs every pipeline.
3. gen_seo_pages.py        - stale buses-from-*.html zombie pages now
                             removed by the cleanup block (it used to skip
                             them; found buses-from-barasat.html and
                             buses-from-manbazar.html lingering outside
                             the sitemap with outdated data).
3b. gen_seo_pages.py       - place pages generated for all places with
                             >= 10 originating buses instead of a hard
                             top-30 cutoff (72 pages now; homepage
                             popular-places links all resolve again).
4. css/ux-fixes.css +      - Map / WhatsApp / Share buttons: equal size and
    css/bus-page.js          solid style for the Map button (it was an
   js/bus-page.js            outline button and rendered visibly smaller),
                             plus a Bengali label for the Map button.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITE = '--write' in sys.argv


def patch(path, marker, anchor, replacement):
    p = ROOT / path
    s = p.read_text(encoding='utf-8')
    if marker in s:
        print('ok (already patched): ' + path)
        return
    if s.count(anchor) != 1:
        print('FAIL ' + path + ': anchor not found or ambiguous:')
        print(repr(anchor[:200]))
        sys.exit(1)
    s = s.replace(anchor, replacement)
    if WRITE:
        p.write_text(s, encoding='utf-8')
        print('patched ' + path)
    else:
        print('would patch ' + path)


RULE3 = '''    # rule 3: same reg_no + same route + same departure time
    # (same physical service listed by two sources, e.g. WB29G9687
    # KALOSONA Asansol->Digha from both wbbus.in and bussathi.in)
    r3 = defaultdict(list)
    for b in buses:
        reg = re.sub(r"[^A-Z0-9]", "", str(b.get("reg_no") or "").upper())
        if not reg or reg in ("NA", "-"):
            continue
        key = (
            b.get("origin", "").strip().lower(),
            b.get("destination", "").strip().lower(),
            norm_time(b.get("departure_time")),
            reg,
        )
        r3[key].append(b)
    for key, v in r3.items():
        if len(v) < 2:
            continue
        v_sorted = sorted(v, key=keeper_rank)
        for b in v_sorted[1:]:
            if b["id"] in keep_ids:
                keep_ids.discard(b["id"])
                removed.append((b, "same reg+route+time as kept copy"))

'''


def clean_data_newlines():
    import re as _re
    p = ROOT / 'data' / 'busjatri_data.json'
    d = json.loads(p.read_text(encoding='utf-8'))
    n = 0

    def tidy(v):
        return _re.sub(r"\s+", " ", v).strip()

    def walk(obj):
        nonlocal n
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    t = tidy(v)
                    if t != v:
                        n += 1
                    obj[k] = t
                else:
                    walk(v)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                if isinstance(v, str):
                    t = tidy(v)
                    if t != v:
                        n += 1
                    obj[i] = t
                else:
                    walk(v)

    walk(d.get('buses', []))
    if n:
        if WRITE:
            p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
            print('cleaned %d fields with embedded whitespace (data)' % n)
        else:
            print('would clean %d fields with embedded whitespace (data)' % n)
    else:
        print('ok (data already clean: no embedded newlines/tabs)')


def main():
    # 1. dedup rule 3
    patch(
        'scripts/dedup_buses.py',
        'same reg+route+time as kept copy',
        '    # rule 2: untimed copy shadowed by a timed copy (same route+name,',
        RULE3 + '    # rule 2: untimed copy shadowed by a timed copy (same route+name,',
    )

    # 2. data newline cleanup (runs every time; idempotent)
    clean_data_newlines()

    # 3. gen_seo_pages: remove stale buses-from pages in the cleanup block
    old_line = '    if fn == "index.html" or fn.startswith("buses-from-") or fn.endswith("-buses.html"):\n        continue'
    new_lines = (
        '    if fn == "index.html" or fn.endswith("-buses.html"):\n'
        '        continue\n'
        '    if fn.startswith("buses-from-"):\n'
        '        if fn not in written:\n'
        '            os.remove(p)\n'
        '            _removed.append(fn)\n'
        '        continue'
    )
    patch('scripts/gen_seo_pages.py', 'if fn not in written:', old_line, new_lines)

    # 3b. gen_seo_pages: place pages for all places with >= 10 originating
    # buses instead of a hard top-30 cutoff (homepage "popular places" links
    # point at place pages; barasat and manbazar fell just outside the old
    # top-30 and their links 404'd after the zombie cleanup above).
    patch(
        'scripts/gen_seo_pages.py',
        'if len(buses_) >= 10',
        'top_places = sorted(\n    place_buses,\n    key=lambda place: -len(place_buses[place]),\n)[:30]',
        'top_places = sorted(\n'
        '    (\n'
        '        place\n'
        '        for place, buses_ in place_buses.items()\n'
        '        if len(buses_) >= 10\n'
        '    ),\n'
        '    key=lambda place: -len(place_buses[place]),\n'
        ')',
    )

    # 4a. ux-fixes.css: Map button solid + same size as WhatsApp/Share
    patch(
        'css/ux-fixes.css',
        '.wa-row .map-btn{background:var(--amber)',
        '.wa-row .map-btn svg,.wa-row .wa-btn svg,.wa-row .share-x-btn svg{width:14px;height:14px}',
        '.wa-row .map-btn svg,.wa-row .wa-btn svg,.wa-row .share-x-btn svg{width:14px;height:14px}\n'
        '/* Map button: solid amber + same size as WhatsApp/Share (audit 2026-09-19) */\n'
        '.wa-row .map-btn{background:var(--amber);color:#fff;border:1.5px solid var(--amber)}\n'
        '.wa-row .map-btn:hover{background:#a06a1a;border-color:#a06a1a;color:#fff}',
    )

    # 4b. bus-page.css: same solid treatment outside .wa-row too
    patch(
        'css/bus-page.css',
        'background:var(--amber);color:#fff;border:1.5px solid var(--amber)',
        '.map-btn{flex:1;min-width:150px;display:inline-flex;align-items:center;justify-content:center;gap:8px;border:1.5px solid var(--amber);color:var(--amber-ink);border-radius:11px;padding:11px 16px;font-weight:700;font-size:13.5px;text-decoration:none;transition:.15s}',
        '.map-btn{flex:1;min-width:150px;display:inline-flex;align-items:center;justify-content:center;gap:8px;background:var(--amber);color:#fff;border:1.5px solid var(--amber);border-radius:11px;padding:11px 16px;font-weight:700;font-size:13.5px;text-decoration:none;transition:.15s}',
    )

    # 4c. bus-page.js: Bengali label for the Map button (language toggle)
    anchor = "' + icon('map') + ' <span class=\"label-en\">Route on Google Maps</span></a>'"
    repl = "' + icon('map') + ' <span class=\"label-en\">Route on Google Maps</span><span class=\"label-bn\">গুগল ম্যাপে রুট দেখুন</span></a>'"
    patch('js/bus-page.js', 'গুগল ম্যাপে রুট দেখুন', anchor, repl)


if __name__ == '__main__':
    main()
