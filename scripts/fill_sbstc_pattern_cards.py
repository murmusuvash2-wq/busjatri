#!/usr/bin/env python3
"""Pattern rule (validated 2026-09-30):

  A bus card's time = the departure time from the ORIGIN named in that card's
  own route label — NOT from the page's origin.

Proof: on asansol-to-kolkata.html the card "Purulia → Kolkata" shows
6:10 AM / 9:15 AM / 1:45 PM, which is exactly the official
"PURULIA TO KOLKATA VIA ASANSOL" up-direction list. The same physical service
appears on intermediate pages, carrying its true origin's time.

Applying the rule to every Time-N/A card found 938 label matches against the
official SBSTC list — but 937 of those cards are WBTC/CTC buses (E-46, BE-11 …)
whose labels merely coincide with SBSTC route names. Filling them from SBSTC
data would be wrong. Only 4 cards are genuinely SBSTC and were filled:

  digha-to-kalna.html              sbstc-nabadwip-digha-1               6:30 AM
  karunamoyee-to-bishnupur.html    sbstc-kolkata-bishnupur-1            9:30 AM
  karunamoyee-to-nandigram.html    sbstc-kolkata-nandigram-1            4:45 PM
  medinipur-to-indus.html          sbstc-midnapur-indus-via-kolkata-1  11:45 AM

Rule for any future fill: the card's OPERATOR must match the source's operator.
"""
import re

TARGETS = [
    ('digha-to-kalna.html',            'sbstc-nabadwip-digha-1',              '6:30 AM'),
    ('karunamoyee-to-bishnupur.html',  'sbstc-kolkata-bishnupur-1',           '9:30 AM'),
    ('karunamoyee-to-nandigram.html',  'sbstc-kolkata-nandigram-1',           '4:45 PM'),
    ('medinipur-to-indus.html',        'sbstc-midnapur-indus-via-kolkata-1',  '11:45 AM'),
]
NOTIME = ('<span class="no-time"><span class="label-en">Time N/A</span>'
          '<span class="label-bn">সময় নেই</span></span>')

if __name__ == "__main__":
    for page, bid, t in TARGETS:
        p = f'bus-time-table/{page}'
        h = open(p, encoding='utf-8').read()
        i = h.find(f'#/bus/{bid}"')
        if i == -1:
            print(page, 'skip'); continue
        start = h.rfind('<div class="bus-row">', 0, i)
        end = h.find('<div class="bus-row">', i)
        if end == -1: end = h.find('</section>', i)
        row = h[start:end]
        if NOTIME not in row:
            print(page, 'already filled'); continue
        h = h[:start] + row.replace(NOTIME, f'<div class="depcol"><span class="dep-t">{t}</span></div>', 1) + h[end:]
        open(p, 'w', encoding='utf-8').write(h)
        print(page, '->', t)
