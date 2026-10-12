# BusJatri — Architecture (modular, one writer per folder)

**Rule:** one concern = one folder = one writer. Nothing shares a file, so nothing conflicts.
**Interface freeze:** `data/busjatri_data.json` keeps its **exact current schema** forever. It
becomes a *generated* file (merged from `data/buses/*.json`); 61 scripts read it, so its shape
must never change.

## Layout

```
data/            one writer each
  buses/         sbstc.json nbstc.json wbtc.json cstc.json private.json community.json
  places/        places.json  districts.geojson
  fares/         sbstc.json
  times/         sbstc.json
  reports/       time-reports.json
  removals/      bus_removals.json
  sources/       raw PDFs / CSVs from official sites
  meta.json      counts, sources, last_updated   (generated)
content/         about-route/  place-notes/  stand-guides/  blog/
design/          tokens.css  layout.css  components.css  templates/
app/             search/  i18n/  theme/  pwa/  components/
scripts/         add/ dedup/ enrich/ geo/ generate/ content/ seo/ reports/ validate/
```

## Flow

```
 SOURCES (one writer each)      BUILD (read-only)          OUTPUT
 data/buses/*.json        \u2502
 data/places/*.json       \u251c\u2500\u2192 scripts/generate/* \u2500\u2192 bus-time-table/*.html
 content/*                \u2502                          via/*.html  blog/*.html
 design/*                 \u2502                          sitemap.xml  robots.txt
 app/*                    \u2518                          build/app-index.json
                                                         \u2191
 data/buses/*.json \u2500\u2500[merge]\u2500\u2500\u2192 busjatri_data.json \u2500\u2500\u2518  (SAME schema \u2192 61 scripts OK)
```

## Rules for every migration step

1. Never change an existing file's schema in the same step as splitting it.
2. After every step: **build + smoke-test the site** before the next step.
3. One folder per step. Never big-bang.
4. Keep the old path working until the new one is verified.

## Migration order

| Step | Work | Risk |
|---|---|---|
| 1 | Create folder skeleton + this doc | none |
| 2 | `design/` \u2014 split 8 CSS into tokens/layout/components | low (visual check) |
| 3 | `app/` \u2014 group the 14 JS files | low |
| 4 | `data/places/` + wb-geo workflow | none (new) |
| 5 | `content/` + content workflow | none (new) |
| 6 | `data/buses/` split + merge \u2192 busjatri_data.json (schema unchanged) | medium |
| 7 | Fold `patch_*.py` into generators, then delete | medium |
| 8 | Workflows ~173 \u2192 ~10 | low |

Each step ends with: build \u2192 test \u2192 commit.
