#!/usr/bin/env python3
"""Fail if any bus-time-table page prints the freshness note more than once.

Used by the "Kolkata sections + audit fixes 20261002" workflow to guard the
duplicate-note fix (the reverse-route pages used to print the note twice).
"""
import glob
import sys

bad = [p for p in glob.glob('bus-time-table/*.html')
       if open(p, encoding='utf-8', errors='ignore').read().count('Schedule data refreshed') > 1]
if bad:
    print('duplicate freshness note on:', bad[:5], f'({len(bad)} pages)')
    sys.exit(1)
print('freshness note: single on every page')
