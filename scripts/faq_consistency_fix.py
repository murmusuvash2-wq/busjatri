#!/usr/bin/env python3
"""#1 — Make the FAQ consistent with the official SBSTC data (55 route pages).

Problem (found via audit): the "first bus" FAQ says e.g. "first bus leaves
Asansol at 5:00 AM" while the official SBSTC section on the same page lists
5:35, 6:20, ... — because 5:00 AM is a Purulia-origin service listed on the page.

Fix: append the official SBSTC window to the first-bus FAQ answer (visible EN,
visible BN, and both FAQPage JSON-LD entries) so the page no longer contradicts
itself. Source of the numbers: the page's own <!-- sbstc-official-v1 --> section.

Idempotent: skips a page already carrying the marker phrase.
"""
import os, re

BASE = os.path.join(os.path.dirname(__file__), "..")
BT = os.path.join(BASE, "bus-time-table")
MARK = "Official SBSTC departures"

BN_DIGITS = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')


def bn_time(t):
    """'5:35 AM' -> 'সকাল ৫:৩৫'"""
    m = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', t.strip(), re.I)
    if not m:
        return t
    h, mi, ap = int(m.group(1)), m.group(2), m.group(3).upper()
    if ap == 'AM':
        part = 'সকাল' if h >= 4 else 'রাত'
    else:
        part = 'দুপুর' if h == 12 or h < 4 else ('বিকেল' if h < 7 else 'রাত')
    return f"{part} {str(h).translate(BN_DIGITS)}:{mi.translate(BN_DIGITS)}"


def official_window(page_html):
    m = re.search(r'<!-- sbstc-official-v1 -->(.*?)</section>', page_html, re.S)
    if not m:
        return None
    sec = m.group(0)
    firsts = re.findall(r'<span class="dep-t">([^<]+)</span>', sec)
    lasts = re.findall(r'শেষ বাস</span>\s*([0-9]{1,2}:[0-9]{2}\s*[AP]M)', sec)
    if not firsts:
        return None
    return firsts[0].strip(), (lasts[0].strip() if lasts else None)


def main():
    done = skipped = 0
    for f in sorted(os.listdir(BT)):
        if not f.endswith('.html'):
            continue
        p = os.path.join(BT, f)
        h = open(p, encoding='utf-8').read()
        if '<!-- sbstc-official-v1 -->' not in h or MARK in h:
            continue
        w = official_window(h)
        if not w or not w[1]:
            skipped += 1
            continue
        first, last = w
        # origin from the EN question
        q = re.search(r'<summary>What is the first bus from ([^<]+?) to ([^<]+?)\?</summary>', h)
        if not q:
            skipped += 1
            continue
        origin_en = q.group(1).strip()
        # BN origin from the BN question
        qb = re.search(r'<summary>([^<]+?) থেকে [^<]+? প্রথম বাস কখন ছাড়ে\?</summary>', h)
        origin_bn = qb.group(1).strip() if qb else origin_en

        # ---- visible EN ----
        old_en = "Arrive a little early, as buses often depart once seats fill up."
        new_en = (f"{MARK} from {origin_en} start at <b>{first}</b> and run till <b>{last}</b>. "
                  + old_en)
        # ---- visible BN ----
        old_bn = "সিটের জন্য একটু আগে গিয়ে অপেক্ষা করাই ভালো।"
        new_bn = (f"{origin_bn} থেকে সরকারি এসবিএসটিসি বাস <b>{bn_time(first)}</b> থেকে ছাড়ে, "
                  f"শেষ <b>{bn_time(last)}</b>। " + old_bn)
        # ---- JSON-LD ----
        j_en = f"{MARK} from {origin_en} start at <b>{first}</b> and run till <b>{last}</b>."
        j_bn = (f"{origin_bn} থেকে সরকারি এসবিএসটিসি বাস <b>{bn_time(first)}</b> থেকে ছাড়ে, "
                f"শেষ <b>{bn_time(last)}</b>।")

        n_en = h.count(old_en)
        n_bn = h.count(old_bn)
        if n_en == 0 or n_bn == 0:
            skipped += 1
            continue
        h = h.replace(old_en, new_en, 1)   # first occurrence = the first-bus FAQ
        h = h.replace(old_bn, new_bn, 1)
        # JSON-LD: replace the first-bus answer text (appears once in the ld+json)
        h = h.replace(old_en, j_en + " " + old_en, 1) if False else h
        # append to JSON-LD first-bus answer specifically
        mld = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', h, re.S)
        if mld:
            ld = mld.group(2)
            ld2 = ld.replace(old_en, j_en + " " + old_en, 1)
            ld2 = ld2.replace(old_bn, j_bn + " " + old_bn, 1)
            if ld2 != ld:
                h = h[:mld.start(2)] + ld2 + h[mld.end(2):]
        open(p, 'w', encoding='utf-8').write(h)
        done += 1
    print(f"pages updated: {done} | skipped: {skipped}")


if __name__ == "__main__":
    main()
