import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {parse,analyze,splitRows,metrics,LIMITS} from '../web/custom-engine.mjs';
const reference=JSON.parse(fs.readFileSync('tests/fixtures/custom_reference.json'));
const source=name=>fs.readFileSync(name==='50_startups'?'data/50_startups/50_Startups.csv':'tests/fixtures/custom_numeric.csv','utf8');
const close=(actual,expected,atol=1e-6,rtol=1e-10)=>assert(Math.abs(actual-expected)<=atol+rtol*Math.abs(expected),`${actual} != ${expected}`);
const fixture=()=>parse(source('custom_numeric'));
const config=reference.cases[1];
const run=data=>analyze(data,config.target,config.features);
test('CSV quoted header/BOM/newline parsing; all row-to-column mappings',()=>{
 const data=fixture();assert.equal(data.headers[1],'years, age');assert.equal(data.rows.length,96);
 const multiline=parse('\uFEFF'+source('custom_numeric').replace('floor area (m²)','"floor\narea"'));
 assert.equal(multiline.headers[0],'floor\narea');assert.equal(multiline.rows.length,96);
});
test('MT19937 split matches sklearn exact row IDs/order across six sizes',()=>{
 for(const [n,expected] of Object.entries(reference.splits))assert.deepEqual(splitRows(Number(n)),expected);
});
for(const fixtureCase of reference.cases)test(`new CSV fit matches sklearn: ${fixtureCase.name}`,()=>{
 const result=analyze(parse(source(fixtureCase.name)),fixtureCase.target,fixtureCase.features);
 assert.deepEqual(result.splits,{train:fixtureCase.train_ids,test:fixtureCase.test_ids});
 result.predictions.forEach((row,i)=>{close(row.prediction,fixtureCase.prediction[i]);close(row.actual,fixtureCase.actual[i]);close(row.residual,row.actual-row.prediction);});
 for(const key of ['mae','mse','rmse','r2']){close(result.holdout.linear_regression[key],fixtureCase.metrics[key]);close(result.holdout.dummy_mean[key],fixtureCase.dummy[key]);}
 assert.equal(result.configuration.feature_selection.startsWith('Not Available'),true);
});
test('test X/y changes cannot fit medians/scales/coefficients; fresh training y changes do',()=>{
 const data=fixture(),a=run(data),changed=structuredClone(data);
 for(const i of a.splits.test){changed.rows[i][0]=String(Number(changed.rows[i][0])+5000);changed.rows[i][3]=String(Number(changed.rows[i][3])+10000);}
 const b=run(changed);assert.deepEqual(b.preprocessing,a.preprocessing);assert.deepEqual(b.fit,a.fit);assert.notDeepEqual(b.predictions,a.predictions);
 const newTraining=structuredClone(data);for(const i of a.splits.train)newTraining.rows[i][3]=String(Number(newTraining.rows[i][3])*2+7);
 assert.notDeepEqual(run(newTraining).fit.coefficients,a.fit.coefficients);
});
test('category vocabulary/imputation use train only, unknown test category is disclosed',()=>{
 const data=parse(source('50_startups')),c=reference.cases[0],a=analyze(data,c.target,c.features);
 const changed=structuredClone(data),id=a.splits.test[0];changed.rows[id][3]='Only in test';
 const b=analyze(changed,c.target,c.features);assert.deepEqual(b.preprocessing,a.preprocessing);assert.deepEqual(b.fit,a.fit);assert.equal(b.unknown_category_count,1);
});
test('target leakage, insufficient features, collinearity, duplicates are refused',()=>{
 assert.throws(()=>analyze(fixture(),config.target,[config.target,config.features[0]]),/Target/);
 assert.throws(()=>analyze(fixture(),config.target,[config.features[0]]),/2–12/);
 const constant=fixture();constant.rows.forEach(r=>r[0]='1');assert.throws(()=>run(constant),/Constant/);
 const collinear=fixture();collinear.rows.forEach(r=>r[1]=String(Number(r[0])*2));assert.throws(()=>run(collinear),/Rank-deficient/);
 const duplicate=fixture();duplicate.rows[1]=[...duplicate.rows[0]];assert.throws(()=>run(duplicate),/Duplicate/);
});
test('empty/malformed/duplicate headers/nonfinite/oversized/insufficient data fail clearly',()=>{
 assert.throws(()=>parse(''),/empty/);
 assert.throws(()=>parse('a,a,y\n'+Array(20).fill('1,2,3').join('\n')),/unique/);
 assert.throws(()=>parse('a,b,y\n"unterminated'),/Invalid CSV/);
 assert.throws(()=>parse('a,b,y\n1,2,3'),/20–2000/);
 assert.throws(()=>parse('a,b,y\n'+Array(20).fill('1,Infinity,3').join('\n')),/Infinity/);
 assert.throws(()=>parse('x'.repeat(LIMITS.bytes+1)),/2 MiB/);
 const tooFew=fixture();tooFew.rows=tooFew.rows.slice(0,20);assert.throws(()=>analyze(tooFew,'Sale value',['floor area (m²)','years, age','distance_km','Sale value']),/Target/);
 const missing=fixture();missing.rows[2][3]='';missing.columns[3].missing=1;assert.throws(()=>run(missing),/Target/);
 const allMissing=fixture();for(const i of splitRows(96).train)allMissing.rows[i][2]='';assert.throws(()=>run(allMissing),/entirely missing/);
});
test('independent metrics known answer and constant target undefined R²',()=>{
 assert.deepEqual(metrics([1,2,3],[1,3,2]),{mae:2/3,mse:2/3,rmse:Math.sqrt(2/3),r2:0,n:3});
 assert.equal(metrics([2,2],[2,2]).r2,null);
});
