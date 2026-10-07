#!/usr/bin/env python3
"""Inject researched stop lists into Kolkata city-route pages that had none.

Data: /scratch/work/assign.json  ->  {page: {code, stops, kind, src}}
Writes an idempotent block marked `<!-- researched-stops-v1 -->`, fixes the
"Stops 0" stat and the "0 stops / 0 stoppages" copy. Also updates
data/cstc_city_bus_timetable.json for matching CSTC routes so regeneration
keeps the stops.

Run from repo root:  python3 scripts/apply_researched_stops.py --write
"""
import json, re, sys, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BT = ROOT / "bus-time-table"
ASSIGN = Path("/scratch/work/assign.json")
CSTC = ROOT / "data" / "cstc_city_bus_timetable.json"
MARK = "<!-- researched-stops-v1 -->"
WRITE = "--write" in sys.argv

CSS = """<style>
.rstop{background:var(--surface,#fff);border:1px solid var(--line,rgba(0,0,0,.12));border-radius:var(--radius,12px);padding:14px 16px;margin:14px 0}
.rstop h2{font-family:var(--font-display,Georgia,serif);font-size:1.05rem;margin:0 0 4px;display:flex;align-items:center;gap:9px;flex-wrap:wrap}
.rstop h2:before{content:"";width:7px;height:20px;background:var(--amber,#b8791f);border-radius:99px}
.rstop .rnum{font:600 12px ui-monospace,monospace;color:var(--ink-dim,#5b5446)}
.rstop .rsrc{font-size:11.5px;color:var(--ink-dim,#5b5446);margin:0 0 10px}
.rstop ol{list-style:none;counter-reset:rs;margin:0;padding:0}
.rstop li{counter-increment:rs;display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px dashed var(--line,rgba(0,0,0,.12));font-size:14px}
.rstop li:last-child{border-bottom:0}
.rstop li:before{content:counter(rs);flex:none;width:22px;height:22px;border-radius:50%;background:var(--amber,#b8791f);color:#fff9ee;font:700 11px ui-monospace,monospace;display:grid;place-items:center}
.rstop .rvia{font:600 11px ui-monospace,monospace;color:var(--ink-dim,#5b5446);margin-left:auto}
</style>"""


def esc(s):
    return html.escape(str(s), quote=True)


def block(code, stops, kind, src):
    tag = "corridor" if kind == "via" else "stop list"
    label = "Corridor (roads on the route)" if kind == "via" else f"Route stops"
    items = "".join(f"<li>{esc(s)}</li>" for s in stops)
    return (f"\n{MARK}\n{CSS}\n"
            f'<section class="rstop"><h2>{label} '
            f'<span class="rnum">({len(stops)})</span></h2>'
            f'<p class="rsrc">Source: {esc(src)} · not estimated</p>'
            f'<ol>{items}</ol></section>\n')


def strip_block(h):
    """Remove a previously-injected block so it can be re-placed (idempotent move)."""
    if MARK not in h:
        return h
    i = h.index(MARK)
    j = h.index("</section>", i) + len("</section>")
    return h[:i] + h[j:]


def insert_after_hero(h, blk):
    m = re.search(r'<section class="(?:cstc-)?hero"[^>]*>.*?</section>', h, re.S)
    if m:
        return h[:m.end()] + blk + h[m.end():]
    anchor = '<h3 class="section-title"><span class="label-en">Other Direction</span>'
    if anchor in h:
        return h.replace(anchor, blk + anchor, 1)
    if "</main>" in h:
        return h.replace("</main>", blk + "</main>", 1)
    return h


def patch_page(path, code, stops, kind, src):
    h = path.read_text(encoding="utf-8")
    was = MARK in h
    h = strip_block(h)          # drop old placement, if any
    n = len(stops)
    # 1) fix the "Stops <strong>0</strong>" stat
    h2 = re.sub(r'(Stops</span>\s*<span[^>]*>[^<]*</span>\s*<strong>)0(</strong>)',
                rf"\g<1>{n}\g<2>", h)
    h2 = h2.replace('<strong>0</strong>', f"<strong>{n}</strong>") if h2 == h else h2
    # 2) fix copy that says 0 stops / 0 stoppages
    h2 = re.sub(r'\b0 route stops\b', f'{n} route stops', h2)
    h2 = re.sub(r'\b0 stoppages\b', f'{n} stoppages', h2)
    h2 = re.sub(r'<b>0</b> stops', f'<b>{n}</b> stops', h2)
    h2 = re.sub(r'\bvia 0 stops\b', f'via {n} stops', h2)
    # 3) insert the block right after the hero section (top of content)
    blk = block(code, stops, kind, src)
    h3 = insert_after_hero(h2, blk)
    if h3 == h2 and not re.search(r'class="(?:cstc-)?hero"', h2):
        return False, "no anchor"
    if h3 == h:
        return False, "already" if was else "no change"
    if WRITE:
        path.write_text(h3, encoding="utf-8")
    return True, "patched"


def update_cstc_json(assign):
    if not CSTC.exists():
        return 0
    data = json.loads(CSTC.read_text(encoding="utf-8"))
    bynorm = {re.sub(r"[^A-Za-z0-9]", "", k).upper(): k for k in data}
    n = 0
    for p, a in assign.items():
        code = a["code"]
        key = bynorm.get(re.sub(r"[^A-Za-z0-9]", "", code).upper())
        if not key:
            continue
        obj = data[key]
        for d in obj.get("directions", []):
            if not d.get("stoppages"):
                d["stoppages"] = a["stops"]
                n += 1
    if WRITE and n:
        CSTC.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return n


def main():
    assign = json.loads(ASSIGN.read_text())
    ok = skip = fail = 0
    for page, a in sorted(assign.items()):
        path = BT / f"{page}.html"
        if not path.exists():
            fail += 1; print("  MISSING", page); continue
        changed, why = patch_page(path, a["code"], a["stops"], a["kind"], a["src"])
        if changed: ok += 1
        elif why == "already": skip += 1
        else: fail += 1; print("  SKIP", page, why)
    cj = update_cstc_json(assign)
    print(f"patched={ok} already={skip} failed={fail} | cstc-json directions filled={cj} | WRITE={WRITE}")


if __name__ == "__main__":
    main()
