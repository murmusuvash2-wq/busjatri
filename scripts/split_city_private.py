#!/usr/bin/env python3
"""Split the Kolkata city hub page (kolkata-city-bus-timetable.html).

Removes the long 428-row "Private Bus Routes - Kolkata" LIST, keeps the
73 WBTC city routes plus the Kolkata/Howrah-area private routes searchable
on the page, and drops the non-Kolkata private routes (they belong in the
normal All-Bus search flow, not on the Kolkata city page).

Idempotent: running it again on an already-split page is a no-op.

Usage:  python3 scripts/split_city_private.py [--write]
"""
import json
import pathlib
import re
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
PAGE = BASE / "kolkata-city-bus-timetable.html"

# Kolkata / Howrah METRO places -> a private route touching any of these
# stays searchable on the Kolkata city page.
KEEP = set("""58 gate ahiritola airport gate 1 airport terminal akra bazar akra fatak alipore zoo aliah university
amity university amtala andul station aquatica b garden babughat badartala bagbazar baghajatin baguiati
baisnabghata bakultala ballyhalt ballykhal bandha ghat bangur avenue bansdroni barasat chapadali barisha
barrackpore chiria barrackpore court barrackpore station baruipur batanagar bbd bag behala 14 no beleghata building
belgharia rathtala belgharia station belurmath bichali ghat birati tantkal bnr hospital boalghata
bonhooghly bt college burul chaital ghat chetla park chingrighata cossipore dakghar dakshineswar danesh shaikh lane
dasnagar derozio college dhakuria dhulagarh dumdum canton dumdum cantonment dumurjola dunlop ecospace esplanade
fishery gate garia bus stand garia metro garia station ghatakpukur golf green golpark greenfield city high court
howrah fire station howrah maidan howrah station jangalpur joyrampur julpia kadamtala kamalgazi kamarhati
karunamoyee kolkata station kona kudghat laketown layalka mahamayatala mahishbathan mandirtala milk colony moonbeam
muchighata mukundapur nabanna nager bazar nayabad netaji nagar new alipore newtown nimta bazar noapara paikpara
palbazar pardankuni park circus parnasree picnic garden rajarhat rajabazar ramnagar ramrajatala rashbehari ruby
ruiya purbapara sakher bazar saltlake 206 santragachi science city sealdah sector v shalimar station shapoorji
shibpur td shyambazar sinthi sm nagar sodepur girja suryasen nagar taratala thakurpukur tikiapara tollygunge metro
topsia ultadanga unitech gate 1 unitech gate 2 uttar ramnagar vip bazar""".split())

# the extra stat chip added next to the WBTC one
PRIVATE_CHIP = (
    '<span class="schip">' + chr(0x1F690) + ' 254 '
    '<span class="label-en">private routes (searchable)</span>'
    '<span class="label-bn">\u09ac\u09c7\u09b8\u09b0\u0995\u09be\u09b0\u09bf \u09b0\u09c1\u099f '
    '(\u09b8\u09be\u09b0\u09cd\u099a\u09af\u09cb\u0997\u09cd\u09af)</span></span>\n      '
)


def nrm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def is_keep(p):
    p = nrm(p)
    return bool(p) and (p in KEEP or p.split()[0] in KEEP)


def main():
    write = "--write" in sys.argv
    h = PAGE.read_text(encoding="utf-8")

    if "Private Bus Routes" not in h and 'id="pvtGrid"' not in h:
        print("already split - nothing to do")
        return

    # 1. filter the ROUTES array -------------------------------------------
    m = re.search(r'(var|const|let)\s+ROUTES\s*=\s*(\[.*?\]);', h, re.DOTALL)
    if not m:
        sys.exit("ROUTES array not found")
    arr = json.loads(m.group(2))
    city = [r for r in arr if not r.get("pvt")]
    pvt = [r for r in arr if r.get("pvt")]
    keep = [r for r in pvt if is_keep(r.get("a")) or is_keep(r.get("b"))]
    drop = [r for r in pvt if not (is_keep(r.get("a")) or is_keep(r.get("b")))]
    print("ROUTES %d = city %d + pvt %d -> keep %d / drop %d" % (len(arr), len(city), len(pvt), len(keep), len(drop)))
    h = h[:m.start(2)] + json.dumps(city + keep, ensure_ascii=False, separators=(",", ":")) + h[m.end(2):]

    # 2. remove the private LIST section -----------------------------------
    i = h.find("Private Bus Routes")
    if i != -1:
        s = h.rfind("<section", 0, i)
        e = h.find("</section>", i) + len("</section>")
        while s > 0 and h[s - 1] in " \n":
            s -= 1
        print("removing private section (%d bytes)" % (e - s))
        h = h[:s] + h[e:]

    # 3. text / chip updates ------------------------------------------------
    reps = [
        ("This page also lists <b>428 private city bus routes</b> with their departure and arrival stands.",
         "Private city buses on Kolkata corridors are also <b>searchable</b> above (by route number, from-to or stoppage)."),
        ('503 <span class="label-en">routes</span>',
         '73 <span class="label-en">WBTC routes</span>'),
    ]
    for a, b in reps:
        if a in h:
            h = h.replace(a, b, 1)
            print("replaced:", a[:45])
        else:
            print("warn: not found:", a[:55])
    if '<span class="schip hot">' in h and PRIVATE_CHIP not in h:
        h = h.replace('<span class="schip hot">', PRIVATE_CHIP + '<span class="schip hot">', 1)
        print("private chip added")

    assert 'id="pvtGrid"' not in h and 'class="badge badge-priv"' not in h, "private markup left behind"
    if write:
        PAGE.write_text(h, encoding="utf-8")
        print("wrote %s: %d bytes" % (PAGE.name, len(h)))
    else:
        print("[dry-run] would write %d bytes (use --write)" % len(h))


if __name__ == "__main__":
    main()
