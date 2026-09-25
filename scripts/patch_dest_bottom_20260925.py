#!/usr/bin/env python3
# Move "Popular Destinations" section to the very end of the homepage (below Popular Routes).
# Order after patch: hero -> Operators -> Live Departures -> Popular Routes -> Destinations.
# Also bumps app.js cache buster. Idempotent, line-based, no regex.
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)
BT = chr(96)

def find_title_line(lines, marker):
    for i, l in enumerate(lines):
        if marker in l:
            return i
    return None

def section_bounds(lines, title_idx):
    start = title_idx
    while start > 0 and lines[start].strip() != '<div class="section">':
        start -= 1
    if lines[start].strip() != '<div class="section">':
        return None, None
    end = title_idx
    while end < len(lines) - 1 and lines[end].strip() != '</div>':
        end += 1
    if end + 1 < len(lines) and lines[end + 1].strip() == '</div>' and not lines[end + 1].rstrip().endswith(BT + ';'):
        end += 1
    return start, end

def main():
    app_path = os.path.join(ROOT, 'js', 'app.js')
    lines = open(app_path, encoding='utf-8').read().split(NL)
    dest_t = find_title_line(lines, 'Popular Destinations</span>')
    routes_t = find_title_line(lines, 'Popular Routes</span>')
    if dest_t is None or routes_t is None:
        print('titles not found')
        sys.exit(1)
    ds, de = section_bounds(lines, dest_t)
    rs, _ = section_bounds(lines, routes_t)
    if ds is None or rs is None:
        print('sections not found')
        sys.exit(1)
    if de < rs:
        block = lines[ds:de + 1]
        del lines[ds:de + 1]
        routes_t = find_title_line(lines, 'Popular Routes</span>')
        rs, _ = section_bounds(lines, routes_t)
        if rs is None:
            print('routes section lost after cut')
            sys.exit(1)
        tpl_end = None
        for j in range(routes_t, len(lines)):
            if lines[j].rstrip().endswith(BT + ';'):
                tpl_end = j
                break
        if tpl_end is None:
            print('homeHTML template end not found')
            sys.exit(1)
        replacement = ['  </div>'] + block[:-1] + ['  </div>' + BT + ';']
        lines[tpl_end:tpl_end + 1] = replacement
        open(app_path, 'w', encoding='utf-8').write(NL.join(lines))
        print('app.js: destinations moved below routes')
    else:
        print('app.js: already below routes')
    idx_path = os.path.join(ROOT, 'index.html')
    itext = open(idx_path, encoding='utf-8').read()
    if 'js/app.js?v=brand20260925f' in itext:
        itext = itext.replace('js/app.js?v=brand20260925f', 'js/app.js?v=brand20260925g')
        open(idx_path, 'w', encoding='utf-8').write(itext)
        print('index.html: buster bumped to brand20260925g')
    elif 'js/app.js?v=brand20260925g' in itext:
        print('index.html: buster already brand20260925g')
    else:
        print('index.html: expected buster not found')
        sys.exit(1)
    print('done')

if __name__ == '__main__':
    main()
