// Panel de decisión de la misma aplicación. Todos los resultados vienen de Python.
import {chart} from './charts.js';
export async function initE13({api,post,error,tab,loadResult,busy}){
 const $=id=>document.getElementById(id),fmt=(x,n=2)=>x==null?'—':Number(x).toLocaleString('es-CL',{maximumFractionDigits:n,minimumFractionDigits:n});
 const info=await api('/api/e13/bootstrap');let estimate=null,current=info.official,changed=false;
 const colors=['#b74733','#2371a6','#2d9b7d','#9561a9','#c28f19','#496274','#bd668b','#648e40'];
 const plans=info.configuration.plans;$('e13-plan').replaceChildren(...plans.map(p=>new Option(p.id+' · D='+fmt(p.D_h)+' h',p.id)));
 $('e13-scenario').replaceChildren(...info.scenarios.map(s=>new Option(s.id+' · peso '+fmt(s.weight*100,3)+' %',s.id)));$('e13-scenario').value=info.scenarios.find(s=>s.curve==='M2_SS').id;
 $('e13-model').textContent=info.meaning+' · Independencia material/clima asumida; enumeración exacta de este modelo discreto, sin garantía de confiabilidad real.';
 $('e13-climate-meta').textContent='GFS 0.5°, original de 31 miembros. Medoides '+info.reduction.medoids.join(', ')+'; pesos '+info.reduction.weights.map(w=>fmt(w*100,2)+' %').join(' / ')+'. '+info.climate[0].metadata.representativeness;
 $('e13-weights').textContent=info.scenarios.map(s=>s.id+': '+fmt(s.weight*100,4)+' %').join(' · ');
 function dirty(){changed=true;estimate=null;$('e13-run').disabled=true;$('e13-dirty').hidden=false;$('e13-estimate').textContent='Inputs modificados: estimar antes de ejecutar. La tabla conserva su procedencia anterior.';}
 function choose(){const p=plans.find(x=>x.id===$('e13-plan').value);$('e13-rate').value=p.rate_m3_h;$('e13-wait').value=p.partition==='single'?0:p.id==='E12_referencia'?0.5:p.id==='protegido_rapido'?.5:p.id==='propuesto_6h'?6:12;$('e13-initial').value=p.initial_C[0];$('e13-remove').value=p.remove_at_h;$('e13-initial').disabled=p.id==='E12_referencia';$('e13-wait').disabled=p.partition==='single'||p.id==='E12_referencia';dirty();}
 $('e13-plan').value='propuesto_6h';choose();changed=false;$('e13-dirty').hidden=true;
 function parameters(){return {plan:$('e13-plan').value,rate_m3_h:Number($('e13-rate').value),wait_h:Number($('e13-wait').value),initial_C:Number($('e13-initial').value),remove_at_h:Number($('e13-remove').value),spacing_m:$('e13-spacing').value.split(',').map(Number),horizon_h:Number($('e13-horizon').value)};}
 async function preflight(){const p=await post('/api/e13/prepare',parameters());estimate=await post('/api/e13/estimate',{configuration:p.configuration});$('e13-estimate').textContent='D físico = '+fmt(estimate.D_h[0],3)+' h; '+estimate.occupied_cells+' celdas; '+estimate.cases+' escenarios. Coste estimado '+fmt(estimate.estimated_s/60,1)+' min (un escenario ≈'+fmt(estimate.estimated_s/estimate.cases,1)+' s).';$('e13-run').disabled=false;return estimate;}
 function table(report,origin){current=report;$('e13-origin').textContent=origin;$('e13-conclusion').textContent=report?.conclusion??'Estudio aún en cálculo';const host=$('e13-table');host.replaceChildren();
  if(!report)return;const headers=['Plan','D [h]','Máx. Tmax [°C]','Máx. ΔT [°C]','P(T>70)','P(ΔT>20)','Pf conjunta','Estado'];const head=document.createElement('tr');headers.forEach(h=>{const e=document.createElement('th');e.textContent=h;head.append(e);});host.append(head);
  for(const p of report.plans){const tr=document.createElement('tr');[p.plan,fmt(p.D_h,3),fmt(p.Tmax_C,3),fmt(p.delta_C,3),fmt(100*p.P_T)+' %',fmt(100*p.P_delta)+' %',fmt(100*p.P_joint)+' %',p.feasible?'Factible en el modelo':'No factible'].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td);});host.append(tr);}
  $('e13-best').textContent=report.best_feasible?'Menor duración factible: '+report.best_feasible.plan+' · '+fmt(report.best_feasible.D_h)+' h':'Sin plan factible. El caso 3D es ilustrativo y no constituye una recomendación.';draw();
 }
 function draw(){chart($('e13-source-chart'),Object.entries(info.sources).map(([name,s],i)=>({name,color:colors[i],x:s.hours,y:s.Q_W_m3,dashed:name.endsWith('22A')})),{yLabel:'Q por edad [W/m³]',xLabel:'Edad desde activación [h]'});
  chart($('e13-climate-chart'),info.climate.map((s,i)=>({name:'Miembro '+s.member+' · '+fmt(s.weight*100,1)+' %',color:colors[i],x:s.seconds,y:s.temperature_C})),{date:true,xLabel:'Fecha UTC · serie auténtica completa',yLabel:'Temperatura del aire [°C]'});
  if(current?.plans?.length){const p=[...current.plans].sort((a,b)=>a.D_h-b.D_h),x=p.map(q=>q.D_h);chart($('e13-frontier'),[{name:'Planes evaluados',color:colors[0],x,y:p.map(q=>100*q.P_joint)},{name:'Límite conjunto 5 %',color:'#333',x:[Math.min(...x),Math.max(...x)+.001],y:[5,5]}],{xLabel:'D: fin de colocación desde t0 [h]',yLabel:'Falla conjunta del modelo [%]'});}
 }
 table(info.official,'Resultados oficiales; familia y pesos declarados. Modificar inputs requiere recálculo.');
 $('e13-plan').addEventListener('change',choose);document.querySelectorAll('[data-e13-input]').forEach(x=>x.addEventListener('input',dirty));
 $('e13-estimate-button').addEventListener('click',async()=>{try{error();await preflight();}catch(e){error(e.message);}});
 $('e13-run').addEventListener('click',async()=>{if(!estimate)return;busy(true);$('e13-run').disabled=true;$('e13-diagnostic').disabled=true;
  try{error();const j=await post('/api/e13/run',{configuration:estimate.configuration,fingerprint:estimate.fingerprint});
   for(;;){const q=await api('/api/jobs/'+j.id);$('e13-progress').textContent=q.progress?q.progress.completed+'/'+q.progress.total+' · '+q.status+' · '+(q.progress.scenario??''):q.message;
    if(q.status==='passed'){const r=await api('/api/e13/results/'+j.id);table(r.summary,'Evaluación nueva '+j.id+'; 24 escenarios realmente calculados.');changed=false;$('e13-dirty').hidden=true;break;}
    if(['failed','cancelled'].includes(q.status))throw Error(q.message);await new Promise(r=>setTimeout(r,1000));}
  }catch(e){error(e.message);}finally{busy(false);$('e13-diagnostic').disabled=false;estimate=null;}
 });
 $('e13-diagnostic').addEventListener('click',async()=>{busy(true);$('e13-diagnostic').disabled=true;
  try{error();await preflight();const r=await post('/api/e13/diagnostic',{parameters:parameters(),scenario:$('e13-scenario').value});$('e13-progress').textContent='Un escenario en Python; D='+fmt(r.D_h,3)+' h. Esto no calcula Pf.';
   for(;;){const q=await api('/api/jobs/'+r.job.id);$('e13-progress').textContent=q.message+' · Diagnóstico individual, Pf no evaluada';if(q.status==='passed'){await loadResult(q.id);tab('vista');$('e13-dirty').hidden=false;$('e13-dirty').textContent='3D y curvas: escenario diagnóstico nuevo. La tabla de riesgo anterior requiere las 24 evaluaciones.';break;}if(['failed','cancelled'].includes(q.status))throw Error(q.message);await new Promise(r=>setTimeout(r,700));}
  }catch(e){error(e.message);}finally{busy(false);$('e13-diagnostic').disabled=false;}
 });
 $('e13-official').addEventListener('click',()=>{table(info.official,'Resultados oficiales de la familia completa');});
 $('e13-view').addEventListener('click',async()=>{try{await loadResult('official');tab('vista');}catch(e){error(e.message);}});
 window.addEventListener('resize',()=>{if(!document.querySelector('[data-panel="decision"]').hidden)draw();});
 return {draw,info};
}
