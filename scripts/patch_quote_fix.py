#!/usr/bin/env python3
"""One-line safety fix in js/extras.js: escape double quotes in the saved
report name as " before it goes into the value="" attribute."""
import io

Q = chr(34)   # double quote
A = chr(39)   # single quote

def main():
    s = io.open('js/extras.js', encoding='utf-8').read()
    old = 'savedName.replace(/' + Q + '/g, ' + A + Q + A + ')'
    new = 'savedName.replace(/' + Q + '/g, ' + A + '&' + 'quot;' + A + ')'
    if old in s:
        assert s.count(old) == 1
        io.open('js/extras.js', 'w', encoding='utf-8').write(s.replace(old, new))
        print('extras.js: quote escape fixed')
    else:
        print('extras.js: already OK')

if __name__ == '__main__':
    main()
