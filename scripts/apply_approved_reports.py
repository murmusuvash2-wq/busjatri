#!/usr/bin/env python3
"""Apply approved user time reports (legacy CSV pipeline).

Reads data/time-reports.json (list of reports). Reports with
status='approved' and a usable time are merged into
data/time-overrides.json, contributor counts are bumped in
data/contributors.json, and processed reports are marked 'done'.

The live site now uses the Apps Script v4 receiver + admin panel
Approve button, which writes time-overrides.json directly - this
script only remains for the legacy Fetch user reports workflow.
"""
import json

OVR = "data/time-overrides.json"
REP = "data/time-reports.json"
CON = "data/contributors.json"


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def main():
    reports = load(REP, [])
    if not reports:
        print("no reports file / empty - nothing to do")
        return
    ovr = load(OVR, {})
    contributors = load(CON, [])
    applied = 0
    for r in reports:
        if r.get("status") != "approved":
            continue
        bus_id = r.get("bus_id")
        stop = r.get("stop")
        time = r.get("time")
        if not (bus_id and stop and time):
            continue
        ovr.setdefault(bus_id, {})
        cur = ovr[bus_id].setdefault(stop, {})
        cur["up" if r.get("dir") != "down" else "down"] = time
        r["status"] = "done"
        applied += 1
        name = r.get("name")
        if name:
            for c in contributors:
                if (c.get("name") or "").lower() == name.lower():
                    c["count"] = c.get("count", 1) + 1
                    break
            else:
                contributors.append({"name": name, "count": 1})
    if applied:
        contributors.sort(key=lambda c: c.get("count", 0), reverse=True)
        with open(OVR, "w", encoding="utf-8") as f:
            json.dump(ovr, f, ensure_ascii=False, indent=2)
            f.write("\n")
        with open(CON, "w", encoding="utf-8") as f:
            json.dump(contributors[:20], f, ensure_ascii=False, indent=2)
            f.write("\n")
        with open(REP, "w", encoding="utf-8") as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
            f.write("\n")
    print("applied:", applied)


if __name__ == "__main__":
    main()
