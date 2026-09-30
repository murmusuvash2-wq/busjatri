# COMPLETE fix for the /bus-time-table/ page (Bengali toggle + names):
#   a) In Bangla mode the whole .sname div was hidden (body.lang-bn .sname{display:none}),
#      so stand names vanished when the Bengali toggle was clicked. Fixed: hide only the
#      English span (.sen), show the Bengali span (.sbn).
#   b) 43 of 76 stand cards had no Bengali name (missing BN dict entries) — added.
#   c) Umbrella "Kolkata (Esplanade)" showed just কলকাতা (qualifier lost) — now
#      কলকাতা (এসপ্ল্যানেড); generator looks up Bengali by display name first.
#   d) Bardhaman-area stands organized: "Barddhaman Alisha Bus Stand" ->
#      "Bardhaman (Alisha Bus Stand)" (same for Nawabhat) via UMBRELLA.
#   e) Spelling: সানত্রাগাছি -> সাঁতরাগাছি (Santragachi, chandrabindu).
# All steps are idempotent (safe to re-run). UTF-8 throughout.
import io
import json
import re
import sys

MISSING = {
    "Amtala": "আমতলা",
    "Babughat": "বাবুঘাট",
    "Bagnan": "বাগনান",
    "Bandwan": "বান্দোয়ান",
    "Barabazar": "বড়বাজার",
    "Barasat Chapadali": "বারাসাত চাপাড়ালি",
    "Bardhaman (Alisha Bus Stand)": "বর্ধমান (আলিশা বাস স্ট্যান্ড)",
    "Bardhaman (Nawabhat Bus Stand)": "বর্ধমান (নবাহাট বাস স্ট্যান্ড)",
    "Basirhat": "বসিরহাট",
    "BBD Bag": "বিবিডি বাগ",
    "Benachity": "বেনাচিটি",
    "Boga": "বোগা",
    "Chandrakona Road": "চন্দ্রকোণা রোড",
    "Chittaranjan": "চিত্তরঞ্জন",
    "Dakshineswar": "দক্ষিণেশ্বর",
    "Dhamakhali": "ধামাখালি",
    "Dhanbad": "ধানবাদ",
    "Durgapur Station": "দুর্গাপুর স্টেশন",
    "Egra": "এগরা",
    "Fulkusma": "ফুলকুসমা",
    "Garia Bus Stand": "গড়িয়া বাস স্ট্যান্ড",
    "Habra": "হাবড়া",
    "Habra Depot": "হাবড়া ডিপো",
    "Habra Station": "হাবড়া স্টেশন",
    "Howrah Maidan": "হাওড়া ময়দান",
    "Howrah Station": "হাওড়া স্টেশন",
    "Jadavpur 8B": "যাদবপুর ৮বি",
    "Karimpur": "করিমপুর",
    "Kolkata (Karunamoyee)": "কলকাতা (করুণাময়ী)",
    "Midnapur": "মেদিনীপুর",
    "Nabanna": "নবান্ন",
    "Newtown": "নিউটাউন",
    "Raipur": "রাইপুর",
    "Rajabazar": "রাজাবাজার",
    "Kolkata (Santragachi)": "কলকাতা (সাঁতরাগাছি)",
    "Sealdah": "শিয়ালদহ",
    "Sector V": "সেক্টর ফাইভ",
    "Shapoorji": "শাপুরজি",
    "Shyambazar": "শ্যামবাজার",
    "Tarakeshwar": "তারকেশ্বর",
    "Tatanagar": "টাটানগর",
    "Thakurpukur": "ঠাকুরপুকুর",
    "Ultadanga": "উল্টোডাঙ্গা",
}

# Existing Bengali spans that must be REPLACED with the corrected value.
OVERRIDES = {
    "Kolkata (Esplanade)": "কলকাতা (এসপ্ল্যানেড)",
    "Kolkata (Santragachi)": "কলকাতা (সাঁতরাগাছি)",
}

# English display-name reorganisation (URLs unchanged).
RENAME = {
    "Barddhaman Alisha Bus Stand": "Bardhaman (Alisha Bus Stand)",
    "Barddhaman Nawabhat Bus Stand": "Bardhaman (Nawabhat Bus Stand)",
}

Q = chr(34)  # double quote
NL = chr(10)

OLD_CSS = ("body.lang-bn .sname{display:none}" + NL +
           "body.lang-bn .keep-en .sname{display:inline}")
