# -*- coding: utf-8 -*-
import re, pathlib, ast

PAT = 'এখানে শুধু <b>(.*?)</b> থেকে ছাড়া বাস দেখানো হয়েছে।'
REP = 'এখানে শুধু সেই বাসগুলো দেখানো হয়েছে যেগুলো <b>\\1</b> থেকে ছাড়ে।'
GPAT = 'এখানে শুধু <b>{}</b> থেকে ছাড়া বাস দেখানো হয়েছে।'
GREP = 'এখানে শুধু সেই বাসগুলো দেখানো হয়েছে যেগুলো <b>{}</b> থেকে ছাড়ে।'
BPAT = 'শুধু সেই স্ট্যান্ড থেকে <b>ছাড়া</b> বাস দেখানো হয়।'
BREP = 'শুধু সেই বাস দেখানো হয় যেগুলো সেই স্ট্যান্ড থেকে ছাড়ে।'

n_html = 0
for f in sorted(pathlib.Path('bus-time-table').glob('*.html')):
    s = f.read_text(encoding='utf-8')
    s2, n = re.subn(PAT, REP, s)
    if n:
        f.write_text(s2, encoding='utf-8')
        n_html += n and 1
print('patched html files:', n_html)

g = pathlib.Path('scripts/gen_stand_v2.py')
s = g.read_text(encoding='utf-8')
assert GPAT in s, 'gen_stand_v2 pattern missing'
s2 = s.replace(GPAT, GREP)
ast.parse(s2)
g.write_text(s2, encoding='utf-8')
print('gen_stand_v2.py patched')

b = pathlib.Path('scripts/gen_btt_v2.py')
s = b.read_text(encoding='utf-8')
if BPAT in s:
    s2 = s.replace(BPAT, BREP)
    ast.parse(s2)
    b.write_text(s2, encoding='utf-8')
    print('gen_btt_v2.py patched')
else:
    print('gen_btt_v2.py: pattern not found (skip)')

left = [f.name for f in pathlib.Path('bus-time-table').glob('*.html')
        if 'থেকে ছাড়া বাস' in f.read_text(encoding='utf-8')]
assert not left, 'leftover files: %s' % left[:5]
assert n_html > 0, 'no html patched'
print('OK - all patched, no leftovers')
