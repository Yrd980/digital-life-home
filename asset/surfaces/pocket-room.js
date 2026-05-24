const PHASES = {
  '/ask': ['opening mind channel', 'listening to Miri', 'writing chat trace'],
  '/bridge': ['reading body room', 'bridging to Miri', 'saving next move'],
  '/doorbell': ['opening door', 'checking pulse', 'leaving visit trace'],
  '/note': ['pinning room note', 'writing room state', 'leaving visible trace'],
  '/hunt': ['looking around', 'finding a small thing', 'refreshing shelf'],
  '/craft': ['checking shelf', 'crafting charm', 'saving trace'],
  '/today': ['reading daily', 'marking turn', 'saving trace']
};

const SHELL_PATHS = new Set(JSON.parse(document.body.dataset.shellPaths || '[]'));
const ROOM_PHASES = ['dawn', 'day', 'evening', 'night'];
const MIRI_IDLE_STATES = ['listening', 'looking', 'reading', 'typing'];
let miriIdleTimer = 0;

function actionPath(path) {
  if (path.startsWith('/web/')) return path.slice('/web'.length) || '/';
  if (path === '/web') return '/';
  return path;
}

function setThinking(text) {
  const phase = document.querySelector("[data-live='phase']");
  if (phase) phase.textContent = text || '';
}

function phaseTicker(path) {
  const phases = PHASES[path] || ['waking', 'thinking', 'writing trace'];
  let index = 0;
  setThinking(phases[index]);
  return setInterval(() => {
    index = Math.min(index + 1, phases.length - 1);
    setThinking(phases[index]);
  }, 1600);
}

function setPageClass(main) {
  const marker = main.querySelector('[data-page-class]');
  if (!marker) return;
  main.className = 'web-main ' + marker.dataset.pageClass;
  marker.remove();
}

function room() {
  return document.querySelector('[data-room]');
}

function bubble() {
  return document.querySelector('.miri-bubble');
}

function airPrompt() {
  return document.querySelector('[data-air-prompt-form]');
}

function currentRoomPhase(date = new Date()) {
  const hour = date.getHours();
  if (hour < 6 || hour >= 21) return 'night';
  if (hour < 9) return 'dawn';
  if (hour >= 18) return 'evening';
  return 'day';
}

function setRoomPhase(phase = currentRoomPhase()) {
  const currentRoom = room();
  if (!currentRoom || !ROOM_PHASES.includes(phase)) return;
  ROOM_PHASES.forEach((item) => currentRoom.classList.toggle('is-' + item, item === phase));
  currentRoom.dataset.runtimePhase = phase;
}

function syncRuntimePhase() {
  setRoomPhase(currentRoomPhase());
}

function applyLivePayload(data) {
  if (!data) return;
  const stamp = document.querySelector("[data-live='stamp']");
  const latest = document.querySelector("[data-live='latest']");
  const currentRoom = room();
  if (latest && (data.web_reply || data.reply || data.web_latest || data.latest)) {
    latest.textContent = data.web_reply || data.reply || data.web_latest || data.latest;
  }
  if (stamp && data.time) stamp.textContent = data.time;
  if (currentRoom) {
    if (data.room_phase) setRoomPhase(data.room_phase);
    if (data.miri_state) currentRoom.dataset.miriState = data.miri_state;
    currentRoom.classList.toggle('has-relics', Number(data.relic_count || 0) > 0);
    currentRoom.classList.toggle('has-stash', Number(data.stash_count || 0) > 0);
    currentRoom.classList.toggle('has-notes', Number(data.note_count || 0) > 0);
  }
  if (data.bubble_tone && bubble()) bubble().dataset.bubbleTone = data.bubble_tone;
}

function chooseMiriIdleState() {
  const currentRoom = room();
  if (!currentRoom) return 'listening';
  if (currentRoom.classList.contains('is-speaking')) return 'listening';
  if (currentRoom.dataset.runtimePhase === 'night' && Math.random() < 0.35) return 'dozing';
  return MIRI_IDLE_STATES[Math.floor(Math.random() * MIRI_IDLE_STATES.length)];
}

function scheduleMiriIdle(delay = 1200) {
  window.clearTimeout(miriIdleTimer);
  miriIdleTimer = window.setTimeout(() => {
    const currentRoom = room();
    if (currentRoom) currentRoom.dataset.miriIdle = chooseMiriIdleState();
    scheduleMiriIdle(6500 + Math.random() * 9000);
  }, delay);
}

function setHotspot(name = '') {
  const currentRoom = room();
  if (currentRoom) currentRoom.dataset.hotspot = name;
}

function showAirPrompt(seed = '') {
  const form = airPrompt();
  if (!form) return;
  const input = form.querySelector('input');
  const currentRoom = room();
  currentRoom?.classList.add('is-speaking');
  if (currentRoom) {
    currentRoom.dataset.hotspot = 'miri';
    currentRoom.dataset.miriIdle = 'listening';
  }
  form.classList.add('is-visible');
  if (input) {
    if (seed && !input.value) input.value = seed;
    input.focus();
    input.selectionStart = input.value.length;
    input.selectionEnd = input.value.length;
  }
}

function hideAirPrompt(delay = 0) {
  const form = airPrompt();
  if (!form) return;
  window.setTimeout(() => {
    const input = form.querySelector('input');
    if (document.activeElement === input || (input && input.value.trim())) return;
    form.classList.remove('is-visible');
    const currentRoom = room();
    currentRoom?.classList.remove('is-speaking');
    if (currentRoom?.dataset.hotspot === 'miri') currentRoom.dataset.hotspot = '';
  }, delay);
}

