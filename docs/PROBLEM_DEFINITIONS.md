# 問題定義 / Problem definitions

狀態：50 Startups baseline 已實作並作本地技術驗證（PR 待審），
原先的預期 schema 保留於下表；實測與限制見 [review report](reports/50_startups/report.md)。
Boston 仍為 Planned，未取得或分析資料。
需求來源與待教授確認事項見 [需求矩陣](ASSIGNMENT_REQUIREMENTS.md)。

## Problem 1 — 50 Startups / Profit prediction

目的：練習從企業支出與所在地預測連續的 Profit，解釋可重現流程與誤差。
這是觀察資料的預測練習，不證明增加支出會造成獲利增加。

| Item | 預期規格／驗證責任 |
| --- | --- |
| Sample | 每列一家公司；Issue #3 預期 50 筆，取得核准資料後才可宣稱實測數量 |
| Target y | Profit；不得混入 X；貨幣、期間與計量定義待來源驗證 |
| Raw features X | R&D Spend、Administration、Marketing Spend（數值）；State（類別）：四個原始 predictors |
| Candidate source | 教師 README 引用的 Avik-Jain repository 之 datasets/50_Startups.csv；不是本次已核准／取得的資料 |
| Provenance gate | 記錄來源 URL、固定 revision、license／使用限制、取得時間、SHA-256、schema 與 units；不可只記可變動 URL |
| Data checks | 欄名／型態、缺值、非有限值、重複列／企業、目標範圍、類別與樣本可獨立性；異常先記錄，不以 test 成績決定刪列 |

原始欄位數與 one-hot 後維度必須分開記錄。例如**若訓練折實際有三個 State 類別**，
使用 drop-first 會生成兩欄，加上三個數值欄得到五個模型輸入欄；這是條件例子，
不是本次資料量測。採用幾個 dummy、基準類別及未知類別策略必須記錄。
不能預先以全資料學到的類別清單擬合 encoder。

教師來源：[固定版本 README](https://github.com/huanchen1107/AIoT-DIC2-MultipleLR/blob/8b65e3bd9745e650ae7bea28f9562c059d5029ed/README.md)。
Issue #3 改用 manifest 固定的鏡像 revision，校驗後取得 CSV 並獨立執行；
沒有使用教師的結果當作本專案結果。

## Problem 2 — Boston Housing / MEDV prediction

目的：檢查第一題建立的 CRISP-DM 流程可否移轉至另一個問題，同時討論歷史資料限制。
歷史觀測單位是 Boston 地區 census tract 層級，不是當代個別房屋。
MEDV 指自住房屋價值中位數，歷史定義單位為千美元；候選版本仍需逐項驗證。

[sklearn 歷史 schema 說明](https://github.com/scikit-learn/scikit-learn/blob/1.1.3/sklearn/datasets/descr/boston_house_prices.rst)
列出 13 個 predictors：CRIM、ZN、INDUS、CHAS、NOX、RM、AGE、
DIS、RAD、TAX、PTRATIO、B、LSTAT；含 MEDV 共 14 欄不代表有 14 個特徵。
數量、樣本與變數編碼是來源的預期描述，本專案尚未對任何檔案實測。

資料含不恰當的種族構造變數 B，變數定義與資料蒐集背景有倫理問題。
不能把 B 或 LSTAT 當作中性的個人屬性，也不能以移除 B 宣稱已消除偏誤。
MEDV 的上限截斷、年代、地理範圍、聚合觀測與潛在空間相關均需檢查並寫入限制。
不得將結果作當前估價、因果、群體差異合理化或決策建議。

[sklearn 歷史資料說明](https://scikit-learn.org/1.1/modules/generated/sklearn.datasets.load_boston.html)
解釋變數與倫理背景；[1.2.0 官方移除訊息](https://github.com/scikit-learn/scikit-learn/blob/1.2.0/sklearn/datasets/__init__.py#L100-L147)
記錄 `load_boston` 已移除。本專案不得呼叫它、降版繞過移除或直接下載未審查鏡像。
後續由教師確認允許的歷史資料版本、license、來源、變數處置與教學限制，再建立 manifest。
若無法核准，提出替代資料問題交教師決策，不能自行更換指定題目。

## 共同輸出與邊界 / Shared deliverables

每題：問題／target／units、來源與 schema、train-only EDA、切分／前處理證據、
CV 與一次 holdout 評估、圖像解釋、限制與六階段 gate 紀錄。
[評估協定](EVALUATION_PROTOCOL.md) 區分通用預設與需因資料結構重審的條件；
Boston 若有空間群組，隨機切分不保證可評估對新地區的外推。
兩題各自比較模型與 baseline，不跨不同 y／units 直接比較 RMSE 高低。
