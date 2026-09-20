#!/usr/bin/env python3
"""Wire the deployed Apps Script receiver URL into js/extras.js and bump
the extras.js cache-bust version in index.html. Idempotent."""

ENDPOINT = 'https://script.google.com/macros/s/AKfycbyf-rjtn606T1FUfGaPiYnyIMCZIU99ZlwqmkI3cVfPT0SarjTY12MZQpu2exLczdUD/exec'

def main():
    s = open('js/extras.js', encoding='utf-8').read()
    old = 'var REPORT_FORM = { action: "" };   // <-- Apps Script web-app URL goes here'
    if 'AKfycbyf' not in s:
        assert s.count(old) == 1, 'endpoint anchor not found'
        s = s.replace(old, 'var REPORT_FORM = { action: "' + ENDPOINT + '" };')
        open('js/extras.js', 'w', encoding='utf-8').write(s)
        print('extras.js: endpoint wired')
    else:
        print('extras.js: already wired')

    h = open('index.html', encoding='utf-8').read()
    if 'js/extras.js?v=rpt20260920b' not in h:
        old_v = 'js/extras.js?v=rpt20260920a'
        assert h.count(old_v) == 1, 'version anchor not found'
        h = h.replace(old_v, 'js/extras.js?v=rpt20260920b')
        open('index.html', 'w', encoding='utf-8').write(h)
        print('index.html: cache-bust bumped')
    else:
        print('index.html: already bumped')

if __name__ == '__main__':
    main()
