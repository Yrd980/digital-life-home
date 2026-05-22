const PHASES = {
  '/ask': ['opening mind channel', 'listening to Miri', 'writing memory trace'],
  '/bridge': ['scanning body', 'asking Miri', 'shaping room voice'],
  '/nightly': ['reading today logs', 'folding relics', 'writing nightly'],
  '/postcard': ['reading heading', 'drawing constellation', 'writing postcard'],
  '/bottle': ['sealing message', 'placing bottle in state', 'refreshing shelf'],
  '/doorbell': ['opening door', 'checking pulse', 'leaving visit relic'],
  '/ritual': ['choosing ritual', 'asking imagination', 'saving trace'],
  '/toy': ['checking toy bay', 'saving toy trace'],
  '/quest': ['touching quest', 'updating state', 'saving relic'],
  '/heading': ['reading heartbeat', 'choosing heading', 'saving course'],
  '/remember': ['holding memory', 'writing state', 'lighting relic']
};
function setThinking(active, text) {
  const phase = document.querySelector("[data-live='phase']");
  if (phase) phase.textContent = text || '';
}
const SHELL_PATHS = new Set(JSON.parse(document.body.dataset.shellPaths || '[]'));
function actionPath(path) {
  if (path.startsWith('/board/')) return path.slice('/board'.length) || '/';
  if (path === '/board') return '/';
  if (path.startsWith('/web/')) return path.slice('/web'.length) || '/';
  if (path === '/web') return '/';
  return path;
}
function wakeRoom() {
  // Keep web calm: data updates only, no decorative motion.
}
function phaseTicker(path) {
  const phases = PHASES[path] || ['waking', 'thinking', 'writing trace'];
  let index = 0;
  setThinking(true, phases[index]);
  return setInterval(() => {
    index = Math.min(index + 1, phases.length - 1);
    setThinking(true, phases[index]);
  }, 1600);
}
async function refreshVitals() {
  const box = document.querySelector("[data-live='vitals']");
  const stamp = document.querySelector("[data-live='stamp']");
  const latest = document.querySelector("[data-live='latest']");
  const mood = document.querySelector("[data-live='mood']");
  try {
    const res = await fetch('/api/live', {cache: 'no-store'});
    if (!res.ok) return;
    const data = await res.json();
    if (box) box.innerHTML = box.classList.contains('mini-vitals') && data.vitals_html ? data.vitals_html : (data.presence || data.vitals);
    if (latest && (data.reply || data.latest)) latest.innerHTML = (data.reply || data.latest).replace(/</g, '&lt;').replace(/>/g, '&gt;') + '<br><span class="heart">*</span>';
    if (mood && data.mood) mood.textContent = data.mood;
    if (stamp) stamp.textContent = data.time;
  } catch (_) {}
}
setInterval(refreshVitals, 7000);
async function submitFlash(form) {
  wakeRoom();
  const resultBox = document.querySelector("[data-live='result']");
  const flashBox = document.querySelector("[data-live='flash']");
  const button = form.querySelector("button");
  if (button) button.disabled = true;
  try {
    const res = await fetch('/api/bridge-flash', {method: 'POST', body: new FormData(form)});
    if (!res.ok) throw new Error('flash failed');
    const data = await res.json();
    if (resultBox) resultBox.textContent = data.result;
    if (flashBox) flashBox.textContent = data.flash;
    const live = data.live || {};
    const vitals = document.querySelector("[data-live='vitals']");
    const stamp = document.querySelector("[data-live='stamp']");
    if (vitals && live.vitals) vitals.innerHTML = live.vitals;
    if (stamp && live.time) stamp.textContent = live.time;
    form.reset();
  } catch (_) {
    form.submit();
  } finally {
    if (button) button.disabled = false;
  }
}
async function submitAction(form) {
  wakeRoom();
  const path = actionPath(form.getAttribute('action') || '/ask');
  const resultBox = document.querySelector("[data-live='result']");
  const buttons = Array.from(form.querySelectorAll("button"));
  const ticker = phaseTicker(path);
  buttons.forEach((button) => button.disabled = true);
  try {
    const res = await fetch('/api' + path, {method: 'POST', body: new FormData(form)});
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    if (resultBox) resultBox.textContent = data.result || '';
    const live = data.live || {};
    const vitals = document.querySelector("[data-live='vitals']");
    const stamp = document.querySelector("[data-live='stamp']");
    if (vitals && live.vitals) vitals.innerHTML = live.vitals;
    if (stamp && live.time) stamp.textContent = live.time;
    await refreshVitals();
    setThinking(false, 'done');
  } catch (error) {
    if (resultBox) resultBox.textContent = 'Action failed: ' + (error && error.message ? error.message : error);
    setThinking(false, 'failed');
  } finally {
    clearInterval(ticker);
    buttons.forEach((button) => button.disabled = false);
  }
}
function setActiveNav(path) {
  const clean = path === '' ? '/' : path;
  document.querySelectorAll('.nav-item').forEach((item) => {
    const href = item.getAttribute('href') || '/';
    item.classList.toggle('is-active', href === clean);
  });
}
async function navigateRoom(path, push = true) {
  const clean = path || '/';
  if (!SHELL_PATHS.has(clean)) {
    window.location.href = clean;
    return;
  }
  const main = document.querySelector('.deck-main') || document.querySelector('.board-main');
  if (!main) {
    window.location.href = clean;
    return;
  }
  main.setAttribute('aria-busy', 'true');
  try {
    const res = await fetch(clean + '?partial=1', {cache: 'no-store'});
    if (!res.ok) throw new Error('navigation failed');
    main.innerHTML = await res.text();
    setActiveNav(clean);
    document.body.className = document.body.classList.contains('surface-board') ? 'cockpit-page surface-board' : 'cockpit-page surface-web';
    if (push) history.pushState({path: clean}, '', clean);
    await refreshVitals();
  } catch (_) {
    window.location.href = clean;
  } finally {
    main.removeAttribute('aria-busy');
  }
}
document.addEventListener('submit', (event) => {
  const form = event.target;
  if (form && form.matches("[data-action='flash']")) {
    event.preventDefault();
    submitFlash(form);
  } else if (form && form.matches("[data-action='async']")) {
    event.preventDefault();
    submitAction(form);
  }
});
document.addEventListener('click', (event) => {
  const link = event.target.closest('a[href]');
  if (!link || event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const url = new URL(link.href, window.location.href);
  if (url.origin !== window.location.origin) return;
  if (!SHELL_PATHS.has(url.pathname)) return;
  event.preventDefault();
  navigateRoom(url.pathname);
});
window.addEventListener('popstate', () => navigateRoom(window.location.pathname, false));
