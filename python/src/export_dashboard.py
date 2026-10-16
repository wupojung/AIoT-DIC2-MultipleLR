"""Export reviewed experiment snapshots for static presentation; never train models."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / 'docs/reports'


def export(dataset):
    sources = {}
    def read(relative):
        path = REPORTS / relative
        raw = path.read_bytes()
        sources[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    boston = dataset == 'boston_housing'
    folder = 'boston_housing' if boston else 'feature_selection'
    result = read(f'{folder}/results.json')
    split = read(f'{folder}/splits.json')
    frozen = read(f'{folder}/frozen_selection.json')
    if boston:
        quality = read('boston_housing/data_quality.json')
        baseline_cv = next(row for row in result['comparison_summary'] if row['method'] == 'All Features')
        holdout = result['holdout']
        raw_features = quality['predictors']
        rows = quality['shape'][0]
        note = 'B excluded; exclusion does not remove proxy bias. Historic, potentially censored MEDV. No consequential housing use; original dataset rights remain unresolved.'
    else:
        metrics = read('50_startups/metrics.json')
        baseline_cv = {f'{metric}_mean': value['mean'] for metric, value in metrics['train_cv']['linear_regression'].items()}
        holdout = {'All Features': metrics['holdout']['linear_regression'], 'Dummy': metrics['holdout']['dummy_mean']}
        raw_features = ['R&D Spend', 'Administration', 'Marketing Spend', 'State']
        rows = len(split['train_row_ids']) + len(split['test_row_ids'])
        note = 'Currency and collection period are unverified (source units). State uses drop-first one-hot encoding; encoded dummies count separately. Selected-model holdout was not evaluated in Issue #4.'
    full = next(trace for trace in result['traces'] if trace['context'] == 'full_training')
    return {'schema_version': 1, 'dataset_id': dataset,
        'name': 'Boston Housing' if boston else '50 Startups',
        'subtitle': 'Historic housing · workflow reuse' if boston else 'Business investment · regression baseline',
        'target': 'MEDV' if boston else 'Profit', 'units': 'historical USD thousands' if boston else 'source units (currency unverified)',
        'rows': rows, 'raw_features': raw_features, 'encoded_features': full['encoded_names'],
        'train_rows': len(split['train_row_ids']), 'test_rows': len(split['test_row_ids']),
        'seed': 42, 'excluded': ['B'] if boston else [], 'baseline_cv': baseline_cv,
        'holdout': holdout, 'choice': frozen['choice'], 'nested': result['nested_summary'],
        'curves': result['comparison_summary'], 'orders': full['orders'],
        'lasso_alpha': full['details']['LassoCV']['alpha'],
        'note': note, 'report': f'docs/reports/{folder}/' + ('REPORT.md' if boston else 'REPORT.md'),
        'baseline_report': 'docs/reports/boston_housing/REPORT.md' if boston else 'docs/reports/50_startups/report.md',
        'sources': sources}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for dataset in ['50_startups', 'boston_housing']:
        path = ROOT / 'web/data' / f'{dataset}.json'
        text = json.dumps(export(dataset), indent=2, ensure_ascii=False, allow_nan=False) + '\n'
        if args.check:
            if not path.exists() or path.read_text() != text:
                raise SystemExit(f'FAIL stale or altered dashboard export: {path}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        print(f'PASS {dataset}: static export matches reviewed sources' if args.check else f'EXPORTED {path}')


if __name__ == '__main__':
    main()
