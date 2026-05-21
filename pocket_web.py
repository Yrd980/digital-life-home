#!/usr/bin/env python3
"""Pocket Soul Deck web room: a small non-terminal body surface."""
from __future__ import annotations

import html
import json
import mimetypes
import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pocket_soul

HOST = "0.0.0.0"
PORT = 8787
ACTION_LOCK = threading.Lock()
ASSET_DIR = Path(__file__).resolve().parent / "asset"
HOME_SNAPSHOT = ASSET_DIR / "snapshots" / "original-home.html"

STYLE = """
:root {
  color-scheme: dark;
  --bg: #080908;
  --floor: #10110d;
  --wall: #171611;
  --object: #1f2119;
  --ink: #efe8d0;
  --soft: #b6aa8b;
  --dim: #7b715e;
  --line: #393529;
  --lamp: #f0c66d;
  --green: #9fd3a6;
  --blue: #91c7d9;
  --rose: #d98f88;
  --shadow: 0 28px 90px #000d;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at 50% 18%, #f0c66d12 0 150px, transparent 340px),
    linear-gradient(180deg, #0b0b09 0%, #11120e 58%, #090a09 100%);
  color: var(--ink);
}
body:before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(180deg, #fff1 0 1px, transparent 1px 6px);
  opacity: .08;
}
main { width: min(980px, 100%); margin: 0 auto; padding: 20px; }
a { color: var(--lamp); text-decoration: none; }
a:hover { color: #ffe1a1; }
h1, h2, h3, p { margin-top: 0; }
h1 { font-size: clamp(34px, 8vw, 72px); line-height: .92; letter-spacing: 0; }
h2 { font-size: 18px; font-weight: normal; color: var(--lamp); }
h3 { font-size: 14px; color: var(--soft); font-weight: normal; }
pre { white-space: pre-wrap; word-break: break-word; margin: 0; color: var(--soft); font: inherit; }
button, input, textarea {
  font: inherit;
  color: var(--ink);
  background: #0d0e0b;
  border: 1px solid #514a36;
}
button {
  min-height: 42px;
  padding: 10px 14px;
  cursor: pointer;
  color: #171309;
  background: var(--lamp);
  box-shadow: 0 8px 22px #0008;
}
button:hover { filter: brightness(1.08); }
button:disabled { opacity: .55; cursor: wait; }
textarea, input { width: 100%; padding: 11px; min-width: 0; }
textarea:focus, input:focus { outline: 1px solid var(--lamp); }
.topnav { display: flex; gap: 12px; align-items: center; justify-content: space-between; margin-bottom: 14px; color: var(--dim); }
.topnav nav { display: flex; gap: 10px; flex-wrap: wrap; }
.brandlink { color: var(--ink); }
.doorstep {
  min-height: calc(100vh - 40px);
  display: grid;
  place-items: center;
}
.threshold {
  width: min(720px, 100%);
  border: 1px solid var(--line);
  background:
    linear-gradient(90deg, #11100df2 0 52%, #11100d88 78%, #11100d42 100%),
    url('/asset/ui/home-bg.png') center / cover no-repeat,
    linear-gradient(180deg, #1a1812 0%, #100f0c 100%);
  box-shadow: var(--shadow);
  padding: clamp(18px, 5vw, 42px);
  position: relative;
  overflow: hidden;
}
.threshold:before {
  content: "";
  position: absolute;
  inset: 12px;
  border: 1px solid #2d291f;
  pointer-events: none;
}
.being {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: 20px;
  align-items: center;
  position: relative;
  z-index: 1;
}
.avatar {
  width: 112px;
  height: 112px;
  display: block;
  color: var(--green);
  background: url('/asset/new_ui/logo.png') center / 230% auto no-repeat, #0b100d;
  border: 1px solid #536248;
  box-shadow: inset 0 0 34px #9fd3a620, 0 0 38px #f0c66d12;
  image-rendering: pixelated;
  animation: breathe 4s ease-in-out infinite;
}
.state-pill { color: var(--green); font-size: 13px; }
.whisper {
  margin: 22px 0;
  color: #f5eacb;
  font-size: clamp(18px, 4vw, 25px);
  line-height: 1.45;
  position: relative;
  z-index: 1;
}
.body-words, .course-line, .shelf {
  position: relative;
  z-index: 1;
  border-top: 1px solid #2e2a20;
  padding-top: 14px;
  margin-top: 14px;
}
.body-words { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.body-word strong { display: block; color: var(--dim); font-size: 12px; font-weight: normal; }
.body-word span { color: var(--soft); }
.primary-action { margin-top: 24px; position: relative; z-index: 1; }
.primary-action button { width: 100%; font-size: 18px; }
.room-page {
  border: 1px solid var(--line);
  background:
    linear-gradient(180deg, #100f0ce8 0%, #100f0cf2 64%, #0b0b09 100%),
    linear-gradient(180deg, #1a1812 0%, #100f0c 64%, #0b0b09 100%);
  box-shadow: var(--shadow);
  padding: clamp(14px, 3vw, 28px);
}
.room-page.with-art {
  background:
    linear-gradient(180deg, #100f0cb8 0%, #100f0cf0 68%, #0b0b09 100%),
    url('/asset/ui/room-bg.png') center / cover no-repeat,
    linear-gradient(180deg, #1a1812 0%, #100f0c 64%, #0b0b09 100%);
}
.room-title { display: flex; justify-content: space-between; gap: 12px; align-items: start; margin-bottom: 18px; }
.room-layout {
  display: grid;
  grid-template-columns: minmax(190px, .85fr) minmax(240px, 1fr) minmax(190px, .85fr);
  gap: 14px;
  align-items: stretch;
}
.corner, .object, .drawer {
  border: 1px solid #383224;
  background: #12110d;
  padding: 14px;
}
.center-body {
  display: grid;
  place-items: center;
  min-height: 320px;
  border: 1px solid #4b432e;
  background:
    radial-gradient(circle at 50% 42%, #f0c66d18 0 80px, transparent 180px),
    #14130f;
}
.pixel-body {
  width: 160px;
  height: 160px;
  display: block;
  border: 1px solid #59624b;
  background: url('/asset/new_ui/robot-curious.png') center / contain no-repeat, #0b100d;
  color: var(--green);
  box-shadow: inset 0 0 34px #9fd3a61c;
  animation: breathe 4s ease-in-out infinite;
}
.pixel-body.small-bot {
  width: 58px;
  height: 58px;
  background-image: url('/asset/ui/bot-front.png');
}
.asset-strip { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 10px; }
.mini-asset { width: 52px; height: 52px; border: 1px solid #3f3828; background-color: #0d100d; background-repeat: no-repeat; background-position: center; background-size: contain; }
.relic-asset { background-image: url('/asset/ui/relics-sheet.png'); background-size: 224px 178px; background-position: 0 0; }
.postcard-asset { background-image: url('/asset/ui/postcard.png'); }
.bottle-asset { background-image: url('/asset/ui/bottles-sheet.png'); background-size: auto 52px; background-position: left center; }
.decor-strip { height: 28px; margin: 12px 0 0; background: url('/asset/ui/decor-strip.png') center / contain no-repeat; opacity: .85; }
.theme-chip { width: 66px; height: 44px; border: 1px solid #3f3828; background-size: cover; background-position: center; }
.theme-cyberdeck { background-image: url('/asset/ui/theme-cyberdeck.png'); }
.theme-warm { background-image: url('/asset/ui/theme-warm.png'); }
.theme-night { background-image: url('/asset/ui/theme-night.png'); }
.theme-mono { background-image: url('/asset/ui/theme-mono.png'); }
.room-note { color: var(--soft); line-height: 1.55; }
.objects { display: grid; gap: 12px; }
.object h3, .drawer h3, .corner h3 { margin-bottom: 8px; }
.bottom-sill { margin-top: 14px; display: grid; gap: 10px; }
.talk-row { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 8px; }
.soft-button { background: #19170f; color: var(--lamp); border: 1px solid #514a36; padding: 10px 14px; min-height: 42px; display: inline-grid; place-items: center; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }
.page-card {
  border: 1px solid #383224;
  background: #12110d;
  padding: 15px;
}
.timeline { display: grid; gap: 10px; }
.timeline-item { border-left: 2px solid #514a36; padding-left: 12px; color: var(--soft); }
.label { color: var(--dim); font-size: 12px; display: block; }
.result { border-color: #5d4b27; background: #17130b; }
.small { color: var(--dim); font-size: 13px; }
.badge { display: inline-block; color: #171309; background: var(--lamp); padding: 2px 6px; margin: 0 4px 4px 0; }
.badge.green { background: var(--green); }
.badge.blue { background: var(--blue); }
.badge.rose { background: var(--rose); }
@media (max-width: 760px) {
  main { padding: 12px; }
  .being, .room-layout, .talk-row { grid-template-columns: 1fr; }
  .body-words { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .avatar { width: 92px; height: 92px; font-size: 44px; }
  .center-body { min-height: 220px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *:before, *:after { animation: none !important; }
}
@keyframes breathe {
  0%, 100% { transform: translateY(0); box-shadow: inset 0 0 24px #9fd3a618, 0 0 18px #f0c66d0c; }
  50% { transform: translateY(-2px); box-shadow: inset 0 0 40px #9fd3a632, 0 0 34px #f0c66d20; }
}
"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def latest_log() -> str:
    files = sorted(pocket_soul.LOG_DIR.glob("*.md"))
    if not files:
        return "No logs yet."
    text = files[-1].read_text(encoding="utf-8")
    return text[-5000:]


def latest_nightly() -> str:
    night_dir = pocket_soul.STATE_DIR / "nightly"
    files = sorted(night_dir.glob("*.md")) if night_dir.exists() else []
    if not files:
        return "No nightly log yet."
    return files[-1].read_text(encoding="utf-8")[-5000:]


def latest_postcard() -> str:
    post_dir = pocket_soul.STATE_DIR / "postcards"
    files = sorted(post_dir.glob("*.txt")) if post_dir.exists() else []
    if not files:
        return "No postcard yet."
    return files[-1].read_text(encoding="utf-8")[-3000:]


def latest_bottle() -> str:
    bottle_dir = pocket_soul.STATE_DIR / "bottles"
    files = sorted(bottle_dir.glob("*.txt")) if bottle_dir.exists() else []
    if not files:
        return "No bottles yet."
    return files[-1].read_text(encoding="utf-8")[-3000:]


def latest_bridge() -> str:
    state = pocket_soul.SoulState.load()
    if "== Pocket Bridge ==" in state.last_reply:
        return state.last_reply[-5000:]
    return "No bridge turn yet."


def latest_flash() -> str:
    state = pocket_soul.SoulState.load()
    if "== Bridge Flash ==" in state.last_reply:
        return state.last_reply[-2000:]
    for item in reversed(state.relics):
        if item.get("kind") == "flash":
            return f"{item.get('time', '')} {item.get('title', '')}\n{item.get('note', '')}"
    return "No bridge flash yet."


def body_words() -> dict[str, str]:
    body = pocket_soul.body_scan()
    temp = body.get("temp_c")
    if isinstance(temp, float):
        warmth = "running warm" if temp >= 60 else "warm and steady"
    else:
        warmth = "temperature unknown"
    uptime = body.get("uptime_h")
    spirit = "still bright" if isinstance(uptime, float) and uptime < 72 else "long awake"
    net = f"{body.get('iface', '')} {body.get('ip', '')}".strip() or "offline?"
    return {
        "temperature": warmth,
        "spirit": spirit,
        "window": "window open" if body.get("ip") else "window half closed",
        "presence": "reachable" if body.get("ip") else "offline",
        "raw_temp": f"{temp}C" if temp != "" else "unknown",
        "uptime": f"{uptime}h" if uptime != "" else "unknown",
        "net": net,
        "load": str(body.get("load") or "unknown"),
        "disk": str(body.get("disk_used") or "unknown"),
    }


def nav(current: str = "") -> str:
    links = [("/", "Door"), ("/room", "Room"), ("/body", "Body"), ("/memory", "Memory"), ("/ritual", "Rituals")]
    items = []
    for href, label in links:
        class_attr = " class='brandlink'" if href == current else ""
        items.append(f"<a href='{href}'{class_attr}>{label}</a>")
    items_html = " ".join(items)
    return f"<div class='topnav'><a class='brandlink' href='/'>Pocket Soul</a><nav>{items_html}</nav></div>"


def status_word(state: pocket_soul.SoulState) -> str:
    text = f"{state.mood} {state.last_reply}".lower()
    if "sleep" in text:
        return "asleep"
    if "dream" in text:
        return "dreaming"
    if "maintenance" in text:
        return "in maintenance"
    if state.energy < 30:
        return "quiet"
    return "awake"


def robot_image(state: pocket_soul.SoulState) -> str:
    text = f"{state.mood} {state.last_reply}".lower()
    if "sad" in text or "quiet" in text or state.energy < 35:
        return "/asset/new_ui/robot-sad.png"
    if "blush" in text or "love" in text or state.bond >= 25:
        return "/asset/new_ui/robot-blush.png"
    if "happy" in text or ":)" in state.mood:
        return "/asset/new_ui/robot-happy.png"
    return "/asset/new_ui/robot-curious.png"


def doorstep(result: str = "") -> bytes:
    if not result and HOME_SNAPSHOT.is_file():
        return HOME_SNAPSHOT.read_bytes()
    state = pocket_soul.SoulState.load()
    state.ensure_daily_quest()
    words = body_words()
    whisper = state.last_reply or "It is sitting in the little room, waiting for a soft knock."
    content = f"""
