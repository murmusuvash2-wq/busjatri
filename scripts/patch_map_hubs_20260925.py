#!/usr/bin/env python3
"""
2026-09-25 patch: hub-only waypoints for the Google Maps route button.

Bug (user report, ISHIKA Bardhaman -> Manbazar): the blue line on the map
went here and there, not along the bus route. Cause: the button sent three
evenly-spread stop names as waypoints, and tiny villages (Telipukur,
Chhandar, Pairachali ...) geocode to the WRONG places, so Google routed
a 678 km loop instead of the real ~150 km road.

Measured with the Maps directions panel:
  old waypoints (Telipukur|Chhandar|Pairachali) : 678 km, 15 hr
  good waypoints (Sonamukhi|Bankura|Indpur)     : 149 km, 4 hr 20
  origin + destination only                     : 162 km, 3 hr 47

Fix: pick waypoints ONLY from a curated list of ~135 big towns and
well-known places that geocode reliably. Each of the three route
segments contributes its most frequent whitelisted stop; a segment
without any known town contributes nothing. With fewer (or zero)
waypoints Google still draws a sane direct route, so the line never
wanders far off the bus road again. Only ux-fixes.js fixMapLink changes
(app.js / bus-page.js initial URLs are always rewritten by fixMapLink).

Idempotent. Backslash-free source.
"""

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REL = 'js/ux-fixes.js'

OLD_BLOCK = """    var inter = seq.slice(1, -1);
    var MAXW = 3;
    var wp = [];
    if (inter.length <= MAXW) {
      wp = inter;
    } else {
      for (var i = 0; i < MAXW; i++) {
        var k = Math.round(i * (inter.length - 1) / (MAXW - 1));
        if (wp.indexOf(inter[k]) === -1) wp.push(inter[k]);
      }
    }
"""

NEW_BLOCK = """    var inter = seq.slice(1, -1);
    var wp = [];
    if (inter.length <= 3) {
      wp = inter;
    } else {
      /* 2026-09-25 hub-only waypoints: evenly-spread village names
         geocode to wrong places and sent the blue line far off the bus
         route (Bardhaman-Manbazar drew a 678 km loop). Only curated
         big-town names are used now; segments without a known town
         add no waypoint, and origin+destination alone still gives a
         sane direct route. */
      var t3 = Math.floor(inter.length / 3);
      var segs = [[0, t3], [t3, t3 * 2], [t3 * 2, inter.length]];
      segs.forEach(function (sg) {
        var best = null, bf = -1;
        for (var i = sg[0]; i < sg[1]; i++) {
          var nm = inter[i];
          if (!MAP_HUBS[nm.toLowerCase()]) continue;
          if (nm === seq[0] || nm === seq[seq.length - 1]) continue;
          var f = mapHubFreq(nm);
          if (f > bf) { bf = f; best = nm; }
        }
        if (best && wp.indexOf(best) === -1) wp.push(best);
      });
    }
"""

