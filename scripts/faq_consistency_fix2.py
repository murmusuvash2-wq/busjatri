#!/usr/bin/env python3
"""Corrective pass for faq_consistency_fix.py.

The first run replaced the FIRST occurrence of the sentence — which is inside the
FAQPage JSON-LD in <head> — so the JSON-LD got the official window (twice) and
the VISIBLE FAQ answer was never updated.

This pass:
  1. collapses the doubled sentence inside the JSON-LD,
  2. adds the official window to the VISIBLE first-bus FAQ (EN + BN) only,
     scoped to the faq-v2 section so the JSON-LD is never touched.
"""
import os, re

BASE = os.path.join(os.path.dirname(__file__), "..")
BT = os.path.join(BASE, "bus-time-table")
MARK = "Official SBSTC departures"
BN_DIGITS = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')


def bn_time(t):
    m = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', t.strip(), re.I)
    if not m:
        return t
    h, mi, ap = int(m.group(1)), m.group(2), m.group(3).upper()
    if ap == 'AM':
        part = 'সকাল' if h >= 4 else 'রাত'
    else:
        part = 'দুপুর' if h == 12 or h < 4 else ('বিকেল' if h < 7 else 'রাত')
    return f"{part} {str(h).translate(BN_DIGITS)}:{mi.translate(BN_DIGITS)}"


def official_window(html):
    m = re.search(r'<!-- sbstc-official-v1 -->(.*?)</section>', html, re.S)
    if not m:
        return None
    sec = m.group(0)
    firsts = re.findall(r'<span class="dep-t">([^<]+)</span>', sec)
    lasts = re.findall(r'শেষ বাস</span>\s*([0-9]{1,2}:[0-9]{2}\s*[AP]M)', sec)
    return (firsts[0].strip(), lasts[0].strip()) if firsts and lasts else None


OLD_EN = "Arrive a little early, as buses often depart once seats fill up."
OLD_BN = "সিটের জন্য একটু আগে গিয়ে অপেক্ষা করাই ভালো।"

def main():
    fixed = dedup = 0
    for f in sorted(os.listdir(BT)):
        if not f.endswith('.html'):
            continue
        p = os.path.join(BT, f)
        h = open(p, encoding='utf-8').read()
        if '<!-- sbstc-official-v1 -->' not in h:
            continue
        w = official_window(h)
        if not w:
            continue
        first, last = w
        q = re.search(r'<summary>What is the first bus from ([^<]+?) to ([^<]+?)\?</summary>', h)
        qb = re.search(r'<summary>([^<]+?) থেকে [^<]+? প্রথম বাস কখন ছাড়ে\?</summary>', h)
        if not q:
            continue
        origin_en = q.group(1).strip()
        origin_bn = qb.group(1).strip() if qb else origin_en

        # 1) de-duplicate the JSON-LD sentence
        dup_en = f"{MARK} from {origin_en} start at <b>{first}</b> and run till <b>{last}</b>."
        h2 = h.replace(dup_en + " " + dup_en, dup_en)
        if h2 != h:
            dedup += 1
            h = h2

        # 2) visible FAQ (scoped to the faq-v2 section)
        msec = re.search(r'<section class="seo-section faq-v2">.*?</section>', h, re.S)
        if not msec:
            continue
        sec = msec.group(0)
        if MARK in sec:
            continue
        new_en = f"{dup_en} " + OLD_EN
        new_bn = (f"{origin_bn} থেকে সরকারি এসবিএসটিসি বাস <b>{bn_time(first)}</b> থেকে ছাড়ে, "
                  f"শেষ <b>{bn_time(last)}</b>। " + OLD_BN)
        sec2 = sec.replace(OLD_EN, new_en, 1).replace(OLD_BN, new_bn, 1)
        if sec2 == sec:
            continue
        h = h[:msec.start()] + sec2 + h[msec.end():]
        open(p, 'w', encoding='utf-8').write(h)
        fixed += 1
    print(f"visible FAQ fixed: {fixed} | JSON-LD de-duplicated: {dedup}")


if __name__ == "__main__":
    main()