function openRoomPanel(name) {
  const drawer = document.querySelector('[data-room-drawer]');
  if (!drawer) return;
  const panels = Array.from(drawer.querySelectorAll('[data-panel]'));
  const panel = panels.find((item) => item.dataset.panel === name) || panels[0];
  panels.forEach((item) => item.classList.toggle('is-active', item === panel));
  const title = drawer.querySelector('[data-panel-title]');
  if (title && panel) title.textContent = panel.dataset.panelLabel || panel.dataset.panel || '';
  drawer.dataset.panelName = name;
  const currentRoom = room();
  if (currentRoom) {
    currentRoom.classList.add('is-focused');
    currentRoom.dataset.focus = name;
    currentRoom.dataset.hotspot = name;
    currentRoom.dataset.miriIdle = 'looking';
  }
  drawer.hidden = false;
}

function closeRoomPanel() {
  const drawer = document.querySelector('[data-room-drawer]');
  if (drawer) {
    drawer.hidden = true;
    drawer.dataset.panelName = '';
  }
  const currentRoom = room();
  if (currentRoom) {
    currentRoom.classList.remove('is-focused');
    currentRoom.dataset.focus = '';
    currentRoom.dataset.hotspot = '';
  }
}

async function refreshVitals() {
  try {
    const res = await fetch('/api/live', {cache: 'no-store'});
    if (!res.ok) return;
    const data = await res.json();
    applyLivePayload(data);
  } catch (_) {}
}

async function submitAction(form) {
  const path = actionPath(form.getAttribute('action') || '/ask');
  const resultBox = document.querySelector("[data-live='result']");
  const buttons = Array.from(form.querySelectorAll('button'));
  const ticker = phaseTicker(path);
  room()?.classList.add('is-busy');
  buttons.forEach((button) => button.disabled = true);
  try {
    const res = await fetch('/api' + path, {method: 'POST', body: new FormData(form)});
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    if (resultBox) resultBox.textContent = data.web_result || data.result || '';
    applyLivePayload(data.live || data);
    if (form.matches('[data-air-prompt-form]')) {
      form.reset();
      form.querySelector('input')?.blur();
      hideAirPrompt(1300);
    }
    setThinking('done');
  } catch (error) {
    if (resultBox) resultBox.textContent = 'Action failed: ' + (error && error.message ? error.message : error);
    setThinking('failed');
  } finally {
    clearInterval(ticker);
    buttons.forEach((button) => button.disabled = false);
    room()?.classList.remove('is-busy');
  }
}

async function navigateRoom(path, push = true) {
  const clean = path || '/';
  if (!SHELL_PATHS.has(clean)) {
    window.location.href = clean;
    return;
  }
  const main = document.querySelector('.web-main');
  if (!main) {
    window.location.href = clean;
    return;
  }
  main.setAttribute('aria-busy', 'true');
  try {
    const res = await fetch(clean + '?partial=1', {cache: 'no-store'});
    if (!res.ok) throw new Error('navigation failed');
    main.innerHTML = await res.text();
    setPageClass(main);
    if (push) history.pushState({path: clean}, '', clean);
    await refreshVitals();
    syncRuntimePhase();
    scheduleMiriIdle();
  } catch (_) {
    window.location.href = clean;
  } finally {
    main.removeAttribute('aria-busy');
  }
}

document.addEventListener('submit', (event) => {
  const form = event.target;
  if (form && form.matches("[data-action='async']")) {
    event.preventDefault();
    if (form.matches('[data-air-prompt-form]')) {
      const input = form.querySelector('input');
      if (!input || !input.value.trim()) {
        form.reset();
        input?.blur();
        hideAirPrompt(0);
        return;
      }
    }
    submitAction(form);
  }
});

document.addEventListener('click', (event) => {
  const panelTarget = event.target.closest('[data-panel-target]');
  if (panelTarget) {
    event.preventDefault();
    openRoomPanel(panelTarget.dataset.panelTarget);
    return;
  }
  if (event.target.closest('[data-air-prompt]')) {
    event.preventDefault();
    showAirPrompt();
    return;
  }
  if (event.target.closest('[data-panel-close]')) {
    event.preventDefault();
    closeRoomPanel();
  }
});

document.addEventListener('pointerover', (event) => {
  const target = event.target.closest?.('[data-hotspot]');
  if (target) setHotspot(target.dataset.hotspot || '');
});

document.addEventListener('pointerout', (event) => {
  const target = event.target.closest?.('[data-hotspot]');
  if (!target) return;
  const next = event.relatedTarget;
  if (next && target.contains(next)) return;
  const nextHotspot = next?.closest?.('[data-hotspot]');
  if (nextHotspot && nextHotspot.dataset.hotspot === target.dataset.hotspot) return;
  setHotspot('');
});

document.addEventListener('keydown', (event) => {
  const target = event.target;
  const typing = target && (
    target.matches?.('input, textarea, select') ||
    target.isContentEditable
  );
  if (typing) {
    if (event.key === 'Escape') {
      target.blur();
      hideAirPrompt(0);
    }
    return;
  }
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  if (event.key === 'Escape') {
    closeRoomPanel();
    hideAirPrompt(0);
    return;
  }
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    showAirPrompt();
    return;
  }
  if (event.key.length === 1) {
    event.preventDefault();
    showAirPrompt(event.key);
  }
});

document.addEventListener('focusout', (event) => {
  if (event.target.closest?.('[data-air-prompt-form]')) hideAirPrompt(1600);
});

window.addEventListener('popstate', () => navigateRoom(window.location.pathname, false));
syncRuntimePhase();
scheduleMiriIdle();
window.setInterval(syncRuntimePhase, 60000);
setInterval(refreshVitals, 7000);
