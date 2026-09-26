# P1 SEO: top route pages content depth (user-approved 2026-09-26).
# Edits gen_route_v2.py:
#  1. data-rich <title> (bus count + first bus time)
#  2. unique intro paragraph under the hero (4 EN + 4 BN variants, chosen by
#     a stable hash of the route; facts 100% from data; SBSTC sentence appended)
#  3. SBSTC chip in the hero stat-chips
#  4. "More Buses to {destination}" internal-link section
# Regenerate ONLY the top GSC pages (--routes), then add_ga4.
# All Bengali embedded as \u escapes (ASCII-safe).

GEN = 'scripts/gen_route_v2.py'

s = open(GEN, encoding='utf-8').read()
if 'P1 SEO' in s:
    print('already applied')
    raise SystemExit(0)

def sub1(old, new):
    global s
    assert s.count(old) == 1, 'anchor not unique: ' + old[:60]
    s = s.replace(old, new, 1)

INS = r'''    # ---- P1 SEO (2026-09-26): unique intro paragraph, SBSTC chip, to-destination links ----
    _sb = 0
    for b in faq_buses:
        _bt = str(b.get("bus_type", "")).upper()
        _nm = str(b.get("bus_name", "")).upper()
        _op = str(b.get("operator", "")).upper()
        if "SBSTC" in _bt or _nm.startswith("SBSTC") or _op == "SBSTC":
            _sb += 1
    _via = ""
    _vc = {}
    for b in buses:
        _sq = g.bus_stops(b)
        for _st in (_sq[1:-1] if len(_sq) > 2 else _sq):
            if _st and _st != origin and _st != destination:
                _vc[_st] = _vc.get(_st, 0) + 1
    if _vc:
        _via = sorted(_vc.items(), key=lambda kv: -kv[1])[0][0]
    if _sb:
        chips += f'<span class="schip">\U0001F3DB {L(str(_sb) + " SBSTC", bn_num(_sb) + " SBSTC")}</span>'
    intro_html = ""
    if stats["first"] is not None and count > 1:
        _v = sum(ord(c) for c in origin + ">" + destination) % 4
        _EN = [
            "{count} bus services run from {origin} to {destination} - the first departs at {first} and the last at {last}. Several major stops fall along the way. Schedules can change, so confirm at the bus counter before travelling.",
            "BusJatri lists {count} bus services on the {origin} to {destination} route - first departure {first}, last {last}. {via} is one of the major stops on the way. Verify timings before you travel.",
            "A total of {count} buses serve the {origin} to {destination} route. The day's first bus leaves at {first} and the last one at {last}. Schedules can change without notice - check at the counter before you set out.",
            "You can catch {count} bus services from {origin} to {destination}. The first bus is at {first} and the last at {last}. Every bus's times and stoppages are listed on this page.",
        ]
        _BN = [
            (
            "{n}\u099f\u09bf \u09ac\u09be\u09b8 \u09b8\u09be\u09b0\u09cd\u09ad\u09bf\u09b8 {o} \u09a5\u09c7\u0995\u09c7 {d} \u09aa\u09b0\u09cd\u09af\u09a8\u09cd\u09a4 \u099a\u09b2\u09c7 \u2014 \u09aa\u09cd\u09b0\u09a5\u09ae \u09ac\u09be\u09b8 \u099b\u09be\u09a1\u09bc\u09c7 {f}, \u09b6\u09c7\u09b7 \u09ac\u09be\u09b8 \u099b\u09be\u09a1\u09bc\u09c7 {l}\u0964 \u09af\u09be\u09a4\u09cd\u09b0\u09be\u09b0 \u09aa\u09a5\u09c7 \u09ac\u09c7\u09b6"
            " \u0995\u09af\u09bc\u09c7\u0995\u099f\u09bf \u0997\u09c1\u09b0\u09c1\u09a4\u09cd\u09ac\u09aa\u09c2\u09b0\u09cd\u09a3 \u09b8\u09cd\u099f\u09aa \u09aa\u09a1\u09bc\u09c7\u0964 \u09b8\u09ae\u09af\u09bc \u09ac\u09a6\u09b2\u09be\u09a4\u09c7 \u09aa\u09be\u09b0\u09c7, \u09a4\u09be\u0987 \u09af\u09be\u09a4\u09cd\u09b0\u09be\u09b0 \u0986\u0997\u09c7 \u0995\u09be\u0989\u09a8\u09cd\u099f\u09be\u09b0\u09c7 \u09a8\u09bf\u09b6\u09cd\u099a\u09bf\u09a4 \u0995\u09b0\u09c7 \u09a8\u09bf\u09a8\u0964"),
            (
            "BusJatri-\u09a4\u09c7 {o} \u2192 {d} \u09b0\u09c1\u099f\u09c7 {n}\u099f\u09bf \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u09a4\u09be\u09b2\u09bf\u0995\u09be\u09ad\u09c1\u0995\u09cd\u09a4 \u2014 \u09aa\u09cd\u09b0\u09a5\u09ae \u099b\u09be\u09a1\u09bc\u09c7 {f}, \u09b6\u09c7\u09b7 \u099b\u09be\u09a1\u09bc\u09c7 {l}\u0964 \u09aa\u09a5\u09c7\u09b0 \u09ac"
            "\u09a1\u09bc \u09b8\u09cd\u099f\u09aa\u0997\u09c1\u09b2\u09cb\u09b0 \u09ae\u09a7\u09cd\u09af\u09c7 {v} \u0985\u09a8\u09cd\u09af\u09a4\u09ae\u0964 \u09af\u09be\u09a4\u09cd\u09b0\u09be\u09b0 \u0986\u0997\u09c7 \u09b8\u09ae\u09af\u09bc \u09af\u09be\u099a\u09be\u0987 \u0995\u09b0\u09c7 \u09a8\u09bf\u09a8\u0964"),
            (
            "{o} \u09a5\u09c7\u0995\u09c7 {d} \u09b0\u09c1\u099f\u09c7 \u09ae\u09cb\u099f {n}\u099f\u09bf \u09ac\u09be\u09b8 \u099a\u09b2\u09c7\u0964 \u09a6\u09bf\u09a8\u09c7\u09b0 \u09aa\u09cd\u09b0\u09a5\u09ae \u09ac\u09be\u09b8 {f} \u099f\u09be\u09af\u09bc \u099b\u09be\u09a1\u09bc\u09c7 \u098f\u09ac\u0982 \u09b6\u09c7\u09b7 \u09ac\u09be\u09b8 {l} \u099f\u09be\u09af\u09bc\u0964 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u09b9"
            "\u09a0\u09be\u09ce \u09ac\u09a6\u09b2\u09c7 \u09af\u09c7\u09a4\u09c7 \u09aa\u09be\u09b0\u09c7 \u2014 \u09ac\u09c7\u09b0 \u09b9\u0993\u09af\u09bc\u09be\u09b0 \u0986\u0997\u09c7 \u09a8\u09bf\u09b6\u09cd\u099a\u09bf\u09a4 \u0995\u09b0\u09c7 \u09a8\u09bf\u09a8\u0964"),
            (
            "{d} \u09af\u09be\u0993\u09af\u09bc\u09be\u09b0 \u099c\u09a8\u09cd\u09af {o} \u09a5\u09c7\u0995\u09c7 {n}\u099f\u09bf \u09ac\u09be\u09b8 \u09b8\u09be\u09b0\u09cd\u09ad\u09bf\u09b8 \u09aa\u09be\u0993\u09af\u09bc\u09be \u09af\u09be\u09af\u09bc\u0964 \u09aa\u09cd\u09b0\u09a5\u09ae \u09ac\u09be\u09b8 {f}, \u09b6\u09c7\u09b7 \u09ac\u09be\u09b8 {l}\u0964 \u09aa\u09cd\u09b0\u09a4\u09bf\u099f\u09bf \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8"
            "\u09ae\u09af\u09bc \u0993 \u09b8\u09cd\u099f\u09aa\u09c7\u099c \u098f\u0987 \u09aa\u09c7\u099c\u09c7\u0987 \u09a6\u09c7\u0993\u09af\u09bc\u09be \u0986\u099b\u09c7\u0964"),
        ]
        if not _via and _v == 1:
            _v = 0
        _en = _EN[_v].format(count=count, origin=g.esc(origin), destination=g.esc(destination), first=g.esc(first), last=g.esc(last), via=g.esc(_via))
        _bn = _BN[_v].format(n=bn_num(count), o=g.esc(bnplace(origin)), d=g.esc(bnplace(destination)), f=g.esc(bn_time(stats["first"])), l=g.esc(bn_time(stats["last"])), v=g.esc(bnplace(_via)))
        if _sb:
            if _sb == count:
                _en += " All of them are SBSTC government buses."
                _bn += " \u09b8\u09ac\u0997\u09c1\u09b2\u09cb\u0987 \u098f\u09b8\u09ac\u09bf\u098f\u09b8\u099f\u09bf\u09b8\u09bf \u09b8\u09b0\u0995\u09be\u09b0\u09bf \u09ac\u09be\u09b8\u0964"
            else:
                _en += " " + str(_sb) + " of them are SBSTC government buses."
                _bn += " \u098f\u09b0 \u09ae\u09a7\u09cd\u09af\u09c7 {n}\u099f\u09bf \u098f\u09b8\u09ac\u09bf\u098f\u09b8\u099f\u09bf\u09b8\u09bf \u09b8\u09b0\u0995\u09be\u09b0\u09bf \u09ac\u09be\u09b8\u0964".format(n=bn_num(_sb))
        intro_html = (
            '<p class="seo-intro" style="margin:12px 0 0;color:var(--ink-dim,#5c544a);font-size:14.5px;line-height:1.6;max-width:72ch">'
            '<span class="label-en">' + _en + '</span>'
            '<span class="label-bn">' + _bn + '</span></p>'
        )
'''

