'use strict';
const tabs = [...document.querySelectorAll('[role="tab"]')];
const selector = document.querySelector('#dataset');
const repository = 'https://github.com/wupojung/AIoT-DIC2-MultipleLR/blob/main/';
const methods = ['Pearson', 'F-Test', 'RFE', 'SFS', 'LassoCV'];
const colors = ['#288f87', '#dfaa52', '#638ac5', '#b47ea8', '#db7863'];
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const featureName = name => name.replace(/^(numeric|state)__/, '').replace(/^State_/, 'State: ');
const number = (value, digits = 4) => Number(value).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
const stat = (label, value, note, accent = false, key = '') => `<div class="stat ${accent ? 'accent' : ''}"><div class="stat-label">${label}</div><div class="stat-value" ${key ? `data-metric="${key}"` : ''}>${value}</div><div class="stat-note">${note}</div></div>`;
const card = (title, subtitle, body) => `<div class="card"><h3>${title}</h3><p class="card-sub">${subtitle}</p>${body}</div>`;
const heading = (title, subtitle) => `<div class="section-heading"><h2>${title}</h2><p>${subtitle}</p></div>`;

function activateTab(tab) {
  for (const item of tabs) {
    const selected = item === tab;
    item.setAttribute('aria-selected', String(selected));
    item.tabIndex = selected ? 0 : -1;
    document.getElementById(item.getAttribute('aria-controls')).hidden = !selected;
  }
}
for (const [index, tab] of tabs.entries()) {
  tab.addEventListener('click', () => activateTab(tab));
  tab.addEventListener('keydown', event => {
    let next;
    if (['ArrowRight', 'ArrowDown'].includes(event.key)) next = (index + 1) % tabs.length;
    if (['ArrowLeft', 'ArrowUp'].includes(event.key)) next = (index - 1 + tabs.length) % tabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = tabs.length - 1;
    if (next === undefined) return;
    event.preventDefault();
    activateTab(tabs[next]);
    tabs[next].focus();
  });
}

