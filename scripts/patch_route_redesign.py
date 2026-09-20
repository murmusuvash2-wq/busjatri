#!/usr/bin/env python3
"""Route page redesign (2026-09-20):
- bus cards: shadow + border + hover lift, clock icon, big amber departure
- fare shown only when present (green), duration/stops with icons
- Details link on every card -> SPA bus page
- seo-hero: soft gradient card
- routemap: gradient line + glowing dots
- CSS cache-bust ?v=rt20260920"""
import io

def rep(s, old, new, label):
    n = s.count(old)
    assert n == 1, '%s: found %d' % (label, n)
    return s.replace(old, new)

BUS_CARD_OLD = '''def bus_card(bus):
    name = clean_text(bus.get("bus_name")) or "Bus service"
    dep = format_time(parse_time(bus.get("departure_time")))
    arr = format_time(parse_time(bus.get("arrival_time")))
    operator = operator_name(bus)
    stops = total_stops(bus)
    duration = calculate_duration(bus)
    dur_text = fmt_duration(duration) if duration else "—"
    fare = clean_text(bus.get("fare")) or "—"
    bt_raw = (bus.get("bus_type") or "").lower()
    if "gov" in bt_raw or "sbstc" in bt_raw or "nbstc" in bt_raw or "wbtc" in bt_raw:
        badge = '<span class="badge badge-govt">Govt</span>'
    elif "ac" in bt_raw and "non" not in bt_raw:
        badge = '<span class="badge badge-ac">AC</span>'
    else:
        badge = '<span class="badge badge-priv">Private</span>'
    op_line = esc(name)
    if operator:
        op_line += f' · {esc(operator)}'
    if dep == "—":
        dep_html = '<span class="no-time">Time N/A</span>'
    else:
        dep_html = f"{esc(dep)}<small>{esc(arr)} arr</small>"
    return f"""<div class="bus-row">
  <div class="dep">{dep_html}</div>
  <div class="bmid">
    <div class="op">{op_line}</div>
    <div class="mrow"><span>{esc(fare)}</span><span>~{esc(dur_text)}</span><span>{stops or 0} stops</span></div>
  </div>
  {badge}
</div>"""'''

BUS_CARD_NEW = '''def bus_card(bus):
    name = clean_text(bus.get("bus_name")) or "Bus service"
    dep = format_time(parse_time(bus.get("departure_time")))
    arr = format_time(parse_time(bus.get("arrival_time")))
    operator = operator_name(bus)
    stops = total_stops(bus)
    duration = calculate_duration(bus)
    dur_text = fmt_duration(duration) if duration else "—"
    fare = clean_text(bus.get("fare")) or "—"
    bid = bus.get("id") or ""
    bt_raw = (bus.get("bus_type") or "").lower()
    if "gov" in bt_raw or "sbstc" in bt_raw or "nbstc" in bt_raw or "wbtc" in bt_raw:
        badge = '<span class="badge badge-govt">Govt</span>'
    elif "ac" in bt_raw and "non" not in bt_raw:
        badge = '<span class="badge badge-ac">AC</span>'
    else:
        badge = '<span class="badge badge-priv">Private</span>'
    op_line = esc(name)
    if operator:
        op_line += f' · {esc(operator)}'
    clock = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'
    if dep == "—":
        dep_html = f"{clock}<span class=\\"no-time\\">Time N/A</span>"
    else:
        small = f"<small>{esc(arr)} arr</small>" if arr != "—" else ""
        dep_html = f"{clock}<div class=\\"depcol\\"><span class=\\"dep-t\\">{esc(dep)}</span>{small}</div>"
    meta_bits = []
    if fare != "—":
        meta_bits.append(f'<span class="fare">{esc(fare)}</span>')
    meta_bits.append(f"⏱ ~{esc(dur_text)}")
    meta_bits.append(f"🚏 {stops or 0} stops")
    link = ""
    if bid:
        link = f'<a class="bd-link" href="../index.html#/bus/{esc(bid)}" aria-label="View full timetable for {esc(name)}">Details ›</a>'
    return f"""<div class="bus-row">
  <div class="dep">{dep_html}</div>
  <div class="bmid">
    <div class="op">{op_line}</div>
    <div class="mrow">{' · '.join(meta_bits)}</div>
  </div>
  <div class="bright">{badge}{link}</div>
</div>"""'''

