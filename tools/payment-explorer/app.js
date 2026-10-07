'use strict';
const data=window.BLUE_DEMO;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const $=id=>document.getElementById(id);
let current=data.cases.findIndex(c=>c.id==='20'); if(current<0)current=0;
let step=data.cases[current].trace.length-1,tab='graph',selected=null,playing=null;
function activeCase(){return data.cases[current];}
function row(){return activeCase().trace[step];}
function stop(){if(playing)clearInterval(playing);playing=null;$('play').textContent='Play trace';}
function chooseCase(i){stop();current=i;step=activeCase().trace.length-1;selected=null;render();}
function chooseStep(i){step=Math.max(0,Math.min(activeCase().trace.length-1,i));render();}
function render(){
 const c=activeCase(),r=row();
 $('cases').innerHTML=data.cases.map((x,i)=>`<button class="${i===current?'active':''}" data-case="${i}"><span class="num">${x.id}</span>${esc(x.title)}</button>`).join('');
 document.querySelectorAll('[data-case]').forEach(b=>b.onclick=()=>chooseCase(Number(b.dataset.case)));
 $('case-title').textContent=c.title;$('case-path').textContent=c.sourcePath;
 $('metric-docs').textContent=r.graph?.documents?.length??'—';$('metric-edges').textContent=r.graph?.edges?.length??'—';$('metric-steps').textContent=c.trace.length-1;
 $('steps').innerHTML=c.trace.map((x,i)=>`<option value="${i}" ${i===step?'selected':''}>${esc(i===0?'Initialize the application':`${x.label} · ${x.input?.channel??'native input'}`)}</option>`).join('');
 $('status').textContent=r.status==='FAILED'?'EXPECTED REJECTION':r.status;$('status').className='status'+(r.status==='FAILED'?' failed':'');
 $('prev').disabled=step===0;$('next').disabled=step===c.trace.length-1;
 $('receipt').textContent=`Step ${step}/${c.trace.length-1} · ${Number(r.gas).toLocaleString()} gas · receipt ${String(r.receipt).slice(0,19)}…`;
 document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
 if(tab==='graph')renderGraph();else if(tab==='source')renderSource();else if(tab==='events')renderEvents();else if(tab==='state')renderState();else renderCatalogue();
}
function graphInfo(){
 const g=row().graph??{documents:[],edges:[],root:'root'};
 const docs=g.documents??[],edges=g.edges??[],paths=new Map([[g.root??'root','']]),depth=new Map([[g.root??'root',0]]);
 let again=true;while(again){again=false;for(const e of edges){if(paths.has(e.source)&&!paths.has(e.target)){paths.set(e.target,paths.get(e.source)+e.path);depth.set(e.target,depth.get(e.source)+1);again=true;}}}
 docs.forEach(d=>{if(!paths.has(d.key)){paths.set(d.key,'/unmapped');depth.set(d.key,0);}});
 return {g,docs,edges,paths,depth};
}
function labelFor(path){
 if(!path)return activeCase().id==='20'?'Referral Agreement':activeCase().documentName.slice(0,26);
 if(path.endsWith('/payout'))return 'Commission payout';
 if(path.endsWith('/delivery'))return 'Delivery evidence';
 if(path.endsWith('/property'))return 'Property evidence';
 if(path.endsWith('/payment'))return 'Payment Instruction';
 if(/\/procurements\/[^/]+$/.test(path))return 'Procurement Agreement';
 if(/\/orders\/[^/]+$/.test(path))return `Order · ${path.split('/').pop()}`;
 if(/\/periods\/[^/]+$/.test(path))return `Period · ${path.split('/').pop()}`;
 return path.split('/').pop();
}
function renderGraph(){
 const {g,docs,edges,paths,depth}=graphInfo();
 if(!docs.length){$('panel').innerHTML='<div class="empty">Graph metadata is unavailable for this recorded row.</div>';return;}
 if(!selected||!docs.some(d=>d.key===selected))selected=g.root??docs[0].key;
 const levels=new Map();docs.forEach(d=>{let n=depth.get(d.key)??0;if(!levels.has(n))levels.set(n,[]);levels.get(n).push(d);});
 const maxDepth=Math.max(...levels.keys()),height=Math.max(365,(maxDepth+1)*87+35),width=790,positions=new Map();
 for(const [n,items]of levels){items.sort((a,b)=>paths.get(a.key).localeCompare(paths.get(b.key)));items.forEach((d,i)=>positions.set(d.key,{x:(i+1)*width/(items.length+1),y:35+n*87}));}
 const edgeHtml=edges.map(e=>{const a=positions.get(e.source),b=positions.get(e.target);if(!a||!b)return'';const cycle=b.y<=a.y;let d;if(cycle){const bend=Math.max(a.x,b.x)+93;d=`M ${a.x+68} ${a.y} C ${bend} ${a.y}, ${bend} ${b.y}, ${b.x+68} ${b.y}`;}else{d=`M ${a.x} ${a.y+25} C ${a.x} ${a.y+50}, ${b.x} ${b.y-50}, ${b.x} ${b.y-25}`;}return`<path class="edge ${cycle?'cycle':''}" d="${d}"><title>${esc(e.path)}</title></path>`;}).join('');
 const nodeHtml=docs.map((d,i)=>{const p=positions.get(d.key),path=paths.get(d.key),title=labelFor(path);return`<g class="node ${selected===d.key?'active':''}" data-node="${i}" tabindex="0" role="button" aria-label="Inspect ${esc(title)}"><rect x="${p.x-72}" y="${p.y-25}" width="144" height="50" rx="7"/><text x="${p.x}" y="${p.y-3}" text-anchor="middle">${esc(title)}</text><text x="${p.x}" y="${p.y+13}" class="subtitle" text-anchor="middle">${esc(path?path.split('/').slice(-2).join('/'):'ROOT DOCUMENT')}</text></g>`;}).join('');
 const doc=docs.find(d=>d.key===selected),path=paths.get(selected),roles=Object.keys(doc.channels??{});
 $('panel').innerHTML=`<div class="graph-wrap"><div class="graph-canvas"><svg viewBox="0 0 ${width} ${height}" aria-label="Native document graph"><defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#afbdd2"/></marker></defs>${edgeHtml}${nodeHtml}<text class="graph-legend" x="18" y="${height-10}">SOLID: EMBEDDING · DASHED: BACK / SHARED REFERENCE · SELECT A DOCUMENT</text></svg></div><aside class="graph-inspect"><div class="small-label">DOCUMENT INSTANCE</div><h3>${esc(labelFor(path))}</h3><p>Address in this recorded graph</p><code>${esc(path||'/')}</code><p style="margin-top:22px">Connected source channels</p>${roles.map(x=>`<span class="chip">${esc(x)}</span>`).join('')}<p style="margin-top:22px">Exact native reference</p><code>${esc(doc.blueId)}</code><p style="margin-top:19px">These are fixture routes, not a grant of live account authority. The source contains the operations each role may use.</p></aside></div>`;
 document.querySelectorAll('[data-node]').forEach(b=>{const select=()=>{selected=docs[Number(b.dataset.node)].key;renderGraph();};b.onclick=select;b.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}};});
}
function renderState(){const r=row(),values={...(r.observations??{}),...(r.reads??{})},keys=Object.keys(values).sort();$('panel').innerHTML=`<div class="scroll-panel"><p class="panel-note">Selected paths read from the actual resulting native document. This is not a reconstructed full state. Unavailable paths may refer to documents not created at this step.</p>${keys.length?keys.map(k=>`<details class="state-row" ${Object.keys(r.reads??{}).includes(k)?'open':''}><summary>${esc(k)}</summary><pre>${esc(JSON.stringify(values[k],null,2))}</pre></details>`).join(''):'<div class="empty">This row has no selected state-path assertions. Inspect its events and graph, or move to the next input.</div>'}</div>`;}
function renderEvents(){const events=row().events??[];$('panel').innerHTML=`<div class="scroll-panel"><p class="panel-note">Public events emitted by this native processing result. Child outcomes may be relayed with the host clause and original event context. An expected rejection emits no committed events.</p>${events.length?events.map((e,i)=>`<article class="event-card"><h4>${i+1}. ${esc(e.kind??'Typed document event')}${e.clause?' · '+esc(e.clause):''}</h4><pre>${esc(JSON.stringify(e,null,2))}</pre></article>`).join(''):'<div class="empty">No public events were emitted by this recorded result.</div>'}</div>`;}
function renderSource(){$('panel').innerHTML=`<div class="scroll-panel"><p class="panel-note">Complete authored source, including nested templates. Referenced clause types are supplied in the package. This read-only viewer does not execute edits.</p><pre class="source">${esc(activeCase().source)}</pre></div>`;}
function renderCatalogue(){$('panel').innerHTML=`<div class="scroll-panel"><p class="panel-note">Package families. Each entry distinguishes the delivered native profile from extensions. The full parameter and binding reference is in catalogue/payment-family.json.</p><div class="catalogue-grid">${data.catalogue.families.map((f,i)=>`<article class="family"><div class="small-label">${String(i+1).padStart(2,'0')} / CLAUSE FAMILY</div><h3>${esc(f.title)}</h3><p>${esc(f.meaning)}</p><details><summary>Parameters and scope</summary>${f.parameters.map(p=>`<div class="parameter"><code>${esc(p.name)}</code> · ${esc(p.type)}<br>${esc(p.meaning)}</div>`).join('')}<p><strong>Delivered:</strong> ${esc(f.status)}</p><p><strong>Extension:</strong> ${esc(f.extensions)}</p></details></article>`).join('')}</div></div>`;}
$('prev').onclick=()=>{stop();chooseStep(step-1);};$('next').onclick=()=>{stop();chooseStep(step+1);};$('steps').onchange=e=>{stop();chooseStep(Number(e.target.value));};
$('play').onclick=()=>{if(playing){stop();return;}if(step===activeCase().trace.length-1)step=0;playing=setInterval(()=>{if(step===activeCase().trace.length-1){stop();return;}chooseStep(step+1);},1100);$('play').textContent='Pause trace';render();};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;render();});
render();
