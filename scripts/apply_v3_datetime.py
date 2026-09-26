#!/usr/bin/env python3
"""SBSTC v3 (2026-09-26, user request): replace Today/Tomorrow + time-of-day
chips with a real calendar date input + hour-only (12h AM/PM) select.
Applies to scripts/gen_operator_pages.py and js/op-board.js in repo root.
Idempotent: skips if opd20260926 buster already present.
Verifies final file md5s."""
import io
import ast
import hashlib
import sys

GP = 'scripts/gen_operator_pages.py'
OB = 'js/op-board.js'
EXPECT_GP = '7593f5e80c2bc56ee12038b4aa8bf5ef'
EXPECT_OB = 'f32489836db0cba139a9a4f0030daf73'


def done(p):
    return 'opd20260926' in io.open(p, encoding='utf-8').read()


def md5(p):
    return hashlib.md5(io.open(p, 'rb').read()).hexdigest()


def patch():
    # ---------------- op-board.js ----------------
    j = io.open(OB, encoding='utf-8').read()

    def sub(old, new, cnt=1):
        nonlocal_j[0] = nonlocal_j[0].replace(old, new)
        assert nonlocal_j[0].count(new) >= 1

    nonlocal_j = [j]

    # 1) DAY semantics -> selected date string ('' = today)
    assert nonlocal_j[0].count("var TOD = 'any', DAY = 'today';") == 1
    sub("var TOD = 'any', DAY = 'today';", "var TOD = 'any', DAY = '';")

    # 2) todOK -> hour filter + date helpers
    old_tod = """  function todOK(t) {
    if (TOD === 'any') return true;
    if (TOD === 'm') return t >= 240 && t < 720;
    if (TOD === 'd') return t >= 720 && t < 1020;
    return t >= 1020 || t < 240;
  }"""
    new_tod = """  function bjTodayStr() {
    function p(n) { return (n < 10 ? '0' : '') + n; }
    var d = new Date();
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  }
  function dateIsToday() { return !DAY || DAY === bjTodayStr(); }
  function todOK(t) {
    if (TOD === 'any') return true;
    return Math.floor(t / 60) === TOD;
  }"""
    assert old_tod in nonlocal_j[0]
    sub(old_tod, new_tod)

    # 3) board sort: not-today => full-day ascending
    assert nonlocal_j[0].count(".sort(DAY === 'tomorrow'") == 1
    sub(".sort(DAY === 'tomorrow'", ".sort(!dateIsToday()")

    # 4) search sort: today => grace-upcoming, else ascending
    old_s = "return DAY === 'tomorrow' ? a - c : ((a < minutesNow() - 30 ? a + 1440 : a) - minutesNow()) - ((c < minutesNow() - 30 ? c + 1440 : c) - minutesNow());"
    new_s = "return dateIsToday() ? ((a < minutesNow() - 30 ? a + 1440 : a) - minutesNow()) - ((c < minutesNow() - 30 ? c + 1440 : c) - minutesNow()) : a - c;"
    assert old_s in nonlocal_j[0]
    sub(old_s, new_s)

    # 5) replace chips wiring with date + hour listeners
    lines = nonlocal_j[0].split('\n')
    i0 = next(i for i, l in enumerate(lines) if "['bjDayChips', 'bjTodChips'].forEach" in l)
    i1 = None
    for i in range(i0, i0 + 30):
        if lines[i].rstrip() == '    });':
            i1 = i
            break
    assert i1 is not None
    new_block = """    var bjDateI = document.getElementById('bjDate');
    var bjHourS = document.getElementById('bjHour');
    if (bjDateI && !bjDateI.value) bjDateI.value = bjTodayStr();
    function syncFilters() {
      DAY = bjDateI ? bjDateI.value : '';
      TOD = (bjHourS && bjHourS.value !== 'any') ? parseInt(bjHourS.value, 10) : 'any';
      renderRows();
      var rs = document.getElementById('bjOpResults');
      if (rs && rs.getAttribute('data-q') === '1') window.bjSearchGo();
    }
    if (bjDateI) bjDateI.addEventListener('change', syncFilters);
    if (bjHourS) bjHourS.addEventListener('change', syncFilters);"""
    lines[i0:i1 + 1] = new_block.split('\n')
    nonlocal_j[0] = '\n'.join(lines)

    # 6) updPh: bilingual hour option label
    old_ph = """    function updPh() {
      var isBn = document.body.classList.contains('lang-bn');"""
    new_ph = """    function updPh() {
      var isBn = document.body.classList.contains('lang-bn');
      var hs0 = document.getElementById('bjHour');
      if (hs0 && hs0.options.length) hs0.options[0].text = isBn ? '\\u09af\\u09c7\\u0995\\u09cb\\u09a8\\u09cb \\u09b8\\u09ae\\u09df' : 'Any time';"""
    assert old_ph in nonlocal_j[0]
    sub(old_ph, new_ph)

    io.open(OB, 'w', encoding='utf-8').write(nonlocal_j[0])

    # ---------------- gen_operator_pages.py ----------------
    s = io.open(GP, encoding='utf-8').read()
    box = [s]

    def gsub(old, new, cnt=1):
        assert box[0].count(old) == cnt, old[:60]
        box[0] = box[0].replace(old, new)

    gsub("op-board.js?v=opc20260926", "op-board.js?v=opd20260926")

    gsub("'.bj-chip-row{display:flex;flex-wrap:wrap;gap:2px;margin-top:8px}'",
         "'.bj-chip-row{display:flex;flex-wrap:wrap;gap:2px;margin-top:8px}'\n"
         "                    '.bj-dt-row{display:flex;gap:10px;margin-top:10px}'\n"
         "                    '.bj-dt{flex:1;min-width:0}'\n"
         "                    '.bj-dt label{display:block;font-size:11px;letter-spacing:.12em;font-weight:700;"
         "color:var(--amber-ink,#6b4610);text-transform:uppercase;margin-bottom:6px}'\n"
         "                    '.bj-dt input,.bj-dt select{width:100%;padding:12px;border-radius:10px;"
         "border:1.5px solid var(--line,#ccc);background:var(--bg,#fff);font:inherit;font-size:15px;"
         "color:var(--ink,#211c16)}'\n"
         "                    '.bj-dt input:focus,.bj-dt select:focus{outline:none;border-color:var(--amber,#b8791f)}'")

    lines = box[0].split('\n')
    i0 = next(i for i, l in enumerate(lines) if 'bjDayChips' in l)
    i1 = next(i for i, l in enumerate(lines) if 'bjTodChips' in l)
    i_end = None
    for i in range(i1, i1 + 8):
        if lines[i].strip() == "'</div>'":
            i_end = i
            break
    assert i_end is not None
    opt_lines = ["'<option value=\"any\" selected>Any time</option>'"]
    for h in range(24):
        lbl = (h % 12) or 12
        ap = 'AM' if h < 12 else 'PM'
        opt_lines.append("'<option value=\"%d\">%d %s</option>'" % (h, lbl, ap))
    new_markup = (
        ["'<div class=\"bj-dt-row\">'",
         "'<div class=\"bj-dt\"><label for=\"bjDate\">\\U0001F4C5 <span class=\"label-en\">Date</span>"
         "<span class=\"label-bn\">\\u09a4\\u09be\\u09b0\\u09bf\\u0996</span></label>'",
         "'<input id=\"bjDate\" type=\"date\"></div>'",
         "'<div class=\"bj-dt\"><label for=\"bjHour\">\\U0001F550 <span class=\"label-en\">Time (hour)</span>"
         "<span class=\"label-bn\">\\u09b8\\u09ae\\u09df (\\u0998\\u09a3\\u09cd\\u099f\\u09be)</span></label>'",
         "'<select id=\"bjHour\">'"] + opt_lines +
        ["'</select></div>'", "'</div>'"])
    lines[i0:i_end + 1] = new_markup
    box[0] = '\n'.join(lines)
    ast.parse(box[0])
    io.open(GP, 'w', encoding='utf-8').write(box[0])


if __name__ == '__main__':
    if not done(GP) and not done(OB):
        patch()
    ok_gp = md5(GP) == EXPECT_GP
    ok_ob = md5(OB) == EXPECT_OB
    print('genop md5:', 'OK' if ok_gp else 'FAIL')
    print('op-board md5:', 'OK' if ok_ob else 'FAIL')
    if not (ok_gp and ok_ob):
        sys.exit(1)
    print('v3 patch applied & verified')
