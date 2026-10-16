"""Independently recompute exported metrics and check row/source integrity."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def check(condition, message):
    if not condition:
        raise ValueError(message)


def compare_metrics(actual, predicted, reported):
    expected = {'mae': mean_absolute_error(actual, predicted),
                'mse': mean_squared_error(actual, predicted),
                'rmse': np.sqrt(mean_squared_error(actual, predicted)),
                'r2': r2_score(actual, predicted)}
    for key, value in expected.items():
        check(np.isclose(reported[key], value, rtol=1e-9, atol=1e-8), f'Metric mismatch: {key}')
    check(reported['n'] == len(actual), 'Metric sample count mismatch')


def verify(directory, source):
    def read(name):
        return json.loads((directory / name).read_text(encoding='utf-8'))

    provenance = read('provenance.json')
    check(hashlib.sha256(source.read_bytes()).hexdigest() == provenance['sha256'], 'Source hash mismatch')
    frame = pd.read_csv(source)
    split = read('splits.json')
    train, test = set(split['train_row_ids']), set(split['test_row_ids'])
    check(len(train) == 40 and len(test) == 10 and not train & test, 'Invalid train/test split')
    check(train | test == set(range(len(frame))), 'Missing/extra source row IDs')
    report = read('metrics.json')
    holdout = pd.read_csv(directory / 'holdout_predictions.csv')
    check(holdout['row_id'].tolist() == split['test_row_ids'], 'Holdout row IDs differ')
    check(np.allclose(holdout['actual'], frame.loc[holdout['row_id'], 'Profit']), 'Holdout actual mismatch')
    check(np.allclose(holdout['residual'], holdout['actual'] - holdout['linear_prediction']), 'Residual mismatch')
    check(np.allclose(holdout['dummy_prediction'], frame.loc[list(train), 'Profit'].mean()), 'Dummy fit leaked')
    for model, column in [('linear_regression', 'linear_prediction'), ('dummy_mean', 'dummy_prediction')]:
        compare_metrics(holdout['actual'], holdout[column], report['holdout'][model])
    cv = pd.read_csv(directory / 'train_cv_predictions.csv')
    fold_results = read('training_cv.json')['folds']
    seen = []
    check(len(split['folds']) == len(fold_results) == 5, 'Expected five folds')
    for fold, result in zip(split['folds'], fold_results):
        fit, val = set(fold['fit_row_ids']), set(fold['validation_row_ids'])
        check(not fit & val and fit | val == train, 'Fold isolation failed')
        seen.extend(val)
        part = cv[cv['fold'] == fold['fold']]
        check(part['row_id'].tolist() == fold['validation_row_ids'], 'CV row ID mismatch')
        check(np.allclose(part['actual'], frame.loc[part['row_id'], 'Profit']), 'CV actual mismatch')
        check(np.allclose(part['dummy_prediction'], frame.loc[list(fit), 'Profit'].mean()), 'CV Dummy fit leaked')
        for column, median in result['preprocessing']['numeric_training_medians'].items():
            check(np.isclose(median, frame.loc[list(fit), column].median()), 'Fold imputer mismatch')
        for model, column in [('linear_regression', 'linear_prediction'), ('dummy_mean', 'dummy_prediction')]:
            compare_metrics(part['actual'], part[column], result[model])
    check(sorted(seen) == sorted(train), 'Training rows must be validated exactly once')
    for model in ['linear_regression', 'dummy_mean']:
        for metric in ['mae', 'mse', 'rmse', 'r2']:
            values = [fold[model][metric] for fold in fold_results]
            summary = report['train_cv'][model][metric]
            check(np.isclose(summary['mean'], np.mean(values)), 'CV mean mismatch')
            check(np.isclose(summary['std_ddof0'], np.std(values)), 'CV std mismatch')
    train_frame = frame.loc[split['train_row_ids']]
    exported = pd.read_csv(directory / 'train_correlation.csv', index_col=0)
    check(np.allclose(exported, train_frame[exported.columns].corr()), 'Training-only correlation mismatch')
    frozen = read('frozen_plan.json')
    check(frozen['config_sha256'] == hashlib.sha256((directory / 'config.json').read_bytes()).hexdigest(),
          'Frozen config hash mismatch')
    check(read('status.json')['status'] == 'TECHNICAL_COMPLETE', 'Run did not complete')
    check(len(list(directory.glob('*.png'))) == 6, 'Expected six charts')
    for image in directory.glob('*.png'):
        check(image.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n', 'Invalid PNG')
    print('PASS: source hash, 40/10 split, five folds, CV/holdout metrics, train-only correlation, six PNGs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    verify(args.run_directory, args.source)
