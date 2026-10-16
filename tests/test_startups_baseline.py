"""Offline tests use synthetic teaching-shaped data, never published as real results."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python/src'))
import startups_baseline as baseline
import verify_startups_run


def fixture():
    rng = np.random.default_rng(918)
    frame = pd.DataFrame(rng.uniform(1, 100, size=(50, 3)), columns=baseline.NUMERIC)
    frame['State'] = ['A', 'B', 'C', 'A', 'B'] * 10
    frame['Profit'] = 5 + frame['R&D Spend'] * 2 - frame['Administration'] + rng.normal(0, 2, 50)
    return frame


class BaselineUnitTests(unittest.TestCase):
    def test_metrics_independent_known_answer_and_undefined_r2(self):
        result = baseline.metrics([1, 2, 3], [2, 2, 2])
        self.assertAlmostEqual(result['mae'], 2 / 3)
        self.assertAlmostEqual(result['mse'], 2 / 3)
        self.assertAlmostEqual(result['rmse'], np.sqrt(2 / 3))
        self.assertAlmostEqual(result['r2'], 0)
        self.assertIsNone(baseline.metrics([2, 2], [1, 1])['r2'])
        self.assertIsNone(baseline.metrics([2], [1])['r2'])

    def test_reject_bad_source_schema_target_and_duplicates(self):
        for kind in ['missing_target', 'wrong_schema', 'duplicate', 'infinity', 'all_empty', 'bad_numeric', 'blank_state']:
            frame = fixture()
            if kind == 'missing_target': frame.loc[0, 'Profit'] = np.nan
            if kind == 'wrong_schema': frame = frame.rename(columns={'Profit': 'Other'})
            if kind == 'duplicate': frame.loc[1] = frame.loc[0]
            if kind == 'infinity': frame.loc[0, 'Profit'] = np.inf
            if kind == 'all_empty': frame['State'] = np.nan
            if kind == 'bad_numeric': frame['R&D Spend'] = 'oops'
            if kind == 'blank_state': frame.loc[0, 'State'] = ' '
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                baseline.validate_data(frame)

    def test_imputation_and_encoding_do_not_learn_validation_values(self):
        frame = fixture()
        frame.loc[0, 'R&D Spend'] = np.nan
        fit_ids = list(range(40))
        frame.loc[40:, 'R&D Spend'] = 1e12
        frame.loc[40:, 'State'] = 'VALIDATION_ONLY'
        model = baseline.fit_checked(baseline.make_pipeline(), frame.loc[fit_ids, baseline.FEATURES],
                                     frame.loc[fit_ids, 'Profit'])
        state = baseline.fitted_schema(model)
        self.assertAlmostEqual(state['numeric_training_medians']['R&D Spend'],
                               frame.loc[fit_ids, 'R&D Spend'].median())
        self.assertNotIn('VALIDATION_ONLY', state['state_categories'])
        predictions, unknown = baseline.predict_checked(model, frame.loc[40:, baseline.FEATURES])
        self.assertTrue(np.isfinite(predictions).all())
        self.assertEqual(unknown, 10)
        frame.loc[fit_ids, 'Administration'] = np.nan
        with self.assertRaisesRegex(ValueError, 'training-fold'):
            baseline.fit_checked(baseline.make_pipeline(), frame.loc[fit_ids, baseline.FEATURES],
                                 frame.loc[fit_ids, 'Profit'])

    def test_source_download_cache_and_hash_tampering(self):
        payload = fixture().to_csv(index=False).encode()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'url': 'https://example.invalid/pinned.csv',
                                           'sha256': hashlib.sha256(payload).hexdigest()}))
            response = MagicMock()
            response.__enter__.return_value.read.return_value = payload
            with patch.object(baseline, 'MANIFEST', manifest), \
                 patch.object(baseline.urllib.request, 'urlopen', return_value=response) as download:
                frame, metadata = baseline.acquire_data(root / 'cache')
                self.assertEqual(len(frame), 50)
                self.assertIsNotNone(metadata['acquisition']['retrieved_at_utc'])
                baseline.acquire_data(root / 'cache')
                self.assertEqual(download.call_count, 1)
                (root / 'cache/50_Startups.csv').write_bytes(b'tampered')
                with self.assertRaisesRegex(ValueError, 'SHA-256'):
                    baseline.acquire_data(root / 'cache')


class BaselineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.frame = fixture()
        cls.source = cls.root / 'synthetic.csv'
        cls.source.write_text(cls.frame.to_csv(index=False))
        cls.provenance = {'scope': 'synthetic fixture',
                          'sha256': hashlib.sha256(cls.source.read_bytes()).hexdigest()}
        cls.first = baseline.run_analysis(cls.frame, cls.provenance, cls.root, 'first')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def read(self, name):
        return json.loads((self.first / name).read_text())

    def test_independent_verifier_rejects_tampered_metrics(self):
        verify_startups_run.verify(self.first, self.source)
        path = self.first / 'metrics.json'
        original = path.read_bytes()
        altered = json.loads(original)
        altered['holdout']['linear_regression']['mse'] += 100
        try:
            path.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError, 'Metric mismatch'):
                verify_startups_run.verify(self.first, self.source)
        finally:
            path.write_bytes(original)

    def test_split_fold_isolation_and_fold_local_statistics(self):
        splits = self.read('splits.json')
        train, test = set(splits['train_row_ids']), set(splits['test_row_ids'])
        self.assertEqual((len(train), len(test)), (40, 10))
        self.assertFalse(train & test)
        self.assertEqual(train | test, set(range(50)))
        seen = []
        for fold, result in zip(splits['folds'], self.read('training_cv.json')['folds']):
            fit, val = set(fold['fit_row_ids']), set(fold['validation_row_ids'])
            self.assertFalse(fit & val)
            self.assertEqual(fit | val, train)
            seen.extend(val)
            for column in baseline.NUMERIC:
                self.assertAlmostEqual(result['preprocessing']['numeric_training_medians'][column],
                                       self.frame.loc[list(fit), column].median())
        self.assertEqual(sorted(seen), sorted(train))

    def test_exported_metrics_recompute_from_predictions(self):
        holdout = pd.read_csv(self.first / 'holdout_predictions.csv')
        reported = self.read('metrics.json')['holdout']
        for name, column in [('linear_regression', 'linear_prediction'), ('dummy_mean', 'dummy_prediction')]:
            y, prediction = holdout['actual'], holdout[column]
            self.assertAlmostEqual(reported[name]['mae'], mean_absolute_error(y, prediction))
            self.assertAlmostEqual(reported[name]['mse'], mean_squared_error(y, prediction))
            self.assertAlmostEqual(reported[name]['rmse'], np.sqrt(mean_squared_error(y, prediction)))
            self.assertAlmostEqual(reported[name]['r2'], r2_score(y, prediction))
        np.testing.assert_allclose(holdout['residual'], holdout['actual'] - holdout['linear_prediction'])
        cv = pd.read_csv(self.first / 'train_cv_predictions.csv')
        folds = self.read('training_cv.json')['folds']
        for fold in folds:
            part = cv[cv['fold'] == fold['fold']]
            self.assertAlmostEqual(fold['linear_regression']['mse'],
                                   mean_squared_error(part['actual'], part['linear_prediction']))
        for image in self.first.glob('*.png'):
            self.assertEqual(image.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(len(list(self.first.glob('*.png'))), 6)
        self.assertEqual(self.first.parent.name, '50_startups')
        self.assertEqual(self.read('status.json')['status'], 'TECHNICAL_COMPLETE')

    def test_reproducibility_and_no_overwrite_or_path_escape(self):
        second = baseline.run_analysis(self.frame, {'scope': 'synthetic fixture'}, self.root, 'repeat')
        for name in ['metrics.json', 'splits.json', 'training_cv.json', 'fitted_model.json',
                     'train_cv_predictions.csv', 'holdout_predictions.csv', 'frozen_plan.json']:
            self.assertEqual((self.first / name).read_bytes(), (second / name).read_bytes())
        with self.assertRaises(FileExistsError):
            baseline.run_analysis(self.frame, {}, self.root, 'first')
        with self.assertRaises(ValueError):
            baseline.run_analysis(self.frame, {}, self.root, '../escape')

    def test_holdout_changes_cannot_change_training_outputs(self):
        mutated = self.frame.copy()
        test_ids = self.read('splits.json')['test_row_ids']
        mutated.loc[test_ids, 'R&D Spend'] += 1e10
        mutated.loc[test_ids, 'State'] = 'HOLDOUT_ONLY'
        mutated.loc[test_ids, 'Profit'] += 5e6
        changed = baseline.run_analysis(mutated, {'scope': 'synthetic fixture'}, self.root, 'mutated')
        for name in ['fitted_model.json', 'training_cv.json', 'train_cv_predictions.csv',
                     'train_descriptive_statistics.csv', 'train_correlation.csv', 'frozen_plan.json']:
            self.assertEqual((self.first / name).read_bytes(), (changed / name).read_bytes())
        metrics = json.loads((changed / 'metrics.json').read_text())
        self.assertEqual(metrics['holdout']['unknown_state_count'], 10)


if __name__ == '__main__':
    unittest.main()
