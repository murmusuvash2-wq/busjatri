#!/usr/bin/env python3
"""
Stand page generator v2 — "Buses from X" pages (bus stand display board).

Demo-approved design (2026-09-22, Khatra demo). Layers on gen_route_v2
(same shell, header pills, dark mode, bus cards, FAQ style):

  1. Hero: "Buses from X" + Bengali subtitle + stat chips
     (buses listed / destinations / first / last)
  2. Departure board: every bus STARTING from the stand, time-sorted,
     same bilingual bus-row cards as route pages, destination shown
     as an amber "to <dest>" label
  3. All Destinations from X: compact chips "Dest (n)" linking to the
     route page (which carries through-services + alt routes)
  4. FAQ: 5 English + 5 Bengali search-intent questions, data-driven
  5. Safe wording: "N buses listed", never "only N buses run";
     more services may exist — ask at the stand

Origin matching uses the same strict matcher + alias groups as the
homepage search (buses-from-kolkata also lists buses whose origin is
Esplanade/Howrah — homepage parity). Stop-passing buses are NOT on the
board (route pages carry them) — the note under the board says so.

Usage (run from repo root):
  python3 scripts/gen_stand_v2.py --stands "Kolkata,Digha,Khatra"
  python3 scripts/gen_stand_v2.py --all

Writes bus-time-table/buses-from-<slug>.html (same URL as before —
design change only, no page moves, no deletions).
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_route_v2 as v2

g = v2.g


# ------------------------------------------------------------
# stand discovery + bus list
# ------------------------------------------------------------

def stand_buses(stand):
    """Buses whose ORIGIN matches the stand (strict matcher + aliases,
    same as the homepage 'from' side). Stop-passing buses are not here."""
    return [b for b in g.BUSES if v2.place_matches_strict(b.get("origin"), stand)]


def discover_stands():
    """(display_name, filename) for every existing buses-from-*.html."""
    out = []
    for fname in sorted(os.listdir(g.OUT)):
        if not fname.startswith("buses-from-") or not fname.endswith(".html"):
            continue
        try:
            with open(os.path.join(g.OUT, fname), "r", encoding="utf-8", errors="ignore") as fh:
                head = fh.read(4000)
        except OSError:
            continue
        m = re.search(r"<title>Buses from (.*?)\s*[–\-]", head)
        name = m.group(1).strip() if m and m.group(1).strip() else fname[len("buses-from-"):-len(".html")].replace("-", " ").title()
        out.append((name, fname))
    return out


# ------------------------------------------------------------
# destination grouping (merge alias names onto one route page chip)
# ------------------------------------------------------------

def destination_groups(stand, buses):
    """[(display_name, count, route_file_or_None)] sorted by count desc.

    Each bus destination is resolved against the stand's route_meta pairs
    so 'Kolkata (Esplanade)' and 'Kolkata' merge into one chip that links
    to the real route page."""
    routes = [t for (o, t) in g.route_meta if v2.place_matches_strict(o, stand)]
    groups = {}
    for b in buses:
        d = g.clean_text(b.get("destination")) or "?"
        resolved = None
        for t in routes:
            if v2.place_matches_strict(t, d) or v2.place_matches_strict(d, t):
                resolved = t
                break
        if resolved is not None:
            key = "file::" + g.slug(stand) + "-to-" + g.slug(resolved) + ".html"
            display = resolved
            link = f"{g.slug(stand)}-to-{g.slug(resolved)}.html"
        else:
            key = "name::" + d.lower()
            display = d
            link = None
        if key not in groups:
            groups[key] = [display, 0, link]
        groups[key][1] += 1
    out = [(display, count, link) for display, count, link in groups.values()]
    out.sort(key=lambda x: (-x[1], x[0]))
    return out


# ------------------------------------------------------------
# FAQ — 5 EN + 5 BN, search-intent questions, data-driven answers
# ------------------------------------------------------------

def faq_pairs_stand(stand, buses, dest_groups):
    stats = g.route_stats(buses)
    first = stats["first"]
    last = stats["last"]
    count = len(buses)
    operators = [o for o in stats["operators"] if o and o.strip() and o.strip() not in ("—", "-")]
    top = [d for d, _c, _l in dest_groups[:8]]

    def bus_at(minutes):
        best, best_bus = None, None
        for b in buses:
            t = g.parse_time(b.get("departure_time"))
            if t is None:
                continue
            if minutes is None or abs(t - minutes) < abs((best if best is not None else 99999) - minutes):
                best, best_bus = t, b
        return best_bus

    first_bus = bus_at(first) if first is not None else None
    last_bus = bus_at(last) if last is not None else None
    p_bn = v2.bnplace(stand)

    def dest_of(b):
        return g.clean_text(b.get("destination")) or "its destination"

    en, bn = [], []

    if count == 0:
        en = [
            ("Are there any buses from {}?".format(stand),
             "No bus services from {} are listed yet. More services may exist — ask at the stand, or check the route pages for nearby places.".format(stand)),
            ("How do I check bus timings from {}?".format(stand),
             "You can search any route from {} on the homepage, or open the route page for your destination — it lists every departure with stoppages.".format(stand)),
            ("Which places are connected to {} by bus?".format(stand),
             "Nearby stands and destinations are shown on the Bus Timetable index. Ask at the stand for the latest connections.".format(stand)),
            ("Which operators run buses from {}?".format(stand),
             "No operator is listed for {} yet. If you know a bus, you can contribute it on the Contribute a Bus page.".format(stand)),
            ("Is there a bus timetable app for {} buses?".format(stand),
             "BusJatri works in any mobile browser — search your route and get timings, stoppages and operators without installing anything."),
        ]
        bn = [
            ("{} থেকে কি কোনো বাস আছে?".format(p_bn),
             "এখনও {} থেকে কোনো বাস তালিকাভুক্ত নেই। আরও বাস থাকতে পারে — স্ট্যান্ডে জেনে নিন, বা কাছের জায়গার রুট পেজ দেখুন।".format(p_bn)),
            ("{} থেকে বাসের সময় কীভাবে জানব?".format(p_bn),
             "হোমপেজে যেকোনো রুট সার্চ করুন, বা গন্তব্যের রুট পেজ খুলুন — সেখানে ছাড়ার সময় ও স্টপ দেওয়া থাকে।"),
            ("{} থেকে কোথায় কোথায় বাস যায়?".format(p_bn),
             "কাছের স্ট্যান্ড ও গন্তব্য বাস টাইম টেবিল ইনডেক্সে দেওয়া আছে। সাম্প্রতিক তথ্যের জন্য স্ট্যান্ডে জেনে নিন।"),
            ("{} থেকে কোন সংস্থার বাস চলে?".format(p_bn),
             "{} থেকে এখনও কোনো অপারেটর তালিকাভুক্ত নেই। বাসের খবর জানা থাকলে Contribute a Bus পেজ থেকে জানাতে পারেন।".format(p_bn)),
            ("{} বাসের সময়সূচি অ্যাপে পাওয়া যায়?".format(p_bn),
             "BusJatri যেকোনো মোবাইল ব্রাউজারে চলে — কিছু ইনস্টল না করেই রুট সার্চ করে সময়, স্টপ ও অপারেটর দেখা যায়।"),
        ]
        return en, bn

    # ---- timed pages ----
    en.append(("What is the first bus from {}?".format(stand),
               "The first departure listed from {} is at {} — {}, to {}. Arrive a little early, as buses often leave once seats fill up.".format(
                   stand, g.format_time(first), g.clean_text(first_bus.get("bus_name")) or "a bus service", dest_of(first_bus))))
    en.append(("What is the last bus from {}?".format(stand),
               "The last listed departure is {} — {}, to {}. More services may exist, so ask at the stand.".format(
                   g.format_time(last), g.clean_text(last_bus.get("bus_name")) or "a bus service", dest_of(last_bus))))
    en.append(("How many buses start from {} daily?".format(stand),
               "{} buses are listed starting from {}, serving {} destinations. More services may exist — ask at the stand.".format(count, stand, len(dest_groups))))
    if top:
        en.append(("Which places can I go from {} by bus?".format(stand),
                   "From {} you can travel to {} — the full destination list with bus counts is on this page.".format(
                       stand, ", ".join(top[:6]) + (" and others" if len(top) > 6 else ""))))
    else:
        en.append(("Where does the bus from {} go?".format(stand),
                   "Destinations from {} are shown on this page with bus counts.".format(stand)))
    if operators:
        en.append(("Which operators run buses from {}?".format(stand),
                   "Listed services include {}. Government (SBSTC/NBSTC/WBTC) and private buses both serve this stand.".format(
                       ", ".join(operators[:4]) + (" and others" if len(operators) > 4 else ""))))
    else:
        en.append(("Do government buses run from {}?".format(stand),
                   "Operator details are not listed for every service. Ask at the stand for the latest SBSTC/NBSTC/WBTC and private bus information."))
    while len(en) > 5:
        en.pop()

    bn.append(("{} থেকে প্রথম বাস কখন ছাড়ে?".format(p_bn),
               "তালিকা অনুযায়ী প্রথম বাস ছাড়ে {} — {}, {} যায়। সিটের জন্য একটু আগে গিয়ে অপেক্ষা করাই ভালো।".format(
                   v2.bn_time(first), g.clean_text(first_bus.get("bus_name")) or "একটি বাস", v2.bnplace(dest_of(first_bus)))))
    bn.append(("{} থেকে দিনের শেষ বাস কতক্ষণে?".format(p_bn),
               "তালিকায় শেষ বাস {} — {}, {} যায়। এর পরেও আরও বাস থাকতে পারে, স্ট্যান্ডে জেনে নিন।".format(
                   v2.bn_time(last), g.clean_text(last_bus.get("bus_name")) or "একটি বাস", v2.bnplace(dest_of(last_bus)))))
    bn.append(("{} থেকে দিনে কতটি বাস ছাড়ে?".format(p_bn),
               "তালিকায় {}টি বাস, {}টি গন্তব্যে। যা জানা গেছে তাই তালিকায় — আরও বাস থাকতে পারে, স্ট্যান্ডে জেনে নিন।".format(
                   v2.bn_num(count), v2.bn_num(len(dest_groups)))))
    if top:
        bn.append(("{} থেকে কোথায় কোথায় বাস যায়?".format(p_bn),
                   "{} থেকে যাওয়া যায় {} জায়গায় — বাসের সংখ্যাসহ পুরো তালিকা এই পেজেই দেওয়া আছে।".format(
                           p_bn, ", ".join(v2.bnplace(t) for t in top[:6]) + (" প্রভৃতি" if len(top) > 6 else ""))))
    else:
        bn.append(("{} থেকে বাস কোথায় যায়?".format(p_bn),
                   "{} থেকে যাওয়া গন্তব্যগুলি বাসের সংখ্যাসহ এই পেজে দেওয়া আছে।".format(p_bn)))
    if operators:
        bn.append(("{} থেকে কোন কোন সংস্থার বাস চলে?".format(p_bn),
                   "তালিকায় আছে {}। সরকারি (SBSTC/NBSTC/WBTC) ও বেসরকারি দুই ধরনের বাসই চলে।".format(
                       ", ".join(operators[:4]) + (" প্রভৃতি" if len(operators) > 4 else ""))))
    else:
        bn.append(("{} থেকে সরকারি বাস আছে?".format(p_bn),
                   "সব বাসের অপারেটর তালিকাভুক্ত নয়। সাম্প্রতিক SBSTC/NBSTC/WBTC ও বেসরকারি বাসের খবর স্ট্যান্ডে জেনে নিন।"))
    while len(bn) > 5:
        bn.pop()

    return en, bn


# ------------------------------------------------------------
# stand page v2
# ------------------------------------------------------------

def generate_stand_page_v2(stand):
    filename = "buses-from-{}.html".format(g.slug(stand))
    buses = stand_buses(stand)
    dest_groups = destination_groups(stand, buses)
    stats = g.route_stats(buses)
    first = stats["first"]
    last = stats["last"]
    count = len(buses)
    p_bn = v2.bnplace(stand)

    title = "Buses from {} – Time Table & Routes | বাস সময়সূচী | {}".format(stand, g.SITE_NAME)
    if count == 0:
        description = "Bus services from {} — destinations, operators and timetable information on {}.".format(stand, g.SITE_NAME)
    else:
        description = "Buses from {} — {} buses listed to {} destinations".format(stand, count, len(dest_groups))
        if first is not None:
            description += ", first {}, last {}".format(g.format_time(first), g.format_time(last))
        description += ". Departures, routes and operators on {}.".format(g.SITE_NAME)
    description = description[:300]
    canonical = "{}/bus-time-table/{}".format(g.BASE, filename)

    # ---- hero ----
    if count == 0:
        chips = '<span class="schip">🚌 {}</span>'.format(v2.L("No buses listed yet", "এখনও কোনো বাস তালিকাভুক্ত নেই"))
    else:
        chips = (
            '<span class="schip">🚌 {}</span>'.format(
                v2.L("{} buses listed".format(count), "{}টি বাস তালিকাভুক্ত".format(v2.bn_num(count)))
            )
            + '<span class="schip">📍 {}</span>'.format(
                v2.L("{} destinations".format(len(dest_groups)), "{}টি গন্তব্য".format(v2.bn_num(len(dest_groups))))
            )
            + ('<span class="schip hot">⏰ {} {}</span>'.format(v2.L("First", "প্রথম"), g.esc(g.format_time(first))) if first is not None else "")
            + ('<span class="schip">⏰ {} {}</span>'.format(v2.L("Last", "শেষ"), g.esc(g.format_time(last))) if last is not None else "")
        )
    hero = """<div class="crumbs"><a href="../index.html">{}</a> › <a href="./">{}</a> › <span>Buses from {}</span></div>
