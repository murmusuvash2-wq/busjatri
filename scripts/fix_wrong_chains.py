# Fix the 25 wrong-chain buses found in the 2026-09-24 data audit.
# Source check results (bussathi.in / wbbus.in, fetched via ZenRows):
#   - 23 bussathi.in pages have NO usable timetable (empty tables or a
#     timetable belonging to a different bus - the source site itself is
#     broken for these buses). Their stoppage chains in our data are
#     copies of OTHER buses' chains, so they are removed (option 2).
#     Origin/destination/departure/arrival are kept - those came from the
#     source listings and are confirmed correct.
#   - 2 wbbus.in pages have correct timetables; those chains are
#     repaired from the source (option 1):
#       BARNALI (WB33A9797) Neradeul->Garhbeta:
#         Neradeul 7:40 AM, Chandrakona Town, Raskundu, Garhbeta (down 6:00 PM)
#       HILLTOP SUPER (WB55B6775) Ajodhya Hills->Purulia:
#         Ajodhya Hills 7:40 AM/7:30 PM, Sirkabad 8:20 AM/7:10 PM,
#         Aharara 8:30 AM, Damda, Purulia 9:30 AM/6:10 PM
# Backslash-free source; string ops only; idempotent.

DATA = 'data/busjatri_data.json'

REMOVE_IDS = [
    'bussathi-green-valley-238',
    'bussathi-krishna-803',
    'bussathi-tithy-834',
    'bussathi-avijan-838',
    'bussathi-krishna-gopal-862',
    'bussathi-radha-damodar-864',
    'bussathi-sahin-865',
    'bussathi-western-diamond-869',
    'bussathi-sbstc-870',
    'bussathi-sbstc-871',
    'bussathi-sbstc-872',
    'bussathi-sbstc-873',
    'bussathi-sbstc-875',
    'bussathi-sbstc-874',
    'bussathi-bhagyalaxmi-878',
    'bussathi-arman-884',
    'bussathi-green-valley-885',
    'bussathi-gurjot-886',
    'bussathi-laxmi-narayan-890',
    'bussathi-maa-kali-893',
    'bussathi-maa-sarada-895',
    'bussathi-madan-mohan-897',
    'bussathi-pally-duth-901',
]

BARNALI = 'wbbus-in-barnali-1266'
HILLTOP = 'wbbus-in-hilltop-super-1309'

BARNALI_CHAIN = (
    '[{"no": 1, "name": "Neradeul", "up_time": "7:40 AM", "down_time": ""},'
    ' {"no": 2, "name": "Chandrakona Town", "up_time": "", "down_time": ""},'
    ' {"no": 3, "name": "Raskundu", "up_time": "", "down_time": ""},'
    ' {"no": 4, "name": "Garhbeta", "up_time": "", "down_time": "6:00 PM"}]'
)

HILLTOP_CHAIN = (
    '[{"no": 1, "name": "Ajodhya Hills", "up_time": "7:40 AM", "down_time": "7:30 PM"},'
    ' {"no": 2, "name": "Sirkabad", "up_time": "8:20 AM", "down_time": "7:10 PM"},'
    ' {"no": 3, "name": "Aharara", "up_time": "8:30 AM", "down_time": ""},'
    ' {"no": 4, "name": "Damda", "up_time": "", "down_time": ""},'
    ' {"no": 5, "name": "Purulia", "up_time": "9:30 AM", "down_time": "6:10 PM"}]'
)

ID_MARK = '"id": "'


def record_span(s, bid):
    pos = s.find(ID_MARK + bid + '"')
    if pos < 0:
        raise SystemExit('bus not found: ' + bid)
    nxt = s.find(ID_MARK, pos + 10)
    end = nxt if nxt > 0 else len(s)
    return pos, end


def stop_array_span(s, pos, end):
    sp = s.find('"stoppages":', pos)
    if sp < 0 or sp > end:
        raise SystemExit('stoppages not found in record at ' + str(pos))
    ob = s.find('[', sp)
    if ob < 0 or ob > end or ob - sp > 20:
        raise SystemExit('stoppages open bracket not found at ' + str(pos))
    cl = s.find(']', ob)
    if cl < 0 or cl > end:
        raise SystemExit('stoppages close not found in record at ' + str(pos))
    return ob, cl


def set_field(s, pos, end, field, value):
    mk = '"' + field + '": "'
    fp = s.find(mk, pos)
    if fp < 0 or fp > end:
        print('   field not found in record:', field)
        return s
    vs = fp + len(mk)
    ve = s.find('"', vs)
    old = s[vs:ve]
    if old == value:
        return s
    print('   %s: %s -> %s' % (field, old, value))
    return s[:vs] + value + s[ve:]


def set_int_field(s, pos, end, field, value):
    mk = '"' + field + '": '
    fp = s.find(mk, pos)
    if fp < 0 or fp > end:
        print('   field not found:', field)
        return s
    vs = fp + len(mk)
    ve = s.find(',', vs)
    if ve < 0 or ve > end:
        ve = s.find('}', vs)
    old = s[vs:ve].strip()
    if old == str(value):
        return s
    print('   %s: %s -> %s' % (field, old, value))
    return s[:vs] + str(value) + s[ve:]


def main():
    with open(DATA, encoding='utf-8') as fh:
        s = fh.read()

    for bid in REMOVE_IDS:
        pos, end = record_span(s, bid)
        ob, cl = stop_array_span(s, pos, end)
        if s[ob:cl + 1] == '[]':
            print(bid, ': already empty')
            continue
        s = s[:ob] + '[]' + s[cl + 1:]
        pos, end = record_span(s, bid)
        s = set_int_field(s, pos, end, 'total_stoppages', 0)
        print(bid, ': stoppage chain removed')

    for bid, chain, dep, arr in [
        (BARNALI, BARNALI_CHAIN, '7:40 AM', None),
        (HILLTOP, HILLTOP_CHAIN, '7:40 AM', '9:30 AM'),
    ]:
        pos, end = record_span(s, bid)
        ob, cl = stop_array_span(s, pos, end)
        if s[ob:cl + 1] == chain:
            print(bid, ': already repaired')
        else:
            s = s[:ob] + chain + s[cl + 1:]
            pos, end = record_span(s, bid)
            n = 4 if bid == BARNALI else 5
            s = set_int_field(s, pos, end, 'total_stoppages', n)
            print(bid, ': chain repaired from wbbus.in')
        pos, end = record_span(s, bid)
        s = set_field(s, pos, end, 'departure_time', dep)
        if arr:
            pos, end = record_span(s, bid)
            s = set_field(s, pos, end, 'arrival_time', arr)

    with open(DATA, 'w', encoding='utf-8') as fh:
        fh.write(s)
    print('done')


if __name__ == '__main__':
    main()
