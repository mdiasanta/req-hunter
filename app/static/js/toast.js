export function toast(msg, type = '') {
  const root = document.getElementById('toast');
  if (!root) return;

  const el = document.createElement('div');
  el.className = 'toast' + (type ? ' ' + type : '');
  el.textContent = msg;
  root.appendChild(el);
  setTimeout(() => el.remove(), 3800);
}