<div class="seo-hero">
  <h1>Buses from {}</h1>
  <p class="bn-sub">{} — ছাড়ার সময়সূচি</p>
  <div class="stat-chips">{}</div>
</div>""".format(
        v2.L("Home", "হোম"), v2.L("Bus Timetable", "বাস টাইম টেবিল"),
        g.esc(stand), g.esc(stand), g.esc(p_bn), chips,
    )

    # ---- departure board ----
    if count == 0:
        board = """<section class="seo-section">
  <h3 class="section-title">{}</h3>
  <p class="alt-note">{}</p>
</section>""".format(
            v2.L("No bus services listed yet", "এখনও কোনো বাস তালিকাভুক্ত নেই"),
            v2.L("No bus starting from {} is listed yet. Check the Bus Timetable index for nearby stands, or search your route on the homepage.".format(g.esc(stand)),
                 "এখনও {} থেকে ছাড়া কোনো বাস তালিকাভুক্ত নেই। কাছের স্ট্যান্ডের জন্য বাস টাইম টেবিল ইনডেক্স দেখুন, বা হোমপেজে রুট সার্চ করুন।".format(g.esc(p_bn))))
    else:
        entries = []
        for b in buses:
            dep = g.parse_time(b.get("departure_time")) or 9999
            dest = g.clean_text(b.get("destination")) or ""
            via = "to {}".format(dest) if dest else None
            entries.append((dep, v2.bus_card_v2(b, via=via)))
        entries.sort(key=lambda e: e[0])
        board = """<section class="seo-section">
  <h3 class="section-title">{}</h3>
  <p class="alt-note">{}</p>
  {}
