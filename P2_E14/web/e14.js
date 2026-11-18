// Interfaz de resultados calculados por Python. No contiene integrador térmico.
import {chart} from './charts.js';
export async function initE14({api,post,error,tab,loadResult,busy}){
 const $=id=>document.getElementById(id),fmt=(x,n=3)=>x==null?'—':Number(x).toLocaleString('es-CL',{minimumFractionDigits:n,maximumFractionDigits:n});
 const info=await api('/api/e14/bootstrap');let current=info.reports.monte_carlo??info.reports.enumeration,estimated=null;
 let jobs=[...info.jobs];function jobsMenu(){$('e14-jobs').replaceChildren(...jobs.map(j=>new Option(j.id.slice(0,8)+' · '+j.status,j.id)));}jobsMenu();
 const plans=info.configuration.plans;$('e14-plan').replaceChildren(new Option('Todos los planes','all'),...plans.map(p=>new Option(p.id,p.id)));$('e14-plan').value='curado_frio5';
 $('e14-scenario').replaceChildren(...info.scenarios.map(s=>new Option(s.id+' · peso '+fmt(s.weight*100,2)+' %',s.id)));$('e14-scenario').value=info.scenarios.find(s=>s.curve==='M4_SS'&&s.member===17).id;
 $('e14-model').textContent=info.model;$('e14-hpc').textContent=info.HPC;
 function parameters(){
  const number=id=>{if(!$(id).value.trim()||!Number.isFinite(Number($(id).value)))throw Error('Completa los parámetros numéricos.');return Number($(id).value);};
  const optional=id=>$(id).value.trim()===''?null:number(id);
  return {plan_ids:$('e14-plan').value==='all'?plans.map(p=>p.id):[$('e14-plan').value],N:number('e14-N'),master_seed:number('e14-seed'),kind:$('e14-kind').value,spacing_m:$('e14-spacing').value.split(',').map(Number),temperature_C:optional('e14-temperature'),insulation_m:optional('e14-insulation'),remove_at_h:optional('e14-remove')};
 }
 function dirty(){estimated=null;$('e14-run').disabled=true;$('e14-dirty').hidden=false;$('e14-cost').textContent='Inputs modificados; estimar nuevamente. Los resultados visibles mantienen su procedencia anterior.';}
 async function estimate(){const r=await post('/api/e14/estimate',{parameters:parameters()});estimated=r;$('e14-cost').textContent=r.draws_per_plan+' realizaciones/plan · '+r.unique_physics+' inputs físicos únicos · '+r.cache_hits+' reutilizados · '+r.new_physics+' nuevos · coste estimado '+fmt(r.estimated_s,0)+' s. '+r.meaning;$('e14-run').disabled=false;return r;}
 function render(r,origin){current=r;$('e14-origin').textContent=origin;const body=$('e14-table');body.replaceChildren();if(!r){body.textContent='Resultados aún en cálculo';return;}
  const head=document.createElement('tr');['Plan','D [h]','Tmax [°C]','ΔTmax [°C]','gT mínimo [°C]','gΔ mínimo [°C]','P(T>70)','P(ΔT>20)','Pf OR','IC95% MC'].forEach(t=>{const th=document.createElement('th');th.textContent=t;head.append(th);});body.append(head);
  for(const p of r.plans){const tr=document.createElement('tr');[p.plan,fmt(p.D_h),fmt(p.Tmax_C),fmt(p.delta_C),fmt(70-p.Tmax_C),fmt(20-p.delta_C),fmt(p.P_T*100,2)+' %',fmt(p.P_delta*100,2)+' %',fmt(p.P_joint*100,2)+' %',p.CI?'['+p.CI.map(x=>fmt(x*100,3)).join('; ')+'] %':'No aplica: enumeración exacta'].forEach(t=>{const td=document.createElement('td');td.textContent=t;tr.append(td);});body.append(tr);}
  $('e14-prob-plan').replaceChildren(...r.plans.map(p=>new Option(p.plan,p.plan)));draw();
 }
 function draw(){
  if(!current)return;const p=current.plans.find(p=>p.plan===$('e14-prob-plan').value)??current.plans[0];const points=p.Pf_N;
  if(!points){$('e14-PfN').textContent='Enumeración ponderada exacta: no hay error de muestreo ni intervalo Monte Carlo.';$('e14-CI').textContent='Pesos hipotéticos declarados: este resultado exacto tampoco incluye error numérico ni incertidumbre experimental.';return;}
  const x=points.map(q=>Math.log10(q.N));chart($('e14-PfN'),[
   {name:'Pf(N)',color:'#ad3b28',x,y:points.map(q=>100*q.Pf)},
   {name:'IC95% inferior',color:'#297c93',x,y:points.map(q=>100*q.CI[0]),dashed:true},
   {name:'IC95% superior',color:'#297c93',x,y:points.map(q=>100*q.CI[1]),dashed:true},
   {name:'Criterio conjunto 5 %',color:'#555',x:[x[0],x.at(-1)],y:[5,5]}],{xLabel:'log10 N (1=10, 2=100, 3=1000, 4=10000)',xUnit:'log10 N',yLabel:'Probabilidad del modelo [%]'});
  $('e14-CI').textContent=p.interval_type+' · N='+p.N+' · fallas='+p.failures+'. La enumeración es la referencia exacta del modelo; el IC no representa incertidumbre experimental o numérica.';
 }
 async function seeds(id='official'){const b=await api('/api/e14/samples/'+id);$('e14-samples').textContent='Semilla maestra '+b.master_seed+' · '+b.N+' realizaciones; primeras '+b.samples.length+':\n'+b.samples.map(s=>'R'+s.realization+' → '+s.scenario+' · '+s.seed_words.join(',')).join('\n');}
 render(current,'Resultados oficiales E14; hipótesis y configuración guardadas.');if(info.reports.monte_carlo)await seeds();
 document.querySelectorAll('[data-e14-input]').forEach(e=>e.addEventListener('input',dirty));$('e14-prob-plan').addEventListener('change',draw);
 $('e14-estimate').addEventListener('click',async()=>{try{error();await estimate();}catch(e){error(e.message);}});
 $('e14-run').addEventListener('click',async()=>{
  if(!estimated)return;busy(true);$('e14-run').disabled=true;$('e14-cancel').hidden=false;
  try{error();const j=await post('/api/e14/run',{parameters:parameters(),fingerprint:estimated.fingerprint});$('e14-cancel').dataset.job=j.id;jobs.unshift(j);jobsMenu();
   for(;;){const s=await api('/api/jobs/'+j.id);$('e14-progress').textContent=s.progress?s.status+' · '+s.progress.completed_chunks+'/'+s.progress.total_chunks+' chunks · '+s.message:s.message;
    if(s.status==='passed'){jobs[0].status='passed';jobsMenu();render(await api('/api/e14/results/'+j.id),'Ejecución nueva '+j.id+'; resultados calculados y validados.');await seeds(j.id);$('e14-dirty').hidden=true;break;}
    if(['failed','cancelled'].includes(s.status))throw Error(s.message);await new Promise(r=>setTimeout(r,700));}
  }catch(e){error(e.message);}finally{busy(false);estimated=null;$('e14-cancel').hidden=true;}
 });
 $('e14-cancel').addEventListener('click',async()=>{try{await post('/api/cancel/'+$('e14-cancel').dataset.job,{});$('e14-progress').textContent='Cancelación solicitada; se espera al input actual sin perder casos completos.';}catch(e){error(e.message);}});
 $('e14-diagnostic').addEventListener('click',async()=>{
  busy(true);$('e14-diagnostic').disabled=true;
  try{error();await estimate();const j=await post('/api/e14/diagnostic',{parameters:parameters(),scenario:$('e14-scenario').value});
   for(;;){const q=await api('/api/jobs/'+j.id);$('e14-progress').textContent=q.message+' · Un escenario no estima Pf.';if(q.status==='passed'){await loadResult(q.id);tab('vista');$('e14-dirty').hidden=false;$('e14-dirty').textContent='3D y curvas son del diagnóstico nuevo; la tabla de riesgo mantiene su procedencia y no fue recalculada.';break;}if(['failed','cancelled'].includes(q.status))throw Error(q.message);await new Promise(r=>setTimeout(r,700));}
  }catch(e){error(e.message);}finally{busy(false);$('e14-diagnostic').disabled=false;}
 });
 $('e14-official').addEventListener('click',()=>{render(info.reports.monte_carlo??info.reports.enumeration,'Resultados oficiales guardados');seeds().catch(e=>error(e.message));});
 $('e14-enumeration').addEventListener('click',()=>render(info.reports.enumeration,'Enumeración ponderada exacta oficial: 24 átomos por plan, sin IC Monte Carlo.'));
 $('e14-load-job').addEventListener('click',async()=>{try{const id=$('e14-jobs').value;render(await api('/api/e14/results/'+id),'Job guardado '+id);await seeds(id);}catch(e){error(e.message);}});
 $('e14-resume-job').addEventListener('click',async()=>{busy(true);try{error();const j=await post('/api/e14/resume',{id:$('e14-jobs').value});$('e14-dirty').hidden=false;$('e14-dirty').textContent='Reanudando configuración guardada; no se aplican inputs editados.';for(;;){const q=await api('/api/jobs/'+j.id);$('e14-progress').textContent=q.message;if(q.status==='passed'){render(await api('/api/e14/results/'+j.id),'Job reanudado '+j.id);await seeds(j.id);break;}if(['failed','cancelled'].includes(q.status))throw Error(q.message);await new Promise(r=>setTimeout(r,700));}}catch(e){error(e.message);}finally{busy(false);}});
 $('e14-discard-job').addEventListener('click',async()=>{try{const id=$('e14-jobs').value,p=await post('/api/discard-plan',{result:id});if(!confirm('¿Retirar la prueba '+id+'? '+p.files.length+' archivos, '+fmt(p.bytes/1e6)+' MB. Se conserva la biblioteca científica y el oficial.'))return;await post('/api/discard',{result:id,fingerprint:p.fingerprint});jobs=jobs.filter(j=>j.id!==id);jobsMenu();}catch(e){error(e.message);}});
 window.addEventListener('resize',()=>{if(!document.querySelector('[data-panel="e14"]').hidden)draw();});return {draw,info};
}
