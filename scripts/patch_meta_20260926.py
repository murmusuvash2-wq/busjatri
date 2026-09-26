# -*- coding: utf-8 -*-
import ast, io
p = 'scripts/gen_operator_pages.py'
s = io.open(p, encoding='utf-8').read()

NEW = {
 'sbstc-buses': dict(
   title='SBSTC Bus Time Table (\u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf) \u2014 Routes & Timings',
   desc='SBSTC bus time table: routes, departure times & destinations across West Bengal. \u098f\u09b8\u09ac\u09bf\u098f\u09b8\u099f\u09bf\u09b8\u09bf \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf, \u09b0\u09c1\u099f \u0993 \u099b\u09be\u09a1\u09bc\u09be\u09b0 \u09b8\u09ae\u09af\u09bc \u2014 \u0995\u09b2\u0995\u09be\u09a4\u09be, \u09a6\u09c0\u0998\u09be, \u09a6\u09c1\u09b0\u09cd\u0997\u09be\u09aa\u09c1\u09b0 \u09b8\u09b9 \u09b8\u09ac \u09b0\u09c1\u099f\u0964',
   ogt='SBSTC \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u2014 Bus Time Table | BusJatri',
   ogd='\u098f\u09b8\u09ac\u09bf\u098f\u09b8\u099f\u09bf\u09b8\u09bf (SBSTC) \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u2014 \u09b0\u09c1\u099f, \u099b\u09be\u09a1\u09bc\u09be\u09b0 \u09b8\u09ae\u09af\u09bc \u0993 \u0997\u09a8\u09cd\u09a4\u09ac\u09cd\u09af\u0964 \u0995\u09b2\u0995\u09be\u09a4\u09be\u2013\u09a6\u09c0\u0998\u09be, \u09a6\u09c1\u09b0\u09cd\u0997\u09be\u09aa\u09c1\u09b0, \u09ac\u09b0\u09cd\u09a7\u09ae\u09be\u09a8 \u09b8\u09b9 \u09b8\u09ac \u09b0\u09c1\u099f BusJatri-\u09a4\u09c7\u0964'),
 'nbstc-buses': dict(
   title='NBSTC Bus Time Table (\u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf) \u2014 Routes & Timings',
   desc='NBSTC bus time table: routes, departure times & destinations across North Bengal. \u098f\u09a8\u09ac\u09bf\u098f\u09b8\u099f\u09bf\u09b8\u09bf \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf, \u09b0\u09c1\u099f \u0993 \u099b\u09be\u09a1\u09bc\u09be\u09b0 \u09b8\u09ae\u09af\u09bc \u2014 \u09b6\u09bf\u09b2\u09bf\u0997\u09a1\u09bc\u09bf, \u0995\u09cb\u099a\u09ac\u09bf\u09b9\u09be\u09b0, \u09ae\u09be\u09b2\u09a6\u09be \u09b8\u09b9 \u09b8\u09ac \u09b0\u09c1\u099f\u0964',
   ogt='NBSTC \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u2014 Bus Time Table | BusJatri',
   ogd='\u098f\u09a8\u09ac\u09bf\u098f\u09b8\u099f\u09bf\u09b8\u09bf (NBSTC) \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u2014 \u09b0\u09c1\u099f, \u099b\u09be\u09a1\u09bc\u09be\u09b0 \u09b8\u09ae\u09af\u09bc \u0993 \u0997\u09a8\u09cd\u09a4\u09ac\u09cd\u09af\u0964 \u09b6\u09bf\u09b2\u09bf\u0997\u09a1\u09bc\u09bf, \u0995\u09cb\u099a\u09ac\u09bf\u09b9\u09be\u09b0, \u09ae\u09be\u09b2\u09a6\u09be \u09b8\u09b9 \u09b8\u09ac \u09b0\u09c1\u099f BusJatri-\u09a4\u09c7\u0964'),
 'wbtc-buses': dict(
   title='WBTC Bus Time Table (\u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf) \u2014 Routes & Timings',
   desc='WBTC (CSTC) bus time table: routes, departure times & destinations across Kolkata and West Bengal. \u09a1\u09ac\u09cd\u09b2\u09bf\u0989\u09ac\u09bf\u099f\u09bf\u09b8\u09bf \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u0993 \u09b0\u09c1\u099f \u2014 \u0995\u09b2\u0995\u09be\u09a4\u09be \u09b8\u09b9 \u09b8\u09ac \u09b0\u09c1\u099f\u0964',
   ogt='WBTC \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u2014 Bus Time Table | BusJatri',
   ogd='\u09a1\u09ac\u09cd\u09b2\u09bf\u0989\u09ac\u09bf\u099f\u09bf\u09b8\u09bf (WBTC) \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u2014 \u09b0\u09c1\u099f, \u099b\u09be\u09a1\u09bc\u09be\u09b0 \u09b8\u09ae\u09af\u09bc \u0993 \u0997\u09a8\u09cd\u09a4\u09ac\u09cd\u09af\u0964 \u0995\u09b2\u0995\u09be\u09a4\u09be \u0993 \u09aa\u09b6\u09cd\u099a\u09bf\u09ae\u09ac\u0999\u09cd\u0997\u09c7\u09b0 \u09b8\u09ac \u09b0\u09c1\u099f BusJatri-\u09a4\u09c7\u0964'),
 'shyamoli-paribahan-buses': dict(
   title='Shyamoli Paribahan Bus Time Table (\u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf)',
   desc='Shyamoli Paribahan AC Volvo bus time table: routes, departure times & destinations. \u09b6\u09cd\u09af\u09be\u09ae\u09b2\u09c0 \u09aa\u09b0\u09bf\u09ac\u09b9\u09a8\u09c7\u09b0 \u098f\u09b8\u09bf \u09ad\u09b2\u09cd\u09ad\u09cb \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u0993 \u09b0\u09c1\u099f \u2014 \u0995\u09b2\u0995\u09be\u09a4\u09be \u09b8\u09b9 \u09b8\u09ac \u09b0\u09c1\u099f\u0964',
   ogt='\u09b6\u09cd\u09af\u09be\u09ae\u09b2\u09c0 \u09aa\u09b0\u09bf\u09ac\u09b9\u09a8\u09c7\u09b0 \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf | BusJatri',
   ogd='\u09b6\u09cd\u09af\u09be\u09ae\u09b2\u09c0 \u09aa\u09b0\u09bf\u09ac\u09b9\u09a8\u09c7\u09b0 \u098f\u09b8\u09bf \u09ad\u09b2\u09cd\u09ad\u09cb \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u2014 \u09b0\u09c1\u099f, \u099b\u09be\u09a1\u09bc\u09be\u09b0 \u09b8\u09ae\u09af\u09bc \u0993 \u0997\u09a8\u09cd\u09a4\u09ac\u09cd\u09af\u0964 \u09b8\u09ac \u09b0\u09c1\u099f BusJatri-\u09a4\u09c7\u0964'),
 'volvo-ac-buses': dict(
   title='Volvo AC Bus Time Table (\u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf) \u2014 Routes & Timings',
   desc='Volvo AC bus time table: routes, departure times & destinations across West Bengal. \u098f\u09b8\u09bf \u09ad\u09b2\u09cd\u09ad\u09cb \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u2014 \u09b0\u09c1\u099f \u0993 \u099b\u09be\u09a1\u09bc\u09be\u09b0 \u09b8\u09ae\u09af\u09bc \u098f\u0995 \u099c\u09be\u09af\u09bc\u0997\u09be\u09af\u09bc\u0964',
   ogt='\u09ad\u09b2\u09cd\u09ad\u09cb \u098f\u09b8\u09bf \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u2014 Bus Time Table | BusJatri',
   ogd='\u098f\u09b8\u09bf \u09ad\u09b2\u09cd\u09ad\u09cb \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09bf \u2014 \u09b0\u09c1\u099f, \u099b\u09be\u09a1\u09bc\u09be\u09b0 \u09b8\u09ae\u09af\u09bc \u0993 \u0997\u09a8\u09cd\u09a4\u09ac\u09cd\u09af\u0964 \u09aa\u09b6\u09cd\u099a\u09bf\u09ae\u09ac\u0999\u09cd\u0997\u09c7\u09b0 \u09b8\u09ac \u09b0\u09c1\u099f BusJatri-\u09a4\u09c7\u0964'),
}

