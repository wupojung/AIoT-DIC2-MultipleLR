# DIC2-05 — Boston 啟動審查與最小重構提案

狀態：**等待 owner 確認來源使用範圍、B 政策與 Boston 評估設定**。
此文件不是已接受 ADR，不修改任何 ADR。未載入 Boston 進行分析／訓練，
沒有 Boston metrics 或圖表，不能標記整項 Issue PASS。

## 已確認的專案狀態

- 最新 main：`2eb9074`，PR #15 已於 2026-10-16 合併，Issue #4 已關閉。
- 工作分支：dic2-05-boston-workflow。Issue #5 仍開啟。
- 已閱讀 AGENTS、README、CRISP-DM、EVALUATION_PROTOCOL、WORKFLOW_REUSE、
  ARCHITECTURE 與 Accepted ADR-0001；盤點原 Baseline、Feature Selection 與 verifier/tests。
- 既有實驗與已接受協定／ADR 均保留。不把 owner 後續指示當成教授已確認資料倫理政策。

## 來源查證（metadata，不是本地實測結果）

建議固定 scikit-learn **1.1.3 的歷史 CSV 副本**，只讀資料檔與來源說明，
不安裝舊 sklearn，也不呼叫 `load_boston()`。

| 項目 | 可追溯證據／目前狀態 |
| --- | --- |
| Revision | `ffc0f66676b4835eb1bdd3f3ecab025e9c1be9fe`（1.1.3 tag 對應 commit，已查 GitHub API） |
| CSV candidate | [sklearn/datasets/data/boston_house_prices.csv](https://github.com/scikit-learn/scikit-learn/blob/ffc0f66676b4835eb1bdd3f3ecab025e9c1be9fe/sklearn/datasets/data/boston_house_prices.csv) |
| Source metadata | Git blob `61193a5d646cc190ec2b10b87a975c234bfe03eb`、34742 bytes；SHA-256 待核准後取得檔案計算（Git blob 不是 SHA-256） |
| Expected schema | 506 rows、13 原始 predictors、MEDV；由來源文件記載，尚未本地載入驗證 |
| Variable definitions | [固定版本 schema 說明](https://github.com/scikit-learn/scikit-learn/blob/ffc0f66676b4835eb1bdd3f3ecab025e9c1be9fe/sklearn/datasets/descr/boston_house_prices.rst) |
| Provenance | 說明指向 StatLib／舊 UCI；[StatLib 原始頁](https://lib.stat.cmu.edu/datasets/boston) 可讀，已查閱欄位與文獻 header |
| License evidence | [固定版本 COPYING](https://github.com/scikit-learn/scikit-learn/blob/ffc0f66676b4835eb1bdd3f3ecab025e9c1be9fe/COPYING) 是 repository 的 BSD-3-Clause notice；不能直接聲稱原始 dataset 專屬權利已查明 |
| Permitted-use evidence | [Toronto Delve 說明](https://www.cs.toronto.edu/~delve/data/boston/bostonDetail.html) 列 Assessment 用途；不將此擴張為任意再散布授權 |

原始資料、鏡像、sklearn 修正紀錄與 BostonHousing2/cmedv 不可混稱完全相同版本。
[舊 loader 文件](https://scikit-learn.org/1.1/modules/generated/sklearn.datasets.load_boston.html)
記有早期個別資料點修正，故本提案明確稱「版本固定的歷史副本」，不宣稱與最早 StatLib
逐位元組相同。若獲准，manifest 記錄 revision、URL、Git blob、SHA-256、取得時間、
解析方式、完整 schema、單位、權利限制；cache 及 raw data 不提交。

### 欄位定義與建議角色

以下依上述來源說明整理；欄名、型別、缺值、範圍與實際 row count 仍需載入後驗證。

| 欄位 | 定義（簡述） | 建議角色 |
| --- | --- | --- |
| CRIM | 地區每人犯罪率 | 數值 predictor |
| ZN | 大面積住宅用地比例 | 數值 predictor |
| INDUS | 非零售商業用地比例 | 數值 predictor |
| CHAS | 是否鄰 Charles River 的指示值 | 保持 0/1 數值；驗證二元值 |
| NOX | 氮氧化物濃度 | 數值 predictor |
| RM | 每住宅平均房間數 | 數值 predictor |
| AGE | 1940 年前建屋所占比例 | 數值 predictor |
| DIS | 至就業中心的加權距離 | 數值 predictor |
| RAD | 放射公路可及性指數 | 本期沿原線性基準作數值；揭露不是天然等距的保證 |
| TAX | 每萬美元房產的稅率 | 數值 predictor |
| PTRATIO | 學生／教師比例 | 數值 predictor |
| B | 以地區黑人比例構造的非可逆變數 | 建議僅原始 schema 稽核保留，排除建模 |
| LSTAT | 原始資料所稱社經低地位人口比例 | 數值 predictor，但必須揭露階級／代理偏誤限制 |
| MEDV | 自住房屋價值中位數，歷史千美元單位 | Target；不可進入 X |

## 等待確認的決策

### A. B 欄位／倫理

**建議**：原始 13 predictors 完整驗 schema；主分析排除 B，因此模型 p=12，
k=1–12。所有五方法與 Baseline 都用相同允許欄位，不另跑含 B 的敏感度分析，
除非 owner 明確要求。排除 B 不代表移除其他代理變數或已達公平性。

[sklearn 歷史警告](https://scikit-learn.org/1.1/modules/generated/sklearn.datasets.load_boston.html)
說明 B 的種族構造與研究假設問題，並不鼓勵一般用途。本期僅限歷史方法／倫理教學，
不作現實估價、群體差異合理化或因果推論。需要 owner 確認，不能自行當作教師核准。

### B. Split、CV、alpha 與 holdout

**建議**：保留 seed=42、80/20、外五折比較、內三折選模、selector-local 三折。
Boston 自己重新產生 IDs／folds，不重用 Startups 的索引。所有 scaler、補值、選擇器
和 Lasso alpha 調整只在各自 training folds。預期 404 train / 102 test，尚未實測。

原始 13 欄沒有可信任的 census-tract ID、座標或地理群組。Toronto 說明也指出原始列
順序不明；不能把 row index 或 RAD 當成已驗證的空間群組。隨機切分僅是歷史樣本內
的教學 benchmark，不證明新地區／時期外推能力。若要求空間泛化，先補可靠群組來源
再另提 split protocol，不能默默換資料版本或按分數選切分。

**需一併確認的 Boston 尺度設定**：MEDV 是千美元，不能直接把 Startups 的 alpha
範圍 1–100000 當成通用尺度。建議 Boston 固定 `np.logspace(-4, 2, 21)`，
在建模前記錄，使用相同多 alpha LassoCV／fold-block 程序和 OLS 最終估計器。
Startups 的原 alpha grid 與結果完全不改；不是看 Boston 分數後換 grid。

先完成 train-only 五方法／k 曲線與 nested CV，凍結最後候選，再同次評估預先指定的
All Features LinearRegression、Dummy mean 與最終候選。Baseline 是預定對照，不依
holdout 選方法／k；不逐 k 掃 test、不重跑 seed 找高分。三種指標層級分表。
若 owner 希望本期完全不開 holdout，也可先只交 train/nested 證據，須明示尚無 holdout。

### C. 來源與使用範圍

兩種可選範圍：

1. 接受固定歷史副本供本地教學，保存 notice 與原始文獻，明確記錄資料專屬授權
   尚未獨立確證；不提交／再散布 raw data，不將 owner 同意表述成教師／權利人授權。
2. 先補齊資料專屬授權／教師提供來源，再取得檔案與建模。

在確認 A／B／C 前不載入 Boston 作實驗；也不將此提案寫成 Accepted ADR。

## 最小必要重構（共通核心已啟動，Boston 尚未實作）

目前固定值主要在 startups_baseline.py 的 FEATURES/TARGET/50-row 驗證、State
preprocessing，以及 feature_selection.py 的 k=1–5、三個 State levels、40-row split、
輸出目錄。兩個 verifier 也固定了樣本數、context 數、6240 predictions／600 subsets。
直接複製整份程式會把這些假設帶進 Boston，不能算 workflow reuse。

建議僅一個共通 module 和少量 dataset settings；不建立 plugin／registry framework：

1. **Dataset settings**：dataclass 或明確 dict，包含 dataset_id、target、數值／類別欄、
   expected schema、排除欄、單位、alpha grid。split/CV 預設共用，資料來源／解析器各自保留。
2. **共享運算**：將 metrics、建立 preprocessing、split／fold、五方法選擇與 nested
   計算、JSON/CSV／圖表輸出抽成一般函式。k 上限由實際允許的 encoded columns 決定；
   不把 Startups 的 State 特殊檢查放進共通核心。
3. **相容入口**：保留現有 Startups CLI 及預設行為；用其 config 呼叫共通函式。
   舊 verifier/tests、既有 report snapshots 與數值全部保留。Boston 新入口僅負責
   固定來源解析、專屬驗證／倫理排除、呼叫同一工作流程與千美元報告。
4. **驗證／報告**：共用從 predictions 重算指標與檢查 fit IDs 的邏輯；原驗證入口維持
   既有嚴格數量／欄位檢查。Boston verifier 依設定驗證，避免把舊固定數量改成寬鬆通過。
5. **完全隔離**：輸出 `outputs/boston_housing/<run-id>/`，review 快照另開目錄；
   不重用模型、前處理物件、索引、排名或指標。新 run-id 仍拒絕覆寫。

## 核准後的品質關卡

- BUILD：乾淨 clone 安裝原有相依；原則上不增加套件。
- RUN：核准來源取得與 hash/schema 檢查；實際 Baseline／五方法執行。
- TEST：原 21 tests 全通過；新增 Boston raw-13/model-12、B 排除、fold isolation、
  holdout mutation、預測重算、實際 selectors、動態 k、各資料集輸出隔離與重現測試。
- VERIFY：Startups 新舊 predictions/metrics/圖表一致；Boston 的 JSON/CSV／曲線一致，
  明確分開 training CV、nested 與凍結後一次 holdout；檢查 accepted ADR／舊實驗未變。
- PASS：只對實際跑過的項目報結果，PR 附繁中 CRISP-DM 報告、圖表、未決限制。
  不 Merge、不 close Issue #5；完成後等待人工 review。

## 本次已執行檢查（僅啟動階段）

2026-10-16，以既有 Python 3.14.2 驗證環境執行：
```sh
/tmp/dic2-03-venv/bin/python -m unittest discover -s tests -v
git diff --check
git diff origin/main HEAD -- docs/adr python/src tests docs/reports
```
原有 **21 tests PASS**（8.351 秒），相對文件連結檢查包含本提案；whitespace check
通過。既有程式／實驗／ADR 無修改。只新增此提案文件，不代表 Boston 的 BUILD/RUN/
TEST/VERIFY/PASS 已完成。尚未執行 Boston 載入、schema 實測、EDA、訓練、選擇或評估。

## 進度更新：可獨立執行的共通重構

不依賴 Boston 未決政策，已開始實作：

- regression_workflow.py：DatasetConfig、來源 schema 驗證、排除欄位防護、
  Pipeline 建構、原樣 metrics／JSON、seeded split/folds。
- Startups Baseline 保留既有入口、State block 名稱與規則，改為呼叫共通函式。
- 原五方法與 nested engine 接收 config／alpha 參數，k 由實際編碼維度產生；
  Startups config 仍嚴格要求五欄且保持原 alpha grid。
- 圖表可設定特徵軸與單位；原 Startups 預設文字／樣式保持相同。
- 另以純合成 60-row、12-numeric-feature 資料測試：沒有 State 假設、排除／target
  不進入 predictors、不同樣本數的五折／三折、全部五方法與動態 k=1–12。

這不是 Boston 資料測試。來源 loader／manifest、B 政策落實、Boston baseline／holdout、
專屬 verifier、CRISP-DM 報告和實測圖表仍待政策確認後完成；不能把 synthetic 結果
當作 Boston 結果。原實驗快照、原 verifier/tests、已接受協定與 ADR 未修改。

## 最新共通階段驗證（不代表 Boston PASS）

已於獨立 clone `/tmp/dic2-05-shared-check` 建立 fresh venv，依原 requirements/
constraints 安裝且 pip check 通過。使用原已驗證的 Startups cache，程式仍重新核對
來源 SHA-256，不聲稱本輪做過新的 Boston 下載。

- BUILD：共通程式 fresh venv 安裝成功，未新增相依。
- RUN：環境檢查、Startups Baseline 與五方法實驗實際執行成功。
- TEST：**29 tests PASS**（包含原 21 項），另外 8 項驗 config、排除欄、無 State、
  12 特徵／動態 k、另一個樣本數、nested engine、自訂 alpha 與圖表單位／軸。
- VERIFY：兩個既有 verifier 通過，含 24 組多 alpha replay；Web 10 scenarios 通過，
  console/JS/network errors/warnings 為 0。Baseline 20 個 runtime artifacts、
  Feature Selection 13 個 artifacts 與重構前 byte-identical（來源下載時間紀錄未納入）。
- 舊報告、舊測試、接受的 ADR／評估協定、Web、部署與相依檔案未修改。

實際命令（在 clone root，cache 為先前已驗證的絕對路徑）：
```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python python/src/environment_check.py
.venv/bin/python python/src/startups_baseline.py --cache-dir /path/to/verified/50_startups --run-id shared-check
.venv/bin/python python/src/feature_selection.py --cache-dir /path/to/verified/50_startups --run-id shared-check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python python/src/verify_startups_run.py outputs/50_startups/shared-check --source /path/to/verified/50_startups/50_Startups.csv
.venv/bin/python python/src/verify_feature_selection.py outputs/50_startups/feature_selection/shared-check --source /path/to/verified/50_startups/50_Startups.csv --replay-lasso
python3 -m http.server 8000 --directory web
# Another terminal:
NODE_PATH=/tmp/dic2-browser/node_modules node tests/browser_smoke.cjs
```

以上只通過**共通重構／Startups 相容性**關卡。Boston 的來源 schema 實測、Baseline、
Feature Selection、holdout、JSON/CSV、圖表與繁中 CRISP-DM 報告仍未執行，
不得對整個 Issue #5 標 PASS；等待來源／B／評估設定的明確確認。
