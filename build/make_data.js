/* make_data.js - assemble app/data/data.js: live tenders, relevant history, insights linked to accounts, validation. */
const fs=require('fs'),path=require('path');
const E=require('../app/engine.js');global.window={};require('../app/data/catalogue.js');
const cat=window.JW_CATALOGUE;
const S=f=>JSON.parse(fs.readFileSync(path.join(__dirname,'seed',f)));
const O=f=>JSON.parse(fs.readFileSync(path.join(__dirname,'out',f)));
const accRx=cat.accounts.map(a=>({a,rx:new RegExp(a.rx)}));
function accOf(entity){const out=[];String(entity||'').split(/\s*[\/—]\s*|\s+and\s+/).concat([entity]).forEach(part=>{const c=E.canon(part);accRx.forEach(x=>{if(x.rx.test(c)){[x.a.id,x.a.group].forEach(k=>{if(k&&out.indexOf(k)<0)out.push(k);});}});});return out;}
const record=S('public_record.json').map(r=>({id:r.id,title:r.title,entity:r.entity,outcome:r.outcome,products:r.products,src:r.source_name,u:r.source_url||'',acc:accOf(r.entity)}));
const types=S('signal_types.json').types;
const signals=S('signals.json').map(s=>({id:s.id,date:s.date,type:s.type,entity:s.entity,title:s.title,summary:s.summary,benefit:s.benefit,lag:s.tender_lag,src:s.source_name,u:s.source_url,products:s.products,acc:accOf(s.entity)}));
const predictions=S('predictions.json').map(p=>({id:p.id,title:p.title,entity:p.entity,portal:p.portal,from:p.window_from,to:p.window_to,prob:p.probability,value:p.value_note,products:p.products,evidence:p.evidence,next:p.next_action,method:p.method,acc:accOf(p.entity+' / '+(p.publisher||''))}));
const sc=S('trend_scouting.json');
const trends=S('trends.json').map(t=>({id:t.id,country:t.country,title:t.title,when:t.when,summary:t.summary,u:t.source_url,owner:t.pk_owner,policy:t.enabling_policy,ready:t.readiness,products:t.products,pitch:t.pitch,criteria:t.criteria,acc:accOf(t.pk_owner)}));
const insights={record,signals,predictions,trends,types,criteria:sc.criteria,minCriteria:sc.min_criteria};
const ctx=E.build(cat,insights);
const meta=O('meta.json');const now=new Date(meta.today+'T12:00:00+05:00');
const open=O('tenders_open.json').map(t=>{const o={};for(const k in t){if(t[k]===''||t[k]==null||t[k]===0)continue;if(k==='b'&&t.b===t.bn)continue;if(k==='v'||k==='sbd')continue;o[k]=t[k];}return o;});
/* history: keep only tenders the same engine marks relevant; they feed demand history and renewal timing */
const RECUR=/ (licen[a-z]*|subscription[a-z]*|renewal[a-z]*|annual|sla|service level agreement|support services|maintenance contract|insurance|internet service[a-z]*|internet connectivity|bandwidth|sms service[a-z]*|rental|one year|01 year|1 year) /;
/* ── archive: what has been seen before. Lets history and the "new" flag build themselves over time ── */
const ARC=path.join(__dirname,'..','archive');if(!fs.existsSync(ARC))fs.mkdirSync(ARC);
const A=f=>{try{return JSON.parse(fs.readFileSync(path.join(ARC,f)));}catch(e){return null;}};
const W=(f,o)=>fs.writeFileSync(path.join(ARC,f),JSON.stringify(o));
const today=meta.today;
const seen=A('seen.json')||{};const firstRun=!Object.keys(seen).length;
const fresh=[];
const stamp=(meta.scan&&meta.scan.at)?meta.scan.at.slice(0,16):today;
open.forEach(t=>{if(!seen[t.id]){seen[t.id]=stamp;if(!firstRun)fresh.push(t.id);}t.fs=seen[t.id];});
{const keep={};const cutoff=new Date(Date.parse(today)-120*864e5).toISOString().slice(0,10);const oid=new Set(open.map(t=>t.id));Object.keys(seen).forEach(k=>{if(seen[k]>=cutoff||oid.has(k))keep[k]=seen[k];});W('seen.json',keep);}
/* relevant tenders are kept after they close; they join the history that drives buyer demand and renewals */
const arch=A('relevant.json')||{};
open.forEach(t=>{if(E.assess(t,ctx,now).rel){const o={};['id','s','ref','t','b','bn','cat','mth','nt','pub','cl','u','kind','st'].forEach(k=>{if(t[k])o[k]=t[k];});if(t.d)o.d=String(t.d).slice(0,300);arch[t.id]=o;}});
W('relevant.json',arch);
const histSrc=O('tenders_hist.json');{const have=new Set(histSrc.map(h=>h.id)),oid=new Set(open.map(t=>t.id));Object.values(arch).forEach(h=>{if(!oid.has(h.id)&&!have.has(h.id)&&h.cl&&h.cl.slice(0,10)<today)histSrc.push(h);});}
const hist=[];const renew=[];let histSeen=0;
const openKeys=new Set(open.map(t=>E.canon(t.t).slice(0,60)+'|'+(t.bn||t.b||'').slice(0,20)));
histSrc.forEach(t=>{histSeen++;const r=E.assess(t,ctx,now);if(!r.rel)return;
  const row={id:t.id,s:t.s,t:t.t,bn:t.bn||t.b,pub:t.pub||'',cl:(t.cl||'').slice(0,10),u:t.u,p:r.asked.map(p=>p.id),a:r.account.id,play:r.play};hist.push(row);
  if(r.play!=='monitor'&&row.cl&&RECUR.test(E.canon(t.t))&&r.asked.some(p=>p.str===3)){
    const d=new Date(row.cl+'T00:00:00Z');const add=m=>{const x=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+m,1));return x.toISOString().slice(0,7);};
    const to=add(13);if(to>=meta.today.slice(0,7)) renew.push({id:'RN-'+t.id,title:t.t,entity:row.bn,a:row.a,from:add(11)<meta.today.slice(0,7)?meta.today.slice(0,7):add(11),to,products:row.p,basis:{ref:t.ref||t.id,cl:row.cl,u:t.u},reissued:openKeys.has(E.canon(t.t).slice(0,60)+'|'+String(row.bn).slice(0,20))});
  }});
{const seen=new Set();const keep=[];renew.sort((a,b)=>b.basis.cl.localeCompare(a.basis.cl));renew.forEach(r=>{const k=E.canon(r.title).replace(/ (corrigendum|addendum|extension|procurement|of|notice|re|tender) /g,' ').replace(/ \d+ /g,' ').replace(/\s+/g,' ').slice(0,48)+'|'+r.a+'|'+String(r.entity).slice(0,18);if(seen.has(k))return;seen.add(k);r.title=r.title.replace(/^(corrigendum|addendum)[\s\-:0-9]*/i,'').replace(/^procurement of procurement of/i,'Procurement of');keep.push(r);});renew.length=0;keep.forEach(r=>renew.push(r));}
renew.sort((a,b)=>a.from.localeCompare(b.from));
let validation={};try{validation=O('validation.json');}catch(e){}

