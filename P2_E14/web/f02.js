import {Viewer} from './viewer.js';
import {chart} from './charts.js';

const $ = id => document.getElementById(id);
const fmt = (x, decimals=3) => Number(x).toLocaleString('es-CL', {maximumFractionDigits:decimals});
const pct = x => fmt(x*100,3)+' %';
const percentLimit = .05;

function cells(row, values, tag) {
 for (const value of values) {
  const cell=document.createElement(tag);
  cell.textContent=value;
  row.append(cell);
 }
}

export async function initF02({api,error,tab,loadResult}) {
 const result=await api('/api/f02');
 const {plans,configuration:cfg,water,statistics:stats,geometry}=result;
 const id=cfg.id;
 const comparison=$('f02-plan');
 comparison.replaceChildren(...plans.map(p=>new Option(p.plan,p.plan)));
 comparison.value=id;
 $('f02-case').textContent=id+' / '+result.representative;
 const slider=$('f02-time');
 slider.max=result.times_h.length-1;
 const overlay=$('f02-overlay');
 let frameIndex=0, generation=0;
 const viewer=new Viewer($('f02-scene'), q=>{
  $('f02-pick').textContent='Vertida '+q.pour+' · '+fmt(q.temperature)+' °C · ['+
      geometry.centers_m[q.cell].map(v=>fmt(v)).join(', ')+'] m';
 }, v=>{
  $('f02-render').textContent=fmt(result.times_h[frameIndex])+' h · '+v.counts.activeCells+
    ' celdas activas · V'+[...v.active].join(', V')+' · '+v.quads.length+' caras · '+v.filter.mode+' · '+(v.gl?'WebGL '+v.glError:'Canvas 2D')+
    ' · escala '+result.range_C.map(t=>fmt(t)).join('–')+' °C';
  overlay.replaceChildren();
  const {axis,mode,position}=v.filter;
  const currentSeconds=result.times_h[frameIndex]*3600;
  for (const [time,point,color] of [
   [result.peak.time_s,result.peak.coordinate_m,'#f34134'],
   [result.delta_peak.time_s,result.delta_peak.hot.coordinate_m,'#f34134'],
   [result.delta_peak.time_s,result.delta_peak.cold.coordinate_m,'#25b6ff']
  ]) {
   if(Math.abs(time-currentSeconds)>1e-7)continue;
   if(mode==='slice' && Math.abs(point[axis]-position)>geometry.spacing_m[axis]/2)continue;
   if(mode==='clip' && point[axis]>position)continue;
   const [cx,cy]=v.project(point);
   const marker=document.createElementNS('http://www.w3.org/2000/svg','circle');
   for(const [key,value] of Object.entries({cx,cy,r:6,fill:color,stroke:'#102831','stroke-width':2}))marker.setAttribute(key,value);
   overlay.append(marker);
  }
  if (!$('f02-pipes').checked) return;
  for (const tube of water.circuits) {
   if (!v.active.has(tube.pour)) continue;
   const a=[tube.x_low_m,tube.y_m,tube.z_m],b=[tube.x_high_m,tube.y_m,tube.z_m];
   if (mode==='slice' && axis!==0 && Math.abs(a[axis]-position)>geometry.spacing_m[axis]/2) continue;
   if (mode==='slice' && axis===0) {
    if (position<a[0] || position>b[0]) continue;
    a[0]=position; b[0]=position;
   }
   if (mode==='clip') {
    if (a[axis]>position) continue;
    if (axis===0) b[0]=Math.min(b[0],position);
   }
   const [x1,y1]=v.project(a),[x2,y2]=v.project(b);
   const line=document.createElementNS('http://www.w3.org/2000/svg','line');
   for (const [key,value] of Object.entries({x1,y1,x2,y2,stroke:'#00eced','stroke-width':3,'stroke-linecap':'round'}))
    line.setAttribute(key,value);
   overlay.append(line);
  }
 });
 viewer.setGeometry(geometry);
 [viewer.low,viewer.high]=result.range_C;
 async function load(index) {
  index=Math.min(Number(slider.max),Math.max(0,index));
  const serial=++generation;
  const response=await fetch('/api/f02/frame/'+index);
  if (!response.ok) throw Error('No se pudo cargar el campo F02');
  const values=new Float32Array(await response.arrayBuffer());
  if(serial!==generation)return;
  if(values.length!==geometry.labels.length) throw Error('Campo y geometría F02 no coinciden');
  frameIndex=index;
  slider.value=index;
  viewer.setFrame(values,result.active[index]);
 }
 function filter() {
  viewer.filter={mode:$('f02-filter').value,axis:Number($('f02-axis').value),
      position:Number($('f02-plane').value),side:'negative'};
  viewer.pourColor=$('f02-color').value==='pour';
  viewer.update();
 }
 function redraw() {
  const choice=plans.find(p=>p.plan===comparison.value);
  const table=$('f02-table');
  table.replaceChildren();
  const header=table.insertRow();
  cells(header,['Plan','D [h]','Tmax [°C]','ΔTmax [°C]','P(T>70)','P(ΔT>20)','Pf conjunta','Estado'],'th');
  for (const p of plans) {
   const row=table.insertRow();
   row.setAttribute('aria-selected',String(p===choice));
   cells(row,[p.plan,fmt(p.D_h),fmt(p.Tmax_C),fmt(p.delta_C),pct(p.P_T),pct(p.P_delta),pct(p.P_joint),
    p.P_joint<=percentLimit?'Cumple en los escenarios del modelo':'No cumple'],'td');
  }
  $('f02-selected').textContent=choice.plan+' · Pf '+pct(choice.P_joint)+' · '+fmt(choice.D_h)+' h de colocación'+
   (choice.plan===id?' · 24 escenarios ponderados, sin IC de muestreo':' · enumeración E14');
  $('f02-visual').hidden=choice.plan!==id;
  $('f02-e14-view').hidden=choice.plan!=='curado_frio5';
  const palette=['#44657a','#ad3b28','#147e7c'];
  chart($('f02-risk'),[...plans.map((p,i)=>({name:p.plan,color:palette[i%3],x:[p.D_h],y:[p.P_joint*100]})),
   {name:'Límite 5 %',color:'#888',x:[0,Math.max(...plans.map(p=>p.D_h))],y:[5,5],dashed:true}],
   {xLabel:'Duración de colocación [h]',yLabel:'Pf ponderada [%]'});
  const x=plans.map((_,i)=>i+1);
  chart($('f02-maxima'),[{name:'Tmax',color:'#ad3b28',x,y:plans.map(p=>p.Tmax_C)},
    {name:'ΔTmax',color:'#147e7c',x,y:plans.map(p=>p.delta_C)},
    {name:'Límite ΔT',color:'#888',x,y:x.map(()=>20),dashed:true},
    {name:'Límite Tmax',color:'#a77241',x,y:x.map(()=>70),dashed:true}],
    {xLabel:'Plan (orden de la tabla)',xUnit:'plan',yLabel:'Temperatura [°C]'});
  if(choice.plan===id){
   const hours=stats.stats_time_s.map(t=>t/3600);
   chart($('f02-curves'),[['Tmax','stats_Tmax_C','#ad3b28'],['Mínimo S25','stats_S25_C','#297c93'],
    ['Diferencial','stats_delta_C','#147e7c']].map(([name,k,color])=>({name,color,x:hours,y:stats[k]})));
   viewer.draw();
  }
 }
 const pipe=cfg.pipe;
 const notes=[['Agua de entrada',fmt(pipe.inlet)+' °C'],['Caudal unitario',fmt(pipe.flow_ls)+' L/s'],
  ['Caudal máximo',fmt(water.flow_peak_ls)+' L/s'],['Operación',pipe.start_h+'–'+pipe.stop_h+' h'],
  ['Tramos activos',water.circuits.length+' · '+fmt(water.active_length_m)+' m'],
  ['Potencia máxima en 24 casos',fmt(result.max_power_kW)+' kW'],
  ['Energía máxima extraída',fmt(result.max_energy_GJ)+' GJ'],['Supuestos',cfg.assumptions]];
 for (const [label,value] of notes) {
  const dt=document.createElement('dt'),dd=document.createElement('dd');
  dt.textContent=label;dd.textContent=value;$('f02-water').append(dt,dd);
 }
 $('f02-source').textContent='Simulaciones Python '+result.generated_at_utc+' · SHA-256 del código/configuración '+
  result.kernel_sha256+' · Base E14 '+result.e14_base+'. Duración excluye instalación y curado.'+
  (result.controls.length?' Controles independientes de malla y paso guardados.':' Controles de malla y paso pendientes.');
 $('f02-inputs').textContent=JSON.stringify({configuration:cfg,scenarios:result.scenarios,controls:result.controls},null,2);
 comparison.addEventListener('change',redraw);
 $('f02-e14-view').addEventListener('click',async()=>{
  try { await loadResult('official'); tab('vista'); }
  catch (e) { error(e.message); }
 });
 for(const key of ['f02-filter','f02-axis','f02-plane','f02-pipes','f02-color']) $(key).addEventListener('change',filter);
 const move=i=>load(i).catch(e=>error(e.message));
 slider.addEventListener('input',()=>move(Number(slider.value)));
 $('f02-previous').addEventListener('click',()=>move(frameIndex-1));
 $('f02-next').addEventListener('click',()=>move(frameIndex+1));
 window.addEventListener('resize',()=>{if(!document.querySelector('[data-panel="f02"]').hidden)redraw();});
 await load(result.times_h.findIndex(t=>t>=200));
 return {redraw};
}
