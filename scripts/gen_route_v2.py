#!/usr/bin/env python3
"""
Route page generator v2 — demo-approved design (2026-09-22, rev 2).

Layers on top of gen_seo_pages.py (loads only its safe helpers + data):
  1. Unified header: logo + EN/বাংলা pills + working dark-mode button
  2. Dark mode via body.dark (palette from the approved demo)
  3. Rich FAQ: 5 English + 5 Bengali SEARCH-INTENT questions, data-driven
     answers, all in <details> cards + FAQPage JSON-LD (10 questions)
  4. Safe wording: we only claim what is LISTED — "1 bus listed", never
     "only 1 bus runs" (more services may exist in reality)
  5. Pre-computed alternative-route section (1-change) below the bus list
  6. Unified 7-link footer
  7. Through-services: buses that pass both places (homepage search
     parity — Digha→Bardhaman shows 6 buses, not just the 1 exact match)

Usage:
  python3 scripts/gen_route_v2.py --routes "Durgapur::Esplanade,Digha::Kolkata"
  python3 scripts/gen_route_v2.py --all

Run from the repo root. Writes bus-time-table/<from>-to-<to>.html.
Never fabricates: untimed legs/stops are skipped, "—" placeholders used.
"""

import os
import sys
import types

os.environ.setdefault("SITE_BASE", "https://busjatri.in")

# Guarded load of gen_seo_pages: exec ONLY the safe head of the file
# (constants, helpers, data load, route indexes). The module has NO
# __main__ guard and its tail regenerates every page + sitemap on plain
# import — the cut below makes that impossible to run accidentally.
_GEN_SRC_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "gen_seo_pages.py"
)
with open(_GEN_SRC_PATH, "r", encoding="utf-8") as _f:
    _gen_src = _f.read()
_CUT = "os.makedirs(OUT, exist_ok=True)"  # first statement of the generation tail
if _CUT not in _gen_src:
    raise RuntimeError("gen_seo_pages.py layout changed — guarded import needs a review")
_safe_src = _gen_src[: _gen_src.index(_CUT)]
g = types.ModuleType("gseo_core")
g.__dict__["__name__"] = "gseo_core"
exec(compile(_safe_src, _GEN_SRC_PATH, "exec"), g.__dict__)
for _need in ("BUSES", "route_meta", "slug", "esc", "parse_time", "route_stats"):
    if not hasattr(g, _need):
        raise RuntimeError(f"guarded import missing {_need} — layout changed")

# ------------------------------------------------------------
# version tags (bump on every change)
# ------------------------------------------------------------
CSS_V2 = "seov2b"
JS_V2 = "seopagea"

# ------------------------------------------------------------
# Bengali helpers
# ------------------------------------------------------------

BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def bn_num(n):
    return str(n).translate(BN_DIGITS)


def bn_time(minutes):
    """minutes-of-day -> Bengali clock string like 'সকাল ৬:৩০'."""
    if minutes is None:
        return "—"
    m = minutes % 1440
    h, mm = divmod(m, 60)
    if h < 4:
        period = "রাত"
    elif h < 5:
        period = "ভোর"
    elif h < 12:
        period = "সকাল"
    elif h < 16:
        period = "দুপুর"
    elif h < 18:
        period = "বিকেল"
    elif h < 19:
        period = "সন্ধে"
    else:
        period = "রাত"
    h12 = h % 12 or 12
    return f"{period} {bn_num(h12)}:{bn_num(f'{mm:02d}')}"


def bn_dur(minutes):
    if minutes is None:
        return "—"
    h, m = divmod(int(minutes), 60)
    parts = []
    if h:
        parts.append(bn_num(h) + " ঘণ্টা")
    if m:
        parts.append(bn_num(m) + " মিনিট")
    return " ".join(parts) if parts else "—"


def bnplace(name):
    return g.bn(name) or name


def L(en, bn):
    """bilingual label span pair"""
    return f'<span class="label-en">{en}</span><span class="label-bn">{bn}</span>'


# ------------------------------------------------------------
# ALT-ROUTE PRE-COMPUTE (static port of js/alt-route.js findAlt)
# ------------------------------------------------------------

def _seq_of(bus):
    stops = bus.get("stoppages") or []
    seq = [g.norm_place(bus.get("origin"))] + [
        g.norm_place(s.get("name")) for s in stops
    ] + [g.norm_place(bus.get("destination"))]
    return [x for x in seq if x and x != "—"]


def _from_stop(stop, direction):
    if not stop:
        return None
    key = "up_time" if direction == "up" else "down_time"
    return g.parse_time(stop.get(key))


def _stop_at(bus, pos, direction):
    """pos in _seq_of convention: 0=origin, 1..n=stoppages, n+1=destination.
    Mirrors alt-route.js stopAt() (JS position n+2 == our n+1)."""
    stops = bus.get("stoppages") or []
    n = len(stops)
    if pos == 0:
        if direction == "up":
            return g.parse_time(bus.get("departure_time"))
        return _from_stop(stops[-1] if stops else None, "down")
    if 1 <= pos <= n:
        return _from_stop(stops[pos - 1], direction)
    if pos == n + 1:
        if direction == "up":
            return g.parse_time(bus.get("arrival_time"))
        return _from_stop(stops[-1] if stops else None, "down")
    return None


