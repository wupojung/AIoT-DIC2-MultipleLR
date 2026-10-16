# 評估協定 / Evaluation protocol

狀態：**Proposed**，待 owner 審查；不含結果。適用兩題的共通預設，
Issue #3 僅先做 50 Startups baseline。任何變更先記錄理由與新協定版本，
不能看 holdout 分數後調整方法再宣稱同一次獨立評估。

## E1 — Split and CV / 切分與驗證

- 建議固定 `random_state=42`，80% train / 20% test，shuffle=True；不對連續 y
  直接作分類 stratification。這符合 Issue #3 的 80/20 要求，seed 與 folds 是本案提案。
- 先完成來源／schema、資料獨立性及重複／群組稽核，再凍結資料版本與 row IDs。
  同公司、重複觀測、時間或地理群組不得跨切分；若不滿足獨立假設，先重審
  group/time/spatial split，不能直接套用隨機規則。Boston 的外推情境尤其要說明。
- 凍結 test IDs；所有資料導向 EDA、相關性排名、補值、縮放、編碼、特徵選擇及調參
  僅用 train。可在全資料查結構／完整性，但不能先看全資料的 y 關係再選模型。
- 訓練內預設 `KFold(n_splits=5, shuffle=True, random_state=42)`；保存每折 row IDs。
  確認每個驗證折至少兩筆且 target 有變異；否則暫停審查 folds，不把未定義 R² 填成成功值。
- 若新增特徵選擇／超參數，用外層同一組 5 folds 評估完整選擇程序，外層 training
  內再用 inner 3-fold（shuffle=True、seed 42）選 k／alpha／候選；不得使用外層
  validation 選候選再把該分數當無偏評估。記錄全部搜尋範圍與選擇規則。
- 最終候選用全部 train 的內部 CV 決定後凍結，重擬合 train，才對 test 評估一次。
  報告預先宣告的 Dummy baseline 與最終 LinearRegression 同次測試；不得再按 test 挑 k。

理由與技術參考：[sklearn CV](https://scikit-learn.org/stable/modules/cross_validation.html)、
[避免資料洩漏](https://scikit-learn.org/stable/common_pitfalls.html)。

## E2 — Preprocessing and baseline / 前處理與基準

提案使用 sklearn Pipeline／ColumnTransformer，數值欄若有缺值以 training median
補值；類別若有缺值以 training most-frequent 補值，再 OneHotEncoder。
State 建議 drop-first、handle_unknown='ignore'，記錄基準類別及未知值計數；未知值
可能與基準同為全零，必須揭露。全空欄、無法解析的數值與缺失 y 先停止並提出處理決策，
不得靜默刪除。重複資料策略在切分前固定且記錄。

Issue #3 擬合全核准特徵的 `LinearRegression(fit_intercept=True)` 作主要 baseline；
另用 `DummyRegressor(strategy='mean')` 作無特徵參考。對外呈現變換後欄名與係數，
不把相關或係數方向當成因果。Lasso 需要的尺度處理也只能在 training fold 擬合。

## E3 — Feature selection fairness / 公平比較

未來研究 Pearson（依 abs(r) 排序）、F-test（f_regression）、RFE、前向 SFS、
LassoCV，全部選完後交給**同一個 LinearRegression**，相同外層 splits、
指標、候選 k 預算與前處理規則。Lasso 在此是 selector，不拿 Lasso 的預測值
當成這張比較表的最終 estimator。可另做估計器比較，但需分表。

比較單位提議採編碼後欄位，須同時報原始特徵群組映射與折內有效欄數；
若要以整個 State 群組為單位則另立實驗，不混算 k。Pearson/F-test 不適用
無變異欄；不可任意把 State 變成有序整數。所有排名與 selector fit 都在訓練折內。

SFS 的內層 scoring 也不可沿用先在全部外層 training 擬合的 encoder／scaler；
須讓 preprocessing 隨 inner folds 重擬合。LassoCV 的內部選 alpha 同樣不能先對
完整外層 training 縮放後就宣稱 inner-CV 無洩漏：以 inner-CV 評估完整前處理＋
Lasso 候選（例如顯式 alpha search），或另提出可證明 fold-local 的設計供審查。
這個實作細節尚未決定，不在 Issue #3 寫完整選擇器。

預先指定 training-CV mean RMSE 為選擇準則，越小越好；完全同分時選較少特徵，
再以固定方法／欄名順序解決同分。不同外層折可選到不同特徵，須記錄穩定性。
教師範例的方法組合不等於此五種方法的強制清單。
參考：[sklearn feature selection](https://scikit-learn.org/stable/modules/feature_selection.html)。

## E4 — Metrics and plots / 指標與圖像

令 e_i = y_i − ŷ_i（residual），n 是評估 partition 樣本數：

| Metric | 定義 | 單位／解讀 |
| --- | --- | --- |
| MAE | sum(abs(e_i)) / n | 與 y 同單位；越低越好 |
| MSE | sum(e_i²) / n | y 單位的平方；越低越好 |
| RMSE | sqrt(MSE) | 與 y 同單位；越低越好 |
| R² | 1 − sum(e_i²) / sum((y_i − mean(y))²) | 無單位；可為負；分母使用該評估集均值 |

若 n < 2 或 y 常數，R² 應記 undefined 與原因；不得利用 API 的有限值替代掩蓋問題。
MAE/MSE/RMSE 必須由同一組 y／ŷ 重算。sklearn 的負誤差 scorer 轉回正值再報告。
每折計算後報 mean/std、折樣本數；mean fold RMSE 不等於 sqrt(mean fold MSE)，
若報 pooled out-of-fold 指標要分別命名。Train CV、train fitted、holdout 分表，
小樣本的不確定性必須揭露；沒有目前可宣稱的「最佳 k」或最低 R² 門檻。

圖像提案：actual-vs-predicted（相同單位與 y=x 線）、residual-vs-predicted
（零線）、殘差分布；訓練資料的 EDA 相關圖另標 partition。
CV 特徵數曲線不能以 holdout 掃 k。Profit 貨幣／期間待確認，Boston MEDV 歷史千美元
需經來源核對；未確認單位標明 unknown，不擅貼美元符號。
指標技術參考：[sklearn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html)。

## E5 — Evidence and Issue #3 tests / 證據與驗收提案

每次 run 在 `outputs/<dataset_id>/<run_id>/` 保存 config、來源 hash、環境版本、
row IDs／fold IDs、欄位轉換、每折指標、holdout y／ŷ／residual、圖與限制說明。
這是未來產物規格，不是目前可用檔案或 API；outputs 仍預設忽略。

I3 至少測試：train/test disjoint、fold subset／disjoint、encoder／補值只看 training、
未知 State 可預測並揭露、缺失 target／錯誤 schema 有明確失敗、固定資料／seed 可重現、
由保存 predictions 重算四指標一致、產物落於 dataset 專屬目錄。
檢查目標洩漏與重複跨切分；以實際輸出生成圖表。任何未量測或失敗不得記 PASS。