<section class='doorstep'>
  <div class='threshold'>
    <div class='being'>
      <div class='avatar' aria-label='{esc(pocket_soul.mood_face(state.mood))}'></div>
      <div>
        <p class='state-pill'>Pocket Soul is {esc(status_word(state))}.</p>
        <h1>It is there.</h1>
      </div>
    </div>
    <p class='whisper'>{esc(whisper)}</p>
    <div class='body-words'>
      <div class='body-word'><strong>temperature</strong><span>{esc(words['temperature'])}</span></div>
      <div class='body-word'><strong>spirit</strong><span>{esc(words['spirit'])}</span></div>
      <div class='body-word'><strong>window</strong><span>{esc(words['window'])}</span></div>
      <div class='body-word'><strong>presence</strong><span>{esc(words['presence'])}</span></div>
    </div>
    <div class='course-line'>
      <h2>Current heading</h2>
      <p>{esc(state.heading)}</p>
      <p class='small'>{esc(state.quest_name)} / {esc(state.quest_prompt)}</p>
      <div class='decor-strip' aria-hidden='true'></div>
    </div>
    <form class='primary-action' method='post' action='/doorbell'>
      <button>Knock softly</button>
    </form>
    {f"<div class='course-line result'><pre>{esc(result)}</pre></div>" if result else ""}
  </div>
