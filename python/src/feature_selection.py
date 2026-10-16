"""Training-only feature selection; original baseline and holdout remain untouched."""
import argparse
from dataclasses import dataclass
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import re
import warnings

import numpy as np
import pandas as pd
from sklearn.feature_selection import RFE, f_regression, r_regression
from sklearn.linear_model import Lasso, LassoCV, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning

import startups_baseline as baseline
import regression_workflow as workflow

METHODS = ['Pearson', 'F-Test', 'RFE', 'SFS', 'LassoCV']
ALPHAS = np.logspace(0, 5, 21).tolist()


def protocol():
    return {'version': 'DIC2-04-v1', 'seed': 42, 'test_size': 0.2,
            'comparison_folds': 5, 'selection_folds': 3, 'selector_folds': 3,
            'unit': 'encoded columns; State dummies are independent candidates',
            'ks': [1, 2, 3, 4, 5], 'methods': METHODS, 'final_estimator': 'LinearRegression',
            'alpha_grid': ALPHAS, 'lasso_tol': 1e-8, 'lasso_max_iter': 100000,
            'alpha_rule': 'minimum LassoCV mean fold MSE; exact ties prefer larger alpha',
            'ranking_rule': 'descending absolute score/coefficient, exact ties lexical name',
            'selection_rule': 'minimum mean fold RMSE, then smaller k, then lexical method',
            'holdout': 'NOT evaluated; baseline holdout already disclosed in Issue #3'}


@dataclass
class Prepared:
    preprocess: object
    scaler: object
    values: np.ndarray
    names: list

    def transform(self, X, names=None):
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Found unknown categories', category=UserWarning)
            values = self.preprocess.transform(X)
        table = pd.DataFrame(values, columns=self.names, index=X.index)
        return table.reindex(columns=names or self.names, fill_value=0).to_numpy()


def prepare(X, context, audit, config=baseline.CONFIG):
    for column in config.features:
        if X[column].isna().all():
            raise ValueError(f'Entirely missing training column {column} in {context}')
    preprocess = workflow.make_pipeline(config).named_steps['preprocess']
    values = preprocess.fit_transform(X)
    names = preprocess.get_feature_names_out().tolist()
    scaler = StandardScaler().fit(values)
    record = {'context': context, 'fit_row_ids': X.index.tolist(),
              'encoded_names': names,
              'numeric_medians': (preprocess.named_transformers_['numeric']
                                  .named_steps['imputer'].statistics_.tolist() if config.numeric else [])}
    if config.categorical:
        encoder = preprocess.named_transformers_[config.categorical_block].named_steps['encoder']
        if config.categorical_block == 'state' and config.categorical == ('State',):
            record.update({'state_categories': encoder.categories_[0].tolist(),
                           'state_reference': encoder.categories_[0][0]})
        else:
            record['categorical_schema'] = {
                name: {'categories': categories.tolist(), 'reference': categories[0]}
                for name, categories in zip(config.categorical, encoder.categories_)}
    record.update({'scaler_mean': scaler.mean_.tolist(), 'scaler_scale': scaler.scale_.tolist()})
    audit.append(record)
    return Prepared(preprocess, scaler, values, names)


def folds(X, n=3):
    return workflow.folds(X, n=n, seed=baseline.SEED)


def ranked(names, scores):
    return sorted(names, key=lambda name: (-float(scores[names.index(name)]), name))


def lasso_rank(X, y, prepared, context, audit, config=baseline.CONFIG, alphas=None):
    """Real multi-alpha LassoCV on disjoint, independently preprocessed fold blocks.

    Each CV split accesses only its own block. Explicit alphas avoid a global
    data-derived alpha grid. LassoCV's stacked-data refit is discarded; refit the
    chosen alpha on the actual local training design for meaningful coefficients.
    """
    blocks, targets, cv, records = [], [], [], []
    offset = 0
    for i, (fit, val) in enumerate(folds(X)):
        local = prepare(X.iloc[fit], f'{context}/lasso/{i}', audit, config)
        train_values = local.scaler.transform(local.values)
        validation_values = local.scaler.transform(local.transform(X.iloc[val]))
        # Column meanings may differ across blocks. Fits are independent, so
        # zero padding just supplies a common array width, never shared weights.
        width = len(prepared.names)
        if train_values.shape[1] > width:
            raise ValueError('Unexpected expanded inner-fold schema')
        block = np.vstack([train_values, validation_values])
        block = np.pad(block, ((0, 0), (0, width - block.shape[1])))
        blocks.append(block)
        targets.append(np.r_[y.iloc[fit], y.iloc[val]])
        cv.append((np.arange(offset, offset + len(fit)),
                   np.arange(offset + len(fit), offset + len(block))))
        records.append({'fold': i, 'fit_row_ids': X.iloc[fit].index.tolist(),
                        'validation_row_ids': X.iloc[val].index.tolist(),
                        'block_fit_indices': cv[-1][0].tolist(),
                        'block_validation_indices': cv[-1][1].tolist(),
                        'encoded_names': local.names})
        offset += len(block)
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        selector = LassoCV(alphas=ALPHAS if alphas is None else alphas, cv=cv, fit_intercept=True, max_iter=100000,
                           tol=1e-8, selection='cyclic', n_jobs=1).fit(np.vstack(blocks), np.concatenate(targets))
        model = Lasso(alpha=float(selector.alpha_), max_iter=100000, tol=1e-8,
                      selection='cyclic').fit(prepared.scaler.transform(prepared.values), y)
    return ranked(prepared.names, np.abs(model.coef_)), {
        'alpha': float(selector.alpha_), 'alphas': selector.alphas_.tolist(),
        'mse_path': selector.mse_path_.tolist(), 'folds': records,
        'standardized_coefficients': dict(zip(prepared.names, model.coef_.tolist())),
        'zero_coefficient_names': [name for name, coef in zip(prepared.names, model.coef_) if abs(coef) <= 1e-12],
        'refit': 'Lasso on full local training at LassoCV alpha; stacked refit coefficients not used'}


