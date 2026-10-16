# Data provenance / 資料邊界

[50 Startups manifest](50_startups_manifest.json) 固定教師引用鏡像的 revision、URL、
SHA-256、預期 schema、repository license 及未確認限制。baseline 初次執行下載至
ignored 的 data/50_startups/，記錄 retrieval.json，之後使用校驗過的 cache。
原始 CSV 不提交；cache 若改動會失敗，不自動改用其他來源。

來源 repository 在固定 revision 附 MIT notice（2018 Avik Jain），但原始資料蒐集與
資料專屬權利未獨立查明；僅作本次本地教學分析，不主張重新授權或可生產使用。
Profit 與支出的幣別／期間無可靠證據，圖表使用 source units。無企業識別／時間資料，
不能完整驗證樣本獨立性；拒絕重複 predictors，仍不代表解決所有抽樣偏誤。

[Boston manifest](boston_housing_manifest.json) 固定歷史 sklearn CSV revision、Git blob、SHA256 與 schema。
依 [owner 暫行政策](../docs/BOSTON_WORKFLOW_PROPOSAL.md) 執行本地教學 MVP；B 不進入模型。
`boston_workflow.py` 首次下載到 ignored data/boston_housing/，每次核對 hash；不提交 raw CSV。
原始資料專屬授權／來源權利尚未完全確證，不以 repository BSD 當作資料重新授權。
私有／自訂資料不得提交；本次只新增 metadata manifest 與衍生實驗證據。
