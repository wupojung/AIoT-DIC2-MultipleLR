# Custom CSV Regression MVP — BUILD → RUN → TEST → VERIFY → PASS

**技術 PASS 僅限本次 Regression MVP；Custom 五方法 Feature Selection 尚未交付，Issue #7 仍等待 Review，不宣稱全部驗收完成。**

## BUILD — PASS

由獨立分支（最新 main `86ff2ce`）local clean clone `/tmp/dic2-07-clean`，建立新 venv，安裝既有固定 requirements；沒有變更 ML 依賴。

```sh
git clone --local --branch dic2-07-custom-csv . /tmp/dic2-07-clean
python3 -m venv /tmp/dic2-07-clean/.venv
/tmp/dic2-07-clean/.venv/bin/python -m pip install -r /tmp/dic2-07-clean/requirements.txt
# From clone root:
.venv/bin/python -m pip check
```

Python 3.14.2 / macOS arm64；pip check: No broken requirements found。
瀏覽器不需 Python／npm 安裝：純靜態 vendored ES modules，含 MIT notices 和 build dependency lock。

## RUN — PASS

```sh
.venv/bin/python python/src/environment_check.py
.venv/bin/python tests/generate_custom_reference.py
python3 -m http.server 8002 --directory web
```

環境 PASS。Reference generator 從原 pinned source 取得並驗 hash，獨立 sklearn 1.9.1 對兩份 CSV 做小型 baseline fit（不是重跑原有 Nested CV）。96-row fixture 的來源明確是合成測試。
乾淨 checkout 重新產生的 `tests/fixtures/custom_reference.json` 與提交參考逐位元組一致。

## TEST — PASS

```sh
node --test tests/custom_engine.test.mjs
.venv/bin/python -m unittest discover -s tests -v
DASHBOARD_URL=http://localhost:8002/ NODE_PATH=/tmp/dic2-browser/node_modules node tests/custom_browser.cjs
```

- **9/9 JS core tests PASS**，82.699 ms，見 [engine-tests.txt](engine-tests.txt)。CSV quoting/BOM/newline、精確 sklearn split（6 大小）、兩份 CSV 的預測／四指標／Dummy、train-only 中位數／尺度／係數、unknown category、重新訓練、target exclusion、常數／collinearity／duplicates／invalid inputs。
- **32/32 原有 Python tests PASS**，11.606 秒，見 [python-tests.txt](python-tests.txt)。包含既有 leakage／reproducibility／verifier 小型測試；沒有覆寫 accepted experiments，也未重跑完整原 Nested CV CLI。
- Local browser E2E **PASS**：URL 讀取 50 Startups（含 State）和檔案上傳另一 schema；自行選 X/Y → module Worker → 下載 fresh run JSON；實際值全部比對 sklearn。
- 設定更動會清除舊分數；target checkbox disabled；Custom FS 顯示 Not Available；內建兩份三頁功能正常。
- 真正 `https://example.com/` response 沒有 ACAO，Chrome CORS 拒絕後 UI 明示 local-file fallback，沒有 proxy。此預期 CORS console error 單獨保存，Unexpected Console / JS errors 為 0。
- 開發期 route mock 沒有正確觸發 CORS，已改用實際站點；clean 第一次 core test 在來源下載尚未完成前執行，缺少 cache 而失敗，完成 prerequisite 後重新跑 9/9 PASS。這些未通過的嘗試不算正式 PASS。

## VERIFY — public site PASS

```sh
gh workflow run pages.yml --ref dic2-07-custom-csv
DASHBOARD_URL=https://wupojung.github.io/AIoT-DIC2-MultipleLR/ NODE_PATH=/tmp/dic2-browser/node_modules node tests/custom_browser.cjs
git diff origin/main HEAD --check
git diff origin/main HEAD -- docs/reports/50_startups docs/reports/feature_selection docs/reports/boston_housing docs/adr web/data .github requirements.txt constraints.txt
```

- [Pages deployment success](https://github.com/wupojung/AIoT-DIC2-MultipleLR/actions/runs/38928694867)，Web commit **`f19dc0111c950cec140d2998adfe44d79a9e16d6`**。
- 預先核對公開 HTML／JS／CSS／3 custom modules／vendor／兩個原 dataset JSON 共 9 個資產，HTTP 200、逐位元組一致：[deployed-assets.json](deployed-assets.json)。
- 正式公開網站再次載入公開 50 Startups URL、上傳 numeric CSV，重新執行新模型；完整 [browser-verification.json](browser-verification.json) 記錄 browser／timestamp、7 類 E2E checks、兩次新模型指標、來源數據誤差及預期 CORS 訊息。
- 50 Startups OLS RMSE **9055.957323498**、R² **0.898726641432**；numeric OLS **5.983776090 / 0.998557064958**。最大 prediction abs 差分別 **2.44e-7 / 3.41e-13**；在預先設定 tolerance 內。
- 正式 Screenshot 是公開網站真實 Chrome 的 1920×1080 viewport full-page captures；見 [報告](REPORT.md)。沒有 AI image／mockup。沒有假 FS 截圖。
- 兩內建資料集及所有原始實驗、已接受 ADR／protocol、依賴、Web dataset snapshots、workflow 保持不變；whitespace clean。

僅為不合併的展示，將本分支加入既有 `github-pages` environment 精確 allowlist，再手動 dispatch 原 workflow；保留 main 規則，不改 CI/CD。後續 main 正常部署可能替換 preview。

## 明確未執行／限制

不測完整五尺寸、跨平台或 coverage；不實作 Custom Pearson/F-Test/RFE/SFS/LassoCV、k 曲線、CV/nested CV、group/time/spatial split。輸入限制與拒絕政策見 [操作契約](../../CUSTOM_CSV.md)。
沒有 Vercel、Flask、API、帳號／資料庫；不讓私有 CSV 進入 repo／本站伺服器。ADR-0002 保持 Proposed，PR #12 不 Merge；本 PR 也不自動 Merge 或關閉 Issue #7。