function chart(data, metric, id) {
  const width = 660, height = 260, left = 58, right = 18, top = 18, bottom = 42;
  const rows = data.curves;
  const values = rows.map(row => row[`${metric}_mean`]);
  const low = Math.min(...values), high = Math.max(...values);
  const pad = (high - low || 1) * .16;
  const min = low - pad, max = high + pad;
  const n = data.encoded_features.length;
  const x = k => left + (k - 1) / (n - 1) * (width - left - right);
  const y = value => top + (max - value) / (max - min) * (height - top - bottom);
  let drawing = '';
  for (let i = 0; i <= 4; i++) {
    const value = min + (max - min) * i / 4, py = y(value);
    drawing += `<line x1="${left}" x2="${width-right}" y1="${py}" y2="${py}" stroke="#e9eff3"/><text x="${left-10}" y="${py+3}" text-anchor="end">${number(value, metric === 'r2' ? 3 : (high > 100 ? 0 : 1))}</text>`;
  }
  const full = rows.find(row => row.method === 'All Features');
  drawing += `<line x1="${left}" x2="${width-right}" y1="${y(full[`${metric}_mean`])}" y2="${y(full[`${metric}_mean`])}" stroke="#9cabb6" stroke-dasharray="5 5"/>`;
  methods.forEach((method, i) => {
    const points = rows.filter(row => row.method === method).sort((a,b) => a.k-b.k);
    drawing += `<polyline data-method="${method}" fill="none" stroke="${colors[i]}" stroke-width="2" stroke-linejoin="round" points="${points.map(row => `${x(row.k)},${y(row[`${metric}_mean`])}`).join(' ')}"/>`;
    drawing += points.map(row => `<circle cx="${x(row.k)}" cy="${y(row[`${metric}_mean`])}" r="3" fill="white" stroke="${colors[i]}" stroke-width="1.7"><title>${method}, k=${row.k}: ${number(row[`${metric}_mean`], 6)}</title></circle>`).join('');
  });
  for (let k = 1; k <= n; k++) drawing += `<text x="${x(k)}" y="${height-23}" text-anchor="middle">${k}</text>`;
  drawing += `<text class="axis-title" x="${(left+width-right)/2}" y="${height-4}" text-anchor="middle">Number of encoded features</text>`;
  return `<svg class="chart" data-chart="${metric}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="${id}"><title id="${id}">${escapeHTML(data.name)}: 5-fold training CV ${metric.toUpperCase()} versus number of features</title>${drawing}</svg><div class="legend">${methods.map((method,i) => `<span><i style="background:${colors[i]}"></i>${method}</span>`).join('')}<span><i style="background:#9cabb6"></i>All features</span></div>`;
}
function curves(data, prefix) {
  return `<div class="chart-grid">${card('Feature count vs. RMSE', `5-fold training CV · ${escapeHTML(data.units)} · lower is better`, chart(data, 'rmse', `${prefix}-rmse`))}${card('Feature count vs. R²', '5-fold training CV · coefficient of determination · higher is better', chart(data, 'r2', `${prefix}-r2`))}</div>`;
}
function featurePills(features, selected = false) {
  return `<div class="pills">${features.map(name => `<span class="pill ${selected ? 'selected' : ''}">${escapeHTML(featureName(name))}</span>`).join('')}</div>`;
}
function metricTable(rows) {
  return `<div class="table-wrap"><table><thead><tr><th>Model / assessment</th><th>MAE</th><th>MSE</th><th>RMSE</th><th>R²</th></tr></thead><tbody>${rows.map(([label,row]) => `<tr><td>${label}</td>${['mae','mse','rmse','r2'].map(metric => `<td>${number(row[metric], metric === 'mse' ? 2 : 4)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function render(data) {
  document.body.dataset.dataset = data.dataset_id;
  document.querySelector('#dataset-description').textContent = `${data.subtitle} · Target: ${data.target}`;
  const base = data.holdout['All Features'];
  const sources = `<div class="source-links"><a href="${repository}${data.report}" target="_blank" rel="noreferrer">Read analysis report ↗</a><a href="${repository}${data.baseline_report}" target="_blank" rel="noreferrer">Baseline evidence ↗</a><a href="data/${data.dataset_id}.json">Download dashboard JSON ↧</a></div>`;
  const note = `<p class="notice">${escapeHTML(data.note)}</p>`;
  document.querySelector('#overview').innerHTML = heading('Experiment overview', '80 / 20 split · random seed 42 · LinearRegression') +
    `<div class="stats">${stat('Observations', number(data.rows,0), `${data.train_rows} train / ${data.test_rows} holdout`)}${stat('Model inputs', `${data.encoded_features.length}<small>features</small>`, `${data.raw_features.length} raw predictors${data.excluded.length ? ' · B excluded' : ' · State one-hot'}`)}${stat('Holdout RMSE', number(base.rmse), 'All-feature baseline · lower is better', true, 'baseline-rmse')}${stat('Holdout R²', number(base.r2), 'All-feature baseline · higher is better', true, 'baseline-r2')}</div>` +
    heading('How feature count changes performance', 'Training CV only · holdout never used to choose k') + curves(data, 'overview') +
    `<div class="bottom-grid">${card('A reproducible learning workflow', 'CRISP-DM · six phases, one evidence trail', `<div class="workflow">${['Business','Data','Prepare','Model','Evaluate','Communicate'].map((name,i) => `<div class="step"><b>0${i+1}</b>${name}</div>`).join('')}</div><p class="muted">Fold-local preprocessing and feature selection. Final estimator: LinearRegression. Human review remains separate from technical verification.</p>`)}${card('Training-selected model', 'Chosen with 3-fold full-training CV, before holdout', `<div class="info-line"><span>Selector / feature count</span><strong>${data.choice.method} / k = ${data.choice.k}</strong></div><div class="info-line"><span>Selection CV RMSE (optimistic)</span><strong>${number(data.choice.rmse_mean)}</strong></div><div class="info-line"><span>Nested outer RMSE ± fold std</span><strong>${number(data.nested.rmse.mean)} ± ${number(data.nested.rmse.std)}</strong></div>`)}</div>` + note + sources;
  document.querySelector('#features').innerHTML = heading('Feature Selection', 'Five genuine selectors · the same final LinearRegression estimator') + curves(data, 'features') +
    `<div class="bottom-grid">${card('Full-training feature ranking', 'These are actual fitted orders; fold-specific subsets are in the source report.', `<div class="method-controls" role="group" aria-label="Feature ranking method">${methods.map((method,i) => `<button type="button" data-rank-method="${method}" aria-pressed="${i===0}">${method}</button>`).join('')}</div><div id="ranking"></div>`)}${card('Frozen final selection', 'Selected by training CV; no search over holdout scores', `<div class="info-line"><span>Method</span><strong>${data.choice.method}</strong></div><div class="info-line"><span>Number of features</span><strong>${data.choice.k} / ${data.encoded_features.length}</strong></div>${featurePills(data.choice.features,true)}<p class="muted">LassoCV full-training alpha: ${number(data.lasso_alpha,6)}. Ranking uses absolute standardized coefficients; zero coefficients may appear at the tail. RFE order is reverse elimination; SFS is greedy entry.</p>`)}</div>` + note + sources;
  const evaluationRows = [['All-feature LinearRegression',data.holdout['All Features']]];
  if (data.holdout.Selected) evaluationRows.push([`Selected LinearRegression (${data.choice.method}, k=${data.choice.k})`,data.holdout.Selected]);
  evaluationRows.push(['Mean-prediction dummy',data.holdout.Dummy]);
  document.querySelector('#evaluation').innerHTML = heading('Evaluation', 'Different assessments answer different questions') +
    `<div class="metric-summary">${card('Training cross-validation', 'All-feature baseline · 5 folds, mean fold scores', `<div class="info-line"><span>RMSE</span><strong data-metric="cv-rmse">${number(data.baseline_cv.rmse_mean)}</strong></div><div class="info-line"><span>R²</span><strong data-metric="cv-r2">${number(data.baseline_cv.r2_mean)}</strong></div><p class="muted">Same training folds across fixed method/k candidates. Units: ${escapeHTML(data.units)}.</p>`)}${card('Nested model-selection assessment', 'Outer 5 / inner 3 folds; selectors use local 3-fold CV', `<div class="info-line"><span>Outer RMSE ± fold std</span><strong>${number(data.nested.rmse.mean)} ± ${number(data.nested.rmse.std)}</strong></div><div class="info-line"><span>Outer R² ± fold std</span><strong>${number(data.nested.r2.mean)} ± ${number(data.nested.r2.std)}</strong></div><p class="muted">Assesses selection within training, independently of the final holdout.</p>`)}</div>` +
    card('Final holdout results', `${data.test_rows} untouched test observations · ${escapeHTML(data.units)} · one evaluation per predeclared model`, metricTable(evaluationRows) + (!data.holdout.Selected ? '<p class="notice">Selected-model holdout: not evaluated. Issue #4 reports training-only feature selection; the holdout above belongs to the accepted Issue #3 all-feature baseline.</p>' : '<p class="muted">The selected model was frozen before holdout prediction. Differences from baseline are small and do not establish a stable improvement.</p>')) +
    `<div class="bottom-grid" style="margin-top:20px">${card('Model feature schema', `Target: ${data.target} · ${data.encoded_features.length} encoded inputs`, featurePills(data.encoded_features))}${card('Interpretation & limitations', 'Prediction is not causation', `<p class="muted">${escapeHTML(data.note)}</p><p class="muted">Random historical sample evaluation; not evidence of temporal or geographic generalization. Metrics from different target units must not be compared across datasets.</p>`)}</div>` + sources;
  function showRanking(method) {
    document.querySelectorAll('[data-rank-method]').forEach(button => button.setAttribute('aria-pressed',String(button.dataset.rankMethod === method)));
    document.querySelector('#ranking').innerHTML = `<div class="table-wrap"><table><thead><tr><th>Rank / k</th><th>Added feature</th><th>Cumulative count</th></tr></thead><tbody>${data.orders[method].map((name,i) => `<tr><td>${String(i+1).padStart(2,'0')}</td><td>${escapeHTML(featureName(name))}</td><td>${i+1} / ${data.encoded_features.length}</td></tr>`).join('')}</tbody></table></div>`;
  }
  document.querySelectorAll('[data-rank-method]').forEach(button => button.addEventListener('click', () => showRanking(button.dataset.rankMethod)));
  showRanking('Pearson');
}
async function start() {
  selector.disabled = true;
  try {
    const datasets = new Map(await Promise.all(['50_startups','boston_housing'].map(async id => {
      const response = await fetch(`data/${id}.json`);
      if (!response.ok) throw new Error(`Cannot load ${id}: HTTP ${response.status}`);
      const data = await response.json();
      if (data.dataset_id !== id || data.schema_version !== 1 || !data.curves.length) throw new Error(`Invalid experiment data: ${id}`);
      return [id,data];
    })));
    selector.addEventListener('change', () => render(datasets.get(selector.value)));
    render(datasets.get(selector.value));
    document.querySelector('#content').hidden = false;
    document.querySelector('#status').textContent = '';
    selector.disabled = false;
  } catch (error) {
    document.querySelector('#status').textContent = `Unable to load experiment data. ${error.message}. Serve this site over HTTP; direct file opening is not supported.`;
    console.error(error);
  }
}
start();
