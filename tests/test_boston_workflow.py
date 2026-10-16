"""Critical Boston policy and source guards; no network access in unit tests."""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python/src'))
import boston_workflow as boston
import regression_workflow as workflow


class BostonGuards(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        self.frame = pd.DataFrame(rng.uniform(1, 10, (506, 14)), columns=boston.COLUMNS)
        self.frame['CHAS'] = rng.integers(0, 2, 506)

    def test_source_hash_and_schema_are_checked_before_use(self):
        raw = ('506,13,,,,,,,,,,,,\n' + self.frame.to_csv(index=False)).encode()
        manifest = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                    'git_blob': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}
        parsed = boston.parse_source(raw, manifest)
        self.assertEqual(parsed.shape, (506, 14))
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            boston.parse_source(raw + b'\n', manifest)
        with self.assertRaises(ValueError):
            boston.validate(parsed.rename(columns={'B': 'other'}))

    def test_excluded_b_is_validated_but_never_used_for_prediction(self):
        boston.validate(self.frame)
        train, test = workflow.split_row_ids(self.frame.index)
        X = self.frame.loc[train, list(boston.CONFIG.features)]
        model = workflow.make_pipeline(boston.CONFIG).fit(X, self.frame.loc[train, 'MEDV'])
        original = model.predict(self.frame.loc[test])
        altered = self.frame.loc[test].copy()
        altered['B'] = -1e9
        altered['MEDV'] = 1e9
        np.testing.assert_array_equal(original, model.predict(altered))
        self.frame['B'] = np.nan
        with self.assertRaises(ValueError):
            boston.validate(self.frame)

    def test_training_only_imputation_and_fixed_boston_protocol(self):
        train, test = workflow.split_row_ids(self.frame.index)
        model = workflow.make_pipeline(boston.CONFIG).fit(self.frame.loc[train], self.frame.loc[train, 'MEDV'])
        medians = model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['imputer'].statistics_
        np.testing.assert_allclose(medians, self.frame.loc[train, list(boston.CONFIG.features)].median())
        self.assertEqual(len(boston.CONFIG.features), 12)
        self.assertNotIn('B', boston.CONFIG.features)
        self.assertEqual(boston.protocol()['alpha_grid'], np.logspace(-4, 2, 21).tolist())
        self.frame.loc[0, 'CHAS'] = 2
        with self.assertRaises(ValueError):
            boston.validate(self.frame)
