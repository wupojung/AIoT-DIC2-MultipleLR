import {parse, analyze} from './custom-engine.mjs';
self.onmessage = ({data}) => {
 const started=performance.now();
 try {
  const result=analyze(parse(data.text),data.target,data.features);
  self.postMessage({result:{...result,source:data.source,executed_at:new Date().toISOString(),execution_ms:performance.now()-started}});
 } catch(error){self.postMessage({error:error.message||String(error)});}
};
