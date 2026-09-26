# Home board grace: 30 min -> 10 min (user decision 2026-09-26)
import io, sys

p = 'js/ux-fixes.js'
s = io.open(p, encoding='utf-8').read()
n = s.count('< -30)')
assert n == 3, 'expected 3 grace spots, found %d' % n
s = s.replace('< -30)', '< -10)')
io.open(p, 'w', encoding='utf-8').write(s)
print('ux-fixes.js: grace -30 -> -10 in %d spots' % n)

p2 = 'index.html'
s2 = io.open(p2, encoding='utf-8').read()
old = 'ux-fixes.js?v=rpt20260926a'
new = 'ux-fixes.js?v=rpt20260926b'
assert s2.count(old) == 1, 'buster string count: %d' % s2.count(old)
s2 = s2.replace(old, new)
io.open(p2, 'w', encoding='utf-8').write(s2)
print('index.html: buster %s -> %s' % (old, new))

# verify
s3 = io.open(p, encoding='utf-8').read()
assert s3.count('< -10)') == 3 and '< -30)' not in s3
assert '<title>' in s2 and new in io.open(p2, encoding='utf-8').read()
print('verify OK: 3x -10, no -30 left, buster bumped')
