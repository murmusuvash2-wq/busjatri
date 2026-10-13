#!/usr/bin/env python3
"""app/build.py - BusJatri app build.

The front-end source lives in app/ grouped by system:
  app/search/      search, fuzzy, aliases, autocomplete, alt-route
  app/i18n/        EN / BN language
  app/theme/       dark / light
  app/pwa/         install, icons, service worker
  app/components/  header, op-board, route-slider, bus-page, extras, ux-fixes ...

This copies them to js/<name>.js (the path the pages load), so pages never change.
Idempotent. Edit in app/, run the build."""
import os, shutil, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP  = os.path.join(ROOT, "app")
JS   = os.path.join(ROOT, "js")

def main():
    n = 0
    for f in sorted(glob.glob(os.path.join(APP, "**", "*.js"), recursive=True)):
        dst = os.path.join(JS, os.path.basename(f))
        if not os.path.exists(dst) or open(f,"rb").read() != open(dst,"rb").read():
            shutil.copy(f, dst); n += 1
            print("app ->", os.path.basename(f))
    print(f"app/build.py: {n} file(s) copied to js/")

if __name__ == "__main__":
    main()