def sfs_rank(X, y, prepared, context, audit, config=baseline.CONFIG):
    # Cache fold-local transformations once, not a globally fitted design.
    blocks, fold_records = [], []
    for i, (fit, val) in enumerate(folds(X)):
        local = prepare(X.iloc[fit], f'{context}/sfs/{i}', audit, config)
        fold_records.append({'fold': i, 'fit_row_ids': X.iloc[fit].index.tolist(),
                             'validation_row_ids': X.iloc[val].index.tolist(),
                             'encoded_names': local.names,
                             'unavailable_candidates': sorted(set(prepared.names) - set(local.names))})
        blocks.append((local.transform(X.iloc[fit], prepared.names),
                       local.transform(X.iloc[val], prepared.names),
                       y.iloc[fit], y.iloc[val]))
    selected, steps = [], []
    while len(selected) < len(prepared.names):
        candidates = []
        for name in sorted(set(prepared.names) - set(selected)):
            subset = selected + [name]
            indices = [prepared.names.index(item) for item in subset]
            scores = []
            for train, val, target, actual in blocks:
                prediction = LinearRegression().fit(train[:, indices], target).predict(val[:, indices])
                scores.append(baseline.metrics(actual, prediction)['rmse'])
            candidates.append({'added': name, 'subset': subset, 'fold_rmse': scores,
                               'mean_rmse': float(np.mean(scores))})
        winner = min(candidates, key=lambda candidate: (candidate['mean_rmse'], candidate['added']))
        selected.append(winner['added'])
        steps.append({'k': len(selected), 'chosen': winner['added'], 'candidates': candidates})
    return selected, {'steps': steps, 'folds': fold_records, 'implementation': 'greedy forward, recomputed candidate CV each step'}


def fit_selectors(X, y, context, audit, config=baseline.CONFIG, alphas=None):
    prepared = prepare(X, context, audit, config)
    if config.expected_encoded_features is not None and len(prepared.names) != config.expected_encoded_features:
        if config.dataset_id == '50_startups':
            raise ValueError('Fixed k=1..5 requires three observed State levels in each selector training set')
        raise ValueError(f'Expected {config.expected_encoded_features} encoded features')
    values, names = prepared.values, prepared.names
    pearson = np.abs(r_regression(values, y, force_finite=True))
    f_scores = f_regression(values, y, force_finite=True)[0]
    recursive = RFE(LinearRegression(), n_features_to_select=1, step=1)
    recursive.fit(prepared.scaler.transform(values), y)
    rfe_order = sorted(names, key=lambda name: int(recursive.ranking_[names.index(name)]))
    sfs_order, sfs_trace = sfs_rank(X, y, prepared, context, audit, config)
    lasso_order, lasso_trace = lasso_rank(X, y, prepared, context, audit, config, alphas)
    orders = {'Pearson': ranked(names, pearson), 'F-Test': ranked(names, f_scores),
              'RFE': rfe_order, 'SFS': sfs_order, 'LassoCV': lasso_order}
    details = {'Pearson': {'absolute_r': dict(zip(names, pearson.tolist()))},
               'F-Test': {'f_scores': dict(zip(names, f_scores.tolist()))},
               'RFE': {'ranking': dict(zip(names, recursive.ranking_.tolist())),
                       'elimination_order': list(reversed(rfe_order[1:])), 'survivor': rfe_order[0],
                       'order_meaning': 'reverse elimination, not forward entry'},
               'SFS': sfs_trace, 'LassoCV': lasso_trace}
    return prepared, {'context': context, 'fit_row_ids': X.index.tolist(),
                      'encoded_names': names, 'orders': orders, 'details': details,
                      'subsets': {method: {str(k): order[:k] for k in range(1, len(names) + 1)}
                                  for method, order in orders.items()}}


