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

## 狀態與證據紀錄 / Status and evidence

- **Planned**：交付物與驗收已定義，尚未執行。兩題所有分析階段目前都是 Planned。
- **Work in progress**：已有實際輸入／執行紀錄，但驗證尚未完整；列出缺少的證據。
- **PASS**：保存可重現的輸入、命令、產物與驗證結果，且該 gate 已經 reviewer 確認。
  Foundation 或規格文件的技術 PASS 不等於資料分析 PASS，也不取代人工審查。

每個 phase record 應有 dataset_id、phase、status、run_id、來源／config version、
artifact paths、validation commands/results、reviewer 與未決項目。失敗時明確記錄 FAIL
及原因並保留該階段開啟；不得為了推進流程跳過 gate。

## 兩題具體交付 / Dataset-specific traceability

下列均為 **Planned**，對應 [需求 R1–R7](ASSIGNMENT_REQUIREMENTS.md)、
[問題定義](PROBLEM_DEFINITIONS.md) 與 [E1–E5 評估協定](EVALUATION_PROTOCOL.md)。
共通 E1–E5 為待審提案；資料來源與倫理未核准前不開始分析。

| Phase | 50 Startups evidence / 第一題 | Boston Housing evidence / 第二題 | Validation / PASS gate |
| --- | --- | --- | --- |
| 1 Business Understanding | Profit 預測目的、單位待確認、四原始特徵假設與非因果界線 | MEDV 歷史地區預測目的、教學限定、倫理審查與變數處置決策 | R1/R4：teacher/owner 確認問題與未決要求處置；無自創評分門檻 |
| 2 Data Understanding | 核准來源／license/hash；實測 50 rows 假設、schema、缺值／重複與 training-only EDA | 核准歷史版本／license/hash；核對 13 predictors 假設、聚合單位、B/LSTAT 限制、target 截斷及地理相關 | R2/E1：來源 manifest + schema report；不把期待數量記成已驗證；結構稽核後先凍結切分再做導向建模的 EDA |
| 3 Data Preparation | 保存 row IDs／folds、train-only 補值與 State one-hot 欄名／基準類別 | 依核准變數設置 numeric/categorical roles，評估 group/spatial split；不盲用第一題欄位 | E1/E2：無重複／群組跨 split；Pipeline 僅在 training fit；unknown category 可追蹤；無 y 洩漏 |
| 4 Modeling | Issue #3 全核准特徵 LinearRegression + mean Dummy，記錄 train CV；選擇器另期實作 | 用第二題新 split 與新 fit 重跑 baseline，記錄對 workflow 的必要調整 | E1–E3：共用外層 folds 與 estimator；內層選擇也隔離 preprocessing；保存設定、候選與每折結果 |
| 5 Evaluation | 凍結後一次 holdout，四指標、預測／殘差與單位；不沿用教師範例分數 | 同樣輸出四指標與殘差，說明歷史／空間／倫理限制；不與 Profit RMSE 跨單位排名 | R3/E4/E5：由 y/ŷ 重算一致，圖表來自產物；CV/holdout 分開；未達事先條件誠實報告，不偷換 test |
| 6 Deployment | 可重現 baseline 執行與學習報告，記錄第一題可重用部分 | workflow transfer 記錄、限制與第二題報告；兩題完成後選一提交 | R1/R6/R7：clean-environment 重現、report/artifacts 一致、teacher 批准主題／格式；非要求本期 hosting 或 API |

Readiness：見 [Issue #3 開工清單](ASSIGNMENT_REQUIREMENTS.md)。
重用介面與非目標見 [WORKFLOW_REUSE](WORKFLOW_REUSE.md)。
