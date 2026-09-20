#!/usr/bin/env python3
"""Rename footer link text 'Add a Bus' -> 'Bus Contribution' in index.html."""
import io

def main():
    h = io.open('index.html', encoding='utf-8').read()
    a = '>Add a Bus</a>'
    b = '>Bus Contribution</a>'
    if b in h:
        print('index.html: already renamed')
        return
    n = h.count(a)
    assert n == 1, 'add-a-bus anchor: %d' % n
    h = h.replace(a, b)
    io.open('index.html', 'w', encoding='utf-8').write(h)
    print('index.html: footer link renamed to Bus Contribution')

if __name__ == '__main__':
    main()
