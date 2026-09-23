# Generates sitemap-via.xml and merges all via/ stop pages into the MAIN
# sitemap.xml as well. Keeps robots.txt in sync. Idempotent: safe to re-run.
import os, glob

NL = chr(10)

slugs = sorted(os.path.basename(p)[:-5] for p in glob.glob('via/*.html'))
slugs = [s for s in slugs if s != 'index']

via_urls = ['https://busjatri.in/via/']
via_urls += ['https://busjatri.in/via/' + s for s in slugs]

# standalone via sitemap (already submitted to GSC)
lines = ['<?xml version="1.0" encoding="UTF-8"?>']
lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
for u in via_urls:
    lines.append('  <url><loc>' + u + '</loc></url>')
lines.append('</urlset>')
open('sitemap-via.xml', 'w', encoding='utf-8').write(NL.join(lines) + NL)
print('sitemap-via.xml:', len(via_urls), 'urls')

# merge into MAIN sitemap.xml (idempotent)
m = open('sitemap.xml', encoding='utf-8').read()
missing = [u for u in via_urls if u not in m]
if missing:
    block = NL.join('<url><loc>' + u + '</loc><priority>0.6</priority></url>' for u in missing)
    if not m.endswith(NL):
        m += NL
    m = m.replace('</urlset>', block + NL + '</urlset>')
    open('sitemap.xml', 'w', encoding='utf-8').write(m)
print('sitemap.xml: merged', len(missing), 'new via urls')

# robots.txt sync
r = open('robots.txt', encoding='utf-8').read()
add = 'Sitemap: https://busjatri.in/sitemap-via.xml'
if add not in r:
    if not r.endswith(NL):
        r += NL
    r += add + NL
    open('robots.txt', 'w', encoding='utf-8').write(r)
    print('robots.txt: added via sitemap line')
else:
    print('robots.txt: already ok')
