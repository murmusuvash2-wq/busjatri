# Generates sitemap-via.xml from the via/ folder (2,605 stop pages)
# and keeps robots.txt in sync. Idempotent: safe to re-run.
import os, glob

NL = chr(10)

slugs = sorted(os.path.basename(p)[:-5] for p in glob.glob('via/*.html'))
slugs = [s for s in slugs if s != 'index']

lines = ['<?xml version="1.0" encoding="UTF-8"?>']
lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
lines.append('  <url><loc>https://busjatri.in/via/</loc></url>')
for s in slugs:
    lines.append('  <url><loc>https://busjatri.in/via/' + s + '</loc></url>')
lines.append('</urlset>')
open('sitemap-via.xml', 'w', encoding='utf-8').write(NL.join(lines) + NL)
print('sitemap-via.xml:', len(slugs), 'stop urls + 1 hub')

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