NEW_CSS = ("body.lang-bn .sname .sen{display:none}" + NL +
           "body.lang-bn .keep-en .sen{display:inline}" + NL +
           "body.lang-bn .sbn{font-size:16.5px;font-weight:800;color:inherit;margin-left:0}")

# ---------- 1) BN dict in scripts/gen_seo_pages.py ----------
GEN1 = "scripts/gen_seo_pages.py"
src = io.open(GEN1, encoding="utf-8").read()
m = re.search(r"^BN\s*=\s*(\{.*?^\})", src, re.M | re.S)
if not m:
    print("gen_seo_pages.py: BN dict not found")
    sys.exit(1)
import ast
BN = ast.literal_eval(m.group(1))
ALLMAP = dict(MISSING)
ALLMAP.update(OVERRIDES)
new = {k: v for k, v in ALLMAP.items() if k not in BN}
if new:
    block = m.group(1)
    add = "".join(
        "    %s: %s,%s" % (repr(k).replace("'", Q), repr(v).replace("'", Q), NL)
        for k, v in sorted(new.items())
    )
    src = src.replace(block, block[:-1] + add + "}")
if new:
    io.open(GEN1, "w", encoding="utf-8").write(src)
    print("gen_seo_pages.py: added %d BN entries" % len(new))
else:
    print("gen_seo_pages.py: already up to date")

# ---------- 2) generator: scripts/gen_btt_v2.py ----------
GEN2 = "scripts/gen_btt_v2.py"
g = io.open(GEN2, encoding="utf-8").read()
changed = []
old_card = "<div class=" + Q + "sname" + Q + ">{name}{bn}</div>"
new_card = ("<div class=" + Q + "sname" + Q + "><span class=" + Q + "sen" + Q
            + ">{name}</span>{bn}</div>")
if old_card in g:
    g = g.replace(old_card, new_card)
    changed.append("card template")
if OLD_CSS in g:
    g = g.replace(OLD_CSS, NEW_CSS)
    changed.append("CSS")
old_bn = "bn = v2.bnplace(name)"
new_bn = "bn = g.bn(card_name(name)) or g.bn(name) or v2.bnplace(name)"
if old_bn in g:
    g = g.replace(old_bn, new_bn, 1)
    changed.append("bn lookup by display name")
if changed:
    io.open(GEN2, "w", encoding="utf-8").write(g)
    print("gen_btt_v2.py: fixed %s" % ", ".join(changed))
else:
    print("gen_btt_v2.py: already up to date")

# ---------- 2b) UMBRELLA entries in scripts/gen_stand_v2.py ----------
GEN3 = "scripts/gen_stand_v2.py"
s3 = io.open(GEN3, encoding="utf-8").read()
if "barddhaman-alisha-bus-stand" not in s3:
    ins = (
        "    # Bardhaman-area satellite stands, shown as Bardhaman (<stand>)" + NL +
        '    "barddhaman-alisha-bus-stand": ("Bardhaman (Alisha Bus Stand)", ("barddhaman alisha bus stand", "bardhaman alisha", "burdwan alisha", "alisha bus stand")),' + NL +
        '    "barddhaman-nawabhat-bus-stand": ("Bardhaman (Nawabhat Bus Stand)", ("barddhaman nawabhat bus stand", "nawabhat bus stand", "nawabhat")),' + NL
    )
    anchor = '    "santragachi": ("Kolkata (Santragachi)", ("santragachi",)),' + NL
    if anchor not in s3:
        print("gen_stand_v2.py: UMBRELLA anchor not found")
        sys.exit(1)
    s3 = s3.replace(anchor, anchor + ins)
    io.open(GEN3, "w", encoding="utf-8").write(s3)
    print("gen_stand_v2.py: 2 UMBRELLA entries added")
else:
    print("gen_stand_v2.py: already up to date")

# ---------- 3) bus-time-table/index.html ----------
PAGE = "bus-time-table/index.html"
h = io.open(PAGE, encoding="utf-8").read()
if OLD_CSS in h:
    h = h.replace(OLD_CSS, NEW_CSS)
    print("index.html: CSS fixed")

