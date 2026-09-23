# Generates sitemap-via.xml from the via/ folder (2,606 stop pages),
# keeps robots.txt in sync, and hooks sitemap regen into via-stop-pages.yml.
# Idempotent: safe to re-run. Backslash-free source.
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

# --- robots.txt sync ---
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

# --- hook into via-stop-pages.yml so future via regens refresh the sitemap ---
wf = '.github/workflows/via-stop-pages.yml'
y = open(wf, encoding='utf-8').read()
if 'patch_via_sitemap' not in y:
    step = (
        '      - name: Regenerate via sitemap' + NL +
        '        run: python3 scripts/patch_via_sitemap.py' + NL + NL
    )
    y = y.replace('      - name: Commit and push if changed', step + '      - name: Commit and push if changed')
    y = y.replace(
        'git add scripts/gen_via_stop_v2.py via',
        'git add scripts/gen_via_stop_v2.py scripts/patch_via_sitemap.py sitemap-via.xml via'
    )
    open(wf, 'w', encoding='utf-8').write(y)
    print('via-stop-pages.yml: sitemap step added')
else:
    print('via-stop-pages.yml: already ok')
