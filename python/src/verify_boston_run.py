"""Lean independent integrity, leakage and prediction verifier for the Boston MVP."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import boston_workflow as boston
import feature_selection as fs
import regression_workflow as workflow


def scores(actual, prediction, record):
    expected = {'mae': mean_absolute_error(actual, prediction),
                'mse': mean_squared_error(actual, prediction),
                'rmse': np.sqrt(mean_squared_error(actual, prediction)),
                'r2': r2_score(actual, prediction)}
    for name, value in expected.items():
        assert np.isclose(value, record[name], rtol=1e-10, atol=1e-10), (name, value, record[name])


def verify(directory, frame):
    directory = Path(directory)
    read = lambda name: json.loads((directory / name).read_text())
    boston.validate(frame)
    assert read('protocol.json') == boston.protocol()
    assert read('provenance.json')['sha256'] == json.loads((boston.ROOT / 'data/boston_housing_manifest.json').read_text())['sha256']
    split, result = read('splits.json'), read('results.json')
    train, test = workflow.split_row_ids(frame.index)
    assert split == {'train_row_ids': train.tolist(), 'test_row_ids': test.tolist()}
    train_set, test_set = set(train), set(test)
    assert len(train) == 404 and len(test) == 102 and not train_set & test_set
    names = ['numeric__' + name for name in boston.CONFIG.features]
    assert len(names) == 12 and 'numeric__B' not in names
    X, y = frame.loc[train, list(boston.CONFIG.features)], frame.loc[train, 'MEDV']
    expected_contexts = {'full_training': (train_set, set())}
    for outer, (fit, val) in enumerate(workflow.folds(X, 5)):
        local = X.iloc[fit]
        expected_contexts[f'outer{outer}'] = (set(local.index), set(X.iloc[val].index))
        for inner, (a, b) in enumerate(workflow.folds(local, 3)):
            expected_contexts[f'outer{outer}/inner/{inner}'] = (set(local.iloc[a].index), set(local.iloc[b].index))
    for inner, (a, b) in enumerate(workflow.folds(X, 3)):
        expected_contexts[f'final/inner/{inner}'] = (set(X.iloc[a].index), set(X.iloc[b].index))
    assert len(result['traces']) == len(expected_contexts) == 24
    contexts = {trace['context']: trace for trace in result['traces']}
    assert set(contexts) == set(expected_contexts)
    subset_csv = pd.read_csv(directory / 'selected_features.csv')
    assert len(subset_csv) == 24 * 5 * 12
    for context, trace in contexts.items():
        fit, val = expected_contexts[context]
        assert set(trace['fit_row_ids']) == fit and set(trace.get('validation_row_ids', [])) == val
        assert not fit & val and not (fit | val) & test_set
        assert trace['encoded_names'] == names
        assert set(trace['orders']) == set(fs.METHODS)
        for method, order in trace['orders'].items():
            assert len(order) == 12 and set(order) == set(names)
            for k in range(1, 13):
                assert trace['subsets'][method][str(k)] == order[:k]
                row = subset_csv[(subset_csv.context == context) & (subset_csv.method == method) & (subset_csv.k == k)].iloc[0]
                assert json.loads(row.features_json) == order[:k] and json.loads(row.order_json) == order
        for method in ['SFS', 'LassoCV']:
            local = frame.loc[trace['fit_row_ids']]
            for entry, (a, b) in zip(trace['details'][method]['folds'], workflow.folds(local, 3)):
                assert entry['fit_row_ids'] == local.iloc[a].index.tolist()
                assert entry['validation_row_ids'] == local.iloc[b].index.tolist()
        lasso = trace['details']['LassoCV']
        grid, path = np.array(lasso['alphas']), np.array(lasso['mse_path'])
        assert np.allclose(grid, sorted(boston.ALPHAS, reverse=True)) and path.shape == (21, 3)
        assert lasso['alpha'] == grid[np.argmin(path.mean(axis=1))]
    for audit in result['audit']:
        ids = audit['fit_row_ids']
        assert set(ids) <= train_set and not set(ids) & test_set
        assert audit['encoded_names'] == names
        numeric = frame.loc[ids, list(boston.CONFIG.features)]
        assert np.allclose(audit['numeric_medians'], numeric.median().to_numpy())
        assert np.allclose(audit['scaler_mean'], numeric.mean().to_numpy())
        assert np.allclose(audit['scaler_scale'], numeric.std(ddof=0).to_numpy())
        if audit['context'] != 'final_refit':
            parent = audit['context'].split('/sfs/')[0].split('/lasso/')[0]
            assert set(ids) <= expected_contexts[parent][0]
    predictions = pd.read_csv(directory / 'predictions.csv.gz')
    assert set(predictions.row_id) == train_set
    assert np.allclose(predictions.actual, frame.loc[predictions.row_id, 'MEDV'])
    records = result['comparison'] + result['tuning'] + result['dummy_cv']
    assert len(predictions) == sum(r['n'] for r in records)
    designs = {}
    for context, (fit, val) in expected_contexts.items():
        if not val:
            continue
        trace = contexts[context]
        local = workflow.make_pipeline(boston.CONFIG).named_steps['preprocess']
        fit_ids = trace['fit_row_ids']
        val_ids = trace['validation_row_ids']
        designs[context] = (local.fit_transform(frame.loc[fit_ids]),
                            local.transform(frame.loc[val_ids]), fit_ids, val_ids)
    for record in records:
        rows = predictions[(predictions.context == record['context']) &
                           (predictions.method == record['method']) & (predictions.k == record['k'])]
        assert len(rows) == record['n'] and set(rows.row_id) == expected_contexts[record['context']][1]
        scores(rows.actual, rows.prediction, record)
        fit_values, val_values, fit_ids, val_ids = designs[record['context']]
        assert rows.row_id.tolist() == val_ids
        if record['method'] == 'Dummy':
            predicted = np.repeat(frame.loc[fit_ids, 'MEDV'].mean(), len(val_ids))
        else:
            selected_indices = [names.index(n) for n in record['features']]
            predicted = LinearRegression().fit(fit_values[:, selected_indices], frame.loc[fit_ids, 'MEDV']).predict(val_values[:, selected_indices])
        assert np.allclose(rows.prediction, predicted, rtol=1e-9, atol=1e-9)
    for outer, nested in enumerate(result['nested']):
        winner = fs.choose(fs.summarize([r for r in result['tuning'] if r['context'].startswith(f'outer{outer}/inner/')]))
        assert nested['method'] == winner['method'] and nested['k'] == winner['k']
        observed = next(r for r in result['comparison'] if r['context'] == f'outer{outer}' and r['method'] == winner['method'] and r['k'] == winner['k'])
        assert all(nested[key] == value for key, value in observed.items())
    summary = fs.summarize(result['comparison'])
    pd.testing.assert_frame_equal(pd.DataFrame(summary), pd.read_csv(directory / 'comparison.csv'), check_exact=False)
    pd.testing.assert_frame_equal(pd.read_csv(directory / 'comparison.csv'), pd.read_csv(directory / 'plot_data.csv'))
    assert result['final_choice'] == {**fs.choose(fs.summarize([r for r in result['tuning'] if r['context'].startswith('final/')])),
        'features': result['final_choice']['features'], 'selection_cv': '3-fold full training'}
    frozen = read('frozen_selection.json')
    assert frozen['choice'] == result['final_choice'] and frozen['holdout_evaluations'] == 0
    assert frozen['protocol_sha256'] == hashlib.sha256((directory / 'protocol.json').read_bytes()).hexdigest()
    chosen = result['final_choice']
    full = contexts['full_training']
    assert chosen['features'] == (names if chosen['method'] == 'All Features' else full['orders'][chosen['method']][:chosen['k']])
    # Independent refit verifies actual final LR predictions from the original source.
    pipeline = workflow.make_pipeline(boston.CONFIG).fit(X, y)
    train_values = pipeline.named_steps['preprocess'].transform(X)
    test_values = pipeline.named_steps['preprocess'].transform(frame.loc[test, list(boston.CONFIG.features)])
    indices = [names.index(n) for n in chosen['features']]
    expected = {'All Features': pipeline.predict(frame.loc[test, list(boston.CONFIG.features)]),
                'Selected': LinearRegression().fit(train_values[:, indices], y).predict(test_values[:, indices]),
                'Dummy': np.repeat(y.mean(), len(test))}
    holdout = pd.read_csv(directory / 'holdout_predictions.csv')
    assert len(holdout) == 306 and set(holdout.method) == set(expected)
    for method, predicted in expected.items():
        rows = holdout[holdout.method == method]
        assert rows.row_id.tolist() == test.tolist()
        assert np.allclose(rows.actual, frame.loc[test, 'MEDV'])
        assert np.allclose(rows.prediction, predicted) and np.allclose(rows.residual, rows.actual - rows.prediction)
        scores(rows.actual, rows.prediction, result['holdout'][method])
    for metric in ['rmse', 'r2']:
        assert (directory / f'features_vs_{metric}.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    evidence = {'status': 'PASS', 'source_rows': 506, 'predictors': 12, 'train_rows': 404,
        'holdout_rows': 102, 'selector_contexts': 24, 'subset_rows': len(subset_csv),
        'training_predictions_recomputed': len(predictions), 'holdout_predictions_recomputed': len(holdout),
        'checks': ['pinned source/schema', 'exact split and fold isolation', 'fold-local imputer/scaler statistics',
                   'all five selector traces and k subsets', 'LassoCV alpha path minimum',
                   'prediction-derived four metrics', 'plot data equality', 'independent final LR refit'],
        'deferred': 'Exhaustive selector replay/platform/coverage/UI expansion: Issue #8; human review pending'}
    workflow.write_json(directory / 'verification.json', evidence)
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--cache-dir', type=Path, default=boston.ROOT / 'data/boston_housing')
    args = parser.parse_args()
    frame, _ = boston.acquire_data(args.cache_dir)
    print(json.dumps(verify(args.directory, frame), ensure_ascii=False))