def candidates(record):
    yield 'All Features', len(record['encoded_names']), record['encoded_names']
    for method in METHODS:
        for k in range(1, len(record['encoded_names']) + 1):
            yield method, k, record['orders'][method][:k]


def evaluate(X, y, fit, val, context, prepared, selection):
    records, predictions = [], []
    validation = prepared.transform(X.iloc[val])
    for method, k, names in candidates(selection):
        indices = [prepared.names.index(name) for name in names]
        estimator = LinearRegression().fit(prepared.values[:, indices], y.iloc[fit])
        predicted = estimator.predict(validation[:, indices])
        records.append({'context': context, 'method': method, 'k': k,
                        'features': names, **baseline.metrics(y.iloc[val], predicted)})
        predictions.extend({'context': context, 'method': method, 'k': k,
                            'row_id': int(row), 'actual': float(actual), 'prediction': float(pred)}
                           for row, actual, pred in zip(X.iloc[val].index, y.iloc[val], predicted))
    return records, predictions


def summarize(records):
    frame = pd.DataFrame(records)
    rows = []
    for (method, k), group in frame.groupby(['method', 'k'], sort=True):
        row = {'method': method, 'k': int(k), 'n_folds': len(group)}
        for metric in ['mae', 'mse', 'rmse', 'r2']:
            row[f'{metric}_mean'] = float(group[metric].mean())
            row[f'{metric}_std'] = float(group[metric].std(ddof=0))
        rows.append(row)
    return rows


def choose(summary):
    return min(summary, key=lambda row: (row['rmse_mean'], row['k'], row['method']))


def cv_candidates(X, y, n_folds, prefix, audit, traces, config=baseline.CONFIG, alphas=None):
    records, predictions = [], []
    for i, (fit, val) in enumerate(folds(X, n_folds)):
        context = f'{prefix}/{i}'
        prepared, selection = fit_selectors(X.iloc[fit], y.iloc[fit], context, audit, config, alphas)
        selection['validation_row_ids'] = X.iloc[val].index.tolist()
        traces.append(selection)
        scores, predicted = evaluate(X, y, fit, val, context, prepared, selection)
        records.extend(scores)
        predictions.extend(predicted)
    return records, predictions


def training_experiment(X, y, config=baseline.CONFIG, alphas=None):
    """Only local training rows enter this API. No holdout argument exists."""
    audit, traces, comparison, all_predictions, tuning, nested = [], [], [], [], [], []
    for outer, (fit, val) in enumerate(folds(X, 5)):
        local_X, local_y = X.iloc[fit], y.iloc[fit]
        inner, inner_predictions = cv_candidates(local_X, local_y, 3, f'outer{outer}/inner', audit, traces, config, alphas)
        choice = choose(summarize(inner))
        tuning.extend(inner)
        all_predictions.extend(inner_predictions)
        context = f'outer{outer}'
        prepared, selection = fit_selectors(local_X, local_y, context, audit, config, alphas)
        selection['validation_row_ids'] = X.iloc[val].index.tolist()
        traces.append(selection)
        scores, predicted = evaluate(X, y, fit, val, context, prepared, selection)
        comparison.extend(scores)
        all_predictions.extend(predicted)
        chosen = next(row for row in scores if row['method'] == choice['method'] and row['k'] == choice['k'])
        nested.append({**chosen, 'selection_cv_rmse': choice['rmse_mean'],
                       'selected_using': f'outer{outer}/inner', 'selection_folds': 3})
        print(f'RUN outer fold {outer + 1}/5 complete', flush=True)
    final_scores, final_predictions = cv_candidates(X, y, 3, 'final/inner', audit, traces, config, alphas)
    tuning.extend(final_scores)
    all_predictions.extend(final_predictions)
    final_summary = summarize(final_scores)
    choice = choose(final_summary)
    _, final = fit_selectors(X, y, 'full_training', audit, config, alphas)
    traces.append(final)
    features = (final['encoded_names'] if choice['method'] == 'All Features'
                else final['subsets'][choice['method']][str(choice['k'])])
    return {'comparison': comparison, 'comparison_summary': summarize(comparison),
            'tuning': tuning, 'final_selection_summary': final_summary, 'nested': nested,
            'nested_summary': {metric: {'mean': float(np.mean([row[metric] for row in nested])),
                                         'std': float(np.std([row[metric] for row in nested]))}
                               for metric in ['rmse', 'r2']},
            'final_choice': {**choice, 'features': features, 'selection_cv': '3-fold full training'},
            'traces': traces, 'audit': audit, 'predictions': all_predictions}


