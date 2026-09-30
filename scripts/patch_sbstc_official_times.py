#!/usr/bin/env python3
"""Add the official SBSTC departure-time list to matching route pages.

Source: transport.wb.gov.in "LIST OF OPERARTIVE ROUTES OF SBSTC"
(RouteTimeTableFareSBSTC.pdf) — the official WB Transport Dept listing, parsed
into data/sbstc-official-times.json. 63 published routes map to 56 pages.

Each page gets one section:
  SBSTC — Official Departure Times
    row (up direction): first time, "N services daily", last time, Govt, fare
    row (down direction): same
    note: full official time list both directions + source + "report a change"
          link to ../contribute.html

If the page already carries the redBus-derived SBSTC card (asansol-sbstc-v1),
that card is REPLACED so the two sources cannot contradict each other.

Idempotent: guarded by <!-- sbstc-official-v1 -->.
"""
import json, os, re

BASE = os.path.join(os.path.dirname(__file__), "..")
BT = os.path.join(BASE, "bus-time-table")
MARKER = "<!-- sbstc-official-v1 -->"

SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
       '<path d="M12 7v5l3 2"/></svg>')

ALIAS = {'midnapur': 'midnapur', 'midnapore': 'midnapur', 'arambag': 'arambagh',
         'goyespur': 'gayespur', 'garhbhowanipur': 'garbhawanipur'}


def norm(s):
    s = s.lower()
    s = re.sub(r'\s*\b(a\.c\.?|ac)\b\s*$', '', s)
    s = re.sub(r'\s+via[-\s].*$', '', s)
    return s.replace('&', 'and').strip()


def title(s):
    return ' '.join(w.capitalize() if w not in ('to', 'via') else w for w in s.split())


def row(direction_en, direction_bn, times, fare):
    first = times[0]
    last = times[-1]
    n = len(times)
    if n == 1:
        mid = '<span class="label-en">single daily service</span><span class="label-bn">দৈনিক একটি পরিষেবা</span>'
    else:
        mid = f"{n} <span class=\"label-en\">services daily</span><span class=\"label-bn\">টি পরিষেবা প্রতিদিন</span>"
    return f'''<div class="bus-row">
      <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{first}</span></div></div>
      <div class="bmid">
        <div class="op">SBSTC <span style="color:var(--amber-ink,#6b4610);font-weight:600">· {direction_en}</span></div>
        <div class="mrow">⏱ {mid} · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> {last}</div>
      </div>
      <div class="bright"><span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span><span class="badge">from ₹{fare}</span></div>
    </div>'''


def build_section(entries):
    rows = []
    up_notes, dn_notes = [], []
    for r, a, b in entries:
        rows.append(row(f"{title(a)} → {title(b)}", '', r['up_times'], r['fare_inr']))
        if r['down_times']:
            rows.append(row(f"{title(b)} → {title(a)}", '', r['down_times'], r['fare_inr']))
        up_notes.append(f"{title(a)} → {title(b)}: " + ", ".join(r['up_times']))
        if r['down_times']:
            dn_notes.append(f"{title(b)} → {title(a)}: " + ", ".join(r['down_times']))
    en = ("Official departure times from the WB Transport (SBSTC) route listing — "
          + " | ".join(up_notes + dn_notes) +
          ". Buses can run late. Has a timing changed? Report it on our "
          '<a href="../contribute.html">Contribute page</a>.')
    bn = ("ডব্লিউবি ট্রান্সপোর্ট (এসবিএসটিসি) সরকারি রুট তালিকা অনুযায়ী ছাড়ার সময়। "
          "বাস দেরিতে চলতে পারে। সময় বদলে থাকলে আমাদের "
          '<a href="../contribute.html">Contribute পেজে</a> জানান।')
    return (f'''{MARKER}
<section class="seo-section">
    <h3 class="section-title"><span class="label-en">SBSTC — Official Departure Times</span><span class="label-bn">এসবিএসটিসি — সরকারি ছাড়ার সময়</span></h3>
    {chr(10).join('    ' + r for r in rows)}
    <p class="bn-sub"><span class="label-en">{en}</span><span class="label-bn">{bn}</span></p>
  </section>
''')


def insert(h, sec):
    m = h.find('<!-- asansol-sbstc-v1 -->')
    if m != -1:
        e = h.find('</section>', m) + len('</section>')
        return h[:m] + sec.rstrip() + h[e:]
    m = h.find('<!-- wbtc-long-v1 -->')
    if m != -1:
        e = h.find('</section>', m) + len('</section>')
        return h[:e] + "\n  " + sec + h[e:]
    vs = h.find('Via Stoppages')
    if vs != -1:
        e = h.rfind('</section>', 0, vs) + len('</section>')
        return h[:e] + "\n  " + sec + h[e:]
    e = h.find('</section>') + len('</section>')
    return h[:e] + "\n  " + sec + h[e:]


def main():
    d = json.load(open(os.path.join(BASE, 'data/sbstc-official-times.json'), encoding='utf-8'))
    pages = {}
    for r in d['routes']:
        rt = norm(r['route'])
        if ' to ' not in rt:
            continue
        a, b = [x.strip() for x in rt.split(' to ', 1)]
        a = ALIAS.get(a, a); b = ALIAS.get(b, b)
        slug = f"{a.replace(' ','-')}-to-{b.replace(' ','-')}.html"
        if os.path.exists(os.path.join(BT, slug)):
            pages.setdefault(slug, []).append((r, a, b))
    print(f"pages to patch: {len(pages)}")
    done = 0
    for slug, entries in sorted(pages.items()):
        p = os.path.join(BT, slug)
        h = open(p, encoding='utf-8').read()
        if MARKER in h:
            continue
        sec = build_section(entries)
        h = insert(h, sec)
        open(p, 'w', encoding='utf-8').write(h)
        done += 1
    print(f"patched: {done}")


if __name__ == "__main__":
    main()
