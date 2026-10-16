/** Browser CSV regression MVP. No network, DOM, eval or saved experiment results. */
import {Matrix, SingularValueDecomposition, parseCSV} from './vendor/numerics.mjs';
export const LIMITS = Object.freeze({bytes:2*1024*1024,rows:2000,columns:40,features:12,encoded:20,categories:10,minRows:20});
const missing = value => value.trim() === '';
const decimal = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i;
const numeric = value => decimal.test(value.trim()) && Number.isFinite(Number(value));
const mean = values => values.reduce((s,v)=>s+v,0)/values.length;
const unique = values => [...new Set(values)];
const median = values => {const s=[...values].sort((a,b)=>a-b),i=Math.floor(s.length/2);return s.length%2?s[i]:(s[i-1]+s[i])/2;};
function fail(message){throw new Error(message);}

export function parse(text){
 if(new TextEncoder().encode(text).length>LIMITS.bytes)fail('CSV exceeds 2 MiB. Use a smaller dataset.');
 if(!text.trim())fail('CSV is empty.');
 const parsed=parseCSV(text.replace(/^\uFEFF/,''),{delimiter:',',skipEmptyLines:true});
 if(parsed.errors.length)fail(`Invalid CSV: ${parsed.errors[0].message}`);
 const [rawHeaders,...rows]=parsed.data;
 const headers=rawHeaders.map(h=>h.trim());
 if(headers.length<3||headers.length>LIMITS.columns)fail('CSV needs 3–40 columns (target plus at least two predictors).');
 if(headers.some(h=>!h)||unique(headers).length!==headers.length)fail('Column names must be nonempty and unique after trimming.');
 if(headers.some(h=>h.length>120))fail('Column names must be at most 120 characters.');
 if(rows.length<LIMITS.minRows||rows.length>LIMITS.rows)fail('CSV must contain 20–2000 data rows.');
 if(rows.some(r=>r.length!==headers.length))fail('CSV rows have inconsistent column counts. Check delimiters/quotes.');
 if(rows.some(r=>r.some(c=>/^(?:[+-]?infinity|[+-]?inf|nan)$/i.test(c.trim()))))fail('NaN/Infinity tokens are unsupported. Use an empty cell for missing predictors.');
 const columns=headers.map((name,index)=>{
  const values=rows.map(r=>r[index]).filter(v=>!missing(v));
  const isNumeric=values.length>0&&values.every(numeric);
  const mixed=values.some(numeric)&&!isNumeric;
  return {name,index,type:!values.length?'empty':mixed?'mixed':isNumeric?'numeric':'categorical',missing:rows.length-values.length,unique:unique(values).length};
 });
 return {headers,rows,columns};
}

// NumPy RandomState's legacy MT19937 + masked rejection Fisher-Yates.
// This reproduces sklearn train_test_split(random_state=42), including row order.
export function splitRows(length,seed=42){
 const state=new Uint32Array(624);state[0]=seed>>>0;
 for(let i=1;i<624;i++)state[i]=(Math.imul(1812433253,state[i-1]^(state[i-1]>>>30))+i)>>>0;
 let at=624;
 function next(){
  if(at===624){for(let i=0;i<624;i++){const y=(state[i]&0x80000000)|(state[(i+1)%624]&0x7fffffff);state[i]=state[(i+397)%624]^(y>>>1)^((y&1)?0x9908b0df:0);}at=0;}
  let y=state[at++];y^=y>>>11;y^=(y<<7)&0x9d2c5680;y^=(y<<15)&0xefc60000;y^=y>>>18;return y>>>0;
 }
 const ids=Array.from({length},(_,i)=>i);
 for(let i=length-1;i>0;i--){let mask=i;mask|=mask>>>1;mask|=mask>>>2;mask|=mask>>>4;mask|=mask>>>8;mask|=mask>>>16;let j;do{j=next()&mask;}while(j>i);[ids[i],ids[j]]=[ids[j],ids[i]];}
 const n=Math.ceil(length*.2);return {train:ids.slice(n),test:ids.slice(0,n)};
}

function fitPreprocessor(data,features,train){
 const specs=[],names=[];
 for(const feature of features){
  const column=data.columns.find(c=>c.name===feature);
  if(!column||!['numeric','categorical'].includes(column.type))fail(`Unsupported predictor: ${feature}. Use purely numeric or nonnumeric categorical columns.`);
  const values=train.map(i=>data.rows[i][column.index].trim()).filter(v=>v!=='');
  if(!values.length)fail(`Training feature is entirely missing: ${feature}`);
  if(column.type==='numeric'){
   const numbers=values.map(Number),value=median(numbers);
   if(unique(numbers).length<2)fail(`Constant training feature: ${feature}`);
   specs.push({name:feature,index:column.index,type:'numeric',median:value});names.push(feature);
  }else{
   const cats=unique(values).sort();
   if(cats.length<2||cats.length>LIMITS.categories)fail(`Categorical predictor ${feature} needs 2–10 training categories. Remove IDs/high-cardinality columns.`);
   const counts=cats.map(c=>values.filter(v=>v===c).length),mode=cats[counts.indexOf(Math.max(...counts))];
   specs.push({name:feature,index:column.index,type:'categorical',mode,categories:cats,reference:cats[0]});
   names.push(...cats.slice(1).map(c=>`${feature}=${c}`));
  }
 }
 if(names.length>LIMITS.encoded)fail('One-hot encoding exceeds the 20-input limit. Select fewer features/categories.');
 if(unique(names).length!==names.length)fail('Encoded feature names collide. Rename the source columns/categories.');
 return {specs,names};
}
function transform(data,ids,preprocess){
 let unknown=0;
 const values=ids.map(i=>preprocess.specs.flatMap(s=>{
  const raw=data.rows[i][s.index].trim();
  if(s.type==='numeric')return [raw===''?s.median:Number(raw)];
  const value=raw===''?s.mode:raw;if(!s.categories.includes(value))unknown++;
  return s.categories.slice(1).map(c=>value===c?1:0);
 }));
 return {values,unknown};
}
export function metrics(actual,predicted){
 if(actual.length!==predicted.length||!actual.length||predicted.some(v=>!Number.isFinite(v)))fail('Non-finite or invalid model predictions. Reduce extreme values.');
 const residual=actual.map((a,i)=>a-predicted[i]),mse=mean(residual.map(r=>r*r)),den=actual.reduce((s,y)=>s+(y-mean(actual))**2,0);
 const result={mae:mean(residual.map(Math.abs)),mse,rmse:Math.sqrt(mse),r2:den>0&&actual.length>=2?1-residual.reduce((s,r)=>s+r*r,0)/den:null,n:actual.length};
 if(!Number.isFinite(result.mae)||!Number.isFinite(mse))fail('Metric overflow. Rescale extreme numeric values before analysis.');
 return result;
}

