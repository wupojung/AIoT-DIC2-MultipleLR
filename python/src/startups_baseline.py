"""Reproducible 50 Startups baseline; no feature selection or Web integration."""
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
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[2]
NUMERIC = ['R&D Spend', 'Administration', 'Marketing Spend']
FEATURES = NUMERIC + ['State']
TARGET = 'Profit'
SEED = 42
MANIFEST = ROOT / 'data/50_startups_manifest.json'


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n',
                    encoding='utf-8')


def acquire_data(cache_dir):
    """Fetch only the pinned source; verify cached/downloaded bytes before parsing."""
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    cache_dir = Path(cache_dir)
    path = cache_dir / '50_Startups.csv'
    if path.exists():
        payload = path.read_bytes()
    else:
        with urllib.request.urlopen(manifest['url'], timeout=30) as response:
            payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != manifest['sha256']:
        raise ValueError('Source SHA-256 mismatch; refusing to analyze changed data')
    frame = pd.read_csv(io.BytesIO(payload))
    validate_data(frame)
    if not path.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        write_json(cache_dir / 'retrieval.json', {
            'url': manifest['url'], 'sha256': digest,
            'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
        })
    retrieval = cache_dir / 'retrieval.json'
    metadata = dict(manifest)
    metadata['acquisition'] = (json.loads(retrieval.read_text(encoding='utf-8'))
                               if retrieval.exists() else {'retrieved_at_utc': None,
                                                           'note': 'Pre-existing verified cache; retrieval time unknown'})
    return frame, metadata


def validate_data(frame):
    """Fail explicitly rather than silently changing schema, rows or target."""
    if list(frame.columns) != FEATURES + [TARGET] or len(frame) != 50:
        raise ValueError('Expected 50 rows with four predictors and Profit in canonical order')
    if not frame.index.equals(pd.RangeIndex(50)):
        raise ValueError('Expected original zero-based CSV row IDs')
    for column in NUMERIC + [TARGET]:
        if not pd.api.types.is_numeric_dtype(frame[column]):
            raise ValueError(f'Non-numeric column: {column}')
        values = frame[column].to_numpy(dtype=float)
        if np.isinf(values).any() or frame[column].isna().all():
            raise ValueError(f'Infinite or entirely missing column: {column}')
    if frame[TARGET].isna().any():
        raise ValueError('Missing target Profit is not permitted')
    states = frame['State'].dropna()
    if not states.map(lambda value: isinstance(value, str) and bool(value.strip())).all():
        raise ValueError('State must contain nonblank strings or missing values')
    if frame['State'].isna().all():
        raise ValueError('Entirely missing State')
    if frame.duplicated().any() or frame.duplicated(subset=FEATURES).any():
        raise ValueError('Duplicate rows/predictor groups require a split-policy review')


def make_pipeline():
    numeric = Pipeline([('imputer', SimpleImputer(strategy='median'))])
    categorical = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=False)),
    ])
    return Pipeline([
        ('preprocess', ColumnTransformer([
            ('numeric', numeric, NUMERIC), ('state', categorical, ['State']),
        ])),
        ('regressor', LinearRegression(fit_intercept=True)),
    ])


def metrics(y, prediction):
    y, prediction = np.asarray(y, dtype=float), np.asarray(prediction, dtype=float)
    if y.shape != prediction.shape or not len(y) or not np.isfinite(prediction).all():
        raise ValueError('Invalid predictions')
    residual = y - prediction
    mse = float(np.mean(residual ** 2))
    denominator = float(np.sum((y - np.mean(y)) ** 2))
    return {'mae': float(np.mean(np.abs(residual))), 'mse': mse,
            'rmse': float(np.sqrt(mse)),
            'r2': float(1 - np.sum(residual ** 2) / denominator)
            if len(y) >= 2 and denominator > 0 else None,
            'r2_undefined_reason': None if len(y) >= 2 and denominator > 0
            else 'Fewer than two samples or constant target', 'n': len(y)}


