#!/usr/bin/env python3
# BusJatri brand patch: circular logo in every header + new favicon (navy front-bus),
# apple-touch-icon + PWA icons refreshed. Idempotent, line-based, no regex.
# Icons are drawn with Pillow (see workflow: pip install pillow).
import base64, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)
IMG_TAG = '<img class="brand-logo" src="/logo.png" alt="BusJatri" style="width:30px;height:30px;border-radius:50%">'
FAVICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="15" fill="#1d2a4d"/><rect x="8" y="20" width="5" height="11" rx="2.5" fill="#fff"/><rect x="51" y="20" width="5" height="11" rx="2.5" fill="#fff"/><rect x="14" y="11" width="36" height="36" rx="7" fill="#fff"/><rect x="18.5" y="15.5" width="27" height="12.5" rx="3.5" fill="#1d2a4d"/><rect x="21" y="17.5" width="10" height="8.5" rx="1.5" fill="#3a4a75"/><rect x="24" y="31" width="16" height="4.5" rx="1.5" fill="#f59e0b"/><rect x="17.5" y="39" width="7" height="4.5" rx="2" fill="#f59e0b"/><rect x="39.5" y="39" width="7" height="4.5" rx="2" fill="#f59e0b"/><rect x="18" y="51" width="28" height="6" rx="3" fill="#f59e0b"/><circle cx="32" cy="49.5" r="7.5" fill="#fff"/><circle cx="32" cy="49.5" r="3.2" fill="#1d2a4d"/></svg>'
LOGO_B64 = (
    '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'
)

FAV_LINES = [
    '<link rel="icon" type="image/svg+xml" href="/favicon.svg">',
    '<link rel="icon" type="image/png" sizes="48x48" href="/favicon.png">',
]
APPLE_LINE = '<link rel="apple-touch-icon" href="/apple-touch-icon.png" />'

BLOCK_TAGS = ('</a>', '</div>', '</header', '</h1', '</h2', '</h3', '<p>', '<p ', '<img', '<body')

NAVY = (29, 42, 77, 255)
NAVY_LT = (58, 74, 117, 255)
ORANGE = (245, 158, 11, 255)
WHITE = (255, 255, 255, 255)

