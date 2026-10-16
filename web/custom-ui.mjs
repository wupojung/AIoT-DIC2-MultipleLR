import {parse, LIMITS} from './custom-engine.mjs';
const $=s=>document.querySelector(s);
const esc=v=>String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll(String.fromCharCode(34),'&quot;').replaceAll(String.fromCharCode(39),'&#39;');
const fmt=v=>v===null?'Undefined':Number(v).toLocaleString('en-US',{minimumFractionDigits:4,maximumFractionDigits:4});
const card=(title,body)=>`<div class="card"><h3>${title}</h3>${body}</div>`;
let dataset=null,csv='',source=null,result=null,worker=null,timer=null,controller=null,generation=0;
function status(message,error=false){$('#custom-status').textContent=message;$('#custom-status').classList.toggle('error',error);}
function choices(){return [...document.querySelectorAll('#feature-columns input:checked')].map(i=>i.value);}
function updateButton(){$('#run-custom').disabled=!dataset||!$('#target-column').value||choices().length<2||choices().length>LIMITS.features||!!worker;}
function stop(){worker?.terminate();worker=null;clearTimeout(timer);$('#cancel-custom').hidden=true;updateButton();}
function renderEmpty(){for(const id of ['overview','features','evaluation'])$(`#${id}`).innerHTML=card(id==='features'?'Not Available · Custom Feature Selection':'No custom result yet',`<p class="muted">${id==='features'?'Regression MVP only. Pearson, F-Test, RFE, SFS and LassoCV rankings and feature-count curves are not implemented for custom CSV. No built-in rankings or scores are reused.':'Load a CSV, select Target Y and at least two Features X, then run a new regression. Previous dataset scores are not shown here.'}</p>`);}
function clearResult(){result=null;$('#download-custom').disabled=true;if($('#dataset').value==='custom')renderEmpty();}
function invalidate(){generation++;stop();clearResult();updateButton();status('Configuration changed. Run a new regression to compute results.');}
function activate(){$('.dataset-bar .snapshot-tag').textContent='BROWSER-FITTED · NEW MODEL';$('.top-tag').innerHTML='<span class=live-dot></span> Custom browser computation';$('.side-note small').innerHTML='JavaScript SVD / OLS<br>Fresh browser computation';$('.subheading').textContent='Import your CSV. Fit a new model. Inspect reproducible predictions.';$('footer > span:last-child').textContent='New OLS fit · Training-only preprocessing · Source units';$('#custom-import').hidden=false;document.body.dataset.dataset='custom';$('#dataset-description').textContent='Custom CSV · a new browser-fitted model';if(result)renderResult(result);else renderEmpty();$('#tab-overview').click();}
document.addEventListener('custom-dataset-selected',activate);
document.addEventListener('builtin-dataset-selected',()=>{generation++;controller?.abort();stop();$('#custom-import').hidden=true;});
async function accept(bytes,label,g){
 if(bytes.length>LIMITS.bytes)throw new Error('CSV exceeds 2 MiB.');
 const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes),parsed=parse(text),hash=await crypto.subtle.digest('SHA-256',bytes);
 if(g!==generation)return;
 dataset=parsed;csv=text;source={...label,sha256:[...new Uint8Array(hash)].map(v=>v.toString(16).padStart(2,'0')).join('')};
 $('#csv-config').hidden=false;
 $('#csv-preview').innerHTML=`<div class="section-heading"><h3>${esc(label.name)}</h3><p>${parsed.rows.length} rows · ${parsed.headers.length} columns · first 5</p></div><div class="table-wrap"><table><thead><tr>${parsed.columns.map(c=>`<th>${esc(c.name)}<br><small>${c.type} · missing ${c.missing}</small></th>`).join('')}</tr></thead><tbody>${parsed.rows.slice(0,5).map(r=>`<tr>${r.map(v=>`<td>${esc(v||'∅')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
 $('#target-column').innerHTML='<option value="">Choose a target…</option>'+parsed.columns.map(c=>`<option value="${esc(c.name)}" ${c.type!=='numeric'||c.missing||c.unique<5?'disabled':''}>${esc(c.name)} (${c.type}${c.missing?', missing cells':''})</option>`).join('');
 $('#feature-columns').innerHTML=parsed.columns.map(c=>`<label class="feature-option"><input type="checkbox" value="${esc(c.name)}" ${!['numeric','categorical'].includes(c.type)||c.unique<2?'disabled':''}><span>${esc(c.name)} <small>${c.type}${c.unique<2?' · constant/empty':''}</small></span></label>`).join('');
 document.querySelectorAll('#feature-columns input').forEach(i=>i.addEventListener('change',invalidate));status(`Loaded ${parsed.rows.length} rows. Select a continuous target and at least two predictors.`);updateButton();
}
function beginLoad(){generation++;controller?.abort();stop();dataset=null;csv='';source=null;$('#csv-config').hidden=true;clearResult();updateButton();return generation;}
$('#csv-file').addEventListener('change',async()=>{const file=$('#csv-file').files[0];if(!file)return;$('#csv-url').value='';const g=beginLoad();status('Reading and validating CSV…');try{if(file.size>LIMITS.bytes)throw new Error('CSV exceeds 2 MiB.');await accept(new Uint8Array(await file.arrayBuffer()),{kind:'local file',name:file.name},g);}catch(e){if(g===generation)status(`Unable to load CSV: ${e.message}`,true);}});
$('#load-csv-url').addEventListener('click',async()=>{
 $('#csv-file').value='';const g=beginLoad();controller=new AbortController();const abort=controller;let timeout;status('Loading public CSV URL…');
 try{
  const url=new URL($('#csv-url').value);
  if(url.username||url.password||!(url.protocol==='https:'||(url.protocol==='http:'&&['localhost','127.0.0.1'].includes(url.hostname))))throw new Error('Use a public HTTPS CSV URL without credentials.');
  timeout=setTimeout(()=>abort.abort(),15000);
  const response=await fetch(url,{mode:'cors',credentials:'omit',referrerPolicy:'no-referrer',signal:abort.signal});
  if(!response.ok)throw new Error(`HTTP ${response.status}`);
  if(Number(response.headers.get('content-length'))>LIMITS.bytes)throw new Error('CSV exceeds 2 MiB.');
  const reader=response.body.getReader(),chunks=[];let length=0;
  while(true){const {value,done}=await reader.read();if(done)break;length+=value.length;if(length>LIMITS.bytes){await reader.cancel();throw new Error('CSV exceeds 2 MiB.');}chunks.push(value);}
  const bytes=new Uint8Array(length);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}await accept(bytes,{kind:'public URL',name:url.href},g);
 }catch(e){if(g===generation)status(`URL load failed (CORS/network/format): ${e.message}. Upload the local CSV file instead; no proxy is used.`,true);}finally{clearTimeout(timeout);}
});
$('#target-column').addEventListener('change',()=>{for(const i of document.querySelectorAll('#feature-columns input')){const c=dataset.columns.find(c=>c.name===i.value);i.disabled=i.value===$('#target-column').value||!['numeric','categorical'].includes(c.type)||c.unique<2;if(i.disabled)i.checked=false;}invalidate();});
$('#run-custom').addEventListener('click',()=>{
 if($('#run-custom').disabled)return;const g=++generation;clearResult();status('Fitting a fresh model in a Web Worker…');
 worker=new Worker(new URL('./custom-worker.mjs',import.meta.url),{type:'module'});$('#cancel-custom').hidden=false;updateButton();
 function failure(message){if(g!==generation)return;stop();status(`Analysis rejected: ${message}`,true);}
 worker.onmessage=({data})=>{if(g!==generation)return;if(data.error){failure(data.error);return;}stop();result=data.result;renderResult(result);$('#download-custom').disabled=false;status(`Regression complete · ${result.execution_ms.toFixed(1)} ms worker compute · ${result.splits.train.length} train / ${result.splits.test.length} test. Download JSON to preserve this run.`);};
 worker.onerror=e=>{e.preventDefault();failure(e.message||'Worker failed to load. Refresh or use a smaller CSV.');};timer=setTimeout(()=>failure('20-second compute limit reached. Use fewer rows/features.'),20000);
 worker.postMessage({text:csv,target:$('#target-column').value,features:choices(),source});
});
$('#cancel-custom').addEventListener('click',()=>{generation++;stop();status('Analysis cancelled. No results were retained.');});
$('#download-custom').addEventListener('click',()=>{if(!result)return;const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)+'\n'],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='mlr-custom-regression-run.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
function scatter(rows,residual=false){
 const ys=rows.map(r=>residual?r.residual:r.prediction),xs=rows.map(r=>residual?r.prediction:r.actual);
 let loX=Math.min(...xs),hiX=Math.max(...xs),loY=residual?Math.min(0,...ys):Math.min(...xs,...ys),hiY=residual?Math.max(0,...ys):Math.max(...xs,...ys);
 if(!residual){loX=loY;hiX=hiY;}const px=(hiX-loX||1)*.08,py=(hiY-loY||1)*.12;loX-=px;hiX+=px;loY-=py;hiY+=py;
 const x=v=>55+(v-loX)/(hiX-loX)*560,y=v=>20+(hiY-v)/(hiY-loY)*210;
 let svg='';for(let i=0;i<5;i++){const v=loY+(hiY-loY)*i/4;svg+=`<line x1="55" x2="615" y1="${y(v)}" y2="${y(v)}" stroke="#e6edf1"/><text x="48" y="${y(v)+4}" text-anchor="end">${Number(v.toPrecision(4))}</text>`;}
 svg+=residual?`<line x1="55" x2="615" y1="${y(0)}" y2="${y(0)}" stroke="#b98d53" stroke-dasharray="5 4"/>`:`<line x1="${x(loX)}" x2="${x(hiX)}" y1="${y(loX)}" y2="${y(hiX)}" stroke="#9caeb9" stroke-dasharray="5 4"/>`;
 svg+=rows.map((r,i)=>`<circle cx="${x(xs[i])}" cy="${y(ys[i])}" r="3" fill="#258c7d" opacity=".7"><title>row ${r.row_id}: ${fmt(ys[i])}</title></circle>`).join('');
 svg+=`<text x="335" y="255" text-anchor="middle">${residual?'Predicted target (source units)':'Actual target (source units)'}</text><text x="58" y="12">${residual?'Residual = actual − predicted':'Predicted target'}</text>`;
 return `<svg class="chart" viewBox="0 0 660 270" role="img" aria-label="${residual?'Holdout residuals versus prediction':'Holdout actual versus prediction'}">${svg}</svg>`;
}
function renderResult(r){
 const m=r.holdout.linear_regression,d=r.holdout.dummy_mean;
 const stats=[['Observations',r.rows,`${r.splits.train.length} train / ${r.splits.test.length} holdout`],['Model inputs',r.preprocessing.names.length,`${r.features.length} raw predictors`],['Holdout RMSE',fmt(m.rmse),'New OLS · lower is better'],['Holdout R²',fmt(m.r2),'New OLS · higher is better']];
 $('#overview').innerHTML=`<div class="section-heading"><h2>Custom Dataset · newly fitted regression</h2><p>Target: ${esc(r.target)} · source units</p></div><div class="stats">${stats.map(([name,value,note],i)=>`<div class="stat ${i>1?'accent':''}"><div class="stat-label">${name}</div><div class="stat-value" ${i===2?'data-custom-metric="rmse"':i===3?'data-custom-metric="r2"':''}>${value}</div><div class="stat-note">${note}</div></div>`).join('')}</div><div class="chart-grid">${card('Holdout actual vs. predicted',scatter(r.predictions))}${card('Holdout residuals vs. predicted',scatter(r.predictions,true))}</div><p class="notice">Exploratory custom analysis. Random split assumes independent observations. Repeated choices after viewing holdout invalidate an independent-test interpretation.</p>`;
 $('#features').innerHTML=card('Not Available · Custom Feature Selection',`<p class="notice">Regression MVP only. Pearson, F-Test, RFE, Forward SFS and LassoCV, rankings and Number of Features vs. RMSE/R² curves are not implemented for custom CSV. No fixed ranking or built-in JSON is substituted. Holdout is never scanned to select k.</p><h3>Actual fitted input columns (not a ranking)</h3><div class="pills">${r.preprocessing.names.map(n=>`<span class="pill">${esc(n)}</span>`).join('')}</div>`);
 const table=`<div class="table-wrap"><table><thead><tr><th>Model</th><th>MAE</th><th>MSE</th><th>RMSE</th><th>R²</th></tr></thead><tbody>${[['Fresh LinearRegression / OLS',m],['Mean Dummy',d]].map(([name,row])=>`<tr><td>${name}</td>${['mae','mse','rmse','r2'].map(k=>`<td>${fmt(row[k])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
 const predictions=`<div class="table-wrap"><table><thead><tr><th>Source row ID</th><th>Actual</th><th>Prediction</th><th>Residual</th></tr></thead><tbody>${r.predictions.slice(0,12).map(p=>`<tr><td>${p.row_id}</td><td>${fmt(p.actual)}</td><td>${fmt(p.prediction)}</td><td>${fmt(p.residual)}</td></tr>`).join('')}</tbody></table></div><p class="muted">First ${Math.min(r.predictions.length,12)} of ${r.predictions.length}. Download JSON for every prediction, split ID, coefficient and training imputation/encoding.</p>`;
 const model=`<p class="muted">${esc(r.engine)}<br>Seed 42 · 80/20 · training-only median/mode + drop-first one-hot<br>Rank: ${r.fit.rank} · scaled condition: ${fmt(r.fit.condition)}<br>Unknown test categories: ${r.unknown_category_count}<br>CSV SHA256: <code class="fingerprint">${r.source.sha256}</code></p><div class="table-wrap"><table><thead><tr><th>Input</th><th>Coefficient (source units)</th></tr></thead><tbody><tr><td>Intercept</td><td>${fmt(r.fit.intercept)}</td></tr>${r.preprocessing.names.map((name,i)=>`<tr><td>${esc(name)}</td><td>${fmt(r.fit.coefficients[i])}</td></tr>`).join('')}</tbody></table></div>`;
 $('#evaluation').innerHTML=card('Custom holdout evaluation · newly computed',table)+`<div class="bottom-grid" style="margin-top:20px">${card('Predictions & residuals',predictions)}${card('Reproducible model configuration',model)}</div><p class="notice">No training CV, nested CV or feature selection is claimed for this Custom Regression MVP. Built-in datasets retain their separately reviewed CV results.</p>`;
}

$('#dataset option[value=custom]').disabled=false;