</section>""".format(
            v2.L("Today's Departures from {}".format(g.esc(stand)), "আজ {} থেকে ছাড়বে".format(g.esc(p_bn))),
            v2.L("Only buses starting from {} are shown here — for buses that pass through, see the route pages. More services may exist, so ask at the stand.".format(g.esc(stand)),
                 "এখানে শুধু {} থেকে ছাড়া বাসগুলি দেখানো হয়েছে — মাঝপথের বাসের জন্য রুট পেজ দেখুন। আরও বাস থাকতে পারে, স্ট্যান্ডে জেনে নিন।".format(g.esc(p_bn))),
            "".join(card for _k, card in entries))

    # ---- destinations ----
    dest_section = ""
    if dest_groups:
        chips2 = []
        for display, c, link in dest_groups:
            inner = "{} <span>({})</span>".format(g.esc(display), c)
            if link:
                chips2.append('<a class="rel-chip" href="{}">{}</a>'.format(g.esc(link), inner))
            else:
                chips2.append('<span class="rel-chip">{}</span>'.format(inner))
        dest_section = """<section class="seo-section">
  <h3 class="section-title">{}</h3>
  <div class="chip-row">{}</div>
</section>""".format(
            v2.L("All Destinations from {}".format(g.esc(stand)), "{} থেকে সব গন্তব্য".format(g.esc(p_bn))),
            "".join(chips2))

    # ---- FAQ ----
    en, bn = faq_pairs_stand(stand, buses, dest_groups)
    faq_section = """<section class="seo-section faq-v2">
  <h3 class="section-title">FAQ · সাধারণ প্রশ্ন</h3>
  {}
