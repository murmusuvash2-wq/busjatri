# WBTC departure board removal (user decision, 2026-09-26):
# WBTC data has 9 timed departures out of 948 buses (0%) - the depo departure
# board would render "No departures found" and mislead users.
# Rule: an operator page only gets the departure board when at least 25% of
# its buses carry a departure time. WBTC (0%) loses the board; SBSTC/NBSTC
# (98%) and Shyamoli (100%) keep theirs.

import re

GENOP = 'scripts/gen_operator_pages.py'

g = open(GENOP, encoding='utf-8').read()

if 'timed_n * 4' in g:
    print('already applied')
    raise SystemExit(0)

old = (
    "    board = (\"<section id='bjLive' style='margin-top:16px'></section>\" +\n"
    "        \"<script>window.bjOpCfg = \" + json.dumps({'name': op['name'], 'bn': bn_short, 'token': op_token, 'count': len(buses)}, ensure_ascii=False) + \"; window.bjOpData = \" + json.dumps(lv_rows, ensure_ascii=False) + \";</script>\" +\n"
    "        \"<script src='../js/op-board.js?v=opsf20260926' defer></script>\")\n"
)
new = (
    "    timed_n = sum(1 for r in lv_rows if r[4].strip())\n"
    "    if timed_n * 4 < len(lv_rows):\n"
    "        # operator has (almost) no departure times in our data (WBTC: 9/948):\n"
    "        # an empty 'No departures found' board would mislead - skip the board\n"
    "        board = ''\n"
    "    else:\n"
    "        board = (\"<section id='bjLive' style='margin-top:16px'></section>\" +\n"
    "            \"<script>window.bjOpCfg = \" + json.dumps({'name': op['name'], 'bn': bn_short, 'token': op_token, 'count': len(buses)}, ensure_ascii=False) + \"; window.bjOpData = \" + json.dumps(lv_rows, ensure_ascii=False) + \";</script>\" +\n"
    "            \"<script src='../js/op-board.js?v=opsf20260926' defer></script>\")\n"
)
assert old in g, 'board block not found'
g = g.replace(old, new, 1)

import ast
ast.parse(g)
with open(GENOP, 'w', encoding='utf-8') as fh:
    fh.write(g)
print('OK')
