#!/usr/bin/env python3
"""Mobile UX + performance fixes from the 18 Sept 2026 audit.

CSS (css/seo.css, css/style.css, css/extras.css):
  1. Bus rows: operator name no longer single-line-truncated (2-line clamp).
  2. 9.5px sub-labels -> 10.5px (readability).
  3. Search field labels: bigger + higher contrast (amber-ink).
  4. Language buttons: bigger tap area + font.
  5. Theme icon button: 34 -> 38px.
  6. Suggestion chips: bigger tap area.
  7. Destination cards: wider, name wraps, tag wraps (no more clipped text).

JS (js/app.js):
  8. Load app-index-lite.json first (fast first paint), fetch the full
     stop index in the background and merge sx/ux/dx + sn into BUSES.
  9. loadFullBus(): fetch one small per-bus file (data/bus-details/<id>.json,
     ~1-2 KB) instead of the 5 MB bulk bus-details.json.

Build (scripts/build_client_data.py):
  10. Also emit data/app-index-lite.json (no sx/ux/dx) and per-bus
      detail files under data/bus-details/.

All-or-nothing per file, idempotent (skips already-patched pieces).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--write" not in sys.argv
applied = []


def edit(path, pairs, label):
    src = path.read_text(encoding="utf-8")
    out = src
    for old, new in pairs:
        if new in out and old not in out:
            continue  # already patched
        n = out.count(old)
        if n != 1:
            raise SystemExit(f"ABORT ({label}): anchor found {n}x (expected 1): {old[:60]!r}")
        out = out.replace(old, new, 1)
    if out != src:
        if not DRY:
            path.write_text(out, encoding="utf-8")
        applied.append(label)


# ---------- css/seo.css (route pages) ----------
seo_css = ROOT / "css" / "seo.css"
edit(seo_css, [
    (
        ".bus-row .op{font-weight:600;font-size:13.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
        ".bus-row .op{font-weight:600;font-size:13.5px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}",
    ),
    (
        ".bus-row .dep small{display:block;font-size:9.5px;color:var(--ink-dim);font-weight:500}",
        ".bus-row .dep small{display:block;font-size:10.5px;color:var(--ink-dim);font-weight:500}",
    ),
    (
        ".rm-name{font-size:9.5px;font-weight:600;margin-top:6px;text-align:center;line-height:1.25}",
        ".rm-name{font-size:10.5px;font-weight:600;margin-top:6px;text-align:center;line-height:1.25}",
    ),
], "css/seo.css")

# ---------- css/style.css (homepage SPA) ----------
style_css = ROOT / "css" / "style.css"
edit(style_css, [
    (
        "  display: flex; align-items: center; gap: 5px; font-family: var(--font-mono); font-size: 10.5px; font-weight: 600;\n"
        "  color: var(--ink-dim); margin-bottom: 6px; text-transform: uppercase; letter-spacing: .1em;",
        "  display: flex; align-items: center; gap: 5px; font-family: var(--font-mono); font-size: 11.5px; font-weight: 600;\n"
        "  color: var(--amber-ink); margin-bottom: 6px; text-transform: uppercase; letter-spacing: .1em;",
    ),
    (
        "  padding: 5px 12px; font-size: 12.5px; font-weight: 600; cursor: pointer; color: var(--ink-dim);",
        "  padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; color: var(--ink-dim);",
    ),
    (
        "  width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center;",
        "  width: 38px; height: 38px; display: inline-flex; align-items: center; justify-content: center;",
    ),
    (
        ".sugg-chip {\n  background: var(--surface-2); border: 1px solid var(--line); border-radius: 999px; padding: 7px 14px;\n"
        "  font-size: 12.5px; font-weight: 600; color: var(--ink); cursor: pointer; transition: .15s;\n}",
        ".sugg-chip {\n  background: var(--surface-2); border: 1px solid var(--line); border-radius: 999px; padding: 9px 15px;\n"
        "  font-size: 13px; font-weight: 600; color: var(--ink); cursor: pointer; transition: .15s;\n}",
    ),
], "css/style.css")

# ---------- css/extras.css (destination cards) ----------
extras_css = ROOT / "css" / "extras.css"
edit(extras_css, [
    (
        ".place-card {\n  flex: 0 0 128px;\n  scroll-snap-align: start;\n  padding: 13px 12px;\n}",
        ".place-card {\n  flex: 0 0 142px;\n  scroll-snap-align: start;\n  padding: 13px 13px;\n}",
    ),
], "css/extras.css (card width)")

_APPEND_EXTRAS = """
/* Mobile audit fixes 18 Sept 2026: destination cards must not clip text */
.place-card .name { overflow-wrap: anywhere; }
.place-card .place-tag { white-space: normal; max-width: 100%; }
"""
_ex = extras_css.read_text(encoding="utf-8")
if "destination cards must not clip text" not in _ex:
    if not DRY:
        extras_css.write_text(_ex.rstrip() + "\n" + _APPEND_EXTRAS, encoding="utf-8")
    applied.append("css/extras.css (append wrap rules)")

# ---------- js/app.js ----------
app_js = ROOT / "js" / "app.js"
edit(app_js, [
    (
        "    const res = await fetch('data/app-index.json');\n"
        "    if (!res.ok) throw new Error('HTTP ' + res.status);\n"
        "    DATA = await res.json();",
        "    let res = await fetch('data/app-index-lite.json');\n"
        "    if (!res.ok) res = await fetch('data/app-index.json');\n"
        "    if (!res.ok) throw new Error('HTTP ' + res.status);\n"
        "    DATA = await res.json();",
    ),
    (
        "    window.addEventListener('hashchange', render);\n"
        "    render();\n"
        "  } catch (e) {",
        "    window.addEventListener('hashchange', render);\n"
        "    render();\n"
        "    loadFullIndex();\n"
        "  } catch (e) {",
    ),
    (
        "async function loadFullBus(id) {\n"
        "  await loadFullBusData();\n"
        "  return FULL_BUSES[id];\n"
        "}",
        "async function loadFullIndex() {\n"
        "  /* background: full stop index (sx/ux/dx + sn) for stoppage search */\n"
        "  try {\n"
        "    const res = await fetch('data/app-index.json');\n"
        "    if (!res.ok) return;\n"
        "    const full = await res.json();\n"
        "    if (full.sn && DATA) DATA.sn = full.sn;\n"
        "    (full.buses || []).forEach(fb => {\n"
        "      const b = BUSES[fb.id];\n"
        "      if (b && !b.sx && fb.sx) { b.sx = fb.sx; b.ux = fb.ux; b.dx = fb.dx; }\n"
        "    });\n"
        "    if (location.hash.startsWith('#/search') || location.hash.startsWith('#/stop')) render();\n"
        "  } catch (e) { /* stoppage search needs the full index; quiet fail */ }\n"
        "}\n"
        "async function loadFullBus(id) {\n"
        "  if (FULL_BUSES && FULL_BUSES[id]) return FULL_BUSES[id];\n"
        "  try {\n"
        "    const res = await fetch('data/bus-details/' + encodeURIComponent(id) + '.json');\n"
        "    if (res.ok) {\n"
        "      const b = await res.json();\n"
        "      if (!FULL_BUSES) FULL_BUSES = {};\n"
        "      FULL_BUSES[id] = b;\n"
        "      return b;\n"
        "    }\n"
        "  } catch (e) {}\n"
        "  await loadFullBusData();\n"
        "  return FULL_BUSES[id];\n"
        "}",
    ),
], "js/app.js")

# ---------- scripts/build_client_data.py ----------
bcd = ROOT / "scripts" / "build_client_data.py"
edit(bcd, [
    (
        '(ROOT / "data" / "app-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")\n'
        '(ROOT / "data" / "bus-details.json").write_text(json.dumps({b["id"]: b for b in source["buses"]}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")\n'
        'print("Built app-index.json (compact + stop indexes + times) and bus-details.json")\n'
        'print("Initial index bytes:", (ROOT / "data" / "app-index.json").stat().st_size)\n'
        'print("Lazy detail bytes:", (ROOT / "data" / "bus-details.json").stat().st_size)',
        '(ROOT / "data" / "app-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")\n'
        'lite = dict(index)\n'
        'lite["buses"] = [{k: v for k, v in b.items() if k not in ("sx", "ux", "dx")} for b in search_buses]\n'
        '(ROOT / "data" / "app-index-lite.json").write_text(json.dumps(lite, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")\n'
        '(ROOT / "data" / "bus-details.json").write_text(json.dumps({b["id"]: b for b in source["buses"]}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")\n'
        'import shutil\n'
        'details_dir = ROOT / "data" / "bus-details"\n'
        'if details_dir.exists():\n'
        '    shutil.rmtree(details_dir)\n'
        'details_dir.mkdir(parents=True)\n'
        'for bus in source["buses"]:\n'
        '    (details_dir / (bus["id"] + ".json")).write_text(json.dumps(bus, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")\n'
        'print("Built app-index.json, app-index-lite.json and per-bus details")\n'
        'print("Lite index bytes:", (ROOT / "data" / "app-index-lite.json").stat().st_size)\n'
        'print("Full index bytes:", (ROOT / "data" / "app-index.json").stat().st_size)\n'
        'print("Per-bus detail files:", len(list(details_dir.glob("*.json"))))\n'
        'print("Legacy bulk detail bytes:", (ROOT / "data" / "bus-details.json").stat().st_size)',
    ),
], "scripts/build_client_data.py")

print("applied:", applied if applied else "nothing (all already patched)")
print("dry run" if DRY else "written")
