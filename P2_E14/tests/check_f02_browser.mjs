// Chromium launched with --headless --enable-unsafe-swiftshader --remote-debugging-port=19222.
import assert from 'node:assert/strict';
import {setTimeout as wait} from 'node:timers/promises';

const devtools=process.env.CHROME_CDP??'http://127.0.0.1:19222';
const web=process.env.F02_URL??'http://127.0.0.1:18714';
const [tab]=await (await fetch(devtools+'/json/list')).json();
const ws=new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
const jobs=new Map(),exceptions=[],failures=[];
let id=0;
ws.onmessage=e=>{
 const msg=JSON.parse(e.data);
 if(jobs.has(msg.id)){jobs.get(msg.id)(msg);jobs.delete(msg.id);}
 if(msg.method==='Runtime.exceptionThrown')exceptions.push(msg.params.exceptionDetails.text);
 if(msg.method==='Network.responseReceived' && msg.params.response.status>=400 &&
     msg.params.response.url.startsWith(web))failures.push(msg.params.response.url);
};
const call=(method,params={})=>new Promise(resolve=>{
 jobs.set(++id,resolve);ws.send(JSON.stringify({id,method,params}));
});
async function evalPage(expression){
 const data=await call('Runtime.evaluate',{expression,returnByValue:true});
 assert(!data.error && !data.result.exceptionDetails,JSON.stringify(data));
 return data.result.result.value;
}
async function until(x){
 for(let i=0;i<80;i++){if(await evalPage(x))return;await wait(250);}
 throw Error('No se observó: '+x);
}
try{
 await call('Page.enable');await call('Runtime.enable');await call('Network.enable');
 await call('Page.navigate',{url:web});
 await until("document.querySelectorAll('#e14-table tr').length===9");
 await until("document.querySelector('nav [data-tab=e14]').classList.contains('selected')");
 await evalPage("document.querySelector('nav [data-tab=f02]').click()");
 await until("document.querySelectorAll('#f02-table tr').length===10 && document.querySelector('#f02-render').innerText.includes('WebGL 0')");
 const details=await evalPage(`({
  plan:[...document.querySelector('#f02-plan').options].map(x=>x.value),
  row:document.querySelector('#f02-table tr[aria-selected=true]').innerText,
  charts:['risk','maxima','curves'].every(x=>document.querySelector('#f02-'+x+' svg path')),
  points:document.querySelectorAll('#f02-risk svg circle').length,
  case:document.querySelector('#f02-case').innerText
 })`);
 assert.equal(details.plan.length,9);assert(details.plan.includes('moderate_20'));
 assert(details.row.includes('49,599') && details.row.includes('19,158') && details.row.includes('0 %'));
 assert(details.charts && details.points===9 && details.case==='moderate_20 / M4_SS_m17');
 const full=await evalPage("document.querySelector('#f02-render').innerText");
 await evalPage(`document.querySelector('#f02-pipes').click(); document.querySelector('#f02-filter').value='slice';
   document.querySelector('#f02-filter').dispatchEvent(new Event('change'));`);
 const slice=await evalPage("document.querySelector('#f02-render').innerText");
 assert(slice.includes('WebGL 0') && slice.includes('slice') && slice!==full);
 assert(await evalPage("document.querySelectorAll('#f02-overlay line').length>0"));
 await evalPage(`document.querySelector('#f02-next').click();`);
 await until(`document.querySelector('#f02-render').innerText!==${JSON.stringify(slice)}`);
 const next=await evalPage("document.querySelector('#f02-render').innerText");
 await evalPage(`document.querySelector('#f02-filter').value='clip';
   document.querySelector('#f02-filter').dispatchEvent(new Event('change'));`);
 const clip=await evalPage("document.querySelector('#f02-render').innerText");
 assert(clip.includes('clip') && clip.includes('WebGL 0') && clip!==next);
 await evalPage(`document.querySelector('#f02-plan').value='curado_frio5';
    document.querySelector('#f02-plan').dispatchEvent(new Event('change'))`);
 assert(await evalPage("document.querySelector('#f02-selected').innerText.includes('85 %')"));
 assert(await evalPage("document.querySelector('#f02-visual').hidden"));
 await evalPage("document.querySelector('#f02-e14-view').click()");
 await until("document.querySelector('nav [data-tab=vista]').classList.contains('selected')");
 await until("document.querySelector('#renderer-status').innerText.includes('error GL 0')");
 await evalPage(`document.querySelector('nav [data-tab=e14]').click();
   document.querySelector('#e14-enumeration').click();`);
 assert.equal(await evalPage("document.querySelectorAll('#e14-table tr').length"),9);
 await evalPage("document.querySelector('nav [data-tab=vista]').click()");
 await until("document.querySelector('#renderer-status').innerText.includes('error GL 0')");
 assert.deepEqual(exceptions,[]);assert.deepEqual(failures,[]);
 console.log(JSON.stringify({status:'PASS',details,full,slice,next,clip,exceptions,failures},null,2));
}finally{ws.close();}
