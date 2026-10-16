# 工作流程重用 / Workflow reuse specification

狀態：**共通函式、Startups 相容入口與 Boston MVP 已實作，待人工 Review**。
沒有通用 config parser、Plugin System 或 Agent Skill；以下原介面表仍是設計契約，
不能把未落地欄位當成可用功能。
目標是將 50 Startups 已審查流程移轉至 Boston，而非複製第一題結論。
[六階段 gates](CRISP_DM.md) 與 [評估協定](EVALUATION_PROTOCOL.md) 為共同契約。

## Objective and proposed interfaces / 目標與介面

未來 config 需描述以下欄位（不是目前接受的命令列格式）：

| Interface | 必要內容 | 驗證與責任 |
| --- | --- | --- |
| DatasetConfig | dataset_id、核准 source revision/hash、target、numeric/categorical features、units、row/group IDs、ethics notes | 各資料集 adapter 驗 schema／provenance，不自行猜 target |
| EvaluationConfig | protocol version、test fraction、seed、folds、group policy、preprocessing、selection budget | 共用 runner 檢查相依性、禁止 target in X、無法安全切分即 fail |
| RunRecord | run_id、config snapshot、環境、split IDs、phase status、artifact paths | 每階段保存驗證證據，不以檔案存在代替 PASS |
| ResultBundle | 每折指標、凍結 holdout predictions、plots、限制、report | dataset/run 目錄隔離；任何 Web 匯出另需 schema 決策 |

50 Startups config 指 Profit 與 State encoding；Boston config 改 MEDV、核准變數與
歷史單位，重新審查空間相關與倫理 gate。兩者共用程式邏輯及測試契約，
不共用已擬合 encoder、scaler、selector、model、split indices 或數值績效。
新增資料集需重新走 Phase 1–2，不能只換 CSV URL 就標六階段 PASS。

## Planned execution / 未來執行順序

1. Validate config + provenance → problem/data report。
2. Audit independent observations → frozen split manifest。
3. Fold-local preprocessing → training CV → frozen selected pipeline。
4. Fit approved training data → once-only holdout → verified evidence bundle。
5. Review phase gates → teacher approves submission; presentation later consumes verified artifacts。

Issue #3 僅建立第一題 baseline 與必需介面，不要求先打造通用框架。
之後累積兩題差異再提取真正可用的 Skill；Skill 的 instructions、觸發條件、
執行入口與測試由後續 issue 定義，此文件不宣稱已安裝或能自動完成分析。

非目標：任意 CSV 自動推斷、模型服務、後端／前端執行決策、部署、CI、
跨資料集直接比較 RMSE、未核准資料下載或任意未核准模型執行。
Issue #3 前置項目見 [readiness checklist](ASSIGNMENT_REQUIREMENTS.md)。

## Issue #5 — 已落地的共用部分（階段性交付）

- `regression_workflow.DatasetConfig`：dataset_id、target、numeric/categorical、
  expected_rows、raw_columns、excluded、transformer 名稱與可選的 expected encoded count。
  source manifest 由各 loader 管理；alpha grid 以明確參數傳入 selector engine，
  並非已存在任意檔案／網址的 config parser。
- 共用 source schema 驗證、target／excluded 與 predictors 隔離、Pipeline、metrics、
  JSON、seeded split/folds；Startups Baseline 現在實際呼叫這些函式。
- `feature_selection.training_experiment(X_train, y_train, config=..., alphas=...)`
  是同一套五方法／nested 程式；只能傳入 training rows，沒有 holdout 引數。
  動態 k 取決於當地實際編碼維度，Startups 預設仍要求五欄／原 alpha grid。
- `plot_curves(..., xlabel=..., units=...)` 共用繪圖，可改特徵軸／單位；
  Startups 預設完全保留。Baseline／Feature Selection 舊 CLI 與 verifier 不變。

已用獨立**合成資料**驗證 60 rows／12 numeric predictors、無 State、另一個 target、
排除欄與自訂 alpha，以及全部五方法／nested／動態 k=1–12；
可執行範例在 [共用核心測試](../tests/test_regression_workflow.py)。
這不是 Boston 實驗，也沒有重用模型、索引、排名或原數值。

Boston adapter 現已實作 pinned loader、hash/schema、B 排除、Baseline + Dummy、五方法、
凍結後一次 holdout、驗證器與繁中報告，詳見 [來源政策](BOSTON_WORKFLOW_PROPOSAL.md) 與
[實測報告](reports/boston_housing/REPORT.md)。CLI：`python python/src/boston_workflow.py --run-id boston-v1`。
共用程式、新 split、新 fit、新排名與新數值；Boston 沒有 State/OHE，alpha grid 另設 1e-4..1e2。
驗證：`python python/src/verify_boston_run.py outputs/boston_housing/boston-v1`。人工接受仍待 Review。
