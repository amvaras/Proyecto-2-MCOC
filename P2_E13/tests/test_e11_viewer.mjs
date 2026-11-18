import assert from 'node:assert/strict';
import {buildQuads} from '../web/viewer.js';
// Caso asimétrico de 2×3×4, pasos no cúbicos y origen desplazado.
const g={origin_m:[10,-2,4],spacing_m:[.7,1.2,.3],shape:[2,3,4],centers_m:[],indices:[],labels:[]};
for(let i=0;i<2;i++)for(let j=0;j<3;j++)for(let k=0;k<4;k++){g.indices.push([i,j,k]);g.centers_m.push([10+(i+.5)*.7,-2+(j+.5)*1.2,4+(k+.5)*.3]);g.labels.push(k<2?1:2);}
const temperatures=Float32Array.from(g.indices.map(([i,j,k])=>20+i+10*j+100*k)),before=Buffer.from(temperatures.buffer).toString('hex'),visible={1:true,2:true},active=new Set([1,2]);
const full=buildQuads(g,temperatures,active,visible,{mode:'full',axis:2,position:4.4,side:'negative'});
assert.equal(full.cells,24);assert.equal(full.quads.length,52); // 2(nx ny + nx nz + ny nz)
for(let axis=0;axis<3;axis++){
 const position=g.origin_m[axis]+g.spacing_m[axis]*.75;
 const sliced=buildQuads(g,temperatures,active,visible,{mode:'slice',axis,position,side:'negative'});
 assert.equal(sliced.cells,24/g.shape[axis]);assert.equal(sliced.quads.length,sliced.cells);
 for(const q of sliced.quads){assert(q.corners.every(p=>Math.abs(p[axis]-position)<1e-12));assert.equal(q.temperature,temperatures[q.cell]);}
 const clipped=buildQuads(g,temperatures,active,visible,{mode:'clip',axis,position,side:'negative'});
 assert(clipped.cells<full.cells);assert(clipped.quads.every(q=>q.corners.every(p=>p[axis]<=position+1e-12)));
 const positive=buildQuads(g,temperatures,active,visible,{mode:'clip',axis,position,side:'positive'});
 assert(positive.quads.every(q=>q.corners.every(p=>p[axis]>=position-1e-12)));
}
const hidden=buildQuads(g,temperatures,active,{1:true,2:false},{mode:'full',axis:2,position:4.4});assert.equal(hidden.cells,12);
const early=buildQuads(g,temperatures,new Set([1]),visible,{mode:'full',axis:2,position:4.4});assert.equal(early.cells,12);assert(early.quads.every(q=>q.pour===1));
const future=buildQuads(g,temperatures,new Set([1]),visible,{mode:'full',axis:2,position:4.4},true);assert.equal(future.cells,24);assert.equal(future.activeCells,12);assert(future.quads.some(q=>q.future));
assert.equal(Buffer.from(temperatures.buffer).toString('hex'),before);
console.log(JSON.stringify({status:'PASS',full_cells:24,surface_quads:52,slice_axes:3,clip_sides:2,future_mask:true,visibility:true,physical_arrays_unchanged:true}));