def make_icon(size, rounded=True, scale=1.0):
    from PIL import Image, ImageDraw
    SS = 4
    im = Image.new('RGBA', (size * SS, size * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size * SS
    if rounded:
        d.rounded_rectangle([0, 0, s, s], radius=int(s * 15 / 64), fill=NAVY)
    else:
        d.rectangle([0, 0, s, s], fill=NAVY)
    u = s / 64.0
    def T(v):
        return (v - 32) * scale + 32
    def R(x0, y0, x1, y1, r, fill):
        d.rounded_rectangle([u * T(x0), u * T(y0), u * T(x1), u * T(y1)], radius=u * r * scale, fill=fill)
    def C(cx, cy, r, fill):
        d.ellipse([u * (T(cx) - r * scale), u * (T(cy) - r * scale), u * (T(cx) + r * scale), u * (T(cy) + r * scale)], fill=fill)
    R(8, 20, 13, 31, 2.5, WHITE); R(51, 20, 56, 31, 2.5, WHITE)
    R(14, 11, 50, 47, 7, WHITE)
    R(18.5, 15.5, 45.5, 28, 3.5, NAVY)
    R(21, 17.5, 31, 26, 1.5, NAVY_LT)
    R(24, 31, 40, 35.5, 1.5, ORANGE)
    R(17.5, 39, 24.5, 43.5, 2, ORANGE); R(39.5, 39, 46.5, 43.5, 2, ORANGE)
    R(18, 51, 46, 57, 3, ORANGE)
    C(32, 49.5, 7.5, WHITE); C(32, 49.5, 3.2, NAVY)
    return im.resize((size, size), Image.LANCZOS)

def write_assets():
    p = os.path.join(ROOT, 'logo.png')
    data = base64.b64decode(LOGO_B64)
    if not (os.path.exists(p) and open(p, 'rb').read() == data):
        open(p, 'wb').write(data)
        print('asset written: logo.png')
    p = os.path.join(ROOT, 'favicon.svg')
    if not (os.path.exists(p) and open(p).read() == FAVICON_SVG):
        open(p, 'w').write(FAVICON_SVG)
        print('asset written: favicon.svg')
    pngs = [
        ('favicon.png', lambda: make_icon(48)),
        ('apple-touch-icon.png', lambda: make_icon(180, rounded=False)),
        ('icons/icon-192.png', lambda: make_icon(192)),
        ('icons/icon-512.png', lambda: make_icon(512)),
        ('icons/icon-maskable-192.png', lambda: make_icon(192, rounded=False, scale=0.72)),
        ('icons/icon-maskable-512.png', lambda: make_icon(512, rounded=False, scale=0.72)),
    ]
    import io
    for rel, fn in pngs:
        p = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        buf = io.BytesIO()
        fn().save(buf, format='PNG')
        data = buf.getvalue()
        if not (os.path.exists(p) and open(p, 'rb').read() == data):
            open(p, 'wb').write(data)
            print('asset written:', rel)

def patch_text(text):
    lines = text.split(NL)
    has_apple = 'apple-touch-icon' in text
    insert_apple = not has_apple
    out = []
    changed = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'rel="icon"' in line and 'data:image/svg+xml' in line:
            indent = line[:len(line) - len(line.lstrip())]
            for fl in FAV_LINES:
                out.append(indent + fl)
            if insert_apple:
                out.append(indent + APPLE_LINE)
            changed = True
            i += 1
            continue
        if 'apple-touch-icon' in line and 'href="apple-touch-icon.png"' in line:
            line = line.replace('href="apple-touch-icon.png"', 'href="/apple-touch-icon.png"')
            changed = True
        if 'Bus<span>Jatri</span>' in line:
            if '<svg' in line and '</svg>' in line:
                a = line.find('<svg')
                b = line.find('</svg>') + 6
                line = line[:a] + IMG_TAG + line[b:]
                changed = True
            else:
                j = len(out) - 1
                start = -1
                steps = 0
                while j >= 0 and steps < 6:
                    if '<svg' in out[j]:
                        ok = True
                        for k in range(j + 1, len(out)):
                            for t in BLOCK_TAGS:
                                if t in out[k]:
                                    ok = False
                        if ok:
                            start = j
                        break
                    if any(t in out[j] for t in ('</a>', '</div>', '</header', '<body')):
                        break
                    j -= 1
                    steps += 1
                if start >= 0:
                    ind = out[start][:len(out[start]) - len(out[start].lstrip())]
                    out[start] = ind + IMG_TAG
                    for k in range(start + 1, len(out)):
                        out[k] = ''
                    changed = True
        out.append(line)
        i += 1
    return NL.join(out), changed

def iter_targets():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in ('.git', '__pycache__', 'node_modules', 'data-raw')]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if fn.endswith('.html'):
                yield p
            elif fn.endswith('.py') and fn.startswith('gen_') and 'patch_' not in fn:
                yield p
            elif fn.endswith('.py') and fn in ('finalize_pages.py', 'apply_seo_redesign.py'):
                yield p

def main():
    write_assets()
    from PIL import Image
    img = Image.open(os.path.join(ROOT, 'logo.png'))
    img.load()
    if img.size != (160, 160):
        print('logo.png size mismatch:', img.size)
        sys.exit(1)
    touched = 0
    scanned = 0
    for p in iter_targets():
        scanned += 1
        text = open(p, encoding='utf-8').read()
        if 'rel="icon"' not in text and 'Bus<span>Jatri</span>' not in text and 'apple-touch-icon' not in text:
            continue
        new, changed = patch_text(text)
        if changed:
            open(p, 'w', encoding='utf-8').write(new)
            touched += 1
    print('scanned:', scanned, 'patched:', touched)

if __name__ == '__main__':
    main()
