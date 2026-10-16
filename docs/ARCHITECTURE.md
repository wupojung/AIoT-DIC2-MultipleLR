# Architecture

## Implemented foundation
| Area | Responsibility |
| --- | --- |
| python/src | Environment check + accepted baseline + training-only feature selection CLI (review pending) |
| web | Static dual-dataset Dashboard; Overview/Feature Selection/Evaluation, local SVG charts and reviewed JSON exports |
| data | Pinned source metadata; ignored verified download cache |
| outputs | Ignored generated artifacts; tracked placeholder only |
| docs | CRISP-DM gates, glossary and architecture decisions |
| tests | Foundation/browser checks + offline leakage, metrics, integrity and reproducibility tests |

The Web has no dependency on Python execution and uses no external assets.

## Planned, not implemented
Python now implements the 50 Startups baseline with fold-local preprocessing, training CV,
once-per-run frozen holdout evaluation and dataset/run-specific artifact export.
Issue #4 adds a separate training-only feature-selection experiment, independent verifier
and report exporter. Its nested selection uses 5/3 folds with 3-fold selector-local CV;
all predictions are LinearRegression. It never calls holdout prediction.
Issue #3 code/results and accepted ADRs remain intact. Boston MVP now uses the same parameterized regression/selection core with its own pinned-source loader,
12-predictor configuration (B excluded), dummy baseline, frozen final holdout and report/verifier.
See [Boston evidence](reports/boston_housing/REPORT.md); human review remains pending.
Runtime artifacts are ignored; curated review figures may be recorded in docs/reports/.
Issue #6 adds the standard-library export_dashboard.py adapter and schema_version=1 static JSON in web/data.
The browser fetches both snapshots once and redraws all panels on dataset change. Built-in views never execute ML. Issue #7 adds a DOM-free CSV/SVD engine in a module Worker,
with a separate custom importer/view; only a single JavaScript implementation ships. See [Custom contract](CUSTOM_CSV.md).
ADR-0002 remains Proposed; this MVP is directly authorized by the task and its PoC evidence, not ADR acceptance. No API or model service exists; the existing GitHub Pages workflow hosts only web/.
See [ADR-0001](adr/ADR-0001-project-foundation.md) and [CRISP-DM](CRISP_DM.md).