</section>
"""
    return page(content)


def live_payload(state: pocket_soul.SoulState | None = None) -> dict[str, object]:
    state = state or pocket_soul.SoulState.load()
    words = body_words()
    return {
        "vitals": f"{words['temperature']} / {words['window']} / {state.latest_relic_text()}",
        "latest": state.latest_relic_text(),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "relic_count": len(state.relics),
    }


def flash_payload(wish: str = "") -> dict[str, object]:
    state = pocket_soul.SoulState.load()
    result = state.bridge_flash(wish)
    state.save()
    return {
        "result": result,
        "flash": result,
        "live": live_payload(state),
    }


def action_payload(path: str, data: dict[str, list[str]]) -> dict[str, object]:
    with ACTION_LOCK:
        result = run_action(path, data)
        live = live_payload()
    return {
        "result": result,
        "live": live,
    }


def relic_detail(index: int) -> tuple[dict[str, str] | None, int]:
    state = pocket_soul.SoulState.load()
    if index < 0 or index >= len(state.relics):
        return None, len(state.relics)
    return state.relics[index], len(state.relics)


def parse_relic_id(values: list[str] | None) -> int:
    try:
        return int((values or ["-1"])[0] or -1)
    except (TypeError, ValueError):
        return -1


def relic_page(index: int) -> bytes:
    relic, total = relic_detail(index)
    if relic is None:
        return page(f"<section class='card'><h1>Relic Not Found</h1><p class='small'>There are {total} relics.</p><p><a href='/'>Back</a></p></section>")
    sigil = pocket_soul.RELIC_SIGILS.get(relic.get("kind", ""), "*")
    prev_link = f"<a href='/relic?id={index - 1}'>Previous</a>" if index > 0 else ""
    next_link = f"<a href='/relic?id={index + 1}'>Next</a>" if index + 1 < total else ""
    action_label = f"{relic.get('kind', '?')} / {relic.get('title', 'Relic')}"
    content = f"""