export function analyze(data,target,features){
 if(!Array.isArray(features)||features.length<2||features.length>LIMITS.features||unique(features).length!==features.length)fail('Choose 2–12 distinct raw predictor columns.');
 if(features.includes(target))fail('Target must not be included among Features.');
 const yColumn=data.columns.find(c=>c.name===target);
 if(!yColumn||yColumn.type!=='numeric'||yColumn.missing)fail('Target must be numeric, complete and finite. Choose a continuous target.');
 const y=data.rows.map(r=>Number(r[yColumn.index]));
 if(unique(y).length<5)fail('Target needs at least five distinct values; this MVP supports continuous regression, not classification.');
 // Structural duplicate checks precede the split; never remove rows based on test scores.
 const featureIndices=features.map(f=>data.headers.indexOf(f));
 if(featureIndices.some(i=>i<0))fail('Unknown feature column.');
 const keys=data.rows.map(r=>JSON.stringify(featureIndices.map((i,j)=>data.columns[i].type==='numeric'&&!missing(r[i])?Number(r[i]):r[i].trim())));
 if(unique(keys).length!==keys.length)fail('Duplicate predictor rows require a group/split review; this MVP cannot safely analyze them.');
 const split=splitRows(data.rows.length),preprocessing=fitPreprocessor(data,features,split.train);
 if(split.train.length<Math.max(16,3*(preprocessing.names.length+1)))fail('Insufficient training rows: require at least 3 × (encoded inputs + intercept), and 16 training rows.');
 const train=transform(data,split.train,preprocessing),test=transform(data,split.test,preprocessing);
 const actual=split.test.map(i=>y[i]),trainingY=split.train.map(i=>y[i]),ym=mean(trainingY);
 if(unique(trainingY).length<2||unique(actual).length<2)fail('Target is constant in a training/test partition; R² cannot support this split.');
 const means=preprocessing.names.map((_,j)=>mean(train.values.map(r=>r[j])));
 const scales=means.map((m,j)=>Math.sqrt(mean(train.values.map(r=>(r[j]-m)**2))));
 if(scales.some(s=>!Number.isFinite(s)||s===0))fail('A transformed training column is constant/non-finite. Remove it.');
 const design=train.values.map(r=>r.map((v,j)=>(v-means[j])/scales[j]));
 const svd=new SingularValueDecomposition(new Matrix(design),{autoTranspose:true});
 if(svd.rank!==preprocessing.names.length||!Number.isFinite(svd.condition)||svd.condition>1e8)fail('Rank-deficient or ill-conditioned predictors. Remove collinear variables.');
 const standardized=svd.solve(Matrix.columnVector(trainingY.map(v=>v-ym))).to1DArray();
 const coefficients=standardized.map((v,j)=>v/scales[j]),intercept=ym-coefficients.reduce((s,c,j)=>s+c*means[j],0);
 const predictions=test.values.map(r=>ym+standardized.reduce((s,c,j)=>s+c*(r[j]-means[j])/scales[j],0));
 const dummy=actual.map(()=>ym);
 return {schema_version:1,engine:'MLR-JS-OLS-v1 / ml-matrix 6.12.1 SVD',target,features:[...features],rows:data.rows.length,
  configuration:{seed:42,test_size:.2,split_algorithm:'NumPy RandomState MT19937 permutation; ceil(0.2*n) test rows',
   numeric:'training median imputation',categorical:'training most frequent; lexical ties, sorted drop-first one-hot; unknown -> all zero',
   estimator:'centered/scaled SVD OLS, fit intercept; coefficients converted to source units',feature_selection:'Not Available: Regression MVP only; holdout is not used to choose k',units:'user source units; not verified'},
  splits:split,preprocessing,fit:{means,scales,coefficients,intercept,rank:svd.rank,condition:svd.condition,training_target_mean:ym},
  unknown_category_count:test.unknown,holdout:{linear_regression:metrics(actual,predictions),dummy_mean:metrics(actual,dummy)},
  predictions:split.test.map((id,i)=>({row_id:id,actual:actual[i],prediction:predictions[i],residual:actual[i]-predictions[i],dummy_prediction:ym})),
  warnings:['Historical/sample random split only; no group/time/spatial generalization claim.','Repeated reruns after viewing holdout make it exploratory, not a new independent test.',...(test.unknown?['Unknown test categories map to the reference all-zero code.']:[])]};
}
