#!/usr/bin/env python3
"""Auto cache-bust: stamp every local js/css reference with a content hash.

Runs LAST in every build workflow. For each .html page, every
`.../js/x.js` / `.../css/x.css` reference gets `?v=<8-char hash of the
asset's bytes>`. When an asset changes, its hash changes, every page
that loads it asks for a new URL, and Cloudflare fetches the fresh
file -- no manual version bumping, and the bug cannot silently come
back behind a stale cache.

Idempotent: unchanged assets keep the same hash, so re-runs produce no
diff.
"""
import os, re, hashlib, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def hash_assets():
    h = {}
    for pat in ("js/*.js", "css/*.css"):
        for f in glob.glob(os.path.join(ROOT, pat)):
            h[os.path.basename(f)] = hashlib.sha1(open(f, "rb").read()).hexdigest()[:8]
    return h

# (optional ../) js|css / name . ext   with optional ?v=...
REF = re.compile(r'((?:\.\./)*)((?:js|css)/([A-Za-z0-9_.\-]+\.(?:js|css)))(?:\?v=[A-Za-z0-9_.\-]+)?')

def main():
    hashes = hash_assets()
    if not hashes:
        print("cache-bust: no assets found"); return
    pages = refs = 0
    for path in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        if os.sep + ".git" + os.sep in path:
            continue
        s = open(path, encoding="utf-8").read()
        box = {"n": 0}
        def repl(m):
            prefix, rel, base = m.group(1), m.group(2), m.group(3)
            h = hashes.get(base)
            if not h:
                return m.group(0)
            new = "%s%s?v=%s" % (prefix, rel, h)
            if new != m.group(0):
                box["n"] += 1
            return new
        ns = REF.sub(repl, s)
        if ns != s:
            open(path, "w", encoding="utf-8").write(ns)
            pages += 1; refs += box["n"]
    print("cache-bust: %d pages updated, %d refs stamped" % (pages, refs))

if __name__ == "__main__":
    main()