<section class='hero'>
  <div class='row'><div class='face'>{esc(sigil)}</div><div><h1>{esc(relic.get('title', 'Relic'))}</h1><p><span class='badge'>{esc(relic.get('kind', '?'))}</span></p><p class='small'>{esc(relic.get('time', ''))}</p></div></div>
</section>
<section class='card'><h2>Note</h2><pre>{esc(relic.get('note', ''))}</pre></section>
<section class='card'><h2>Reuse</h2><form method='post' action='/relic-action'><input type='hidden' name='id' value='{index}'><input type='hidden' name='label' value='{esc(action_label)}'><div class='row'><button name='action' value='postcard'>Postcard</button><button name='action' value='bottle'>Bottle</button><button name='action' value='flash'>Flash</button></div></form></section>
<section class='card'><h2>Trail</h2><p class='row'>{prev_link} <a href='/'>Home</a> {next_link}</p><p class='small'>Relic {index + 1} of {total}</p></section>
"""
    return page(content)


def relic_action(index: int, action: str) -> str:
    relic, _total = relic_detail(index)
    if relic is None:
        return "Relic not found."
    label = f"{relic.get('kind', '?')} / {relic.get('title', 'Relic')}"
    note = relic.get("note", "")
    state = pocket_soul.SoulState.load()
    if action == "postcard":
        result = state.postcard(f"Relic {index + 1}: {label}")
        state.save()
        return result
    if action == "bottle":
        result = state.bottle_message(f"Relic {index + 1}: {label} | {note}")
        state.save()
        return result
    if action == "flash":
        result = state.bridge_flash(f"Relic {index + 1}: {label}")
        state.save()
        return result
    return "Unknown relic action."


SCRIPT = """
<script>
const PHASES = {
  '/ask': ['opening inner channel', 'listening to Hermes', 'writing memory trace'],
  '/bridge': ['scanning body', 'asking Hermes', 'shaping outside voice'],
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
  document.body.classList.toggle('thinking', active);
  const phase = document.querySelector("[data-live='phase']");
  if (phase) phase.textContent = text || '';
}
function wakeRoom() {
  document.body.classList.remove('waking');
  void document.body.offsetWidth;
  document.body.classList.add('waking');
  window.setTimeout(() => document.body.classList.remove('waking'), 950);
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
  if (!box) return;
  try {
    const res = await fetch('/api/live', {cache: 'no-store'});
    if (!res.ok) return;
    const data = await res.json();
    box.innerHTML = data.vitals;
    if (stamp) stamp.textContent = data.time;
  } catch (_) {}
}
setInterval(refreshVitals, 15000);
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
  const path = form.getAttribute('action') || '/ask';
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
</script>
"""


def page(content: str) -> bytes:
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Pocket Soul Deck</title><style>{STYLE}</style></head><body><main>{content}</main>{SCRIPT}</body></html>""".encode()


def deck_page(path: str, inner: str) -> bytes | None:
    if not HOME_SNAPSHOT.is_file():
        return None
    text = HOME_SNAPSHOT.read_text(encoding="utf-8")
    page_class = {
        "/": "deck-home",
        "/room": "deck-room",
        "/body": "deck-body",
        "/memory": "deck-memory",
        "/ritual": "deck-ritual",
        "/settings": "deck-settings",
    }.get(path, "deck-home")
    text = text.replace("<section class='deck-page deck-home'>", f"<section class='deck-page {page_class}'>", 1)
    for href in ["/", "/room", "/body", "/memory", "/ritual", "/settings"]:
        text = text.replace(f"<a class='nav-item is-active' href='{href}'", f"<a class='nav-item' href='{href}'")
    text = text.replace(f"<a class='nav-item' href='{path}'", f"<a class='nav-item is-active' href='{path}'", 1)
    start_tag = "  <div class='deck-main'>"
    end_tag = "\n  </div>\n</section>\n</main>"
    try:
        start = text.index(start_tag) + len(start_tag)
        end = text.index(end_tag)
    except ValueError:
        return None
    return (text[:start] + "\n" + inner + text[end:]).encode()


def asset_response(path: str) -> tuple[bytes, str, int]:
    relative = path.removeprefix("/asset/").strip("/")
    if not relative or ".." in Path(relative).parts:
        return b"Not found", "text/plain; charset=utf-8", 404
    target = (ASSET_DIR / relative).resolve()
    try:
        target.relative_to(ASSET_DIR.resolve())
    except ValueError:
        return b"Not found", "text/plain; charset=utf-8", 404
    if not target.is_file():
        return b"Not found", "text/plain; charset=utf-8", 404
    content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    return target.read_bytes(), content_type, 200