# 1. replace title= and desc= per operator, insert ogt/ogd after desc
import re
count_ops = 0
for stem, nd in NEW.items():
    m = re.search(r"dict\(stem='%s'" % re.escape(stem), s)
    assert m, stem
    seg_start = m.start()
    seg_end = s.find('pred=', seg_start)
    seg = s[seg_start:seg_end]
    old_title = re.search(r"title='[^']*'", seg).group(0)
    old_desc = re.search(r"desc='[^']*'", seg).group(0)
    seg2 = seg.replace(old_title, "title='%s'" % nd['title'].replace(chr(39), chr(92)+chr(39)))
    new_desc_full = "desc='%s'," % nd['desc'].replace(chr(39), chr(92)+chr(39)) + chr(10) + "         ogt='%s'," % nd['ogt'] + chr(10) + "         ogd='%s'," % nd['ogd']
    seg2 = seg2.replace(old_desc, new_desc_full.rstrip(','))
    s = s[:seg_start] + seg2 + s[seg_end:]
    count_ops += 1
print('operators patched:', count_ops)

# 2. HEAD template og/twitter block
OLD_OG = '''<meta property="og:title" content="{title} | BusJatri">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}/bus-time-table/{stem}.html">'''
NEW_OG = '''<meta property="og:title" content="{ogt}">
<meta property="og:description" content="{ogd}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}/bus-time-table/{stem}.html">
<meta property="og:image" content="{BASE}/og-image.png">
<meta property="og:locale" content="en_IN">
<meta property="og:locale:alternate" content="bn_IN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{ogt}">
<meta name="twitter:description" content="{ogd}">
<meta name="twitter:image" content="{BASE}/og-image.png">'''
assert s.count(OLD_OG) == 1, 'og block count: %d' % s.count(OLD_OG)
s = s.replace(OLD_OG, NEW_OG)

# 3. format call: add ogt/ogd
OLD_F = "body = HEAD.format(title=esc(op['title']), desc=esc(op['desc']), stem=op['stem'],"
NEW_F = "body = HEAD.format(title=esc(op['title']), desc=esc(op['desc']), stem=op['stem'], ogt=esc(op['ogt']), ogd=esc(op['ogd']),"
assert s.count(OLD_F) == 1
s = s.replace(OLD_F, NEW_F)

ast.parse(s)
io.open(p, 'w', encoding='utf-8').write(s)
print('generator patched + ast OK')
