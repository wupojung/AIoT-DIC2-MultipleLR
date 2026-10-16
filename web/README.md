# Regression Analysis Dashboard MVP

Serve from the repository root:

```sh
python3 -m http.server 8000 --directory web
```

Open http://localhost:8000/ or the [GitHub Pages demo](https://wupojung.github.io/AIoT-DIC2-MultipleLR/).
HTTP is required for fetch; direct `file://` opening is unsupported. No npm build/runtime dependency, CDN, backend or model execution.

Overview, Feature Selection and Evaluation support 50 Startups / Boston Housing switching.
Custom Dataset is explicitly disabled. Dataset JSON loads once; switching redraws all panels synchronously, preventing stale cross-dataset numbers.
All-feature holdout, training CV, nested selection and final training-selected features have separate labels.
50 Startups selected-model holdout is unavailable and shown as not evaluated; the accepted baseline holdout is still displayed.
Charts show fixed method/k mean training-CV scores, not test scans or confidence intervals.

## Static data contract

```sh
python3 python/src/export_dashboard.py
python3 python/src/export_dashboard.py --check
```

The standard-library exporter reads accepted `docs/reports/` JSON only; it never imports ML packages or retrains.
`web/data/{50_startups,boston_housing}.json` contains summaries, curve points, full-training ranks, final selection, metrics and source SHA256 lineage.
The `--check` command regenerates in memory and fails for stale/altered payloads. Raw CSV, prediction caches and full audit files are not published.
Adding new experiments needs an explicit exporter update; there is no arbitrary JSON/CSV upload or inference.

## Lean desktop verification

With the server running, use the existing external development Playwright installation:

```sh
NODE_PATH=/tmp/dic2-browser/node_modules node tests/dashboard_smoke.cjs
DASHBOARD_URL=https://wupojung.github.io/AIoT-DIC2-MultipleLR/ NODE_PATH=/tmp/dic2-browser/node_modules node tests/dashboard_smoke.cjs
```

Defaults to local macOS Google Chrome; `CHROME_PATH` may override it.
1920×1080 only: 50 Startups → Boston → Startups, all three tabs, exact JSON/metric/table values, every curve coordinate, feature orders, keyboard, horizontal overflow and console/network errors.
Screenshots and evidence go to `docs/assets/`. No complete Python regression, nested CV, coverage or five-size matrix is required for this MVP.
The old `browser_smoke.cjs` describes the previous disabled-selector foundation and is superseded for this Dashboard; it was not run or represented as passing here.

Pages uses the existing `pages.yml` deployment workflow. For pre-merge review the owner-authorized feature branch is specifically allowed in the `github-pages` environment and dispatched manually. Main-only automatic deployment rules and CI remain unchanged.
