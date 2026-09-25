#!/usr/bin/env python3
# Repairs 3 transcription-corrupted b64 chunk lines in scripts/patch_brand_20260925.py.
# Self-verifying: final LOGO_B64 must decode to the exact logo.png (md5 check).
import base64, hashlib, os, sys

NL = chr(10)
P = os.path.join('scripts', 'patch_brand_20260925.py')
MD5 = '6cd0a84c1c118b417122cdcf7f1b9fdf'
PREF = 'PzF8RzVpREFgZ35pfaCHPySZb1+OhZCelZi7ZjWkmJ2lsL7WoXzRwL0'

def inner(s):
    a = s.find(chr(39))
    b = s.rfind(chr(39))
    return s[a + 1:b]

lines = open(P).read().split(NL)
fixed = 0

il = inner(lines[12])
if il == PREF + 'A' * 257:
    lines[12] = '    ' + chr(39) + PREF + 'A' * 265 + chr(39) + ' +'
    fixed += 1
elif il != PREF + 'A' * 265:
    print('chunk2 unexpected')
    sys.exit(1)

il = inner(lines[13])
if set(il) == {'A'} and len(il) == 312:
    lines[13] = '    ' + chr(39) + 'A' * 320 + chr(39) + ' +'
    fixed += 1
elif not (set(il) == {'A'} and len(il) == 320):
    print('chunk3 unexpected')
    sys.exit(1)

il = inner(lines[21])
if len(il) == 319 and il[84] == 'H':
    lines[21] = '    ' + chr(39) + il[:84] + '9' + il[84:] + chr(39) + ' +'
    fixed += 1
elif not (len(il) == 320 and il[84] == '9'):
    print('chunk11 unexpected')
    sys.exit(1)

open(P, 'w').write(NL.join(lines))

start = None
chunks = []
for i, ln in enumerate(lines):
    if ln.startswith('LOGO_B64 = ('):
        start = i + 1
    elif start is not None and ln.strip() == ')':
        break
    elif start is not None:
        chunks.append(inner(ln.strip()))
data = base64.b64decode(''.join(chunks))
digest = hashlib.md5(data).hexdigest()
print('fixer repairs:', fixed, '| logo md5:', digest)
if digest != MD5:
    print('MD5 MISMATCH - aborting')
    sys.exit(1)
print('b64 fixer OK')
