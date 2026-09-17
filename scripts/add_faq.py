#!/usr/bin/env python3
"""Add a data-driven, visible FAQ + richer FAQ JSON-LD to every route page.

For each bus-time-table/<from>-to-<to>.html page, computes real answers from
data/busjatri_data.json: first bus, last bus, night buses, journey duration,
operators, via-stoppages and (for SBSTC routes) fare. The existing FAQPage
JSON-LD is replaced; the visible FAQ section is re-created idempotently.
Run with no arguments.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / 'bus-time-table'
DATA = json.loads((ROOT / 'data' / 'busjatri_data.json').read_text(encoding='utf-8'))

TIME_RE = re.compile(r'^(\d{1,2}):(\d{2})\s*(AM|PM)$', re.I)

def to_min(t):
    m = TIME_RE.match((t or '').strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    ap = m.group(3).upper()
    if ap == 'AM':
        h = 0 if h == 12 else h
    else:
        h = 12 if h == 12 else h + 12
    return h * 60 + mi

def fmt(m):
    h, mi = divmod(m, 60)
    ap = 'AM' if h < 12 else 'PM'
    h12 = h % 12 or 12
    return f'{h12}:{mi:02d} {ap}'

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', (s or '').lower()).strip('-')

AMP = chr(38)
def esc(s):
    return (s or '').replace(AMP, AMP + 'amp;').replace('<', AMP + 'lt;').replace('>', AMP + 'gt;').replace('"', AMP + 'quot;')

# ---- route -> buses index (from ROUTES plus a reverse scan for full coverage) ----
ROUTES = DATA.get('routes') or {}
BUSES_BY_ID = {b['id']: b for b in DATA['buses']}

slug_buses = {}
for slug_key, r in ROUTES.items():
    slug_buses[slug_key] = [BUSES_BY_ID[i] for i in (r.get('bus_ids') or []) if i in BUSES_BY_ID]
for b in DATA['buses']:
    s = slug(f"{b.get('origin','')}-to-{b.get('destination','')}")
    if s:
        slug_buses.setdefault(s, [])
        if b not in slug_buses[s]:
            slug_buses[s].append(b)

# ---- SBSTC fare map ----
FARE = {}
sb = ROOT / 'data' / 'sbstc_routes.json'
if sb.exists():
    try:
        for r in json.loads(sb.read_text(encoding='utf-8')):
            if r.get('fare'):
                FARE[slug(r.get('name', ''))] = r['fare']
    except Exception as e:
        print('  sbstc fares skipped:', e)

FAQ_CSS = '<style>.bj-faq{margin:26px 0 6px}.bj-faq h2{font-size:1.12rem;margin:0 0 10px}.bj-faq details{border:1px solid #e8e0d0;border-radius:10px;margin:8px 0;background:#fffdf7}.bj-faq summary{padding:10px 14px;cursor:pointer;font-weight:600;font-size:.92rem;list-style:none}.bj-faq summary::-webkit-details-marker{display:none}.bj-faq summary::after{content:"+";float:right;color:#b8791f;font-weight:700}.bj-faq details[open] summary::after{content:"\\2013"}.bj-faq .faq-a{padding:0 14px 12px;color:#5a5348;font-size:.88rem;line-height:1.55}</style>'

JSONLD_RE = re.compile(r'<script type="application/ld\+json">\{"@context": "https://schema\.org", "@type": "FAQPage".*?</script>', re.S)
FAQ_SECTION_RE = re.compile(r'<section class="bj-faq".*?</section>', re.S)

def first_dep(b):
    t = to_min(b.get('departure_time'))
    if t is not None:
        return t
    for s in (b.get('stoppages') or []):
        t = to_min(s.get('up_time'))
        if t is not None:
            return t
    return None

def journey_mins(b):
    d, a = to_min(b.get('departure_time')), to_min(b.get('arrival_time'))
    if d is None or a is None:
        return None
    if a < d:
        a += 720  # PM arrival recorded as AM bug guard
        if a < d:
            a += 720
    return a - d

def build_qa(fr, to, buses):
    fr_t, to_t = (fr or '').strip(), (to or '').strip()
    frL, toL = fr_t.lower(), to_t.lower()
    fwd = [b for b in buses if (b.get('origin') or '').lower() == frL and (b.get('destination') or '').lower() == toL]
    pool = fwd or buses
    deps = [d for d in (first_dep(b) for b in pool) if d is not None]
    qa = []
    if deps:
        qa.append((f"What is the first bus from {fr_t} to {to_t}?.strip()",
                   f"The first bus from {fr_t} to {to_t} departs at {fmt(min(deps))}."))
        qa.append((f"What is the last bus from {fr_t} to {to_t}?",
                   f"The last bus from {fr_t} to {to_t} departs at {fmt(max(deps))}."))
        qa.append((f"How many buses run from {fr_t} to {to_t}?",
                   f"{len(pool)} bus services are listed on this route" +
                   (" (including return services)." if not fwd else ".")))
        night = sorted(d for d in deps if d >= 20 * 60 or d < 5 * 60)
        if night:
            qa.append((f"Is there any night bus from {fr_t} to {to_t}?",
                       "Yes — late-night / early-morning services depart at " +
                       ", ".join(fmt(d) for d in night[:5]) + "."))
        else:
            qa.append((f"Is there any night bus from {fr_t} to {to_t}?",
                       f"No night service is listed on this route. The last bus leaves at {fmt(max(deps))} and services resume in the morning."))
    else:
        qa.append((f"What is the bus timing from {fr_t} to {to_t}?",
                   "Timings for this route are still being collected. Please check the timetable above for any listed services, or ask at the bus stand."))
        qa.append((f"How many buses run from {fr_t} to {to_t}?",
                   f"{len(pool)} bus services are listed on this route."))
    durs = [d for d in (journey_mins(b) for b in pool) if d and 0 < d <= 12 * 60]
    if durs:
        avg = sum(durs) // len(durs)
        qa.append((f"How long does the bus take from {fr_t} to {to_t}?",
                   f"The journey takes roughly {avg // 60} hour{'s' if avg // 60 != 1 else ''} {avg % 60} minute{'s' if avg % 60 != 1 else ''}, depending on traffic and stoppages."))
    ops = sorted({('Government' if 'government' in (b.get('bus_type') or '').lower() else 'Private') for b in pool})
    if ops:
        names = sorted({(b.get('bus_name') or '').strip() for b in pool if b.get('bus_name') and len(b.get('bus_name','')) < 26})
        sample = ", ".join(names[:3])
        qa.append((f"Which operators run buses on the {fr_t} to {to_t} route?",
                   f"Services include {' and '.join(ops).lower()} operators" + (f" such as {sample}." if sample else ".")))
    # via stoppages from the bus with the most stops
    best = max(pool, key=lambda b: len(b.get('stoppages') or []), default=None)
    if best and best.get('stoppages'):
        via = [s.get('name') for s in best['stoppages'] if s.get('name')][1:9]
        if len(via) >= 2:
            qa.append((f"Which places does the {fr_t} to {to_t} bus pass through (via)?",
                       "The main stoppages on the way are " + ", ".join(via) + "."))
    fare = FARE.get(slug(f"{fr_t}-to-{to_t}"))
    if fare:
        qa.append((f"What is the bus fare from {fr_t} to {to_t}?",
                   f"The listed SBSTC fare for this route is {fare}. Private bus fares may differ — confirm with the conductor."))
    else:
        qa.append((f"What is the bus fare from {fr_t} to {to_t}?",
                   "Fares for this route are not listed yet. West Bengal bus fares depend on distance and bus type — confirm the exact fare with the conductor or the bus stand counter."))
    return qa

def render(qa, fr_t, to_t):
    items = "".join(
        f'<details class="faq-item"><summary>{esc(q)}</summary><div class="faq-a">{esc(a)}</div></details>'
        for q, a in qa)
    sec = (f'{FAQ_CSS}\n<section class="bj-faq" aria-label="FAQ">'
           f'<h2>Frequently Asked Questions — {esc(fr_t)} to {esc(to_t)}</h2>{items}</section>')
    mainentity = json.dumps([
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa],
        ensure_ascii=False)
    jsonld = ('<script type="application/ld+json">{"@context": "https://schema.org", '
              '"@type": "FAQPage", "mainEntity": ' + mainentity + '}</script>')
    return sec, jsonld

def main():
    n_ok = n_skip = 0
    for p in sorted(PAGES.glob('*.html')):
        if p.name == 'index.html':
            continue
        s = p.read_text(encoding='utf-8')
        # route names: try ROUTES first, else from the h1
        key = p.stem
        r = ROUTES.get(key) or {}
        fr, to = r.get('from'), r.get('to')
        if not fr:
            m = re.search(r'<h1>([^<]+?)\s*<span[^>]*>.*?</span>\s*([^<]+?)</h1>', s)
            if m:
                fr, to = m.group(1).strip(), m.group(2).strip()
        if not fr:
            m2 = re.match(r'(.+?)-to-(.+)$', key)
            if m2:
                fr = m2.group(1).replace('-', ' ').title()
                to = m2.group(2).replace('-', ' ').title()
        buses = slug_buses.get(key) or []
        if not fr or not to:
            n_skip += 1
            continue
        qa = build_qa(fr, to, buses)
        sec, jsonld = render(qa, fr, to)
        s = FAQ_SECTION_RE.sub('', s)
        s = JSONLD_RE.sub(jsonld, s)
        if '</main>' in s:
            s = s.replace('</main>', sec + '\n</main>', 1)
        elif '</body>' in s:
            s = s.replace('</body>', sec + '\n</body>', 1)
        else:
            n_skip += 1
            continue
        p.write_text(s, encoding='utf-8')
        n_ok += 1
    print(f'FAQ added to {n_ok} route pages ({n_skip} skipped)')

if __name__ == '__main__':
    main()
