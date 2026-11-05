/* Current ARDF: rendering only. Primary source calculations live in current_frontier.py. */
'use strict';
const data=window.ARDF_CURRENT, $=id=>document.getElementById(id);
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const fmt=(x,d=4)=>finite(x)?x.toLocaleString('en-US',{maximumFractionDigits:d}):'Unknown';
const money=x=>finite(x)?'$'+x.toPrecision(5):'Unknown';
const dominates=(a,b)=>finite(a.score)&&finite(a.cost)&&a.cost>=0&&finite(b.score)&&finite(b.cost)&&b.cost>=0&&a.cost<=b.cost&&a.score>=b.score&&(a.cost<b.cost||a.score>b.score);
const frontier=rows=>rows.filter(r=>finite(r.cost)&&r.cost>=0&&finite(r.score)&&!rows.some(o=>dominates(o,r))).sort((a,b)=>a.cost-b.cost||b.score-a.score||a.id.localeCompare(b.id));
const weightInputs={};
for(const tier of ['S','A','B','C','Unrated']){const l=document.createElement('label');l.textContent=tier+' × ';const input=document.createElement('input');input.type='number';input.min=0;input.max=5;input.step=.25;input.value=1;input.setAttribute('aria-label',tier+' benchmark weight multiplier');input.addEventListener('input',render);l.append(input);$('weights').append(l);weightInputs[tier]=input;}
for(const lab of [...new Set(data.rows.map(r=>r.lab))].sort())$('lab').add(new Option(lab,lab));
function currentRows(){
 const basis=$('basis').value;
 if(basis.startsWith('priors'))return data[basis].map(r=>({...r}));
 const weighted=$('tier-toggle').checked;
 const weights=Object.fromEntries(Object.entries(data.benchmarks).map(([k,[_,w,t]])=>[k,w*(weighted?Number(weightInputs[t].value):1)]));
 if(Object.values(weights).some(w=>!finite(w)||w<0||w>500)||Object.values(weights).reduce((a,b)=>a+b,0)<=0)throw Error('Choose nonnegative weights with at least one positive benchmark.');
 return data.rows.map(r=>{
  const vals=Object.entries(weights).filter(([_,w])=>w>0), total=vals.reduce((s,[_,w])=>s+w,0);
  let score=basis==='published'?r.published_score:r.score;
  let cost=basis==='published'?r.published_cost:r.cost;
  if(weighted){score=vals.every(([k])=>finite(r.components[k]))?vals.reduce((s,[k,w])=>s+w*r.components[k],0)/total:null;
    cost=vals.every(([k])=>finite(r.component_costs[k]))?vals.reduce((s,[k,w])=>s+w*r.component_costs[k],0)/total:null;}
  return {...r,score,cost};
 });
}
function table(id,headers,rows){const root=$(id);root.replaceChildren();const head=document.createElement('thead'),tr=document.createElement('tr');headers.forEach(h=>{const th=document.createElement('th');th.textContent=h;tr.append(th)});head.append(tr);root.append(head);const body=document.createElement('tbody');rows.forEach(cells=>{const tr=document.createElement('tr');cells.forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td)});body.append(tr)});root.append(body);}
let lastRows=[];
function render(){try{
 const basis=$('basis').value,lab=$('lab').value,query=$('search').value.toLowerCase(),primary=!basis.startsWith('priors');
 $('tier-toggle').disabled=!primary||basis==='published';
 if(!primary||basis==='published')$('tier-toggle').checked=false;
 const rows=currentRows().filter(r=>(!lab||r.lab===lab));
 lastRows=rows;
 const f=frontier(rows),fs=new Set(f.map(r=>r.id)),paired=rows.filter(r=>finite(r.score)&&finite(r.cost)&&r.cost>=0);
 const shown=rows.filter(r=>(!$('frontier-only').checked||fs.has(r.id))&&(!query||(r.name+' '+r.lab).toLowerCase().includes(query))).sort((a,b)=>(a.cost??Infinity)-(b.cost??Infinity)||(b.score??-Infinity)-(a.score??-Infinity));
 $('summary').textContent=`${rows.length} configurations · ${paired.length} paired · ${f.length} frontier points · ${rows.filter(r=>finite(r.score)&&!finite(r.cost)).length} scored but unpriced · ${rows.filter(r=>!finite(r.score)).length} without complete score`;
 $('basis-note').textContent=basis==='priors_subscription'?'Priors subscription estimates, including API-price fallback where no subscription is mapped. These are not your bill or measured quota burn. Free routes remain rate-limited.':basis==='priors_api'?'Priors API estimates and scores. Compare against the independently recomputed ARDF view; this is the reference, not the source for ARDF.':basis==='published'?'Official AA published composite. AA freezes Briefcase contributions, so this can differ from recomputing the currently displayed components.':'ARDF independently recomputes all ten weighted components and nine evaluation costs from the primary AA snapshot. No Priors scores or costs enter this calculation.';
 $('weight-note').textContent=$('tier-toggle').checked?'Custom subjective tier weights active. Score and workload cost are both reweighted locally. Priors comparison below remains the pinned original index.':'Original weights active. Subjective tiers are OFF. No default downweighting.';
 $('line').textContent=f.map(r=>r.name).join(' → ');
 table('frontier-table',['Configuration','Score','Task cost','Output tokens / task','Estimated time / task'],f.map(r=>[r.name,fmt(r.score),money(r.cost),fmt(r.tokens,0),finite(r.time)?fmt(r.time/60,2)+' min':'Unknown']));
 table('all-table',['Configuration','Provider','Effort','Score','Cost / task','Evidence / dominance'],shown.map(r=>{const d=rows.filter(o=>dominates(o,r)).sort((a,b)=>b.score-a.score||a.cost-b.cost)[0];return [r.name,r.lab,r.effort,fmt(r.score),money(r.cost),!finite(r.score)?'Incomplete score; retained in catalog':!finite(r.cost)?'Unpriced; retained, not ranked':d?'Dominated by '+d.name:'Frontier'];}));
 draw(paired,f);
 $('status').textContent='Snapshot '+data.manifest.retrieved_at+' · all providers by default · search affects the table only';
 }catch(e){$('status').textContent=e.message;}}
