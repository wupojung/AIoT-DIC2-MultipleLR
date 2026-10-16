# Python baseline / 執行指南

Baseline 使用 Python 3.12+；實測／.python-version 為 3.14.2。環境 smoke check
本身仍僅需標準函式庫，原始 foundation 的 3.11 設定不適用目前 numpy/scipy 相依。
requirements.txt 明列四個直接相依與用途：numpy（數值驗證）、pandas（schema/EDA）、
scikit-learn（Pipeline/CV/迴歸）、matplotlib（真實結果圖）。constraints.txt 固定本次
驗證的間接相依版本；joblib 僅是 sklearn 相依，沒有模型序列化或額外 framework。
其他平台／版本未實測，安裝失敗不得宣稱通過。

macOS，從 repository root：
```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python python/src/environment_check.py
python python/src/startups_baseline.py --run-id baseline-v1
python python/src/verify_startups_run.py outputs/50_startups/baseline-v1 --source data/50_startups/50_Startups.csv
python -m unittest discover -s tests -v
```
Windows PowerShell（選用已安裝的 Python 3.12+）：
```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe python/src/environment_check.py
.\.venv\Scripts\python.exe python/src/startups_baseline.py --run-id baseline-v1
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

第一次執行會從固定 revision 下載唯一的 50 Startups CSV，校驗 SHA-256 再解析；
需網路。之後用 data/50_startups/ 的已驗證 cache 可離線重跑。
不得靜默接受改動的 CSV。沒有任意 CSV URL 介面。
`--cache-dir` 可更換 cache 位置，`--output-root` 可更換匯出根目錄；run-id 只接受
ASCII 字母／數字／底線／連字號。既有 run 直接失敗，不覆寫測試結果。

產物位於 `outputs/50_startups/<run-id>/`，預設不提交：

| Artifact | 用途 |
| --- | --- |
| provenance.json / environment.json / config.json | 固定來源、hash、使用限制、取得時間、環境與方法 |
| data_quality.json | 全資料結構／缺值／重複稽核；非全資料建模 EDA |
| train_descriptive_statistics.csv / train_correlation.csv | 只使用 40 筆 training 的統計及相關性 |
| train_distributions.png / train_correlation.png / train_state_counts.png | training-only EDA |
| splits.json / training_cv.json / train_cv_predictions.csv | train/test IDs、每折 IDs、fold-local 中位數／類別、CV 指標與預測 |
| fitted_model.json / frozen_plan.json | 最終訓練欄位／係數與 holdout 前的凍結設定；非可載入的模型檔 |
| metrics.json / holdout_predictions.csv | CV mean/std、10 筆 holdout 四指標及 y/ŷ/residual、Dummy 參考 |
| holdout_*.png / REPORT.md / status.json | 診斷圖、限制及技術完成／失敗狀態，人工 gate 仍待審 |

80/20、seed 42；train 內 5-fold。補值、State one-hot drop-first 都在每折 training
擬合；unknown State 記數並編成全零，可能與 reference category 重合。全空欄、
缺失 target、錯誤 schema、非有限值及重複 predictors 明確拒絕，需另行 review，
不依 holdout 成績刪列。不能用多次重跑找最佳 seed/k；不同 run-id 的重跑僅供重現核對。
Baseline 命令沒有特徵選擇；本次沒有 Boston、Web 整合或部署。原始蒐集、幣別、期間及公司獨立性未知，
不作因果推論。來源 repository 的 MIT 不代表原始資料權利已獨立查明；不提交原始 CSV。

參考：[評估協定](../docs/EVALUATION_PROTOCOL.md)、
[資料來源 manifest](../data/50_startups_manifest.json)、
[CRISP-DM](../docs/CRISP_DM.md)。真實資料結果應由 baseline 命令產生；tests 的合成資料
只用於檢驗無洩漏、指標、失敗處理與重現性，不能冒充真實分析。

[實測結果與六張圖](../docs/reports/50_startups/report.md) 是供審查的固定執行證據，
不由程式寫死；新的 run 會在 outputs 另行產生自己的結果。

## Issue #4 — Feature Selection

不更動 Baseline；同一套相依即可執行五種真正選擇器及 All Features 對照：
```sh
python python/src/feature_selection.py --run-id fs-v1
python python/src/verify_feature_selection.py outputs/50_startups/feature_selection/fs-v1 --source data/50_startups/50_Startups.csv --replay-lasso
python python/src/report_feature_selection.py outputs/50_startups/feature_selection/fs-v1 --output-dir /tmp/fs-review
```
Windows 同樣可用 `.\.venv\Scripts\python.exe` 取代 python，輸出目錄改為本地新目錄。
run-id 和報告目錄不得已存在。第一個命令僅讓原 40 train 進入比較器，不做 holdout
預測；輸出在獨立 feature_selection/ 子目錄，不覆寫原實驗。

[實驗協定](../docs/FEATURE_SELECTION_PROTOCOL.md) 說明 5/3/3 folds、State 編碼計數、
真正 SFS、LassoCV fold blocks 與 zero-coefficient padding。
[繁中分析與兩張曲線](../docs/reports/feature_selection/REPORT.md) 及其 JSON/CSV 是實測
審查快照；每次新 run 都自行重算。Verifier 會驗原始 row IDs／每次 fit 的統計、重 fit
所選欄位的 OLS、重算預測指標、replay 多 alpha path，並由 CSV 重畫比對兩張 PNG。
曲線最低點、nested 選模成績及最後三折凍結方案是不同層級，不混稱最佳 test 結果。
