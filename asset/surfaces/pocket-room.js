const ROOM_PHASES = ['dawn', 'day', 'evening', 'night'];
const MIRI_IDLE_STATES = ['listening', 'looking', 'reading', 'typing'];
const RECENT_TOUCH_WINDOW = 5000;
const ACTION_LINES = {
  knock: [
    'The door answers with a short wooden tap.',
    'A tiny knock travels through the frame.',
    'The doorplate shivers, then settles.'
  ],
  find: [
    'Dust gathers on the rug. Something tiny wants to be found.',
    'A soft scrape under the desk fades back into quiet.',
    'The floor gives up one small hush of dust.'
  ],
  craft: [
    'The craft bench gives one warm spark.',
    'A careful fleck of light skips across the cable.',
    'The tools blink once, then pretend nothing happened.'
  ],
  daily: [
    'The marked day glows brighter.',
    'A check mark warms, then tucks itself back in.',
    'The day accepts one small tick of light.'
  ],
  body: [
    'The room body gives a slow teal pulse.',
    'A low teal breath moves under the desk light.',
    'Warm glass hums once under your hand.'
  ],
  note: [
    'A new scrap joins the pinboard.',
    'The fresh note presses itself flat.',
    'Paper takes the thought and holds still.'
  ],
  talk: [
    'Miri listens. The room keeps the whisper.',
    'The whisper lands softly near Miri.',
    'Miri holds the words for this visit.'
  ]
};
const PANEL_LINES = {
  pinboard: [
    'Pinned scraps lean closer.',
    'One paper corner lifts before going still.',
    'The pinboard waits with a paper-soft rustle.'
  ],
  shelf: [
    'The shelf waits for a tiny poke.',
    'A few small objects pretend they did not move.',
    'The shelf gives a careful wooden wobble.'
  ],
  daily: [
    'Today has one warm mark left.',
    'The checklist brightens at the edge.',
    'A small tick waits inside the paper.'
  ],
  body: [
    'The room body hums under the lamp.',
    'A teal pulse rolls through the room body.',
    'Warm glass answers from under the light.'
  ]
};
const MIRI_SPRITES = {
  calm: 'asset/calm.png',
  happy: 'asset/happy.png',
  sleep: 'asset/sleep.png',
  think: 'asset/think.png'
};
const PIECE_REACTIONS = {
  'coffee mug': [
    'The mug gives off a tiny warm breath.',
    'The mug remembers being held.',
    'A ring of warmth fades into the shelf.'
  ],
  'open notebook': [
    'The notebook waits on a half-written line.',
    'A page lifts, then forgets what it was going to say.',
    'The notebook keeps one sentence half-awake.'
  ],
  'tiny keyboard': [
    'The tiny keyboard clicks once.',
    'One key answers before the others wake up.',
    'A quiet plastic tap runs under your finger.'
  ],
  cassette: [
    'The cassette catches a purple glint.',
    'A stored song turns over in its sleep.',
    'The tape wheel thinks about moving, then stops.'
  ],
  'small screwdriver': [
    'The screwdriver rolls a careful quarter turn.',
    'The screwdriver points at nothing in particular.',
    'Metal gives a dry little tick against the shelf.'
  ],
  'star bottle': [
    'The star bottle twinkles from inside.',
    'One tiny star bumps the glass.',
    'The bottle keeps a fleck of night to itself.'
  ],
  'cable bundle': [
    'The cable bundle curls back into place.',
    'A loop of cable tightens, then relaxes.',
    'The cable remembers being untangled.'
  ],
  'mini robot': [
    'The mini robot blinks in place.',
    'The little robot warms one teal eye.',
    'A tiny servo hum disappears under the lamp.'
  ],
  'to do list': [
    'The checklist looks freshly touched.',
    'A task line straightens itself.',
    'The paper makes room for one more small plan.'
  ],
  'thank you': [
    'The thank-you note feels warmer.',
    'The note keeps its gratitude close to the pin.',
    'A soft crease relaxes across the thank-you.'
  ],
  'photo note': [
    'The photo note leans toward the room.',
    'The photo catches a warmer corner of light.',
    'The picture remembers the desk for a second.'
  ],
  'desk polaroid': [
    'The polaroid remembers lamplight.',
    'The desk in the photo glows at the edge.',
    'The polaroid gives back a square of quiet.'
  ],
  'daily checklist': [
    'The daily mark gives one small tick.',
    'A check mark brightens, then settles.',
    'The checklist keeps the day a little warmer.'
  ]
};
const MIRI_TOUCH_LINES = [
  'Miri tilts toward the whisper spot.',
  'Miri looks up like she heard the room breathe.',
  'Miri waits without breaking the quiet.'
];
const RAPID_TOUCH_LINES = [
  'Miri blinks twice, then forgives the tapping.',
  'Miri looks mildly interrupted, but stays close.',
  'Miri gives the room a tiny please-be-gentle look.'
];
const TOUCH_KEY_BY_ACTION = {
  knock: 'door',
  find: 'floor',
  craft: 'craft',
  daily: 'daily',
  body: 'body',
  note: 'pinboard',
  talk: 'talk'
};
const GAZE_BY_ACTION = {
  knock: 'door',
  find: 'floor',
  craft: 'craft',
  daily: 'daily',
  body: 'body',
  note: 'pinboard',
  talk: 'miri'
};
const COMBO_REACTIONS = [
  {
    from: 'door',
    to: 'miri',
    className: 'door-miri',
    gaze: 'door',
    idle: 'looking',
    mood: 'think',
    tone: 'think',
    line: 'Miri looks at the door first, then back at you.'
  },
  {
    from: 'daily',
    to: 'talk',
    className: 'daily-talk',
    gaze: 'daily',
    idle: 'reading',
    mood: 'calm',
    tone: 'system',
    line: 'The marked day makes the whisper land softer.'
  },
  {
    from: 'piece:open notebook',
    to: 'pinboard',
    className: 'notebook-pinboard',
    gaze: 'pinboard',
    idle: 'reading',
    mood: 'calm',
    tone: 'think',
    line: 'The notebook nudges the pinned paper into a quiet answer.'
  }
];
const SESSION_SEEDS = [
  {
    key: 'door',
    touch: 'door',
    className: 'seed-door',
    surface: 'knock',
    gaze: 'door',
    idle: 'looking',
    mood: 'think',
    tone: 'think',
    line: 'The door was listening for that.'
  },
  {
    key: 'daily',
    touch: 'talk',
    className: 'seed-daily',
    surface: 'daily',
    gaze: 'daily',
    idle: 'reading',
    mood: 'calm',
    tone: 'system',
    line: 'Today makes the whisper land softer.'
  },
  {
    key: 'body',
    touch: 'body',
    className: 'seed-body',
    surface: 'body',
    gaze: 'body',
    idle: 'thinking',
    mood: 'calm',
    tone: 'system',
    line: 'The teal pulse was waiting under the room.'
  },
  {
    key: 'pinboard',
    touch: 'pinboard',
    className: 'seed-pinboard',
    surface: 'pinboard',
    gaze: 'pinboard',
    idle: 'reading',
    mood: 'calm',
    tone: 'think',
    line: 'The pinned scraps answer in a small paper hush.'
  },
  {
    key: 'shelf',
    touch: 'shelf',
    className: 'seed-shelf',
    surface: 'shelf',
    gaze: 'shelf',
    idle: 'looking',
    mood: 'happy',
    tone: 'think',
    line: 'The restless shelf gives a second tiny wobble.'
  },
  {
    key: 'craft',
    touch: 'craft',
    className: 'seed-craft',
    surface: 'craft',
    gaze: 'craft',
    idle: 'typing',
    mood: 'happy',
    tone: 'system',
    line: 'One hidden spark catches before the tools go quiet.'
  }
];
const PIECE_MOTIONS = {
  'coffee mug': 'warm',
  'open notebook': 'page',
  'tiny keyboard': 'tap',
  cassette: 'glint',
  'small screwdriver': 'roll',
  'star bottle': 'sparkle',
  'cable bundle': 'curl',
  'mini robot': 'blink',
  'to do list': 'paper',
  'thank you': 'paper',
  'photo note': 'photo',
  'desk polaroid': 'photo',
  'daily checklist': 'tick'
};
const AMBIENT_SURPRISES = [
  {name: 'door', hotspot: 'door', idle: 'looking', duration: 1700},
  {name: 'pinboard', hotspot: 'pinboard', idle: 'reading', duration: 1900},
  {name: 'shelf', hotspot: 'shelf', idle: 'looking', duration: 1800},
  {name: 'daily', hotspot: 'daily', idle: 'reading', duration: 1600},
  {name: 'body', hotspot: 'body', idle: 'thinking', duration: 2200},
  {name: 'craft', hotspot: 'craft', idle: 'typing', duration: 1500}
];

