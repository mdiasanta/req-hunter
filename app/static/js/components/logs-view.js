import { api } from '../api.js';
import { toast } from '../toast.js';

class LogsView extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <div class="logs-top">
        <h2>Application Logs</h2>
        <div class="logs-actions">
          <label class="small muted" for="logs-limit">Lines</label>
          <input id="logs-limit" type="number" value="200" min="1" max="2000">
          <button class="btn secondary" id="logs-refresh-btn">Refresh</button>
        </div>
      </div>
      <div class="logs-panel" id="logs-out">No logs loaded yet.</div>
    `;

    this.querySelector('#logs-refresh-btn').addEventListener('click', () => this.refresh());
  }

  async refresh() {
    const logsOut = this.querySelector('#logs-out');
    const rawLimit = Number(this.querySelector('#logs-limit').value || 200);
    const limit = Math.max(1, Math.min(2000, rawLimit));
    this.querySelector('#logs-limit').value = String(limit);

    logsOut.textContent = 'Loading logs...';
    try {
      const data = await api('/logs/?limit=' + limit);
      if (!data.items.length) {
        logsOut.textContent = 'No logs yet.';
        return;
      }
      logsOut.textContent = data.items.join('\n');
      logsOut.scrollTop = logsOut.scrollHeight;
    } catch (err) {
      logsOut.textContent = 'Failed to load logs.';
      toast('Failed to load logs: ' + err.message, 'err');
    }
  }
}

customElements.define('logs-view', LogsView);