CSS_LINK_OLD = '<link rel="stylesheet" href="../css/seo.css">'
CSS_LINK_NEW = '<link rel="stylesheet" href="../css/seo.css?v=rt20260920">'

CSS_ADD = '''
/* ===== route page redesign (2026-09-20) ===== */
.seo-hero{padding:16px 18px;background:linear-gradient(135deg,color-mix(in srgb,var(--amber) 12%,var(--surface)),var(--surface) 60%);border:1px solid color-mix(in srgb,var(--amber) 30%,transparent);border-radius:18px;margin:4px 0 18px}
.seo-hero h1{font-size:clamp(1.55rem,5.5vw,2.05rem)}
.schip{box-shadow:0 1px 2px rgba(28,25,23,.05)}
.bus-row{gap:14px;border:1px solid var(--border-strong);border-radius:16px;padding:14px 16px;margin-bottom:12px;box-shadow:0 1px 3px rgba(28,25,23,.06);transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease}
.bus-row:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(28,25,23,.10);border-color:color-mix(in srgb,var(--amber) 45%,transparent)}
.bus-row .dep{display:flex;gap:7px;align-items:flex-start;font-size:17px;min-width:90px;color:var(--amber-ink);flex-shrink:0}
.bus-row .dep>svg{width:15px;height:15px;color:var(--amber);margin-top:3px;flex-shrink:0}
.bus-row .depcol{display:flex;flex-direction:column;line-height:1.15}
.bus-row .dep small{display:block;font-size:10.5px;color:var(--ink-dim);font-weight:500;margin-top:1px}
.bus-row .op{font-size:14px}
.bus-row .mrow{display:flex;flex-wrap:wrap;gap:8px;font-size:11.5px;margin-top:4px;align-items:center}
.bus-row .mrow .fare{color:var(--green);font-weight:700}
.bus-row .bright{display:flex;flex-direction:column;align-items:flex-end;gap:7px;flex-shrink:0}
.bd-link{font-size:11px;font-weight:700;letter-spacing:.02em;color:var(--amber-ink);background:var(--amber-soft);border:1px solid color-mix(in srgb,var(--amber) 35%,transparent);padding:4px 10px;border-radius:8px;text-decoration:none;white-space:nowrap}
.bd-link:hover{background:color-mix(in srgb,var(--amber) 18%,var(--surface))}
.routemap{box-shadow:0 1px 3px rgba(28,25,23,.05)}
.rm-line{border:none;background:linear-gradient(90deg,var(--amber),var(--maroon));height:3.5px;border-radius:999px}
.rm-dot{width:13px;height:13px;border:3px solid var(--amber);box-shadow:0 0 0 4px color-mix(in srgb,var(--amber) 14%,transparent)}
.rm-stop.end .rm-dot{border-color:var(--maroon);box-shadow:0 0 0 4px color-mix(in srgb,var(--maroon) 14%,transparent)}
@media(max-width:640px){
 .bus-row{padding:12px 13px;gap:10px}
 .bus-row .dep{min-width:74px;font-size:15.5px}
 .bus-row .bright{gap:5px}
 .bd-link{padding:3px 8px;font-size:10.5px}
}
/* ===== end route page redesign ===== */
'''

def main():
    g = io.open('scripts/gen_seo_pages.py', encoding='utf-8').read()
    if 'bd-link' in g:
        print('gen_seo_pages.py: already patched')
    else:
        g = rep(g, BUS_CARD_OLD, BUS_CARD_NEW, 'bus_card')
        g = rep(g, CSS_LINK_OLD, CSS_LINK_NEW, 'css link')
        io.open('scripts/gen_seo_pages.py', 'w', encoding='utf-8').write(g)
        print('gen_seo_pages.py: bus_card + css cache-bust done')

    c = io.open('css/seo.css', encoding='utf-8').read()
    if 'route page redesign (2026-09-20)' in c:
        print('seo.css: already patched')
    else:
        if not c.endswith('\n'):
            c += '\n'
        c += CSS_ADD
        io.open('css/seo.css', 'w', encoding='utf-8').write(c)
        print('seo.css: redesign styles appended')

if __name__ == '__main__':
    main()
