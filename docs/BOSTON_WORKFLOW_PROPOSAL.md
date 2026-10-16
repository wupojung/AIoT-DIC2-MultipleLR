# Boston Housing — 資料版本、政策與最小重用實作

依 [PR #17 owner 決策](https://github.com/wupojung/AIoT-DIC2-MultipleLR/pull/17#issuecomment-6218126601) 實作 MVP。
這是暫行專案決策，不是教師核准、原始資料新授權或 Accepted ADR；不修改既有 ADR。
PR #15 已合併、Issue #4 已完成。技術實測見 [Boston 報告](reports/boston_housing/REPORT.md) 與 [驗證紀錄](reports/boston_housing/VERIFICATION.md)。

## 資料來源與實測

- 固定 scikit-learn 1.1.3 commit `ffc0f66676b4835eb1bdd3f3ecab025e9c1be9fe` 的 [CSV 歷史副本](https://github.com/scikit-learn/scikit-learn/blob/ffc0f66676b4835eb1bdd3f3ecab025e9c1be9fe/sklearn/datasets/data/boston_house_prices.csv)。不安裝舊 sklearn、不呼叫已移除 loader。
- 實際下載 34742 bytes；Git blob `61193a5d646cc190ec2b10b87a975c234bfe03eb`；SHA256 `d98212636026544fc9b9c0f372e5f819872e6fa6fa757ab025efdda22180f2d6`。每次從 cache 或網路取得均核對三者。
- 第一列為 506/13 metadata；第二列為 header。實際解析 506×14，13 原始 predictors + MEDV。完整欄序、數值型別、有限值、CHAS 二元、重複資料與列數均驗證後才切分。
- [固定版本欄位文件](https://github.com/scikit-learn/scikit-learn/blob/ffc0f66676b4835eb1bdd3f3ecab025e9c1be9fe/sklearn/datasets/descr/boston_house_prices.rst) 指向 StatLib／舊 UCI，原始文獻 Harrison & Rubinfeld (1978)。版本固定副本不等於最早 StatLib 或 BostonHousing2/cmedv；舊 sklearn 曾修正個別資料點。
- [Toronto Delve](https://www.cs.toronto.edu/~delve/data/boston/bostonDetail.html) 提供歷史背景、Assessment 用途與 MEDV 可能截斷說明。
- [repository COPYING](https://github.com/scikit-learn/scikit-learn/blob/ffc0f66676b4835eb1bdd3f3ecab025e9c1be9fe/COPYING) 的 BSD-3-Clause 不足以證明原始 dataset 專屬授權。原始權利／provenance 仍是明示限制；依 owner 決策僅做本地教學評估，不再散布 raw CSV，cache 被 gitignore 排除。未宣稱已取得教師或權利人批准。

以下是上述固定版本定義的繁中摘要：

| 欄位 | 定義／處理 |
| --- | --- |
| CRIM | 地區人均犯罪率 |
| ZN | 大面積住宅用地比例（>25,000 sq.ft.） |
| INDUS | 非零售商業用地比例 |
| CHAS | 是否鄰 Charles River，二元 0/1，保留數值 |
| NOX | 氮氧化物濃度，parts per 10 million |
| RM | 每住宅平均房間數 |
| AGE | 1940 年前自住住宅比例 |
| DIS | 至五個就業中心的加權距離 |
| RAD | 放射狀公路可及性索引，保留數值，不假裝空間群組 ID |
| TAX | 每 $10,000 的全額房產稅率 |
| PTRATIO | 地區師生比 |
| B | 1000(Bk−0.63)²，Bk 是歷史地區黑人比例；原始 schema 保留，模型排除 |
| LSTAT | 來源稱 lower status population 百分比，具社經偏誤與歷史價值判斷 |
| MEDV | 自住住宅價值中位數，歷史千美元，Target |

B 排除後 12 個候選，無 State one-hot；不代表消除種族／社經代理偏誤。不適合現代或有實際影響的住房決策。

## 評估決策與重用

seed=42、80/20（404/102）、outer 5 / inner 3；SFS/Lasso 的局部 CV 也為 3 folds。
來源未提供可驗證地理分組，沿用隨機歷史樣本協定，不宣稱 spatial generalization。
Boston alpha 預設 21 點 logspace(-4,2)，在首輪建模前固定，未從 test 選擇。
使用 training CV 選方法/k，保存凍結選擇後，對預先宣告 all-feature LR、selected LR、mean dummy 各評估一次 holdout。

最小重構是 `regression_workflow.DatasetConfig`、schema／Pipeline／split/folds／metrics／JSON 共用函式，
以及參數化既有 `feature_selection.training_experiment` 與繪圖。Boston adapter 只負責來源／政策、資料集設定與產物報告，
全特徵 baseline CV 直接重用同次 selector engine 的 All Features 結果，沒有複製整套 baseline runner。
Startups CLI、五欄 State 規則、原 alpha、原協定及既有 snapshots 保留；不重用任何訓練模型、切分索引、排名或分數。
不建立 plugin/framework，不做其他 Issue。精簡測試與驗證範圍依 owner 決策；完整 QA 延至 Issue #8。
