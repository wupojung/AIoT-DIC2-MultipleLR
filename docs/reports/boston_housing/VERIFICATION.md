# Boston MVP — BUILD → RUN → TEST → VERIFY → PASS

**技術關卡 PASS；人工／教師接受仍待審查。**

在 `/tmp/dic2-05-mvp-check` 由本分支 clean local clone 建立全新 venv；Python 3.14.2 / macOS arm64。
沒有新增套件或更動 requirements/constraints。依序完成以下關卡，未執行項目不列 PASS。

## BUILD — PASS

```sh
git clone --local --branch dic2-05-boston-workflow . /tmp/dic2-05-mvp-check
python3 -m venv /tmp/dic2-05-mvp-check/.venv
/tmp/dic2-05-mvp-check/.venv/bin/python -m pip install -r /tmp/dic2-05-mvp-check/requirements.txt
/tmp/dic2-05-mvp-check/.venv/bin/python -m pip check
```

安裝成功；pip check: No broken requirements found。套件版本見 environment.json。

## RUN — PASS

在 clone root：

```sh
.venv/bin/python python/src/environment_check.py
.venv/bin/python python/src/boston_workflow.py --run-id boston-mvp-v1
.venv/bin/python python/src/startups_baseline.py --run-id issue5-regression
.venv/bin/python python/src/feature_selection.py --run-id issue5-regression
python3 -m http.server 8000 --directory web
```

兩份資料皆在 clean clone 實際從 pinned URL 取得並核對 hash；不使用 load_boston。
Boston 506×14、B 排除後 12 欄、404 train / 102 holdout；各 CLI 正常結束。
Boston 24 組 selector contexts、1,440 個 method/k 特徵集合、148,268 筆 training predictions。
凍結 LassoCV/k=10 後才產生各模型的 102 筆 holdout 預測。

## TEST — PASS

```sh
.venv/bin/python -m unittest discover -s tests -v
NODE_PATH=/tmp/dic2-browser/node_modules node tests/browser_smoke.cjs
```

**32 tests PASS**，完整 stdout/stderr 見 [tests.txt](tests.txt)，含原 21 項、共通重用 8 項與 Boston 必要防護 3 項。
原有實測資料／測試沒有改寫。Source hash/schema、B/target 排除、training medians、固定協定皆有測試。

Playwright + 本機 Google Chrome 真實瀏覽器：1920×1080、1440×900、768×1024、390×844、375×812；HTTP/file 共 **10/10 PASS**。
檢查頁籤、狀態、鍵盤、文字／水平溢出，console/JS/network errors/warnings 均 0。
在 temp clone 產生 15 張 full-page screenshots，未覆寫已接受的 repo screenshots；本次未修改 Web。
詳細 [web_smoke.json](web_smoke.json)。完整平台矩陣與 UI 擴充 QA 延至 Issue #8。

## VERIFY — PASS

```sh
.venv/bin/python python/src/verify_boston_run.py outputs/boston_housing/boston-mvp-v1
.venv/bin/python python/src/verify_startups_run.py outputs/50_startups/issue5-regression --source data/50_startups/50_Startups.csv
.venv/bin/python python/src/verify_feature_selection.py outputs/50_startups/feature_selection/issue5-regression --source data/50_startups/50_Startups.csv --replay-lasso
git diff origin/main HEAD --check
git diff origin/main HEAD -- docs/adr docs/EVALUATION_PROTOCOL.md docs/FEATURE_SELECTION_PROTOCOL.md docs/reports/50_startups docs/reports/feature_selection requirements.txt constraints.txt web .github tests/test_startups_baseline.py tests/test_feature_selection.py
```

- Boston verifier：來源、精確 splits/folds、train/test 隔離、fold-local imputer/scaler 統計、五方法及所有 k 集合、Lasso alpha path 最小點皆通過。
- 148,268 筆 training 預測與 306 筆 holdout 預測的四項指標重算一致；另從原始來源獨立重擬合各 context/subset 的 LR 預測，並核對 nested 決策僅由 inner scores 產生。
- comparison.csv/plot_data.csv 一致；兩張實際程式繪圖已目視檢查。外層固定方法/k 曲線與 final inner selection 分開。
- 第二次 clean run 與開發 run：12 個數值／設定／PNG 產物 byte-identical，解壓後 training CSV 內容一致（gzip header 時間不作數值重現條件）。
- Startups Baseline verifier PASS；Feature Selection verifier PASS，包含 24 組 LassoCV paths 獨立 replay。
- Startups Baseline 20 個產物、Feature Selection 13 個產物與先前接受的參考 byte-identical；來源取得時間不納入比對，hash 另驗。詳見 verification.json。
- Protected paths diff 為空，原 ADR、凍結評估規則、依賴、舊實驗、舊測試、Web/部署保持一致；whitespace clean。

## 產物與限制

本目錄是程式輸出 review snapshot，包含完整 results.json、predictions.csv.gz、每個 context/method/k 的 selected_features.csv、metrics/圖表資料與兩張 PNG。
可在全新 output run 重新產生；run-id 已存在時拒絕覆寫。`results.json` 較大，GitHub 可能需 Raw/下載檢視。
Runtime outputs/cache 仍被忽略；不提交 raw CSV、模型檔或環境。

Owner 的來源／B／alpha／split 決策為暫行專案決策，不代表教師批准或新資料授權。
原始權利／來源完整歷史未完全釐清；資料過時、MEDV 可能截斷、空間相關及代理偏誤仍是限制。
本次不做完整 selector algorithm replay、跨平台／覆蓋率、Web 資料整合或部署；完整 QA 交 Issue #8。
Ready for Review 不等於人工接受；不 Merge、不關閉 Issue #5。
