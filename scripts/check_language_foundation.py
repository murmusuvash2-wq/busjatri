#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
legacy_fn = re.compile(r"function\s+(?:toggleTheme|setLang)\s*\(", re.I)
legacy_attr = re.compile(r"onclick\s*=.*(?:toggleTheme|setLang)\s*\(", re.I)

for p in ROOT.rglob("*.html"):
    if ".git" in p.parts:
        continue
    s = p.read_text(encoding="utf-8", errors="ignore")
    if legacy_fn.search(s):
        errors.append(str(p) + ": legacy language/theme function")
    if legacy_attr.search(s):
        errors.append(str(p) + ": legacy inline language/theme handler")
    if "js/hdr.js?v=" in s and "js/lang.js?v=" not in s:
        errors.append(str(p) + ": hdr.js present without central lang.js")

if errors:
    print("LANGUAGE FOUNDATION CHECK FAILED")
    for e in errors[:100]:
        print(" -", e)
    sys.exit(1)

print("LANGUAGE FOUNDATION CHECK PASSED")
print(" - generated HTML has no legacy language/theme controller")
print(" - shared hdr.js pages include central lang.js")
