# Time-data audit & format fix — BusJatri

Generated during a review of `https://busjatri.in/kolkata-city-bus-timetable`.

## 1. Fixed in this PR — inconsistent time formats (safe, mechanical)

The dataset is canonically `h:mm AM/PM`, but 780 time values across three data
files used other formats, so the UI rendered some times inconsistently and
search/sort could not parse them:

| issue | example | count |
|---|---|---|
| bare 24-hour clock | `"08:00"`, `"17:00"`, `"00:30"` | 780 (312 in busjatri_data, 312 in bus-details, 156 in app-index) |
| `Noon` literal | `"12:00 Noon"` | 11 |
| lowercase / padded hour | `"04:00 AM"` | 3 |
| trailing qualifier | `"8:20 AM (2nd day)"` | 2 |

All were normalised to `h:mm AM/PM` (e.g. `17:00` → `5:00 PM`, `12:00 Noon` →
`12:00 PM`). No time was changed in meaning — only its representation. The
script used is `scripts/fix-time-formats.py` and is idempotent.

## 2. Found but NOT auto-fixed — needs a human / a source

These are real, but "fixing" them means supplying times that are not in the
data, which we must not invent:

- **Missing times are the dominant problem.** Of 4,435 buses, **2,754 have no
  stop-level times at all**; 2,088 have no `departure_time` and 3,275 no
  `arrival_time`. Of 111,760 stop-time cells, 47,627 `up` and 48,711 `down`
  are empty (~86%).
- **70 buses have `up_time` values that run backwards** along the route, and
  **31 buses have `down_time` values that run forwards** (down is the reverse
  trip, so it should decrease with stop number). These look like real
  transcription errors and should be checked against the source.
- **City timetable (`data/cstc_city_bus_timetable.json`, 73 routes):**
  6 routes (14A, 7A, S-16, S-2B, S-4, S-4B) list *identical* departures and
  arrivals in both directions. We checked the official CSTC schedule images in
  `assets/cstc-schedules/` — the images themselves print the same times for
  both directions, so this is faithful to the source, not a data bug.
  20 direction time-lists are non-monotonic and 7 have an arrival <= its
  departure; several of these also appear in the source images, so they need
  careful human review rather than a blanket fix.

## 3. Suggested next steps

1. Re-check the 70 / 31 direction anomalies against the source pages.
2. For the ~2,750 untimed buses, prioritise WBTC/SBSTC/NBSTC government
   services where an official schedule exists.
3. Add a validation step to CI: reject any time value that is not
   `h:mm AM/PM`, and flag non-monotonic sequences in a report (do not fail).
