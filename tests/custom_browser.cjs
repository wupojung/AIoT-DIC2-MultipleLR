// Targeted Custom CSV E2E; runs against localhost or the deployed Pages site.
const {chromium}=require('playwright');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
const root=path.resolve(__dirname,'..'),base=process.env.DASHBOARD_URL||'http://localhost:8000/';
const references=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/custom_reference.json')));
const out=path.join(root,'docs/reports/custom_csv'),assets=path.join(root,'docs/assets');
const close=(a,b,atol=1e-6,rtol=1e-10)=>assert(Math.abs(a-b)<=atol+rtol*Math.abs(b),`${a} != ${b}`);
(async()=>{
 fs.mkdirSync(out,{recursive:true});const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1,acceptDownloads:true});const jsErrors=[],consoleErrors=[],expectedCors=[],cases=[];let cors=false;
 page.on('pageerror',e=>jsErrors.push(e.message));page.on('console',m=>{if(m.type()==='error'){if(cors&&/CORS|Access-Control|net::ERR_FAILED/.test(m.text()))expectedCors.push(m.text());else consoleErrors.push(m.text());}});
 try{
  await page.goto(base,{waitUntil:'networkidle'});await page.waitForFunction(()=>!document.querySelector('#dataset').disabled&&!document.querySelector('#dataset option[value=custom]').disabled);
  await page.selectOption('#dataset','custom');assert(await page.locator('#custom-import').isVisible());assert.equal(await page.locator('[data-metric]').count(),0);
  const runs=[];
  for(const reference of references.cases){
   if(reference.name==='50_startups'){
    const manifest=JSON.parse(fs.readFileSync(path.join(root,'data/50_startups_manifest.json')));
    await page.fill('#csv-url',manifest.url);await page.click('#load-csv-url');
   }else await page.setInputFiles('#csv-file',path.join(root,'tests/fixtures/custom_numeric.csv'));
   await page.waitForFunction(()=>!document.querySelector('#csv-config').hidden);
   const headers=await page.locator('#feature-columns input').evaluateAll(inputs=>inputs.map(i=>i.value));
   await page.selectOption('#target-column',reference.target);
   assert(await page.locator('#feature-columns input').nth(headers.indexOf(reference.target)).isDisabled());
   for(const feature of reference.features)await page.locator('#feature-columns input').nth(headers.indexOf(feature)).check();
   assert(await page.locator('#run-custom').isEnabled());
   if(reference.name==='custom_numeric')await page.screenshot({path:path.join(assets,'custom-csv-import-1920x1080.png'),fullPage:true});
   await page.click('#run-custom');await page.waitForFunction(()=>document.querySelector('#custom-status').textContent.startsWith('Regression complete'));
   const downloaded=page.waitForEvent('download');await page.click('#download-custom');const download=await downloaded;const result=JSON.parse(fs.readFileSync(await download.path()));
   assert.equal(result.source.sha256,reference.sha256);assert.deepEqual(result.splits.train,reference.train_ids);assert.deepEqual(result.splits.test,reference.test_ids);
   result.predictions.forEach((row,i)=>{close(row.prediction,reference.prediction[i]);close(row.actual,reference.actual[i]);});
   for(const key of ['mae','mse','rmse','r2']){close(result.holdout.linear_regression[key],reference.metrics[key]);close(result.holdout.dummy_mean[key],reference.dummy[key]);}
   assert.equal(await page.locator('#overview svg circle').count(),reference.test_ids.length*2);
   assert.equal(await page.locator('[data-custom-metric=rmse]').textContent(),result.holdout.linear_regression.rmse.toLocaleString('en-US',{minimumFractionDigits:4,maximumFractionDigits:4}));
   await page.click('#tab-features');assert((await page.locator('#features').textContent()).includes('Not Available'));assert.equal(await page.locator('#features svg').count(),0);
   await page.click('#tab-evaluation');assert((await page.locator('#evaluation').textContent()).includes('Predictions & residuals'));
   await page.click('#tab-overview');
   if(reference.name==='custom_numeric')await page.screenshot({path:path.join(assets,'custom-csv-regression-1920x1080.png'),fullPage:true});
   fs.writeFileSync(path.join(out,`${reference.name}-browser-run.json`),JSON.stringify(result,null,2)+'\n');
   runs.push({name:reference.name,holdout:result.holdout,execution_ms:result.execution_ms,max_prediction_abs_error:Math.max(...result.predictions.map((r,i)=>Math.abs(r.prediction-reference.prediction[i])))});
   cases.push(`${reference.name}: import, configure, worker fit, JSON download, sklearn equivalence, residual charts, Not Available feature selection`);
  }
  // Target/feature edits invalidate old custom results immediately.
  const first=page.locator('#feature-columns input').first();await first.uncheck();assert.equal(await page.locator('[data-custom-metric]').count(),0);assert(await page.locator('#download-custom').isDisabled());cases.push('configuration change clears stale model/results');
  await page.setInputFiles('#csv-file',{name:'invalid.csv',mimeType:'text/csv',buffer:Buffer.from('a,a,y\n1,2,3')});await page.waitForFunction(()=>document.querySelector('#custom-status').classList.contains('error'));assert(await page.locator('#run-custom').isDisabled());cases.push('invalid duplicate-header/insufficient CSV rejected');
  // Real cross-origin response from example.com has no Access-Control-Allow-Origin.
  cors=true;await page.fill('#csv-url','https://example.com/');await page.click('#load-csv-url');
  await page.waitForFunction(()=>document.querySelector('#custom-status').textContent.includes('Upload the local CSV file instead'));
  await page.waitForTimeout(100);cors=false;cases.push('real example.com CORS denial shows local-file fallback');
  for(const id of ['50_startups','boston_housing']){
   await page.selectOption('#dataset',id);assert(await page.locator('#custom-import').isHidden());
   const expected=JSON.parse(fs.readFileSync(path.join(root,`web/data/${id}.json`)));
   for(const tab of ['overview','features','evaluation']){await page.click(`#tab-${tab}`);assert(await page.locator(`#${tab}`).isVisible());}
   await page.click('#tab-overview');assert.equal(await page.locator('[data-metric=baseline-rmse]').textContent(),expected.holdout['All Features'].rmse.toLocaleString('en-US',{minimumFractionDigits:4,maximumFractionDigits:4}));
   cases.push(`${id} built-in three-page regression intact`);
  }
  assert.deepEqual(jsErrors,[]);assert.deepEqual(consoleErrors,[]);
  const proof={status:'PASS',url:base,tested_at:new Date().toISOString(),browser:await browser.version(),viewport:{width:1920,height:1080},cases,runs,js_errors:jsErrors,unexpected_console_errors:consoleErrors,expected_cors_errors:expectedCors};
  fs.writeFileSync(path.join(out,'browser-verification.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
