"""Config and reuse checks use unrelated synthetic data, not Boston records."""
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import sys
import unittest
import contextlib
import io

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python/src'))
import regression_workflow as workflow
import startups_baseline as startups
import feature_selection as selection


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.numeric = tuple(f'x{i}' for i in range(12))
        self.config = workflow.DatasetConfig(
            'synthetic_other', 'response', self.numeric, (), 60,
            self.numeric + ('excluded_context', 'response'), excluded=('excluded_context',))
        rng = np.random.default_rng(71)
        self.frame = pd.DataFrame(rng.normal(size=(60, 12)), columns=self.numeric)
        self.frame['excluded_context'] = np.arange(60)
        self.frame['response'] = 3 * self.frame['x0'] - self.frame['x1']

    def test_numeric_only_dataset_has_no_state_or_excluded_input(self):
        workflow.validate_data(self.frame, self.config)
        train, val = workflow.split_row_ids(self.frame.index)
        model = workflow.make_pipeline(self.config).fit(
            self.frame.loc[train], self.frame.loc[train, self.config.target])
        names = model.named_steps['preprocess'].get_feature_names_out().tolist()
        self.assertEqual(names, [f'numeric__{name}' for name in self.numeric])
        original = model.predict(self.frame.loc[val])
        changed = self.frame.loc[val].copy()
        changed['excluded_context'] = 1e20
        changed['response'] = -1e20
        np.testing.assert_array_equal(original, model.predict(changed))
        self.assertLess(workflow.metrics(self.frame.loc[val, 'response'], original)['rmse'], 1e-12)
        self.assertIsNot(model, workflow.make_pipeline(self.config))

    def test_config_prevents_target_and_exclusion_leakage(self):
        with self.assertRaisesRegex(ValueError, 'Target/excluded'):
            replace(self.config, numeric=self.numeric + ('response',))
        with self.assertRaisesRegex(ValueError, 'Target/excluded'):
            replace(self.config, numeric=self.numeric + ('excluded_context',))
        with self.assertRaisesRegex(ValueError, 'unique'):
            replace(self.config, categorical=('x0',))
        with self.assertRaisesRegex(ValueError, 'schema'):
            replace(self.config, raw_columns=self.numeric + ('response',))
        for frame in [self.frame.iloc[:-1], self.frame.drop(columns=['x1'])]:
            with self.assertRaises(ValueError):
                workflow.validate_data(frame, self.config)

    def test_medians_are_fit_on_local_training_rows(self):
        self.frame.loc[0, 'x0'] = np.nan
        fit = self.frame.iloc[:40].copy()
        model = workflow.make_pipeline(self.config).fit(fit, fit['response'].fillna(0))
        median = model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['imputer'].statistics_[0]
        self.assertEqual(median, fit['x0'].median())
        altered_validation = self.frame.iloc[40:].copy()
        altered_validation['x0'] = 1e30
        model.predict(altered_validation)
        self.assertEqual(median, model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['imputer'].statistics_[0])

    def test_split_and_fold_functions_preserve_sklearn_contract(self):
        for row_count in [50, 60]:
            ids = np.arange(row_count)
            expected = train_test_split(ids, test_size=0.2, random_state=42, shuffle=True)
            actual = workflow.split_row_ids(ids)
            for left, right in zip(expected, actual):
                np.testing.assert_array_equal(left, right)
            for (left_fit, left_val), (right_fit, right_val) in zip(
                    workflow.folds(actual[0], n=5), KFold(5, shuffle=True, random_state=42).split(actual[0])):
                np.testing.assert_array_equal(left_fit, right_fit)
                np.testing.assert_array_equal(left_val, right_val)

    def test_shared_selectors_accept_twelve_numeric_columns_and_custom_alpha(self):
        X, y = self.frame.loc[:47, list(self.numeric)], self.frame.loc[:47, 'response']
        _, trace = selection.fit_selectors(X, y, 'synthetic', [], self.config, [.001, .01, .1, 1])
        self.assertEqual(len(list(selection.candidates(trace))), 61)
        for method in selection.METHODS:
            self.assertEqual(len(trace['orders'][method]), 12)
            self.assertEqual(set(trace['subsets'][method]), {str(k) for k in range(1, 13)})
            self.assertFalse(any('State' in name or 'excluded' in name for name in trace['orders'][method]))
        self.assertEqual(trace['details']['LassoCV']['alphas'], [1, .1, .01, .001])
        self.assertEqual(selection.protocol()['alpha_grid'], selection.ALPHAS)

    def test_shared_nested_engine_accepts_different_sample_and_feature_counts(self):
        ids, reserved = workflow.split_row_ids(self.frame.index)
        X, y = self.frame.loc[ids, list(self.numeric)], self.frame.loc[ids, 'response']
        with contextlib.redirect_stdout(io.StringIO()):
            result = selection.training_experiment(X, y, self.config, [.001, .01, .1, 1])
        self.assertEqual(len(result['comparison_summary']), 61)
        self.assertEqual(len(result['comparison']), 5 * 61)
        all_features = next(row for row in result['comparison_summary'] if row['method'] == 'All Features')
        self.assertEqual(all_features['k'], 12)
        predicted_ids = {row['row_id'] for row in result['predictions']}
        self.assertEqual(predicted_ids, set(ids))
        self.assertFalse(predicted_ids & set(reserved))
        for entry in result['audit']:
            self.assertLessEqual(set(entry['fit_row_ids']), set(ids))
            self.assertNotIn('state_categories', entry)
        self.assertEqual(len(result['final_choice']['features']), result['final_choice']['k'])

    def test_plot_feature_axis_and_units_follow_supplied_experiment(self):
        summary = []
        for method in selection.METHODS + ['All Features']:
            for k in ([12] if method == 'All Features' else range(1, 13)):
                summary.append({'method': method, 'k': k, 'rmse_mean': 2 + k / 10,
                                'rmse_std': .1, 'r2_mean': .8, 'r2_std': .01})
        captured = []
        def inspect(path, figure):
            axis = figure.axes[0]
            self.assertEqual(axis.get_xlabel(), 'Synthetic numeric predictors')
            np.testing.assert_array_equal(axis.get_xticks(), range(1, 13))
            self.assertIn('All Features (k=12)', axis.get_legend_handles_labels()[1])
            if path.stem.endswith('rmse'):
                self.assertEqual(axis.get_ylabel(), 'CV RMSE (synthetic units)')
            captured.append(path)
            startups.plt.close(figure)
        with patch.object(startups, 'save_plot', side_effect=inspect):
            selection.plot_curves(summary, Path('/tmp'), xlabel='Synthetic numeric predictors', units='synthetic units')
        self.assertEqual(len(captured), 2)

    def test_existing_startups_adapter_uses_the_same_core(self):
        self.assertEqual(startups.CONFIG.features, tuple(startups.FEATURES))
        self.assertEqual(startups.CONFIG.categorical_block, 'state')
        self.assertEqual(startups.CONFIG.expected_rows, 50)
        self.assertEqual(startups.metrics([1, 2, 3], [2, 2, 2]), workflow.metrics([1, 2, 3], [2, 2, 2]))
