# Search fix: remove 'howrah' from the Kolkata place-alias group in BOTH
# js/app.js (SPA search) and scripts/gen_route_v2.py (route page matching).
# Why: 'howrah' was grouped with kolkata/esplanade/garia/karunamoyee, so
# searching "Howrah to X" matched Karunamoyee/Kolkata-origin buses (85+
# Karunamoyee buses) and Kolkata route pages showed Howrah buses as
# through services. Howrah Station/Maidan are distinct termini - a Howrah
# search must only match Howrah-origin buses. Route pages are regenerated
# by the workflow after this patch.
# Backslash-free source; single string replacement per file.

OLD = "'esplanade', 'howrah', 'santragachi'"
NEW = "'esplanade', 'santragachi'"
FILES = ['js/app.js', 'scripts/gen_route_v2.py']


def main():
    ok = 0
    for f in FILES:
        with open(f, encoding='utf-8') as fh:
            s = fh.read()
        if OLD not in s:
            if NEW in s:
                print(f, ': already patched')
                ok += 1
            else:
                print(f, ': pattern not found - ABORT')
            continue
        s = s.replace(OLD, NEW, 1)
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(s)
        print(f, ': howrah removed from kolkata alias group')
        ok += 1
    if ok != len(FILES):
        raise SystemExit('patch failed for at least one file')
    print('done')


if __name__ == '__main__':
    main()
