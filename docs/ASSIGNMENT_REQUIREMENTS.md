# 作業需求 / Assignment requirements

文件狀態：**Proposed for review**；2026-10-16 查證。這是 Issue #2 的規格，
不是資料分析結果或教授已核准所有提案的聲明。

## 證據與狀態 / Evidence and status

來源優先序：教師 repository → 本專案契約與 Accepted ADR → owner 提供的課堂提示。
高優先來源未談及的事項不能自行視為否定較低來源。

- **T1 — 教師範例**：[README（固定版本）](https://github.com/huanchen1107/AIoT-DIC2-MultipleLR/blob/8b65e3bd9745e650ae7bea28f9562c059d5029ed/README.md)。
  已讀 README 與 main.py 的資料來源／切分設定。此範例展示 50 Startups、CRISP-DM、
  迴歸及特徵選擇；不等於完整課堂評分規範。未執行教師程式、未驗證其績效或圖表。
- **T2 — 教師程式**：[main.py（同版本）](https://github.com/huanchen1107/AIoT-DIC2-MultipleLR/blob/8b65e3bd9745e650ae7bea28f9562c059d5029ed/main.py)。
  僅作實作參考，不直接複製其前處理或以測試集尋找最佳特徵的方式。
- **P1 — 專案契約**：[README](../README.md)、[AGENTS](../AGENTS.md)、
  [架構](ARCHITECTURE.md)、[Accepted ADR-0001](adr/ADR-0001-project-foundation.md)。
- **O1 — Owner 課堂紀錄**：[Issue #2](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues/2)。
  包含 Kaggle 搜尋提示、sklearn／CRISP-DM、R²／MSE 與圖像解釋；這是 owner 轉述，
  不是已取得的教授原始講義。兩題選一提交與 bonus 的紀錄見 P1。
- **I3 — 下一項工作**：[Issue #3](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues/3)。
- **X1 — 未驗證舊實驗**：[DIC-2_test](https://github.com/wupojung/DIC-2_test)。
  本次未讀取／執行，不用於權威需求或分析結論。

**Confirmed / 已確認**：來源明確記載；需標明是專案要求或教師範例，
不代表教授另行確認。**Inferred / 推論**：本專案提出的實作解讀。
**Needs Instructor Confirmation / 待教授確認**：會影響作業解釋的未決問題。
P0 是必要交付／正確性，P1 是建議方法，Optional 無已知加分權重。

## 需求矩陣 / Requirement matrix

| ID / 教師或專案要求 | Interpretation / 解讀與狀態 | Evidence | Priority | Open question / 待確認 | Acceptance / 驗收 |
| --- | --- | --- | --- | --- | --- |
| R1 兩題，選一提交 / two problems, submit one | Confirmed（P1 專案紀錄）；50 Startups → Boston Housing | P1；T1 僅佐證第一題範例 | P0 | Q1 提交格式、期限及第二題來源／倫理要求？ | 兩題各有六階段證據，教師確認最終提交主題與格式 |
| R2 sklearn + CRISP-DM | Confirmed（O1 紀錄、T1 範例） | O1、T1 | P0 | 是否另要求特定套件版本？ | Python 可重現；六階段輸入／輸出／驗收可追溯 |
| R3 R² / MSE 與圖像解釋 | Confirmed（O1 紀錄）；MAE/RMSE、殘差為專案補充 | O1、P1 | P0 | Q2 有無指定圖型、最低分數或 rubric？ | 實測指標、有單位、真實值對預測及殘差圖與限制說明 |
| R4 Kaggle features >13, <40 | Confirmed（搜尋語句存在）；是否硬性條件為 Needs Instructor Confirmation | O1 | P0 釐清 | Q3 是否所有題目必須來自 Kaggle 且符合 14–39？特徵數如何計算？ | 書面記錄教授答覆；未答覆前不得擅自淘汰指定題目 |
| R5 特徵選擇比較 / selection comparison | Inferred：Pearson、F-test、RFE、SFS、LassoCV 依 Issue #2 規劃；非斷言教師指定此五種 | O1 issue、T1 範例 | P1；不屬 I3 baseline | Q4 教授必做的方法與比較單位？ | 同估計器、同資料切分與評估方式；訓練內決定特徵 |
| R6 dataset dropdown / 任意 CSV URL | Confirmed（P1 記錄為 possible bonus）；權重 Needs Instructor Confirmation | P1 | Optional | Q5 是否加分、權重、任意 CSV 的限制？ | 核准後才實作；若實作必須重算且不能以假結果冒充 |
| R7 可重現與人工審查 / reproducibility and review | Confirmed（專案要求） | P1、I3 | P0 | 資料使用權及前處理細節待審 | 固定來源／切分／環境；PR 記錄五關；不自動 merge／close |

## 搜尋提示與特徵數 / Search prompt is not yet a binding rule

O1 記錄的搜尋提示為 `list kaggle multiple linear regression problems, choose features > 13, < 40`。
若以整數特徵計算，範圍為 14–39；但尚不清楚這是找候選資料的提示，還是兩題均適用的正式限制。
原始 predictors 不含 target，也不能將 one-hot 展開數偷偷當成原始欄位數。

T1 以 50 Startups 為示範，P1 指定兩題；所以不能僅依搜尋提示就推定這些題目被禁止。
也不能宣稱它們已滿足 14–39。請教授確認 Q3：Kaggle 是否強制、範圍是否強制、
是算原始欄位、編碼後欄位，還是含 target 的總欄位？回答前維持待確認，保留原訂題目。
預期 schema 與待驗證數量見 [問題定義](PROBLEM_DEFINITIONS.md)。

## 決策與 Issue #3 readiness / 開工清單

目前 **規格可供審查，資料／分析尚未就緒**。以下核准不得由 Codex 假定：

- [x] ADR-0001 Accepted，foundation 已由 owner merge。
- [x] 兩題目標、預期特徵及限制已有規格，非實測 schema。
- [x] [評估協定](EVALUATION_PROTOCOL.md) 已提出；[工作流程](WORKFLOW_REUSE.md) 已定義未來介面。
- [ ] Owner 接受 Issue #2 PR 與評估提案（80/20、seed 42、5-fold、無洩漏管線）。
- [ ] 教授／owner 釐清 Q1–Q5，或逐項記錄允許先做 I3 的暫行範圍；不得標成教師已確認。
- [ ] 核准 50 Startups 來源、版本／可用性、license、取得方式與單位；I3 取得後記錄 checksum。
- [ ] I3 實測核對預期 50 rows、四個原始 predictors、Profit、缺失與重複；不合即停止查明。
- [ ] 核准 State 編碼／未知類別、缺值／重複策略；確認 row ID、切分與 fold 記錄格式。
- [ ] 核准 I3 dependency 版本與 Python 相容性、執行入口、產物隔離及重現驗收。
- [ ] Boston 資料來源與倫理處理另外核准；它未就緒不等於 I3 必須實作它。

I3 僅實作 50 Startups baseline、EDA、訓練 CV 與一次 holdout、圖表與可重現匯出。
不包含 feature-selection suite、Boston 訓練、Web 整合或 CSV URL。成功門檻是正確、
可重算且無洩漏，不擅設最低 R²。實作測試與產物契約見另外兩份規格。
