#!/usr/bin/env python3
"""Fill missing departure times on the two WBTC E-70 entries (Habra Depot
<-> Jhargram) from redBus (Sep 2026).

Sources (redBus, accessed 27 Sep 2026):
- Live search Habra->Jhargram 29-Sep-2026: card "WBTC (CTC) Habra - Barasat -
  Midnapur - Jhargram - 181" departs 04:20, arrives 09:25 (5h 5m), Non AC
  Seater (2+3), fare Rs 172.
- Live search Jhargram->Kolkata 02-Oct-2026: card "WBTC (CTC) ... Jhargram -
  181" departs 14:40, arrives 18:45 (4h 5m) at Kolkata, fare Rs 145.
- Live search Kolkata->Jhargram 02-Oct-2026: the same 181 shown boarding in
  Kolkata at 05:40 -> 09:25 - one physical service, 04:20 from Habra Depot
  and a Kolkata pickup later.

Mapping note (disclosed): our source kolkata-travel-router calls this route
E-70; redBus calls it 181. Corridor and timings match exactly, so E-70 =
route 181 is the working identification (site owner approved).

Decisions (disclosed):
- Forward entry gets departure 4:20 AM and arrival 9:25 AM (both directly
  from the live card).
- Return entry gets departure 2:40 PM only. The redBus arrival 18:45 is at
  KOLKATA, not at the Habra Depot terminus, so arrival stays empty.
- Through-service cards on other route pages will show the bus's start time
  (existing site behaviour - same as every other through service, e.g.
  Bandwan->Kolkata on the Jhargram->Kolkata page).

No new buses are added: total stays 4420. No SBSTC page, homepage count or
sitemap changes. Idempotent. ASCII-only source.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "busjatri_data.json"

TIME_SOURCE = "redbus.in (WBTC CTC route 181, Sep 2026)"

UPDATES = {
    "ktr-government-e-70": {
        "departure_time": "4:20 AM",
        "arrival_time": "9:25 AM",
        "fare": "Rs. 172",
    },
    "ktr-government-e-70-1": {
        "departure_time": "2:40 PM",
        "arrival_time": "",
        "fare": "Rs. 145",
    },
}


def main():
    write = "--write" in sys.argv
    data = json.loads(DATA.read_text(encoding="utf-8"))
    buses = data["buses"]
    by_id = {b["id"]: b for b in buses}

    for bid, fields in UPDATES.items():
        b = by_id[bid]
        assert b["operator"] == "WBTC", b["operator"]
        for k, v in fields.items():
            if b.get(k) == "" or b.get(k) is None:
                b[k] = v
                print(("WRITE: " if write else "DRY: ") + bid + " " + k + " -> " + repr(v))
            else:
                assert b[k] == v, (bid, k, b[k], v)

    for bid in UPDATES:
        b = by_id[bid]
        if "time_source" not in b or b.get("time_source") != TIME_SOURCE:
            b["time_source"] = TIME_SOURCE

    assert len(buses) == 4420, len(buses)
    assert data["meta"]["total_buses"] == 4420

    if write:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print("total buses:", len(buses))


if __name__ == "__main__":
    main()