def fit_checked(pipeline, X, y):
    for column in FEATURES:
        if X[column].isna().all():
            raise ValueError(f'Entirely missing training-fold column: {column}')
    return pipeline.fit(X, y)


def fitted_schema(pipeline):
    prep = pipeline.named_steps['preprocess']
    encoder = prep.named_transformers_['state'].named_steps['encoder']
    return {
        'numeric_training_medians': dict(zip(NUMERIC, prep.named_transformers_['numeric']
                                            .named_steps['imputer'].statistics_.tolist())),
        'state_training_mode': prep.named_transformers_['state'].named_steps['imputer']
                              .statistics_[0],
        'state_categories': encoder.categories_[0].tolist(),
        'state_reference': encoder.categories_[0][encoder.drop_idx_[0]],
        'encoded_feature_names': prep.get_feature_names_out().tolist(),
        'original_feature_groups': NUMERIC + ['State'],
    }


def predict_checked(pipeline, X):
    schema = fitted_schema(pipeline)
    unknown = X['State'].notna() & ~X['State'].isin(schema['state_categories'])
    # sklearn warns about all-zero unknowns; the exact count is exported explicitly.
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Found unknown categories', category=UserWarning)
        prediction = pipeline.predict(X)
    return prediction, int(unknown.sum())


def save_plot(path, figure):
    figure.tight_layout()
    figure.savefig(path, dpi=140, metadata={'Software': 'DIC-2 baseline'})
    plt.close(figure)


def export_eda(frame, train_ids, directory):
    train = frame.loc[train_ids]
    write_json(directory / 'data_quality.json', {
        'scope': 'Full-data structural integrity only; no target-directed selection',
        'rows': len(frame), 'raw_predictors': FEATURES, 'target': TARGET,
        'dtypes': frame.dtypes.astype(str).to_dict(),
        'missing': frame.isna().sum().astype(int).to_dict(),
        'duplicate_rows': int(frame.duplicated().sum()),
        'duplicate_predictor_groups': int(frame.duplicated(subset=FEATURES).sum()),
        'independence_limit': 'No company IDs/time metadata; independent-row teaching assumption unverified',
    })
    train.describe(include='all').to_csv(directory / 'train_descriptive_statistics.csv')
    correlation = train[NUMERIC + [TARGET]].corr()
    correlation.to_csv(directory / 'train_correlation.csv')
    figure, axes = plt.subplots(2, 2, figsize=(10, 7))
    for axis, column in zip(axes.flat, NUMERIC + [TARGET]):
        axis.hist(train[column].dropna(), bins=10, edgecolor='white')
        axis.set(title=column, xlabel='Source units (currency/period unverified)', ylabel='Train count')
    figure.suptitle('Training data distributions only')
    save_plot(directory / 'train_distributions.png', figure)
    figure, axis = plt.subplots(figsize=(7, 6))
    image = axis.imshow(correlation, vmin=-1, vmax=1, cmap='RdBu_r')
    axis.set_xticks(range(4), correlation.columns, rotation=30, ha='right')
    axis.set_yticks(range(4), correlation.columns)
    axis.set_title('Training Pearson correlation (not causal)')
    figure.colorbar(image, ax=axis)
    save_plot(directory / 'train_correlation.png', figure)
    figure, axis = plt.subplots(figsize=(7, 5))
    counts = train['State'].fillna('(missing)').value_counts().sort_index()
    axis.bar(counts.index, counts.values)
    axis.set(title='State counts — training only', ylabel='Train count')
    save_plot(directory / 'train_state_counts.png', figure)