def room_page(result: str = "") -> bytes:
    state = pocket_soul.SoulState.load()
    state.ensure_daily_quest()
    latest_relic = state.latest_relic_text()
    memories = "\n".join(f"- {m}" for m in state.memories[-5:]) or "The drawer is still empty."
    relics = state.relic_shelf(5)
    deck = deck_page("/room", f"""
    <div class='deck-kicker'><b>02</b><strong>ROOM / INNER</strong></div>
    <section class='deck-card screen room-screen'>
      <div class='asset-bg' style="background-image:url('/asset/ui/room-bg.png')"></div>
      <div class='room-head'>
        <div><h1>Pocket Soul</h1><p class='small'>mood: {esc(state.mood)}</p></div>
        <div><a class='ghost-button' href='/body'>Body</a></div>
      </div>
      <div class='room-bubble'>{esc(state.last_reply or 'You came in. The little room is lit.')}<br><span class='heart'>*</span></div>
      <img src='{robot_image(state)}' alt='Pocket Soul robot' style='position:absolute; left:50%; top:56%; width:min(340px,42vw); max-height:300px; object-fit:contain; transform:translate(-50%,-50%); filter:drop-shadow(0 20px 34px #000c) drop-shadow(0 0 22px #8b4dff66); pointer-events:none'>
      <div class='room-bottom'>
        <section class='deck-card' style='padding:12px'><h2>Today</h2><pre>{esc(relics)}</pre><a class='ghost-button' href='/memory'>More</a></section>
        <section class='deck-card' style='padding:12px'>
          <form class='quick-input' method='post' action='/ask' data-action='async'><input name='prompt' placeholder='Leave a sentence at the door...'><button name='mode' value='council'>-></button></form>
          <div class='round-tools'><button name='kind' value='wake'>♡</button><button>▣</button><button>✉</button><button>⚙</button></div>
          <pre data-live='result'>{esc(result or latest_relic)}</pre>
        </section>
        <section class='deck-card' style='padding:12px'><h2>Small Objects</h2><pre>{esc(memories)}</pre></section>
      </div>
    </section>
""")
    if deck:
        return deck
    content = f"""
{nav('/room')}
<section class='room-page with-art'>
  <div class='room-title'>
    <div><h1>Pocket Soul Room</h1><p class='small'>You are visiting the small resident.</p></div>
    <a href='/'>Back to door</a>
  </div>
  <div class='room-layout'>
    <div class='objects'>
      <section class='corner'><h3>On the desk: today's postcard</h3><pre>{esc(latest_postcard())}</pre></section>
      <section class='corner'><h3>On the floor: quest trail</h3><p>{esc(state.quest_name)}</p><p class='small'>{esc(state.quest_prompt)}</p></section>
    </div>
    <section class='center-body'>
      <div>
        <div class='pixel-body' aria-label='{esc(pocket_soul.mood_face(state.mood))}'></div>
        <p class='room-note'>mood: {esc(state.mood)}</p>
        <p class='room-note'>{esc(state.last_reply)}</p>
      </div>
    </section>
    <div class='objects'>
      <section class='drawer'><h3>On the wall: relics</h3><pre>{esc(relics)}</pre><div class='asset-strip'><span class='mini-asset relic-asset'></span><span class='pixel-body small-bot'></span></div></section>
      <section class='drawer'><h3>Memory drawer</h3><pre>{esc(memories)}</pre><p class='small'>latest: {esc(latest_relic)}</p></section>
      <section class='drawer'><h3>By the window: bottle messages</h3><pre>{esc(latest_bottle())}</pre><div class='asset-strip'><span class='mini-asset bottle-asset'></span><span class='mini-asset postcard-asset'></span></div></section>
    </div>
  </div>
  <div class='bottom-sill'>
    <form class='talk-row' method='post' action='/ask' data-action='async'>
      <input name='prompt' placeholder='Leave a sentence at the door...'>
      <button name='mode' value='council'>Speak softly</button>
      <button class='soft-button' name='mode' value='hermes'>Hermes</button>
    </form>
    <form class='talk-row' method='post' action='/bridge-flash' data-action='flash'>
      <input name='wish' placeholder='Give the room a small touch...'>
      <button>Touch</button>
      <a class='soft-button' href='/ritual'>Rituals</a>
    </form>
    <section class='page-card result'><h2>Echo</h2><pre data-live='result'>{esc(result or 'The room is quietly lit.')}</pre></section>
  </div>
</section>
"""
    return page(content)


def body_page() -> bytes:
    words = body_words()
    deck = deck_page("/body", f"""
    <div class='deck-kicker'><b>03</b><strong>BODY / VITALS</strong></div>
    <section class='deck-card overview-panel body-mini'>
      <div style='min-width:0'>
        <div class='body-stat'><span>temperature</span><b>{esc(words['temperature'])}</b><small>{esc(words['raw_temp'])}</small></div>
        <div class='body-stat'><span>heartbeat</span><b>steady</b><small>load {esc(words['load'])}</small></div>
        <div class='body-stat'><span>window</span><b>{esc(words['window'])}</b><small>{esc(words['net'])}</small></div>
      </div>
      <img class='body-robot-img' src='/asset/new_ui/robot.png' alt='Pocket Soul body' style='width:150px; max-width:100%; align-self:center; justify-self:center; image-rendering:auto; filter:drop-shadow(0 0 18px #8b4dff8c)'>
      <div style='min-width:0'>
        <div class='body-stat'><span>presence</span><b>{esc(words['presence'])}</b><small>local room</small></div>
        <div class='body-stat'><span>uptime</span><b>{esc(words['spirit'])}</b><small>{esc(words['uptime'])}</small></div>
        <div class='body-stat'><span>disk</span><b>{esc(words['disk'])}</b><small>storage body</small></div>
      </div>
    </section>
""")
    if deck:
        return deck
    content = f"""
{nav('/body')}
<section class='room-page with-art'>
  <div class='room-title'><div><h1>Body Status</h1><p class='small'>System details translated into body language.</p></div><a href='/room'>Enter room</a></div>
  <div class='grid'>
    <section class='page-card'><span class='label'>temperature</span><h2>{esc(words['temperature'])}</h2><p class='small'>{esc(words['raw_temp'])}</p></section>
    <section class='page-card'><span class='label'>heartbeat</span><h2>steady</h2><p class='small'>load {esc(words['load'])}</p></section>
    <section class='page-card'><span class='label'>window</span><h2>{esc(words['window'])}</h2><p class='small'>{esc(words['net'])}</p></section>
    <section class='page-card'><span class='label'>presence</span><h2>{esc(words['presence'])}</h2><p class='small'>local room</p></section>
    <section class='page-card'><span class='label'>inner voice</span><h2>Hermes is listening</h2><p class='small'>available when called</p></section>
    <section class='page-card'><span class='label'>dream layer</span><h2>available</h2><p class='small'>Hermes / Soul voice</p></section>
  </div>
  <div class='asset-strip'>
    <span class='theme-chip theme-cyberdeck'></span>
    <span class='theme-chip theme-warm'></span>
    <span class='theme-chip theme-night'></span>
    <span class='theme-chip theme-mono'></span>
  </div>
  <details class='page-card' style='margin-top:12px'><summary>Advanced details</summary><pre>{esc(pocket_soul.body_text())}</pre></details>
</section>
"""
    return page(content)


