# AIoT DIC-2 — Multiple Linear Regression Lab

**NCHU AIoT 2026 · Doing in Class 2** · Python / scikit-learn · CRISP-DM

[![Pages deployment](https://github.com/wupojung/AIoT-DIC2-MultipleLR/actions/workflows/pages.yml/badge.svg)](https://github.com/wupojung/AIoT-DIC2-MultipleLR/actions/workflows/pages.yml)
[![GitHub license / source](https://img.shields.io/badge/Source-GitHub-181717?logo=github)](https://github.com/wupojung/AIoT-DIC2-MultipleLR)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](python/README.md)

> **Live Demo（靜態 UI 預覽）：** [開啟 GitHub Pages](https://wupojung.github.io/AIoT-DIC2-MultipleLR/) · [部署狀態](https://github.com/wupojung/AIoT-DIC2-MultipleLR/actions/workflows/pages.yml)  
> 首次使用請先查看 Actions 部署結果；此連結是預定 GitHub Pages 站址，**尚未在本次 README 修改中完成正式上線驗證**。目前只提供 Dashboard 介面預覽，**尚無 Web 端模型執行、資料集切換或自訂 CSV 分析**。

本專案使用 **Multiple Linear Regression（多元線性迴歸）** 研究特徵選擇與模型評估，以 **CRISP-DM 六階段**組織學習過程。重點是**可重現、可稽核的實驗**：由真實 Python 執行產生指標及圖表，不以靜態展示數字冒充即時分析。

## Project at a glance / 專案現況

| 模組 | 狀態 | 證據／連結 |
| --- | --- | --- |
| 50 Startups — Regression Baseline | 已合併（Issue #3 / PR #14） | [實測報告與六張圖](docs/reports/50_startups/report.md) |
| Feature Selection — 五種方法 | 已合併（Issue #4 / PR #15） | [比較報告及 RMSE / R² 曲線](docs/reports/feature_selection/REPORT.md) |
| Boston Housing — Workflow Reuse | Issue #5 待交付／審查 | [Issue #5](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues/5) |
| Web Dashboard | 靜態介面骨架 | [Web 說明](web/README.md) |
| Custom CSV / Dataset URL | 尚未實作 | [Issue #7](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues/7) · [ADR-0002 提案 PR](https://github.com/wupojung/AIoT-DIC2-MultipleLR/pull/12) |

**Demo Screenshot：** 待補。取得正式確認的 Demo 畫面後，再加入專案截圖；不使用不相符的示意圖冒充。

## Measured research results / 實測成果

| 實驗 | 指標 | 實測結果 | 解讀 |
| --- | --- | ---: | --- |
| 50 Startups Baseline | Holdout R² | **0.898727** | 固定 40/10 split；10 筆測試樣本 |
| 50 Startups Baseline | Holdout RMSE | **9,055.957** | 來源數值單位，貨幣／期間未確認 |
| Feature Selection | Nested CV mean RMSE | **9,237.359** | 評估 training-only 選模程序，非新的 holdout |
| Feature Selection | 最終凍結選擇 | **F-Test, k=3** | 使用全部 training 的三折選模，非直接取圖上的最低點 |

研究限制與完整精度詳見 [Baseline report](docs/reports/50_startups/report.md)、[Feature Selection report](docs/reports/feature_selection/REPORT.md)。以上不是網站即時計算結果；不同資料集的 RMSE 不應直接比較。Feature Selection 不重複利用已公開的測試集挑選方法。

## Engineering quality / CI, CD & Coverage

| 機制 | 現況 | 查看方式 |
| --- | --- | --- |
| **CD — GitHub Pages** | 已有 `.github/workflows/pages.yml`；部署是否成功以 Actions 為準 | [Pages workflow](https://github.com/wupojung/AIoT-DIC2-MultipleLR/actions/workflows/pages.yml) |
| **CI — Python / Browser tests** | 有本地自動化測試，但**尚未建立獨立的 CI Workflow** | [測試程式](tests/) · [Issues](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues) |
| **Test coverage** | **尚未量測，無可信覆蓋率百分比** | 待加入 `coverage.py` 與 `coverage.xml` |
| **Verification** | 各 PR 提供 BUILD → RUN → TEST → VERIFY → PASS 紀錄 | [Merged PR #14](https://github.com/wupojung/AIoT-DIC2-MultipleLR/pull/14) · [Merged PR #15](https://github.com/wupojung/AIoT-DIC2-MultipleLR/pull/15) |

部署徽章讀取 GitHub Actions 真實狀態；目前**不放假的 CI Passed／Coverage % 徽章**。預計後續新增獨立 CI（Python 單元測試、Verifier、Browser smoke），並量測 Coverage，再依實際結果決定是否設置門檻。Coverage 是測試覆蓋程度，**不是模型準確率，也不是 R²**。

> **部署注意：** 現有 Pages Workflow 只在 `main` 的 `web/**` 或 Workflow 本身異動時自動觸發，亦可手動執行。單獨修改 README **不會觸發 Pages 部署**。請於 [Settings → Pages](https://github.com/wupojung/AIoT-DIC2-MultipleLR/settings/pages) 使用「GitHub Actions」來源。

## Datasets and assignment / 資料與作業範圍

- **50 Startups:** 預測 `Profit`，以 50 筆資料完成可重現的 Baseline 與 Feature Selection。
- **Boston Housing:** 預測 `MEDV`；這是存在種族相關欄位倫理爭議的歷史教學資料集，使用前須確認來源與處理政策。
- **Optional bonus:** 未來希望支援資料集下拉選單及自訂 CSV 檔案／URL，重新選擇 Target (y)／Features (X) 並計算結果；目前**尚未實作**。
- 課堂出現的「14–39 Features」是資料集探索提示詞，是否為正式要求仍待教師確認；最後上傳規範也以教師最新說明為準。

## Research workflow / CRISP-DM

| Phase | 工作 |
| --- | --- |
| 1. Business Understanding | 定義問題、預測目標及限制 |
| 2. Data Understanding | 來源、schema、EDA、品質檢查 |
| 3. Data Preparation | 訓練／測試切分、缺值、類別編碼、避免 Data Leakage |
| 4. Modeling | LinearRegression、Dummy Baseline、Cross-Validation |
| 5. Evaluation | MAE／MSE／RMSE／R²、殘差、五種 Feature Selection、Nested CV |
| 6. Deployment | 可重現成果、研究報告與網站展示；Web 模型串接未完成 |

五種方法：**Pearson、F-Test、RFE、Forward SFS、LassoCV**。所有方法的最終估計器統一為 LinearRegression；詳細比較方法與資料切分請參考 [Feature Selection Protocol](docs/FEATURE_SELECTION_PROTOCOL.md)。

## Quick start / 本地執行

需要 **Python 3.12+**（已報告驗證環境 Python 3.14.2）以及一般瀏覽器；套件清單見 [requirements.txt](requirements.txt) / [constraints.txt](constraints.txt)。

```sh
git clone https://github.com/wupojung/AIoT-DIC2-MultipleLR.git
cd AIoT-DIC2-MultipleLR
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python python/src/environment_check.py
python python/src/startups_baseline.py --run-id baseline-v1
python -m unittest discover -s tests -v
python -m http.server 8000 --directory web
```

瀏覽 <http://localhost:8000/>。上述 Baseline 命令需要下載並 SHA-256 驗證固定的 50 Startups 資料來源；執行結果放在 `outputs/`（預設不提交）。依 [Feature Selection 報告](docs/reports/feature_selection/REPORT.md) 的指令可另行重現特徵選擇實驗。Windows 指令請見 [Python 使用說明](python/README.md)。

## Architecture, documentation & governance

- [Architecture](docs/ARCHITECTURE.md) · [CRISP-DM](docs/CRISP_DM.md) · [Evaluation Protocol](docs/EVALUATION_PROTOCOL.md) · [Workflow Reuse](docs/WORKFLOW_REUSE.md)
- [Dataset definitions & ethics](docs/PROBLEM_DEFINITIONS.md) · [Data sources](data/README.md) · [Bilingual glossary](docs/GLOSSARY.md)
- [ADR-0001（Accepted）](docs/adr/ADR-0001-project-foundation.md) · [ADR index](docs/adr/README.md) · [ADR-0002（Proposed PR）](https://github.com/wupojung/AIoT-DIC2-MultipleLR/pull/12)
- [Repository Issues](https://github.com/wupojung/AIoT-DIC2-MultipleLR/issues) · [Teacher reference (read-only)](https://github.com/huanchen1107/AIoT-DIC2-MultipleLR) · [Previous experiment (reference only)](https://github.com/wupojung/DIC-2_test)

**Development policy:** Codex on isolated branches, BUILD → RUN → TEST → VERIFY → PASS; every PR requires human review and explicit merge approval. Unverified claims, hard-coded model scores and holdout-driven feature tuning are prohibited.

## 自訂 CSV 測試資料 / Custom regression CSV examples

以下是真實公開 CSV 的**候選測試資料**，已檢查 GitHub 原始檔來源及欄位名稱。適用於未來 Custom Dataset 功能驗證，**不表示目前網站已具備 CSV 匯入或分析功能**。來源屬第三方，網址可用性、CORS、授權與欄位內容可能變動；請在正式測試時重新驗證。

| Dataset | CSV URL | Target (y) | 建議 Features (X) | 注意事項 |
| --- | --- | --- | --- | --- |
| 50 Startups | [50_Startups.csv](https://raw.githubusercontent.com/Avik-Jain/100-Days-Of-ML-Code/master/datasets/50_Startups.csv) | `Profit` | `R&D Spend`, `Administration`, `Marketing Spend`, `State` | `State` 是類別欄位，需 one-hot；小樣本，評估有不確定性。 |
| Auto MPG | [mpg.csv](https://raw.githubusercontent.com/mwaskom/seaborn-data/master/mpg.csv) | `mpg` | `cylinders`, `displacement`, `horsepower`, `weight`, `acceleration` | `horsepower` 有缺失值；`name` 不建議直接當連續數值特徵。 |
| Restaurant Tips | [tips.csv](https://raw.githubusercontent.com/plotly/datasets/master/tips.csv) | `tip` | `total_bill`, `size` | 想加入 `sex`, `smoker`, `day`, `time` 等類別欄位時，必須先做適當編碼；避免將觀察關係誤解為因果。 |

**預計使用方式（尚未實作）：** 將 CSV URL 貼入 Custom Dataset → 預覽資料 → 手動指定 Target 與兩個以上 Features → 檢查缺值與類別資料 → 選擇適合的前處理 → 重新訓練 Regression → 顯示來自本次資料的 MAE / MSE / RMSE / R² 與圖表。切勿重用別的資料集的模型、特徵排序或分數。

如果網址被瀏覽器的 **CORS** 政策阻擋，改用「下載 CSV 後上傳檔案」（待實作）。不是每個 CSV 都適合多元線性迴歸；Target 須為可用的連續數值，且需要足夠獨立樣本，不得存在無法處理的資料洩漏、特徵共線性或有效樣本不足問題。這些示例**並非**課堂「14–39 特徵」的符合性證明。

## GitHub Pages preview deployment

正式預覽網址預計為 `https://wupojung.github.io/AIoT-DIC2-MultipleLR/`，但**必須等 GitHub Pages 正式啟用且部署成功後才能視為可用**。

GitHub Repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**。本 Repo 的 `.github/workflows/pages.yml` 將只發佈 `web/` 這個靜態資料夾，不會公開 `data/`、Python 產物或其他研究檔案。首次部署需確認 Settings 已啟用並檢查 Actions 實際結果；目前網頁僅為 Foundation UI，不支援 CSV 分析。
