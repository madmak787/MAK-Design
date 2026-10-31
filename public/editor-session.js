/* Document lifecycle shared by the portal and its regression checks. */
(function (root) {
  'use strict';
  class EditorSession {
    constructor(api) { this.api = api; this.projects = new Map(); }
    async documents() { return this.api.execute('doc.list', {}); }
    async current() {
      const doc = (await this.documents()).find(d => d.active);
      return doc ? {doc, project: this.projects.get(doc.id) || null} : null;
    }
    async open(project) {
      const before = await this.documents();
      const starter = before.length === 1 && before[0].name === 'Untitled' &&
        !before[0].dirty && !before[0].path ? before[0] : null;
      if (project) {
        const existing = before.find(d => this.projects.get(d.id)?.id === project.id);
        if (existing) {
          await this.api.execute('doc.switch', {index: existing.index});
          return this.current();
        }
        await this.api.openFile(project.name + '.figcraft',
          Uint8Array.from(atob(project.data), c => c.charCodeAt(0)));
        const opened = await this.current();
        if (!opened) throw new Error('The design could not be opened.');
        this.projects.set(opened.doc.id, {id: project.id, version: project.version, name: project.name});
        // Only the engine's untouched starter is removed. Recovered or edited files stay open.
        if (starter && starter.id !== opened.doc.id) {
          const blank = (await this.documents()).find(d => d.id === starter.id && !d.dirty && !d.path);
          if (blank) await this.api.execute('file.close', {index: blank.index});
        }
      } else if (!starter) {
        await this.api.execute('file.new', {});
      }
      return this.current();
    }
    async record(project, documentId) {
      if(documentId!==undefined){this.projects.set(documentId,project);return;}
      const current = await this.current();
      if (!current) throw new Error('No active design.');
      this.projects.set(current.doc.id, project);
    }
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = EditorSession;
  else root.MakEditorSession = EditorSession;
})(globalThis);
