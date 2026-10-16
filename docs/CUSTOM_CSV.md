# Custom CSV — Regression MVP

選擇 Dataset → **Custom Dataset**，上傳 UTF-8 CSV 或輸入公開 HTTPS CSV URL。
預覽後自行選擇一個連續數值 Y 與至少兩個 X，按 **Run new regression**。
這會真正重新訓練，不讀取內建模型、排名或數值。

## 已實作

- 本地檔案、公開 URL、欄位／前五列預覽、載入／錯誤狀態。
- 數值與低基數非數值類別 X；數值缺值補 training median，類別補 training mode，再按訓練類別排序 drop-first one-hot。Unknown test category 全零並記數。
- 固定 42／80:20；MT19937 permutation 與 sklearn `train_test_split` 的 IDs／順序相同。
- Web Worker 內 fresh SVD OLS + intercept、mean Dummy、MAE/MSE/RMSE/R²、holdout 預測及殘差散點／表格。
- SVD 前只按 training 中心／尺度處理以改善條件數；係數回轉 source units。完整秩檢查與 scaled condition >1e8 拒絕。
- Download run JSON：來源 SHA256、選定 X/Y、split IDs、training 補值／類別／尺度、係數、每筆預測、執行版本與時間。原 CSV 不包含於下載；要重現須自行保留原 CSV。JSON 包含結果與來源 URL，分享前自行確認內容。
- 更換檔案／Target／Features 清除舊結果；切換內建資料集不混用數值；可取消 worker，20 秒上限。

## 明確未實作

**Custom Feature Selection 為 Not Available**：五方法排名、k 曲線、training CV／nested CV 另行擴充。
本次依任務允許分開交付 Regression MVP；沒有用固定排名、單次全資料相關性或內建 JSON 冒充。
Feature Selection 頁只列實際設計矩陣欄名，明示「不是排名」。既有兩資料集的五方法結果不變。

沒有 Vercel、Flask、API、資料庫、帳號、遠端模型服務；ADR-0002／PR #12 保持 Proposed。
目前是使用者授權的 MVP 技術選擇，不宣稱 ADR 已獲接受。

## 輸入邊界／限制

CSV 固定逗號分隔／UTF-8、最多 2 MiB、20–2000 data rows、3–40 columns、2–12 raw X、最多 20 encoded inputs。
Category 每個 training column 2–10 levels；不自動將數字代碼猜成類別。混合數值／文字欄須先清理；常數、全空 training X、缺失／非數值 Y、NaN/Inf、重複欄名／predictor rows、collinearity 明確拒絕，不默默刪列。
Y 至少五個 distinct values 只是防誤用的必要檢查，仍須使用者選擇真正連續 target。Train 至少 16 筆且 ≥3×(encoded inputs+intercept)；有些 20-row 檔案仍會因高維拒絕。
資料中的非空 numeric values 必須是有限十進位；空字串才表示缺值。未選欄仍需完整 CSV 結構。

無 time/group/spatial split。重複資料檢查不能證明獨立性；公司／人／時間群組需使用者先審查。
本次沒有以 holdout 選 k 或調參；若人為看完 holdout 再改 X/Y，結果只能視為探索，不能宣稱新獨立測試。

URL 使用原生 fetch/CORS，credentials omit、no-referrer、15 秒 timeout、streaming size cap，無 proxy。CORS／HTTP／格式失敗時明示檔案上傳替代。
CSV 僅在 browser memory，worker 也不呼叫雲端；URL 載入必然向該公開站點請求。沒有將 CSV 傳到本站、資料庫或分析服務。
GitHub Pages／HTTPS 或 localhost HTTP 才是支援的使用方式；不支援 file://。

## 重現與驗證

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tests/generate_custom_reference.py
node --test tests/custom_engine.test.mjs
python3 -m http.server 8000 --directory web
NODE_PATH=/tmp/dic2-browser/node_modules node tests/custom_browser.cjs
```

50 Startups reference 下載原 pinned manifest／驗 hash；不在 repo 重散布原 CSV。
`tests/fixtures/custom_numeric.csv` 是明確標記的 96-row **合成測試資料**，另一個 schema、quoted comma／Unicode 欄名及 5 個空值；不冒充真實住房觀測。
參考程式只跑兩個小型 sklearn fit，不重跑既有 Baseline／Feature Selection／Nested CV。
浮點容忍：預測 absolute 1e-6，指標 absolute 1e-6 + relative 1e-10（MSE 大量級需相對容忍）；實際誤差見 report。

[選型／實際結果與正式截圖](reports/custom_csv/REPORT.md)。
