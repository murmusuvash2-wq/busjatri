#!/usr/bin/env python3
"""Shared lib for the Kolkata city route generator.

Design: hero (⇄ bidirectional) + direction switch + compact vertical trips with
click-drop-down (times) OR stops-only list (no time). Dark toggle, breadcrumb
(Home / Kolkata City Bus / Route), popular routes interlinked, FAQ + About
(so pages are not thin for Google). Idempotent; run AFTER gen_seo_pages.py.

Usage: python3 scripts/build_city_route_pages.py
"""
import json, os, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "busjatri_data.json")
CSTC = os.path.join(ROOT, "data", "cstc_city_bus_timetable.json")
OUT = os.path.join(ROOT, "bus-time-table")
BASE = "https://busjatri.in"

CITY = ['esplanade','howrah','park street','barabazar','sealdah','shyambazar','garia','behala','jadavpur',
 'tollygunge','dumdum','dudum','barasat','salt lake','karunamoyee','ballygunge','alipore','gariahat','rajabazar',
 'shibpur','bally','belur','chitpur','bagbazar','cossipore','khidirpur','taratala','joka','thakurpukur','parnasree',
 'babughat','ultadanga','kasba','dhakuria','dunlop','tobin','baranagar','kamalgazi','narendrapur','metiabruz',
 'garden reach','kankurgachi','maniktala','entally','bhowanipore','baguiati','kestopur','lake town','park circus',
 'baruipur','sonarpur','nabanna','santragachi','birati','madhyamgram','sodepur','agarpara','belghoria',
 'behala chowrastha','science city','mukundapur','badartala','bengal chemical','shilpara','bengal chem']

BN = {'dunlop':'ডানলপ','ballygunge':'বালিগঞ্জ','ballygunge stn':'বালিগঞ্জ স্টেশন','esplanade':'এসপ্ল্যানেড',
 'howrah':'হাওড়া','howrah stn':'হাওড়া স্টেশন','dumdum':'দমদম','dudum':'দমদম','dum dum':'দমদম','shyambazar':'শ্যামবাজার',
 'barabazar':'বড়বাজার','sealdah':'শিয়ালদহ','garia':'গড়িয়া','behala':'বেহালা','jadavpur':'যাদবপুর','tollygunge':'টালিগঞ্জ',
 'park street':'পার্ক স্ট্রিট','manicktala':'মানিকতলা','belgachia':'বেলগাছিয়া','barasat':'বারাসত','salt lake':'সল্টলেক',
 'karunamoyee':'করুণাময়ী','alipore':'আলিপুর','gariahat':'গড়িয়াহাট','rajabazar':'রাজাবাজার','ballygunge':'বালিগঞ্জ'}

def esc(v): return html.escape(str(v or ''), quote=True)
def slug(v): return re.sub(r'[^a-z0-9]+', '-', (v or '').lower()).strip('-') or 'x'
def bn(n): return BN.get((n or '').strip().lower(), '')
def is_city(p): return any(c in (p or '').lower() for c in CITY)
def mins(t):
    m = re.match(r'(\d{1,2}):(\d{2})', str(t or ''))
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None
def f12(t):
    m = mins(t)
    if m is None: return str(t or '—')
    h, mi = divmod(m, 60); ap = 'AM' if (h % 24) < 12 else 'PM'; h = h % 12 or 12
    return f'{h}:{mi:02d} {ap}'
def dur(a, b):
    x, y = mins(a), mins(b)
    if x is None or y is None or y < x: return ''
    d = y - x; return f'{d//60}h {d%60:02d}m' if d >= 60 else f'{d}m'
def norm_place(p):
    p = re.sub(r'\s+', ' ', (p or '').strip())
    p = re.sub(r'\s+(station|stn|bus stand|bus-stand|terminus|depot|stand)$', '', p, flags=re.I)
    return p.strip() or p
def collect_stops(bs):
    out = []
    for b in sorted(bs, key=lambda x: -len(x.get('stoppages') or [])):
        for st in (b.get('stoppages') or []):
            nm = (st.get('name') if isinstance(st, dict) else st) or ''
            nm = re.sub(r'\s+', ' ', nm).strip()
            if nm and nm not in out: out.append(nm)
    return out
def routenum(name):
    n = re.sub(r'^(WBTC|CSTC|SBSTC)\s+', '', (name or '').strip(), flags=re.I)
    m = re.search(r'([A-Za-z]{0,3}-?\d+[A-Za-z0-9/]*)', n)
    return m.group(1) if m else (n[:12] or 'CITY')