# 1) title
sub1('    title = f"{origin} to {destination} Bus Time Table | {g.SITE_NAME}"\n',
     '    if count > 1 and stats["first"] is not None:\n        title = f"{origin} to {destination} Bus Time Table ({count} buses, first {first})"\n    elif stats["first"] is not None:\n        title = f"{origin} to {destination} Bus Time Table (1 bus, departs {first})"\n    else:\n        title = f"{origin} to {destination} Bus Time Table | {g.SITE_NAME}"\n')

# 2) intro + SBSTC chip block (before bn_sub)
sub1('    bn_sub = f\'<p class="bn-sub">',
     INS + '    bn_sub = f\'<p class="bn-sub">')

# 3) hero template gets intro
sub1('  <div class="stat-chips">{chips}</div>\n</div>"""',
     '  <div class="stat-chips">{chips}</div>\n  {intro_html}\n</div>"""')

# 4) to-destination links + body
sub1('    body = hero + timetable + alt_section + major_section + faq_section + reverse_section + related_section\n',
     '    related_to = [(o, t) for (o, t) in g.route_meta if t == destination and o != origin]\n    related_to = sorted(related_to, key=lambda p: -len(g.route_meta[p]))[:8]\n    to_section = ""\n    if related_to:\n        links2 = "".join(\n            f\'<a class="rel-chip" href="{g.slug(o)}-to-{g.slug(t)}.html">{g.esc(o)} \\u2192 {g.esc(t)}</a>\'\n            for o, t in related_to\n        )\n        to_section = f"""<section class="seo-section">\n  <h3 class="section-title">{L("More Buses to " + g.esc(destination), g.esc(bnplace(destination)) + " \\u09af\\u09be\\u0993\\u09af\\u09bc\\u09be\\u09b0 \\u0986\\u09b0\\u0993 \\u09ac\\u09be\\u09b8")}</h3>\n  <div class="chip-row">{links2}</div>\n</section>"""\n\n    body = hero + timetable + alt_section + major_section + faq_section + reverse_section + related_section + to_section\n')

import ast
ast.parse(s)
with open(GEN, 'w', encoding='utf-8') as fh:
    fh.write(s)
assert 'P1 SEO' in s and 'seo-intro' in s and 'to_section' in s
print('OK')