def export_diagnostics(y, prediction, directory):
    residual = y - prediction
    figure, axis = plt.subplots(figsize=(6, 6))
    axis.scatter(y, prediction)
    low, high = min(y.min(), prediction.min()), max(y.max(), prediction.max())
    margin = (high - low) * 0.05 or 1.0
    low, high = low - margin, high + margin
    axis.plot([low, high], [low, high], '--', color='gray')
    axis.set(xlabel='Actual Profit (source units)', ylabel='Predicted Profit (source units)',
             title='Frozen holdout — actual vs predicted', xlim=(low, high), ylim=(low, high))
    axis.set_aspect('equal', adjustable='box')
    save_plot(directory / 'holdout_actual_predicted.png', figure)
    figure, axis = plt.subplots(figsize=(7, 5))
    axis.scatter(prediction, residual)
    axis.axhline(0, linestyle='--', color='gray')
    axis.set(xlabel='Predicted Profit (source units)', ylabel='Actual minus predicted (source units)',
             title='Frozen holdout residuals')
    save_plot(directory / 'holdout_residuals.png', figure)
    figure, axis = plt.subplots(figsize=(7, 5))
    axis.hist(residual, bins=6, edgecolor='white')
    axis.set(xlabel='Residual (source units)', ylabel='Holdout count',
             title='Frozen holdout residual distribution')
    save_plot(directory / 'holdout_residual_distribution.png', figure)


