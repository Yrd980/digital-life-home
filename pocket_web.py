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
:root { color-scheme: dark; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
body { margin: 0; background: #080a0f; color: #e8ffe8; }
main { max-width: 920px; margin: 0 auto; padding: 18px; }
.hero { border: 1px solid #2a7; padding: 16px; background: #10151d; }
.hero.live { animation: breathe 4s ease-in-out infinite; }
.face { font-size: 56px; line-height: 1; }
.vitals { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; margin-top: 12px; }
.vital { border: 1px solid #263; background: #07120d; padding: 10px; }
.vital strong { display: block; color: #9ff; font-size: 12px; font-weight: normal; }
.rail { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
.sigil { border: 1px solid #365; background: #101820; color: #9ff; padding: 4px 7px; min-width: 18px; text-align: center; text-decoration: none; }
.sigil:hover { border-color: #9ff; background: #17242d; }
.flash-button { border-color: #9ff; background: #17313a; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 12px; }
.card { border: 1px solid #244; background: #0d1118; padding: 12px; min-height: 88px; }
h1, h2 { margin: 0 0 8px; }
a, button { color: #9ff; }
textarea, input, select { width: 100%; box-sizing: border-box; background: #05070a; color: #e8ffe8; border: 1px solid #366; padding: 10px; font: inherit; }
button { background: #123; border: 1px solid #4aa; padding: 9px 12px; cursor: pointer; }
.row { display: flex; gap: 8px; flex-wrap: wrap; }
pre { white-space: pre-wrap; word-break: break-word; background: #05070a; border: 1px solid #223; padding: 12px; max-height: 420px; overflow: auto; }
.badge { color: #111; background: #8f8; padding: 2px 6px; }
.small { color: #9ab; font-size: 13px; }
.thinking { border-color: #9ff; box-shadow: 0 0 0 1px #224, 0 0 18px #0ff3 inset; }
.phase { color: #9ff; min-height: 20px; }
.phase:before { content: ""; display: inline-block; width: 8px; height: 8px; margin-right: 8px; border: 1px solid #9ff; background: #123; animation: blink 1s steps(2, start) infinite; }
@keyframes breathe { 0%, 100% { border-color: #275; } 50% { border-color: #9ff; } }
@keyframes blink { 50% { opacity: .25; } }
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


def vital_strip(state: pocket_soul.SoulState) -> str:
    latest = state.latest_relic_text()
    recent = state.relics[-10:]
    if recent:
        start = len(state.relics) - len(recent)
        rail = "".join(
            f"<a class='sigil' href='/relic?id={idx}' title='{esc(item.get('kind', ''))}: {esc(item.get('title', ''))}'>{esc(pocket_soul.RELIC_SIGILS.get(item.get('kind', ''), '*'))}</a>"
            for idx, item in enumerate(recent, start)
        )
    else:
        rail = "<span class='small'>No touch trail yet.</span>"
    return f"""
<div class='vitals'>
  <div class='vital'><strong>energy</strong>{state.energy}/100</div>
  <div class='vital'><strong>bond</strong>Lv.{state.bond}</div>
  <div class='vital'><strong>spark</strong>{state.spark}</div>
  <div class='vital'><strong>visits</strong>{state.visits}</div>
  <div class='vital'><strong>latest</strong>{esc(latest)}</div>
</div>
<div class='rail'>{rail}</div>
"""


def live_payload(state: pocket_soul.SoulState | None = None) -> dict[str, object]:
    state = state or pocket_soul.SoulState.load()
    return {
        "vitals": vital_strip(state),
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
        return state.postcard(f"Relic {index + 1}: {label}")
    if action == "bottle":
        return state.bottle_message(f"Relic {index + 1}: {label} | {note}")
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


def home(result: str = "") -> bytes:
    state = pocket_soul.SoulState.load()
    state.ensure_daily_quest()
    if not result:
        now = datetime.now()
        try:
            last = datetime.strptime(state.last_visit, "%Y-%m-%d %H:%M") if state.last_visit else None
        except ValueError:
            last = None
        if last is None or now - last > timedelta(minutes=5):
            result = state.doorbell("web")
            state.save()
    toys = pocket_soul.available_toys()
    toy_buttons = "".join(f"<button name='toy' value='{esc(name)}'>{esc(name)}</button>" for name, _cmd, _argv, _desc in toys[:16])
    memories = "\n".join(f"- {m}" for m in state.memories[-12:]) or "No memories yet."
    quest_status = "done" if state.quest_done else "open"
    content = f"""
<section class='hero live'>
  <div class='row'><div class='face'>{esc(pocket_soul.mood_face(state.mood))}</div><div><h1>Pocket Soul Deck</h1><div><span class='badge'>Hermes inner</span> <span class='badge'>Cloud imagination</span> <span class='badge'>Codex tool arm</span></div><p>{esc(state.mood)}</p><p>{esc(state.last_reply)}</p></div></div>
  <div data-live='vitals'>{vital_strip(state)}</div>
  <form method='post' action='/bridge-flash' class='row' data-action='flash'><input name='wish' placeholder='touch the deck'><button class='flash-button'>Flash</button></form>
  <p class='small' data-live='stamp'>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</section>
<div class='grid'>
  <section class='card'><h2>Doorbell</h2><pre>{esc(state.last_reply)}</pre><form method='post' action='/doorbell' data-action='async'><button>Knock</button></form></section>
  <section class='card'><h2>Pulse</h2><pre>{esc(state.pulse())}</pre><p class='small'><a href='/api/pulse'>pulse endpoint</a></p></section>
  <section class='card'><h2>Nightly</h2><form method='post' action='/nightly' data-action='async'><button>Write Nightly</button></form><pre>{esc(latest_nightly())}</pre><p class='small'><a href='/api/nightly'>nightly endpoint</a></p></section>
  <section class='card'><h2>Postcard</h2><form method='post' action='/postcard' data-action='async'><input name='title' placeholder='title'><button>Write Postcard</button></form><pre>{esc(latest_postcard())}</pre><p class='small'><a href='/api/postcard'>postcard endpoint</a></p></section>
  <section class='card'><h2>Bottle</h2><form method='post' action='/bottle' data-action='async'><input name='wish' placeholder='message'><button>Cast Bottle</button></form><pre>{esc(latest_bottle())}</pre><p class='small'><a href='/api/bottle'>pick bottle endpoint</a></p></section>
  <section class='card'><h2>Bridge</h2><form method='post' action='/bridge' data-action='async'><textarea name='wish' rows='3' placeholder='Give Hermes, Soul, and Codex one shared wish'></textarea><button>Run Bridge</button></form><pre>{esc(latest_bridge())}</pre><p class='small'><a href='/api/bridge'>latest bridge endpoint</a></p></section>
  <section class='card'><h2>Bridge Flash</h2><form method='post' action='/bridge-flash' data-action='flash'><input name='wish' placeholder='one immediate spark'><button>Flash</button></form><pre data-live='flash'>{esc(latest_flash())}</pre><p class='small'><a href='/api/bridge-flash'>flash endpoint</a></p></section>
  <section class='card'><h2>Body</h2><pre>{esc(pocket_soul.body_text())}</pre><p class='small'><a href='/api/body'>body endpoint</a></p></section>
  <section class='card'><h2>Heading</h2><pre>{esc(state.heading)}\n{esc(state.next_action)}</pre><form method='post' action='/heading' data-action='async'><button name='action' value='from-heartbeat'>Refresh from heartbeat</button></form></section>
  <section class='card'><h2>Daily Quest</h2><p><span class='badge'>{esc(quest_status)}</span> {esc(state.quest_name)}</p><pre>{esc(state.quest_prompt)}\n\nReward: {esc(state.quest_reward)}</pre><form method='post' action='/quest' data-action='async'><button name='action' value='complete'>Complete</button><button name='action' value='reroll'>Reroll</button></form></section>
  <section class='card'><h2>Constellation</h2><pre>{esc(state.constellation(34, 11))}</pre><p class='small'><a href='/api/map'>map endpoint</a></p></section>
  <section class='card'><h2>Relics</h2><pre>{esc(state.relic_shelf(5))}</pre><p class='small'><a href='/api/relics'>relic shelf endpoint</a></p></section>
  <section class='card'><h2>Soul Card</h2><pre>{esc(state.soul_card())}</pre><p class='small'><a href='/api/card'>JSON/text card endpoint</a></p></section>
  <section class='card'><h2>Speak</h2><form method='post' action='/ask' data-action='async'><textarea name='prompt' rows='4' placeholder='Say anything to the living deck'></textarea><div class='row'><button name='mode' value='hermes'>Hermes only</button><button name='mode' value='council'>Council</button><button name='mode' value='soul'>Soul</button><button name='mode' value='codex'>Codex tool</button></div></form></section>
  <section class='card'><h2>Rituals</h2><form method='post' action='/ritual' data-action='async'><div class='row'><button name='kind' value='wake'>Wake</button><button name='kind' value='dream'>Dream</button><button name='kind' value='log'>Captain log</button><button name='kind' value='radar'>Radar</button></div></form><p class='small'>Rituals make the board feel less like software and more like a room.</p></section>
  <section class='card'><h2>Toys</h2><form method='post' action='/toy' data-action='async'><div class='row'>{toy_buttons}</div></form><p class='small'>Toys launch on the board, not inside this browser.</p></section>
  <section class='card'><h2>Memory</h2><pre>{esc(memories)}</pre><form method='post' action='/remember' data-action='async'><input name='memory' placeholder='记住：'><button>Remember</button></form></section>
</div>
<section class='card'><h2>Thinking</h2><p class='phase' data-live='phase'>idle</p><p class='small'>Every button above calls the real board action; this line shows the current phase while the board works.</p></section>
<section class='card'><h2>Result</h2><pre data-live='result'>{esc(result or 'The room is quiet.')}</pre></section>
<section class='card'><h2>Latest Log</h2><pre>{esc(latest_log())}</pre></section>
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
            index = int(params.get("id", ["-1"])[0] or -1)
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
            index = int(params.get("id", ["-1"])[0] or -1)
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
        self._send(home())

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
        self._send(home(result))

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
        index = int(data.get("id", ["-1"])[0] or -1)
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
