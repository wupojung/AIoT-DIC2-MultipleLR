# Data provenance / 資料邊界

[50 Startups manifest](50_startups_manifest.json) 固定教師引用鏡像的 revision、URL、
SHA-256、預期 schema、repository license 及未確認限制。baseline 初次執行下載至
ignored 的 data/50_startups/，記錄 retrieval.json，之後使用校驗過的 cache。
原始 CSV 不提交；cache 若改動會失敗，不自動改用其他來源。

來源 repository 在固定 revision 附 MIT notice（2018 Avik Jain），但原始資料蒐集與
資料專屬權利未獨立查明；僅作本次本地教學分析，不主張重新授權或可生產使用。
Profit 與支出的幣別／期間無可靠證據，圖表使用 source units。無企業識別／時間資料，
不能完整驗證樣本獨立性；拒絕重複 predictors，仍不代表解決所有抽樣偏誤。

Boston 不下載、不訓練；須另行確認歷史來源、license、變數與倫理限制。私有／自訂資料
不得提交。新增 tracked dataset 需要明確決策，本次只追蹤 metadata manifest。