def run_analysis(frame, provenance, output_root, run_id):
    """Run a predeclared baseline once, refusing to overwrite an existing run."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', run_id):
        raise ValueError('run-id must be 1–64 ASCII letters/digits/hyphens/underscores')
    validate_data(frame)
    train_ids, test_ids = train_test_split(frame.index.to_numpy(), test_size=0.2,
                                          random_state=SEED, shuffle=True)
    fold_ids = list(KFold(n_splits=5, shuffle=True, random_state=SEED).split(train_ids))
    for fit, validation in fold_ids:
        for ids in [train_ids[fit], train_ids[validation], test_ids]:
            if len(ids) < 2 or frame.loc[ids, TARGET].nunique() < 2:
                raise ValueError('Constant/insufficient partition target; review split protocol')
    directory = Path(output_root) / '50_startups' / run_id
    directory.mkdir(parents=True, exist_ok=False)
    try:
        config = {'protocol': 'DIC2-03-baseline-v1', 'seed': SEED, 'test_size': 0.2,
                  'cv': {'n_splits': 5, 'shuffle': True, 'random_state': SEED},
                  'features': FEATURES, 'target': TARGET, 'numeric_imputer': 'median',
                  'state_imputer': 'most_frequent', 'state_encoding': 'onehot/drop-first/ignore-unknown',
                  'estimator': 'LinearRegression(fit_intercept=True)',
                  'reference': 'DummyRegressor(strategy=mean)', 'selection': 'none',
                  'units': 'Source numerical units; currency and reporting period unverified'}
        write_json(directory / 'config.json', config)
        write_json(directory / 'provenance.json', provenance)
        write_json(directory / 'environment.json', {'python': platform.python_version(),
                   'packages': {name: version(name) for name in
                                ['numpy', 'pandas', 'scikit-learn', 'matplotlib', 'scipy']}})
        splits = {'train_row_ids': train_ids.tolist(), 'test_row_ids': test_ids.tolist(),
                  'folds': [{'fold': i, 'fit_row_ids': train_ids[fit].tolist(),
                             'validation_row_ids': train_ids[val].tolist()}
                            for i, (fit, val) in enumerate(fold_ids)]}
        write_json(directory / 'splits.json', splits)
        export_eda(frame, train_ids, directory)
        X, y = frame[FEATURES], frame[TARGET]
        fold_results, cv_predictions = [], []
        for i, (fit, val) in enumerate(fold_ids):
            fit_ids, val_ids = train_ids[fit], train_ids[val]
            pipeline = fit_checked(make_pipeline(), X.loc[fit_ids], y.loc[fit_ids])
            prediction, unknown = predict_checked(pipeline, X.loc[val_ids])
            dummy = DummyRegressor(strategy='mean').fit(X.loc[fit_ids], y.loc[fit_ids])
            dummy_prediction = dummy.predict(X.loc[val_ids])
            fold_results.append({'fold': i, 'linear_regression': metrics(y.loc[val_ids], prediction),
                                 'dummy_mean': metrics(y.loc[val_ids], dummy_prediction),
                                 'unknown_state_count': unknown, 'preprocessing': fitted_schema(pipeline)})
            cv_predictions.extend({'fold': i, 'row_id': int(row), 'actual': float(actual),
                                   'linear_prediction': float(pred), 'dummy_prediction': float(base)}
                                  for row, actual, pred, base in
                                  zip(val_ids, y.loc[val_ids], prediction, dummy_prediction))
        summary = {}
        for model in ['linear_regression', 'dummy_mean']:
            summary[model] = {metric: {'mean': float(np.mean([fold[model][metric] for fold in fold_results])),
                                      'std_ddof0': float(np.std([fold[model][metric] for fold in fold_results]))}
                              for metric in ['mae', 'mse', 'rmse', 'r2']}
        pipeline = fit_checked(make_pipeline(), X.loc[train_ids], y.loc[train_ids])
        schema = fitted_schema(pipeline)
        regressor = pipeline.named_steps['regressor']
        write_json(directory / 'fitted_model.json', {**schema,
                   'coefficients': regressor.coef_.tolist(), 'intercept': float(regressor.intercept_)})
        pd.DataFrame(cv_predictions).to_csv(directory / 'train_cv_predictions.csv', index=False)
        write_json(directory / 'training_cv.json', {'folds': fold_results, 'summary': summary})
        # Written before any holdout predictions: no candidate/feature selection follows.
        write_json(directory / 'frozen_plan.json', {'config_sha256': hashlib.sha256(
                   (directory / 'config.json').read_bytes()).hexdigest(),
                   'holdout_policy': 'One evaluation per declared run; repeated runs verify reproducibility, not tuning',
                   'candidate': 'All four raw features; no selected k', 'status': 'frozen'})
        prediction, unknown = predict_checked(pipeline, X.loc[test_ids])
        dummy = DummyRegressor(strategy='mean').fit(X.loc[train_ids], y.loc[train_ids])
        dummy_prediction = dummy.predict(X.loc[test_ids])
        holdout = {'linear_regression': metrics(y.loc[test_ids], prediction),
                   'dummy_mean': metrics(y.loc[test_ids], dummy_prediction), 'unknown_state_count': unknown}
        pd.DataFrame({'row_id': test_ids, 'actual': y.loc[test_ids].to_numpy(),
                      'linear_prediction': prediction, 'residual': y.loc[test_ids].to_numpy() - prediction,
                      'dummy_prediction': dummy_prediction}).to_csv(directory / 'holdout_predictions.csv', index=False)
        write_json(directory / 'metrics.json', {'train_cv': summary, 'holdout': holdout})
        export_diagnostics(y.loc[test_ids].to_numpy(), prediction, directory)
        (directory / 'REPORT.md').write_text(
            '# 50 Startups baseline\n\nTechnical execution complete; human CRISP-DM review pending.\n'
            '40 training / 10 holdout rows; five training folds; no feature selection.\n'
            'See metrics.json, train_cv_predictions.csv and holdout_predictions.csv for measured results.\n'
            'EDA is training-only; data_quality.json is full-source structural audit.\n'
            'Units/currency/period and original collection/independent-company provenance are unverified.\n'
            'Repository MIT notice does not independently establish original dataset rights.\n'
            'Small teaching sample; no causal or deployment claim. Unknown State is encoded as all zeros\n'
            'and counted; this may coincide with the reference category.\n', encoding='utf-8')
        write_json(directory / 'status.json', {'status': 'TECHNICAL_COMPLETE',
                   'human_phase_review': 'pending', 'holdout_evaluations_per_estimator': 1})
    except Exception as error:
        write_json(directory / 'status.json', {'status': 'FAIL', 'reason': str(error)})
        raise
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, default=ROOT / 'data/50_startups')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'outputs')
    parser.add_argument('--run-id', required=True, help='New run name; existing runs are never overwritten')
    args = parser.parse_args()
    frame, provenance = acquire_data(args.cache_dir)
    directory = run_analysis(frame, provenance, args.output_root, args.run_id)
    print(json.dumps({'status': 'TECHNICAL_COMPLETE', 'output': str(directory)}))


if __name__ == '__main__':
    main()