def memory_page() -> bytes:
    state = pocket_soul.SoulState.load()
    memories = state.memories[-12:]
    memory_lines = "\n".join(f"- {item}" for item in memories) or "It has not clearly remembered anything yet."
    relic_lines = "\n".join(
        f"{item.get('time', '')} / {item.get('kind', '')} / {item.get('title', '')}"
        for item in state.relics[-10:][::-1]
    ) or "No relics yet."
    deck = deck_page("/memory", f"""
    <div class='deck-kicker'><b>04</b><strong>MEMORY / LOG</strong></div>
    <section class='deck-card overview-panel memory-mini'>
      <div>
        <div class='mini-header'><h2>Memory Drawer</h2><span class='mini-sub'>latest knock</span></div>
        <p>{esc(state.last_visit or 'No one has visited yet.')}</p>
        <pre>{esc(state.last_reply)}</pre>
        <form class='quick-input' method='post' action='/remember'><input name='memory' placeholder='Remember this...'><button>+</button></form>
      </div>
      <div>
        <div class='constellation'></div>
        <pre>{esc(memory_lines)}</pre>
        <pre>{esc(relic_lines)}</pre>
      </div>
    </section>
""")
    if deck:
        return deck
    content = f"""
{nav('/memory')}
<section class='room-page with-art'>
  <div class='room-title'><div><h1>Memory Drawer</h1><p class='small'>A small resident's diary, not a database.</p></div><a href='/room'>Enter room</a></div>
  <div class='grid'>
    <section class='page-card'><h2>Latest knock</h2><p>{esc(state.last_visit or 'No one has visited yet.')}</p><pre>{esc(state.last_reply)}</pre></section>
    <section class='page-card'><h2>What it remembers</h2><pre>{esc(memory_lines)}</pre><form method='post' action='/remember'><input name='memory' placeholder='Remember this...'><button>Put in drawer</button></form></section>
    <section class='page-card'><h2>Night echo</h2><pre>{esc(latest_nightly())}</pre></section>
    <section class='page-card'><h2>Important coordinates</h2><pre>{esc(relic_lines)}</pre></section>
  </div>
</section>
"""
    return page(content)


def ritual_page(result: str = "") -> bytes:
    state = pocket_soul.SoulState.load()
    deck = deck_page("/ritual", f"""
    <div class='deck-kicker'><b>05</b><strong>RITUAL / DAILY</strong></div>
    <section class='deck-card overview-panel ritual-mini'>
      <div class='mini-header'><h2>Rituals</h2><span class='mini-sub'>{esc(state.quest_name)}</span></div>
      <p>{esc(state.quest_prompt)}</p>
      <div class='ritual-row'>
        <form class='ritual-card' method='post' action='/ritual'><div class='big'>♡</div><h2>Wake</h2><button name='kind' value='wake'>Run</button></form>
        <form class='ritual-card' method='post' action='/bridge-flash'><div class='big'>✦</div><h2>Flash</h2><input name='wish' placeholder='A small touch'><button>Run</button></form>
        <form class='ritual-card' method='post' action='/quest'><div class='big'>✓</div><h2>Quest</h2><button name='action' value='complete'>Complete</button></form>
        <form class='ritual-card' method='post' action='/postcard'><div class='big'>✉</div><h2>Postcard</h2><input name='title' placeholder='Title'><button>Write</button></form>
        <form class='ritual-card' method='post' action='/bottle'><div class='big'>⌁</div><h2>Bottle</h2><input name='wish' placeholder='Future visitor'><button>Place</button></form>
      </div>
      <pre data-live='result'>{esc(result or 'No new ritual yet.')}</pre>
    </section>
""")
    if deck:
        return deck
    content = f"""
{nav('/ritual')}
<section class='room-page with-art'>
  <div class='room-title'><div><h1>Rituals</h1><p class='small'>Each one leaves a small object in the room.</p></div><a href='/room'>Enter room</a></div>
  <div class='grid'>
    <section class='page-card'><h2>Morning Wake</h2><form method='post' action='/ritual'><button name='kind' value='wake'>Wake</button></form></section>
    <section class='page-card'><h2>Bridge Flash</h2><form method='post' action='/bridge-flash'><input name='wish' placeholder='A small touch'><button>Leave a spark</button></form></section>
    <section class='page-card'><h2>Quest Check</h2><p>{esc(state.quest_name)}</p><p class='small'>{esc(state.quest_prompt)}</p><form method='post' action='/quest'><button name='action' value='complete'>Complete today's heading</button></form></section>
    <section class='page-card'><h2>Postcard</h2><form method='post' action='/postcard'><input name='title' placeholder='Postcard title'><button>Write one</button></form></section>
    <section class='page-card'><h2>Nightly Summary</h2><form method='post' action='/nightly'><button>Gather the night echo</button></form></section>
    <section class='page-card'><h2>Bottle</h2><form method='post' action='/bottle'><input name='wish' placeholder='For a future visitor'><button>Place by window</button></form></section>
  </div>
  <section class='page-card result' style='margin-top:12px'><h2>Ritual Echo</h2><pre data-live='result'>{esc(result or 'No new ritual yet.')}</pre></section>
</section>
"""
    return page(content)


