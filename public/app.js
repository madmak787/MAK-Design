'use strict';
const $=id=>document.getElementById(id);
let csrf='', active=null, pending=false, dirty=false, apiReady=null;
let docSession=null, opening=false, currentDocId=null, nameDirty=false;
let allProjects=[], fileFilter='recent', fileLayout='grid', syncing=false;
const allowed=new Set(['node.create','node.set','text.create','text.set','text.style','shape.rectangle','shape.ellipse','frame.create','layout.add','layout.set','fill.add','fill.set','stroke.add','stroke.set','effect.add','transform.move','transform.resize','align.left','align.top']);
function notice(message){$('notice').textContent=message;$('notice').hidden=false;}
document.addEventListener('click',e=>{if(e.target!==$('notice')) $('notice').hidden=true;});
function show(id){document.body.classList.toggle('editing',id==='work');document.body.classList.toggle('browsing',id==='home');document.body.classList.toggle('viewing',id==='viewer');for(const x of ['login','home','work','viewer']) $(x).hidden=x!==id;}
async function request(action,body,query={}){const url=new URL('/api.php',location.origin);url.searchParams.set('action',action);for(const [k,v]of Object.entries(query))url.searchParams.set(k,v);const res=await fetch(url,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json','X-CSRF-Token':csrf}:{},body:body?JSON.stringify(body):undefined,credentials:'same-origin'});const value=await res.json();if(!res.ok)throw new Error(value.error||'Request failed.');return value;}
function guard(fn){return async()=>{try{await fn();}catch(e){notice(e.message);}};}
function element(tag, className, text) {
  const el=document.createElement(tag); if(className)el.className=className;
  if(text!==undefined)el.textContent=text; return el;
}
function renderFiles(){
  const query=$('file-search').value.toLocaleLowerCase().trim();
  let projects=allProjects.filter(p=>(fileFilter!=='shared'||Number(p.links)>0)&&p.name.toLocaleLowerCase().includes(query));
  projects.sort($('file-sort').value==='name'?(a,b)=>a.name.localeCompare(b.name):(a,b)=>b.updated.localeCompare(a.updated));
  $('files-heading').textContent={recent:'Recents',all:'All files',shared:'Shared with clients'}[fileFilter];
  $('file-count').textContent=projects.length+' '+(projects.length===1?'file':'files');
  $('projects').classList.toggle('list-layout',fileLayout==='list');
  $('projects').replaceChildren();
  for(const p of projects){
    const card=element('article','project');
    const preview=element('button','file-preview');preview.setAttribute('aria-label','Open '+p.name);
    if(Number(p.hasPreview)){
      const image=element('img');image.src='/api.php?action=thumbnail&id='+encodeURIComponent(p.id)+'&version='+p.version;
      image.alt='';image.loading='lazy';preview.append(image);
    }else preview.append(element('span','file-placeholder','✦'));
    preview.onclick=guard(()=>openProject(p.id));
    const info=element('div','file-info');
    const open=element('button','file-name',p.name);open.onclick=guard(()=>openProject(p.id));
    const date=element('p','small muted','Edited '+new Date(p.updated).toLocaleString());
    info.append(open,date);
    const row=element('div','row file-sharing');
    row.append(element('span','file-badge',Number(p.links)?'Shared · '+p.links+' links':'Private'));
    if(Number(p.links)){
      const revoke=element('button','revoke-link','Revoke links');
      revoke.onclick=guard(async()=>{await request('revoke',{id:p.id});notice('Client links revoked.');await home();});row.append(revoke);
    }
    info.append(row);card.append(preview,info);$('projects').append(card);
  }
  if(!projects.length){
    const empty=element('div','empty');empty.append(element('span','empty-symbol','✦'),element('h2','',query?'No matching files':fileFilter==='shared'?'No shared files yet':'A fresh canvas awaits'),element('p','muted',query?'Try another file name.':fileFilter==='shared'?'Create a client preview link from the editor to see it here.':'Create a design to start making something good.'));
    $('projects').append(empty);
  }
  document.querySelectorAll('[data-filter]').forEach(button=>{
    if(button.dataset.filter===fileFilter)button.setAttribute('aria-current','page');else button.removeAttribute('aria-current');
  });
  $('grid-view').setAttribute('aria-pressed',String(fileLayout==='grid'));
  $('list-view').setAttribute('aria-pressed',String(fileLayout==='list'));
}
async function home(){allProjects=(await request('list')).projects;renderFiles();show('home');}
async function editor(){if(apiReady)return apiReady;apiReady=new Promise((resolve,reject)=>{const frame=$('editor');let tries=0;frame.src='/editor/index.html?control';const timer=setInterval(()=>{if(frame.contentWindow?.figcraft){clearInterval(timer);frame.contentWindow.figcraft.execute('pref.publishServer',{url:''}).then(()=>{docSession=new MakEditorSession(frame.contentWindow.figcraft);resolve(frame.contentWindow.figcraft);},reject);}else if(++tries>180){clearInterval(timer);apiReady=null;reject(new Error('The editor could not start. Try a current desktop browser with WebGL2 enabled.'));}},500);});return apiReady;}
async function syncProjectState(){
  if(!docSession||$('work').hidden||syncing||opening)return;
  syncing=true;
  try{
    const state=await docSession.current();if(!state)return;
    if(state.doc.id!==currentDocId){
      currentDocId=state.doc.id;nameDirty=false;
      $('project-name').value=state.project?.name||state.doc.name;
    }
    active=state.project;dirty=state.doc.dirty||nameDirty;
    $('save-status').textContent=pending?'Saving…':dirty?'Unsaved changes':active?'Saved':'Draft';
  }finally{syncing=false;}
}
async function openProject(id){
  if(opening)return;
  if(pending)throw new Error('Please wait for the current save to finish.');
  if(dirty&&!confirm('Switch files? Your current design will stay open in its tab. Save first to keep it on the server.'))return;
  opening=true;
  try{
    const project=id?await request('load',null,{id}):null;
    show('work');notice('Opening your design…');const api=await editor();
    const state=await docSession.open(project);
    currentDocId=state.doc.id;active=state.project;nameDirty=false;dirty=state.doc.dirty;
    $('project-name').value=active?.name||state.doc.name;
    await api.execute('view.layers',{});await api.execute('view.design',{});await api.execute('view.zoomFit',{});
    $('save-status').textContent=dirty?'Unsaved changes':active?'Saved':'Draft';$('notice').hidden=true;
  }finally{opening=false;}
}
async function save(){
  if(pending)return;
  pending=true;$('save').disabled=true;$('save-status').textContent='Saving…';
  try{
    const api=await editor();const state=await docSession.current();if(!state)throw new Error('No active design.');
    const name=$('project-name').value.trim();if(!name)throw new Error('Give this design a name.');
    if(name!==state.doc.name)await api.execute('file.rename',{name});
    const file=await api.execute('file.saveAs',{data:true});let preview='',previewError='';
    try{preview=(await api.execute('file.export',{format:'png',size:'1600w'})).data;}catch(e){previewError=e.message;}
    const p=await request('save',{id:state.project?.id||'',version:state.project?.version||0,name,data:file.data,preview});
    await docSession.record({id:p.id,version:p.version,name},state.doc.id);
    const now=await docSession.current();
    if(now?.doc.id===state.doc.id){
      active={id:p.id,version:p.version,name};nameDirty=$('project-name').value.trim()!==name;
      // Edits made during the upload must not be marked as saved.
      const latest=await api.execute('file.saveAs',{data:true});
      if(latest.data===file.data)await api.execute('file.markSaved',{});
      dirty=nameDirty||latest.data!==file.data;
    }
    notice(previewError?'Design saved. Preview could not be updated: '+previewError:'Project and client preview saved.');
  }finally{pending=false;$('save').disabled=false;await syncProjectState();}
}
function download(name,data){const blob=new Blob([data],{type:'application/octet-stream'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
async function copy(text){try{await navigator.clipboard.writeText(text);notice('Copied to clipboard.');return true;}catch{const area=document.createElement('textarea');area.value=text;area.readOnly=true;$('notice').replaceChildren(area);$('notice').hidden=false;area.select();return false;}}
async function share(){active=(await docSession?.current())?.project||null;if(!active)throw new Error('Save your project and preview first.');const result=await request('share',{id:active.id});const copied=await copy(location.origin+'/#view='+result.token);if(copied)notice('Client preview link copied. It expires in 30 days. Revoke links from Projects.');}
async function copyPrompt(){const api=await editor();const commands=(await api.commands()).filter(c=>allowed.has(c.id));const prompt='Create an editable design for MAK Design using the FigCraft command API. Brief: '+$('brief').value+'\nReturn ONLY JSON {"commands":[{"command":"node.create","params":{...},"as":"frame"},...]}. Maximum 150 commands. Add layers to the active page; do not delete or open files. Use these exact command schemas:\n'+JSON.stringify(commands)+'\nStep references: set "as":"frame" on an earlier command and use {"$ref":"frame"} as a later parent/id. node.create uses type, x,y,width,height,name,text and props. Use hex colours such as #9c225f. Preserve existing layers. Avoid external assets and scripts. Text, geometry and colours must remain editable.';await copy(prompt);}
async function importCommands(raw){if(raw.length>200000)throw new Error('The AI reply is too large.');const cleaned=raw.trim().replace(/^```(?:json)?\s*/,'').replace(/\s*```$/,'');const value=JSON.parse(cleaned);if(!Array.isArray(value.commands)||!value.commands.length||value.commands.length>150)throw new Error('Expected JSON with 1–150 commands.');for(const c of value.commands){if(!c||!allowed.has(c.command)||typeof c.params!=='object'||!c.params)throw new Error('This reply contains an unsupported command. Copy a fresh prompt and try again.');}await (await editor()).execute('command.batch',{commands:value.commands,label:'AI design import'});await (await editor()).execute('select.none',{});await (await editor()).execute('view.zoomFit',{});dirty=true;notice('Editable layers added. Review the design, then save. Use Undo to remove the import.');}
const sample={commands:[{command:'node.create',as:'hero',params:{type:'frame',name:'MAK · Studio landing',width:1200,height:800,props:{fill:'#fff8f3'}}},{command:'node.create',params:{type:'text',parent:{$ref:'hero'},x:64,y:56,width:900,height:44,text:'MAK / DESIGN STUDIO',props:{fontSize:20,fill:'#9c225f'}}},{command:'node.create',params:{type:'text',parent:{$ref:'hero'},x:64,y:220,width:1050,height:200,text:'Good ideas deserve\na little room to grow.',props:{fontSize:72,fill:'#9c225f'}}},{command:'node.create',params:{type:'rectangle',parent:{$ref:'hero'},x:64,y:535,width:260,height:64,props:{fill:'#9c225f',cornerRadius:12}}},{command:'node.create',params:{type:'text',parent:{$ref:'hero'},x:92,y:552,width:210,height:40,text:'Let’s make something ↗',props:{fontSize:18,fill:'#ffffff'}}}]};
$('login-form').onsubmit=async e=>{e.preventDefault();try{const p=await request('login',{password:$('password').value});csrf=p.csrf;$('password').value='';$('logout').hidden=false;await home();}catch(err){notice(err.message);}};
$('logout').onclick=guard(async()=>{if(dirty&&!confirm('Sign out? Download or save your design first.'))return;await request('logout',{});location.reload();});
$('new').onclick=guard(()=>openProject());$('save').onclick=guard(save);$('back').onclick=guard(async()=>{if(dirty&&!confirm('Return to projects? Save first to keep this design on the server.'))return;await home();});$('share').onclick=guard(share);
$('download').onclick=guard(async()=>{const f=await (await editor()).execute('file.saveAs',{data:true});download(f.name,Uint8Array.from(atob(f.data),c=>c.charCodeAt(0)));notice('Design downloaded.');});
function toggleAI(open){$('ai').hidden=!open;$('ai-toggle').setAttribute('aria-expanded',String(open));}
$('ai-toggle').onclick=()=>toggleAI($('ai').hidden);$('ai-close').onclick=()=>toggleAI(false);
$('layers-toggle').onclick=guard(async()=>{await (await editor()).execute('view.layers',{});});
$('properties-toggle').onclick=guard(async()=>{await (await editor()).execute('view.design',{});});
$('fullscreen').onclick=guard(async()=>{if(document.fullscreenElement)await document.exitFullscreen();else if(document.documentElement.requestFullscreen)await document.documentElement.requestFullscreen();else throw new Error('Use your browser’s fullscreen option on this device.');});
$('copy-prompt').onclick=guard(copyPrompt);$('import').onclick=guard(()=>importCommands($('commands').value));$('starter').onclick=guard(()=>importCommands(JSON.stringify(sample)));
$('project-name').oninput=()=>{dirty=true;nameDirty=true;$('save-status').textContent='Unsaved changes';};
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{fileFilter=b.dataset.filter;renderFiles();});
$('file-search').oninput=renderFiles;$('file-sort').onchange=renderFiles;
$('grid-view').onclick=()=>{fileLayout='grid';renderFiles();};$('list-view').onclick=()=>{fileLayout='list';renderFiles();};
document.querySelectorAll('[data-action]').forEach(button=>button.onclick=()=>{
  button.closest('details').open=false;
  const target={new:'new',save:'save',download:'download',share:'share',back:'back',fullscreen:'fullscreen'}[button.dataset.action];
  if(target)$(target).click();
});
document.querySelectorAll('[data-command]').forEach(button=>button.onclick=guard(async()=>{
  button.closest('details').open=false;await (await editor()).execute(button.dataset.command,{});await syncProjectState();
}));
document.addEventListener('click',event=>document.querySelectorAll('.command-menu[open]').forEach(menu=>{if(!menu.contains(event.target))menu.open=false;}));
document.addEventListener('keydown',event=>{if(event.key==='Escape'){toggleAI(false);document.querySelectorAll('.command-menu[open]').forEach(menu=>menu.open=false);}});
setInterval(()=>syncProjectState().catch(()=>{}),800);
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
(async()=>{try{const token=new URLSearchParams(location.hash.slice(1)).get('view');if(token){$('logout').hidden=true;show('viewer');const p=await request('preview',null,{token});$('view-name').textContent=p.name;$('view-updated').textContent='Last saved '+new Date(p.updated).toLocaleString();$('view-image').src='/api.php?action=preview&image=1&token='+encodeURIComponent(token);return;}const s=await request('session');csrf=s.csrf;$('logout').hidden=!s.owner;if(s.owner)await home();else show('login');}catch(e){show('login');notice(e.message);}})();
