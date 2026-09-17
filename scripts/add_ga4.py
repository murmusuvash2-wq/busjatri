#!/usr/bin/env python3
"""Inject the GA4 gtag snippet into every HTML page (idempotent).

Runs standalone and is also invoked by finalize_pages.py, so every time pages
are regenerated the analytics tag is re-applied automatically. GA measurement
IDs are public values — they appear in every page's HTML by design.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GA_ID = "G-L4E3D1YX9X"

SNIPPET = (
    "<!-- Google tag (gtag.js) - GA4 -->\n"
    '<script async src="https://www.googletagmanager.com/gtag/js?id=' + GA_ID + '"></script>\n'
    "<script>\n"
    "  window.dataLayer = window.dataLayer || [];\n"
    "  function gtag(){dataLayer.push(arguments);}\n"
    "  gtag('js', new Date());\n"
    "  gtag('config', '" + GA_ID + "');\n"
    "</script>\n"
)

PRIVACY_BULLET = (
    "      • <strong>Google Analytics (GA4)</strong> — anonymous traffic measurement; "
    "Google may set cookies to distinguish visitors.<br>\n"
)

def inject_html(p):
    s = p.read_text(encoding="utf-8")
    if GA_ID in s:
        return False
    i = s.lower().rfind("</head>")
    if i == -1:
        return False
    p.write_text(s[:i] + SNIPPET + s[i:], encoding="utf-8")
    return True

def main():
    count = 0
    pages = list(ROOT.glob("*.html")) + list((ROOT / "bus-time-table").glob("*.html"))
    for p in pages:
        try:
            if inject_html(p):
                count += 1
        except Exception as e:
            print("  skip", p.name, e)
    print(f"GA4 ({GA_ID}) injected into {count} HTML files")

    # keep the privacy policy honest about analytics
    pp = ROOT / "privacy-policy.html"
    if pp.exists():
        s = pp.read_text(encoding="utf-8")
        if "Google Analytics" not in s:
            anchor = "      • <strong>Google Fonts</strong>"
            if anchor in s:
                s = s.replace(anchor, PRIVACY_BULLET + anchor, 1)
                pp.write_text(s, encoding="utf-8")
                print("privacy-policy.html: added Google Analytics bullet")
        s = pp.read_text(encoding="utf-8")
        s2 = s.replace("Last updated: 14 September 2026", "Last updated: 17 September 2026")
        if s2 != s:
            pp.write_text(s2, encoding="utf-8")
            print("privacy-policy.html: date bumped")

if __name__ == "__main__":
    main()