class AltIndex:
    """place-slug -> bus positions, built once for all routes."""

    def __init__(self, buses):
        self.buses = buses
        self.where = {}  # slug -> {bus_idx: [positions]}
        self.seq_cache = []
        for i, bus in enumerate(buses):
            seq = _seq_of(bus)
            self.seq_cache.append(seq)
            for pos, name in enumerate(seq):
                self.where.setdefault(g.slug(name), {}).setdefault(i, []).append(pos)

    def find(self, origin, destination, max_options=3):
        o_slug, d_slug = g.slug(origin), g.slug(destination)
        results = []

        o_buses = self.where.get(o_slug, {})
        d_buses = self.where.get(d_slug, {})

        # deliverers: bus2 serves destination (not at pos 0) and never serves origin
        deliverers = []
        for bi, poss in d_buses.items():
            if bi in o_buses:
                continue
            tpos = min(poss)
            if tpos < 1:
                continue
            deliverers.append((bi, tpos))

        # hub index for deliverers: every boarding point on each deliverer
        hub_index = {}
        for bi, tpos in deliverers:
            seq = self.seq_cache[bi]
            for p in range(len(seq)):
                if p == tpos:
                    continue
                key = g.slug(seq[p])
                if not key:
                    continue
                hub_index.setdefault(key, []).append((bi, tpos, p))

        # bus1: serves origin, never serves destination
        for b1i, poss in o_buses.items():
            if b1i in d_buses:
                continue
            fpos = min(poss)
            seq1 = self.seq_cache[b1i]
            bus1 = self.buses[b1i]
            dep1 = _stop_at(bus1, fpos, "up")
            if dep1 is None:
                continue
            for hp in range(fpos + 1, len(seq1)):
                hub = seq1[hp]
                if g.slug(hub) in (o_slug, d_slug):
                    continue
                arr1 = _stop_at(bus1, hp, "up")
                if arr1 is None:
                    continue
                a1 = arr1 + 1440 if arr1 < dep1 else arr1
                for b2i, tpos2, hpos2 in hub_index.get(g.slug(hub), []):
                    if b2i == b1i:
                        continue
                    bus2 = self.buses[b2i]
                    if hpos2 < tpos2:
                        brd2 = _stop_at(bus2, hpos2, "up")
                        arr2 = _stop_at(bus2, tpos2, "up")
                    else:
                        brd2 = _stop_at(bus2, hpos2, "down")
                        arr2 = _stop_at(bus2, tpos2, "down")
                    if brd2 is None or arr2 is None:
                        continue
                    b2n = brd2
                    while b2n < a1 + 5:
                        b2n += 1440
                    wait = b2n - a1
                    if wait < 5 or wait > 240:
                        continue
                    a2n = arr2
                    while a2n <= b2n:
                        a2n += 1440
                    total = a2n - dep1
                    if total > 36 * 60:
                        continue
                    results.append({
                        "hub": hub,
                        "b1": bus1, "b2": bus2,
                        "dep1": dep1, "arr_hub": a1,
                        "board2": b2n, "arrive": a2n,
                        "wait": wait, "total": total,
                    })

        # best option per hub (shortest total), then top hubs
        per_hub = {}
        for opt in results:
            key = g.slug(opt["hub"])
            cur = per_hub.get(key)
            if cur is None or opt["total"] < cur["total"]:
                per_hub[key] = opt
        opts = sorted(per_hub.values(), key=lambda o: o["total"])
        return opts[:max_options]


# ------------------------------------------------------------
# place matching — port of app.js placeMatches (fuzzy + alias groups)
# ------------------------------------------------------------

import re as _re

_PLACE_ALIAS_GROUPS = [
    ['contai', 'kanthi'],
    ['berhampore', 'baharampur'],
    ['bardhaman', 'burdwan'],
    ['kolkata', 'calcutta', 'esplanade', 'howrah', 'santragachi', 'garia', 'tollygunge', 'kudghat', 'karunamoyee'],
    ['bolpur', 'santiniketan'],
    ['tarakeswar', 'tarakeshwar'],
    ['malda', 'english bazar', 'malda town'],
    ['cooch behar', 'koch bihar'],
    ['krishnanagar', 'krishnagar'],
]
_PLACE_ALIAS = {}
for _grp in _PLACE_ALIAS_GROUPS:
    for _n in _grp:
        _PLACE_ALIAS[_n] = _grp


def _pm_core(v, q):
    if not v or not q:
        return False
    if q in v:
        return True
    vc = _re.sub(r'[^a-z0-9]', '', v)
    qc = _re.sub(r'[^a-z0-9]', '', q)
    if vc.endswith('ac'):
        vc = vc[:-2]
    if qc.endswith('ac'):
        qc = qc[:-2]
    if qc and (vc == qc or qc in vc):
        return True
    vs = _re.sub(r'[^bcdfghjklmnpqrstvwxyz]', '', v)
    qs = _re.sub(r'[^bcdfghjklmnpqrstvwxyz]', '', q)
    if len(qs) >= 4 and (vs == qs or qs in vs):
        return True
    return False


def _pm_alias_variants(name):
    k = str(name or '').lower().strip()
    grp = _PLACE_ALIAS.get(k)
    return [k] + list(grp) if grp else [k]

_PM_CACHE = {}


def place_matches(value, query):
    """Faithful port of app.js placeMatches (kept fast by a memo cache —
    stop names repeat heavily across buses)."""
    key = (str(value or '').lower().strip(), str(query or '').lower().strip())
    hit = _PM_CACHE.get(key)
    if hit is not None:
        return hit
    v, q = key
    res = False
    if v and q:
        if _pm_core(v, q):
            res = True
        else:
            for aq in _pm_alias_variants(q):
                if _pm_core(v, aq):
                    res = True
                    break
            if not res:
                for av in _pm_alias_variants(v):
                    if _pm_core(av, q):
                        res = True
                        break
    _PM_CACHE[key] = res
    return res


def _pm_core_strict(v, q):
    """Like _pm_core but the skeleton tier only accepts a shared PREFIX
    (same word, spelling variant). Search-style 'contains' skeletons let
    Santipur match Aantpur — wrong for a static route page."""
    if not v or not q:
        return False
    if q in v:
        return True
    vc = _re.sub(r'[^a-z0-9]', '', v)
    qc = _re.sub(r'[^a-z0-9]', '', q)
    if vc.endswith('ac'):
        vc = vc[:-2]
    if qc.endswith('ac'):
        qc = qc[:-2]
    if qc and (vc == qc or qc in vc):
        return True
    vs = _re.sub(r'[^bcdfghjklmnpqrstvwxyz]', '', v)
    qs = _re.sub(r'[^bcdfghjklmnpqrstvwxyz]', '', q)
    if len(qs) >= 4 and (vs == qs or vs.startswith(qs)):
        return True
    return False


