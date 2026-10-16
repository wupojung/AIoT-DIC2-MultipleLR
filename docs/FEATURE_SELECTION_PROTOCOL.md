# Issue #4 — Feature Selection 實驗協定

版本 DIC2-04-v1。沿用 [已接受評估規劃](EVALUATION_PROTOCOL.md) 的
seed 42、80/20、相同五個 training folds、同資料 manifest、缺值與 State 規則。
本文件補足 Issue #4 的具體實作，沒有修改 ADR 或 Issue #3 Baseline。
研究結果不得反過來改 seed、k grid、alpha grid 或比較準則。

## 評估層級

1. 固定方法／k 比較：40 筆 train 內相同 shuffled 5-fold；每個外折 training
   重新擬合前處理與選擇器，再以 LinearRegression 預測外折 validation。
   k=1–5，五方法共 25 候選，加 All Features(k=5)。曲線顯示 mean ± fold std(ddof=0)，
   不把從曲線挑出的最低點當作無偏的選模成績。
2. 巢狀選模：每個外折 training 內，先以相同 shuffled 3-fold 比較所有 26 候選，
   再將勝者的外折分數作為整個選模程序的評估。內折中的 SFS/LassoCV 仍須再做
   selector-local 3-fold，確保前處理與選擇都在其適當 training 範圍。
3. 最終凍結方案：以全部 40 train 的 3-fold 選方法／k，重擬合 train 上的選擇器，
   記錄實際特徵，不在這次執行 holdout。相同分數優先較小 k，再方法字典序。
   Pearson/F-Test 等價時可能以字典序決定方法，不代表統計上 F-Test 比較好。

深層 training 最少約 14 筆，小樣本不穩定是限制。3-fold 是可行的預定內層規模，
不是看結果後挑出來的 folds。所有 fold IDs、每折每候選預測及選擇路徑均輸出。
Issue #3 的 holdout 指標已公開，所以不能將它稱作未曾曝光的新獨立 test。
本期 **holdout_evaluations=0**；未來確認方案須先由人審查，不另挑 seed 或再以 test 調參。

## 特徵單位與共同前處理

原始 X 是四欄；training State 有 California／Florida／New York 三類，drop-first
以 California 作基準，模型欄位為：

| Encoded name | 原始群組 |
| --- | --- |
| numeric__R&D Spend | R&D Spend |
| numeric__Administration | Administration |
| numeric__Marketing Spend | Marketing Spend |
| state__State_Florida | State |
| state__State_New York | State |

本實驗將兩個 dummy 當成分開的選擇單位，k=5 是五個編碼後欄位，非五個原始變數。
群組 State 的選擇是另一種實驗，未混在本次比較內。每個 selector 的 training
必須實際有三個 State levels 才支援統一 k=1–5；否則明確失敗，不夾限 k 或造出第五欄。

中位數／眾數補值及 OneHotEncoder 每折重新 fit；unknown State 按原 Baseline 規則
全零。SFS 候選內折若缺少某已命名 dummy，僅補全零輸入欄並記錄 unavailable_candidates，
不從 validation 學類別。所有真正 fit 的 schema、基準類別、row IDs 和統計均有 audit。
本次固定資料的實際執行中沒有這種缺欄情況。

最終預測一律用未縮放的選定欄位 + LinearRegression(fit_intercept=True)，與 All Features
Baseline 相同。RFE 與 Lasso 排名需要比較係數時才以當地 training StandardScaler
標準化所有編碼欄；Pearson/F-test 與 SFS 最終 OLS 評分也不因此換成其他估計器。

## 五種真實選擇器

| 方法 | 實際運算與順序定義 |
| --- | --- |
| Pearson | sklearn r_regression 絕對值降序；零變異以有限零值處理 |
| F-Test | sklearn f_regression 分數降序；同樣使用 train y，非全資料檢定 |
| RFE | sklearn RFE(LinearRegression, n_features_to_select=1, step=1) 真正遞迴刪除；排名由 ranking_ 還原，輸出為反向淘汰順序，不冒充前向加入 |
| SFS | 自行實作真正 greedy forward：每一步對全部剩餘欄位做三折 OLS RMSE 比較，只加入勝者；保存所有候選／分數。沒有以固定排序代替 SFS |
| LassoCV | 真正多 alpha LassoCV + 最佳 alpha 的 local-training Lasso 重擬合；依標準化絕對係數降序，最終預測仍是 OLS |

