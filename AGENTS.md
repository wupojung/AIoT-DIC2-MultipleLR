# Repository instructions

Read root README.md, this file, the active GitHub issue, docs/ARCHITECTURE.md,
docs/CRISP_DM.md and relevant ADRs before modifying existing work.

## Scope and boundaries
- DIC-2 teaches multiple linear regression using 50 Startups, then Boston Housing.
- Foundation only in issue #1: no training, API, CSV import, deployment or copied prior codebase.
- Distinguish implemented behavior from plans. Never fabricate metrics or features.
- Do not commit credentials, .env, environments, private datasets, caches or model artifacts.
- Keep dependencies minimal; explain additions. Use readable Python and semantic, accessible HTML.
- Work on a feature branch; submit a PR. Never auto-merge or close the issue before human acceptance.
- Teachers own assignment interpretation and final acceptance; propose changes to decisions through ADRs.

## Required gates (in order)
1. BUILD: clean checkout; `python3 -m venv .venv`, then `.venv/bin/python -m pip install -r requirements.txt` (Windows: `.venv\Scripts\python`).
2. RUN: `.venv/bin/python python/src/environment_check.py`; serve `python3 -m http.server 8000 --directory web` and inspect the page in a browser.
3. TEST: `.venv/bin/python -m unittest discover -s tests -v`; browser-check tabs, placeholders, responsive layout and console.
4. VERIFY: `git diff --check`; review required files, links, scope, secrets and actual results.
5. PASS: report exact commands and results in PR, with skipped checks explicit. Failed required gates block PASS.

CRISP-DM phase gates require recorded input/output evidence and review before progressing;
see docs/CRISP_DM.md. Fit preprocessing/selection on training folds only. Reserve test data
for final evaluation and compare methods on identical splits. Boston source/ethics must be reviewed.
