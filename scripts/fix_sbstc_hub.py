#!/usr/bin/env python3
"""Fix the SBSTC hub page (bus-time-table/sbstc-buses.html).

GSC URL Inspection showed: fetch OK, indexing allowed, but Google-selected
canonical is empty (i.e. NOT indexed) — the page is a thin hub of route links
with no actual timetable. It ranks for the biggest keyword in our GSC data
("sbstc bus timetable", 22 impressions, pos 13.3) yet earns 0 clicks.

Fix: add a real, unique-content section — the official SBSTC route timetable
(68 routes, departure times + fares) from data/sbstc-official-times.json
(source: transport.wb.gov.in official WBTC/SBSTC route listing) — using only
existing CSS classes (seo-section / bus-row / badge), and link each route to
its page where one exists.

Idempotent: guarded by <!-- sbstc-hub-official-v1 -->.
"""
import json, os, re

BASE = os.path.join(os.path.dirname(__file__), "..")
BT = os.path.join(BASE, "bus-time-table")
MARKER = "<!-- sbstc-hub-official-v1 -->"
SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
       'aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>')
ALIAS = {'midnapur': 'midnapur', 'midnapore': 'midnapur', 'arambag': 'arambagh',
         'goyespur': 'gayespur', 'garhbhowanipur': 'garbhawanipur'}


def norm(s):
    s = s.lower()
    s = re.sub(r'\s*\b(a\.c\.?|ac)\b\s*$', '', s)
    return re.sub(r'\s+via[-\s].*$', '', s).strip()


def title(s):
    return ' '.join(w.capitalize() if w not in ('to', 'via') else w for w in s.split())


def main():
    d = json.load(open(os.path.join(BASE, 'data/sbstc-official-times.json'), encoding='utf-8'))
    pages = {f[:-5] for f in os.listdir(BT) if f.endswith('.html')}
    rows, linked = [], 0
    for r in sorted(d['routes'], key=lambda r: -len(r['up_times'])):
        rt = norm(r['route'])
        if ' to ' not in rt:
            continue
        a, b = [x.strip() for x in rt.split(' to ', 1)]
        n = len(r['up_times'])
        first, last = r['up_times'][0], r['up_times'][-1]
        slug = f"{a.replace(' ','-')}-to-{b.replace(' ','-')}"
        link = ''
        if slug in pages:
            link = (f'<a class="bd-link" href="./{slug}.html" aria-label="View {title(a)} to {title(b)} timetable">'
                    '<span class="label-en">Details ›</span><span class="label-bn">বিস্তারিত ›</span></a>')
            linked += 1
        n_txt = ('single daily service' if n == 1 else f'{n} services daily')
        n_bn = ('দৈনিক একটি পরিষেবা' if n == 1 else f'{n}টি পরিষেবা প্রতিদিন')
        rows.append(f'''<div class="bus-row">
      <div class="dep">{SVG}<div class="depcol"><span class="dep-t">{first}</span></div></div>
      <div class="bmid">
        <div class="op">SBSTC <span style="color:var(--amber-ink,#6b4610);font-weight:600">· {title(a)} → {title(b)}</span></div>
        <div class="mrow">🚌 {n_txt} <span class="label-bn">{n_bn}</span> · ⏰ <span class="label-en">last bus</span><span class="label-bn">শেষ বাস</span> {last}</div>
      </div>
      <div class="bright"><span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span><span class="badge">from ₹{r['fare_inr']}</span>{link}</div>
    </div>''')

    sec = f'''{MARKER}
<section class="seo-section">
  <h3 class="section-title"><span class="label-en">SBSTC Route Timetable — Official Departure Times</span><span class="label-bn">এসবিএসটিসি রুট সময়সূচি — সরকারি ছাড়ার সময়</span></h3>
  <p class="bn-sub"><span class="label-en">Every route below is from the official WB Transport (SBSTC) route listing — first departure, number of daily services, last bus and fare. Buses can run late. Spotted a change? Report it on our <a href="../contribute.html">Contribute page</a>.</span><span class="label-bn">নিচের প্রতিটি রুট অফিসিয়াল ডব্লিউবি ট্রান্সপোর্ট (এসবিএসটিসি) রুট তালিকা থেকে — প্রথম ছাড়া, দৈনিক পরিষেবার সংখ্যা, শেষ বাস ও ভাড়া। বাস দেরিতে চলতে পারে। সময় বদলে থাকলে আমাদের <a href="../contribute.html">Contribute পেজে</a> জানান।</span></p>
  {chr(10).join('  ' + r for r in rows)}
</section>
'''

    p = os.path.join(BT, 'sbstc-buses.html')
    h = open(p, encoding='utf-8').read()
    if MARKER in h:
        print('already patched')
        return
    # insert right before the "All Destinations" heading
    m = re.search(r'<h2[^>]*>(?:(?!</h2>).)*?All Destinations', h, re.S)
    if not m:
        raise SystemExit('anchor (All Destinations) not found')
    h = h[:m.start()] + sec + '\n' + h[m.start():]
    open(p, 'w', encoding='utf-8').write(h)
    print(f'added {len(rows)} official route rows | {linked} linked to their page')


if __name__ == "__main__":
    main()
