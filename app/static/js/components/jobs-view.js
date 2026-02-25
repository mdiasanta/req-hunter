import { api } from '../api.js';
import { PER_PAGE, STATUSES, state } from '../state.js';
import { esc, fmtDate } from '../utils.js';
import { toast } from '../toast.js';

function badge(s) {
  return `<span class="badge s-${s}">${s}</span>`;
}

function statusSelect(id, cur) {
  return '<select class="s-select" data-id="' + id + '">' +
    STATUSES.map(s => `<option${s === cur ? ' selected' : ''}>${s}</option>`).join('') +
    '</select>';
}

class JobsView extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <div class="filters" id="filters">
        <button class="pill active" data-status="">All</button>
        <button class="pill" data-status="new">New</button>
        <button class="pill" data-status="seen">Seen</button>
        <button class="pill" data-status="applied">Applied</button>
        <button class="pill" data-status="rejected">Rejected</button>
        <button class="pill" data-status="ignored">Ignored</button>
      </div>
      <div id="jobs-out"></div>
    `;

    this.querySelector('#filters').addEventListener('click', (e) => {
      const pill = e.target.closest('.pill');
      if (!pill) return;
      this.querySelectorAll('.pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      state.filter = pill.dataset.status;
      state.page = 0;
      this.refresh();
    });
  }

  async refresh() {
    const qs = new URLSearchParams({
      limit: PER_PAGE,
      offset: state.page * PER_PAGE,
    });

    if (state.filter) {
      qs.set('status', state.filter);
    }

    try {
      const data = await api('/jobs/?' + qs);
      state.total = data.total;
      this.renderJobs(data.items);
    } catch (e) {
      toast('Failed to load jobs: ' + e.message, 'err');
    }
  }

  renderJobs(jobs) {
    const out = this.querySelector('#jobs-out');

    if (!jobs.length) {
      out.innerHTML = '<div class="card"><div class="empty"><strong>No jobs found</strong>Add a source and run a scrape to get started.</div></div>';
      return;
    }

    const rows = jobs.map((j) => `
      <tr>
        <td class="col-title"><a href="${esc(j.url)}" target="_blank" rel="noopener">${esc(j.title)}</a></td>
        <td>${esc(j.company)}</td>
        <td class="muted">${j.location ? esc(j.location) : '—'}</td>
        <td class="muted small">${esc(j.source)}</td>
        <td class="muted small">${fmtDate(j.scraped_at)}</td>
        <td>${badge(j.status)}</td>
        <td>${statusSelect(j.id, j.status)}</td>
      </tr>
    `).join('');

    const start = state.page * PER_PAGE + 1;
    const end = Math.min(start + jobs.length - 1, state.total);

    out.innerHTML = `
      <div class="card">
        <table>
          <thead>
            <tr>
              <th>Title</th><th>Company</th><th>Location</th>
              <th>Source</th><th>Scraped</th><th>Status</th><th>Change</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
        <div class="pager">
          <span class="pager-info">${start}–${end} of ${state.total}</span>
          <div class="pager-btns">
            <button class="btn secondary sm" id="pg-prev" ${state.page === 0 ? 'disabled' : ''}>&#8592; Prev</button>
            <button class="btn secondary sm" id="pg-next" ${end >= state.total ? 'disabled' : ''}>Next &#8594;</button>
          </div>
        </div>
      </div>
    `;

    out.querySelector('#pg-prev')?.addEventListener('click', () => {
      state.page -= 1;
      this.refresh();
    });

    out.querySelector('#pg-next')?.addEventListener('click', () => {
      state.page += 1;
      this.refresh();
    });

    out.querySelectorAll('.s-select').forEach((sel) => {
      sel.addEventListener('change', async (e) => {
        const id = e.target.dataset.id;
        const status = e.target.value;
        try {
          await api('/jobs/' + id, {
            method: 'PATCH',
            body: JSON.stringify({ status }),
          });
          const b = e.target.closest('tr').querySelector('.badge');
          b.className = 'badge s-' + status;
          b.textContent = status;
          toast('Marked as ' + status, 'ok');
        } catch (_err) {
          toast('Update failed', 'err');
        }
      });
    });
  }
}

customElements.define('jobs-view', JobsView);
