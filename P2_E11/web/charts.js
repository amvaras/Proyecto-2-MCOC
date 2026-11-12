// SVG local e inspección de muestras; no modifica datos del solver.
export function chart(host,series,{xLabel='Tiempo relativo [h]',yLabel='Temperatura [°C]',date=false,reference=null}={}){
 host.replaceChildren();const width=Math.max(400,host.clientWidth||900),height=host.clientHeight||300,margin={l:62,r:20,t:35,b:52},W=width-margin.l-margin.r,H=height-margin.t-margin.b;
 const points=series.flatMap(s=>s.x.map((x,i)=>[x,s.y[i]]).filter(p=>p[1]!=null&&Number.isFinite(p[1])));if(!points.length){host.textContent='Sin muestras activas en este intervalo.';return;}
 let xmin=Math.min(...points.map(p=>p[0])),xmax=Math.max(...points.map(p=>p[0])),ymin=Math.min(...points.map(p=>p[1])),ymax=Math.max(...points.map(p=>p[1]));if(xmax===xmin)xmax=xmin+1;if(ymax===ymin){ymin-=1;ymax+=1;}const pad=(ymax-ymin)*.1;ymin-=pad;ymax+=pad;
 const x=v=>margin.l+(v-xmin)/(xmax-xmin)*W,y=v=>margin.t+(ymax-v)/(ymax-ymin)*H;
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${width} ${height}`);host.append(svg);
 function el(name,attrs,text){const e=document.createElementNS(ns,name);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text!=null)e.textContent=text;svg.append(e);return e;}
 const font={'font-family':'Segoe UI,Arial','font-size':10,fill:'#708595'};
 for(let i=0;i<=5;i++){const v=ymin+(ymax-ymin)*i/5,py=y(v);el('line',{x1:margin.l,y1:py,x2:width-margin.r,y2:py,stroke:'#e4ebef'});el('text',{x:margin.l-8,y:py+3,'text-anchor':'end',...font},v.toFixed(1));const xx=xmin+(xmax-xmin)*i/5;el('text',{x:x(xx),y:height-30,'text-anchor':'middle',...font},date?new Date(xx*1000).toISOString().slice(5,16).replace('T',' '):xx.toFixed(1));}
 el('text',{x:width/2,y:height-6,'text-anchor':'middle',...font},xLabel);el('text',{x:margin.l,y:13,...font},yLabel);
 for(const [i,s]of series.entries()){let d='',open=false;for(let j=0;j<s.x.length;j++){if(s.y[j]==null||!Number.isFinite(s.y[j])){open=false;continue;}d+=(open?'L':'M')+x(s.x[j])+','+y(s.y[j]);open=true;}el('path',{d,fill:'none',stroke:s.color,'stroke-width':2,'stroke-dasharray':s.dashed?'6 4':'none'});el('text',{x:margin.l+180*(i%4),y:26+Math.floor(i/4)*12,...font,fill:s.color},s.name);}
 if(reference!=null&&reference>=ymin&&reference<=ymax){el('line',{x1:margin.l,x2:width-margin.r,y1:y(reference),y2:y(reference),stroke:'#ba5b47','stroke-dasharray':'4 3'});}
 const cursor=el('line',{x1:0,x2:0,y1:margin.t,y2:height-margin.b,stroke:'#9badb7',visibility:'hidden'}),tooltip=document.createElement('div');tooltip.className='tooltip';tooltip.hidden=true;host.append(tooltip);
 svg.addEventListener('pointermove',e=>{const box=svg.getBoundingClientRect(),px=(e.clientX-box.left)*width/box.width,t=xmin+(px-margin.l)/W*(xmax-xmin);if(t<xmin||t>xmax)return;cursor.setAttribute('x1',px);cursor.setAttribute('x2',px);cursor.setAttribute('visibility','visible');tooltip.hidden=false;tooltip.textContent=series.map(s=>{let j=0;for(let i=1;i<s.x.length;i++)if(Math.abs(s.x[i]-t)<Math.abs(s.x[j]-t))j=i;const when=date?new Date(s.x[j]*1000).toISOString():s.x[j].toFixed(2)+' h';return `${s.name}: ${s.y[j]==null?'inactiva':Number(s.y[j]).toFixed(3)} · ${when}`;}).join('\n');});
 svg.addEventListener('pointerleave',()=>{tooltip.hidden=true;cursor.setAttribute('visibility','hidden');});
}
