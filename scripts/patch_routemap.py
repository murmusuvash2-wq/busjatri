#!/usr/bin/env python3
"""One-time patch: route map now always shows origin and destination.

The Route Map previously showed only the FIRST 10 stops of the most common
stop sequence, so long routes never displayed the destination (e.g.
Bardhaman -> Bandwan ended at Bankura). Now shows first 8 stops, a gap
marker, and the last 2 stops. Also adds the .rm-gap style to css/seo.css.

Idempotent: safe to run multiple times.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch(path, replacements):
    p = os.path.join(ROOT, path)
    with open(p, encoding="utf-8") as fh:
        s = fh.read()
    if replacements[0][1] in s:
        print(path + ": already patched")
        return
    for old, new in replacements:
        if old not in s:
            raise SystemExit("ABORT: expected text not found in " + path + ": " + old[:60])
        s = s.replace(old, new, 1)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(s)
    print(path + ": patched")


GEN = "scripts/gen_seo_pages.py"

GAP = '<div class="rm-gap" aria-hidden="true">\u22ef</div>'

patch(GEN, [
    ("    sequence = list(sequence[:10])", "    sequence = list(sequence)"),
    ('        return ""\n    dots = ""\n    for i, stop in enumerate(sequence):',
     '        return ""\n'
     "    # Show origin + destination always: first 8 stops, gap marker, last 2 stops\n"
     "    if len(sequence) > 10:\n"
     "        shown = sequence[:8] + [None] + sequence[-2:]\n"
     "    else:\n"
     "        shown = list(sequence)\n"
     '    dots = ""\n'
     "    for i, stop in enumerate(shown):"),
    ('        end_cls = " end" if i in (0, len(sequence)-1) else ""',
     "        if stop is None:\n"
     "            dots += '" + GAP + "'\n"
     "            continue\n"
     '        end_cls = " end" if i in (0, len(shown)-1) else ""'),
    ("if len(sequence) == 10 else", "if len(sequence) > 10 else"),
])

patch("css/seo.css", [
    (".rm-stop.end .rm-dot{",
     ".rm-gap{width:58px;display:flex;justify-content:center;margin-top:7px;"
     "color:var(--ink-dim);font-size:13px;font-weight:700;letter-spacing:1px}\n"
     ".rm-stop.end .rm-dot{"),
])

print("route-map patch complete")
