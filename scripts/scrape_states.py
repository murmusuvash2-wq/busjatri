#!/usr/bin/env python3
"""Daily raw bus-data scraper for future state expansion (JH / BR / OD).

Collects bus timetable data from public official sources into
data-raw/states/<state>/ as RAW snapshots. Nothing here touches the live
BusJatri site, the FB pipeline, sitemaps or pages - this is pure data
accumulation for a future /jh /br /od expansion, to be filtered later.

Sources (v1):
  Bihar    - BSRTC depot timetable PDFs (redBus-hosted CMS for BSRTC)
             https://s3.rdbuz.com/Images/WL/CMS/BSRTC/<Depot>_Details.pdf
             Depot list discovered from https://bsrtc.co.in/schedules plus a
             seeded list of known depots. PDFs vary in column layout, so the
             parser stores BOTH parsed rows and the raw page text (so the
             data can always be re-parsed later without re-downloading).
  Jharkhand- Janta Bus Service schedules page (Ranchi private operator)
             https://www.jantabus.in/schedules.html
  Odisha   - registered but not yet scraped: booking.osrtc.org is a
             search-only SPA with no bulk timetable endpoint found yet.

Output per source:
  data-raw/states/<state>/<source>.json   - latest snapshot
  data-raw/log.json                       - append-only run log

Usage:
  python3 scripts/scrape_states.py          # scrape + write data-raw/
"""
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data-raw" / "states"
LOG = ROOT / "data-raw" / "log.json"
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")

BSRTC_BASE = "https://s3.rdbuz.com/Images/WL/CMS/BSRTC/"
BSRTC_INDEX = "https://bsrtc.co.in/schedules"
BSRTC_DEPOTS = [
    "Bankipur(Patna)", "Gaya", "Bhagalpur", "Muzaffarpur", "Darbhanga",
    "Purnea", "Purnia", "Rajgir", "Biharsharif", "Bihar Sharif", "Nawada",
    "Chapra", "Motihari", "Sitamarhi", "Ara", "Buxar", "Katihar",
    "Mithapur", "Gopalganj", "Siwan", "Jehanabad", "Munger", "Begusarai",
    "Khagaria", "Saharsa", "Madhepura", "Supaul", "Araria", "Kishanganj",
    "Sasaram", "Dehri", "Bhabhua", "Aurangabad", "Hajipur", "Samastipur",
    "Lakhisarai", "Jamui", "Sheikhpura", "Arwal", "Bettiah", "Raxaul",
    "Forbesganj", "Madhubani", "Jhanjharpur",
]
JANTABUS_URL = "https://www.jantabus.in/schedules.html"

TIME_RE = re.compile(r"^\d{1,2}:\d{2}\s*(?:AM|PM)$", re.I)
TIME_EMBED_RE = re.compile(r"(\d{1,2}:\d{2}\s*(?:AM|PM))", re.I)


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "BusJatriDataBot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# --------------------------------------------------------------- Bihar
def discover_bsrtc_pdfs():
    urls = set(BSRTC_BASE + d.replace(" ", "%20") + "_Details.pdf" for d in BSRTC_DEPOTS)
    try:
        html = fetch(BSRTC_INDEX).decode("utf-8", "replace")
        for m in re.finditer(r"https?://[^\s\"'<>]+?\.pdf", html):
            u = m.group(0).replace("&", "&")
            if "BSRTC" in u or "_Details" in u:
                urls.add(u)
    except Exception as e:
        print(f"  discovery fetch failed ({e}); using seed list")
    return sorted(urls)


def parse_bsrtc_pdf(data):
    """Parse a BSRTC depot PDF. Returns (rows, raw_pages)."""
    import io
    import pdfplumber

    rows, raw_pages = [], []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            raw_pages.append(text)
            for line in text.split("\n"):
                row = parse_bsrtc_line(line)
                if row:
                    rows.append(row)
    return rows, raw_pages


