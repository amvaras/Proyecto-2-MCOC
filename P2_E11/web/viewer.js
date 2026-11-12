// Adaptación gráfica de celdas XYZ reales. No contiene integración térmica.
export const palette=['#5794d6','#70c8c2','#edba55','#e18468','#a5bd74'];
export function heatColor(x,difference=false){
 const u=Math.max(0,Math.min(.999999,x));const stops=difference?[[.13,.32,.7],[.94,.95,.94],[.76,.15,.15]]:[[.145,.063,.267],[.66,.20,.46],[.97,.49,.16],[.99,1,.64]];
 const n=stops.length-1,i=Math.floor(u*n),a=u*n-i;return stops[i].map((v,k)=>v+(stops[i+1][k]-v)*a);
}
export function buildQuads(g,temperatures,active,visible,filter,showFuture=false){
 const ds=g.spacing_m,axis=filter.axis,pos=filter.position,half=ds.map(x=>x/2),quads=[],members=new Map();
 const layer=Math.min(g.shape[axis]-1,Math.max(0,Math.floor((pos-g.origin_m[axis])/ds[axis])));
 for(let c=0;c<g.labels.length;c++){
  const future=!active.has(g.labels[c]);if(visible[g.labels[c]]===false||(future&&!showFuture))continue;
  const center=g.centers_m[c];if(filter.mode==='slice'&&g.indices[c][axis]!==layer)continue;
  if(filter.mode==='clip'&&(filter.side==='negative'?center[axis]-half[axis]>=pos:center[axis]+half[axis]<=pos))continue;
  members.set(g.indices[c].join(','),{c,future});
 }
 function quad(c,normalAxis,sign,lo,hi,future){
  const other=[0,1,2].filter(i=>i!==normalAxis),corners=[];
  for(const [a,b]of [[0,0],[1,0],[1,1],[0,1]]){const p=[...lo];p[normalAxis]=sign>0?hi[normalAxis]:lo[normalAxis];p[other[0]]=a?hi[other[0]]:lo[other[0]];p[other[1]]=b?hi[other[1]]:lo[other[1]];corners.push(p);}
  const normal=[0,0,0];normal[normalAxis]=sign;quads.push({corners,normal,cell:c,pour:g.labels[c],future,temperature:temperatures[c]});
 }
 for(const {c,future}of members.values()){
  const center=g.centers_m[c],lo=center.map((v,i)=>v-half[i]),hi=center.map((v,i)=>v+half[i]);
  if(filter.mode==='slice'){lo[axis]=hi[axis]=pos;quad(c,axis,1,lo,hi,future);continue;}
  if(filter.mode==='clip'){if(filter.side==='negative')hi[axis]=Math.min(hi[axis],pos);else lo[axis]=Math.max(lo[axis],pos);}
  for(let a=0;a<3;a++)for(const sign of [-1,1]){
   const neighbor=[...g.indices[c]];neighbor[a]+=sign;
   const cap=filter.mode==='clip'&&a===axis&&(sign>0?hi[a]<center[a]+half[a]-1e-9:lo[a]>center[a]-half[a]+1e-9);
   if(cap||!members.has(neighbor.join(',')))quad(c,a,sign,lo,hi,future);
  }
 }
 return {quads,cells:members.size,activeCells:[...members.values()].filter(v=>!v.future).length};
}

