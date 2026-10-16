"""Small shared building blocks; dataset policy and I/O stay with each caller."""
from dataclasses import dataclass
import json
import re

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


@dataclass(frozen=True)
class DatasetConfig:
    dataset_id: str
    target: str
    numeric: tuple[str, ...]
    categorical: tuple[str, ...]
    expected_rows: int
    raw_columns: tuple[str, ...]
    excluded: tuple[str, ...] = ()
    categorical_block: str = 'categorical'
    expected_encoded_features: int | None = None

    def __post_init__(self):
        if not re.fullmatch(r'[a-z0-9][a-z0-9_]*', self.dataset_id):
            raise ValueError('Invalid dataset_id')
        if self.expected_rows < 1 or not self.features:
            raise ValueError('Expected rows and predictors must be nonempty')
        if len(set(self.features)) != len(self.features):
            raise ValueError('Predictor roles must be disjoint and unique')
        if self.target in self.features or set(self.features) & set(self.excluded):
            raise ValueError('Target/excluded columns must not enter predictors')
        expected = set(self.features) | set(self.excluded) | {self.target}
        if set(self.raw_columns) != expected or len(set(self.raw_columns)) != len(self.raw_columns):
            raise ValueError('Raw schema must cover predictors, exclusions and target exactly')
        if self.categorical_block in {'numeric', 'remainder'}:
            raise ValueError('Categorical transformer name conflicts with another block')

    @property
    def features(self):
        return self.numeric + self.categorical


def validate_data(frame, config):
    """Source checks do not select variables or modify observations."""
    if list(frame.columns) != list(config.raw_columns) or len(frame) != config.expected_rows:
        raise ValueError(f'Expected {config.expected_rows} rows with canonical {config.dataset_id} schema')
    if not frame.index.equals(pd.RangeIndex(config.expected_rows)):
        raise ValueError('Expected original zero-based source row IDs')
    for column in config.numeric + (config.target,):
        if not pd.api.types.is_numeric_dtype(frame[column]):
            raise ValueError(f'Non-numeric column: {column}')
        values = frame[column].to_numpy(dtype=float)
        if np.isinf(values).any() or frame[column].isna().all():
            raise ValueError(f'Infinite or entirely missing column: {column}')
    if frame[config.target].isna().any():
        raise ValueError(f'Missing target {config.target} is not permitted')
    for column in config.categorical:
        if not frame[column].dropna().map(lambda value: isinstance(value, str) and bool(value.strip())).all():
            raise ValueError(f'{column} must contain nonblank strings or missing values')
        if frame[column].isna().all():
            raise ValueError(f'Entirely missing {column}')
    if frame.duplicated().any() or frame.duplicated(subset=list(config.features)).any():
        raise ValueError('Duplicate rows/predictor groups require a split-policy review')


def make_pipeline(config):
    transformers = []
    if config.numeric:
        numeric = Pipeline([('imputer', SimpleImputer(strategy='median'))])
        transformers.append(('numeric', numeric, list(config.numeric)))
    if config.categorical:
        categorical = Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('encoder', OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=False)),
        ])
        transformers.append((config.categorical_block, categorical, list(config.categorical)))
    return Pipeline([
        ('preprocess', ColumnTransformer(transformers)),
        ('regressor', LinearRegression(fit_intercept=True)),
    ])


def split_row_ids(row_ids, test_size=0.2, seed=42):
    return train_test_split(np.asarray(row_ids), test_size=test_size, random_state=seed, shuffle=True)


def folds(rows, n=3, seed=42):
    return list(KFold(n_splits=n, shuffle=True, random_state=seed).split(rows))


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


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n',
                    encoding='utf-8')
