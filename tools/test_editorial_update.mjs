import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
const original=JSON.parse(execFileSync('git',['show','e3b03a3:_data/aventura.json'],{maxBuffer:20e6}))[0];
const target=JSON.parse(await fs.readFile('_data/aventura.json','utf8'))[0];
const reference=JSON.parse(await fs.readFile('assets/editorial/referencia-textos.json','utf8'));
const get=(o,path)=>path.split('.').reduce((a,k)=>a?.[k],o);
const set=(o,path,v)=>{const keys=path.split('.');const last=keys.pop();for(const k of keys)o=o[k]??={};o[last]=structuredClone(v);};
globalThis.Hooks={once(){}};
globalThis.foundry={utils:{getProperty:get}};
globalThis.ui={notifications:{info(){},warn(){}}};
let writes=0,fetches=0,failAt=0;
class Document {
 constructor(source){Object.assign(this,structuredClone(source));this.id=this._id;}
 getFlag(mod,key){return this.flags?.[mod]?.[key];}
 async update(patch){if(failAt && ++writes===failAt)throw Error('fallo simulado');if(!failAt)writes++;for(const [k,v] of Object.entries(patch))if(k!=='_id')set(this,k,v);}
 async updateEmbeddedDocuments(type,patches){assert.equal(type,'JournalEntryPage');for(const patch of patches)await this.pages.get(patch._id).update(patch);}
}
function world(source){
 writes=0;fetches=0;failAt=0;
 const state=new Map();const journal=new Map(source.journal.map(j=>{const doc=new Document(j);doc.pages=new Map(j.pages.map(p=>[p._id,new Document(p)]));return[j._id,doc];}));
 globalThis.game={user:{id:'gm',isGM:true},users:{activeGM:{id:'gm'}},journal,actors:new Map(source.actors.map(a=>[a._id,new Document(a)])),settings:{get:(_m,k)=>state.get(k)??'',set:async(_m,k,v)=>state.set(k,v)},modules:new Map([['mr-nadir',{api:{}}]]),packs:new Map([['mr-nadir.aventura',{getDocuments:async()=>[target]}]])};
 globalThis.fetch=async()=>{fetches++;return{ok:true,json:async()=>reference};};
 return state;
}
const {actualizarTextos,firmaTexto}=await import('../js/editorial.js');
const oldPage=original.journal[0].pages[0];
assert(reference.paginas[oldPage._id]['text.content'].includes(firmaTexto(oldPage.text.content)));
// Una partida en curso con notas, heridas e inventario propios.
let state=world(original);
const customPage=game.journal.get(original.journal[0]._id).pages.get(oldPage._id);
customPage.text.content+='<p>NOTAS DE LA MESA</p>';
const actor=game.actors.get(original.actors[0]._id);actor.system.health.value=3;actor.items.push({_id:'objetoPropio',name:'Inventario propio'});actor.system.biography+='<p>NOTAS DEL PERSONAJE</p>';
const ownBio=actor.system.biography;const ownItems=structuredClone(actor.items);
const clocks={hora:1530,r3:2,bomba:false};const beforeClocks=structuredClone(clocks);
const result=await actualizarTextos();
assert(result.paginas>90);assert(result.camposPropios>=2);
assert(customPage.text.content.endsWith('<p>NOTAS DE LA MESA</p>'));
assert.equal(actor.system.biography,ownBio);assert.equal(actor.system.health.value,3);assert.deepEqual(actor.items,ownItems);assert.deepEqual(clocks,beforeClocks);
assert.equal(state.get('revisionEditorial'),'2.4.0');
const changed=[...game.journal.values()].flatMap(j=>[...j.pages.values()]).find(p=>p.getFlag('mr-nadir','textoAnterior240'));
assert(changed);assert.equal(typeof changed.getFlag('mr-nadir','textoAnterior240').campos['text.content'],'string');
const backup=structuredClone(changed.flags);const count=writes;
await actualizarTextos();assert.equal(writes,count);assert.equal(fetches,1);
await actualizarTextos({revisar:true});assert.deepEqual(changed.flags,backup);assert(customPage.text.content.includes('NOTAS DE LA MESA'));
// Una importación nueva ya contiene el texto actual y no genera copias innecesarias.
state=world(target);await actualizarTextos();assert.equal(writes,0);assert.equal(state.get('revisionEditorial'),'2.4.0');
// Solo el Guardián activo puede escribir.
world(original);game.user.isGM=false;await actualizarTextos();assert.equal(fetches,0);assert.equal(writes,0);
world(original);game.users.activeGM.id='otro';await actualizarTextos();assert.equal(fetches,0);
// Un fallo no marca la revisión completa; se puede reanudar sin perder la copia anterior.
state=world(original);failAt=4;await assert.rejects(actualizarTextos(),/fallo simulado/);assert.equal(state.has('revisionEditorial'),false);
failAt=0;await actualizarTextos();assert.equal(state.get('revisionEditorial'),'2.4.0');
for(const j of target.journal)for(const p of j.pages)assert.equal(game.journal.get(j._id).pages.get(p._id).text.content,p.text.content);
console.log('OK: textos, notas propias, estadísticas, inventario, copia, reintento, idempotencia y permiso del Guardián.');
