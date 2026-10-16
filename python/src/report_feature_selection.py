"""Publish a curated Traditional Chinese review snapshot from measured outputs."""
import argparse
import json
from pathlib import Path
import shutil

import feature_selection as fs


def publish(source, destination):
    result = json.loads((source / 'results.json').read_text(encoding='utf-8'))
    protocol = json.loads((source / 'protocol.json').read_text(encoding='utf-8'))
    if protocol != fs.protocol():
        raise ValueError('Report exporter expects the recorded v1 protocol')
    if json.loads((source / 'status.json').read_text())['status'] != 'TECHNICAL_COMPLETE':
        raise ValueError('Cannot publish failed/partial run')
    destination.mkdir(parents=True, exist_ok=False)
    for name in ['results.json', 'comparison.csv', 'plot_data.csv', 'predictions.csv',
                 'selected_features.csv', 'final_selection.csv', 'frozen_selection.json',
                 'protocol.json', 'splits.json', 'provenance.json', 'environment.json', 'status.json',
                 'features_vs_rmse.png', 'features_vs_r2.png']:
        shutil.copyfile(source / name, destination / name)
    full = next(trace for trace in result['traces'] if trace['context'] == 'full_training')
    lines = ['# 50 Startups 特徵選擇實測分析報告', '',
             '狀態：技術驗證完成，人工審查待完成。此報告與圖表由真實執行產物生成；',
             'Issue #3 的 Baseline／指標／圖片未覆寫。只使用原 40 筆 train，不再評估已公開過的 holdout。', '',
             '## 方法與資料', '',
             '沿用原 manifest、seed 42、80/20 和五折。五種 selector 每折重新擬合，',
             '最後預測皆為 LinearRegression。State 的兩個 dummy 分開計算 k，',
             'k=5 是三個數值欄 + Florida／New York，而非五個原始欄位。',
             '前處理／SFS／alpha 的三折計算全部在對應 training 範圍；',
             '細節、alpha grid、資料 block 隔離與同分規則見 [實驗協定](../../FEATURE_SELECTION_PROTOCOL.md)。', '',
             '## 五折比較表與曲線', '',
             '每列是固定方法／k 的五個 validation fold，± 為 ddof=0 的 fold std；',
             '誤差使用來源數值單位（幣別、期間未知），R² 無單位。',
             '每折的特徵集合可不同，不是先用全部 train 排名再交叉驗證。', '',
             '| 方法 | k | CV RMSE mean ± std | CV R² mean ± std |', '| --- | --- | --- | --- |']
    for row in result['comparison_summary']:
        lines.append(f"| {row['method']} | {row['k']} | {row['rmse_mean']:.3f} ± {row['rmse_std']:.3f} | {row['r2_mean']:.6f} ± {row['r2_std']:.6f} |")
    lines += ['', '![特徵數與五折 CV RMSE](features_vs_rmse.png)', '',
              '![特徵數與五折 CV R²](features_vs_r2.png)', '', '### 曲線的最低點（描述性比較）', '']
    for method in fs.METHODS:
        winner = min((row for row in result['comparison_summary'] if row['method'] == method),
                     key=lambda row: (row['rmse_mean'], row['k']))
        lines.append(f"- {method}：最低平均 RMSE 的 k={winner['k']}，RMSE={winner['rmse_mean']:.3f}，R²={winner['r2_mean']:.6f}。")
    lines += ['', 'Pearson 與單變量 F-test 在此得到等價排序；曲線相同有數學理由，並非共用固定假排名。',
              'RFE 逐步重 fit 刪欄；SFS 每步對剩餘候選重算內折表現，所以局部路徑可不同。',
              'Lasso 依標準化係數排序，對正則化強度與共線性敏感。',
              '不同 k 的 R² 和 RMSE 最佳點不一定相同；規則預先以 mean RMSE 選擇，不事後換指標。', '',
              '## 全部 40 train 的實際順序與每個 k 集合', '',
              '此表用於解釋最終重擬合，不可拿它代替每折選擇。RFE 順序是反向淘汰優先序；',
              'SFS 是實際 greedy 加入順序，其他方法是分數／絕對係數排序。', '',
              '| 方法 | k | 特徵（依該方法順序） |', '| --- | --- | --- |']
    for method, order in full['orders'].items():
        for k in range(1, 6):
            lines.append(f"| {method} | {k} | " + ' → '.join(f'`{name}`' for name in order[:k]) + ' |')
    lasso = full['details']['LassoCV']
    lines += ['', f"LassoCV 在完整 train 的真實最佳 alpha={lasso['alpha']:.12g}，以 21 個預定 alpha 的三折 mean MSE 選出。", '',
              '| Lasso 標準化欄位 | 實測係數 |', '| --- | --- |']
    for name, coefficient in lasso['standardized_coefficients'].items():
        lines.append(f'| `{name}` | {coefficient:.9f} |')
    lines += ['', '零係數欄：' + '、'.join(f'`{name}`' for name in lasso['zero_coefficient_names']) + '。',
              '這些欄位在高 k 時僅按明訂字典序補入，不代表 Lasso 判定它們有非零貢獻。',
              '[完整 600 組每折／方法／k 子集與順序](selected_features.csv)；',
              '[真實選擇器 trace、SFS 候選分數、alpha path 與 fit audit](results.json)。', '',
              '## 巢狀驗證與最終凍結方案', '',
              '曲線最低點經過 26 候選比較，有選擇偏差；另外用外五折／內三折評估整個選模程序。',
              '各外折只憑自己的 training 內折選方法／k，再評分外折 validation：', '',
              '| 外折 | 內折勝者 | k | 外折 RMSE | 外折 R² |', '| --- | --- | --- | --- | --- |']
    for row in result['nested']:
        lines.append(f"| {row['context']} | {row['method']} | {row['k']} | {row['rmse']:.3f} | {row['r2']:.6f} |")
    nested, choice = result['nested_summary'], result['final_choice']
    lines += ['', f"整個選模程序的 nested RMSE={nested['rmse']['mean']:.3f} ± {nested['rmse']['std']:.3f}，",
              f"nested R²={nested['r2']['mean']:.6f} ± {nested['r2']['std']:.6f}。", '',
              f"全部 40 train 依相同內三折規則凍結的方案為 **{choice['method']}，k={choice['k']}**；",
              f"選擇用 CV RMSE={choice['rmse_mean']:.3f}（這是選擇分數，不是無偏的新 test 指標）。", '',
              '特徵：' + '、'.join(f'`{name}`' for name in choice['features']) + '。', '',
              '完整 train 的三折選模和五折曲線描述性最低點可能不同，這正反映小樣本／切分不確定性；',
              '不事後改採較好看的曲線勝者。[最終三折候選表](final_selection.csv)、',
              '[凍結方案與 protocol hash](frozen_selection.json)。本次 holdout_evaluations=0。', '',
              '## 驗證證據與限制', '',
              'Verifier 由 6240 筆 training-only 預測重算四指標，重新擬合各候選 OLS，',
              '驗全部 fit/split、600 組子集與 nested 決策；逐 alpha 的獨立 Lasso 重算',
              '確認全部 24 組 LassoCV path。從已驗 CSV 重畫圖並比對 PNG bytes。',
              '測試另更動整個 holdout X/y，要求結果、選擇、audit、圖表完全不變。',
              'All Features CV 與原 Baseline regression tests 持續比較。', '',
              '最小內層 training 約 14 筆，fold std 不是信賴區間；只一組切分不足以證明方法顯著勝出。',
              '原 Baseline holdout 已曝光，無法稱為新的未見 test。樣本來源、資料專屬權利、',
              '幣別／期間、企業獨立性仍有限制；不能作因果解釋或現實獲利建議。', '',
              '教師範例 [README（固定版本）](https://github.com/huanchen1107/AIoT-DIC2-MultipleLR/blob/8b65e3bd9745e650ae7bea28f9562c059d5029ed/README.md)',
              '展示的演算法組合與以 test 呈現 k 曲線不同；本期依 Issue #4 五方法、training CV／nested、同下游 OLS，',
              '不複製教師分數或預設最佳 k。舊 [DIC-2_test](https://github.com/wupojung/DIC-2_test/blob/969ae66465ddb815dab76a29c887207cf4885843/feature_selection.py)',
              '中的固定 RFE 路徑、以固定排序當 SFS、固定 k=2 標記、seed=0 與 mixed Lasso/RandomForest',
              '預測等做法均不沿用；第五欄直接由 encoder 名稱與真正選擇結果取得。', '',
              '## 重現', '', '```sh',
              'python python/src/feature_selection.py --run-id fs-v1',
              'python python/src/verify_feature_selection.py outputs/50_startups/feature_selection/fs-v1 --source data/50_startups/50_Startups.csv --replay-lasso',
              'python python/src/report_feature_selection.py outputs/50_startups/feature_selection/fs-v1 --output-dir /tmp/fs-review',
              'python -m unittest discover -s tests -v', '```', '',
              '首次需固定來源 CSV 或已驗證 cache；run-id 與報告目錄都拒絕覆寫。',
              '沒有修改已接受 ADR、Baseline、Web 整合或部署；等待人工審查，不自動 Merge／close Issue。']
    (destination / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    publish(args.run_directory, args.output_dir)
