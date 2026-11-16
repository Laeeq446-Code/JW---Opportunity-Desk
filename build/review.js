const E=require('../app/engine.js');global.window={};require('../app/data/catalogue.js');
const cat=window.JW_CATALOGUE;const ctx=E.build(cat,null);
const open=require('./out/tenders_open.json');
const now=new Date('2026-11-12T12:00:00+05:00');
const mode=process.argv[2];
if(mode==='rel'){
  open.map(t=>({t,r:E.assess(t,ctx,now)})).filter(x=>x.r.rel).sort((a,b)=>a.r.asked[0].id.localeCompare(b.r.asked[0].id)||b.r.score-a.r.score)
  .forEach(x=>console.log(x.r.score,x.r.play[0],x.t.s[0]+x.t.s[2],'|',x.t.t.slice(0,62),'|',x.r.asked.map(p=>p.id+p.str+'['+(p.title.length?p.title:p.desc.map(d=>'~'+d)).slice(0,2).join(',')+']').join(' ')));
}