def plot_curves(summary, directory, xlabel='Number of encoded features (State dummies separate)',
                units='source units'):
    table = pd.DataFrame(summary)
    for metric in ['rmse', 'r2']:
        figure, axis = baseline.plt.subplots(figsize=(9, 6))
        for method, marker, style in zip(METHODS, ['o', 's', '^', 'D', 'x'], ['-', '--', '-.', ':', '-']):
            rows = table[table['method'] == method].sort_values('k')
            axis.errorbar(rows['k'], rows[f'{metric}_mean'], yerr=rows[f'{metric}_std'],
                          marker=marker, linestyle=style, capsize=3, label=method, alpha=0.8)
        full = table[table['method'] == 'All Features'].iloc[0]
        axis.axhline(full[f'{metric}_mean'], linestyle='--', color='black', label=f"All Features (k={int(full['k'])})")
        axis.set(xlabel=xlabel,
                 ylabel=f'CV RMSE ({units})' if metric == 'rmse' else 'CV R²',
                 title='Fixed method/k: 5-fold training CV (error bars: fold std)', xticks=range(1, int(table['k'].max()) + 1))
        axis.legend()
        baseline.save_plot(directory / f'features_vs_{metric}.png', figure)


def run(frame, provenance, output_root, run_id):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', run_id):
        raise ValueError('Invalid run-id')
    baseline.validate_data(frame)
    train_ids, test_ids = workflow.split_row_ids(frame.index, test_size=0.2, seed=baseline.SEED)
    directory = Path(output_root) / '50_startups/feature_selection' / run_id
    directory.mkdir(parents=True, exist_ok=False)
    baseline.write_json(directory / 'protocol.json', protocol())
    baseline.write_json(directory / 'provenance.json', provenance)
    baseline.write_json(directory / 'environment.json', {'python': platform.python_version(),
                         'packages': {name: version(name) for name in
                                      ['numpy', 'pandas', 'scikit-learn', 'matplotlib', 'scipy']}})
    baseline.write_json(directory / 'splits.json', {'train_row_ids': train_ids.tolist(),
                                                   'test_row_ids': test_ids.tolist()})
    try:
        result = training_experiment(frame.loc[train_ids, baseline.FEATURES], frame.loc[train_ids, baseline.TARGET])
        predictions = result.pop('predictions')
        pd.DataFrame(predictions).to_csv(directory / 'predictions.csv', index=False)
        pd.DataFrame(result['comparison_summary']).to_csv(directory / 'comparison.csv', index=False)
        pd.DataFrame(result['comparison_summary']).to_csv(directory / 'plot_data.csv', index=False)
        pd.DataFrame(result['final_selection_summary']).to_csv(directory / 'final_selection.csv', index=False)
        subset_rows = [{'context': trace['context'], 'method': method, 'k': k,
                        'features_json': json.dumps(order[:k]), 'order_json': json.dumps(order),
                        'order_kind': 'reverse elimination' if method == 'RFE' else
                        ('greedy entry' if method == 'SFS' else 'descending score; lexical ties'),
                        'zero_padded_features_json': json.dumps([name for name in order[:k]
                            if method == 'LassoCV' and name in trace['details']['LassoCV']['zero_coefficient_names']])}
                       for trace in result['traces'] for method, order in trace['orders'].items()
                       for k in range(1, 6)]
        pd.DataFrame(subset_rows).to_csv(directory / 'selected_features.csv', index=False)
        baseline.write_json(directory / 'results.json', result)
        baseline.write_json(directory / 'frozen_selection.json', {
            'protocol_sha256': hashlib.sha256((directory / 'protocol.json').read_bytes()).hexdigest(),
            'choice': result['final_choice'], 'holdout_evaluations': 0,
            'status': 'FROZEN_FOR_HUMAN_REVIEW; no new independent test claim'})
        plot_curves(result['comparison_summary'], directory)
        baseline.write_json(directory / 'status.json', {'status': 'TECHNICAL_COMPLETE', 'human_review': 'pending'})
    except Exception as error:
        baseline.write_json(directory / 'status.json', {'status': 'FAIL', 'reason': str(error)})
        raise
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--cache-dir', type=Path, default=baseline.ROOT / 'data/50_startups')
    parser.add_argument('--output-root', type=Path, default=baseline.ROOT / 'outputs')
    args = parser.parse_args()
    frame, source = baseline.acquire_data(args.cache_dir)
    print(json.dumps({'status': 'TECHNICAL_COMPLETE', 'output': str(run(frame, source, args.output_root, args.run_id))}))


if __name__ == '__main__':
    main()
