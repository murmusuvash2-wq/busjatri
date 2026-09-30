# SEO enrichment for /bus-time-table/cooch-behar-to-siliguri
# Target query family: "cooch behar to siliguri bus", "coach bihar to siliguri",
# "coochbehar to siliguri", "koch bihar to siliguri bus time table".
# Adds what competitors (nbstc.in, redBus, wbbustime) already show and Google
# expects on a #1 result: distance, duration, boarding/dropping points, fare
# guidance, and the common spelling variants of "Cooch Behar".
# Idempotent: safe to re-run. UTF-8 throughout.
import io
import json
import re
import sys

PAGE = "bus-time-table/cooch-behar-to-siliguri.html"

FAQ_NEW_EN = [
    (
        "How far is Cooch Behar from Siliguri, and how long does the bus take?",
        "The road distance from Cooch Behar to Siliguri is about 140 km via Falakata "
        "(about 125 km via the Mathabhanga route). A bus normally takes 3\u20134 hours "
        "depending on the route and stops.",
    ),
    (
        "Is it Cooch Behar, Coochbehar or Koch Bihar?",
        "All spellings refer to the same place \u2014 Cooch Behar district in north Bengal "
        "(Bengali: কোচবিহার). The railway station is New Cooch Behar (NCB). Whether you "
        "search cooch behar, coochbehar, koch bihar or coach bihar, this page lists every "
        "bus on the route.",
    ),
    (
        "Where do buses start in Cooch Behar and where do they drop in Siliguri?",
        "Most buses start from the Cooch Behar Central Bus Terminus (some from the Mini "
        "Bus Stand) and drop passengers at Siliguri's Tenzing Norgay Central Bus Stand "
        "(Junction); some services continue towards NJP.",
    ),
]

FAQ_NEW_BN = [
    (
        "কোচবিহার থেকে শিলিগুড়ি কত দূর এবং বাসে কত সময় লাগে?",
        "সড়কপথে দূরত্ব প্রায় ১৪০ কিমি (ফলাকাটা হয়ে) বা প্রায় ১২৫ কিমি (মাথাভাঙ্গা হয়ে)। "
        "বাসে সাধারণত ৩\u20134 ঘণ্টা সময় লাগে।",
    ),
    (
        "কোচবিহার কি Cooch Behar, Coochbehar নাকি Koch Bihar?",
        "সবই একই জায়গা \u2014 উত্তরবঙ্গের কোচবিহার জেলা (বাংলা: কোচবিহার)। রেলস্টেশনের নাম "
        "নিউ কোচবিহার (NCB)। বানান যেমনই হোক, এই পেজে রুটের সব বাসের তালিকা আছে।",
    ),
    (
        "কোচবিহারে বাস কোথা থেকে ছাড়ে আর শিলিগুড়িতে কোথায় নামব?",
        "বেশিরভাগ বাস কোচবিহার কেন্দ্রীয় বাস টার্মিনাস (কিছু মিনি বাস স্ট্যান্ড) থেকে ছাড়ে "
        "এবং শিলিগুড়ির তেনজিং নোরগে সেন্ট্রাল বাস স্ট্যান্ডে (জংশন) নামিয়ে দেয়।",
    ),
]

FARE_OLD_EN = ("Fares are not listed for this route yet. Bus fares in West Bengal depend on "
               "distance and bus type (AC costs more) \u2014 confirm the exact amount with the "
               "conductor or operator.")
FARE_NEW_EN = ("Online-bookable services on this route start around \u20b9120; government "
               "(NBSTC) fares are usually cheaper and depend on distance and bus type "
               "(AC costs more) \u2014 confirm the exact amount with the conductor or operator.")
FARE_OLD_BN = ("\u098f\u0987 \u09b0\u09c1\u099f\u09c7\u09b0 \u09ad\u09be\u09dc\u09be \u098f\u0996\u09a8\u09cb \u09a4\u09be\u09b2\u09bf\u0995\u09be\u09ad\u09c1\u0995\u09cd\u09a4 \u09b9\u09df\u09a8\u09bf\u0964 "
               "\u09a6\u09c2\u09b0\u09a4\u09cd\u09ac \u0986\u09b0\u09cd\u099f\u09cd\u099f\u09bf \u09ac\u09be\u09b8\u09c7\u09b0 \u09a7\u09b0\u09a8 \u09ac\u09c1\u099d\u09c7 \u09ad\u09be\u09dc\u09be \u09b9\u09df (AC \u09ac\u09be\u09b8\u09c7 \u09ac\u09c7\u09b6\u09bf) "
               "\u2014 \u09b8\u09a0\u09bf\u0995 \u099f\u09be\u0995\u09be \u0995\u09a8\u09cd\u09a1\u09be\u0995\u09cd\u099f\u09b0\u09c7\u09b0 \u0995\u09be\u099b\u09c7 \u099c\u09c7\u09a8\u09c7 \u09a8\u09bf\u09a8\u0964")
FARE_NEW_BN = ("\u0985\u09a8\u09b2\u09be\u0987\u09a8\u09c7 \u09ac\u09c1\u0995 \u0995\u09b0\u09be \u09af\u09be\u09df \u098f\u09ae\u09a8 \u09ac\u09be\u09b8\u09c7\u09b0 \u09ad\u09be\u09dc\u09be \u09aa\u09cd\u09b0\u09be\u09af\u09bc \u20b9120 \u09a5\u09c7\u0995\u09c7 \u09b6\u09c1\u09b0\u09c1; "
               "\u09b8\u09b0\u0995\u09be\u09b0\u09bf (NBSTC) \u09ad\u09be\u09dc\u09be \u09b8\u09be\u09a7\u09be\u09b0\u09a3\u09a4 \u0986\u09b0\u0993 \u0995\u09ae \u2014 \u0995\u09a8\u09cd\u09a1\u09be\u0995\u09cd\u099f\u09b0\u09c7\u09b0 \u0995\u09be\u099b\u09c7 \u09a8\u09bf\u09b6\u09cd\u099a\u09bf\u09a4 \u0995\u09b0\u09c7 \u09a8\u09bf\u09a8\u0964")

