#!/usr/bin/env python3
"""Guard: patch_fb_batch4.py crashes (assert) when a bus it wants to
update was already removed by the dedup step of a previous pipeline run
(e.g. wbbus-in-kalosona-1331, deduped by rule 3 on 2026-09-19). This
patcher makes that assert a graceful skip BEFORE batch4 runs (file name
sorts first alphabetically). Idempotent, no data changes."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

p = ROOT / 'scripts' / 'patch_fb_batch4.py'
s = p.read_text(encoding='utf-8')

anchor = '        assert b, f"missing {u[\'id\']}"'
repl = (
    '        if not b:\n'
    '            print(f"{u[\'id\']}: no longer in data (deduped) - skip")\n'
    '            continue'
)

if 'no longer in data (deduped) - skip' in s:
    print('ok (batch4 guard already applied)')
    sys.exit(0)

if s.count(anchor) != 1:
    print('FAIL: batch4 assert anchor not found or ambiguous (count=%d)' % s.count(anchor))
    sys.exit(1)

s = s.replace(anchor, repl)
if '--write' in sys.argv:
    p.write_text(s, encoding='utf-8')
    print('patched scripts/patch_fb_batch4.py (assert -> graceful skip)')
else:
    print('would patch scripts/patch_fb_batch4.py')
