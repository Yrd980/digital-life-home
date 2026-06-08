const ROOM_PHASES = ['dawn', 'day', 'evening', 'night'];
const MIRI_IDLE_STATES = ['listening', 'looking', 'reading', 'typing'];
const ACTION_LINES = {
  knock: 'The door answers with a soft little knock.',
  find: 'Dust gathers on the rug. Something tiny wants to be found.',
  craft: 'The craft bench gives one warm spark.',
  daily: 'The marked day glows brighter.',
  note: 'A new scrap joins the pinboard.',
  talk: 'Miri listens. The room keeps the whisper.'
};
const PIECE_REACTIONS = {
  'coffee mug': 'The mug gives off a tiny warm breath.',
  'open notebook': 'The notebook waits on a half-written line.',
  'tiny keyboard': 'The tiny keyboard clicks once.',
  cassette: 'The cassette catches a purple glint.',
  'small screwdriver': 'The screwdriver rolls a careful quarter turn.',
  'star bottle': 'The star bottle twinkles from inside.',
  'cable bundle': 'The cable bundle curls back into place.',
  'mini robot': 'The mini robot blinks in place.',
  'to do list': 'The checklist looks freshly touched.',
  'thank you': 'The thank-you note feels warmer.',
  'photo note': 'The photo note leans toward the room.',
  'desk polaroid': 'The polaroid remembers lamplight.',
  'daily checklist': 'The daily mark gives one small tick.'
};

let miriIdleTimer = 0;
let actionTimer = 0;

function room() {
  return document.querySelector('[data-room]');
}

function bubble() {
  return document.querySelector('.miri-bubble');
}

function airPrompt() {
  return document.querySelector('[data-air-prompt-form]');
}

function liveLine() {
  return document.querySelector("[data-live='latest']");
}

function resultBox() {
  return document.querySelector("[data-live='result']");
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
  const photo = currentRoom.querySelector('.room-photo');
  if (photo) photo.src = phase === 'night' ? 'asset/room-night.jpg' : 'asset/room-light.jpg';
}

function chooseMiriIdleState() {
  const currentRoom = room();
  if (!currentRoom) return 'listening';
  if (currentRoom.classList.contains('is-speaking')) return 'listening';
  if (currentRoom.classList.contains('is-busy')) return 'typing';
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
  if (!currentRoom) return;
  currentRoom.dataset.hotspot = name;
  const attention = {
    miri: 'listening',
    door: 'looking',
    pinboard: 'reading',
    shelf: 'looking',
    daily: 'reading',
    body: 'thinking',
    floor: 'looking',
    craft: 'typing'
  };
  if (attention[name]) currentRoom.dataset.miriIdle = attention[name];
}

function setPointerGlow(event) {
  const stage = event.target.closest?.('.game-stage');
  const currentRoom = stage?.closest?.('[data-room]');
  if (!stage || !currentRoom) return;
  const bounds = stage.getBoundingClientRect();
  const x = ((event.clientX - bounds.left) / bounds.width) * 100;
  const y = ((event.clientY - bounds.top) / bounds.height) * 100;
  currentRoom.style.setProperty('--cursor-x', `${Math.max(0, Math.min(100, x)).toFixed(2)}%`);
  currentRoom.style.setProperty('--cursor-y', `${Math.max(0, Math.min(100, y)).toFixed(2)}%`);
  currentRoom.classList.add('is-pointer-active');
}

function clearPointerGlow(event) {
  const stage = event.target.closest?.('.game-stage');
  if (!stage) return;
  const nextStage = event.relatedTarget?.closest?.('.game-stage');
  if (nextStage === stage) return;
  stage.closest?.('[data-room]')?.classList.remove('is-pointer-active');
}

function setBubble(text, result = '') {
  const latest = liveLine();
  const resultTarget = resultBox();
  if (latest && text) latest.textContent = text;
  if (resultTarget) resultTarget.textContent = result;
  const stamp = document.querySelector("[data-live='stamp']");
  if (stamp) stamp.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
}

function pulseAction(name) {
  const currentRoom = room();
  if (!currentRoom) return;
  window.clearTimeout(actionTimer);
  currentRoom.classList.add('is-busy', `is-action-${name}`);
  currentRoom.dataset.miriIdle = name === 'knock' ? 'looking' : 'typing';
  setBubble(ACTION_LINES[name] || 'The room answers softly.');
  actionTimer = window.setTimeout(() => {
    currentRoom.classList.remove('is-busy', `is-action-${name}`);
    currentRoom.dataset.miriIdle = 'listening';
  }, 900);
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
    currentRoom.dataset.miriIdle = name === 'daily' ? 'reading' : 'looking';
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

function submitWhisper(form) {
  const input = form.querySelector('input');
  const text = input?.value.trim() || '';
  if (!text) {
    input?.blur();
    hideAirPrompt(0);
    return;
  }
  setBubble('Miri keeps your whisper close.', text);
  pulseAction('talk');
  form.reset();
  input?.blur();
  hideAirPrompt(700);
}

function pinLocalNote(form) {
  const input = form.querySelector('input');
  const text = input?.value.trim() || '';
  if (!text) return;
  const list = document.querySelector('[data-pin-list]');
  if (list) {
    if (list.children.length === 1 && list.textContent.includes('waiting')) list.textContent = '';
    const item = document.createElement('li');
    item.textContent = text;
    list.prepend(item);
  }
  form.reset();
  pulseAction('note');
}

function pokePiece(figure) {
  const label = figure.getAttribute('title') || figure.querySelector('img')?.alt || 'object';
  figure.classList.remove('is-poked');
  void figure.offsetWidth;
  figure.classList.add('is-poked');
  setBubble(PIECE_REACTIONS[label] || 'The object gives a tiny answer.');
}

document.addEventListener('submit', (event) => {
  const form = event.target;
  if (!form) return;
  if (form.matches('[data-air-prompt-form], [data-local-talk]')) {
    event.preventDefault();
    submitWhisper(form);
  }
  if (form.matches('[data-local-note]')) {
    event.preventDefault();
    pinLocalNote(form);
  }
});

document.addEventListener('click', (event) => {
  const panelTarget = event.target.closest('[data-panel-target]');
  if (panelTarget) {
    event.preventDefault();
    openRoomPanel(panelTarget.dataset.panelTarget);
    return;
  }
  const localAction = event.target.closest('[data-local-action]');
  if (localAction) {
    event.preventDefault();
    pulseAction(localAction.dataset.localAction || 'touch');
    return;
  }
  const piece = event.target.closest('.piece-map-item');
  if (piece) {
    event.preventDefault();
    pokePiece(piece);
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

document.addEventListener('pointermove', setPointerGlow);

document.addEventListener('pointerout', (event) => {
  const target = event.target.closest?.('[data-hotspot]');
  clearPointerGlow(event);
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

setRoomPhase();
scheduleMiriIdle();
window.setInterval(setRoomPhase, 60000);
