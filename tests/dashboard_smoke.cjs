// MVP desktop verification only. Playwright is an external development tool.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.DASHBOARD_URL || 'http://localhost:8000/';
const output = path.resolve(__dirname, '../docs/assets');
const root = path.resolve(__dirname, '..');
const format = n => Number(n).toLocaleString('en-US', {minimumFractionDigits:4, maximumFractionDigits:4});
(async () => {
  fs.mkdirSync(output, {recursive:true});
  const browser = await chromium.launch({headless:true, executablePath:process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const page = await browser.newPage({viewport:{width:1920,height:1080}, deviceScaleFactor:1});
  const errors = [], failedRequests = [], cases = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => {if(m.type()==='error') errors.push(m.text());});
  page.on('requestfailed', r => failedRequests.push(r.url()));
  page.on('response', r => {if(r.status()>=400) failedRequests.push(`${r.status()} ${r.url()}`);});
  try {
    await page.goto(base, {waitUntil:'networkidle'});
    await page.waitForFunction(() => !document.querySelector('#dataset').disabled);
    for (const id of ['50_startups','boston_housing','50_startups']) {
      const expected = JSON.parse(fs.readFileSync(path.join(root,`web/data/${id}.json`)));
      await page.selectOption('#dataset',id);
      assert.equal(await page.locator('body').getAttribute('data-dataset'),id);
      await page.locator('#tab-overview').click();
      assert.equal(await page.locator('[data-metric="baseline-rmse"]').textContent(),format(expected.holdout['All Features'].rmse));
      assert.equal(await page.locator('[data-metric="baseline-r2"]').textContent(),format(expected.holdout['All Features'].r2));
      // Both deployed JSON payloads must exactly match reproducible local exports.
      const actual = await page.evaluate(async id => (await fetch(`data/${id}.json`)).json(),id);
      assert.deepEqual(actual,expected);
      for (const tab of ['overview','features','evaluation']) {
        await page.locator(`#tab-${tab}`).click();
        assert.equal(await page.locator('[role="tabpanel"]:visible').count(),1);
        assert.equal(await page.locator(`#${tab}`).isVisible(),true);
        if (tab !== 'evaluation') {
          const charts = page.locator(`#${tab} svg`);
          assert.equal(await charts.count(),2);
          for (const metric of ['rmse','r2']) {
            const chart = page.locator(`#${tab} [data-chart="${metric}"]`);
            assert.equal(await chart.locator('polyline').count(),5);
            assert.equal(await chart.locator('circle').count(),expected.encoded_features.length*5);
            // Compare each plotted coordinate with corresponding source metric.
            const rows = expected.curves;
            const values = rows.map(r => r[`${metric}_mean`]);
            const low=Math.min(...values),high=Math.max(...values),pad=(high-low||1)*.16,min=low-pad,max=high+pad;
            for(const method of ['Pearson','F-Test','RFE','SFS','LassoCV']){
              const points=await chart.locator(`polyline[data-method="${method}"]`).getAttribute('points');
              const expectedPoints=rows.filter(r=>r.method===method).sort((a,b)=>a.k-b.k).map(r=>`${58+(r.k-1)/(expected.encoded_features.length-1)*584},${18+(max-r[`${metric}_mean`])/(max-min)*200}`).join(' ');
              assert.equal(points,expectedPoints);
            }
          }
        }
        if(tab==='features'){
          for(const method of ['Pearson','F-Test','RFE','SFS','LassoCV']){
            await page.locator(`[data-rank-method="${method}"]`).click();
            const names=await page.locator('#ranking tbody tr td:nth-child(2)').allTextContents();
            assert.deepEqual(names,expected.orders[method].map(n=>n.replace(/^(numeric|state)__/, '').replace(/^State_/, 'State: ')));
          }
          await page.locator('[data-rank-method="Pearson"]').click();
        }
        if(tab==='evaluation'){
          assert.equal(await page.locator('[data-metric="cv-rmse"]').textContent(),format(expected.baseline_cv.rmse_mean));
          const rows=page.locator('#evaluation table tbody tr');
          assert.equal(await rows.count(),id==='50_startups'?2:3);
          const labels=['All Features',...(expected.holdout.Selected?['Selected']:[]),'Dummy'];
          for(let i=0;i<labels.length;i++){
            const cells=await rows.nth(i).locator('td').allTextContents();
            for(const [j,metric] of ['mae','mse','rmse','r2'].entries()){
              const digits=metric==='mse'?2:4;
              assert.equal(cells[j+1],Number(expected.holdout[labels[i]][metric]).toLocaleString('en-US',{minimumFractionDigits:digits,maximumFractionDigits:digits}));
            }
          }
        }
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
        const file=`dashboard-${id}-${tab}-1920x1080.png`;
        await page.screenshot({path:path.join(output,file),fullPage:true});
        cases.push({dataset:id,tab,status:'PASS',screenshot:file});
      }
    }
    await page.locator('#tab-overview').focus();
    await page.keyboard.press('ArrowDown');
    assert.equal(await page.locator(':focus').getAttribute('id'),'tab-features');
    assert.deepEqual(errors,[]);assert.deepEqual(failedRequests,[]);
    fs.writeFileSync(path.join(output,'dashboard-verification.json'),JSON.stringify({status:'PASS',url:base,viewport:{width:1920,height:1080},browser:await browser.version(),tool:'Playwright + Google Chrome',tested_at:new Date().toISOString(),cases,console_and_js_errors:errors,failed_requests:failedRequests},null,2)+'\n');
    console.log(`PASS ${base}: 9 dataset/tab scenarios; JSON, exact metrics, all curve coordinates, feature orders, keyboard and console; 6 screenshots`);
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