# rename English display names (cards + datalists), and fix their Bengali
for old, new_en in RENAME.items():
    h, k = re.subn(r">" + re.escape(old) + "<", ">" + re.escape(new_en) + "<", h)
    h = h.replace("<option value=" + Q + old + Q + ">", "<option value=" + Q + new_en + Q + ">")
    if new_en in MISSING:
        bn = MISSING[new_en]
        rx = (r'(<span class=' + Q + 'sen' + Q + '>' + re.escape(new_en) + r'</span>'
              + r'\s*<span class=' + Q + 'sbn' + Q + '>)(.*?)(</span>)')
        h2, k2 = re.subn(rx, lambda mm: mm.group(1) + bn + mm.group(3), h)
        if k2:
            h = h2

# insert missing sbn spans
count = 0
for en, bn in MISSING.items():
    pat = ("<div class=" + Q + "sname" + Q + ">" + en + "</div>")
    if pat in h:
        h = h.replace(pat, ("<div class=" + Q + "sname" + Q + ">" + en
                            + " <span class=" + Q + "sbn" + Q + ">" + bn + "</span></div>"))
        count += 1
if count:
    print("index.html: inserted %d sbn spans" % count)

# replace wrong/truncated Bengali on cards that already have one
fixed_ov = 0
for en, bn in OVERRIDES.items():
    rx = (r'(<span class=' + Q + 'sen' + Q + '>' + re.escape(en) + r'</span>'
          + r'\s*<span class=' + Q + 'sbn' + Q + '>)(.*?)(</span>)')
    h2, k = re.subn(rx, lambda mm: mm.group(1) + bn + mm.group(3), h)
    if k:
        h = h2
        fixed_ov += k
print("index.html: %d overrides applied" % fixed_ov)

# wrap bare English text of .sname in span.sen
def wrap(mm):
    inner = mm.group(1)
    if "class=" + Q + "sen" + Q in inner:
        return mm.group(0)
    idx = inner.find("<span class=" + Q + "sbn" + Q + ">")
    if idx >= 0:
        en, bn = inner[:idx].strip(), " " + inner[idx:].strip()
    else:
        en, bn = inner.strip(), ""
    return ("<div class=" + Q + "sname" + Q + "><span class=" + Q + "sen" + Q + ">"
            + en + "</span>" + bn + "</div>")

h, n = re.subn(r'<div class="sname">(.*?)</div>', wrap, h)
if n:
    print("index.html: %d cards wrapped in span.sen" % n)

# ---------- 4) RT_BN reverse search map ----------
rtm = re.search(r"var RT_BN=(\{.*?\});", h, re.S)
added_rt = 0
if rtm:
    try:
        rt = json.loads(rtm.group(1))
    except Exception:
        rt = None
    if rt is not None:
        rt.pop("সানত্রাগাছি", None)            # old spelling (standalone)
        rt.pop("কলকাতা (সানত্রাগাছি)", None)   # old spelling (qualified)
        rt.pop("বর্ধমান আলিশা বাস স্ট্যান্ড", None)  # pre-rename
        rt.pop("বর্ধমান নবাহাট বাস স্ট্যান্ড", None)  # pre-rename
        for en, bn in ALLMAP.items():
            if bn not in rt:
                rt[bn] = en
                added_rt += 1
        new_js = "var RT_BN=" + json.dumps(rt, ensure_ascii=False, sort_keys=True) + ";"
        h = h.replace(rtm.group(0), new_js)
print("index.html: %d RT_BN entries added" % added_rt)

io.open(PAGE, "w", encoding="utf-8").write(h)

# ---------- verify ----------
h2 = io.open(PAGE, encoding="utf-8").read()
cards = re.findall(r'<div class="sname">(.*?)</div>', h2)
sen = sum(1 for c in cards if "class=" + Q + "sen" + Q in c)
sbn = sum(1 for c in cards if "class=" + Q + "sbn" + Q in c)
css_ok = ("body.lang-bn .sname .sen{display:none}" in h2
          and "body.lang-bn .sname{display:none}" not in h2)
spell_ok = ("সানত্রাগাছি" not in h2 and "সাঁতরাগাছি" in h2)
rename_ok = ("Bardhaman (Alisha Bus Stand)" in h2
             and "Bardhaman (Nawabhat Bus Stand)" in h2
             and "Barddhaman Alisha Bus Stand" not in h2)
print("verify: %d cards | .sen=%d | .sbn=%d | css_ok=%s | spell_ok=%s | rename_ok=%s"
      % (len(cards), sen, sbn, css_ok, spell_ok, rename_ok))
if not (sen == sbn == len(cards) and css_ok and spell_ok and rename_ok):
    print("verify: FAILED")
    sys.exit(1)
print("ALL OK")
