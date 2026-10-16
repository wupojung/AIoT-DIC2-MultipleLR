# AIoT DIC-2 — Multiple Linear Regression

> NCHU AIoT 2026 · Doing in Class 2 · **Project initialization in progress**

本專案用 **Python / scikit-learn** 練習多元線性迴歸（Multiple Linear Regression），以 **CRISP-DM** 六階段引導分析，並逐步製作簡潔的 **Regression Analysis Dashboard**。重點是理解分析流程、正確評估模型，以及將流程重用到第二個問題，而非只追求最高分數。

## Assignment scope

- **Problem 1 — 50 Startups:** 預測 `Profit`，作為第一題的 CRISP-DM 練習。
- **Problem 2 — Boston Housing:** 預測 `MEDV`，驗證第二題能否套用已建立的 Skill / Workflow。這是具倫理限制的歷史教學資料集，需記錄來源及限制。
- 老師要求：完成兩個問題，最後選一個主題上傳。
- **Optional bonus:** 下拉選單切換兩個問題；輸入自訂 CSV Dataset URL 後重新分析（不是顯示預先計算的假結果）。

> 課堂上曾使用「Kaggle regression dataset with 14–39 features」作為搜尋提示詞；是否構成正式作業限制尚待確認。

## Learning workflow — CRISP-DM

| Phase | Focus |
| --- | --- |
| 1. Business Understanding | 定義問題、Target 與應用情境 |
| 2. Data Understanding | Dataset、EDA、欄位、統計與資料品質 |
| 3. Data Preparation | 缺失值、編碼、Train/Test Split、避免 Data Leakage |
| 4. Modeling | Scikit-learn LinearRegression；交叉驗證 |
| 5. Evaluation | MAE、MSE、RMSE、R²、殘差與 Feature Selection |
| 6. Deployment | 模型重用、報告與網頁展示 |

## Planned architecture

- **Python:** 可重現的資料分析與模型評估。
- **Web:** Overview / Feature Selection / Evaluation 三個頁籤，與 Dataset 下拉選單。
- **Docs:** CRISP-DM 學習文件、架構、ADR 決策紀錄及中英雙語術語表。
- **Workflow:** 從 50 Startups 提取可重用流程，再套用 Boston Housing。

目前尚未建立分析程式或正式 Web 成品。**自訂 CSV 應採純前端 JS 還是後端 Python 尚未決議**，由後續 ADR 評估，勿將規劃描述為已完成。

## Development and issue tracking

**Implementation agent: Codex.** 從 [Issue #1 — Initialization](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues/1) 開始，採用小步驟 **BUILD → RUN → TEST → VERIFY → PASS**。每個階段提供實際驗證結果，未驗證不得標記 PASS。透過獨立分支及 PR 交付；**未經人工確認不得自行 Merge**。

- [GitHub Issues](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues)
- [Teacher's reference repository](https://github.com/huanchen1107/AIoT-DIC2-MultipleLR)（唯讀參考）
- [Previous experiment repository](https://github.com/wupojung/DIC-2_test)（僅參考，勿直接複製未驗證的分析結論）
- Learning Journal / HackMD：待補

## Initial setup

此 Repo 的 Python 環境、Web 原型及完整安裝指令由 **Issue #1** 建立。待驗證後更新本章節；在此之前不宣稱有可執行的 Regression Pipeline。

## Research integrity

特徵選擇、前處理與參數調整應在訓練資料內進行；測試集保留供最後評估。不同方法比較時必須使用一致的資料切分與評估方式。圖表與數據必須來自實際執行，不可寫死績效或最佳特徵數。