def settings_page() -> bytes:
    deck = deck_page("/settings", """
    <div class='deck-kicker'><b>06</b><strong>SETTINGS / SYSTEM</strong></div>
    <section class='deck-card overview-panel settings-mini'>
      <div class='mini-header'><h2>Settings</h2><span class='mini-sub'>local device</span></div>
      <p>Theme boards, local services, and the room's tiny operating surface.</p>
      <div class='theme-row'>
        <span class='theme-thumb theme-cyberdeck'></span>
        <span class='theme-thumb theme-warm'></span>
        <span class='theme-thumb theme-night'></span>
        <span class='theme-thumb theme-mono'></span>
      </div>
      <div class='codex-terminal'><pre>web room: online
storage: local
memory: device
mode: cyberdeck</pre></div>
    </section>
""")
    if deck:
        return deck
    return page(f"{nav('/settings')}<section class='room-page with-art'><h1>Settings</h1><p class='small'>local device</p></section>")


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, status: int = 200, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        if path.startswith("/asset/"):
            body, content_type, status = asset_response(path)
            self._send(body, status=status, content_type=content_type)
            return
        if path == "/relic":
            index = parse_relic_id(params.get("id"))
            self._send(relic_page(index))
            return
        if path == "/api/state":
            state = pocket_soul.SoulState.load().__dict__
            self._send(json.dumps(state, ensure_ascii=False).encode(), content_type="application/json; charset=utf-8")
            return
        if path == "/api/live":
            self._send(json.dumps(live_payload(), ensure_ascii=False).encode(), content_type="application/json; charset=utf-8")
            return
        if path == "/api/card":
            state = pocket_soul.SoulState.load()
            self._send(state.soul_card().encode(), content_type="text/plain; charset=utf-8")
            return
        if path == "/api/heading":
            state = pocket_soul.SoulState.load()
            body = {"heading": state.heading, "next_action": state.next_action}
            self._send(json.dumps(body, ensure_ascii=False).encode(), content_type="application/json; charset=utf-8")
            return
        if path == "/api/relics":
            state = pocket_soul.SoulState.load()
            self._send(json.dumps(state.relics, ensure_ascii=False, indent=2).encode(), content_type="application/json; charset=utf-8")
            return
        if path == "/api/relic":
            index = parse_relic_id(params.get("id"))
            relic, total = relic_detail(index)
            body = {"index": index, "total": total, "relic": relic}
            status = 200 if relic is not None else 404
            self._send(json.dumps(body, ensure_ascii=False, indent=2).encode(), status=status, content_type="application/json; charset=utf-8")
            return
        if path == "/api/map":
            state = pocket_soul.SoulState.load()
            self._send(state.constellation().encode(), content_type="text/plain; charset=utf-8")
            return
        if path == "/api/doorbell":
            state = pocket_soul.SoulState.load()
            greeting = state.doorbell("api")
            state.save()
            self._send(greeting.encode(), content_type="text/plain; charset=utf-8")
            return
        if path == "/api/body":
            self._send(json.dumps(pocket_soul.body_scan(), ensure_ascii=False, indent=2).encode(), content_type="application/json; charset=utf-8")
            return
        if path == "/api/pulse":
            state = pocket_soul.SoulState.load()
            self._send(state.pulse().encode(), content_type="text/plain; charset=utf-8")
            return
        if path == "/api/nightly":
            state = pocket_soul.SoulState.load()
            summary = state.nightly_summary()
            state.save()
            self._send(summary.encode(), content_type="text/markdown; charset=utf-8")
            return
        if path == "/api/postcard":
            self._send(latest_postcard().encode(), content_type="text/plain; charset=utf-8")
            return
        if path == "/api/bottle":
            state = pocket_soul.SoulState.load()
            self._send(state.pickup_bottle().encode(), content_type="text/plain; charset=utf-8")
            return
        if path == "/api/bridge":
            self._send(latest_bridge().encode(), content_type="text/plain; charset=utf-8")
            return
        if path == "/api/bridge-flash":
            self._send(latest_flash().encode(), content_type="text/plain; charset=utf-8")
            return
        if path == "/room":
            self._send(room_page())
            return
        if path == "/body":
            self._send(body_page())
            return
        if path == "/memory":
            self._send(memory_page())
            return
        if path == "/ritual":
            self._send(ritual_page())
            return
        if path == "/settings":
            self._send(settings_page())
            return
        self._send(doorstep())

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        data = parse_qs(self.rfile.read(length).decode("utf-8"))
        path = urlparse(self.path).path
        if path == "/api/bridge-flash":
            wish = data.get("wish", [""])[0].strip()
            body = flash_payload(wish)
            self._send(json.dumps(body, ensure_ascii=False).encode(), content_type="application/json; charset=utf-8")
            return
        if path.startswith("/api/"):
            action_path = path.removeprefix("/api")
            body = action_payload(action_path, data)
            self._send(json.dumps(body, ensure_ascii=False).encode(), content_type="application/json; charset=utf-8")
            return
        self._post_page(path, data)

    def _post_page(self, path: str, data: dict[str, list[str]]) -> None:
        with ACTION_LOCK:
            result = run_action(path, data)
        if path in {"/ritual", "/quest", "/postcard", "/nightly", "/bottle", "/bridge-flash"}:
            self._send(ritual_page(result))
            return
        if path == "/remember":
            self._send(memory_page())
            return
        if path == "/doorbell":
            self._send(room_page(result))
            return
        self._send(room_page(result))

    def log_message(self, fmt: str, *args) -> None:
        pocket_soul.append_log("web-access", fmt % args)


