#!/usr/bin/env python3
"""One-time patch (2026-09-17): the wbbustime.in all-routes page links to
route pages with RELATIVE hrefs (/bus-timetable/...), but the crawler only
matched absolute URLs — so discovery returned 0 route pages. This makes the
link regex accept both and builds full URLs. Idempotent; fails loudly.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'scripts' / 'fill_missing_times.py'

def patch(old, new):
    s = P.read_text(encoding='utf-8')
    if new in s:
        print('  already applied')
        return
    if old not in s:
        raise SystemExit(f'ANCHOR MISSING: {old[:70]!r}')
    P.write_text(s.replace(old, new), encoding='utf-8')
    print('  patched')

patch(
'''def find_candidate_urls_on_wbbustime(missing_buses):
    """Discover wbbustime.in route pages and index them by (from, to)."""
    html = fetch("https://wbbustime.in/all-routes/")
    links = re.findall(r'href="(https://wbbustime\\.in/bus-timetable/[^"#?]+)"[^>]*>([^<]+)', html)''',
'''def find_candidate_urls_on_wbbustime(missing_buses):
    """Discover wbbustime.in route pages and index them by (from, to)."""
    html = fetch("https://wbbustime.in/all-routes/")
    # links may be absolute (https://wbbustime.in/bus-timetable/...) or relative (/bus-timetable/...)
    links = re.findall(r'href="(?:https://wbbustime\\.in)?(/bus-timetable/[^"#?]+)"[^>]*>([^<]+)', html)''')

patch(
'''    idx = {}
    for url, text in links:''',
'''    idx = {}
    for path, text in links:
        url = "https://wbbustime.in" + path''')

print('crawler fix done')
