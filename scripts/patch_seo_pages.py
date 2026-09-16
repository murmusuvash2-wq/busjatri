#!/usr/bin/env python3
"""Inject the shared css/seo2.css + js/seo-ux.js tags into every bus-time-table/*.html page.

Run from anywhere:  python3 scripts/patch_seo_pages.py
Idempotent — safe to run repeatedly (skips pages already patched).

Adds:
  <link rel="stylesheet" href="../css/seo2.css?v=...">   (before </head>)
  <script src="../js/seo-ux.js?v=..." defer></script>   (before </body>)

seo-ux.js gives every static page the EN/বাংলা toggle, the dark-mode button,
a compact hero layout, the amber Search button and common-label translation.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BTT = ROOT / "bus-time-table"
VERSION = "20260916a"

LINK = '<link rel="stylesheet" href="../css/seo2.css?v=' + VERSION + '">'
SCRIPT = '<script src="../js/seo-ux.js?v=' + VERSION + '" defer></script>'


def patch(path: pathlib.Path) -> bool:
    html = path.read_text(encoding="utf-8")
    orig = html
    if "seo2.css" not in html:
        if "</head>" in html:
            html = html.replace("</head>", "    " + LINK + "\n</head>", 1)
        else:
            print(f"!! no </head> in {path.name}")
            return False
    if "seo-ux.js" not in html:
        if "</body>" in html:
            html = html.replace("</body>", "  " + SCRIPT + "\n</body>", 1)
        else:
            print(f"!! no </body> in {path.name}")
            return False
    if html != orig:
        path.write_text(html, encoding="utf-8")
        return True
    return False


def main() -> None:
    if not BTT.is_dir():
        print("bus-time-table/ not found — run from the repo root")
        sys.exit(1)
    files = sorted(BTT.glob("*.html"))
    changed = 0
    for p in files:
        if patch(p):
            changed += 1
    print(f"checked {len(files)} pages, updated {changed}")


if __name__ == "__main__":
    main()