_PMS_CACHE = {}


def place_matches_strict(value, query):
    """place_matches with the strict skeleton tier (route-page through
    services). Substring, compact and alias tiers stay identical to the
    homepage search."""
    key = (str(value or '').lower().strip(), str(query or '').lower().strip())
    hit = _PMS_CACHE.get(key)
    if hit is not None:
        return hit
    v, q = key
    res = False
    if v and q:
        if _pm_core_strict(v, q):
            res = True
        else:
            for aq in _pm_alias_variants(q):
                if _pm_core_strict(v, aq):
                    res = True
                    break
            if not res:
                for av in _pm_alias_variants(v):
                    if _pm_core_strict(av, q):
                        res = True
                        break
    _PMS_CACHE[key] = res
    return res


def _pos_in(bus, query):
    """Port of bjPosIn: 0=origin field, 1..n=stoppages, n+2=destination field.
    Uses the strict matcher so unrelated look-alike names (Santipur vs
    Aantpur) do not leak onto route pages."""
    if place_matches_strict(bus.get("origin"), query):
        return 0
    stops = bus.get("stoppages") or []
    for idx, s in enumerate(stops):
        if place_matches_strict(s.get("name"), query):
            return idx + 1
    if place_matches_strict(bus.get("destination"), query):
        return len(stops) + 2
    return -1


def _bj_stop_min(bus, pos, direction):
    """Port of bjStopMin from stop-search-all.js."""
    stops = bus.get("stoppages") or []
    if pos == 0:
        if direction == "up":
            return g.parse_time(bus.get("departure_time"))
        return _from_stop(stops[-1] if stops else None, "down")
    if 1 <= pos <= len(stops):
        return _from_stop(stops[pos - 1], direction)
    if direction == "down":
        return _from_stop(stops[-1] if stops else None, "down")
    return _from_stop(stops[0], "up") if stops else g.parse_time(bus.get("arrival_time"))


def through_services(origin, destination, direct_buses, alt_index=None):
    """Parity with the homepage search (stop-search-all.js v3):
    every bus serving both places in EITHER direction, with the time it
    passes the boarding point (⇗ outward / ⇙ return). Only real stop times
    are used — nothing invented."""
    direct_ids = {b.get("id") for b in direct_buses}
    out = []
    for bus in g.BUSES:
        if bus.get("id") in direct_ids:
            continue
        fi = _pos_in(bus, origin)
        if fi < 0:
            continue
        ti = _pos_in(bus, destination)
        if ti < 0 or fi == ti:
            continue
        direction = "up" if fi < ti else "down"
        dep = _bj_stop_min(bus, fi, direction)
        arr = _bj_stop_min(bus, ti, direction)
        if dep is None and direction == "up":
            dep = g.parse_time(bus.get("departure_time"))
        out.append((dep if dep is not None else 9999, bus, dep, arr))
    out.sort(key=lambda x: x[0])
    return out


def alt_route_section(origin, destination, alt_index):
    opts = alt_index.find(origin, destination)
    if not opts:
        return ""

    cards = []
    for n, o in enumerate(opts, 1):
        b1, b2 = o["b1"], o["b2"]
        n1 = g.clean_text(b1.get("bus_name")) or "Bus service"
        n2 = g.clean_text(b2.get("bus_name")) or "Bus service"
        b1_id, b2_id = b1.get("id") or "", b2.get("id") or ""
        l1 = f'<a href="../index.html#/bus/{g.esc(b1_id)}" style="text-decoration:none;color:inherit">{g.esc(n1)}</a>' if b1_id else g.esc(n1)
        l2 = f'<a href="../index.html#/bus/{g.esc(b2_id)}" style="text-decoration:none;color:inherit">{g.esc(n2)}</a>' if b2_id else g.esc(n2)
        cards.append(f"""<div class="alt-card">
  <div class="alt-head">
    <span class="alt-badge">{L(f'Route {n} · via', f'রুট {bn_num(n)} ·')}</span> {g.esc(o['hub'])}
    <span>{L('1 change', '১ বার বাস বদল')}</span>
  </div>
  <div class="alt-leg">
    <div><div class="al-name">{l1}</div><div class="al-route">{g.esc(origin)} <span class="rarr">→</span> {g.esc(o['hub'])} · {L(f"arrives {g.esc(o['hub'])} {g.format_time(o['arr_hub'] % 1440)}", f"{g.esc(o['hub'])} পৌঁছায় {bn_time(o['arr_hub'])}")}</div></div>
    <span class="al-time">{g.format_time(o['dep1'] % 1440)}</span>
  </div>
  <div class="alt-change">
    <span style="font-weight:800;line-height:1">⇅</span>
    <span style="flex:1;min-width:0">{L('Change buses at ' + g.esc(o['hub']), 'বাস বদলান: ' + g.esc(o['hub']))}</span>
    <span class="alt-wait">{L(str(o['wait']), bn_num(o['wait']))} {L('min wait', 'মিনিট অপেক্ষা')}</span>
  </div>
  <div class="alt-leg">
    <div><div class="al-name">{l2}</div><div class="al-route">{g.esc(o['hub'])} <span class="rarr">→</span> {g.esc(destination)} · {L(f"arrives {g.esc(destination)} {g.format_time(o['arrive'] % 1440)}", f"{g.esc(bnplace(destination))} পৌঁছায় {bn_time(o['arrive'])}")}</div></div>
    <span class="al-time">{g.format_time(o['board2'] % 1440)}</span>
  </div>
  <div class="alt-total">{L('Total: ', 'মোট যাত্রা: ')}<b>{g.format_time(o['dep1'] % 1440)} → {g.format_time(o['arrive'] % 1440)} · {L(g.fmt_duration(o['total']), bn_dur(o['total']) + ' (' + g.fmt_duration(o['total']) + ')')}</b></div>
</div>""")

    return f"""<section class="seo-section alt-route">
  <h3 class="section-title">{L('Alternative route · 1 change', 'বিকল্প পথ · ১ বার বাস বদল')}</h3>
  <p class="alt-note">{L('If a direct bus is full or the timing does not suit you, these one-change routes also connect ' + g.esc(origin) + ' to ' + g.esc(destination) + ':', 'সরাসরি বাস ভরে গেলে বা সময় না মিললে, এক বার বাস বদলেও যাওয়া যায়:')}</p>
  {''.join(cards)}
</section>"""


