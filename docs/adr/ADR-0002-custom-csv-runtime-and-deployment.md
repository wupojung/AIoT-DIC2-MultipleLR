# ADR-0002 — Custom CSV Regression Runtime and Deployment

- Status: Proposed
- Date: 2026-10-16
- Decision owner: Repository owner (wupojung)
- Related: Issue #7 (Custom CSV bonus), Issue #6 (Dashboard), ADR-0001
- Scope: deployment/runtimes for user-selected CSV datasets; no implementation approval yet

## Context
The site will offer built-in 50 Startups and Boston Housing views, plus optionally a user-supplied dataset. A CSV may have different columns, types, target and feature candidates. It is **not valid** to apply a saved 50 Startups model, features, or scores to an unrelated dataset. The analysis must be recomputed for the selected CSV and schema. Course requirements and bonus grading remain subject to confirmation.

## Proposed architectural policy
Prefer a **static, browser-executed** solution when it meets validated functionality and performance needs:
1. **JavaScript in browser → GitHub Pages**, when CSV parsing, preprocessing, OLS LinearRegression, metrics and required feature-selection methods can be independently verified.
2. **Python via Pyodide in browser → GitHub Pages**, if tested Pyodide/package versions support the required numerical/scikit-learn functionality within acceptable load time/memory. Python running in a browser does **not** itself require a Python host.
3. **Python backend → Vercel (`*.vercel.app`)** only when browser approaches cannot meet requirements. Use Vercel Python functions/API subject to actual platform quotas, supported runtimes, execution time, request limits and security review. Vercel is not an unrestricted always-on Python server.

The presence of Python code alone does **not** trigger Vercel: locally generated and published model artifacts can still be served by GitHub Pages. No requirement exists now for paid hosting.

## Custom dataset contract
- Support user CSV **file upload** as a reliable baseline; CSV URL import if the remote host allows CORS. Do not invent universal CORS bypass or automatically send private files to a third-party service.
- Preview schema and sample rows. User explicitly selects one **continuous numeric target y**, and selects **at least two usable independent predictor X columns**. Never auto-include target in X.
- Support numeric predictors and clearly declared categorical encoding; validate sample sufficiency, missing data, duplicate/group independence, invalid types, non-finite values, constant target, high-cardinality features and overly large files. Reject unsupported cases with actionable explanations; not every CSV is fit for multiple regression.
- Define dataset-specific train/test split, fold-local preprocessing, LinearRegression baseline and feature selection, re-fit from scratch for each new dataset. Recompute predictions, MAE/MSE/RMSE/R², residuals and feature-count curves; never reuse scores, selected features, coefficients or trained estimators from other datasets.
- Treat heavy feature selection as an optional gated capability; report unsupported or skipped selectors transparently, do not simulate results.
- Retain reproducibility evidence: dataset fingerprint (without leaking contents), chosen columns, preprocessing, split seed, method version, metric sources and clear limitations. Do not claim CRISP-DM gates PASS without checks and review.
- Public URLs may fail due to CORS, licensing, authentication or network issues; provide file upload fallback.

## Verification before decision is Accepted
- Build minimal isolated PoCs for browser JS and Pyodide, using at least 50 Startups plus a **different-schema numeric CSV**, and compare metrics against local sklearn under the **same** split/preprocessing.
- Verify category handling, target selection, invalid/empty data, URL CORS errors, file upload, performance/memory, offline limitations, and no fabricated outputs.
- Test actual deployment on GitHub Pages for candidate browser path, including browser refresh, static asset paths and cross-origin restrictions.
- If only backend satisfies requirements, prove a small Python endpoint runs on Vercel under real quotas and acceptable latency; document data privacy/retention and request-size controls.
- Attach real browser screenshots and desktop/mobile Playwright reports to corresponding PRs, with BUILD → RUN → TEST → VERIFY → PASS evidence.
- Produce an implementation selection with measured tradeoffs; ask owner to approve this ADR (or a superseding ADR) before committing to runtime/deployment choice.

## Alternatives and consequences
- Browser JS: simplest hosting, but scikit-learn-equivalent feature selectors may require more code/testing.
- Pyodide: reuses parts of Python stack client-side, but bundles/compatibility and CPU/memory may be limiting.
- Vercel Python API: sklearn fidelity easier, but adds third-party compute, quotas, privacy and operational concerns.
- Static precomputed reports are valid for the two built-in datasets but **do not** fulfill general custom CSV analysis.

## Boundaries
No hosting account configuration, external credential, implementation, deployment, or automatic merge is authorized by this Proposed ADR. ADR-0001 remains Accepted and compatible.
