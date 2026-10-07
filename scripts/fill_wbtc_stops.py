#!/usr/bin/env python3
"""Fill missing stoppages (2026-10-07).

Sources, in order:
  1. data/sources/wbtc-intra-city-routes.pdf - the official WBTC intra-city
     route table (route no. + originating/terminating point + stoppage chain).
     Matched to buses by normalised origin/terminating pair (either direction).
  2. A sibling bus on the same origin -> destination (its stop sequence is
     reused, reversed when the direction is opposite).

Writes back to data/busjatri_data.json and the per-bus data/bus-details/<id>.json
files. Idempotent: buses that already have stoppages are left untouched.

Usage: python3 scripts/fill_wbtc_stops.py
"""
import json
import os
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "busjatri_data.json"
DETAIL = ROOT / "data" / "bus-details"
PDF = ROOT / "data" / "sources" / "wbtc-intra-city-routes.pdf"
RESEARCHED = ROOT / "data" / "researched-stops.json"


def apply_researched(buses):
    """Apply manually-researched route stoppages (data/researched-stops.json).
    Overrides existing (partial) stoppages for a matching origin->destination,
    in either direction."""
    if not RESEARCHED.exists():
        return 0
    entries = json.loads(RESEARCHED.read_text(encoding="utf-8"))
    n = 0
    for e in entries:
        o, d, stops = e.get("origin"), e.get("destination"), (e.get("stops") or [])
        if not (o and d and stops):
            continue
        for b in buses:
            bo, bd = norm(b.get("origin")), norm(b.get("destination"))
            if bo == norm(o) and bd == norm(d):
                b["stoppages"] = [{"name": s} for s in stops]
                n += 1
            elif bo == norm(d) and bd == norm(o):
                b["stoppages"] = [{"name": s} for s in reversed(stops)]
                n += 1
    return n


def clean(s):
    return re.sub(r"\s+", " ", (s or "").strip()).strip(" .,-")


def norm(s):
    s = clean(s).lower()
    s = re.sub(r"\s*\((.*?)\)", "", s)
    s = re.sub(r"\b(stn|station|bus stand|bus-stand|stand|terminus|depot|more|gate|no)\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def split_stops(chain):
    if not chain:
        return []
    chain = chain.replace("\n", " ")
    out = []
    for p in re.split(r"\s*[-\u2013\u2014]\s*|\s*,\s*", chain):
        p = re.sub(r"\s+", " ", p).strip(" .,-;")
        if len(p) > 1:
            out.append(p)
    return out


def pdf_index():
    """route (origin,terminus) -> stop list, from the WBTC PDF."""
    idx = {}
    if not PDF.exists():
        return idx
    import pdfplumber
    with pdfplumber.open(str(PDF)) as pdf:
        for page in pdf.pages:
            for table in (page.extract_tables() or []):
                for r in table:
                    r = [(c or "").replace("\n", " ").strip() for c in r]
                    if len(r) < 5:
                        continue
                    sl, rno, orig, term, stopp = r[0], r[1], r[2], r[3], r[4]
                    if not rno or rno.lower().startswith("route") or sl.lower().startswith("sl"):
                        continue
                    stops = split_stops(stopp)
                    if orig and term and stops:
                        a, b = norm(orig), norm(term)
                        idx.setdefault((a, b), stops)
                        idx.setdefault((b, a), list(reversed(stops)))
    return idx


def main():
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    is_map = isinstance(raw, dict)
    buses = raw["buses"] if is_map else raw

    idx = pdf_index()
    n_res = apply_researched(buses)
    print(f"filled from researched-stops.json: {n_res}")
    filled_pdf = 0
    for b in buses:
        if b.get("stoppages"):
            continue
        hit = idx.get((norm(b.get("origin")), norm(b.get("destination"))))
        if hit:
            b["stoppages"] = [{"name": s} for s in hit]
            filled_pdf += 1

    # sibling fill
    def key(b):
        return ((b.get("origin") or "").strip().lower(), (b.get("destination") or "").strip().lower())

    seqs = defaultdict(list)
    for b in buses:
        st = [s.get("name") if isinstance(s, dict) else s for s in (b.get("stoppages") or [])]
        st = [x for x in st if x]
        if st:
            seqs[key(b)].append(st)
            seqs[(key(b)[1], key(b)[0])].append(list(reversed(st)))
    filled_sib = 0
    for b in buses:
        if b.get("stoppages"):
            continue
        k = key(b)
        cand = seqs.get(k) or seqs.get((k[1], k[0]))
        if cand:
            b["stoppages"] = [{"name": s} for s in cand[0]]
            filled_sib += 1

    still = sum(1 for b in buses if not b.get("stoppages"))
    print(f"filled from WBTC PDF: {filled_pdf} | from siblings: {filled_sib} | still without: {still}")

    DATA.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    # refresh per-bus detail files for the buses we changed
    DETAIL.mkdir(parents=True, exist_ok=True)
    n = 0
    for b in buses:
        if not b.get("stoppages"):
            continue
        p = DETAIL / (str(b.get("id")) + ".json")
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            if not d.get("stoppages"):
                d["stoppages"] = b["stoppages"]
                d["total_stoppages"] = len(b["stoppages"])
                p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
                n += 1
    print(f"detail files updated: {n}")


if __name__ == "__main__":
    main()
