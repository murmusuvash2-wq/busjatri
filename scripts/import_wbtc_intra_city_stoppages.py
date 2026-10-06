#!/usr/bin/env python3
"""Import WBTC intra-city via/stoppages from the supplied official PDF.

The timetable JSON remains the authority for departures/arrivals. This importer
only enriches matching routes with the PDF's Origin/Terminating/Stoppage data;
it never creates timing records for routes without timetable data.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data" / "sources" / "wbtc-intra-city-routes.pdf"
DATA = ROOT / "data" / "cstc_city_bus_timetable.json"


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def clean_stop(value: str) -> str:
    value = re.sub(r"\s+", " ", value.replace("\n", " ")).strip(" -–—,.;")
    value = re.sub(r"^via\s*:\s*", "", value, flags=re.I)
    return value.strip()


def split_stops(raw: str) -> list[str]:
    raw = re.sub(r"\s+", " ", (raw or "").replace("\n", " ")).strip()
    # The PDF uses hyphens/dashes and commas between stop names. Keep slash
    # alternatives inside one stop (e.g. College More/SDF) intact.
    parts = re.split(r"\s*[-–—]\s*|\s*,\s*", raw)
    out = []
    for part in parts:
        part = clean_stop(part)
        if part and part.lower() not in {"via", "stoppage"} and len(part) > 1:
            out.append(part)
    return out


def pdf_rows() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with pdfplumber.open(PDF) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables:
                continue
            for table in tables:
                for row in table:
                    if not row or len(row) < 5 or not row[1] or row[1] == "Route\nNo.":
                        continue
                    route = re.sub(r"\s+", " ", row[1].replace("\n", " ")).strip()
                    # Remove PDF annotations such as (IT Spl.) from route code.
                    route = re.sub(r"\s*\([^)]*\)", "", route).strip()
                    stops_raw = row[4] or ""
                    rows[norm(route)] = {
                        "route_pdf": route,
                        "origin_pdf": re.sub(r"\s+", " ", (row[2] or "").replace("\n", " ")).strip(),
                        "terminating_pdf": re.sub(r"\s+", " ", (row[3] or "").replace("\n", " ")).strip(),
                        "stoppages_raw": re.sub(r"\s+", " ", stops_raw.replace("\n", " ")).strip(),
                        "stoppages": split_stops(stops_raw),
                    }
    return rows


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    rows = pdf_rows()
    matched = 0
    for route, obj in data.items():
        row = rows.get(norm(route))
        if not row:
            continue
        matched += 1
        stops = row["stoppages"]
        obj["pdf_stoppages"] = {
            "source": "data/sources/wbtc-intra-city-routes.pdf",
            "origin": row["origin_pdf"],
            "terminating": row["terminating_pdf"],
            "raw": row["stoppages_raw"],
            "stops": stops,
        }
        directions = obj.get("directions") or []
        if directions:
            directions[0]["stoppages"] = stops
            if len(directions) > 1:
                directions[1]["stoppages"] = list(reversed(stops))
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PDF routes: {len(rows)}")
    print(f"timetable routes enriched with stoppages: {matched}/{len(data)}")
    print("unmatched timetable routes:", ", ".join(r for r in data if norm(r) not in rows))


if __name__ == "__main__":
    main()
