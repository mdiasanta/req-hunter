import { api } from '../api.js';
import { esc, fmtDate } from '../utils.js';
import { toast } from '../toast.js';

class SourcesView extends HTMLElement {
  constructor() {
    super();
    this.editingSourceId = null;
  }

  connectedCallback() {
    this.innerHTML = `
      <div class="sources-top">
        <h2>Scrape Sources</h2>
      </div>
      <div id="sources-out"></div>

      <div class="add-form">
        <h3 id="source-form-title">Add Source</h3>
        <div class="form-row">
          <div class="fg">
            <label>Name</label>
            <input id="f-name" class="w-md" type="text" placeholder="Acme Corp">
          </div>
          <div class="fg">
            <label>Base URL</label>
            <input id="f-url" class="w-lg" type="url" placeholder="https://careers.example.com/jobs">
          </div>
          <div class="fg">
            <label>Keyword</label>
            <input id="f-keyword" class="w-md" type="text" placeholder="software engineer">
          </div>
          <div class="fg">
            <label>Query Param</label>
            <input id="f-param" class="w-sm" type="text" value="q" placeholder="q">
          </div>
          <div class="fg">
            <label>URL Path Filter</label>
            <input id="f-path-filter" class="w-md" type="text" placeholder="/job/ (optional)">
          </div>
          <button class="btn" id="save-source-btn">Add</button>
          <button class="btn secondary" id="cancel-edit-btn" hidden>Cancel</button>
        </div>
      </div>
    `;

    this.querySelector('#save-source-btn').addEventListener('click', () => this.saveSource());
    this.querySelector('#cancel-edit-btn').addEventListener('click', () => this.endEditSource());
  }

  setSourceFormMode() {
    const title = this.querySelector('#source-form-title');
    const submitBtn = this.querySelector('#save-source-btn');
    const cancelBtn = this.querySelector('#cancel-edit-btn');
    const isEditing = this.editingSourceId !== null;

    title.textContent = isEditing ? 'Edit Source' : 'Add Source';
    submitBtn.textContent = isEditing ? 'Save' : 'Add';
    cancelBtn.hidden = !isEditing;
  }

  clearSourceForm() {
    ['f-name', 'f-url', 'f-keyword', 'f-path-filter'].forEach((id) => {
      this.querySelector('#' + id).value = '';
    });
    this.querySelector('#f-param').value = 'q';
  }

  beginEditSource(source) {
    this.editingSourceId = source.id;
    this.querySelector('#f-name').value = source.name || '';
    this.querySelector('#f-url').value = source.base_url || '';
    this.querySelector('#f-keyword').value = source.keyword || '';
    this.querySelector('#f-param').value = source.query_param || 'q';
    this.querySelector('#f-path-filter').value = source.url_path_filter || '';
    this.setSourceFormMode();
    this.querySelector('#f-name').focus();
    this.querySelector('#f-name').scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  endEditSource() {
    this.editingSourceId = null;
    this.clearSourceForm();
    this.setSourceFormMode();
  }

  async saveSource() {
    const name = this.querySelector('#f-name').value.trim();
    const base_url = this.querySelector('#f-url').value.trim();
    const keyword = this.querySelector('#f-keyword').value.trim();
    const query_param = this.querySelector('#f-param').value.trim() || 'q';
    const url_path_filter = this.querySelector('#f-path-filter').value.trim() || null;

    if (!name || !base_url || !keyword) {
      toast('Name, URL, and keyword are required', 'err');
      return;
    }

    try {
      const payload = { name, base_url, keyword, query_param, url_path_filter };
      if (this.editingSourceId !== null) {
        await api('/sources/' + this.editingSourceId, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        });
        toast('Source updated', 'ok');
        this.endEditSource();
      } else {
        await api('/sources/', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        toast('Source added', 'ok');
        this.clearSourceForm();
      }
      await this.refresh();
    } catch (err) {
      const action = this.editingSourceId !== null ? 'update' : 'add';
      toast(`Failed to ${action} source: ` + err.message, 'err');
    }
  }

  async refresh() {
    try {
      const data = await api('/sources/');
      this.renderSources(data.items);
      this.setSourceFormMode();
    } catch (e) {
      toast('Failed to load sources: ' + e.message, 'err');
    }
  }

  renderSources(sources) {
    const out = this.querySelector('#sources-out');
    if (!sources.length) {
      out.innerHTML = '<div class="card"><div class="empty"><strong>No sources yet</strong>Add one below to start scraping.</div></div>';
      return;
    }

    const rows = sources.map((s) => `
      <tr data-sid="${s.id}">
        <td><strong>${esc(s.name)}</strong></td>
        <td class="muted small">${esc(s.keyword)}</td>
        <td class="small">
          <a class="url-cell muted" href="${esc(s.base_url)}" target="_blank" title="${esc(s.base_url)}">${esc(s.base_url)}</a>
          ${s.url_path_filter ? `<span class="muted" style="font-size:11px">filter: ${esc(s.url_path_filter)}</span>` : ''}
        </td>
        <td class="muted small">${fmtDate(s.last_scraped_at)}</td>
        <td>
          <label class="toggle">
            <input type="checkbox" class="act-toggle" data-sid="${s.id}" ${s.is_active ? 'checked' : ''}>
            <span class="track"></span>
          </label>
        </td>
        <td>
          <div style="display:flex;gap:6px">
            <button class="btn sm secondary edit-btn" data-sid="${s.id}">Edit</button>
            <button class="btn sm run-btn" data-sid="${s.id}">&#9654; Run</button>
            <button class="btn sm danger del-btn" data-sid="${s.id}">Delete</button>
          </div>
        </td>
      </tr>
    `).join('');

    out.innerHTML = `
      <div class="card">
        <table>
          <thead><tr>
            <th>Name</th><th>Keyword</th><th>URL</th>
            <th>Last Scraped</th><th>Active</th><th>Actions</th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;

    out.querySelectorAll('.act-toggle').forEach((t) => {
      t.addEventListener('change', async (e) => {
        const sid = e.target.dataset.sid;
        const is_active = e.target.checked;
        try {
          await api('/sources/' + sid, {
            method: 'PATCH',
            body: JSON.stringify({ is_active }),
          });
          toast(is_active ? 'Source activated' : 'Source paused', 'ok');
        } catch (_err) {
          toast('Failed to update source', 'err');
          e.target.checked = !is_active;
        }
      });
    });

    out.querySelectorAll('.edit-btn').forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        const sid = Number(e.target.dataset.sid);
        try {
          const source = await api('/sources/' + sid);
          this.beginEditSource(source);
        } catch (_err) {
          toast('Failed to load source for editing', 'err');
        }
      });
    });

    out.querySelectorAll('.run-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const sid = e.target.dataset.sid;
        this.dispatchEvent(new CustomEvent('run-scrape', {
          bubbles: true,
          composed: true,
          detail: {
            path: '/scrape/run/' + sid,
            trigger: e.target,
          },
        }));
      });
    });

    out.querySelectorAll('.del-btn').forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        const sid = e.target.dataset.sid;
        const row = e.target.closest('tr');
        const name = row.querySelector('strong').textContent;
        if (!confirm(`Delete "${name}"?`)) return;
        try {
          await api('/sources/' + sid, { method: 'DELETE' });
          toast('Source deleted', 'ok');
          await this.refresh();
        } catch (_err) {
          toast('Delete failed', 'err');
        }
      });
    });
  }
}

customElements.define('sources-view', SourcesView);
