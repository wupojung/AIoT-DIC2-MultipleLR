# CRISP-DM phase gates

All phases below are planned analysis, not completed by the foundation. For each
phase record inputs, commands, outputs, checks and reviewer decision. A failed
check keeps the phase open. Foundation PASS does not imply any analysis phase PASS.

| Phase / purpose | Inputs | Outputs | Validation and PASS criteria |
| --- | --- | --- | --- |
| 1 Business Understanding: define the question | Assignment and stakeholder constraints | Target, units, intended use, success criteria | Teacher confirms question, scope, target and success criteria before analysis |
| 2 Data Understanding: establish evidence | Approved source and schema | Provenance, license, EDA, quality and ethics notes | Check dimensions, types, missing/duplicate values and target; source and limits reviewed |
| 3 Data Preparation: make reusable inputs | Reviewed raw data and quality notes | Split definition, seed, preprocessing pipeline and feature schema | Verify disjoint train/test; fit imputation, encoding and scaling only inside training folds; no target leakage |
| 4 Modeling: establish reproducible comparisons | Training partition and approved pipeline | Baseline, linear regression and cross-validation records | Repeat with fixed seed; feature selection and tuning use training CV only; same splits across methods |
| 5 Evaluation: assess generalization | Frozen chosen pipeline and untouched test partition | MAE, MSE, RMSE, R², residuals and limitations | Recompute from predictions, verify units and sample counts, compare to baseline; apply phase-1 criteria and review failures |
| 6 Deployment: communicate and reuse | Reviewed evaluation and artifacts | Reproduction instructions, report and optional verified web exports | Reproduce in clean environment; match displayed values to artifacts; teacher approves report and one final submission topic |

## Dataset-specific evidence
| Dataset | Phase 1–2 | Phase 3–4 | Phase 5–6 |
| --- | --- | --- | --- |
| 50 Startups | Profit target; verify currency/units, source and actual schema, including State if present | Review small-sample split/CV feasibility; encode categorical features within folds | Record uncertainty and overfitting risk; obtain review before reusing workflow |
| Boston Housing | MEDV target; verify units/source/license, historical context, problematic racial variable and ethical restrictions with teacher | Reassess schema and features explicitly; do not inherit Startups transformations blindly | Record historical/ethical and target limitations; verify transfer workflow without claiming current-world suitability |

Neither dataset is bundled. Do not fetch or analyze until source and ethical
questions are resolved. Feature-selection methods (RFE, SFS, LassoCV) are future
work and must follow the same leakage and comparison gates. Custom CSV is optional
and has no approved execution architecture yet.