CSS = """<style>
body.dark{--bg:#17130d;--surface:#211b12;--surface-2:#2a2318;--ink:#f3ead9;--ink-dim:#b6a98f;--line:rgba(243,234,217,.14);--line-strong:rgba(243,234,217,.28);--amber:#e0a23c;--amber-ink:#f2c579;--amber-soft:rgba(224,162,60,.16);--green:#7fb08a;--green-soft:rgba(127,176,138,.16)}
.crumb{font:600 11px var(--font-mono);color:var(--ink-dim);padding:14px 0 2px}
.crumb a{color:var(--amber-ink);text-decoration:none}
.hero{position:relative;background:var(--surface);border:1px solid var(--line-strong);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow-sm);overflow:hidden;margin:8px 0 10px}
.hero:before{content:"";position:absolute;left:0;right:0;top:0;border-top:3px dashed var(--line-strong);opacity:.6}
.eyebrow{display:inline-block;background:var(--amber-soft);color:var(--amber-ink);border:1px solid color-mix(in srgb,var(--amber) 40%,transparent);border-radius:999px;font:600 10px var(--font-mono);text-transform:uppercase;letter-spacing:.05em;padding:4px 10px}
.hero h1{font-family:var(--font-display);font-size:clamp(1.35rem,5vw,1.85rem);line-height:1.2;letter-spacing:-.02em;margin:10px 0 6px}
.rcode{display:inline-block;background:var(--amber);color:#fff9ee;border-radius:var(--radius-sm);padding:2px 9px;margin-right:7px;font:700 .72em var(--font-mono);vertical-align:3px}
.hero h1 .bi{color:var(--amber);font-weight:400}
.stats{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}
.stat{background:var(--surface-2);border:1px solid var(--line);border-radius:999px;padding:6px 11px;font:600 11px var(--font-mono);color:var(--ink-dim)}
.stat b{color:var(--ink)}
.dswitch{display:flex;gap:6px;margin:14px 0 6px;background:var(--surface-2);border:1px solid var(--line);border-radius:999px;padding:4px}
.dswitch button{flex:1;border:0;background:none;border-radius:999px;padding:9px 10px;font:700 12px var(--font-mono);color:var(--ink-dim);cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dswitch button.on{background:var(--surface);color:var(--amber-ink);box-shadow:var(--shadow-sm)}
.dswitch button .ar{color:var(--amber)}
.meta{font:600 11px var(--font-mono);color:var(--ink-dim);margin:8px 0}
.thead{display:grid;grid-template-columns:1fr auto 1fr;gap:10px;padding:6px 12px 5px;font:700 10px var(--font-mono);text-transform:uppercase;letter-spacing:.06em;color:var(--ink-dim)}
.thead .m{text-align:center}.thead .r{text-align:right}
.dpanel{display:none}.dpanel.on{display:block}
.trips{display:flex;flex-direction:column;gap:5px}
.trip{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:10px;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-sm);padding:8px 12px;cursor:pointer;text-align:left;font-family:inherit;color:inherit}
.trip:hover,.trip.open{border-color:var(--amber)}
.v{font:700 16px var(--font-mono)}.v.dep{color:var(--amber-ink);text-align:left}.v.arr{color:var(--green);text-align:right}
.mid{display:flex;align-items:center;gap:6px;min-width:64px;justify-content:center}
.ride{font:600 11px var(--font-mono);color:var(--ink-dim)}.chev{font:600 11px var(--font-mono);color:var(--amber-ink)}
.trip.open .chev{transform:rotate(180deg);display:inline-block}
.dd{grid-column:1/-1;max-height:0;overflow:hidden;transition:max-height .28s ease}
.trip.open .dd{max-height:680px}
.dd-in{display:block;border-top:1px dashed var(--line-strong);margin-top:9px;padding-top:9px}
.dd-h{font:700 10px var(--font-mono);text-transform:uppercase;letter-spacing:.04em;color:var(--ink-dim)}
.dd ol,.stoplist{list-style:none;margin:8px 0 0;padding:0 0 0 8px;border-left:2px dashed color-mix(in srgb,var(--amber) 45%,transparent)}
.dd li,.stoplist li{display:flex;align-items:center;gap:9px;position:relative;padding:5px 0 5px 8px;font-size:13.5px}
.dot{width:8px;height:8px;flex:none;margin-left:-13px;border-radius:50%;background:var(--surface);border:2px solid var(--amber)}
.stoplist li.end .dot{background:var(--amber)}
.sn{font-weight:600}.bn{color:var(--ink-dim);font-size:11px}.st{margin-left:auto;font:700 12px var(--font-mono);color:var(--amber-ink);white-space:nowrap}
.dd-note{display:block;margin-top:8px;font-size:11px;color:var(--ink-dim)}
.sec{margin:22px 0}
.sec h2{font-family:var(--font-display);font-size:1.15rem;margin:0 0 10px;display:flex;align-items:center;gap:9px}
.sec h2:before{content:"";width:7px;height:22px;background:var(--amber);border-radius:99px}
.pchips{display:flex;flex-wrap:wrap;gap:7px}
.pchip{background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:8px 13px;font-size:12.5px;font-weight:700;color:var(--ink);text-decoration:none;display:inline-flex;gap:6px;align-items:center}
.pchip:hover{border-color:var(--amber);background:var(--amber-soft);color:var(--amber-ink)}
.pchip .rn{font-family:var(--font-mono);color:var(--amber-ink);font-size:11px}
.faq details{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-sm);margin:7px 0}
.faq details[open]{border-color:var(--amber)}
.faq summary{cursor:pointer;padding:11px 14px;font-weight:700;font-size:13.5px;list-style:none}
.faq summary::-webkit-details-marker{display:none}
.faq summary:before{content:"▸ ";color:var(--amber)}
.faq details[open] summary:before{content:"▾ "}
.faq .a{padding:0 14px 12px;color:var(--ink-dim);font-size:13px}
.about{background:var(--surface-2);border:1px solid var(--line);border-radius:var(--radius-sm);padding:13px 15px;font-size:13px;color:var(--ink)}
.about p{margin:0 0 8px}.about p:last-child{margin:0}
.notime-note{border-left:3px solid var(--amber);background:var(--amber-soft);border-radius:0 var(--radius-sm) var(--radius-sm) 0;padding:10px 13px;font-size:12.5px;margin:12px 0}
@media(max-width:480px){.v{font-size:14px}.trip{padding:7px 10px;gap:6px}.mid{min-width:50px}.dswitch button{font-size:11px}}
</style>"""

