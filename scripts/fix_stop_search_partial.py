# Fix: stop search (Search V3) only searched FULL_BUSES when ANY bus detail
# page had been opened. loadFullBus() turns FULL_BUSES into a PARTIAL
# object (one entry per viewed bus; the full bus-full.json does not even
# exist in the repo), so `Object.values(FULL_BUSES || BUSES)` searched only
# the buses the user had already viewed. E.g. stop search "mejia" showed 1
# bus instead of 23 - KARUNAMOYEE (Raniganj->Kashipur, 5:50 AM / 2:45 PM
# at Mejia) vanished.
# Fix: prefer FULL_BUSES only when it is at least as large as the compact
# BUSES index (i.e. genuinely complete); otherwise use the compact index,
# which carries full stop coverage (sx/ux/dx rebuilt by rebuildCompactStops).
# Same line exists in js/ux-fixes.js (Search V2 - dead code, overridden by
# V3) - patched there too for consistency.
# Also bump the script cache-busters in index.html so browsers drop the
# cached buggy JS.
# Backslash-free source; string ops only.

NEW_LINE = ('var all = (FULL_BUSES && Object.keys(FULL_BUSES).length >= '
            'Object.keys(BUSES).length) ? Object.values(FULL_BUSES) : '
            'Object.values(BUSES);')
OLD_LINE = 'var all = Object.values(FULL_BUSES || BUSES);'

JS_FILES = ['js/stop-search-all.js', 'js/ux-fixes.js']

INDEX_OLD_NEW = [
    ('js/stop-search-all.js?v=bj20260922a', 'js/stop-search-all.js?v=bj20260924a'),
    ('js/ux-fixes.js?v=rpt20260921b', 'js/ux-fixes.js?v=rpt20260924a'),
]


def patch_js():
    for f in JS_FILES:
        with open(f, encoding='utf-8') as fh:
            s = fh.read()
        if OLD_LINE in s:
            s = s.replace(OLD_LINE, NEW_LINE, 1)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(s)
            print(f, ': patched')
        elif NEW_LINE in s:
            print(f, ': already patched')
        else:
            raise SystemExit(f + ': pattern not found - ABORT')


def patch_index():
    f = 'index.html'
    with open(f, encoding='utf-8') as fh:
        s = fh.read()
    for old, new in INDEX_OLD_NEW:
        if old in s:
            s = s.replace(old, new, 1)
            print('index.html:', old, '->', new)
        elif new in s:
            print('index.html:', new, 'already present')
        else:
            raise SystemExit('index.html: ' + old + ' not found - ABORT')
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(s)


def main():
    patch_js()
    patch_index()
    print('done')


if __name__ == '__main__':
    main()