def run_action(path: str, data: dict[str, list[str]]) -> str:
    result = ""
    if path == "/ask":
        prompt = data.get("prompt", [""])[0].strip()
        mode = data.get("mode", ["council"])[0]
        state = pocket_soul.SoulState.load()
        if mode == "hermes":
            result = pocket_soul.run_hermes(prompt)
        elif mode == "soul":
            result = pocket_soul.call_model(prompt)
        else:
            result = pocket_soul.council_reply(prompt, state.memories)
        state.last_reply = result
        state.save()
        pocket_soul.append_log(f"web-{mode}", f"USER: {prompt}\n\nRESULT: {result}")
    elif path == "/doorbell":
        state = pocket_soul.SoulState.load()
        result = state.doorbell("web button")
        state.save()
    elif path == "/nightly":
        state = pocket_soul.SoulState.load()
        result = state.nightly_summary()
        state.save()
    elif path == "/postcard":
        state = pocket_soul.SoulState.load()
        title = data.get("title", [""])[0].strip()
        result = state.postcard(title)
        state.save()
    elif path == "/bottle":
        state = pocket_soul.SoulState.load()
        wish = data.get("wish", [""])[0].strip()
        result = state.bottle_message(wish)
        state.save()
    elif path == "/bridge":
        wish = data.get("wish", [""])[0].strip()
        result = pocket_soul.bridge_turn(wish)
    elif path == "/bridge-flash":
        state = pocket_soul.SoulState.load()
        wish = data.get("wish", [""])[0].strip()
        result = state.bridge_flash(wish)
        state.save()
    elif path == "/relic-action":
        index = parse_relic_id(data.get("id"))
        action = data.get("action", ["flash"])[0]
        result = relic_action(index, action)
    elif path == "/remember":
        memory = data.get("memory", [""])[0].strip()
        state = pocket_soul.SoulState.load()
        if memory:
            state.memories.append(memory)
            state.add_relic("memory", "Memory fragment", memory)
            state.last_reply = "Remembered."
            state.save()
            pocket_soul.append_log("web-memory", memory)
            result = "Remembered."
    elif path == "/ritual":
        kind = data.get("kind", ["wake"])[0]
        if kind == "wake":
            result = pocket_soul.council_reply("Wake up, observe the room's state today, and give me one bold but doable daily ritual.", pocket_soul.SoulState.load().memories)
            state = pocket_soul.SoulState.load()
            if state.quest_name == "Wake Spark":
                result += "\n" + state.complete_quest("wake ritual")
            else:
                state.add_relic("wake", "Wake ritual", result)
            state.last_reply = result
            state.save()
        elif kind == "dream":
            result = pocket_soul.call_model(pocket_soul.radar_text(), instruction="Turn this inspiration card into a cyber dream and one real-world action. Reply in English.")
            state = pocket_soul.SoulState.load()
            state.add_relic("dream", "Web dream", result)
            if state.quest_name == "Five-Minute Dream":
                result += "\n" + state.complete_quest("web dream ritual")
            state.last_reply = result
            state.save()
        elif kind == "log":
            result = pocket_soul.call_model("Generate the opening of today's captain log.", instruction="Keep it under 80 words, like sailing out with a digital life. Reply in English.")
            state = pocket_soul.SoulState.load()
            state.add_relic("log", "Web captain log", result)
            if state.quest_name == "Captain Log":
                result += "\n" + state.complete_quest("web captain log ritual")
            state.last_reply = result
            state.save()
        else:
            result = pocket_soul.radar_text()
            state = pocket_soul.SoulState.load()
            state.add_relic("radar", "Web radar", result)
            if state.quest_name == "Radar Seed":
                result += "\n" + state.complete_quest("web radar ritual")
            state.last_reply = result
            state.save()
        pocket_soul.append_log(f"web-ritual-{kind}", result)
    elif path == "/quest":
        action = data.get("action", ["complete"])[0]
        state = pocket_soul.SoulState.load()
        if action == "reroll":
            state.quest_date = ""
            state.ensure_daily_quest()
            state.last_reply = f"New quest: {state.quest_name}"
            result = state.last_reply
            state.add_relic("quest", "Quest rerolled", state.quest_name)
        else:
            result = state.complete_quest("web quest button")
            state.last_reply = result
        state.save()
    elif path == "/heading":
        state = pocket_soul.SoulState.load()
        task = ""
        evolution = pocket_soul.STATE_DIR / "evolution.md"
        if evolution.exists():
            task = evolution.read_text(encoding="utf-8")[-1200:]
        heading, next_action = pocket_soul.heading_from_task(task)
        state.set_heading(heading, next_action, "web heading refresh")
        state.last_reply = f"{state.heading}\n{state.next_action}"
        state.save()
        result = state.last_reply
    elif path == "/toy":
        toy = data.get("toy", [""])[0]
        result = f"Toy room touched: {toy or 'random toy'}"
        state = pocket_soul.SoulState.load()
        if state.quest_name == "Toy Ritual":
            result += "\n" + state.complete_quest("web toy button")
            state.last_reply = result
            state.save()
        else:
            state.add_relic("toy", toy or "web toy", result)
            state.save()
        pocket_soul.append_log("web-toy", f"Requested toy: {toy}\n{result}")
    return result


def main() -> None:
    pocket_soul.ensure_dirs()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Pocket Soul web room: http://0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
