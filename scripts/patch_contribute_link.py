#!/usr/bin/env python3
"""Add 'Add a Bus' link to the index.html footer (points to contribute.html)."""
import io

def main():
    h = io.open('index.html', encoding='utf-8').read()
    if 'contribute.html' in h:
        print('index.html: already linked')
        return
    a = '<a href="about.html#credits">Credits</a>'
    n = h.count(a)
    assert n == 1, 'credits anchor: %d' % n
    h = h.replace(a, a + '\n        <a href="contribute.html">Add a Bus</a>')
    io.open('index.html', 'w', encoding='utf-8').write(h)
    print('index.html: Add a Bus link added')

if __name__ == '__main__':
    main()
