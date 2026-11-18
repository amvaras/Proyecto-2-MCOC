// Comparar contenido del formulario sin depender del orden de claves JSON.
export function canonicalConfiguration(configuration){
 const c=JSON.parse(JSON.stringify(configuration));
 c.ifc='geometry/foundation.ifc';
 c.simulation_start_utc=new Date(c.simulation_start_utc).toISOString();
 if(c.experimental_source)delete c.physics.hydration;
 function ordered(value){
  if(Array.isArray(value))return value.map(ordered);
  if(value!==null&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,ordered(value[k])]));
  return value;
 }
 return JSON.stringify(ordered(c));
}
