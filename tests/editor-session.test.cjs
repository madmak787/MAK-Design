const {test} = require('node:test');
const assert = require('node:assert/strict');
const EditorSession = require('../public/editor-session.js');
class Engine {
  constructor(dirty = false) { this.docs = [{id: 1, name: 'Untitled', dirty, path: null}]; this.active = 1; this.next = 2; }
  async execute(cmd, p) {
    if (cmd === 'doc.list') return this.docs.map((d,index)=>({...d,index,active:d.id===this.active}));
    if (cmd === 'file.new') { this.docs.push({id:this.next,name:'Untitled',dirty:true}); this.active=this.next++; return {}; }
    if (cmd === 'doc.switch') { this.active=this.docs[p.index].id; return {}; }
    if (cmd === 'file.close') {
      assert.equal(p.force, undefined, 'never force-discard a startup document');
      assert.equal(this.docs[p.index].dirty, false);
      this.docs.splice(p.index,1); return {};
    }
    throw new Error(cmd);
  }
  async openFile(name) { this.docs.push({id:this.next,name,dirty:false}); this.active=this.next++; }
}
const project={id:'saved-project',name:'Landing',data:btoa('test archive'),version:3};
test('New design reuses the engine starter: exactly one Untitled tab',async()=>{
  const api=new Engine(); const s=new EditorSession(api); await s.open();
  assert.equal(api.docs.length,1); assert.equal((await s.current()).doc.id,1);
});
test('Opening a saved project removes only the untouched starter',async()=>{
  const api=new Engine(); const s=new EditorSession(api); await s.open(project);
  assert.equal(api.docs.length,1); assert.equal((await s.current()).project.id,project.id);
});
test('Crash-recovered or edited Untitled work survives opening another project',async()=>{
  const api=new Engine(true); const s=new EditorSession(api); await s.open(project);
  assert.equal(api.docs.length,2); assert.equal(api.docs[0].id,1); assert.equal(api.docs[0].dirty,true);
});
test('Reopening a saved project switches its tab instead of duplicating it',async()=>{
  const api=new Engine(); const s=new EditorSession(api); await s.open(project); await s.open(project);
  assert.equal(api.docs.length,1); assert.equal((await s.current()).project.version,3);
});
test('Native tab changes retain the correct cloud project association',async()=>{
  const api=new Engine(); const s=new EditorSession(api); await s.open(project);
  api.docs[0].dirty=true; await s.open(); assert.equal((await s.current()).project,null);
  await api.execute('doc.switch',{index:0}); assert.equal((await s.current()).project.id,project.id);
});