HUBS_JS = """  /* Curated map waypoint hubs - big/well-known places that geocode
     reliably with \", West Bengal\" appended. Village names that Google
     resolves to the wrong district are deliberately absent. */
  var MAP_HUBS = {
    esplanade: 1, kolkata: 1, 'howrah station': 1, howrah: 1, santragachi: 1,
    'bbd bag': 1, sealdah: 1, babughat: 1, ultadanga: 1, 'rabindra sadan': 1,
    'science city': 1, rashbehari: 1, 'park street': 1, maidan: 1, moulali: 1,
    shyambazar: 1, 'chandni chowk': 1, 'college street': 1, kalighat: 1,
    garia: 1, gariahat: 1, 'park circus': 1, karunamoyee: 1, dakshineswar: 1,
    bally: 1, barasat: 1, basirhat: 1, habra: 1, madhyamgram: 1, dunlop: 1,
    baguiati: 1, newtown: 1, 'diamond harbour': 1, kakdwip: 1, namkhana: 1,
    canning: 1, baruipur: 1, sonarpur: 1, bagnan: 1, uluberia: 1, amta: 1,
    digha: 1, 'new digha': 1, contai: 1, egra: 1, ramnagar: 1, tamluk: 1,
    haldia: 1, mecheda: 1, kolaghat: 1, nandakumar: 1, kharagpur: 1,
    medinipur: 1, midnapur: 1, jhargram: 1, ghatal: 1, belda: 1, daspur: 1,
    'chandrakona town': 1, 'chandrakona road': 1, khirpai: 1, arambagh: 1,
    champadanga: 1, tarakeswar: 1, tarkeshwar: 1, singur: 1, durgapur: 1,
    asansol: 1, raniganj: 1, andal: 1, panagarh: 1, benachity: 1, barakar: 1,
    kulti: 1, chittaranjan: 1, burnpur: 1, budbud: 1, galsi: 1,
    shaktigarh: 1, kalna: 1, guskara: 1, katwa: 1, 'katwa station': 1,
    memari: 1, bardhaman: 1, barddhaman: 1, 'barddhaman station': 1,
    burdwan: 1, bankura: 1, sonamukhi: 1, beliatore: 1, bishnupur: 1,
    onda: 1, chhatna: 1, indpur: 1, khatra: 1, ranibandh: 1, sarenga: 1,
    taldangra: 1, simlapal: 1, barjora: 1, mejia: 1, saltora: 1,
    garhbeta: 1, goaltore: 1, kamarpukur: 1, purulia: 1, manbazar: 1,
    raghunathpur: 1, adra: 1, jhalda: 1, bolpur: 1, santiniketan: 1,
    suri: 1, sainthia: 1, rampurhat: 1, nalhati: 1, ahmadpur: 1,
    berhampore: 1, baharampur: 1, beldanga: 1, kandi: 1, jangipur: 1,
    dhulian: 1, krishnanagar: 1, ranaghat: 1, kalyani: 1, nabadwip: 1,
    santipur: 1, mayapur: 1, chakdaha: 1, siliguri: 1, malda: 1,
    raiganj: 1, balurghat: 1, 'cooch behar': 1, alipurduar: 1,
    mathabhanga: 1, falakata: 1, jalpaiguri: 1, agra: 1, prayagraj: 1,
    varanasi: 1, patna: 1, gaya: 1, dhanbad: 1, bokaro: 1, ranchi: 1,
    jamshedpur: 1, deoghar: 1, dumka: 1, balasore: 1, baleswar: 1,
    baripada: 1, cuttack: 1, bhubaneswar: 1, puri: 1
  };
  var MAP_HUB_FREQ = null;
  function mapHubFreq(name) {
    if (!MAP_HUB_FREQ) {
      MAP_HUB_FREQ = {};
      var src = (typeof FULL_BUSES !== 'undefined' && FULL_BUSES && Object.keys(FULL_BUSES).length) ? FULL_BUSES : BUSES;
      Object.keys(src).forEach(function (k) {
        var b = src[k];
        if (!b) return;
        var seen = {};
        (b.stoppages || []).forEach(function (s) {
          var n = (s && s.name) ? String(s.name).toLowerCase() : '';
          if (n && !seen[n]) { seen[n] = 1; MAP_HUB_FREQ[n] = (MAP_HUB_FREQ[n] || 0) + 1; }
        });
        [b.origin, b.destination].forEach(function (o) {
          var n = o ? String(o).toLowerCase() : '';
          if (n && !seen[n]) { seen[n] = 1; MAP_HUB_FREQ[n] = (MAP_HUB_FREQ[n] || 0) + 1; }
        });
      });
    }
    return MAP_HUB_FREQ[String(name).toLowerCase()] || 0;
  }

"""

def read(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as fh:
        return fh.read()

def write(rel, content):
    with open(os.path.join(ROOT, rel), 'w', encoding='utf-8') as fh:
        fh.write(content)

src = read(REL)

if 'MAP_HUBS' in src:
    print('SKIP', REL, '(already patched)')
else:
    assert OLD_BLOCK in src, 'ux-fixes.js: waypoint selection block not found verbatim'
    src = src.replace(OLD_BLOCK, NEW_BLOCK)
    anchor = '  function fixMapLink() {'
    assert anchor in src, 'ux-fixes.js: fixMapLink anchor not found'
    src = src.replace(anchor, HUBS_JS + anchor, 1)
    write(REL, src)
    print('PATCHED', REL)

# index.html cache buster for ux-fixes.js
idx_rel = 'index.html'
idx = read(idx_rel)
old_v = 'ux20260925a'
new_v = 'ux20260925b'
if new_v in idx:
    print('SKIP', idx_rel, '(cache buster already bumped)')
elif old_v in idx:
    idx = idx.replace(old_v, new_v)
    write(idx_rel, idx)
    print('PATCHED', idx_rel, '(cache buster', old_v, '->', new_v, ')')
else:
    print('WARN: no ux version param found in index.html - check manually')

# ------------------------------------------------------------ validate ----
errors = []

txt = read(REL)
for needle in ['MAP_HUBS', 'mapHubFreq', 'hub-only waypoints']:
    if needle not in txt:
        errors.append('ux-fixes.js: missing ' + needle)
if 'Math.round(i * (inter.length - 1) / (MAXW - 1))' in txt:
    errors.append('ux-fixes.js: old evenly-spread selection still present')

idx2 = read(idx_rel)
if new_v not in idx2:
    errors.append('index.html: ux-fixes cache buster not bumped')

if errors:
    print('VALIDATION FAILED:')
    for e in errors:
        print('  -', e)
    sys.exit(1)

print('VALIDATION OK')
