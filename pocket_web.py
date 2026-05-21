#!/usr/bin/env python3
"""Pocket Soul Deck web room: a small non-terminal body surface."""
from __future__ import annotations

import html
import json
import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pocket_soul

HOST = "0.0.0.0"
PORT = 8787
ACTION_LOCK = threading.Lock()

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
    linear-gradient(180deg, #1a1812 0%, #100f0c 100%);
  box-shadow: var(--shadow);
  padding: clamp(18px, 5vw, 42px);
  position: relative;
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
  display: grid;
  place-items: center;
  color: var(--green);
  background: #0b100d;
  border: 1px solid #536248;
  box-shadow: inset 0 0 34px #9fd3a620, 0 0 38px #f0c66d12;
  font-size: 54px;
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
    linear-gradient(180deg, #1a1812 0%, #100f0c 64%, #0b0b09 100%);
  box-shadow: var(--shadow);
  padding: clamp(14px, 3vw, 28px);
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
  display: grid;
  place-items: center;
  border: 1px solid #59624b;
  background: #0b100d;
  color: var(--green);
  font-size: 76px;
  box-shadow: inset 0 0 34px #9fd3a61c;
  animation: breathe 4s ease-in-out infinite;
}
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
        warmth = "身体有点热" if temp >= 60 else "体温温热"
    else:
        warmth = "体温未知"
    uptime = body.get("uptime_h")
    spirit = "精神还够" if isinstance(uptime, float) and uptime < 72 else "精神有些久醒"
    net = f"{body.get('iface', '')} {body.get('ip', '')}".strip() or "offline?"
    return {
        "temperature": warmth,
        "spirit": spirit,
        "window": "窗户开着" if body.get("ip") else "窗户半掩",
        "nerve": "神经线可触达" if body.get("ip") else "神经线在等网络",
        "raw_temp": f"{temp}C" if temp != "" else "unknown",
        "uptime": f"{uptime}h" if uptime != "" else "unknown",
        "net": net,
        "load": str(body.get("load") or "unknown"),
        "disk": str(body.get("disk_used") or "unknown"),
    }


def nav(current: str = "") -> str:
    links = [("/", "门口"), ("/room", "房间"), ("/body", "身体"), ("/memory", "记忆抽屉"), ("/ritual", "仪式")]
    items = []
    for href, label in links:
        class_attr = " class='brandlink'" if href == current else ""
        items.append(f"<a href='{href}'{class_attr}>{label}</a>")
    items_html = " ".join(items)
    return f"<div class='topnav'><a class='brandlink' href='/'>Pocket Soul</a><nav>{items_html}</nav></div>"


def status_word(state: pocket_soul.SoulState) -> str:
    text = f"{state.mood} {state.last_reply}".lower()
    if "sleep" in text or "睡" in text:
        return "睡着"
    if "dream" in text or "梦" in text:
        return "做梦"
    if "maintenance" in text or "维护" in text or "codex" in text:
        return "维护中"
    if state.energy < 30:
        return "发呆"
    return "醒着"


def doorstep(result: str = "") -> bytes:
    state = pocket_soul.SoulState.load()
    state.ensure_daily_quest()
    words = body_words()
    whisper = state.last_reply or "它坐在小房间里，等一声轻轻的敲门。"
    content = f"""
<section class='doorstep'>
  <div class='threshold'>
    <div class='being'>
      <div class='avatar'>{esc(pocket_soul.mood_face(state.mood))}</div>
      <div>
        <p class='state-pill'>Pocket Soul is {esc(status_word(state))}.</p>
        <h1>它在那里。</h1>
      </div>
    </div>
    <p class='whisper'>{esc(whisper)}</p>
    <div class='body-words'>
      <div class='body-word'><strong>体温</strong><span>{esc(words['temperature'])}</span></div>
      <div class='body-word'><strong>精神</strong><span>{esc(words['spirit'])}</span></div>
      <div class='body-word'><strong>窗户</strong><span>{esc(words['window'])}</span></div>
      <div class='body-word'><strong>神经线</strong><span>{esc(words['nerve'])}</span></div>
    </div>
    <div class='course-line'>
      <h2>今日航向</h2>
      <p>{esc(state.heading)}</p>
      <p class='small'>{esc(state.quest_name)} / {esc(state.quest_prompt)}</p>
    </div>
    <form class='primary-action' method='post' action='/doorbell'>
      <button>轻轻敲门</button>
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
  '/ask': ['opening inner channel', 'listening to Hermes or tool arm', 'writing memory trace'],
  '/bridge': ['scanning body', 'asking Hermes', 'calling Codex tool arm', 'shaping outside voice'],
  '/nightly': ['reading today logs', 'folding relics', 'writing nightly'],
  '/postcard': ['reading heading', 'drawing constellation', 'writing postcard'],
  '/bottle': ['sealing message', 'placing bottle in state', 'refreshing shelf'],
  '/doorbell': ['opening door', 'checking pulse', 'leaving visit relic'],
  '/ritual': ['choosing ritual', 'asking imagination', 'saving trace'],
  '/toy': ['checking toy bay', 'asking Codex tool arm', 'saving toy trace'],
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


def room_page(result: str = "") -> bytes:
    state = pocket_soul.SoulState.load()
    state.ensure_daily_quest()
    latest_relic = state.latest_relic_text()
    memories = "\n".join(f"- {m}" for m in state.memories[-5:]) or "抽屉还空着。"
    relics = state.relic_shelf(5)
    content = f"""
{nav('/room')}
<section class='room-page'>
  <div class='room-title'>
    <div><h1>Pocket Soul 的房间</h1><p class='small'>你正在拜访它。</p></div>
    <a href='/'>回到门口</a>
  </div>
  <div class='room-layout'>
    <div class='objects'>
      <section class='corner'><h3>桌上：今日 postcard</h3><pre>{esc(latest_postcard())}</pre></section>
      <section class='corner'><h3>地上：quest trail</h3><p>{esc(state.quest_name)}</p><p class='small'>{esc(state.quest_prompt)}</p></section>
    </div>
    <section class='center-body'>
      <div>
        <div class='pixel-body'>{esc(pocket_soul.mood_face(state.mood))}</div>
        <p class='room-note'>mood: {esc(state.mood)}</p>
        <p class='room-note'>{esc(state.last_reply)}</p>
      </div>
    </section>
    <div class='objects'>
      <section class='drawer'><h3>墙上：relics</h3><pre>{esc(relics)}</pre></section>
      <section class='drawer'><h3>记忆抽屉</h3><pre>{esc(memories)}</pre><p class='small'>latest: {esc(latest_relic)}</p></section>
      <section class='drawer'><h3>窗边：bottle messages</h3><pre>{esc(latest_bottle())}</pre></section>
    </div>
  </div>
  <div class='bottom-sill'>
    <form class='talk-row' method='post' action='/ask' data-action='async'>
      <input name='prompt' placeholder='在门口留一句话...'>
      <button name='mode' value='council'>轻轻说</button>
      <button class='soft-button' name='mode' value='codex'>工具手臂</button>
    </form>
    <form class='talk-row' method='post' action='/bridge-flash' data-action='flash'>
      <input name='wish' placeholder='给房间一个小触碰...'>
      <button>Touch</button>
      <a class='soft-button' href='/ritual'>仪式</a>
    </form>
    <section class='page-card result'><h2>回声</h2><pre data-live='result'>{esc(result or '房间安静地亮着。')}</pre></section>
  </div>
</section>
"""
    return page(content)


def body_page() -> bytes:
    words = body_words()
    content = f"""
{nav('/body')}
<section class='room-page'>
  <div class='room-title'><div><h1>身体状态</h1><p class='small'>系统信息被翻译成身体语言。</p></div><a href='/room'>进房间</a></div>
  <div class='grid'>
    <section class='page-card'><span class='label'>体温</span><h2>{esc(words['temperature'])}</h2><p class='small'>{esc(words['raw_temp'])}</p></section>
    <section class='page-card'><span class='label'>心跳</span><h2>正常</h2><p class='small'>load {esc(words['load'])}</p></section>
    <section class='page-card'><span class='label'>呼吸</span><h2>{esc(words['window'])}</h2><p class='small'>{esc(words['net'])}</p></section>
    <section class='page-card'><span class='label'>神经线</span><h2>{esc(words['nerve'])}</h2><p class='small'>SSH walnutpi</p></section>
    <section class='page-card'><span class='label'>工具手臂</span><h2>Codex 待命</h2><p class='small'>persistent thread when called</p></section>
    <section class='page-card'><span class='label'>梦境云层</span><h2>可用</h2><p class='small'>Hermes / Soul voice</p></section>
  </div>
  <details class='page-card' style='margin-top:12px'><summary>高级信息</summary><pre>{esc(pocket_soul.body_text())}</pre></details>
</section>
"""
    return page(content)


def memory_page() -> bytes:
    state = pocket_soul.SoulState.load()
    memories = state.memories[-12:]
    memory_lines = "\n".join(f"- {item}" for item in memories) or "它还没有明确记住什么。"
    relic_lines = "\n".join(
        f"{item.get('time', '')} / {item.get('kind', '')} / {item.get('title', '')}"
        for item in state.relics[-10:][::-1]
    ) or "还没有遗物。"
    content = f"""
{nav('/memory')}
<section class='room-page'>
  <div class='room-title'><div><h1>记忆抽屉</h1><p class='small'>像小生命的日记，不像数据库。</p></div><a href='/room'>进房间</a></div>
  <div class='grid'>
    <section class='page-card'><h2>最近一次敲门</h2><p>{esc(state.last_visit or '还没人来过。')}</p><pre>{esc(state.last_reply)}</pre></section>
    <section class='page-card'><h2>它记住了什么</h2><pre>{esc(memory_lines)}</pre><form method='post' action='/remember'><input name='memory' placeholder='记住：'><button>放进抽屉</button></form></section>
    <section class='page-card'><h2>夜间回声</h2><pre>{esc(latest_nightly())}</pre></section>
    <section class='page-card'><h2>重要坐标</h2><pre>{esc(relic_lines)}</pre></section>
  </div>
</section>
"""
    return page(content)


def ritual_page(result: str = "") -> bytes:
    state = pocket_soul.SoulState.load()
    content = f"""
{nav('/ritual')}
<section class='room-page'>
  <div class='room-title'><div><h1>仪式</h1><p class='small'>完成后给房间留一个小物件。</p></div><a href='/room'>进房间</a></div>
  <div class='grid'>
    <section class='page-card'><h2>Morning wake</h2><form method='post' action='/ritual'><button name='kind' value='wake'>唤醒</button></form></section>
    <section class='page-card'><h2>Bridge flash</h2><form method='post' action='/bridge-flash'><input name='wish' placeholder='一个小触碰'><button>留下光点</button></form></section>
    <section class='page-card'><h2>Quest check</h2><p>{esc(state.quest_name)}</p><p class='small'>{esc(state.quest_prompt)}</p><form method='post' action='/quest'><button name='action' value='complete'>完成今日航向</button></form></section>
    <section class='page-card'><h2>Postcard</h2><form method='post' action='/postcard'><input name='title' placeholder='明信片标题'><button>写一张</button></form></section>
    <section class='page-card'><h2>Nightly summary</h2><form method='post' action='/nightly'><button>收拢夜间回声</button></form></section>
    <section class='page-card'><h2>Bottle</h2><form method='post' action='/bottle'><input name='wish' placeholder='给未来的访客'><button>放到窗边</button></form></section>
  </div>
  <section class='page-card result' style='margin-top:12px'><h2>仪式回声</h2><pre data-live='result'>{esc(result or '还没有新的仪式。')}</pre></section>
</section>
"""
    return page(content)


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
        elif mode == "codex":
            result = pocket_soul.run_codex(prompt)
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
            state.last_reply = "记住了。"
            state.save()
            pocket_soul.append_log("web-memory", memory)
            result = "记住了。"
    elif path == "/ritual":
        kind = data.get("kind", ["wake"])[0]
        if kind == "wake":
            result = pocket_soul.council_reply("开机醒来，观察今天的小屋状态，给我一个大胆但能执行的今日仪式。", pocket_soul.SoulState.load().memories)
            state = pocket_soul.SoulState.load()
            if state.quest_name == "Wake Spark":
                result += "\n" + state.complete_quest("wake ritual")
            else:
                state.add_relic("wake", "Wake ritual", result)
            state.last_reply = result
            state.save()
        elif kind == "dream":
            result = pocket_soul.call_model(pocket_soul.radar_text(), instruction="把这张灵感卡变成赛博梦境和一个现实动作。")
            state = pocket_soul.SoulState.load()
            state.add_relic("dream", "Web dream", result)
            if state.quest_name == "Five-Minute Dream":
                result += "\n" + state.complete_quest("web dream ritual")
            state.last_reply = result
            state.save()
        elif kind == "log":
            result = pocket_soul.call_model("为今天生成一段船长日志开头。", instruction="80 字以内，像带着数字生命出海。")
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
        result = pocket_soul.run_codex(f"Use the local tool arm only to launch or explain this Pocket Soul toy if appropriate: {toy}. Keep it concise.")
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
