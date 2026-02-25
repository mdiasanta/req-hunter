import { api } from './api.js';
import { state } from './state.js';
import { toast } from './toast.js';
import './components/jobs-view.js';
import './components/sources-view.js';
import './components/logs-view.js';

const jobsView = document.getElementById('jobs-view');
const sourcesView = document.getElementById('sources-view');
const logsView = document.getElementById('logs-view');

async function runScrape(path, triggerBtn) {
  const runAllBtn = document.getElementById('run-all-btn');
  const statusEl = document.getElementById('scrape-status');

  runAllBtn.disabled = true;
  if (triggerBtn) {
    triggerBtn.disabled = true;
  }
  statusEl.textContent = 'Scraping…';

  try {
    const r = await api(path, { method: 'POST' });
    statusEl.textContent = '';
    const msg = `${r.jobs_new} new job${r.jobs_new !== 1 ? 's' : ''} across ${r.sources_processed} source${r.sources_processed !== 1 ? 's' : ''}`;
    toast(msg, 'ok');
    r.errors.forEach((e) => toast(e, 'err'));

    if (state.tab === 'jobs') {
      await jobsView.refresh();
    }
    if (state.tab === 'sources') {
      await sourcesView.refresh();
    }
    if (state.tab === 'logs') {
      await logsView.refresh();
    }
  } catch (err) {
    statusEl.textContent = '';
    toast('Scrape failed: ' + err.message, 'err');
  } finally {
    runAllBtn.disabled = false;
    if (triggerBtn) {
      triggerBtn.disabled = false;
    }
  }
}

document.getElementById('run-all-btn').addEventListener('click', async () => {
  await runScrape('/scrape/run');
});

document.addEventListener('run-scrape', async (e) => {
  await runScrape(e.detail.path, e.detail.trigger);
});

document.querySelectorAll('.tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach((t) => t.classList.remove('active'));
    tab.classList.add('active');

    state.tab = tab.dataset.tab;
    jobsView.hidden = state.tab !== 'jobs';
    sourcesView.hidden = state.tab !== 'sources';
    logsView.hidden = state.tab !== 'logs';

    if (state.tab === 'sources') {
      sourcesView.refresh();
    }
    if (state.tab === 'logs') {
      logsView.refresh();
    }
  });
});

jobsView.refresh();
