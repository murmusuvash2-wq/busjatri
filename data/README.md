# data/

One writer per file. `busjatri_data.json` is the frozen interface (schema never changes);
the per-operator files below are the editable sources that merge into it.

| File | What | Writer |
|---|---|---|
| `buses/sbstc.json` | SBSTC buses | sbstc-data |
| `buses/nbstc.json` | NBSTC buses | nbstc-data |
| `buses/wbtc.json` | WBTC buses | wbtc-data |
| `buses/cstc.json` | Kolkata city / CSTC | cstc-data |
| `buses/private.json` | private operators | private-data |
| `buses/community.json` | FB / user reports (add + enrich) | add-buses |
| `places/places.json` | place \u2192 district, type, lat/lon, station | wb-geo |
| `places/districts.geojson` | WB 23 district boundaries | wb-geo |
| `fares/sbstc.json` | official SBSTC fares | sbstc-data |
| `times/sbstc.json` | official SBSTC up/down times | sbstc-data |
| `reports/time-reports.json` | user "Report Time" submissions | reports |
| `removals/bus_removals.json` | junk / removed stubs | dedup |
| `meta.json` | counts, sources, last_updated | build-site |