/* ── news: global government-digital trends and Pakistani signals, linked to themes, products and buyers ── */
const TH=S('themes.json');const thx=TH.themes.map(t=>Object.assign({},t,{re:new RegExp(t.rx)}));const tyx=TH.local_types.map(t=>({type:t.type,re:new RegExp(t.rx)}));
const CMAP=[['Gulf','gulf|gcc'],['India','india|indian|uttar pradesh|haryana|nashik|kerala|delhi|mumbai|bengaluru|karnataka|tamil nadu|gujarat|maharashtra|upi'],['UAE','uae|united arab emirates|dubai|abu dhabi'],['Saudi Arabia','saudi|riyadh'],['Singapore','singapore|govtech singapore'],['Estonia','estonia|tallinn'],['Indonesia','indonesia'],['Malaysia','malaysia|selangor'],['South Korea','korea|seoul'],['Hong Kong','hong kong'],['Kenya','kenya'],['Rwanda','rwanda'],['Nigeria','nigeria|anambra|lagos'],['Türkiye','turkey|t[uü]rkiye'],['Bangladesh','bangladesh'],['Egypt','egypt'],['UK','uk|united kingdom|britain|british'],['USA','usa|united states|u s'],['Germany','germany|german'],['Italy','italy|italian'],['Netherlands','netherlands|dutch'],['Romania','romania'],['Kosovo','kosovo'],['Samoa','samoa'],['Malawi','malawi'],['Guinea','guinea'],['Senegal','senegal'],['Sudan','sudan'],['Zimbabwe','zimbabwe'],['South Africa','south africa'],['Philippines','philippines|ph'],['Mexico','mexico|hidalgo'],['Seychelles','seychelles'],['Switzerland','swiss|switzerland'],['Brazil','brazil'],['Benin','benin'],['Qatar','qatar'],['Oman','oman'],['Europe','europe|european|eu']].map(c=>[c[0],new RegExp(' ('+c[1]+') ')]);
const countryOf=t=>{const c=E.canon(t);const m=CMAP.find(x=>x[1].test(c));return m?m[0]:'';};
const PKRX=/ (pakistan|pakistani|raast|sbp|pta|nadra|fbr|pral|nitb|moitt|usf|punjab|sindh|khyber|balochistan|islamabad|karachi|lahore|peshawar|quetta|gwadar|psca|kpitb|pitb|jazzcash|easypaisa|ufone|telenor pakistan) /;
const PKSRC=/pakistan|propakistani|techjuice|dawn|tribune|business recorder|brecorder|phoneworld|digital pakistan|geo news|ary|samaa|the news|bol news|mettis|urdupoint|minute mirror|daily times|nation|aaj|pkrevenue|investify/i;
const JUNK=/ (market size|market share|market to reach|cagr|forecast to|market report|market research|growth opportunit[a-z]*|industry analysis|price in pakistan|specs) /;
function themesOf(text){const c=E.canon(text);return thx.filter(t=>t.re.test(c)).map(t=>t.id);}
function prodsOf(ids,extra){const out=[];ids.forEach(id=>{const t=thx.find(x=>x.id===id);t.products.forEach(p=>{if(out.indexOf(p)<0)out.push(p);});});(extra||[]).forEach(p=>{if(out.indexOf(p)<0)out.unshift(p);});return out.slice(0,6);}
const NARC=A('news.json')||{global:{},local:{}};
let raw=null;try{raw=JSON.parse(fs.readFileSync(path.join(__dirname,'..','raw','news.json')));}catch(e){}
const keyOf=t=>E.canon(t).replace(/ /g,'').slice(0,80);
if(raw){
  raw.global.forEach(a=>{const th=themesOf(a.t);if(!th.length)return;const pk=PKRX.test(E.canon(a.t))||PKSRC.test(a.src||'');if(JUNK.test(E.canon(a.t)))return;const k=keyOf(a.t);const box=pk?NARC.local:NARC.global;if(box[k])return;
    const cc=countryOf(a.t);const c0=E.canon(a.t);box[k]={id:'N'+k.slice(0,10)+(a.date||'').replace(/-/g,''),t:a.t,src:a.src,date:a.date,u:a.u,themes:th,products:prodsOf(th),country:pk?'Pakistan':cc,acc:pk?accOf(a.t):[],type:pk?(tyx.find(x=>x.re.test(c0))||{type:'Project update'}).type:undefined,auto:1};});
  raw.local.forEach(a=>{const th=themesOf(a.t);const ac=accOf(a.t);const m=E.match({t:a.t},ctx);const asked=m.products.filter(p=>p.str>=2).map(p=>p.id);
    if(!th.length&&!asked.length)return;if(!ac.length&&!asked.length)return;const k=keyOf(a.t);if(NARC.local[k])return;
    const c=E.canon(a.t);const ty=(tyx.find(x=>x.re.test(c))||{type:'Project update'}).type;
    NARC.local[k]={id:'L'+k.slice(0,10)+(a.date||'').replace(/-/g,''),t:a.t,src:a.src,date:a.date,u:a.u,themes:th,products:prodsOf(th,asked),acc:ac,type:ty,auto:1};});
}
{const cut=new Date(Date.parse(today)-120*864e5).toISOString().slice(0,10);['global','local'].forEach(b=>Object.keys(NARC[b]).forEach(k=>{if((NARC[b][k].date||'')<cut)delete NARC[b][k];}));W('news.json',NARC);}
const byDate=(a,b)=>(b.date||'').localeCompare(a.date||'');
insights.news={global:Object.values(NARC.global).sort(byDate).slice(0,160),local:Object.values(NARC.local).sort(byDate).slice(0,160),pulled:raw?raw.now:''};
insights.policies=S('policies.json');
/* AI reader output written by scraper/ai_reader.py on the scheduled scan (empty until an API key is set) */
const AIL=A('ai_labels.json')||{meta:{},labels:{}};const AIS=A('ai_signals.json')||{meta:{},labels:{}};
insights.news.local.concat(insights.news.global).forEach(x=>{x.k=keyOf(x.t);const l=AIS.labels[x.k];if(l)x.ai=l;});
const openIds2=new Set(open.map(t=>t.id));const aiOpen={};Object.keys(AIL.labels).forEach(k=>{if(openIds2.has(k))aiOpen[k]=AIL.labels[k];});
insights.themes=TH.themes.map(t=>({id:t.id,label:t.label,products:t.products,owners:t.owners,rx:t.rx}));
/* products per curated trend and signal get theme ids too, so the Trends view can place them */
insights.trends.forEach(t=>{t.themes=themesOf(t.title+' '+t.summary+' '+t.pitch);});
insights.signals.forEach(s=>{s.themes=themesOf(s.title+' '+s.summary);});
insights.predictions.forEach(p=>{p.themes=themesOf(p.title);});
let valset=[];try{valset=O('validation_set.json').map(v=>({id:v.id,t:v.t,b:v.bn||v.b}));}catch(e){}
const data={prompts:S('prompts.json'),ai:{meta:AIL.meta,labels:aiOpen},aisig:AIS,valset,meta:Object.assign({},meta,{hist_seen:histSeen,hist_relevant:hist.length,built:new Date().toISOString(),fresh:fresh.length}),open,hist,renew,insights,validation};
{const fr=new Set(fresh);const nt=open.map(t=>({t,r:E.assess(t,ctx,now)})).filter(x=>fr.has(x.t.id)&&x.r.rel).sort((a,b)=>b.r.score-a.r.score).map(x=>({id:x.t.id,title:x.t.t,buyer:x.r.account.name,score:x.r.score,band:x.r.band.label,play:x.r.play,sbus:x.r.sbus.map(s=>cat.sbus[s].short),products:x.r.asked.map(p=>cat.products.find(q=>q.id===p.id).name),closes:(x.t.cl||'').slice(0,10),days:x.r.days,u:x.t.u}));fs.writeFileSync(path.join(__dirname,'out','new_today.json'),JSON.stringify(nt,null,1));console.log('new relevant this run',nt.length);}
fs.writeFileSync(path.join(__dirname,'..','app','data','data.js'),'window.JW_DATA = '+JSON.stringify(data)+';\n');
/* stats */
let rel=0,multi=0;const play={},band={},sbu={};const res=open.map(t=>E.assess(t,ctx,now));
res.forEach(r=>{if(!r.rel)return;rel++;play[r.play]=(play[r.play]||0)+1;band[r.band.key]=(band[r.band.key]||0)+1;r.sbus.forEach(s=>sbu[s]=(sbu[s]||0)+1);if(r.sbus.length>1)multi++;});
console.log('open',open.length,'relevant',rel,play,band,sbu,'multi',multi,'| hist relevant',hist.length,'of',histSeen,'| renewals',renew.length,'| data.js',Math.round(fs.statSync(path.join(__dirname,'..','app','data','data.js')).size/1024),'KB');
console.log('acc links: signals',signals.filter(s=>s.acc.length).length+'/'+signals.length,'preds',predictions.filter(s=>s.acc.length).length+'/'+predictions.length,'record',record.filter(s=>s.acc.length).length+'/'+record.length,'trends',trends.filter(s=>s.acc.length).length+'/'+trends.length);
const tiers={};res.forEach(r=>{if(r.rel)tiers[r.account.tier]=(tiers[r.account.tier]||0)+1});console.log('tiers',tiers,'signal-backed',res.filter(r=>r.rel&&(r.preds.length||r.sigs.length)).length);
res.map((r,i)=>({r,t:open[i]})).filter(x=>x.r.rel).sort((a,b)=>b.r.score-a.r.score).slice(0,14).forEach(x=>console.log(x.r.score,x.r.band.key,x.r.play,x.r.sbus.join('+'),x.r.account.tier,'|',x.t.t.slice(0,70),'|',x.r.account.name.slice(0,26)));
console.log(renew.slice(0,5).map(r=>r.from+'..'+r.to+' '+r.title.slice(0,60)+' | '+r.entity.slice(0,25)).join('\n'));