INTRO_NOTE = ('<p class="spelling-note"><span class="label-en">Cooch Behar is also written '
              'as <b>Coochbehar</b> or <b>Koch Bihar</b> (কোচবিহার) — all buses on this '
              'route are listed below.</span><span class="label-bn">কোচবিহারকে ইংরেজিতে '
              'Coochbehar / Koch Bihar-ও লেখা হয় — নিচে এই রুটের সব বাসের তালিকা '
              'দেওয়া হয়েছে।</span></p>')

META_DESC_OLD = ("Cooch Behar to Siliguri bus time table — 54 buses listed, first 5:00 AM, "
                 "last 8:45 PM. Run by NBSTC, WBTC. Timings and stoppages on BusJatri.")
META_DESC_NEW = ("Cooch Behar (Coochbehar / Koch Bihar) to Siliguri bus time table — 54 buses, "
                 "first 5:00 AM, last 8:45 PM. Distance about 140 km, journey 3-4 hours. "
                 "NBSTC + private buses, timings and stoppages on BusJatri.")

h = io.open(PAGE, encoding="utf-8").read()

# ---------- master guard ----------
if "How far is Cooch Behar from Siliguri" in h:
    print("already patched — nothing to do")
    sys.exit(0)

orig = h

# ---------- 1) visible FAQ blocks (EN + BN) ----------
def insert_after_last(h, cls, block):
    starts = [m.start() for m in re.finditer(r'<details class="' + cls + r'"', h)]
    if not starts:
        return h, False
    last = starts[-1]
    end = h.index("</details>", last) + len("</details>")
    return h[:end] + block + h[end:], True

for cls, items in (("faq only-en", FAQ_NEW_EN), ("faq only-bn", FAQ_NEW_BN)):
    block = "".join(
        '<details class="' + cls + '"><summary>' + q + '</summary>'
        '<div class="fa-body">' + a + '</div></details>'
        for q, a in items
    )
    h, ok = insert_after_last(h, cls, block)
    if not ok:
        print(cls + ": block not found")
        sys.exit(1)

# ---------- 2) JSON-LD FAQPage (parse, append, dump) ----------
done = [False]

def _patch_schema(mm):
    body = mm.group(2)
    try:
        d = json.loads(body)
    except Exception:
        return mm.group(0)
    if d.get("@type") == "FAQPage":
        for q, a in FAQ_NEW_EN + FAQ_NEW_BN:
            d["mainEntity"].append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            })
        done[0] = True
        return mm.group(1) + json.dumps(d, ensure_ascii=False) + mm.group(3)
    return mm.group(0)

h = re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)', _patch_schema, h, flags=re.S)
if not done[0]:
    print("FAQPage schema not found")
    sys.exit(1)

# ---------- 3) fare answer upgrade (EN + BN, visible + schema handled above if old text present) ----------
h = h.replace(FARE_OLD_EN, FARE_NEW_EN)
# schema copy has no HTML entities; do a looser replace for the schema variant
h = h.replace(
    "Fares are not listed for this route yet. Bus fares in West Bengal depend on distance and bus type (AC costs more)",
    "Online-bookable services on this route start around \u20b9120; government (NBSTC) fares are "
    "usually cheaper and depend on distance and bus type (AC costs more)",
)
if FARE_OLD_BN in h:
    h = h.replace(FARE_OLD_BN, FARE_NEW_BN)

# ---------- 4) intro spelling note ----------
anchor = '</span></p>'
i = h.find(anchor)
if i == -1:
    print("intro anchor not found")
    sys.exit(1)
i += len(anchor)
h = h[:i] + INTRO_NOTE + h[i:]

# ---------- 5) meta description ----------
h = h.replace(META_DESC_OLD, META_DESC_NEW)

io.open(PAGE, "w", encoding="utf-8").write(h)
print("patched: visible FAQ (3 EN + 3 BN), JSON-LD schema, fare, intro note, meta desc")

# ---------- verify ----------
h2 = io.open(PAGE, encoding="utf-8").read()
ok_json = False
for mm in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h2, re.S):
    try:
        d = json.loads(mm.group(1))
        if d.get("@type") == "FAQPage":
            assert len(d["mainEntity"]) == 16, "expected 16 schema questions"
            ok_json = True
    except AssertionError:
        raise
    except Exception:
        pass
checks = {
    "schema valid JSON (16 Q)": ok_json,
    "spelling note": "spelling-note" in h2,
    "distance FAQ": "about 140 km" in h2,
    "variants FAQ": "coach bihar" in h2,
    "visible EN faq = 8": len(re.findall(r'<details class="faq only-en"', h2)) == 8,
    "visible BN faq = 8": len(re.findall(r'<details class="faq only-bn"', h2)) == 8,
    "fare upgraded": "Fares are not listed for this route yet" not in h2,
    "meta updated": "Koch Bihar) to Siliguri bus time table" in h2,
}
for k, v in checks.items():
    print("  %-26s %s" % (k, "OK" if v else "FAIL"))
if not all(checks.values()):
    sys.exit(1)
print("ALL OK")
