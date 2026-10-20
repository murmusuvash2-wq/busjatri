#!/usr/bin/env python3
"""BusJatri Phase 2 frontend architecture guard.

This is a regression guard, not a data validator:
- language/theme controllers must stay centralized
- generated-page source must not reintroduce inline header handlers
- search autocomplete must remain explicitly English/static
- central language assets must exist
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

def read(rel):
    p = ROOT / rel
    if not p.exists():
        errors.append(f"missing required file: {rel}")
        return ""
    return p.read_text(encoding="utf-8", errors="replace")

lang = read("js/lang.js")
hdr = read("js/hdr.js")
search = read("js/stop-search-all.js")

if "window.BJLang" not in lang or "setLang" not in lang:
    errors.append("js/lang.js is not the central BJLang controller")

if "bj:langchange" not in lang or "bj:langchange" not in hdr:
    errors.append("language change event contract is missing")

if ".ac-drop" not in lang or "#stopList" not in lang:
    errors.append("central translator does not protect English search/autocomplete UI")

if ".ac-drop" not in search or "acShow" not in search:
    errors.append("search autocomplete architecture is missing")

# Source generators are the important boundary: generated HTML may be rebuilt,
# but generators must never recreate the old inline controller.
generator_paths = [
    "scripts/gen_route_v2.py",
    "scripts/gen_via_v2.py",
    "scripts/gen_btt_v2.py",
    "scripts/gen_stand_v2.py",
    "scripts/gen_via_stop_v2.py",
    "scripts/gen_operator_pages.py",
]
legacy_patterns = [
    r'onclick\s*=\s*["\']toggleTheme\s*\(',
    r'onclick\s*=\s*["\']setLang\s*\(',
    r'<script>\s*var\s+MOON\s*=',
]
for rel in generator_paths:
    text = read(rel)
    for pat in legacy_patterns:
        if re.search(pat, text, re.I | re.S):
            errors.append(f"{rel} still contains legacy header controller pattern: {pat}")

# The generated-page sync workflow must exist so already-generated output cannot
# permanently drift from the source architecture.
sync = read(".github/workflows/language-system-sync.yml")
if "function setLang" not in sync or "var MOON=" not in sync:
    errors.append("language-system-sync workflow no longer contains its legacy-controller cleanup rule")
if "permissions:" not in sync or "contents: write" not in sync:
    errors.append("language-system-sync workflow lacks contents write permission")

if errors:
    print("PHASE2 FRONTEND ARCHITECTURE: FAIL")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("PHASE2 FRONTEND ARCHITECTURE: PASS")
print(" - central BJLang contract")
print(" - shared language-change event")
print(" - English-only autocomplete boundary")
print(" - generator legacy-handler guard")
print(" - generated-page cleanup workflow")
