# data-raw — future state expansion (JH / BR / OD)

Raw, unedited bus timetable snapshots collected daily by
`.github/workflows/scrape-states.yml` → `scripts/scrape_states.py`.

**Nothing here is live.** This folder is excluded from the deployed site
(see `.assetsignore`), is not in any sitemap, and is not part of the FB
pipeline or busjatri_data.json. It exists purely so that when BusJatri
expands to Jharkhand / Bihar / Odisha, months of accumulated source data
is already sitting here to filter, verify and convert.

Layout:
- `states/bihar/bsrtc.json` — BSRTC depot timetable PDFs (official,
  redBus-hosted CMS), parsed rows + raw page text
- `states/jharkhand/jantabus.json` — Janta Bus Service (Ranchi private operator)
- `log.json` — append-only run log (rows, content hash, changed flag per run)

Adding a source = add a `scrape_*()` function in scripts/scrape_states.py
and a `save()` call in main(). Odisha (OSRTC) is a candidate but its booking
portal is a search-only SPA — needs endpoint research before a bulk scrape
is possible.

Data rule stays the same as the WB site: nothing goes live unless it is
verifiable. These are raw dumps for later filtering — treat every field
as unverified until then.