function draw(rows,f){
 const svg=$('chart'),ns='http://www.w3.org/2000/svg';svg.replaceChildren();
 const n=(tag,a,t)=>{const x=document.createElementNS(ns,tag);Object.entries(a).forEach(([k,v])=>x.setAttribute(k,v));if(t!==undefined)x.textContent=t;svg.append(x);return x};
 if(!rows.length){n('text',{x:30,y:40,fill:'#eff5ff'},'No paired observations. Consult the evidence table.');return;}
 const positive=rows.filter(r=>r.cost>0),logs=positive.map(r=>Math.log10(r.cost));let lo=logs.length?Math.min(...logs):0,hi=logs.length?Math.max(...logs):1;if(hi===lo)hi=lo+1;
 const ymax=Math.max(...rows.map(r=>r.score),1)*1.12;
 const X=r=>r.cost===0?85:190+(Math.log10(r.cost)-lo)/(hi-lo)*820,Y=r=>430-r.score/ymax*370;
 n('line',{x1:65,x2:1040,y1:430,y2:430,stroke:'#95a7bd'});n('line',{x1:145,x2:145,y1:35,y2:430,stroke:'#95a7bd','stroke-dasharray':'4 5'});
 n('text',{x:65,y:455,fill:'#c5d3e3'},'$0 shelf');
 for(let i=0;i<=5;i++){const y=430-i*74;n('line',{x1:65,x2:1040,y1:y,y2:y,stroke:'#22364a'});n('text',{x:8,y:y+4,fill:'#9fb1c6'},fmt(ymax*i/5,1));}
 for(let i=0;i<=4;i++)n('text',{x:190+i*205,y:455,fill:'#9fb1c6','text-anchor':'middle'},money(10**(lo+(hi-lo)*i/4)));
 n('text',{x:190,y:485,fill:'#9fb1c6'},'Positive task cost (log scale); zero-cost points shown separately at left');
 n('text',{x:65,y:22,fill:'#c5d3e3'},'Capability score ↑');
 n('polyline',{points:f.map(r=>[X(r),Y(r)].join(',')).join(' '),fill:'none',stroke:'#ffd166','stroke-width':2.5});
 const labs=[...new Set(rows.map(r=>r.lab))].sort(),colors=Object.fromEntries(labs.map((l,i)=>[l,`hsl(${i*137.508%360} 65% 65%)`])),fs=new Set(f.map(r=>r.id));
 for(const r of rows){let dot=n('circle',{cx:X(r),cy:Y(r),r:fs.has(r.id)?6:3.5,fill:colors[r.lab],stroke:fs.has(r.id)?'#ffd166':'none',tabindex:0,'aria-label':`${r.name}, score ${fmt(r.score)}, cost ${money(r.cost)}`});const title=document.createElementNS(ns,'title');title.textContent=dot.getAttribute('aria-label');dot.append(title);dot.addEventListener('focus',()=>$('point').textContent=title.textContent);dot.addEventListener('mouseenter',()=>$('point').textContent=title.textContent);dot.addEventListener('click',()=>{$('search').value=r.model;render()});}
 $('legend').replaceChildren();for(const lab of labs){const s=document.createElement('span');s.textContent='● '+lab;s.style.color=colors[lab];$('legend').append(s);}
}
for(const id of ['basis','lab','tier-toggle','frontier-only'])$(id).addEventListener('change',render);
$('search').addEventListener('input',render);
$('reset').addEventListener('click',()=>{$('basis').value='primary';$('lab').value='';$('search').value='';$('frontier-only').checked=false;$('tier-toggle').checked=false;Object.values(weightInputs).forEach(x=>x.value=1);render()});
$('download').addEventListener('click',()=>{const blob=new Blob([JSON.stringify({basis:$('basis').value,tierWeightsEnabled:$('tier-toggle').checked,tierWeights:Object.fromEntries(Object.entries(weightInputs).map(([k,v])=>[k,Number(v.value)])),rows:lastRows,frontier:frontier(lastRows)},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='ardf-selected-frontier.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)});
const comparisons=data.comparisons;table('compare-table',['Configuration','ARDF','Priors','Score difference','ARDF API $','Priors API $','Mapping'],comparisons.map(c=>[c.name,fmt(c.ardf_score,6),fmt(c.priors_score),fmt(c.score_delta,6),money(c.ardf_cost),money(c.priors_cost),c.matched?'Exact normalized name + effort':'Unresolved; not silently matched']));
const matched=comparisons.filter(c=>finite(c.score_delta));$('compare-summary').textContent=`${matched.length}/${comparisons.length} rows have comparable scores. Largest absolute score difference: ${fmt(Math.max(...matched.map(c=>Math.abs(c.score_delta))),6)} points. Values displayed by Priors are rounded. Different configurations remain unmatched.`;
render();
