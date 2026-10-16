"""Boston-specific source policy and reporting around the shared training engine."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import io
import json
from pathlib import Path
import platform
import re
import urllib.request

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression

import feature_selection as fs
import regression_workflow as workflow

ROOT = Path(__file__).resolve().parents[2]
COLUMNS = tuple('CRIM ZN INDUS CHAS NOX RM AGE DIS RAD TAX PTRATIO B LSTAT MEDV'.split())
CONFIG = workflow.DatasetConfig('boston_housing', 'MEDV',
    tuple(c for c in COLUMNS if c not in ('B', 'MEDV')), (), 506, COLUMNS,
    excluded=('B',), expected_encoded_features=12)
ALPHAS = np.logspace(-4, 2, 21).tolist()


def validate(frame):
    workflow.validate_data(frame, CONFIG)
    if not all(pd.api.types.is_numeric_dtype(frame[c]) for c in COLUMNS):
        raise ValueError('All original columns, including excluded B, must be numeric')
    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError('Historical source must contain finite, complete numeric observations')
    if not frame.CHAS.isin([0, 1]).all():
        raise ValueError('CHAS must be binary')


def parse_source(raw, manifest):
    if len(raw) != manifest['bytes'] or hashlib.sha256(raw).hexdigest() != manifest['sha256']:
        raise ValueError('Boston source SHA256/size mismatch')
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if blob != manifest['git_blob'] or raw.splitlines()[0].split(b',')[:2] != [b'506', b'13']:
        raise ValueError('Boston Git blob/metadata mismatch')
    frame = pd.read_csv(io.BytesIO(raw), skiprows=1)
    validate(frame)
    return frame


def acquire_data(cache):
    manifest = json.loads((ROOT / 'data/boston_housing_manifest.json').read_text())
    cache = Path(cache)
    path = cache / 'boston_house_prices.csv'
    raw = path.read_bytes() if path.exists() else urllib.request.urlopen(manifest['url'], timeout=60).read()
    frame = parse_source(raw, manifest)
    cache.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(raw)
    return frame, {**manifest, 'verified_at_utc': datetime.now(timezone.utc).isoformat()}


def protocol():
    return {**fs.protocol(), 'version': 'DIC2-05-MVP-v1', 'alpha_grid': ALPHAS,
            'ks': list(range(1, 13)), 'unit': '12 numeric predictors; B excluded; CHAS binary, RAD numeric index',
            'holdout': 'Once after freeze: predeclared all-feature LR, selected LR and mean dummy',
            'scope': 'historical random-sample assessment; not spatial generalization',
            'owner_decision': 'PR17 issuecomment-6218126601; provisional, not instructor approval'}


def run(frame, provenance, output_root, run_id):
    validate(frame)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', run_id):
        raise ValueError('Invalid run-id')
    directory = Path(output_root) / CONFIG.dataset_id / run_id
    directory.mkdir(parents=True, exist_ok=False)
    train, test = workflow.split_row_ids(frame.index)
    X, y = frame.loc[train, list(CONFIG.features)], frame.loc[train, CONFIG.target]
    workflow.write_json(directory / 'protocol.json', protocol())
    workflow.write_json(directory / 'provenance.json', provenance)
    workflow.write_json(directory / 'splits.json', {'train_row_ids': train.tolist(), 'test_row_ids': test.tolist()})
    workflow.write_json(directory / 'environment.json', {'python': platform.python_version(),
        'packages': {p: version(p) for p in ['numpy', 'pandas', 'scikit-learn', 'scipy', 'matplotlib']}})
    workflow.write_json(directory / 'data_quality.json', {'shape': list(frame.shape),
        'missing': int(frame.isna().sum().sum()), 'duplicate_rows': int(frame.duplicated().sum()),
        'medv_at_50': int((frame.MEDV == 50).sum()), 'predictors': list(CONFIG.features),
        'excluded': ['B'], 'train_rows': len(train), 'test_rows': len(test)})
    # Data-dependent descriptive summaries are training-only.
    X.join(y).describe().to_csv(directory / 'training_summary.csv')
    X.join(y).corr().to_csv(directory / 'training_correlations.csv')
    try:
        result = fs.training_experiment(X, y, CONFIG, ALPHAS)
        predictions = result.pop('predictions')
        dummy_scores = []
        for fold, (fit, val) in enumerate(workflow.folds(X, 5)):
            predicted = DummyRegressor(strategy='mean').fit(X.iloc[fit], y.iloc[fit]).predict(X.iloc[val])
            dummy_scores.append({'context': f'outer{fold}', 'method': 'Dummy', 'k': 0,
                                 **workflow.metrics(y.iloc[val], predicted)})
            predictions.extend({'context': f'outer{fold}', 'method': 'Dummy', 'k': 0,
                'row_id': int(row), 'actual': float(actual), 'prediction': float(pred)}
                for row, actual, pred in zip(X.iloc[val].index, y.iloc[val], predicted))
        result['dummy_cv'] = dummy_scores
        # Persist the training-only choice before any holdout transformation/prediction.
        workflow.write_json(directory / 'frozen_selection.json', {
            'choice': result['final_choice'], 'holdout_evaluations': 0,
            'protocol_sha256': hashlib.sha256((directory / 'protocol.json').read_bytes()).hexdigest()})
        prepared = fs.prepare(X, 'final_refit', result['audit'], CONFIG)
        names = result['final_choice']['features']
        indices = [prepared.names.index(n) for n in names]
        baseline = LinearRegression().fit(prepared.values, y)
        selected = LinearRegression().fit(prepared.values[:, indices], y)
        dummy = DummyRegressor(strategy='mean').fit(X, y)
        test_values = prepared.transform(frame.loc[test, list(CONFIG.features)])
        holdout, rows = {}, []
        for method, pred in [('All Features', baseline.predict(test_values)),
                             ('Selected', selected.predict(test_values[:, indices])),
                             ('Dummy', dummy.predict(frame.loc[test, list(CONFIG.features)]))]:
            actual = frame.loc[test, CONFIG.target]
            holdout[method] = workflow.metrics(actual, pred)
            rows.extend({'method': method, 'row_id': int(i), 'actual': float(a),
                         'prediction': float(p), 'residual': float(a-p)} for i, a, p in zip(test, actual, pred))
        result['holdout'] = holdout
        result['fitted_models'] = {'encoded_names': prepared.names, 'selected_features': names,
            'all_coefficients': baseline.coef_.tolist(), 'all_intercept': float(baseline.intercept_),
            'selected_coefficients': selected.coef_.tolist(), 'selected_intercept': float(selected.intercept_)}
        pd.DataFrame(predictions).to_csv(directory / 'predictions.csv.gz', index=False, compression='gzip')
        pd.DataFrame(rows).to_csv(directory / 'holdout_predictions.csv', index=False)
        for file, key in [('comparison', 'comparison_summary'), ('plot_data', 'comparison_summary'),
                          ('final_selection', 'final_selection_summary'), ('nested', 'nested')]:
            pd.DataFrame(result[key]).to_csv(directory / f'{file}.csv', index=False)
        subsets = [{'context': t['context'], 'method': m, 'k': k,
                    'features_json': json.dumps(order[:k]), 'order_json': json.dumps(order)}
                   for t in result['traces'] for m, order in t['orders'].items() for k in range(1, 13)]
        pd.DataFrame(subsets).to_csv(directory / 'selected_features.csv', index=False)
        workflow.write_json(directory / 'results.json', result)
        fs.plot_curves(result['comparison_summary'], directory,
                       xlabel='Number of predictors (B excluded)', units='historical USD thousands')
        write_report(directory, result)
        workflow.write_json(directory / 'status.json', {'status': 'TECHNICAL_COMPLETE', 'human_review': 'pending'})
    except Exception as error:
        workflow.write_json(directory / 'status.json', {'status': 'FAIL', 'reason': str(error)})
        raise
    return directory


def write_report(directory, result):
    choice = result['final_choice']
    lines = ['# Boston Housing — CRISP-DM 實測報告', '',
        '本報告由實際執行產生。技術驗證與人工／教師接受分開；尚待人工 Review。', '',
        '## 1. 商業理解', '',
        '以歷史地區聚合資料預測 MEDV（歷史千美元），驗證流程重用。不得用於現代住房決策，亦不宣稱因果關係。', '',
        '## 2. 資料理解', '',
        '來源、版本、SHA256 與權利限制見 [provenance.json](provenance.json)；欄位說明見 [來源與政策](../../BOSTON_WORKFLOW_PROPOSAL.md)。',
        '506 筆、13 原始 predictors + MEDV；排除 B 後 12 個。完整結構稽核見 [data_quality.json](data_quality.json)。',
        'B 是歷史種族比例的非線性變換；排除不代表移除代理偏誤。LSTAT 等仍具社經偏誤。',
        '原始資料專屬授權與來源權利尚未完全釐清；owner 暫准本地教學評估，不代表教師核准或新授權；不散布原始 CSV。', '',
        '## 3. 資料準備', '',
        'seed=42，404 train / 102 holdout；不沿用 Startups row IDs。來源沒有可用地理群組 ID，僅評估歷史隨機樣本，不能外推空間泛化。',
        'CHAS 保持二元數值；RAD 保持來源的數值索引；無 State/OHE。每個相關 training fold 重擬合補值／尺度及選擇器。', '',
        '## 4. 建模', '',
        '共用 regression_workflow 與 feature_selection.training_experiment；五方法實際執行，最終預測器皆 LinearRegression。',
        '外層 5 折比較固定方法/k；內層 3 折選擇；SFS/Lasso 各自再有 fold-local 3 折。',
        'LassoCV 固定 21 個 alpha（1e-4..1e2）；按局部 CV 最小 mean MSE 選 alpha，同分取較大 alpha；重擬合後依標準化係數絕對值降序、同分依欄名。零係數仍明示在排名尾端，k 可納入。',
        'Pearson 依 abs(r)、F-Test 依 F 值、RFE 依逆淘汰順序（非前向加入）、SFS 依真正貪婪進入順序。所有 context 的完整順序與每個 k 集合見 selected_features.csv。', '',
        '## 5. 評估', '',
        f"訓練內 final 3-fold 選擇：**{choice['method']}，k={choice['k']}**，CV RMSE={choice['rmse_mean']:.6f}。這是選擇分數，不能當成無偏估計。",
        f"最終欄位：{', '.join(choice['features'])}。",
        f"Nested selection 外層 RMSE={result['nested_summary']['rmse']['mean']:.6f} ± {result['nested_summary']['rmse']['std']:.6f}；R²={result['nested_summary']['r2']['mean']:.6f}。", '',
        '| 模型（一次最終 holdout） | MAE | MSE | RMSE | R² |', '| --- | ---: | ---: | ---: | ---: |']
    for method, row in result['holdout'].items():
        lines.append(f"| {method} | {row['mae']:.6f} | {row['mse']:.6f} | {row['rmse']:.6f} | {row['r2']:.6f} |")
    lines += ['', '固定方法/k 的外層 training CV 最低點（描述性比較；不以此重新選 final k）：', '',
              '| 方法 | k | CV RMSE mean ± std | CV R² mean |', '| --- | ---: | ---: | ---: |']
    for method in ['All Features'] + fs.METHODS:
        best = fs.choose([r for r in result['comparison_summary'] if r['method'] == method])
        lines.append(f"| {method} | {best['k']} | {best['rmse_mean']:.6f} ± {best['rmse_std']:.6f} | {best['r2_mean']:.6f} |")
    lines += ['', '![RMSE](features_vs_rmse.png)', '', '![R²](features_vs_r2.png)', '',
        'Pearson 與單變量 F-Test 對連續目標的排序通常等價；它們忽略條件關係與共線性。RFE 考慮多變量係數但可能不穩定；SFS 直接依局部 CV 增益逐步加入，不能回溯；Lasso 用縮放後的收縮係數排名，在相關特徵間可能替換。接近全特徵的最佳點表示本次刪減收益有限，不能把極小差距解讀為穩定優勢。', '',
        '兩圖直接使用 comparison.csv / plot_data.csv，誤差棒為 fold std，並非信賴區間。MEDV 在 50 的堆積／可能截斷、地理依賴、小樣本與方法搜尋均限制解讀；不能保證選擇後優於全特徵。', '',
        '## 6. 溝通與重用', '',
        '重用 config/schema、Pipeline、seeded split/folds、四指標、五選擇器、nested engine、JSON 與繪圖。資料來源／完整性、B 排除、單位及報告保留 Boston 專屬設定。',
        '沒有重用已訓練模型、索引、排名或數值；50 Startups 原結果不覆寫。未建大型框架、Web 整合或部署。',
        '重現：python python/src/boston_workflow.py --run-id boston-mvp-v1；接著 python python/src/verify_boston_run.py outputs/boston_housing/boston-mvp-v1。',
        '完整平台矩陣、完整 selector replay、覆蓋率／UI QA 延至 Issue #8；本次必要驗證見 VERIFICATION.md。']
    (directory / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--cache-dir', type=Path, default=ROOT / 'data/boston_housing')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'outputs')
    args = parser.parse_args()
    frame, provenance = acquire_data(args.cache_dir)
    print(json.dumps({'output': str(run(frame, provenance, args.output_root, args.run_id))}))


if __name__ == '__main__':
    main()