</section>""".format(v2.faq_html_v2(en, bn))

    body = hero + board + dest_section + faq_section

    schema = (
        g.faq_schema(en + bn) + "\n"
        + g.breadcrumb_schema([
            ("Home", "/"),
            ("Bus Timetable", "/bus-time-table/"),
            ("Buses from {}".format(stand), "/bus-time-table/{}".format(filename)),
        ])
    )
    return filename, v2.shell_v2(title, description, canonical, body, schema)


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--stands", help="comma list of stand names, e.g. Kolkata,Digha,Khatra")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry", action="store_true", help="report only, don't write")
    args = ap.parse_args()

    known = discover_stands()
    print("loaded {} buses, {} existing stand pages".format(len(g.BUSES), len(known)))

    if args.all:
        targets = [(name, "buses-from-{}.html".format(g.slug(name))) for name, _f in known]
    else:
        wanted = [x.strip() for x in (args.stands or "").split(",") if x.strip()]
        by_slug = {g.slug(name): (name, fname) for name, fname in known}
        targets = []
        for w in wanted:
            hit = by_slug.get(g.slug(w))
            if not hit:
                print("SKIP (no existing stand page): {}".format(w))
                continue
            targets.append(hit)

    for stand, fname in targets:
        filename, page = generate_stand_page_v2(stand)
        assert filename == fname, "filename mismatch: {} != {}".format(filename, fname)
        n_faq = page.count("<details")
        n_rows = page.count('class="bus-row"')
        n_chips = page.count('class="rel-chip"') + page.count('class=\\"rel-chip\\"')
        print("{}: {} buses, {} rows, {} dest chips, faq={}".format(filename, len(stand_buses(stand)), n_rows, n_chips, n_faq))
        if not args.dry:
            with open(os.path.join(g.OUT, filename), "w", encoding="utf-8") as fh:
                fh.write(page)

    print("\ndone: {} stand pages".format(len(targets)))


if __name__ == "__main__":
    main()