Pearson、F-Test 及 Lasso 的精確同分依 encoded name 字典序。RFE 的係數同分沿用
sklearn 固定欄位順序；SFS 同分以新增欄名字典序決定。每個 k 是該方法當地排序的前 k。
Pearson 與單變量 F-test 在相同樣本下的排序可等價，因此相同曲線不表示複製假資料。

### LassoCV 如何避免內折前處理洩漏

不能先在全部 parent training fit scaler，再把結果交給一般 LassoCV 的多 alpha
內部 CV。這會讓內部 validation 參與縮放。本實作只用公開 API 的 iterable CV：

1. 對 selector-local 三個 folds，分別只用該 fold training fit imputer／encoder／scaler，
   轉換其 training 與 validation，形成各自獨立的資料 block。
2. 垂直堆疊三個 blocks；用明確 CV index pairs 使每次 path fit／validation **只存取
   自己 block**。同一原始 row 雖出現於其他 block，該 split 完全不讀其他 blocks。
   欄位數不足以全零補齊寬度；各折係數互不共享，padding 不構成跨折類別學習。
3. 使用預先固定 `np.logspace(0,5,21)` alpha grid（1 到 100000），避免全堆疊資料
   推導 alpha grid。LassoCV 真正計算全部 alpha 的每折 MSE，選 mean MSE 最小值；
   精確同分依降序 grid 先選較大 alpha。max_iter=100000、tol=1e-8、cyclic、單執行緒。
4. **丟棄** LassoCV 自動在混合 blocks 上的最終 refit 係數；只取 alpha_ 與 mse_path_。
   在真正 parent training 的前處理／尺度上，以該 alpha 重 fit Lasso 並產生排名。
   重擬合不再選 alpha。這是 LassoCV alpha 選擇後的必要一致尺度 refit，不是固定 alpha
   或單候選 CV 的替代品。獨立 verifier 以逐 alpha 的 Lasso 重算所有內折 MSE path。

對照官方 [LassoCV](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LassoCV.html)
的 iterable CV、alpha_ 與 mse_path_；內折顯式 fit 的驗證證據比只包一層 Pipeline 更重要。
零係數不能排序出實質重要性：為了相同 k 曲線，超過 active support 的欄位依字典序補入，
CSV 標示 zero_padded_features；不得宣稱它們是 Lasso 的非零選擇。

## 檔案、驗證與重現

```sh
python python/src/feature_selection.py --run-id fs-v1
python python/src/verify_feature_selection.py outputs/50_startups/feature_selection/fs-v1 --source data/50_startups/50_Startups.csv --replay-lasso
python -m unittest discover -s tests -v
```

沿用 [Python 安裝方式](../python/README.md)，不增加套件。run-id 必須全新，
輸出到獨立 feature_selection/ 子目錄，不覆寫 Baseline。
protocol.json 在計算前記錄規則；splits/provenance/environment 保留重現上下文。
results.json 含五折曲線、內層 tuning、nested summary、全部 24 selector contexts、
168 組 fit audit；predictions.csv 含 6240 筆 training-only 預測；selected_features.csv
含 600 筆 context/method/k 的完整欄名、順序、順序意義和零係數補入標示。
comparison.csv／plot_data.csv 對應兩圖；final_selection.csv 是最後三折選模表。
frozen_selection.json 保留決策與 protocol hash，沒有 test 指標。

Verifier 重新 fit OLS 驗每個候選的預測、獨立重算四指標、audit 統計／split、子集與
nested 選擇、JSON/CSV 一致性；從已驗 CSV 重畫兩圖並逐位元組比對。
--replay-lasso 額外對全部 24 組多 alpha path 做獨立 Lasso 重算，容許僅數值解法的微差。
自動測試還會更動全部 holdout X/y，要求選擇、曲線、audit 與圖片完全不變。