# ------------------------------------------------------------
# FAQ — 5 EN + 5 BN, SEARCH-INTENT questions, rich data answers
# ------------------------------------------------------------

def faq_facts(origin, destination, buses):
    times = []
    first_bus = last_bus = None
    for b in buses:
        t = g.parse_time(b.get("departure_time"))
        if t is not None:
            times.append((t, b))
    times.sort(key=lambda x: x[0])
    if times:
        first_bus = times[0][1]
        last_bus = times[-1][1]
    durs = [d for d in (g.calculate_duration(b) for b in buses) if d]
    durs.sort()
    ops = [o for o in g.route_stats(buses)["operators"] if o not in ("", "—")]
    bt = [g.clean_text(b.get("bus_type") or "").lower() for b in buses]
    ac = sum(1 for x in bt if "ac" in x and "non" not in x)
    govt = sum(1 for x in bt if any(k in x for k in ("gov", "sbstc", "nbstc", "wbtc")))
    night = [b for b in buses if (lambda t: t is not None and (t >= 1200 or t < 300))(g.parse_time(b.get("departure_time")))]
    dawn = [b for b in buses if (lambda t: t is not None and 300 <= t < 600)(g.parse_time(b.get("departure_time")))]
    fares = sorted({g.clean_text(b.get("fare")) for b in buses if g.clean_text(b.get("fare"))})
    return {
        "count": len(buses),
        "first": times[0][0] if times else None,
        "last": times[-1][0] if times else None,
        "first_bus": first_bus,
        "last_bus": last_bus,
        "median": durs[len(durs) // 2] if durs else None,
        "fastest": durs[0] if durs else None,
        "slowest": durs[-1] if durs else None,
        "operators": ops[:6],
        "ac": ac,
        "govt": govt,
        "night": night,
        "dawn": dawn,
        "stops": g.stoppage_summary(buses),
        "fares": fares[:3],
    }


def faq_pairs(origin, destination, buses):
    f = faq_facts(origin, destination, buses)
    fb, lb = f["first_bus"], f["last_bus"]
    single = f["count"] == 1
    o, d = origin, destination
    ob, db = bnplace(origin), bnplace(destination)

    def bus_label(b):
        if b is None:
            return "the listed service"
        n = g.clean_text(b.get("bus_name")) or "the bus"
        op = g.operator_name(b)
        base = g.esc(n)
        return base + (f" ({g.esc(op)})" if op else "")

    def arr_of(b):
        return g.parse_time(b.get("arrival_time")) if b else None

    # ---------------- English (search-intent) ----------------
    en = []
    if f["first"] is not None:
        a1 = f" It normally reaches {d} around {g.format_time(arr_of(fb))}." if arr_of(fb) is not None else ""
        en.append((
            f"What is the first bus from {o} to {d}?",
            f"The first bus listed leaves {o} at <b>{g.format_time(f['first'])}</b> — {bus_label(fb)}.{a1} Arrive a little early, as buses often depart once seats fill up.",
        ))
    else:
        en.append((
            f"What is the bus timing from {o} to {d}?",
            f"Individual departure times are not listed for this route yet. The stops shown above give the route path — confirm current timings at the stand or with the operator before travelling.",
        ))
    if single:
        dep_bit = f", departing at {g.format_time(f['first'])}" if f["first"] is not None else ""
        en.append((
            f"How many buses run from {o} to {d}?",
            f"<b>1 bus is listed</b> on BusJatri for this route{dep_bit} ({bus_label(fb)}). Our timetable shows what sources have reported — more services may exist, so ask at the stand if you need a later option.",
        ))
    elif f["last"] is not None:
        en.append((
            f"What is the last bus from {o} to {d}?",
            f"The last departure listed is at <b>{g.format_time(f['last'])}</b> — {bus_label(lb)}. No later direct bus is listed on BusJatri for the same day, so plan accordingly.",
        ))
    if f["median"] is not None:
        extra = f" The fastest service takes about {g.fmt_duration(f['fastest'])}, while slower ones can take up to {g.fmt_duration(f['slowest'])}." if f["slowest"] != f["fastest"] else ""
        en.append((
            f"How long does the {o} to {d} bus journey take?",
            f"Most listed buses cover this route in about <b>{g.fmt_duration(f['median'])}</b>.{extra} Actual time depends on stops, traffic and the season.",
        ))
    if f["operators"]:
        ops_txt = ", ".join(g.esc(x) for x in f["operators"][:4])
        kind = []
        if f["govt"]:
            kind.append(f"{f['govt']} government" + (" service" if f["govt"] == 1 else " services"))
        priv = f["count"] - f["govt"]
        if priv > 0:
            kind.append(f"{priv} private" + (" service" if priv == 1 else " services"))
        kind_txt = (" — roughly " + " and ".join(kind)) if kind else ""
        ac_txt = f" AC coaches are also listed on this route." if f["ac"] else ""
        en.append((
            f"Which operators run buses from {o} to {d}?",
            f"Services listed on this route include {ops_txt}{kind_txt}.{ac_txt}",
        ))
    if f["first"] is not None and not single:
        am = sum(1 for b in buses if (lambda t: t is not None and t < 720)(g.parse_time(b.get("departure_time"))))
        pm = f["count"] - am
        if am and pm:
            spread = f" — {am} in the morning and {pm} later in the day"
        else:
            spread = ""
        en.append((
            f"How many buses run from {o} to {d}?",
            f"<b>{f['count']} buses are listed</b> for this route on BusJatri, spread from {g.format_time(f['first'])} to {g.format_time(f['last'])}{spread}. More services may exist beyond what is listed.",
        ))

    # ---------------- Bengali (search-intent, different questions) ----
    bn = []
    if f["first"] is not None:
        a1 = f" {db}-এ পৌঁছায় প্রায় {bn_time(arr_of(fb))}।" if arr_of(fb) is not None else ""
        bn.append((
            f"{ob} থেকে {db} প্রথম বাস কখন ছাড়ে?",
            f"তালিকা অনুযায়ী প্রথম বাস ছাড়ে <b>{bn_time(f['first'])}</b> — {bus_label(fb)}।{a1} সিটের জন্য একটু আগে গিয়ে অপেক্ষা করাই ভালো।",
        ))
    else:
        bn.append((
            f"{ob} থেকে {db} বাস কখন কখন ছাড়ে?",
            f"এই রুটের আলাদা আলাদা ছাড়ার সময় এখনো তালিকাভুক্ত হয়নি। উপরের রুট স্টপগুলো দেখে পথটা বুঝে নিন এবং যাত্রার আগে স্ট্যান্ডে বা অপারেটরের কাছে সময় জেনে নিন।",
        ))
    if single:
        dep_bit = f", ছাড়ে {bn_time(f['first'])}" if f["first"] is not None else ""
        bn.append((
            f"{ob} থেকে {db} দিনে কতটি বাস চলে?",
            f"BusJatri-র তালিকায় এই রুটে এখন <b>একটি বাস</b> আছে{dep_bit} ({bus_label(fb)})। যা জানা গেছে তাই তালিকায় — আরও বাস থাকতে পারে, তাই পরে যেতে চাইলে স্ট্যান্ডে একবার জেনে নিন।",
        ))
    elif f["last"] is not None:
        bn.append((
            f"{ob} থেকে {db} দিনের শেষ বাস কতক্ষণে?",
            f"তালিকায় দিনের শেষ বাস ছাড়ে <b>{bn_time(f['last'])}</b> — {bus_label(lb)}। এর পরে ওই দিনের জন্য আর কোনো সরাসরি বাস তালিকাভুক্ত নেই, তাই ফেরার পরিকল্পনা সেই অনুযায়ী করুন।",
        ))
    if f["median"] is not None:
        extra = f" দ্রুততম বাসে প্রায় {bn_dur(f['fastest'])}, আর ধীরগতির বাসে {bn_dur(f['slowest'])} পর্যন্ত লাগতে পারে।" if f["slowest"] != f["fastest"] else ""
        bn.append((
            f"{ob} থেকে {db} যেতে কত সময় লাগে?",
            f"সাধারণত <b>{bn_dur(f['median'])}</b> সময় লাগে।{extra} স্টপ, রাস্তার ভিড় আর ঋতু বুঝে সময় একটু আগে-পরে হয়।",
        ))
    if f["night"]:
        times_txt = " ও ".join(bn_time(g.parse_time(b.get("departure_time"))) for b in f["night"][:4])
        bn.append((
            f"{ob} থেকে {db} রাতের বা ভোরের বাস আছে কি?",
            f"হ্যাঁ — তালিকায় {bn_num(len(f['night']))}টি বাস রাতে বা ভোরে ছাড়ে ({times_txt})। রাতের যাত্রায় আগে থেকে সিট নিশ্চিত করে নিন।",
        ))
    elif f["dawn"]:
        times_txt = " ও ".join(bn_time(g.parse_time(b.get("departure_time"))) for b in f["dawn"][:4])
        bn.append((
            f"{ob} থেকে {db} ভোরের বাস পাওয়া যায়?",
            f"হ্যাঁ — ভোর থেকে সকালের মধ্যে {bn_num(len(f['dawn']))}টি বাস ছাড়ে ({times_txt})। তাড়াতাড়ি পৌঁছাতে চাইলে এগুলোই ভালো বিকল্প।",
        ))
    else:
        first_t = bn_time(f["first"]) if f["first"] is not None else "নির্দিষ্ট সময়ে"
        bn.append((
            f"{ob} থেকে {db} বাসের সময়সূচি কেমন?",
            f"উপরের সময়সূচিতে এই রুটের তালিকাভুক্ত বাসগুলোর ছাড়ার সময় দেওয়া আছে, দিনের প্রথম বাস {first_t}-এ ছাড়ে। ভিড় বা ঋতু বুঝে সময় একটু আগে-পরে হতে পারে, তাই যাত্রার আগে একবার যাচাই করে নিন।",
        ))
    if f["stops"]:
        stops_txt = ", ".join(g.esc(bnplace(s)) for s in f["stops"][:6])
        bn.append((
            f"{ob} থেকে {db} বাসের রুট কোথা দিয়ে যায়?",
            f"তালিকাভুক্ত বাসগুলোর পথের মূল স্টপ: {stops_txt}। নামতে চাইলে কন্ডাক্টরকে আগেই বলে রাখুন, যাতে স্টপে গাড়ি দাঁড়ায়।",
        ))
    else:
        bn.append((
            f"{ob} থেকে {db} AC বাস আছে কি?",
            (f"হ্যাঁ — তালিকায় {bn_num(f['ac'])}টি AC বাস আছে। আরামদায়ক যাত্রার জন্য সেগুলোই বেছে নিতে পারেন।" if f["ac"] else f"তালিকায় এই রুটে আপাতত কোনো AC বাস দেখা যায়নি — সাধারণ সিটার বাসই চলে। স্ট্যান্ডে জেনে নিলে নতুন কোনো AC সার্ভিস বের হলে জানা যাবে।"),
        ))

    # ---- pad to EXACTLY 5 EN + 5 BN (site rule) with search-intent fallbacks ----
    def _pad(lst, pool, cap=5):
        for q, a in pool:
            if len(lst) >= cap:
                break
            if any(q == x[0] for x in lst):
                continue
            lst.append((q, a))
        return lst[:cap]

    en_pool = [
        (f"How much does the {o} to {d} bus ticket cost?",
         (f"Listed fares for this route: <b>{', '.join(g.esc(x) for x in f['fares'])}</b>." if f["fares"] else "Fares are not listed for this route yet.")
         + " Bus fares in West Bengal depend on distance and bus type (AC costs more) — confirm the exact amount with the conductor or operator."),
        (f"What route do buses take from {o} to {d}?",
         f"The main stops on the way are shown above. Ask the conductor for your exact drop point before boarding — most buses stop on request at major stands."),
        (f"Is there an AC bus from {o} to {d}?",
         (f"Yes — {f['ac']} AC bus" + (" is" if f['ac'] == 1 else "es are") + " listed on this route." if f["ac"] else "No AC bus is listed on this route at the moment — regular seater buses run here. Check at the stand for any newer AC service.")
         + " AC coaches are more common on long-distance routes."),
        (f"Are there night buses from {o} to {d}?",
         "See the timetable above for evening and early-morning departures — the departure times listed show which buses run after dark. For late-night travel, confirm the last departure at the stand on the day you travel."),
    ]
    bn_pool = [
        (f"{ob} থেকে {db} বাসের ভাড়া কত?",
         (f"তালিকাভুক্ত ভাড়া: <b>{', '.join(g.esc(x) for x in f['fares'])}</b>।" if f["fares"] else "এই রুটের ভাড়া এখনো তালিকাভুক্ত হয়নি।")
         + " দূরত্ব আর বাসের ধরন বুঝে ভাড়া হয় (AC বাসে বেশি) — সঠিক টাকা কন্ডাক্টরের কাছে জেনে নিন।"),
        (f"{ob} থেকে {db} বাসের রুট কোথা দিয়ে যায়?",
         f"পথের মূল স্টপগুলো উপরে দেওয়া আছে। ওঠার আগে নামার জায়গাটা কন্ডাক্টরকে বলে রাখুন — বেশিরভাগ বাস বড় স্ট্যান্ডে থামে।"),
        (f"{ob} থেকে {db} AC বাস আছে কি?",
         (f"হ্যাঁ — তালিকায় {bn_num(f['ac'])}টি AC বাস আছে।" if f["ac"] else "আপাতত তালিকায় কোনো AC বাস নেই — সাধারণ সিটার বাসই চলে। স্ট্যান্ডে জেনে নিলে নতুন কোনো AC সার্ভিসের খবর পাওয়া যাবে।")
         + " লম্বা দূরত্বের রুটে AC বাস বেশি দেখা যায়।"),
        (f"{ob} থেকে {db} রাতের বাস পাওয়া যায় কি?",
         "উপরের সময়সূচিতে সন্ধে ও ভোরের ছাড়ার সময়গুলো দেখুন — কোন বাস অন্ধকার হওয়ার পরে ছাড়ে বোঝা যাবে। দেরি করে যেতে হলে সেদিন স্ট্যান্ডে গিয়ে শেষ বাসের সময়টা আরেকবার জেনে নিন।"),
    ]
    return _pad(en, en_pool), _pad(bn, bn_pool), f


def faq_html_v2(en, bn):
    def det(q, a, cls, i):
        return f'<details class="{cls}"{" open" if i == 0 else ""}><summary>{q}</summary><div class="fa-body">{a}</div></details>'

    parts = [det(q, a, "faq only-en", i) for i, (q, a) in enumerate(en)]
    parts += [det(q, a, "faq only-bn", i) for i, (q, a) in enumerate(bn)]
    return "".join(parts)

# ------------------------------------------------------------
# v2 shell / header / footer
# ------------------------------------------------------------

MOON_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z"/></svg>'


def header_html_v2():
    return f"""<header class="header">
  <div class="container header-inner">
    <a href="../index.html" class="logo" aria-label="BusJatri home">
      <svg class="icon" viewBox="0 0 24 24" style="width:1.3rem;height:1.3rem;color:var(--amber)" aria-hidden="true"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M4 16h16" fill="none" stroke="currentColor" stroke-width="2"/></svg>
      Bus<span>Jatri</span>
    </a>
    <div class="hdr-ctrl">
      <div class="lang-switch" role="group" aria-label="Language">
        <button type="button" id="langEn" class="pill pill-en on">EN</button>
        <button type="button" id="langBn" class="pill pill-bn">বাংলা</button>
      </div>
      <button type="button" id="themeBtn" class="theme-btn" aria-label="Toggle dark mode">{MOON_SVG}</button>
    </div>
  </div>
</header>"""


def footer_html_v2():
    return """<footer class="footer">
  <div class="container">
    <div class="footer-links">
      <a href="../index.html">Home</a>
      <a href="./">All Bus Timetables</a>
      <a href="../blog/index.html">Blog</a>
      <a href="../contribute.html">Contribute a Bus</a>
      <a href="../about.html">About Us</a>
      <a href="../contact.html">Contact Us</a>
      <a href="../privacy-policy.html">Privacy Policy</a>
    </div>
    <p><strong>BusJatri</strong> — West Bengal Bus Timetable<br>
    Not affiliated with any transport corporation<br>
    Contact: <a href="mailto:busjatri@zohomail.in">busjatri@zohomail.in</a></p>
  </div>
</footer>"""


def shell_v2(title, description, canonical, body, schema=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{g.esc(title)}</title>
<meta name="description" content="{g.esc(description)}">
<link rel="canonical" href="{g.esc(canonical)}">
<meta property="og:title" content="{g.esc(title)}">
<meta property="og:description" content="{g.esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{g.esc(canonical)}">
<meta property="og:image" content="https://busjatri.in/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{g.esc(title)}">
<meta name="twitter:description" content="{g.esc(description)}">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700;9..144,800&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Bengali:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../css/seo.css?v=rt20260920">
<link rel="stylesheet" href="../css/seo-v2.css?v={CSS_V2}">
{schema}
</head>
<body>
{header_html_v2()}
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:860px">
{body}
</main>
{footer_html_v2()}
<script defer src="../js/seo-page.js?v={JS_V2}"></script>
<script defer src="../js/route-slider.js"></script>
</body>
</html>"""


# ------------------------------------------------------------
# bilingual bus card (label spans only — layout untouched)
# ------------------------------------------------------------

def bus_card_v2(bus, dep_min=None, arr_min=None, via=None):
    name = g.clean_text(bus.get("bus_name")) or "Bus service"
    if dep_min is not None:
        dep = g.format_time(dep_min)
        duration = None
        if arr_min is not None:
            duration = arr_min - dep_min
            if duration < 0:
                duration += 1440
            if duration > 720:
                # down-direction stop times can pair up nonsense journeys;
                # keep the departure + route, drop the arrival/duration
                duration = None
                arr_min = None
        arr = g.format_time(arr_min)
    else:
        dep = g.format_time(g.parse_time(bus.get("departure_time")))
        arr = g.format_time(g.parse_time(bus.get("arrival_time")))
        duration = g.calculate_duration(bus)
    operator = g.operator_name(bus)
    stops = g.total_stops(bus)
    dur_text = g.fmt_duration(duration) if duration else "—"
    fare = g.clean_text(bus.get("fare")) or "—"
    bid = bus.get("id") or ""
    bt_raw = (bus.get("bus_type") or "").lower()
    if "gov" in bt_raw or "sbstc" in bt_raw or "nbstc" in bt_raw or "wbtc" in bt_raw:
        badge = f'<span class="badge badge-govt">{L("Govt", "সরকারি")}</span>'
    elif "ac" in bt_raw and "non" not in bt_raw:
        badge = '<span class="badge badge-ac">AC</span>'
    else:
        badge = f'<span class="badge badge-priv">{L("Private", "বেসরকারি")}</span>'
    op_line = g.esc(name)
    if operator:
        op_line += f' · {g.esc(operator)}'
    if via:
        op_line += f' <span style="color:var(--amber-ink,#6b4610);font-weight:600">· {g.esc(via)}</span>'
    clock = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'
    if dep == "—":
        dep_html = f'{clock}<span class="no-time">{L("Time N/A", "সময় নেই")}</span>'
    else:
        small = f'<small>{g.esc(arr)} {L("arr", "পৌঁছায়")}</small>' if arr != "—" else ""
        dep_html = f'{clock}<div class="depcol"><span class="dep-t">{g.esc(dep)}</span>{small}</div>'
    meta_bits = []
    if fare != "—":
        meta_bits.append(f'<span class="fare">{g.esc(fare)}</span>')
    meta_bits.append(f'⏱ ~{g.esc(dur_text)}')
    meta_bits.append(f'🚏 {stops or 0} {L("stops", "স্টপ")}')
    link = ""
    if bid:
        link = f'<a class="bd-link" href="../index.html#/bus/{g.esc(bid)}" aria-label="View full timetable for {g.esc(name)}">{L("Details ›", "বিস্তারিত ›")}</a>'
    return f"""<div class="bus-row">
  <div class="dep">{dep_html}</div>
  <div class="bmid">
    <div class="op">{op_line}</div>
    <div class="mrow">{' · '.join(meta_bits)}</div>
  </div>
  <div class="bright">{badge}{link}</div>
</div>"""


# ------------------------------------------------------------
# route page v2
# ------------------------------------------------------------

def generate_route_page_v2(origin, destination, buses, alt_index):
    filename = f"{g.slug(origin)}-to-{g.slug(destination)}.html"
    route_bn = g.bn_route(origin, destination)
    # through buses (pass both places as stops) — homepage search parity
    through = through_services(origin, destination, buses, alt_index)
    faq_buses = list(buses)
    for _sk, bus, d, a in through:
        vb = dict(bus)
        if d is not None and a is not None and ((a - d) % 1440) > 720:
            a = None
        if d is not None:
            vb["departure_time"] = g.format_time(d)
        vb["arrival_time"] = g.format_time(a) if a is not None else ""
        faq_buses.append(vb)
    stats = g.route_stats(faq_buses)
    first = g.format_time(stats["first"])
    last = g.format_time(stats["last"])
    duration = stats["duration"]
    operators = stats["operators"]
    count = len(faq_buses)
    dur_text = g.fmt_duration(duration) if duration else "—"

    title = f"{origin} to {destination} Bus Time Table | {g.SITE_NAME}"
    ops = [o for o in operators if o and o.strip() and o.strip() not in ("—", "-")][:3]
    run_by = (" Run by " + ", ".join(ops) + ".") if ops else ""
    if stats["first"] is None:
        description = f"{origin} to {destination} bus time table with routes, stoppages and operators on {g.SITE_NAME}."[:300]
    elif count == 1:
        description = f"{origin} to {destination} bus time table — 1 bus listed, departing at {first}.{run_by} Timings and stoppages on {g.SITE_NAME}."[:300]
    else:
        description = f"{origin} to {destination} bus time table — {count} buses listed, first {first}, last {last}.{run_by} Timings and stoppages on {g.SITE_NAME}."[:300]
    canonical = f"{g.BASE}/bus-time-table/{filename}"

    # ---- hero (safe wording: what is LISTED) ----
    if count == 1:
        chips = (
            f'<span class="schip">🚌 {L("1 bus listed", "১টি বাস তালিকাভুক্ত")}</span>'
            + (f'<span class="schip hot">⏰ {L("Departs", "ছাড়ে")} {g.esc(first)}</span>' if stats["first"] is not None else "")
            + (f'<span class="schip">⏱ ~{g.esc(dur_text)}</span>' if stats["duration"] is not None else "")
        )
    else:
        chips = (
            f'<span class="schip">🚌 {count} {L("buses listed", "বাস তালিকাভুক্ত")}</span>'
            + (f'<span class="schip hot">⏰ {L("First", "প্রথম")} {g.esc(first)}</span>' if stats["first"] is not None else "")
            + (f'<span class="schip">⏰ {L("Last", "শেষ")} {g.esc(last)}</span>' if stats["last"] is not None else "")
            + (f'<span class="schip">⏱ ~{g.esc(dur_text)}</span>' if stats["duration"] is not None else "")
        )
    bn_sub = f'<p class="bn-sub"><span class="label-en">{g.esc(origin)} → {g.esc(destination)} — bus timings & stoppages</span><span class="label-bn">{g.esc(route_bn)} বাসের সময়সূচী</span></p>' if route_bn else ""
    hero = f"""<div class="crumbs"><a href="../index.html">{L("Home", "হোম")}</a> › <a href="./">{L("Bus Timetable", "বাস টাইম টেবিল")}</a> › <span>{g.esc(origin)} → {g.esc(destination)}</span></div>
<div class="seo-hero">
  <h1>{g.esc(origin)} <span class="arr">→</span> {g.esc(destination)}</h1>
  {bn_sub}
  <div class="stat-chips">{chips}</div>
</div>"""

    entries = []
    for b in buses:
        entries.append((g.parse_time(b.get("departure_time")) or 9999, bus_card_v2(b)))
    for _sk, bus, d, a in through:
        via = f"{g.clean_text(bus.get('origin'))} → {g.clean_text(bus.get('destination'))}"
        entries.append((d if d is not None else 9999, bus_card_v2(bus, dep_min=d, arr_min=a, via=via)))
    entries.sort(key=lambda e: e[0])
    timetable = f"""<section class="seo-section">
  <h3 class="section-title">{L("Today's Departures", "আজকের ছাড়ার সময়")}</h3>
  {''.join(card for _k, card in entries)}
</section>"""

    # ---- alt-route section (below bus list) ----
    alt_section = alt_route_section(origin, destination, alt_index)

    map_buses = list(buses) + [tb for _sk, tb, _d, _a in through]
    route_section = g.route_stops_html(map_buses, origin, destination)

    major_stops = g.stoppage_summary(map_buses)
    major_section = ""
    if major_stops:
        chips2 = "".join(f'<span class="via-chip">{g.esc(s)}</span>' for s in major_stops)
        major_section = f"""<section class="seo-section">
  <h3 class="section-title">{L("Via Stoppages", "মাঝপথের স্টপ")}</h3>
  <div class="chip-row hscroll">{chips2}</div>
</section>"""

    # ---- FAQ 5 EN + 5 BN (search-intent) ----
    en, bn, _facts = faq_pairs(origin, destination, faq_buses)
    faq_section = f"""<section class="seo-section faq-v2">
  <h3 class="section-title">{L("FAQs", "সাধারণ প্রশ্ন")}</h3>
  {faq_html_v2(en, bn)}
</section>"""

    related = [(o, t) for (o, t) in g.route_meta if o == origin and t != destination]
    related = sorted(related, key=lambda p: -len(g.route_meta[p]))[:8]
    related_section = ""
    if related:
        links = "".join(
            f'<a class="rel-chip" href="{g.slug(o)}-to-{g.slug(t)}.html">{g.esc(o)} → {g.esc(t)}</a>'
            for o, t in related
        )
        related_section = f"""<section class="seo-section">
  <h3 class="section-title">{L("More Routes from " + g.esc(origin), g.esc(bnplace(origin)) + " থেকে আরও রুট")}</h3>
  <div class="chip-row">{links}</div>
</section>"""

    reverse_section = ""
    if (destination, origin) in g.route_meta:
        rev_file = f"{g.slug(destination)}-to-{g.slug(origin)}.html"
        reverse_section = f"""<section class="seo-section">
  <a class="rel-chip" href="{rev_file}">↩ {g.esc(destination)} → {g.esc(origin)} ({L("return", "ফেরার বাস")})</a>
</section>"""

    body = hero + timetable + alt_section + route_section + major_section + faq_section + reverse_section + related_section

    schema = (
        g.faq_schema(en + bn) + "\n"
        + g.breadcrumb_schema([
            ("Home", "/"),
            ("Bus Timetable", "/bus-time-table/"),
            (f"{origin} to {destination}", f"/bus-time-table/{filename}"),
        ])
    )
    return filename, shell_v2(title, description, canonical, body, schema)


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--routes", help="comma list of Origin::Destination")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry", action="store_true", help="report only, don't write")
    args = ap.parse_args()

    print(f"loaded {len(g.BUSES)} buses, {len(g.route_meta)} route pairs")

    alt_index = AltIndex(g.BUSES)

    if args.all:
        pairs = list(g.route_meta.items())
    else:
        wanted = []
        for item in (args.routes or "").split(","):
            item = item.strip()
            if not item:
                continue
            if "::" not in item:
                print(f"SKIP (no ::): {item}")
                continue
            o, d = [x.strip() for x in item.split("::", 1)]
            found = None
            for (ro, rd) in g.route_meta:
                if ro.lower() == o.lower() and rd.lower() == d.lower():
                    found = (ro, rd)
                    break
            if not found:
                print(f"SKIP (no route): {o} -> {d}")
                continue
            wanted.append(found)
        pairs = [(p, g.route_meta[p]) for p in wanted]

    n_alt = 0
    for (origin, destination), buses in pairs:
        filename, page = generate_route_page_v2(origin, destination, buses, alt_index)
        has_alt = "alt-card" in page
        n_alt += 1 if has_alt else 0
        n_faq = page.count("<details")
        status = f"alt={'Y' if has_alt else 'N'} faq={n_faq}"
        print(f"{filename}: {len(buses)} buses, {status}")
        if not args.dry:
            with open(os.path.join(g.OUT, filename), "w", encoding="utf-8") as fh:
                fh.write(page)

    print(f"\ndone: {len(pairs)} pages, {n_alt} with alternative-route section")


if __name__ == "__main__":
    main()