let miriIdleTimer = 0;
let actionTimer = 0;
let surfaceTimer = 0;
let comboTimer = 0;
let gazeTimer = 0;
let recentTouch = null;
let recentTouchTimer = 0;
let rapidTouchTimer = 0;
let ambientSurpriseTimer = 0;
let touchHistory = [];
let knockHistory = [];
let bodyHoldTimer = 0;
let settleTimer = 0;
let sessionSeed = null;
let sessionSeedUsed = false;

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

function miriCharacter() {
  return document.querySelector('[data-miri-character]');
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

function sample(value) {
  if (!Array.isArray(value)) return value;
  return value[Math.floor(Math.random() * value.length)];
}

function clearActionClasses(currentRoom, prefix) {
  Array.from(currentRoom.classList)
    .filter((className) => className.startsWith(prefix))
    .forEach((className) => currentRoom.classList.remove(className));
}

function rememberTouch(key) {
  if (!key) return;
  recentTouch = {key, time: Date.now()};
  window.clearTimeout(recentTouchTimer);
  recentTouchTimer = window.setTimeout(() => {
    if (recentTouch?.key === key) recentTouch = null;
  }, RECENT_TOUCH_WINDOW);
}

function recentTouchKey() {
  if (!recentTouch || Date.now() - recentTouch.time > RECENT_TOUCH_WINDOW) return '';
  return recentTouch.key;
}

function clearRecentTouch() {
  recentTouch = null;
  window.clearTimeout(recentTouchTimer);
}

function chooseSessionSeed() {
  sessionSeed = sample(SESSION_SEEDS);
  sessionSeedUsed = false;
  const currentRoom = room();
  if (currentRoom && sessionSeed) currentRoom.dataset.sessionSeed = sessionSeed.key;
}

function noteTouchTempo() {
  const now = Date.now();
  touchHistory = touchHistory.filter((time) => now - time < 2600);
  touchHistory.push(now);
  if (touchHistory.length < 5) return false;
  touchHistory = [];
  return true;
}

function noteKnockTempo() {
  const now = Date.now();
  knockHistory = knockHistory.filter((time) => now - time < 1800);
  knockHistory.push(now);
  if (knockHistory.length < 3) return false;
  knockHistory = [];
  return true;
}

function setRoomSurface(name, duration = 1400) {
  const currentRoom = room();
  if (!currentRoom || !name) return;
  window.clearTimeout(surfaceTimer);
  clearActionClasses(currentRoom, 'is-surface-');
  currentRoom.classList.add(`is-surface-${name}`);
  surfaceTimer = window.setTimeout(() => {
    currentRoom.classList.remove(`is-surface-${name}`);
  }, duration);
}

function settleRoom(delay = 1500) {
  const currentRoom = room();
  if (!currentRoom) return;
  window.clearTimeout(settleTimer);
  settleTimer = window.setTimeout(() => {
    if (
      currentRoom.classList.contains('is-focused') ||
      currentRoom.classList.contains('is-speaking') ||
      currentRoom.classList.contains('is-busy') ||
      currentRoom.classList.contains('is-pointer-active')
    ) {
      return;
    }
    clearActionClasses(currentRoom, 'is-surface-');
    currentRoom.dataset.hotspot = '';
    currentRoom.dataset.miriGaze = '';
    setMiriIdleState('listening');
  }, delay);
}

function setMiriGaze(target = '', duration = 1600) {
  const currentRoom = room();
  if (!currentRoom) return;
  window.clearTimeout(gazeTimer);
  if (!target) {
    const previousTarget = currentRoom.dataset.miriGaze;
    gazeTimer = window.setTimeout(() => {
      if (currentRoom.dataset.miriGaze === previousTarget) currentRoom.dataset.miriGaze = '';
    }, duration);
    return;
  }
  currentRoom.dataset.miriGaze = target;
  gazeTimer = window.setTimeout(() => {
    if (currentRoom.dataset.miriGaze === target) currentRoom.dataset.miriGaze = '';
  }, duration);
}

function setPieceMotion(figure, label) {
  const motion = PIECE_MOTIONS[label] || 'poke';
  figure.dataset.motion = motion;
  figure.classList.remove('is-poked');
  void figure.offsetWidth;
  figure.classList.add('is-poked');
}

function comboFor(nextKey) {
  const previousKey = recentTouchKey();
  if (!previousKey || !nextKey || previousKey === nextKey) return null;
  return COMBO_REACTIONS.find((combo) => combo.from === previousKey && combo.to === nextKey);
}

function triggerCombo(combo, result = '') {
  const currentRoom = room();
  if (!currentRoom || !combo) return false;
  window.clearTimeout(comboTimer);
  clearActionClasses(currentRoom, 'is-combo-');
  currentRoom.classList.add('is-busy', `is-combo-${combo.className}`);
  setRoomSurface(combo.className, 1900);
  setMiriGaze(combo.gaze, 1900);
  setMiriIdleState(combo.idle || 'looking');
  setMiriMood(combo.mood || 'happy');
  setBubble(combo.line, result, combo.tone || 'neutral');
  clearRecentTouch();
  comboTimer = window.setTimeout(() => {
    currentRoom.classList.remove('is-busy', `is-combo-${combo.className}`);
    setMiriIdleState('listening');
    settleRoom(500);
  }, 1900);
  return true;
}

function maybeTriggerSeedEcho(touchKey, result = '') {
  const currentRoom = room();
  if (!currentRoom || !sessionSeed || sessionSeedUsed || touchKey !== sessionSeed.touch) return false;
  sessionSeedUsed = true;
  window.clearTimeout(comboTimer);
  clearActionClasses(currentRoom, 'is-combo-');
  currentRoom.classList.add('is-busy', `is-combo-${sessionSeed.className}`);
  setRoomSurface(sessionSeed.surface, 1900);
  setMiriGaze(sessionSeed.gaze, 1900);
  setMiriIdleState(sessionSeed.idle || 'looking');
  setMiriMood(sessionSeed.mood || 'happy');
  setBubble(sessionSeed.line, result, sessionSeed.tone || 'neutral');
  clearRecentTouch();
  comboTimer = window.setTimeout(() => {
    currentRoom.classList.remove('is-busy', `is-combo-${sessionSeed.className}`);
    setMiriIdleState('listening');
    settleRoom(500);
  }, 1900);
  return true;
}

function maybeReactToRapidTouch() {
  if (!noteTouchTempo()) return false;
  const currentRoom = room();
  if (!currentRoom) return false;
  window.clearTimeout(rapidTouchTimer);
  currentRoom.classList.add('is-rapid-touch');
  setMiriGaze('miri', 1500);
  setMiriIdleState('thinking');
  setMiriMood('think');
  setBubble(sample(RAPID_TOUCH_LINES), '', 'think');
  rapidTouchTimer = window.setTimeout(() => {
    currentRoom.classList.remove('is-rapid-touch');
    setMiriIdleState('listening');
  }, 1500);
  return true;
}

function triggerAmbientSurprise() {
  const currentRoom = room();
  if (!currentRoom) return;
  if (
    currentRoom.classList.contains('is-focused') ||
    currentRoom.classList.contains('is-busy') ||
    currentRoom.classList.contains('is-speaking') ||
    currentRoom.classList.contains('is-pointer-active')
  ) {
    return;
  }
  const surprise = sample(AMBIENT_SURPRISES);
  if (!surprise) return;
  clearActionClasses(currentRoom, 'is-ambient-');
  currentRoom.classList.add(`is-ambient-${surprise.name}`);
  currentRoom.dataset.hotspot = surprise.hotspot;
  currentRoom.dataset.miriGaze = surprise.hotspot;
  setMiriIdleState(surprise.idle);
  window.setTimeout(() => {
    currentRoom.classList.remove(`is-ambient-${surprise.name}`);
    if (currentRoom.dataset.hotspot === surprise.hotspot && !currentRoom.classList.contains('is-pointer-active')) {
      currentRoom.dataset.hotspot = '';
    }
    if (currentRoom.dataset.miriGaze === surprise.hotspot) currentRoom.dataset.miriGaze = '';
  }, surprise.duration);
}

function scheduleAmbientSurprise(delay = 20000 + Math.random() * 20000) {
  window.clearTimeout(ambientSurpriseTimer);
  ambientSurpriseTimer = window.setTimeout(() => {
    triggerAmbientSurprise();
    scheduleAmbientSurprise();
  }, delay);
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
  if (currentRoom.classList.contains('is-focused')) {
    const focusAttention = {
      pinboard: 'reading',
      shelf: 'looking',
      daily: 'reading',
      body: 'thinking',
      talk: 'listening'
    };
    return focusAttention[currentRoom.dataset.focus] || 'looking';
  }
  if (currentRoom.dataset.runtimePhase === 'night' && Math.random() < 0.35) return 'dozing';
  return MIRI_IDLE_STATES[Math.floor(Math.random() * MIRI_IDLE_STATES.length)];
}

function miriMoodForIdle(state) {
  if (state === 'dozing') return 'sleep';
  if (state === 'thinking' || state === 'typing') return 'think';
  if (state === 'reading') return 'calm';
  return 'happy';
}

function setMiriMood(mood = 'happy') {
  const currentRoom = room();
  const character = miriCharacter();
  const nextMood = MIRI_SPRITES[mood] ? mood : 'happy';
  if (currentRoom) currentRoom.dataset.miriState = nextMood;
  if (character && !character.src.endsWith(MIRI_SPRITES[nextMood])) {
    character.src = MIRI_SPRITES[nextMood];
  }
}

function setMiriIdleState(state = 'listening') {
  const currentRoom = room();
  if (!currentRoom) return;
  currentRoom.dataset.miriIdle = state;
  setMiriMood(miriMoodForIdle(state));
}

function scheduleMiriIdle(delay = 1200) {
  window.clearTimeout(miriIdleTimer);
  miriIdleTimer = window.setTimeout(() => {
    setMiriIdleState(chooseMiriIdleState());
    const currentRoom = room();
    const nightDelay = currentRoom?.dataset.runtimePhase === 'night';
    scheduleMiriIdle((nightDelay ? 9500 : 6500) + Math.random() * (nightDelay ? 12500 : 9000));
  }, delay);
}

function setHotspot(name = '') {
  const currentRoom = room();
  if (!currentRoom) return;
  currentRoom.dataset.hotspot = name;
  const lockGaze = currentRoom.classList.contains('is-busy') || currentRoom.classList.contains('is-lens-settling');
  if (!lockGaze) currentRoom.dataset.miriGaze = name;
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
  if (attention[name] && !lockGaze) setMiriIdleState(attention[name]);
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

function setBubble(text, result = '', tone = 'neutral') {
  const latest = liveLine();
  const resultTarget = resultBox();
  const bubbleTarget = bubble();
  if (latest && text) latest.textContent = text;
  if (resultTarget) resultTarget.textContent = result;
  if (bubbleTarget) bubbleTarget.dataset.bubbleTone = tone;
  const stamp = document.querySelector("[data-live='stamp']");
  if (stamp) stamp.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
}

function pulseAction(name, result = '') {
  const currentRoom = room();
  if (!currentRoom) return;
  const touchKey = TOUCH_KEY_BY_ACTION[name] || name;
  if (name === 'knock' && noteKnockTempo()) {
    const combo = COMBO_REACTIONS.find((item) => item.className === 'door-miri');
    if (triggerCombo(combo)) {
      rememberTouch(touchKey);
      return;
    }
  }
  const combo = comboFor(touchKey);
  if (combo && triggerCombo(combo, result)) return;
  if (maybeTriggerSeedEcho(touchKey, result)) return;
  if (maybeReactToRapidTouch()) {
    rememberTouch(touchKey);
    return;
  }
  const actionMood = {
    knock: 'think',
    find: 'think',
    craft: 'happy',
    daily: 'happy',
    body: 'calm',
    note: 'happy',
    talk: 'happy'
  };
  const actionTone = {
    knock: 'think',
    find: 'think',
    body: 'system',
    talk: 'system'
  };
  window.clearTimeout(actionTimer);
  clearActionClasses(currentRoom, 'is-action-');
  currentRoom.classList.add('is-busy', `is-action-${name}`);
  setRoomSurface(name);
  setMiriGaze(GAZE_BY_ACTION[name] || touchKey);
  setMiriIdleState(name === 'knock' ? 'looking' : 'typing');
  setMiriMood(actionMood[name] || 'happy');
  setBubble(sample(ACTION_LINES[name]) || 'The room answers softly.', result, actionTone[name] || 'neutral');
  rememberTouch(touchKey);
  actionTimer = window.setTimeout(() => {
    currentRoom.classList.remove('is-busy', `is-action-${name}`);
    setMiriIdleState('listening');
    settleRoom(500);
  }, 1300);
}

function startBodyHold() {
  const currentRoom = room();
  if (!currentRoom) return;
  window.clearTimeout(bodyHoldTimer);
  bodyHoldTimer = window.setTimeout(() => {
    currentRoom.classList.add('is-body-holding');
    currentRoom.dataset.hotspot = 'body';
    setRoomSurface('body-hold', 1800);
    setMiriGaze('body', 1800);
    setMiriIdleState('thinking');
    setBubble('The teal pulse deepens under your hand.', '', 'system');
  }, 360);
}

function endBodyHold() {
  const currentRoom = room();
  window.clearTimeout(bodyHoldTimer);
  if (!currentRoom?.classList.contains('is-body-holding')) return;
  currentRoom.classList.remove('is-body-holding');
  pulseAction('body');
}

function showAirPrompt(seed = '') {
  const form = airPrompt();
  if (!form) return;
  const previousTouch = recentTouchKey();
  const combo = comboFor('miri');
  const input = form.querySelector('input');
  const currentRoom = room();
  currentRoom?.classList.add('is-speaking');
  if (currentRoom) {
    currentRoom.dataset.hotspot = 'miri';
    setMiriIdleState('listening');
  }
  if (combo) {
    triggerCombo(combo);
  } else if (maybeTriggerSeedEcho('talk')) {
    // The echo owns the bubble line; the prompt still opens for the user.
  } else {
    if (!seed) setBubble(sample(MIRI_TOUCH_LINES), '', 'system');
    maybeReactToRapidTouch();
  }
  if (previousTouch !== 'daily') rememberTouch('miri');
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
  const combo = comboFor(name);
  let echoTriggered = false;
  if (combo && triggerCombo(combo)) {
    rememberTouch(name);
    echoTriggered = true;
  } else if (maybeTriggerSeedEcho(name)) {
    rememberTouch(name);
    echoTriggered = true;
  } else {
    rememberTouch(name);
    maybeReactToRapidTouch();
  }
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
    if (!echoTriggered) currentRoom.dataset.miriGaze = name;
    setRoomSurface(name, 1200);
    if (!echoTriggered) setMiriIdleState(name === 'daily' || name === 'pinboard' ? 'reading' : 'looking');
  }
  if (!echoTriggered) setBubble(sample(PANEL_LINES[name]) || 'The room leans closer.');
  drawer.hidden = false;
}

function closeRoomPanel() {
  const drawer = document.querySelector('[data-room-drawer]');
  const closingFocus = drawer?.dataset.panelName || '';
  if (drawer) {
    drawer.hidden = true;
    drawer.dataset.panelName = '';
    const title = drawer.querySelector('[data-panel-title]');
    if (title) title.textContent = 'Miri';
  }
  const currentRoom = room();
  if (currentRoom) {
    currentRoom.classList.remove('is-focused');
    currentRoom.dataset.focus = '';
    currentRoom.dataset.hotspot = '';
    currentRoom.classList.add('is-lens-settling');
    setRoomSurface(closingFocus || 'settle', 1000);
    setMiriGaze('', 1100);
    window.setTimeout(() => {
      currentRoom.classList.remove('is-lens-settling');
      if (!currentRoom.classList.contains('is-focused') && !currentRoom.classList.contains('is-busy')) {
        setMiriIdleState('listening');
        settleRoom(400);
      }
    }, 1100);
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
  pulseAction('talk', text);
  form.reset();
  input?.blur();
  hideAirPrompt(700);
}

function pinLocalNote(form) {
  const input = form.querySelector('input');
  const text = input?.value.trim() || '';
  if (!text) return;
  const note = document.querySelector('[data-pin-note]');
  if (note) note.textContent = text;
  form.reset();
  pulseAction('note');
}

function pokePiece(figure) {
  const label = figure.getAttribute('title') || figure.querySelector('img')?.alt || 'object';
  const touchKey = `piece:${label}`;
  const combo = comboFor(touchKey);
  setPieceMotion(figure, label);
  if (combo && triggerCombo(combo)) {
    rememberTouch(touchKey);
    return;
  }
  const areaTouch = label.includes('note') || label.includes('list') ? 'pinboard' : 'shelf';
  if (maybeTriggerSeedEcho(areaTouch)) {
    rememberTouch(touchKey);
    return;
  }
  if (maybeReactToRapidTouch()) {
    rememberTouch(touchKey);
    return;
  }
  setRoomSurface(PIECE_MOTIONS[label] || 'piece', 1200);
  setMiriGaze(areaTouch, 1300);
  setBubble(sample(PIECE_REACTIONS[label]) || 'The object gives a tiny answer.', '', 'think');
  setMiriIdleState(label === 'daily checklist' || label.includes('note') || label.includes('list') ? 'reading' : 'looking');
  rememberTouch(touchKey);
}

document.addEventListener('submit', (event) => {
  const form = event.target;
  if (!form) return;
  if (form.matches('[data-air-prompt-form]')) {
    event.preventDefault();
    submitWhisper(form);
  }
  if (form.matches('[data-local-note]')) {
    event.preventDefault();
    pinLocalNote(form);
  }
});

document.addEventListener('pointerdown', (event) => {
  const bodyTarget = event.target.closest?.(".zone-body, [data-local-action='body']");
  if (bodyTarget) startBodyHold();
});

document.addEventListener('pointerup', endBodyHold);
document.addEventListener('pointercancel', endBodyHold);

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

document.addEventListener('focusin', (event) => {
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
    if (event.key === 'Enter') {
      const form = target.closest?.('[data-air-prompt-form], [data-local-note]');
      if (form) {
        event.preventDefault();
        form.requestSubmit();
      }
      return;
    }
    if (event.key === 'Escape') {
      target.blur();
      if (target.closest?.('[data-room-drawer]')) closeRoomPanel();
      else hideAirPrompt(0);
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
  const target = event.target.closest?.('[data-hotspot]');
  if (target && !event.relatedTarget?.closest?.('[data-hotspot]')) setHotspot('');
});

document.addEventListener('focusout', (event) => {
  if (event.target.closest?.('[data-air-prompt-form]')) hideAirPrompt(1600);
});

setRoomPhase();
chooseSessionSeed();
setMiriMood('happy');
scheduleMiriIdle();
scheduleAmbientSurprise(12000 + Math.random() * 12000);
window.setInterval(setRoomPhase, 60000);
