# AIoT DIC-2 — Multiple Linear Regression Lab

[![Pages Deployment](https://github.com/wupojung/AIoT-DIC2-MultipleLR/actions/workflows/pages.yml/badge.svg)](https://github.com/wupojung/AIoT-DIC2-MultipleLR/actions/workflows/pages.yml)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](python/README.md)
[![CI](https://img.shields.io/badge/CI-Not%20Configured-lightgrey)](https://github.com/wupojung/AIoT-DIC2-MultipleLR/actions)
[![Coverage](https://img.shields.io/badge/Coverage-Not%20Measured-lightgrey)](tests/)

**English** · [繁體中文](README.zh-TW.md)

**NCHU AIoT 2026 · Doing in Class 2** — A reproducible multiple linear regression and feature selection laboratory built with Python, scikit-learn, and the six-phase CRISP-DM methodology.

### Live demo

**[Open the GitHub Pages dashboard](https://wupojung.github.io/AIoT-DIC2-MultipleLR/)** · [Check deployment status](https://github.com/wupojung/AIoT-DIC2-MultipleLR/actions/workflows/pages.yml)

> **Scope of the current demo:** The Web dashboard is a static UI preview, not a live model-serving application. Dataset switching, CSV import, and in-browser regression are not yet available. Follow the deployment status link to confirm whether the site is online.

<!-- Dashboard screenshot: intentionally deferred until an approved capture is provided. -->

## Overview

This project studies **ordinary least squares (OLS) multiple linear regression**, reproducible evaluation, and feature selection. Experiments and charts come from actual Python executions; visualizations are not hand-filled with synthetic scores.

**What has been implemented**

- **50 Startups baseline:** A pinned, checksum-verified dataset; 80/20 train/test split; fold-local preprocessing; LinearRegression and a mean-prediction Dummy baseline; five-fold training CV and a frozen holdout evaluation.
- **Feature selection:** Pearson correlation, F-test, RFE, forward SFS, and LassoCV-based ranking, all evaluated with the same downstream LinearRegression model. Training-only CV and nested model-selection assessment prevent tuning on the holdout.
- **Reproducibility:** Source hashes, split identifiers, validation checks, recorded predictions, executable verification, and traceable reports.
- **Web UI foundation:** Responsive Overview / Feature Selection / Evaluation tabs, with actual model-data integration planned separately.

**Planned:** Boston Housing workflow reuse ([Issue #5](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues/5)), interactive dashboard integration ([Issue #6](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues/6)), and custom CSV support ([Issue #7](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues/7)). These are **not described as delivered features**. The historic Boston Housing dataset has known ethical limitations.

## Verified experimental results

| Experiment | Measurement | Reported result |
| --- | --- | ---: |
| 50 Startups OLS baseline | Holdout R² | **0.898727** |
| 50 Startups OLS baseline | Holdout RMSE | **9,055.957** |
| Feature-selection procedure | Nested CV mean RMSE | **9,237.359** |
| Frozen training-based selection | Selected method and feature count | **F-Test, k=3** |

The holdout is **10 observations**. RMSE is in the source's numeric units; currency and reporting period are unverified. Nested CV figures are **not** new independent holdout scores. See the [baseline report](docs/reports/50_startups/report.md), [feature selection report](docs/reports/feature_selection/REPORT.md), and [evaluation protocol](docs/EVALUATION_PROTOCOL.md).

## Engineering quality and deployment

| Check | Current status | Evidence |
| --- | --- | --- |
| GitHub Pages deployment | GitHub Actions workflow is configured; live status must be checked | [Pages workflow](https://github.com/wupojung/AIoT-DIC2-MultipleLR/actions/workflows/pages.yml) |
| Python / browser checks | Local tests and verification scripts exist; no dedicated CI workflow yet | [Tests](tests/) · [Verification reports](docs/reports/) |
| Test coverage | Not yet measured; **no percentage claimed** | [Tests](tests/) |
| Research provenance | Pinned dataset, stored metadata, fold isolation and reproducibility checks | [Data policy](data/README.md) · [Reports](docs/reports/) |

A green deployment badge indicates the GitHub Pages workflow result, **not** that the regression backend or CSV analysis is working. The existing `.github/workflows/pages.yml` deploys the `web/` directory; README-only changes do **not** trigger its current path-filtered workflow.

## CRISP-DM workflow

| Phase | Purpose |
| --- | --- |
| 1. Business Understanding | Define the target, scope, and research limitations |
| 2. Data Understanding | Check provenance, schema, statistics, and data quality |
| 3. Data Preparation | Split data and apply training-only preprocessing |
| 4. Modeling | Run OLS, dummy baseline, and cross-validation |
| 5. Evaluation | Report MAE, MSE, RMSE, R², diagnostics, and feature selection |
| 6. Deployment | Publish reproducible results and progressively develop the UI |

**Research integrity:** All selectors are fitted inside the relevant training folds. Reported charts are generated from actual runs. Do not choose features using holdout results or compare RMSE directly across datasets with different target units.

## Quick start

Requires Python **3.12+** and a browser. Dependencies and version constraints are documented in [requirements.txt](requirements.txt) and [constraints.txt](constraints.txt).

```sh
git clone https://github.com/wupojung/AIoT-DIC2-MultipleLR.git
cd AIoT-DIC2-MultipleLR
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python python/src/environment_check.py
python python/src/startups_baseline.py --run-id baseline-v1
python -m unittest discover -s tests -v
python -m http.server 8000 --directory web
```

Open <http://localhost:8000/> to preview the static UI. The baseline downloads the **pinned and SHA-256 verified** teaching CSV on its first run; generated outputs are excluded from Git. For feature selection execution and validation, follow the [reproduction instructions](docs/reports/feature_selection/REPORT.md). See [Python instructions](python/README.md) for other operating systems.

## Public CSV examples — for future custom dataset support

The following public files are **candidate regression inputs** for testing the future import feature; **the current website cannot analyze them yet**. Users will need to select a numeric target and suitable feature columns, handle missing/categorical values, and fit the new dataset from scratch.

| Dataset | CSV | Suggested target | Suggested predictors | Caveat |
| --- | --- | --- | --- | --- |
| 50 Startups | [CSV](https://raw.githubusercontent.com/Avik-Jain/100-Days-Of-ML-Code/master/datasets/50_Startups.csv) | `Profit` | `R&D Spend`, `Administration`, `Marketing Spend`, `State` | `State` requires encoding; small sample |
| Auto MPG | [CSV](https://raw.githubusercontent.com/mwaskom/seaborn-data/master/mpg.csv) | `mpg` | `cylinders`, `displacement`, `horsepower`, `weight`, `acceleration` | Missing horsepower values |
| Restaurant Tips | [CSV](https://raw.githubusercontent.com/plotly/datasets/master/tips.csv) | `tip` | `total_bill`, `size` | Other categorical fields need encoding; no causal claim |

CSV URL downloads may be blocked by **CORS**, authentication, or source restrictions. File upload is a proposed fallback, not a current capability. Arbitrary CSVs are not guaranteed to be valid regression datasets; feature/target types, sample count, dependence, leakage, and source rights require checking.

## Documentation and references

- **Research:** [CRISP-DM](docs/CRISP_DM.md) · [Feature-selection protocol](docs/FEATURE_SELECTION_PROTOCOL.md) · [Evaluation protocol](docs/EVALUATION_PROTOCOL.md) · [Workflow reuse](docs/WORKFLOW_REUSE.md)
- **Architecture:** [Architecture](docs/ARCHITECTURE.md) · [ADR-0001 (Accepted)](docs/adr/ADR-0001-project-foundation.md) · [ADR index](docs/adr/README.md) · [ADR-0002 proposal](https://github.com/wupojung/AIoT-DIC2-MultipleLR/pull/12)
- **Data:** [Dataset definitions and ethics](docs/PROBLEM_DEFINITIONS.md) · [Data policy](data/README.md) · [Glossary](docs/GLOSSARY.md)
- **Project:** [Issues](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues) · [Course reference by Professor Huan Chen](https://github.com/huanchen1107/AIoT-DIC2-MultipleLR) · [Previous experiment](https://github.com/wupojung/DIC-2_test)
- **UI inspiration:** [StatsUnlock multiple regression calculator](https://statsunlock.com/multiple-linear-regression-calculator/)

**Development process:** Codex works in feature branches and follows **BUILD → RUN → TEST → VERIFY → PASS**. Pull requests require manual review and explicit approval before merging. The assignment's final submission requirements and historical source limitations remain subject to instructor confirmation.
