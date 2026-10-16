# AIoT DIC-2 — Multiple Linear Regression

> NCHU AIoT 2026 · Doing in Class 2 · **50 Startups baseline · Review pending**

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

目前提供 50 Startups Python baseline、環境檢查與靜態 Web 介面；baseline 尚待 PR 人工審查，Web 尚未連接分析資料。**自訂 CSV 應採純前端 JS 還是後端 Python 尚未決議**，由後續 ADR 評估，勿將規劃描述為已完成。

## Development and issue tracking

**Implementation agent: Codex.** 從 [Issue #1 — Initialization](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues/1) 開始，採用小步驟 **BUILD → RUN → TEST → VERIFY → PASS**。每個階段提供實際驗證結果，未驗證不得標記 PASS。透過獨立分支及 PR 交付；**未經人工確認不得自行 Merge**。

- [GitHub Issues](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues)
- [Teacher's reference repository](https://github.com/huanchen1107/AIoT-DIC2-MultipleLR)（唯讀參考）
- [Previous experiment repository](https://github.com/wupojung/DIC-2_test)（僅參考，勿直接複製未驗證的分析結論）
- Learning Journal / HackMD：待補

## Initial setup

需要 Python 3.12+（實測 3.14.2）與瀏覽器。分析相依及固定版本見 requirements.txt / constraints.txt；標準函式庫環境檢查與 ML baseline 為不同命令。

在 Codex 選擇本地專案資料夾，或先 clone 再開啟：
```sh
git clone https://github.com/wupojung/AIoT-DIC2-MultipleLR.git
cd AIoT-DIC2-MultipleLR
git remote -v
```
確認 origin 的 fetch/push 都是上述 URL。開工前讀取 [AGENTS.md](AGENTS.md)、本 README、目標 Issue 與架構文件；在獨立 feature branch 工作。

macOS 快速開始：
```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python python/src/environment_check.py
python python/src/startups_baseline.py --run-id baseline-v1
python -m unittest discover -s tests -v
python -m http.server 8000 --directory web
```
瀏覽 http://localhost:8000；也可直接開啟 web/index.html。Windows PowerShell 的完整指令見 [Python 指南](python/README.md)。

- [50 Startups 實測報告與圖表](docs/reports/50_startups/report.md)
- [Web 操作與目前限制](web/README.md)
- [資料來源與倫理要求](data/README.md)
- [作業需求、證據與 Issue #3 開工清單](docs/ASSIGNMENT_REQUIREMENTS.md)
- [兩題問題定義與資料限制](docs/PROBLEM_DEFINITIONS.md)
- [評估協定提案](docs/EVALUATION_PROTOCOL.md)
- [工作流程重用設計](docs/WORKFLOW_REUSE.md)
- [CRISP-DM 六階段驗收](docs/CRISP_DM.md)
- [目前／規劃架構](docs/ARCHITECTURE.md)
- [中英術語表](docs/GLOSSARY.md)
- [ADR 流程](docs/adr/README.md) 與 [ADR-0001 基礎架構提案](docs/adr/ADR-0001-project-foundation.md)

Issue #2／PR #11 已由 owner 接受；依後續指示執行 Issue #3。教師未決問題 Q1–Q5、來源原始權利及幣別／期間仍未確認，不視為已獲教授核准。基準執行與限制見 [Python 指南](python/README.md)。

Web 僅頁籤切換可操作；資料集選單為停用的預留介面。Web 尚無 API、資料整合、模型執行、CSV 匯入或部署。遵循 BUILD → RUN → TEST → VERIFY → PASS，實際指令與結果記錄於 PR，人工審查前不關閉 Issue。

## Research integrity

特徵選擇、前處理與參數調整應在訓練資料內進行；測試集保留供最後評估。不同方法比較時必須使用一致的資料切分與評估方式。圖表與數據必須來自實際執行，不可寫死績效或最佳特徵數。
