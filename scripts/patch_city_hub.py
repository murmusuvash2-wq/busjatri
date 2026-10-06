#!/usr/bin/env python3
"""Hub page: remove the long private-routes list AND the CSTC "Official schedule
data / Kolkata CSTC city bus timetable" panel(s).

Kolkata city hub keeps: hero, search (results on search), Popular Routes,
"Which bus goes where?". Removes: the 254-row private list, every
<section class="cstc-panel"> block (incl. the "Official schedule data" one and
the 6 duplicates) and the leftover splice marker. Idempotent.

Usage: python3 scripts/patch_city_hub.py
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUB = os.path.join(ROOT, "kolkata-city-bus-timetable.html")


def main():
    if not os.path.exists(HUB):
        print("hub not found:", HUB); return
    h = open(HUB, encoding="utf-8").read()
    orig = len(h)

    # 1. remove the private-routes-section block (254-row list)
    h2 = re.sub(r'<section class="seo-section private-routes-section"[^>]*>.*?</section>\s*',
                '', h, count=1, flags=re.S)
    removed_priv = len(h) - len(h2)
    h = h2

    # 2. remove EVERY cstc-panel (the "Official schedule data / Kolkata CSTC city
    #    bus timetable" block + all duplicates)
    panels = list(re.finditer(r'<section class="cstc-panel".*?</section>', h, re.S))
    for m in reversed(panels):
        h = h[:m.start()] + h[m.end():]
    removed_panels = len(panels)

    # 3. drop the leftover splice marker
    h = h.replace('<!-- cstc-timetable-v2 -->', '')

    if len(h) != orig:
        open(HUB, "w", encoding="utf-8").write(h)
    print(f"hub: {orig} -> {len(h)} bytes | private-section removed: {removed_priv>0} "
          f"({removed_priv} B) | cstc-panels removed: {removed_panels}")


if __name__ == "__main__":
    main()
