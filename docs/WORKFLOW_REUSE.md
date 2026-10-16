# 工作流程重用 / Workflow reuse specification

狀態：**設計草案，沒有可執行 runner、config parser 或 Skill**。
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
跨資料集直接比較 RMSE、未核准資料下載或任何本次模型執行。
Issue #3 前置項目見 [readiness checklist](ASSIGNMENT_REQUIREMENTS.md)。
