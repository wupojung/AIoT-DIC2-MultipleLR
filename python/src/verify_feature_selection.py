"""Verify selection artifacts from row-level predictions, source and fit traces."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso, LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, train_test_split
from sklearn.preprocessing import StandardScaler

import startups_baseline as baseline
import feature_selection as fs


def check(condition, message):
    if not condition:
        raise ValueError(message)


def near(left, right, message):
    check(np.allclose(left, right, rtol=1e-7, atol=1e-6), message)


def preprocessing(X):
    prep = baseline.make_pipeline().named_steps['preprocess']
    values = prep.fit_transform(X)
    return prep, StandardScaler().fit(values), values


def replay_lasso(trace, frame):
    detail = trace['details']['LassoCV']
    scores = []
    for fold in detail['folds']:
        fit, val = fold['fit_row_ids'], fold['validation_row_ids']
        prep, scaler, values = preprocessing(frame.loc[fit, baseline.FEATURES])
        train = scaler.transform(values)
        validation = scaler.transform(prep.transform(frame.loc[val, baseline.FEATURES]))
        path = []
        for alpha in detail['alphas']:
            model = Lasso(alpha=alpha, max_iter=100000, tol=1e-8).fit(train, frame.loc[fit, 'Profit'])
            path.append(mean_squared_error(frame.loc[val, 'Profit'], model.predict(validation)))
        scores.append(path)
    # LassoCV uses warm starts along the path, independent fits can differ by
    # solver tolerance; 2e-5 relative tolerance is numerical, not a score change.
    check(np.allclose(np.array(scores).T, detail['mse_path'], rtol=2e-5, atol=1e-5),
          'LassoCV path differs from independent fold-local multi-alpha fits')
    selected = detail['alphas'][int(np.argmin(np.mean(detail['mse_path'], axis=1)))]
    near(selected, detail['alpha'], 'LassoCV alpha is not CV minimum')


def verify(directory, source, replay=False):
    def read(name):
        return json.loads((directory / name).read_text(encoding='utf-8'))

    result, split = read('results.json'), read('splits.json')
    frame = pd.read_csv(source)
    check(hashlib.sha256(source.read_bytes()).hexdigest() == read('provenance.json')['sha256'], 'Source hash')
    expected_train, expected_test = train_test_split(np.arange(50), test_size=0.2, random_state=42, shuffle=True)
    check(split == {'train_row_ids': expected_train.tolist(), 'test_row_ids': expected_test.tolist()}, 'Baseline split changed')
    train, test = set(expected_train), set(expected_test)
    predictions = pd.read_csv(directory / 'predictions.csv')
    check(set(predictions['row_id']) == train and not set(predictions['row_id']) & test, 'Holdout entered predictions')
    check(len(predictions) == 6240, 'Wrong prediction count')
    check(not predictions.duplicated(['context', 'method', 'k', 'row_id']).any(), 'Duplicate predictions')
    traces = {trace['context']: trace for trace in result['traces']}
    check(len(traces) == 24, 'Expected 24 selector contexts')
    expected_contexts = {'full_training': (expected_train.tolist(), [])}
    for i, (fit, val) in enumerate(KFold(5, shuffle=True, random_state=42).split(expected_train)):
        parent = expected_train[fit]
        expected_contexts[f'outer{i}'] = (parent.tolist(), expected_train[val].tolist())
        for j, (innerfit, innerval) in enumerate(KFold(3, shuffle=True, random_state=42).split(parent)):
            expected_contexts[f'outer{i}/inner/{j}'] = (parent[innerfit].tolist(), parent[innerval].tolist())
    for j, (fit, val) in enumerate(KFold(3, shuffle=True, random_state=42).split(expected_train)):
        expected_contexts[f'final/inner/{j}'] = (expected_train[fit].tolist(), expected_train[val].tolist())
    check(set(traces) == set(expected_contexts), 'Unexpected selector contexts')
    for context, trace in traces.items():
        fit, val = expected_contexts[context]
        check(trace['fit_row_ids'] == fit and trace.get('validation_row_ids', []) == val, 'Selector split mismatch')
        check(not set(fit) & set(val) and set(fit) <= train, 'Selector fit isolation')
        for method in fs.METHODS:
            order = trace['orders'][method]
            check(len(order) == len(set(order)) == 5 and set(order) == set(trace['encoded_names']), 'Order/name count')
            for k in range(1, 6):
                check(trace['subsets'][method][str(k)] == order[:k], 'Incorrect subset for k')
        for method in ['SFS', 'LassoCV']:
            for fold, (fitpos, valpos) in zip(trace['details'][method]['folds'],
                                            KFold(3, shuffle=True, random_state=42).split(fit)):
                check(fold['fit_row_ids'] == np.array(fit)[fitpos].tolist(), 'Inner fit mismatch')
                check(fold['validation_row_ids'] == np.array(fit)[valpos].tolist(), 'Inner validation mismatch')
        if replay:
            replay_lasso(trace, frame)
    for entry in result['audit']:
        context = entry['context']
        parent = context.split('/lasso/')[0].split('/sfs/')[0]
        check(set(entry['fit_row_ids']) <= set(traces[parent]['fit_row_ids']), 'Preprocessor outside training context')
        X = frame.loc[entry['fit_row_ids'], baseline.FEATURES]
        prep, scaler, _ = preprocessing(X)
        check(entry['encoded_names'] == prep.get_feature_names_out().tolist(), 'Encoded feature names')
        near(entry['numeric_medians'], X[baseline.NUMERIC].median().to_numpy(), 'Median leakage')
        near(entry['scaler_mean'], scaler.mean_, 'Scaler mean leakage')
        near(entry['scaler_scale'], scaler.scale_, 'Scaler scale leakage')
    replay_preps = {}
    for context, trace in traces.items():
        if context == 'full_training':
            continue
        prep, _, values = preprocessing(frame.loc[trace['fit_row_ids'], baseline.FEATURES])
        replay_preps[context] = (prep, values, prep.transform(frame.loc[trace['validation_row_ids'], baseline.FEATURES]))
    rows = result['comparison'] + result['tuning']
    check(len(rows) == 23 * 26, 'Missing method/k/fold records')
    for row in rows:
        trace = traces[row['context']]
        names = trace['encoded_names'] if row['method'] == 'All Features' else trace['orders'][row['method']][:row['k']]
        check(row['features'] == names and len(names) == row['k'], 'Record features/k mismatch')
        part = predictions[(predictions['context'] == row['context']) &
                           (predictions['method'] == row['method']) & (predictions['k'] == row['k'])]
        check(part['row_id'].tolist() == trace['validation_row_ids'], 'Prediction IDs/duplicates')
        near(part['actual'], frame.loc[part['row_id'], 'Profit'], 'Actual source mismatch')
        prep, training, validation = replay_preps[row['context']]
        indices = [prep.get_feature_names_out().tolist().index(name) for name in names]
        refit = LinearRegression().fit(training[:, indices], frame.loc[trace['fit_row_ids'], 'Profit'])
        near(part['prediction'], refit.predict(validation[:, indices]), 'Predictions not from selected LR columns')
        values = {'mae': mean_absolute_error(part['actual'], part['prediction']),
                  'mse': mean_squared_error(part['actual'], part['prediction']),
                  'rmse': np.sqrt(mean_squared_error(part['actual'], part['prediction'])),
                  'r2': r2_score(part['actual'], part['prediction'])}
        for metric, value in values.items():
            near(row[metric], value, 'Metric does not match real predictions')
    table = pd.DataFrame(result['comparison'])
    summary = pd.read_csv(directory / 'comparison.csv')
    for row in summary.to_dict('records'):
        part = table[(table['method'] == row['method']) & (table['k'] == row['k'])]
        check(len(part) == 5, 'Five comparison folds required')
        for metric in ['mae', 'mse', 'rmse', 'r2']:
            near(row[f'{metric}_mean'], part[metric].mean(), 'Summary mean mismatch')
            near(row[f'{metric}_std'], part[metric].std(ddof=0), 'Summary std mismatch')
    pd.testing.assert_frame_equal(summary, pd.DataFrame(result['comparison_summary']), check_exact=False)
    pd.testing.assert_frame_equal(summary, pd.read_csv(directory / 'plot_data.csv'))
    selections = pd.read_csv(directory / 'selected_features.csv')
    check(len(selections) == 600, 'Missing subset CSV records')
    for row in selections.to_dict('records'):
        trace = traces[row['context']]
        check(json.loads(row['features_json']) == trace['subsets'][row['method']][str(row['k'])], 'Subset CSV mismatch')
        check(json.loads(row['order_json']) == trace['orders'][row['method']], 'Order CSV mismatch')
        zeros = trace['details']['LassoCV']['zero_coefficient_names'] if row['method'] == 'LassoCV' else []
        check(json.loads(row['zero_padded_features_json']) == [name for name in json.loads(row['features_json']) if name in zeros], 'Zero-padding labels')
    for nested in result['nested']:
        inner = pd.DataFrame(result['tuning'])
        inner = inner[inner['context'].str.startswith(nested['selected_using'] + '/')]
        scores = inner.groupby(['method', 'k'])['rmse'].mean()
        best = min(scores.index, key=lambda key: (scores[key], key[1], key[0]))
        check(best == (nested['method'], nested['k']), 'Nested choice used wrong scores')
        original = next(row for row in result['comparison'] if row['context'] == nested['context']
                        and row['method'] == nested['method'] and row['k'] == nested['k'])
        near(nested['rmse'], original['rmse'], 'Nested outer score mismatch')
    final_scores = pd.read_csv(directory / 'final_selection.csv')
    final_rows = pd.DataFrame(result['tuning'])
    final_rows = final_rows[final_rows['context'].str.startswith('final/inner/')]
    for row in final_scores.to_dict('records'):
        group = final_rows[(final_rows['method'] == row['method']) & (final_rows['k'] == row['k'])]
        check(len(group) == 3, 'Final selection folds')
        for metric in ['mae', 'mse', 'rmse', 'r2']:
            near(row[f'{metric}_mean'], group[metric].mean(), 'Final summary mean')
            near(row[f'{metric}_std'], group[metric].std(ddof=0), 'Final summary std')
    pd.testing.assert_frame_equal(final_scores, pd.DataFrame(result['final_selection_summary']), check_exact=False)
    for metric in ['rmse', 'r2']:
        near(result['nested_summary'][metric]['mean'], np.mean([row[metric] for row in result['nested']]), 'Nested mean')
        near(result['nested_summary'][metric]['std'], np.std([row[metric] for row in result['nested']]), 'Nested std')
    choice = min(final_scores.to_dict('records'), key=lambda row: (row['rmse_mean'], row['k'], row['method']))
    frozen = read('frozen_selection.json')
    check((choice['method'], choice['k']) == (frozen['choice']['method'], frozen['choice']['k']), 'Final winner mismatch')
    check(frozen['choice'] == result['final_choice'], 'Frozen/JSON choice mismatch')
    method, k = choice['method'], choice['k']
    expected = traces['full_training']['encoded_names'] if method == 'All Features' else traces['full_training']['orders'][method][:k]
    check(frozen['choice']['features'] == expected, 'Frozen selected features')
    check(frozen['holdout_evaluations'] == 0, 'Holdout must stay unused')
    check(frozen['protocol_sha256'] == hashlib.sha256((directory / 'protocol.json').read_bytes()).hexdigest(), 'Protocol hash')
    with tempfile.TemporaryDirectory() as temp:
        fs.plot_curves(summary.to_dict('records'), Path(temp))
        for metric in ['rmse', 'r2']:
            name = f'features_vs_{metric}.png'
            check((directory / name).read_bytes() == (Path(temp) / name).read_bytes(), 'Chart differs from verified CSV')
    print('PASS: source/splits, 6240 predictions, 600 subsets, preprocessing, nested choices, CSV/JSON and both PNGs'
          + ('; all 24 real multi-alpha LassoCV paths independently replayed' if replay else ''))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--replay-lasso', action='store_true')
    args = parser.parse_args()
    verify(args.run_directory, args.source, args.replay_lasso)
