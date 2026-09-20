#!/usr/bin/env python3
"""Switch site to the NEW Apps Script deployment (v4, new project).
URLs to update: extras.js REPORT_FORM.action, contribute.html URL_, admin.html RPT_URL."""
import io

OLD = 'https://script.google.com/macros/s/AKfycbyf-rjtn606T1FUfGaPiYnyIMCZIU99ZlwqmkI3cVfPT0SarjTY12MZQpu2exLczdUD/exec'
NEW = 'https://script.google.com/macros/s/AKfycby3uePQMRoPwXg-7rWRgtF5TIyHe7e1brhGscIC_t_CtzVJiHke8DOf3-Ff5zMk1VZv/exec'

def swap(path, expected):
    s = io.open(path, encoding='utf-8').read()
    if NEW in s:
        print('%s: already switched' % path)
        return
    n = s.count(OLD)
    assert n == expected, '%s: expected %d old URLs, found %d' % (path, expected, n)
    s = s.replace(OLD, NEW)
    assert OLD not in s and s.count(NEW) == expected
    io.open(path, 'w', encoding='utf-8').write(s)
    print('%s: %d URL(s) switched' % (path, expected))

def main():
    swap('js/extras.js', 1)        # REPORT_FORM.action (report + add-time forms)
    swap('contribute.html', 1)      # URL_ (Bus Contribution form)
    swap('admin.html', 1)           # RPT_URL (admin panel)

    h = io.open('index.html', encoding='utf-8').read()
    h2 = h.replace('extras.js?v=rpt20260920c', 'extras.js?v=rpt20260920d')
    if h2 != h:
        io.open('index.html', 'w', encoding='utf-8').write(h2)
        print('index.html: extras.js cache-bust updated')

if __name__ == '__main__':
    main()