export class Viewer{
 constructor(canvas,onPick,onDraw){
  this.canvas=canvas;this.onPick=onPick;this.onDraw=onDraw;this.yaw=-.75;this.pitch=.65;this.zoom=1.3;this.visible={};this.active=new Set();this.filter={mode:'full',axis:1,position:0,side:'negative'};this.low=18;this.high=42;this.difference=false;this.pourColor=false;this.showFuture=false;this.quads=[];
  this.gl=canvas.getContext('webgl',{antialias:true,alpha:true,preserveDrawingBuffer:true});if(this.gl)this.initGL();else this.ctx=canvas.getContext('2d');
  canvas.dataset.renderer=this.gl?'WebGL':'Canvas 2D';let drag=null;
  canvas.addEventListener('pointerdown',e=>{drag={start:[e.clientX,e.clientY],last:[e.clientX,e.clientY]};canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointerup',e=>{if(drag&&Math.hypot(e.clientX-drag.start[0],e.clientY-drag.start[1])<4)this.pick(e);drag=null;});canvas.addEventListener('pointercancel',()=>drag=null);
  canvas.addEventListener('pointermove',e=>{if(!drag)return;this.yaw+=(e.clientX-drag.last[0])*.008;this.pitch=Math.max(-1.55,Math.min(1.55,this.pitch+(e.clientY-drag.last[1])*.008));drag.last=[e.clientX,e.clientY];this.draw();});
  canvas.addEventListener('wheel',e=>{e.preventDefault();this.zoom=Math.max(.3,Math.min(5,this.zoom*Math.exp(-e.deltaY*.001)));this.draw();},{passive:false});new ResizeObserver(()=>this.draw()).observe(canvas);
 }
 initGL(){const gl=this.gl;const shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('Error del visor WebGL');return s;};
  const vs=shader(gl.VERTEX_SHADER,'attribute vec3 pos;attribute vec3 rgb;uniform mat4 matrix;varying vec3 c;void main(){gl_Position=matrix*vec4(pos,1.);c=rgb;}');const fs=shader(gl.FRAGMENT_SHADER,'precision mediump float;varying vec3 c;void main(){gl_FragColor=vec4(c,1.);}');
  this.program=gl.createProgram();gl.attachShader(this.program,vs);gl.attachShader(this.program,fs);gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error('Error de enlace WebGL');
  this.position=gl.getAttribLocation(this.program,'pos');this.color=gl.getAttribLocation(this.program,'rgb');this.matrixUniform=gl.getUniformLocation(this.program,'matrix');this.posBuffer=gl.createBuffer();this.rgbBuffer=gl.createBuffer();gl.enable(gl.DEPTH_TEST);
 }
 setGeometry(g){this.data=g;this.temps=null;this.pivot=g.bounds_m[0].map((v,i)=>(v+g.bounds_m[1][i])/2);this.radius=Math.max(...g.bounds_m[0].map((v,i)=>g.bounds_m[1][i]-v))*.66;this.quads=[];}
 update(){if(!this.data||!this.temps)return;const result=buildQuads(this.data,this.temps,this.active,this.visible,this.filter,this.showFuture);this.quads=result.quads;this.counts=result;
  if(this.gl){const positions=[],colors=[];for(const q of this.quads){let rgb=q.future?[.35,.43,.49]:this.pourColor?palette[(q.pour-1)%5].slice(1).match(/../g).map(v=>parseInt(v,16)/255):heatColor((q.temperature-this.low)/Math.max(this.high-this.low,1e-6),this.difference);const light=.77+.23*(q.normal[2]*.75+q.normal[0]*.25-q.normal[1]*.2);rgb=rgb.map(v=>Math.max(0,v*light));for(const i of [0,1,2,0,2,3]){positions.push(...q.corners[i]);colors.push(...rgb);}}
   const o=this.data.bounds_m[0],length=this.radius*.27;for(let a=0;a<3;a++){const end=[...o];end[a]+=length;positions.push(...o,...end);const rgb=a===0?[1,.35,.3]:a===1?[.3,.9,.5]:[.4,.65,1];colors.push(...rgb,...rgb);}
   this.vertexCount=this.quads.length*6;this.gl.bindBuffer(this.gl.ARRAY_BUFFER,this.posBuffer);this.gl.bufferData(this.gl.ARRAY_BUFFER,new Float32Array(positions),this.gl.DYNAMIC_DRAW);this.gl.bindBuffer(this.gl.ARRAY_BUFFER,this.rgbBuffer);this.gl.bufferData(this.gl.ARRAY_BUFFER,new Float32Array(colors),this.gl.DYNAMIC_DRAW);
  }this.draw();
 }
 setFrame(t,active){this.temps=t;this.active=new Set(active);this.update();}
 matrix(w,h){const cy=Math.cos(this.yaw),sy=Math.sin(this.yaw),sp=Math.sin(this.pitch),cp=Math.cos(this.pitch),s=this.zoom/this.radius,aspect=w/h;const m=new Float32Array([cy*s/aspect,sy*sp*s,sy*cp*s/3,0,-sy*s/aspect,cy*sp*s,cy*cp*s/3,0,0,cp*s,-sp*s/3,0,0,0,0,1]);for(let a=0;a<3;a++)m[12+a]=-(m[a]*this.pivot[0]+m[4+a]*this.pivot[1]+m[8+a]*this.pivot[2]);return m;}
 project(p){const w=this.canvas.clientWidth,h=this.canvas.clientHeight,m=this.matrix(w,h);return [(m[0]*p[0]+m[4]*p[1]+m[8]*p[2]+m[12]+1)*w/2,(1-m[1]*p[0]-m[5]*p[1]-m[9]*p[2]-m[13])*h/2,m[2]*p[0]+m[6]*p[1]+m[10]*p[2]+m[14]];}
 draw(){if(!this.data||!this.temps)return;const canvas=this.canvas,dpr=Math.min(devicePixelRatio||1,2),w=Math.max(1,Math.floor(canvas.clientWidth*dpr)),h=Math.max(1,Math.floor(canvas.clientHeight*dpr));canvas.width=w;canvas.height=h;const m=this.matrix(w,h);
  if(this.gl){const gl=this.gl;gl.viewport(0,0,w,h);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(this.program);gl.uniformMatrix4fv(this.matrixUniform,false,m);for(const [loc,b]of [[this.position,this.posBuffer],[this.color,this.rgbBuffer]]){gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,3,gl.FLOAT,false,0,0);}gl.drawArrays(gl.TRIANGLES,0,this.vertexCount||0);gl.drawArrays(gl.LINES,this.vertexCount||0,6);this.glError=gl.getError();
  }else if(this.ctx){const ctx=this.ctx;ctx.clearRect(0,0,w,h);const faces=this.quads.map(q=>({q,points:q.corners.map(p=>this.project(p))}));faces.sort((a,b)=>b.points[0][2]-a.points[0][2]);ctx.save();ctx.scale(dpr,dpr);for(const {q,points}of faces){ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]));ctx.closePath();const rgb=q.future?[.35,.43,.49]:heatColor((q.temperature-this.low)/(this.high-this.low),this.difference);ctx.fillStyle='rgb('+rgb.map(v=>Math.round(v*255))+')';ctx.fill();}ctx.restore();}
  this.onDraw?.(this);
 }
 pick(e){const rect=this.canvas.getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top;let selected=null,depth=Infinity;
  for(const q of this.quads){const p=q.corners.map(v=>this.project(v));let hit=false;for(let i=0,j=3;i<4;j=i++){if((p[i][1]>y)!==(p[j][1]>y)&&x<(p[j][0]-p[i][0])*(y-p[i][1])/(p[j][1]-p[i][1])+p[i][0])hit=!hit;}const z=p.reduce((s,v)=>s+v[2],0)/4;if(hit&&z<depth){selected=q;depth=z;}}
  if(selected)this.onPick?.(selected);
 }
 reset(){this.yaw=-.75;this.pitch=.65;this.zoom=1.3;this.draw();}
}