def parse_bsrtc_line(line):
    """Parse one timetable line. Time may be '9:15 AM' (2 tokens) or glued.

    Raw text is stored alongside anyway, so this parse just needs to be
    good-enough: from = first token(s), to = following purely-alpha tokens,
    numbers in between/after become service_id / seats, slash-tokens become
    bus_type.
    """
    if not re.search(r"\d{1,2}:\d{2}\s*(AM|PM)", line, re.I):
        return None
    toks = line.split()
    time_idx = ampm = None
    for i, t in enumerate(toks):
        if re.fullmatch(r"\d{1,2}:\d{2}", t) and i + 1 < len(toks) \
                and toks[i + 1].upper() in ("AM", "PM"):
            time_idx, ampm = i, i + 1
            break
        if re.fullmatch(r"\d{1,2}:\d{2}(AM|PM)", t, re.I):
            time_idx, ampm = i, i
            break
    if time_idx is None or time_idx < 2:
        return None
    dep = toks[time_idx] + (" " + toks[ampm] if ampm != time_idx else "")
    head = toks[:time_idx]
    tail = toks[ampm + 1:]
    if re.match(r"^\d{1,3}[.)]?$", head[0]):   # leading serial number
        head = head[1:]
    if not head:
        return None
    # from = first token; to = following purely-alpha tokens (multi-word stops)
    frm = head[0]
    to_toks = []
    i = 1
    while i < len(head) and re.fullmatch(r"[A-Za-z()]+", head[i]):
        to_toks.append(head[i])
        i += 1
    if not to_toks:
        return None
    extra = " ".join(head[i:]) + " " + " ".join(tail)
    row = {"from": frm, "to": " ".join(to_toks), "departure": dep}
    for t in extra.split():
        if re.fullmatch(r"\d{5,7}", t):
            row["service_id"] = t
        elif re.fullmatch(r"\d{2}", t) and 30 <= int(t) <= 65:
            row.setdefault("seats", int(t))
    bt = " ".join(x for x in extra.split() if "/" in x or "AC" in x.upper())
    if bt:
        row["bus_type"] = bt
    leftovers = " ".join(x for x in extra.split()
                         if x != row.get("service_id") and not (x.isdigit())
                         and x not in bt.split())
    if leftovers.strip():
        row["raw_extra"] = " ".join(leftovers.split())
    return row


def scrape_bsrtc():
    pdfs = discover_bsrtc_pdfs()
    all_rows, depots, raw_all = [], {}, {}
    for url in pdfs:
        name = url.rsplit("/", 1)[-1].replace("_Details.pdf", "")
        try:
            data = fetch(url)
        except Exception:
            continue  # 404 or transient - normal for guessed depot names
        try:
            rows, raw_pages = parse_bsrtc_pdf(data)
        except Exception as e:
            print(f"  parse fail {name}: {e}")
            continue
        if not rows:
            continue
        depots[name] = {"url": url, "rows": len(rows)}
        all_rows.extend({"depot": name, **r} for r in rows)
        raw_all[name] = raw_pages
        print(f"  BSRTC {name}: {len(rows)} services")
    snapshot = {
        "state": "bihar",
        "operator": "BSRTC",
        "fetched_at": NOW,
        "depots": depots,
        "rows": all_rows,
        "raw_pages": raw_all,
    }
    return snapshot


# ----------------------------------------------------------- Jharkhand
class _Table(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.cur, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.cur = []
        elif tag in ("td", "th") and self.cur is not None:
            self.cell = []

    def handle_data(self, d):
        if self.cell is not None:
            self.cell.append(d)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.cur.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.cur is not None:
            if any(self.cur):
                self.rows.append(self.cur)
            self.cur = None


def scrape_jantabus():
    html = fetch(JANTABUS_URL).decode("utf-8", "replace")
    p = _Table()
    p.feed(html)
    rows = []
    for r in p.rows:
        if len(r) >= 5 and (" to " in " ".join(r).lower() or "hrs" in " ".join(r).lower()):
            rows.append({
                "service": r[0],
                "route": r[1] if len(r) > 1 else "",
                "coach": r[2] if len(r) > 2 else "",
                "fare": r[3] if len(r) > 3 else "",
                "departure": r[4] if len(r) > 4 else "",
                "journey": r[5] if len(r) > 5 else "",
            })
    # de-dup header rows
    rows = [r for r in rows if r.get("departure") and ":" in r["departure"]]
    print(f"  JantaBus (Jharkhand): {len(rows)} services")
    return {
        "state": "jharkhand",
        "operator": "Janta Bus Service (private)",
        "fetched_at": NOW,
        "source_url": JANTABUS_URL,
        "rows": rows,
    }


# ---------------------------------------------------------------- main
def save(state, name, snapshot):
    d = OUT / state
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{name}.json"
    prev = None
    if p.exists():
        try:
            prev = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            prev = None
    payload = json.dumps(snapshot, ensure_ascii=False, indent=1)
    sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    changed = not prev or prev.get("sha256") != sha
    snapshot["sha256"] = sha
    if changed:
        p.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
    log = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    log.append({
        "ts": NOW, "source": f"{state}/{name}",
        "rows": len(snapshot.get("rows", [])),
        "sha256": sha, "changed": changed,
    })
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{state}/{name}: {len(snapshot.get('rows', []))} rows, changed={changed}")


def main():
    try:
        save("bihar", "bsrtc", scrape_bsrtc())
    except Exception as e:
        print(f"BSRTC scrape failed: {e}")
    try:
        save("jharkhand", "jantabus", scrape_jantabus())
    except Exception as e:
        print(f"JantaBus scrape failed: {e}")
    print("done.")


if __name__ == "__main__":
    main()
