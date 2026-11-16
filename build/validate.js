const E=require('../app/engine.js');global.window={};require('../app/data/catalogue.js');
const ctx=E.build(window.JW_CATALOGUE,null);const now=new Date('2026-11-12T12:00:00+05:00');
const V=require('./out/validation_set.json');
const res={tune:{n:0,hit:0},hold:{n:0,hit:0}};const miss=[];
V.forEach((t,i)=>{const g=i%2?'hold':'tune';const r=E.assess(t,ctx,now);res[g].n++; if(r.rel)res[g].hit++; else if(g==='tune')miss.push(t.t.slice(0,95)+' | '+t.b.slice(0,22));});
for(const g in res) res[g].pct=+(res[g].hit/res[g].n*100).toFixed(1);
console.log(JSON.stringify(res));
if(process.argv[2]==='show') miss.forEach(m=>console.log(m));
if(process.argv[2]==='save') require('fs').writeFileSync(__dirname+'/out/validation.json',JSON.stringify(res));
