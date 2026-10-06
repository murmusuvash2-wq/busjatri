# BusJatri Work Log

Permanent memory of all work done on this site. Read this before starting any new task.
Newest entries first.

---

## 2026-10-06 — Kolkata city bus: route page (time+stoppage+route) + hub search-only
- What:
  1. **Route pages** — new generator `scripts/build_city_route_pages.py` emits the approved city-route design (hero with route code + stats, **TIME** departures table, **ROUTE** horizontal line, **STOPPAGE** list, bilingual EN/বাংলা) for all intra-Kolkata city routes. ~230 pages. Uses existing `cstc-city.css` + a small inline `<style>` for the route line (`.rm-*`).
  2. **Hub** — `scripts/patch_city_hub.py` removes the long `private-routes-section` (254-row list, 188 KB) and de-duplicates the 6 `cstc-panel` blocks (kept 1). Hub 382 KB → 160 KB (−58%). Keeps hero, search (results on search), Popular Routes, "Which bus goes where?", official chips.
  3. Workflow `.github/workflows/city-design.yml` runs both + validates + auto-commits.
- Why: User approved the two demos; asked to implement the route page and make the hub search-only with only important-route chips (no long list). Also fixes the 6× duplicate CSTC panel bug (438 repeated links) found in the audit.
- Files: `scripts/build_city_route_pages.py`, `scripts/patch_city_hub.py`, `.github/workflows/city-design.yml`, `bus-time-table/*` (city pages), `kolkata-city-bus-timetable.html`
- Commits: 8efc53e4 (generator), 23cab3c2 (hub patch), 149543e9 (workflow), 1f8c2fc4 (workflow auto-commit of pages + hub). Run 37411416052: SUCCESS.
- Status: done — hub verified (no private-routes-section, 1 cstc-panel, search intact). City pages verified (cstc-hero + rm-stops + cstc-stops on dunlop-to-ballygunge).
- Notes:
  - The city route pages + hub were previously HAND-AUTHORED (no generator) — this generator now makes them reproducible. **Caution:** `gen_seo_pages.py` (run by 5 regen workflows: regen-seo-pages, regenerate-seo-pages, deploy-data-v3, auto-update, expand-seo-generator) overwrites `bus-time-table/*.html` with the generic design. To keep the city design, add `python3 scripts/build_city_route_pages.py` as a step AFTER `gen_seo_pages.py` in those workflows (not yet done).
  - `build_cstc_city_seo.py` `update_hub()` is non-idempotent (replaces only the first MARK) — source of the 6 duplicates. Not run by any workflow.

## Next steps / backlog
- [ ] Add `python3 scripts/build_city_route_pages.py` after `gen_seo_pages.py` in the 5 regen workflows (so city design survives regen)
- [ ] Fix `build_cstc_city_seo.py` `update_hub()` idempotency (replace whole MARK..</section> region)
- [ ] Kolkata city bus TIME gap: 231/231 city buses have no departure_time (source kolkata-travel-router). Add frequency model ("every ~12 min") + expand official CSTC/WBTC times + wire community times to the report pipeline
- [ ] Add 17 embedded-newline bus names cleanup (`\n → space`)
- [ ] Add dedicated route_number field for city buses (search by bus number)
- [ ] Verify user time update feature on live site (digha-to-esplanade — Add Time)
- [ ] Submit sitemap in Google Search Console; request indexing for key pages
- [ ] Apply for AdSense after 20-30 quality sessions/day
