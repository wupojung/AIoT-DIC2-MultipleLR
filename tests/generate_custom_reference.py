"""Small sklearn reference fits for browser tests; never modify accepted experiments."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
import sklearn

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python/src'))
import startups_baseline as baseline


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--poc-dir',type=Path)
    args=parser.parse_args()
    poc=[]
    startups,_=baseline.acquire_data(ROOT/'data/50_startups')
    cases=[]
    for name,frame,features,target,path in [
        ('50_startups',startups,baseline.FEATURES,baseline.TARGET,ROOT/'data/50_startups/50_Startups.csv'),
        ('custom_numeric',pd.read_csv(ROOT/'tests/fixtures/custom_numeric.csv'),['floor area (m²)','years, age','distance_km'],'Sale value',ROOT/'tests/fixtures/custom_numeric.csv')]:
        train,test=train_test_split(frame.index.to_numpy(),test_size=.2,random_state=42)
        pipeline=baseline.make_pipeline() if name=='50_startups' else Pipeline([('preprocess',SimpleImputer(strategy='median')),('regressor',LinearRegression())])
        pipeline.fit(frame.loc[train,features],frame.loc[train,target])
        predictions=pipeline.predict(frame.loc[test,features])
        dummy=DummyRegressor().fit(frame.loc[train,features],frame.loc[train,target]).predict(frame.loc[test,features])
        pre=pipeline.named_steps['preprocess']
        poc.append({'name':name,'X':pre.transform(frame.loc[train,features]).tolist(),'T':pre.transform(frame.loc[test,features]).tolist(),'y':frame.loc[train,target].tolist(),'actual':frame.loc[test,target].tolist(),'prediction':predictions.tolist()})
        cases.append({'name':name,'target':target,'features':features,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                      'train_ids':train.tolist(),'test_ids':test.tolist(),'prediction':predictions.tolist(),
                      'actual':frame.loc[test,target].tolist(),
                      'metrics':baseline.metrics(frame.loc[test,target],predictions),'dummy':baseline.metrics(frame.loc[test,target],dummy)})
    splits={str(n):{'train':a.tolist(),'test':b.tolist()} for n in [20,21,50,96,101,2000]
            for a,b in [train_test_split(np.arange(n),test_size=.2,random_state=42)]}
    out={'sklearn':sklearn.__version__,'numpy':np.__version__,'tolerance':{'prediction_atol':1e-6,'metric_rtol':1e-10,'metric_atol':1e-6},'cases':cases,'splits':splits}
    (ROOT/'tests/fixtures/custom_reference.json').write_text(json.dumps(out,indent=2)+'\n')
    if args.poc_dir:
        args.poc_dir.mkdir(parents=True,exist_ok=True)
        (args.poc_dir/'fixtures.json').write_text(json.dumps(poc))
        (args.poc_dir/'index.html').write_text('<!doctype html><title>Runtime PoC</title>')
    print('PASS generated two fresh sklearn reference fits; original experiments unchanged')


if __name__=='__main__':main()
