"use strict";
const $=id=>document.getElementById(id),all=q=>[...document.querySelectorAll(q)];
const colors=['#5794d6','#70c8c2','#edba55','#e18468','#a5bd74'];
const fmt=(n,d=1)=>n==null?'—':Number(n).toLocaleString('es-CL',{maximumFractionDigits:d,minimumFractionDigits:d});
const clone=x=>JSON.parse(JSON.stringify(x));
const state={cfg:null,model:null,modelId:'default',jobs:[],resultId:null,report:null,geometry:null,frame:0,cache:new Map(),visible:{},playing:false,token:0};
async function api(path,options={}){const r=await fetch(path,options);const data=await r.json();if(!r.ok)throw new Error(data.error||'No se pudo completar la solicitud');return data;}
const post=(path,data)=>api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
function error(message=''){$('error').textContent=message;$('error').hidden=!message;}
function num(id){const raw=$(id).value.trim(),value=Number(raw);if(raw===''||!Number.isFinite(value))throw new Error('Completa los valores numéricos.');return value;}
function fill(cfg){
 state.cfg=clone(cfg);const ds=Array.isArray(cfg.spacing_m)?cfg.spacing_m:[cfg.spacing_m,cfg.spacing_m,cfg.spacing_m];
 const values={dx:ds[0],dy:ds[1],dz:ds[2],resolutions:cfg.resolutions_m.join(', '),k:cfg.material.k,rho:cfg.material.rho,cp:cfg.material.cp,heat:cfg.hydration.H_vol_J_m3/1e6,'heat-duration':cfg.hydration.duration_s/3600,h:cfg.h_W_m2K,ambient:cfg.ambient_C,end:cfg.t_end_s/3600,step:cfg.max_step_s,save:cfg.save_interval_s/3600};
 for(const[id,value]of Object.entries(values))$(id).value=value;
 $('pours').innerHTML=cfg.events.map((event,i)=>`<div class="pour-row" data-id="${event.pour_id}"><span><i class="dot" style="background:${colors[i%5]}"></i>${event.pour_id}</span><input type="number" step="any" min="0" data-key="activation_s" value="${event.activation_s/3600}" aria-label="Inicio vertida ${event.pour_id}"><input type="number" step="any" data-key="initial_C" value="${event.initial_C}" aria-label="Temperatura vertida ${event.pour_id}"></div>`).join('');
 $('json').value=JSON.stringify(cfg,null,2);error();
 const gaps=cfg.events.slice(1).map((e,i)=>e.activation_s-cfg.events[i].activation_s);
 $('interval').value=gaps.length&&gaps[0]>=0&&gaps.every(v=>Math.abs(v-gaps[0])<1e-6)?gaps[0]/3600:'';
}
function config(){
 const cfg=clone(state.cfg);cfg.spacing_m=[num('dx'),num('dy'),num('dz')];
 cfg.resolutions_m=$('resolutions').value.split(/[,;\s]+/).filter(Boolean).map(Number);
 cfg.material={k:num('k'),rho:num('rho'),cp:num('cp')};cfg.hydration={H_vol_J_m3:num('heat')*1e6,duration_s:num('heat-duration')*3600};
 cfg.h_W_m2K=num('h');cfg.ambient_C=num('ambient');cfg.t_end_s=num('end')*3600;cfg.max_step_s=num('step');cfg.save_interval_s=num('save')*3600;
 cfg.events=all('.pour-row').map(row=>{const event=clone(cfg.events.find(e=>e.pour_id===Number(row.dataset.id)));for(const key of ['activation_s','initial_C']){const field=row.querySelector(`[data-key="${key}"]`);if(!field.value.trim()||!Number.isFinite(Number(field.value)))throw new Error('Completa los inputs de cada vertida.');event[key]=Number(field.value)*(key==='activation_s'?3600:1);}return event;});
 return cfg;
}
function sync(){try{$('json').value=JSON.stringify(config(),null,2);}catch(_){} }
function history(){
 const selected=$('history').value;$('history').innerHTML='<option value="">Elegir resultado</option>'+(state.reference?'<option value="reference">Referencia E08 verificada</option>':'')+state.jobs.filter(j=>j.status==='passed').map(j=>`<option value="${j.id}">${new Date(j.created_at).toLocaleString('es-CL',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})} · ${j.id.slice(0,6)}</option>`).join('');$('history').value=selected;
}
function heatColor(x){const stops=[[.145,.063,.267],[.66,.20,.46],[.97,.49,.16],[.99,1,.64]];const u=Math.max(0,Math.min(.999999,x))*3,i=Math.floor(u),a=u-i;return stops[i].map((v,k)=>v+(stops[i+1][k]-v)*a);}
class Viewer{
 constructor(canvas){
  this.canvas=canvas;this.yaw=-.75;this.pitch=.65;this.zoom=1;this.groups=[];this.temps=null;this.low=0;this.high=1;
  this.gl=canvas.getContext('webgl',{antialias:true,alpha:true});
  if(this.gl)this.initGL();else this.ctx=canvas.getContext('2d');
  let drag=null;canvas.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointerup',()=>drag=null);canvas.addEventListener('pointercancel',()=>drag=null);
  canvas.addEventListener('pointermove',e=>{if(!drag)return;this.yaw+=(e.clientX-drag[0])*.008;this.pitch=Math.max(.05,Math.min(1.5,this.pitch+(e.clientY-drag[1])*.008));drag=[e.clientX,e.clientY];this.draw();});
  canvas.addEventListener('wheel',e=>{e.preventDefault();this.zoom=Math.max(.35,Math.min(5,this.zoom*Math.exp(-e.deltaY*.001)));this.draw();},{passive:false});
  new ResizeObserver(()=>this.draw()).observe(canvas);
 }
 initGL(){const gl=this.gl;
  const shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error('No se pudo iniciar el visor 3D');return s;};
  const vertex=shader(gl.VERTEX_SHADER,'attribute vec3 pos;attribute vec3 normal;attribute float temp;uniform mat4 matrix;varying float t;varying float light;void main(){gl_Position=matrix*vec4(pos,1.0);t=temp;light=0.67+0.33*dot(normal,normalize(vec3(0.3,-0.5,0.9)));}');
  const fragment=shader(gl.FRAGMENT_SHADER,'precision mediump float;varying float t;varying float light;uniform float lo;uniform float hi;uniform float mode;uniform vec3 color;vec3 heat(float u){vec3 a=vec3(.145,.063,.267),b=vec3(.66,.20,.46),c=vec3(.97,.49,.16),d=vec3(.99,1.,.64);if(u<.3333)return mix(a,b,u*3.);if(u<.6667)return mix(b,c,(u-.3333)*3.);return mix(c,d,(u-.6667)*3.);}void main(){vec3 c=mode>.5?color:heat(clamp((t-lo)/max(hi-lo,.001),0.,1.));gl_FragColor=vec4(c*light,1.);}');
  this.program=gl.createProgram();gl.attachShader(this.program,vertex);gl.attachShader(this.program,fragment);gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw new Error('Visor 3D no disponible');
  this.loc={};for(const n of ['pos','normal','temp'])this.loc[n]=gl.getAttribLocation(this.program,n);for(const n of ['matrix','lo','hi','mode','color'])this.loc[n]=gl.getUniformLocation(this.program,n);
  gl.enable(gl.DEPTH_TEST);
 }
 setGeometry(data){
  if(this.gl)for(const g of this.groups)for(const b of [g.posBuffer,g.normalBuffer,g.tempBuffer])this.gl.deleteBuffer(b);
  this.data=data;this.temps=null;this.active=new Set();this.radius=Math.max(...data.extent_m)*.64;this.groups=[];
  for(const [index,source]of data.groups.entries()){
   const positions=[],normals=[],cells=[],quads=[];
   for(const face of source.faces){const axis=face[3],sign=face[4],other=[0,1,2].filter(i=>i!==axis),corners=[];
    for(const [a,b]of [[-1,-1],[1,-1],[1,1],[-1,1]]){const p=face.slice(0,3);p[other[0]]+=a*data.spacing_m[other[0]]/2;p[other[1]]+=b*data.spacing_m[other[1]]/2;corners.push(p);}
    const n=[0,0,0];n[axis]=sign;quads.push({corners,cell:face[5],normal:n});
    for(const j of [0,1,2,0,2,3]){positions.push(...corners[j]);normals.push(...n);cells.push(face[5]);}
   }
   const color=colors[index%5].slice(1).match(/../g).map(v=>parseInt(v,16)/255);
   const group={id:source.vertida_id,positions:new Float32Array(positions),normals:new Float32Array(normals),cells:new Uint32Array(cells),quads,color};
   if(this.gl){for(const [field,values]of [['posBuffer',group.positions],['normalBuffer',group.normals]]){group[field]=this.gl.createBuffer();this.gl.bindBuffer(this.gl.ARRAY_BUFFER,group[field]);this.gl.bufferData(this.gl.ARRAY_BUFFER,values,this.gl.STATIC_DRAW);}group.tempBuffer=this.gl.createBuffer();}
   this.groups.push(group);
  }this.draw();
 }
 setFrame(temperatures,active){this.temps=temperatures;this.active=new Set(active);if(this.gl)for(const g of this.groups){const t=new Float32Array(g.cells.length);for(let i=0;i<t.length;i++)t[i]=temperatures[g.cells[i]];this.gl.bindBuffer(this.gl.ARRAY_BUFFER,g.tempBuffer);this.gl.bufferData(this.gl.ARRAY_BUFFER,t,this.gl.DYNAMIC_DRAW);}this.draw();}
 matrix(w,h){const cy=Math.cos(this.yaw),sy=Math.sin(this.yaw),sp=Math.sin(this.pitch),cp=Math.cos(this.pitch),s=this.zoom/this.radius,aspect=w/h;return new Float32Array([cy*s/aspect,sy*sp*s,sy*cp*s/3,0,-sy*s/aspect,cy*sp*s,cy*cp*s/3,0,0,cp*s,-sp*s/3,0,0,0,0,1]);}
 draw(){
  const canvas=this.canvas,dpr=Math.min(devicePixelRatio||1,2),w=Math.max(1,Math.floor(canvas.clientWidth*dpr)),h=Math.max(1,Math.floor(canvas.clientHeight*dpr));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
  if(!this.data||!this.temps)return;const m=this.matrix(w,h),mode=$('color-mode').value==='pour';
  const visible=g=>this.active.has(g.id)&&state.visible[g.id]!==false;
  if(this.gl){const gl=this.gl;gl.viewport(0,0,w,h);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(this.program);gl.uniformMatrix4fv(this.loc.matrix,false,m);gl.uniform1f(this.loc.lo,this.low);gl.uniform1f(this.loc.hi,this.high);gl.uniform1f(this.loc.mode,mode?1:0);
   for(const g of this.groups){if(!visible(g))continue;for(const [n,b,size]of [['pos',g.posBuffer,3],['normal',g.normalBuffer,3],['temp',g.tempBuffer,1]]){gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.enableVertexAttribArray(this.loc[n]);gl.vertexAttribPointer(this.loc[n],size,gl.FLOAT,false,0,0);}gl.uniform3fv(this.loc.color,g.color);gl.drawArrays(gl.TRIANGLES,0,g.cells.length);}
  }else if(this.ctx){const ctx=this.ctx;ctx.clearRect(0,0,w,h);const faces=[];const project=p=>[(m[0]*p[0]+m[4]*p[1]+m[8]*p[2]+1)*w/2,(1-m[1]*p[0]-m[5]*p[1]-m[9]*p[2])*h/2,m[2]*p[0]+m[6]*p[1]+m[10]*p[2]];
   for(const g of this.groups){if(!visible(g))continue;for(const q of g.quads){const points=q.corners.map(project);faces.push({points,z:points.reduce((s,p)=>s+p[2],0)/4,color:mode?g.color:heatColor((this.temps[q.cell]-this.low)/(this.high-this.low))});}}
   faces.sort((a,b)=>b.z-a.z);for(const face of faces){ctx.beginPath();face.points.forEach((p,i)=>i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]));ctx.closePath();ctx.fillStyle='rgb('+face.color.map(v=>Math.round(v*255)).join(',')+')';ctx.fill();}
  }
 }
 reset(){this.yaw=-.75;this.pitch=.65;this.zoom=1;this.draw();}
}
let viewer;
function pause(){state.playing=false;clearTimeout(state.playTimer);$('play').textContent='▶';}
async function frame(index){
 if(!state.report)return;index=Math.max(0,Math.min(state.report.frames.length-1,index));const token=++state.token,key=state.resultId;
 if(!state.cache.has(index))state.cache.set(index,fetch(`/api/results/${key}/frame/${index}`).then(async r=>{if(!r.ok)throw new Error('No se pudo leer el fotograma');return new Float32Array(await r.arrayBuffer());}));
 const temperatures=await state.cache.get(index);if(token!==state.token||key!==state.resultId)return;
 while(state.cache.size>12)state.cache.delete(state.cache.keys().next().value);
 const row=state.report.frames[index];state.frame=index;$('time').value=index;$('time-label').textContent=fmt(row.time_s/3600,1)+' h';
 $('empty-scene').hidden=row.active_ids.length>0;$('empty-scene').textContent='Todavía no hay vertidas colocadas en este instante.';
 viewer.setFrame(temperatures,row.active_ids);$('frame-info').textContent=row.active_cells.toLocaleString('es-CL')+' celdas activas';
 $('temperature-table').innerHTML=row.by_pour.map((p,i)=>`<tr><td><i class="dot" style="background:${colors[i%5]}"></i>${p.vertida_id}</td><td>${p.active?fmt(p.age_s/3600,1)+' h':'Sin colocar'}</td><td>${fmt(p.mean_C,1)}${p.active?' °C':''}</td><td>${fmt(p.max_C,1)}${p.active?' °C':''}</td></tr>`).join('');
 $('frame-energy').textContent=`Hidratación: ${fmt(row.hydration_energy_J/1e9,2)} GJ · pérdidas: ${fmt(row.outward_energy_J/1e9,2)} GJ · material entrante: ${fmt(row.placement_energy_J/1e9,2)} GJ`;
}
function figure(){if(!state.resultId)return;$('figure').src=`/files/${state.resultId}/figures/${$('figure-choice').value}`;$('figure').hidden=false;}
async function loadResult(id){
 pause();state.token++;const [report,geometry]=await Promise.all([api(`/api/results/${id}/summary`),api(`/api/results/${id}/geometry`)]);
 state.resultId=id;state.report=report;state.geometry=geometry;state.cache=new Map();state.modelId=id;
 fill(report.configuration);$('result-title').textContent=id==='reference'?'Referencia E08 verificada':'Escenario '+id.slice(0,6);$('history').value=id;
 $('peak').textContent=fmt(report.temperature_range_C[1],1)+' °C';$('volume').textContent=fmt(report.nominal.volume_voxel_m3,1)+' m³';$('volume-error').textContent=fmt(100*report.nominal.relative_error,3)+' %';
 $('volume-reference').textContent='IFC: '+fmt(report.nominal.volume_reference_mesh_m3,2)+' m³';$('worst-error').textContent='Mayor error por pieza: '+fmt(100*report.nominal.max_pour_relative_error,2)+' %';
 $('balance').textContent=Object.values(report.checks).every(Boolean)?'Verificado':'Revisar';$('energy-tolerance').textContent='Residuo '+Number(report.energy.residual_J).toExponential(1)+' J';
 $('volume-table').innerHTML=report.nominal.by_pour.map((p,i)=>`<tr><td><i class="dot" style="background:${colors[i%5]}"></i>${p.vertida_id}</td><td>${fmt(p.volume_voxel_m3,2)}</td><td>${fmt(100*p.relative_error,3)} %</td></tr>`).join('');
 const labels={global_energy_balance:'Balance global',step_energy_balance:'Balance por paso',hydration_potential:'Calor integrado',stable_steps:'Paso estable',events_reached:'Activaciones exactas',inactive_is_nan:'Celdas futuras',final_time_exact:'Tiempo final'};
 $('checks').innerHTML=Object.entries(report.checks).map(([name,pass])=>`<span>${pass?'✓':'×'} ${labels[name]||name}</span>`).join('');
 $('visibility-list').innerHTML=geometry.groups.map((g,i)=>{if(!(g.vertida_id in state.visible))state.visible[g.vertida_id]=true;return `<label><input type="checkbox" data-visible="${g.vertida_id}" ${state.visible[g.vertida_id]?'checked':''}><i class="dot" style="background:${colors[i%5]}"></i>V${g.vertida_id}</label>`;}).join('');
 $('time').max=report.frames.length-1;viewer.low=report.temperature_range_C[0];viewer.high=Math.max(viewer.low+1,report.temperature_range_C[1]);viewer.setGeometry(geometry);
 $('scale-low').textContent=fmt(viewer.low,1)+' °C';$('scale-high').textContent=fmt(viewer.high,1)+' °C';$('empty-scene').hidden=true;
 $('downloads').innerHTML=`<a href="/download/${id}">Descargar escenario completo ↓</a><a href="/files/${id}/solution.npz">Historia de temperaturas ↓</a><a href="/files/${id}/inputs.json">Inputs usados ↓</a><a href="/files/${id}/model.ifc">IFC usado ↓</a>`;
 figure();await frame(report.frames.length-1);
}
async function track(job){
 state.activeJob=job.id;$('run').disabled=true;$('cancel').hidden=false;$('progress').hidden=false;pause();
 try{while(state.activeJob===job.id){const current=await api('/api/jobs/'+job.id);$('status').textContent=current.message;if(current.progress){const p=current.progress;$('progress').value=p.t_end_s?100*p.time_s/p.t_end_s:100;$('status').textContent=current.message+' · '+fmt(p.time_s/3600,1)+' h';}if(current.log)$('log').textContent=current.log;
   if(current.status==='passed'){state.jobs=state.jobs.filter(j=>j.id!==job.id);state.jobs.unshift(current);history();await loadResult(job.id);$('status').textContent='Simulación terminada. Puedes explorar el tiempo y ocultar vertidas.';break;}
   if(['failed','cancelled'].includes(current.status)){if(current.status==='failed')throw new Error(current.message);$('status').textContent=current.message;break;}
   await new Promise(r=>setTimeout(r,800));
  }}finally{state.activeJob=null;$('run').disabled=false;$('cancel').hidden=true;$('progress').hidden=true;}
}
$('form').addEventListener('submit',async event=>{event.preventDefault();error();try{await track(await post('/api/run',{configuration:config(),model_id:state.modelId}));}catch(e){error(e.message);$('status').textContent='No se pudo terminar el escenario.';}});
$('form').addEventListener('input',event=>{if(event.target.id!=='json')sync();});
$('apply-json').addEventListener('click',()=>{try{fill(JSON.parse($('json').value));}catch(e){error(e.message);}});
$('export-json').addEventListener('click',()=>{try{const url=URL.createObjectURL(new Blob([JSON.stringify(config(),null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='e08_inputs.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){error(e.message);}});
$('apply-interval').addEventListener('click',()=>{try{const hours=num('interval');if(hours<0)throw new Error('El intervalo debe ser no negativo.');all('.pour-row').forEach((row,i)=>row.querySelector('[data-key="activation_s"]').value=i*hours);sync();}catch(e){error(e.message);}});
all('[data-spacing]').forEach(b=>b.addEventListener('click',()=>{['dx','dy','dz'].forEach((id,i)=>$(id).value=b.dataset.spacing.split(',')[i]);sync();}));
$('cancel').addEventListener('click',async()=>{if(state.activeJob)try{await post('/api/cancel/'+state.activeJob,{});}catch(e){error(e.message);}});
$('history').addEventListener('change',()=>{if($('history').value)loadResult($('history').value).catch(e=>error(e.message));});
$('time').addEventListener('input',()=>{pause();frame(Number($('time').value)).catch(e=>error(e.message));});
$('visibility-list').addEventListener('change',event=>{if(event.target.dataset.visible){state.visible[Number(event.target.dataset.visible)]=event.target.checked;viewer.draw();}});
$('color-mode').addEventListener('change',()=>{document.querySelector('.legend').hidden=$('color-mode').value==='pour';viewer.draw();});$('reset-view').addEventListener('click',()=>viewer.reset());$('figure-choice').addEventListener('change',figure);
$('play').addEventListener('click',()=>{if(state.playing){pause();return;}if(!state.report)return;state.playing=true;$('play').textContent='❚❚';if(state.frame>=state.report.frames.length-1)state.frame=-1;const next=async()=>{if(!state.playing)return;try{await frame(state.frame+1);if(state.frame>=state.report.frames.length-1){pause();return;}state.playTimer=setTimeout(next,150);}catch(e){pause();error(e.message);}};next();});
$('ifc').addEventListener('change',async()=>{const file=$('ifc').files[0];if(!file)return;try{if(file.size>20*1024*1024)throw new Error('El IFC supera 20 MB');$('status').textContent='Leyendo modelo IFC…';const response=await fetch('/api/models',{method:'POST',body:file});const data=await response.json();if(!response.ok)throw new Error(data.error);state.modelId=data.id;state.model=data;const cfg=config();cfg.events=data.pours.map((p,i)=>cfg.events.find(e=>e.pour_id===p.vertida_id)||{pour_id:p.vertida_id,activation_s:i*21600,initial_C:20});fill(cfg);$('model-name').textContent=file.name+' · '+data.pours.length+' vertidas';$('status').textContent='Modelo cargado; revisa los inputs antes de ejecutar.';}catch(e){error(e.message);}});
async function boot(){viewer=new Viewer($('scene'));const data=await api('/api/bootstrap');state.model=data.model;state.jobs=data.jobs;state.reference=data.reference;fill(data.configuration);history();$('model-name').textContent=data.model.name+' · '+data.model.pours.length+' vertidas';$('connection').textContent='● Python conectado';if(data.reference)await loadResult('reference');else{const last=data.jobs.find(j=>j.status==='passed');if(last)await loadResult(last.id);}}
boot().catch(e=>{error(e.message);$('connection').textContent='No se pudo conectar';});
