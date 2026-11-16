/* make_market.js - run the engine over the 2026 tender history (Teknosys/Tender Desk export) and write
   app/data/market.js: one compact row per tender for the Market dashboard, plus detail for relevant ones. */
const fs=require('fs'),path=require('path');
const E=require('../app/engine.js');global.window={};require('../app/data/catalogue.js');
const cat=window.JW_CATALOGUE;
const S=f=>JSON.parse(fs.readFileSync(path.join(__dirname,'seed',f)));
const O=f=>JSON.parse(fs.readFileSync(path.join(__dirname,'out',f)));
const ctx=E.build(cat,{record:[],signals:[],predictions:[],trends:[],types:S('signal_types.json').types,criteria:{},minCriteria:3});
const H=O('history_rows.json');
const TH=S('themes.json').themes.map(t=>({id:t.id,re:new RegExp(t.rx)}));const now=new Date('2026-10-15T12:00:00+05:00');
const P=cat.products.map(p=>p.id),PI={};P.forEach((p,i)=>PI[p]=i);
const months=[],mi={};for(let m=1;m<=10;m++){const k='2026-'+String(m).padStart(2,'0');mi[k]=months.length;months.push(k);}
const J={Federal:0,Punjab:1,KP:2},cats=['G','W','S','C',''],secs=[],si={},orgs=[],oi={},oacc=[];
const rows=[],detail=[];let rel=0;
H.forEach(t=>{const m=mi[(t.pub||'').slice(0,7)];if(m==null)return;
  const r=E.assess(t,ctx,now);
  const sec=t.sect||'Other Public Sector';if(si[sec]==null){si[sec]=secs.length;secs.push(sec);}
  const on=t.org||t.bn||t.b||'Unknown';if(oi[on]==null){oi[on]=orgs.length;orgs.push(on);oacc.push(r.account.id||'');}
  const o=oi[on];if(!oacc[o]&&r.account.id)oacc[o]=r.account.id;
  const pr=r.rel?r.asked.map(p=>PI[p.id]):[];
  let tm=0;if(!/^ (disposal|auction|sale of|lease)/.test(E.canon(t.t))){const c=E.canon(t.t+' '+String(t.d||'').slice(0,400));TH.forEach((x,i)=>{if(x.re.test(c))tm|=(1<<i);});}
  rows.push([m,J[t.j]||0,cats.indexOf(t.cat),si[sec],o,pr.join('.'),r.rel?({lead:1,partner:2,monitor:3}[r.play]):0,tm].join(','));
  if(r.rel){rel++;detail.push([t.id,t.pub,t.t.slice(0,170),o,pr.join('.'),{lead:1,partner:2,monitor:3}[r.play],t.u,t.mth||'',si[sec],J[t.j]||0]);}
});
const out={themes:TH.map(x=>x.id),built:new Date().toISOString(),source:'Teknosys / Tender Desk export, EPADS federal and Punjab e-PADS, advertised 1 Jan to 14 Oct 2026',months,juris:['Federal','Punjab','KP'],cats,secs,orgs,oacc,products:P,rows:rows.join(';'),detail};
fs.writeFileSync(path.join(__dirname,'..','app','data','market.js'),'window.JW_MARKET='+JSON.stringify(out)+';\n');
console.log('market rows',rows.length,'relevant',rel,(rel/rows.length*100).toFixed(1)+'%','orgs',orgs.length,'size',(fs.statSync(path.join(__dirname,'..','app','data','market.js')).size/1e6).toFixed(2)+'MB');
const by={};detail.forEach(d=>d[4].split('.').filter(Boolean).forEach(i=>{by[P[i]]=(by[P[i]]||0)+1}));console.log(Object.entries(by).sort((a,b)=>b[1]-a[1]).slice(0,40).map(x=>x[0]+':'+x[1]).join(' '));
