#!/usr/bin/env python3
"""Pocket Soul Deck web room: a small non-terminal body surface."""
from __future__ import annotations

import html
import json
import mimetypes
import threading
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pocket_soul

HOST = "0.0.0.0"
PORT = 8787
ACTION_LOCK = threading.Lock()
ASSET_DIR = Path(__file__).resolve().parent / "asset"
TEMPLATE_DIR = ASSET_DIR / "templates"
PAGE_TEMPLATE_DIR = TEMPLATE_DIR / "pages"


@dataclass(frozen=True)
class DeckPage:
    path: str
    page_class: str


@dataclass(frozen=True)
class WebResponse:
    body: bytes
    content_type: str = "text/html; charset=utf-8"
    status: int = 200
    cache_control: str = ""


@dataclass(frozen=True)
class RequestContext:
    path: str
    params: dict[str, list[str]]

    @property
    def partial(self) -> bool:
        return self.params.get("partial") == ["1"]


PAGES = [
    DeckPage("/", "deck-room"),
]
PAGE_BY_PATH = {page.path: page for page in PAGES}
SHELL_PATHS = tuple(PAGE_BY_PATH)
ASSETS = {
    "robot_neutral": "/asset/calm.png",
    "robot_blush": "/asset/happy.png",
    "robot_curious": "/asset/think.png",
    "robot_happy": "/asset/happy.png",
    "robot_sad": "/asset/sleep.png",
}



def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def asset(name: str) -> str:
    return ASSETS[name]


def render_page_template(name: str, values: dict[str, object]) -> str:
    template = (PAGE_TEMPLATE_DIR / name).read_text(encoding="utf-8")
    return template.format_map(values)


def surface_stylesheet(surface: str) -> str:
    return "/asset/surfaces/web.css"


def surface_path(path: str, surface: str = "web") -> str:
    return path


def normalize_surface_path(raw_path: str) -> tuple[str, str]:
    parts = raw_path.split("/", 2)
    if len(parts) >= 2 and parts[1] == "web":
        inner = "/" + parts[2] if len(parts) == 3 and parts[2] else "/"
        return "web", inner
    return "web", raw_path


def is_provider_error(text: str) -> bool:
    raw = (text or "").lower()
    needles = [
        "http 429",
        "daily_limit_exceeded",
        "api call failed",
        "no such file or directory",
        "did not answer",
        "traceback",
        "connection error",
        "connection refused",
        "miri mind unavailable",
        "timeout",
    ]
    return any(needle in raw for needle in needles)


WEB_COMMAND_LABELS = (
    ("/today claim", "Mark done"),
    ("/bridge-flash", "Leave trace"),
    ("/bridge", "Bridge"),
    ("/postcard", "Postcard"),
    ("/bottle", "Bottle"),
    ("/ritual", "Daily"),
    ("/craft", "Craft charm"),
    ("/wheel", "Spin spark"),
    ("/hunt", "Find object"),
    ("/ask", "Talk"),
    ("/use", "Use"),
)


def web_copy(text: object) -> str:
    clean = str(text or "")
    upper = clean.strip().upper()
    if upper.startswith("CRAFT BENCH"):
        return "Not enough glow to craft yet. Try Find."
    if upper.startswith("PLAY NUDGE"):
        return "Try a room action."
    clean = clean.replace("CRAFT BENCH", "Craft bench")
    clean = clean.replace("PLAY NUDGE", "Room nudge")
    clean = clean.replace("try:", "next:")
    clean = clean.replace(" hunt ", " find ")
    clean = clean.replace("spark", "glow")
    clean = clean.replace("this moves the toy loop and earns glow", "look around and leave a trace")
    clean = clean.replace("this moves the toy loop and earns spark", "A shelf action that leaves a trace.")
    for command, label in WEB_COMMAND_LABELS:
        clean = clean.replace(command, label)
    return clean


def web_room_voice(text: str) -> str:
    return web_copy(room_voice(text))


def web_kind_label(kind: object) -> str:
    labels = {
        "hunt": "object",
        "craft": "charm",
        "wheel": "spark",
        "visit": "visit",
        "flash": "trace",
        "postcard": "postcard",
        "bottle": "bottle",
        "quest": "daily",
        "wake": "wake",
        "log": "log",
    }
    return labels.get(str(kind or "").lower(), str(kind or "trace"))


def charm_kind(kind: str) -> str:
    known = {
        "visit",
        "quest",
        "flash",
        "wake",
        "hunt",
        "craft",
        "postcard",
        "bottle",
        "wheel",
        "log",
    }
    clean = "".join(ch for ch in (kind or "").lower() if ch.isalnum() or ch == "-")
    return clean if clean in known else "default"


def relic_charm_html(kind: str, label: str = "") -> str:
    title = esc(label or kind or "room trace")
    return f"<span class='relic-charm kind-{charm_kind(kind)}' title='{title}' aria-label='{title}'></span>"


def recent_relic_charms(state: pocket_soul.RoomState, limit: int = 4) -> str:
    visible = [item for item in state.relics if item.get("kind") != "visit"] or state.relics
    charms = [
        relic_charm_html(item.get("kind", ""), item.get("title", "room trace"))
        for item in visible[-limit:][::-1]
    ]
    if not charms:
        charms = [relic_charm_html("default", "empty shelf")]
    return "".join(charms)


def recent_relics_html(state: pocket_soul.RoomState, limit: int = 4) -> str:
    charms = recent_relic_charms(state, limit)
    return "<div class='relic-dock' aria-hidden='true'>" + "".join(charms) + "</div>"


def web_room_phase(now: datetime | None = None) -> str:
    now = now or datetime.now()
    hour = now.hour
    if hour < 6 or hour >= 21:
        return "night"
    if hour < 9:
        return "dawn"
    if hour >= 18:
        return "evening"
    return "day"


def web_room_scene(now: datetime | None = None) -> tuple[str, str]:
    phase = web_room_phase(now)
    image_phase = "night" if phase == "night" else "light"
    filename = f"room-{image_phase}.jpg"
    if not (ASSET_DIR / filename).is_file():
        filename = "room.jpg"
        phase = "day"
    return f"/asset/{filename}", phase


def web_miri_state(state: pocket_soul.RoomState) -> str:
    text = f"{state.mood} {state.last_reply}".lower()
    if is_provider_error(state.last_reply):
        return "resting"
    if state.energy < 35 or "sleep" in text or "tired" in text:
        return "sleepy"
    if "think" in text or "?" in text or "bridge" in text:
        return "thinking"
    if "happy" in text or "love" in text or state.bond >= 25:
        return "bright"
    return "idle"


def web_bubble_tone(state: pocket_soul.RoomState) -> str:
    miri_state = web_miri_state(state)
    if miri_state == "resting":
        return "system"
    if miri_state in {"thinking", "sleepy"}:
        return "think"
    return "neutral"


def web_room_flags(state: pocket_soul.RoomState) -> str:
    flags = []
    if state.relics:
        flags.append("has-relics")
    if state.stash_items(1):
        flags.append("has-stash")
    if state.notes:
        flags.append("has-notes")
    if state.daily_done:
        flags.append("is-daily-done")
    return " ".join(flags)


def web_room_values(state: pocket_soul.RoomState, result: str = "") -> dict[str, object]:
    reply = web_room_voice(state.last_reply)
    room_image, room_phase = web_room_scene()
    return {
        "reply": esc(reply),
        "room_image": room_image,
        "room_phase": room_phase,
        "room_flags": web_room_flags(state),
        "miri_state": web_miri_state(state),
        "bubble_tone": web_bubble_tone(state),
        "miri_image": robot_image(state),
        "pinboard_panel": web_pinboard_panel_html(state),
        "shelf_panel": web_shelf_panel_html(state),
        "daily_panel": web_daily_panel_html(state),
        "body_panel": web_body_panel_html(state),
        "result": esc(web_copy(result)),
        "stamp": esc(datetime.now().strftime("%H:%M")),
    }


def shelf_objects_html(state: pocket_soul.RoomState, limit: int = 8) -> str:
    items = state.stash_items(limit)
    if items:
        charms = [relic_charm_html(item.get("kind", "hunt"), item.get("title", "stash object")) for item in items]
        return "<div class='shelf-objects'>" + "".join(charms) + "</div>"
    return (
        "<p class='shelf-empty'>The shelf is waiting for its first useful little thing.</p>"
        "<div class='shelf-objects'>"
        + relic_charm_html("hunt", "hunt")
        + relic_charm_html("wheel", "spark wheel")
        + relic_charm_html("craft", "craft")
        + "</div>"
    )


def web_pinboard_panel_html(state: pocket_soul.RoomState) -> str:
    if state.notes:
        notes = "".join(f"<li>{esc(note)}</li>" for note in state.notes[-8:][::-1])
    else:
        notes = "<li>The pinboard is empty.</li>"
    return f"""
<form class='note-form' method='post' action='/note' data-action='async'>
  <input name='note' placeholder='Pin a visible note'>
  <button>Pin</button>
</form>
<p class='pin-hint'>Visible props only. Quote one in Talk or Bridge when Miri should see it.</p>
<ul class='pin-list'>{notes}</ul>
"""


def web_shelf_panel_html(state: pocket_soul.RoomState) -> str:
    return f"""
{shelf_objects_html(state, 12)}
{stash_html(state, 10, True)}
"""


def web_daily_panel_html(state: pocket_soul.RoomState) -> str:
    turn = state.today_turn()
    action = esc(web_copy(turn["action"]))
    reason = esc(web_copy(turn["reason"]))
    reward = esc(web_copy(turn["reward"]))
    progress = "done" if turn["daily_done"] else f"{turn['progress']}/{turn['target']}"
    quest = "done" if turn["quest_done"] else "open"
    light = max(0, min(100, int(turn["light"])))
    return f"""
<section class='daily-card' style='--turn-light:{light}%'>
  <h2>{action}</h2>
  <p>{reason}</p>
  <div class='turn-meter' aria-hidden='true'><span></span></div>
  <small>daily {esc(progress)} / invitation {esc(quest)} / reward {reward}</small>
  <form method='post' action='/today' data-action='async'><button name='action' value='claim'>Mark done</button></form>
</section>
"""


def web_body_panel_html(state: pocket_soul.RoomState) -> str:
    words = body_words()
    rows = [
        ("temperature", words["temperature"], words["raw_temp"]),
        ("heartbeat", "steady", f"load {words['load']}"),
        ("window", words["window"], words["net"]),
        ("presence", words["presence"], "local room"),
        ("uptime", words["spirit"], words["uptime"]),
        ("disk", words["disk"], "storage body"),
    ]
    cards = "".join(
        f"<article><span>{esc(label)}</span><b>{esc(value)}</b><small>{esc(detail)}</small></article>"
        for label, value, detail in rows
    )
    return f"<div class='body-grid room-body-grid'>{cards}</div>"


def stash_html(state: pocket_soul.RoomState, limit: int = 8, interactive: bool = False) -> str:
    items = state.stash_items(limit)
    if not items:
        return "<p class='small'>Nothing on the shelf yet. Hunt first, then craft.</p>"
    cards = []
    for item in items:
        kind = esc(item.get("kind", "?"))
        title = esc(item.get("title", "?"))
        note = esc(item.get("note", ""))
        use_form = ""
        if interactive:
            raw_title = esc(item.get("title", ""))
            use_form = f"<form method='post' action='/use' data-action='async'><input type='hidden' name='target' value='{raw_title}'><button>Use</button></form>"
        cards.append(f"<article class='stash-item'><span>{kind}</span><b>{title}</b><p>{note}</p>{use_form}</article>")
    return "<div class='stash-grid'>" + "".join(cards) + "</div>"


def latest_postcard() -> str:
    post_dir = pocket_soul.STATE_DIR / "postcards"
    files = sorted(post_dir.glob("*.txt")) if post_dir.exists() else []
    if not files:
        return "No postcard yet."
    return files[-1].read_text(encoding="utf-8")[-3000:]


def latest_bridge() -> str:
    state = pocket_soul.RoomState.load()
    if "== Pocket Bridge ==" in state.last_reply:
        return state.last_reply[-5000:]
    return "No bridge turn yet."


def latest_flash() -> str:
    state = pocket_soul.RoomState.load()
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


def robot_image(state: pocket_soul.RoomState) -> str:
    text = f"{state.mood} {state.last_reply}".lower()
    if "sad" in text or "quiet" in text or state.energy < 35:
        return asset("robot_sad")
    if "blush" in text or "love" in text or state.bond >= 25:
        return asset("robot_blush")
    if "happy" in text or ":)" in state.mood:
        return asset("robot_happy")
    if state.mood in {"o_o", "*_*"}:
        return asset("robot_curious")
    return asset("robot_neutral")


def room_voice(text: str) -> str:
    """Turn raw logs/model transcripts into one present-tense room line."""
    raw = (text or "").strip()
    if not raw:
        return "I am here. Say one real sentence, or knock softly."
    if is_provider_error(raw):
        return "My inner voice is resting. The local room is still awake; touch the shelf or leave one sentence."
    lines = [line.strip() for line in raw.replace("\r", "\n").splitlines() if line.strip()]
    if lines and lines[0].upper().startswith("CHAT WINDOW"):
        candidates: list[str] = []
        for line in lines:
            lower = line.lower()
            if lower.startswith(("miri:",)):
                candidates.append(line.split(":", 1)[1].strip())
        if candidates:
            raw = candidates[-1]
        else:
            raw = lines[-1]
    raw = raw.replace("/ask keeps talking Enter blinks", "").strip()
    raw = raw.strip("* \n\t")
    if is_provider_error(raw):
        return "My inner voice is resting. The local room is still awake; touch the shelf or leave one sentence."
    return raw or "I am here. Say one real sentence, or knock softly."


def doorstep(result: str = "", partial: bool = False, surface: str = "web") -> bytes:
    state = pocket_soul.RoomState.load()
    state.ensure_daily_quest()
    return deck_page("/", render_page_template("room-web.html", web_room_values(state, result)), partial)


def live_payload(state: pocket_soul.RoomState | None = None) -> dict[str, object]:
    state = state or pocket_soul.RoomState.load()
    words = body_words()
    turn = state.today_turn()
    vitals_html = "".join(
        [
            f"<div class='mini-tile'><span>feeling</span><b>{esc(state.mood)}</b></div>",
            f"<div class='mini-tile'><span>body</span><b>{esc(words['temperature'])}</b></div>",
            f"<div class='mini-tile'><span>spirit</span><b>{esc(state.energy)}%</b></div>",
            f"<div class='mini-tile'><span>window</span><b>{esc(words['window'])}</b></div>",
        ]
    )
    presence = f"Feeling {state.mood}. Body {words['temperature']}. The window is open. Today's invitation: {state.quest_name}."
    web_presence = "Room is open."
    return {
        "vitals": f"{words['temperature']} / {words['window']} / {state.latest_relic_text()}",
        "presence": presence,
        "web_presence": web_presence,
        "vitals_html": vitals_html,
        "latest": room_voice(state.last_reply) if is_provider_error(state.last_reply) else state.latest_relic_text(),
        "reply": room_voice(state.last_reply),
        "web_latest": web_copy(room_voice(state.last_reply) if is_provider_error(state.last_reply) else state.latest_relic_text()),
        "web_reply": web_room_voice(state.last_reply),
        "mood": state.mood,
        "room_phase": web_room_phase(),
        "miri_state": web_miri_state(state),
        "bubble_tone": web_bubble_tone(state),
        "today": turn,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "relic_count": len(state.relics),
        "stash_count": len(state.stash_items(24)),
        "note_count": len(state.notes),
        "room_flags": web_room_flags(state),
    }


def flash_payload(wish: str = "") -> dict[str, object]:
    state = pocket_soul.RoomState.load()
    result = state.bridge_flash(wish)
    state.save()
    return {
        "result": result,
        "web_result": web_copy(result),
        "flash": result,
        "web_flash": web_copy(result),
        "live": live_payload(state),
    }


def action_payload(path: str, data: dict[str, list[str]]) -> dict[str, object]:
    with ACTION_LOCK:
        result = run_action(path, data)
        live = live_payload()
    return {
        "result": result,
        "web_result": web_copy(result),
        "live": live,
    }


def relic_detail(index: int) -> tuple[dict[str, str] | None, int]:
    state = pocket_soul.RoomState.load()
    if index < 0 or index >= len(state.relics):
        return None, len(state.relics)
    return state.relics[index], len(state.relics)


def parse_relic_id(values: list[str] | None) -> int:
    try:
        return int((values or ["-1"])[0] or -1)
    except (TypeError, ValueError):
        return -1


def relic_text(index: int) -> bytes:
    relic, total = relic_detail(index)
    if relic is None:
        return f"Relic not found. total={total}\n".encode()
    text = "\n".join([
        relic.get("title", "Relic"),
        f"kind: {relic.get('kind', '?')}",
        f"time: {relic.get('time', '')}",
        relic.get("note", ""),
        f"index: {index + 1}/{total}",
    ])
    return (text + "\n").encode()


def relic_action(index: int, action: str) -> str:
    relic, _total = relic_detail(index)
    if relic is None:
        return "Relic not found."
    label = f"{relic.get('kind', '?')} / {relic.get('title', 'Relic')}"
    note = relic.get("note", "")
    state = pocket_soul.RoomState.load()
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


SCRIPT_SRC = "/asset/surfaces/pocket-room.js"



def deck_page(path: str, inner: str, partial: bool = False, surface: str = "web") -> bytes | None:
    page_meta = PAGE_BY_PATH.get(path, PAGE_BY_PATH["/"])
    if partial:
        marker = f"<span hidden data-page-class='{esc(page_meta.page_class)}'></span>"
        return (marker + inner).encode()
    shell = TEMPLATE_DIR / "web-shell.html"
    template = shell.read_text(encoding="utf-8")
    shell_paths = [surface_path(item, surface) for item in SHELL_PATHS]
    html_doc = template.format(
        stylesheet=surface_stylesheet(surface),
        page_class=page_meta.page_class,
        content=inner,
        shell_paths=esc(json.dumps(shell_paths)),
        script_src=SCRIPT_SRC,
    )
    return html_doc.encode()


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


class Handler(BaseHTTPRequestHandler):
    def _send_response(self, response: WebResponse, include_body: bool = True) -> None:
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Content-Length", str(len(response.body)))
        if response.cache_control:
            self.send_header("Cache-Control", response.cache_control)
        self.end_headers()
        if include_body:
            self.wfile.write(response.body)

    def _send(
        self,
        body: bytes,
        status: int = 200,
        content_type: str = "text/html; charset=utf-8",
        cache_control: str = "",
    ) -> None:
        self._send_response(WebResponse(body, content_type, status, cache_control))

    def do_HEAD(self) -> None:
        response = self._resolve_get()
        self._send_response(response, include_body=False)

    def do_GET(self) -> None:
        self._send_response(self._resolve_get())

    def _resolve_get(self, include_body: bool = True) -> WebResponse:
        parsed = urlparse(self.path)
        ctx = RequestContext(parsed.path, parse_qs(parsed.query))
        surface, path = normalize_surface_path(ctx.path)
        if path.startswith("/asset/"):
            body, content_type, status = asset_response(path)
            cache = "public, max-age=86400" if status == 200 else ""
            return WebResponse(body if include_body else b"", content_type, status, cache)
        if path == "/relic":
            index = parse_relic_id(ctx.params.get("id"))
            return WebResponse(relic_text(index) if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/state":
            state = pocket_soul.RoomState.load().__dict__
            return WebResponse(json.dumps(state, ensure_ascii=False).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/live":
            return WebResponse(json.dumps(live_payload(), ensure_ascii=False).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/actions":
            layer = (ctx.params.get("layer") or [""])[0]
            return WebResponse(json.dumps(pocket_soul.action_catalog(layer), ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/card":
            state = pocket_soul.RoomState.load()
            return WebResponse(state.room_card().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/heading":
            state = pocket_soul.RoomState.load()
            body = {"heading": state.heading, "next_action": state.next_action}
            return WebResponse(json.dumps(body, ensure_ascii=False).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/relics":
            state = pocket_soul.RoomState.load()
            return WebResponse(json.dumps(state.relics, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/stash":
            state = pocket_soul.RoomState.load()
            body = {
                "spark": state.spark,
                "hunt_streak": state.hunt_streak,
                "items": state.stash_items(24),
                "text": state.stash_view(12),
            }
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/badges":
            state = pocket_soul.RoomState.load()
            rows = [
                {"name": name, "note": note, "unlocked": unlocked}
                for name, note, unlocked in state.badge_rows()
            ]
            body = {
                "lit": sum(1 for row in rows if row["unlocked"]),
                "total": len(rows),
                "badges": rows,
                "text": state.badges_view(),
            }
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/nudge":
            state = pocket_soul.RoomState.load()
            result = state.next_play_nudge()
            state.last_reply = result
            state.save()
            body = {"result": result, "live": live_payload(state)}
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/daily":
            state = pocket_soul.RoomState.load()
            body = {
                "daily": {
                    "name": state.daily_name,
                    "prompt": state.daily_prompt,
                    "key": state.daily_key,
                    "progress": state.daily_progress()[0],
                    "target": state.daily_progress()[1],
                    "reward": state.daily_reward,
                    "done": state.daily_done,
                },
                "text": state.daily_view(),
            }
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/today":
            state = pocket_soul.RoomState.load()
            body = {
                "today": state.today_turn(),
                "text": state.today_turn_text(),
            }
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/relic":
            index = parse_relic_id(ctx.params.get("id"))
            relic, total = relic_detail(index)
            body = {"index": index, "total": total, "relic": relic}
            status = 200 if relic is not None else 404
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8", status)
        if path == "/api/map":
            state = pocket_soul.RoomState.load()
            return WebResponse(state.constellation().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/doorbell":
            state = pocket_soul.RoomState.load()
            greeting = state.doorbell("api")
            state.save()
            return WebResponse(greeting.encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/body":
            return WebResponse(json.dumps(pocket_soul.body_scan(), ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/pulse":
            state = pocket_soul.RoomState.load()
            return WebResponse(state.pulse().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/nightly":
            state = pocket_soul.RoomState.load()
            summary = state.nightly_summary()
            state.save()
            return WebResponse(summary.encode() if include_body else b"", "text/markdown; charset=utf-8")
        if path == "/api/postcard":
            return WebResponse(latest_postcard().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/bottle":
            state = pocket_soul.RoomState.load()
            return WebResponse(state.pickup_bottle().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/bridge":
            return WebResponse(latest_bridge().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/bridge-flash":
            return WebResponse(latest_flash().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path in SHELL_PATHS:
            return WebResponse(doorstep(partial=ctx.partial, surface=surface) if include_body else b"")
        return WebResponse(b"not found\n" if include_body else b"", "text/plain; charset=utf-8", 404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        data = parse_qs(self.rfile.read(length).decode("utf-8"))
        _surface, path = normalize_surface_path(urlparse(self.path).path)
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
        self._send(doorstep(result))

    def log_message(self, fmt: str, *args) -> None:
        pocket_soul.append_log("web-access", fmt % args)


def run_action(path: str, data: dict[str, list[str]]) -> str:
    result = ""
    if path == "/ask":
        prompt = data.get("prompt", [""])[0].strip()
        state = pocket_soul.RoomState.load()
        result = pocket_soul.ask_miri(prompt)
        state.last_reply = result
        state.save()
        pocket_soul.append_log("web-miri", f"USER: {prompt}\n\nRESULT: {result}")
    elif path == "/doorbell":
        state = pocket_soul.RoomState.load()
        result = state.doorbell("web button")
        state.save()
    elif path == "/hunt":
        state = pocket_soul.RoomState.load()
        result = state.pocket_hunt("web button")
        state.save()
    elif path == "/nudge":
        state = pocket_soul.RoomState.load()
        result = state.next_play_nudge()
        state.save()
    elif path == "/daily":
        state = pocket_soul.RoomState.load()
        action = data.get("action", ["view"])[0]
        result = state.claim_daily_play("web button") if action == "claim" else state.daily_view()
        state.save()
    elif path == "/today":
        state = pocket_soul.RoomState.load()
        action = data.get("action", ["view"])[0]
        result = state.complete_today_turn("web button") if action == "claim" else state.today_turn_text()
        state.save()
    elif path == "/wheel":
        state = pocket_soul.RoomState.load()
        result = state.spark_wheel("web button")
        state.save()
    elif path == "/craft":
        state = pocket_soul.RoomState.load()
        target = data.get("target", [""])[0].strip()
        result = state.craft_keepsake(target, "web button")
        state.save()
    elif path == "/use":
        state = pocket_soul.RoomState.load()
        target = data.get("target", [""])[0].strip()
        result = state.use_stash_item(target, "web button")
        state.save()
    elif path == "/nightly":
        state = pocket_soul.RoomState.load()
        result = state.nightly_summary()
        state.save()
    elif path == "/postcard":
        state = pocket_soul.RoomState.load()
        title = data.get("title", [""])[0].strip()
        result = state.postcard(title)
        state.save()
    elif path == "/bottle":
        state = pocket_soul.RoomState.load()
        wish = data.get("wish", [""])[0].strip()
        result = state.bottle_message(wish)
        state.save()
    elif path == "/bridge":
        wish = data.get("wish", [""])[0].strip()
        result = pocket_soul.bridge_turn(wish)
    elif path == "/bridge-flash":
        state = pocket_soul.RoomState.load()
        wish = data.get("wish", [""])[0].strip()
        result = state.bridge_flash(wish)
        state.save()
    elif path == "/relic-action":
        index = parse_relic_id(data.get("id"))
        action = data.get("action", ["flash"])[0]
        result = relic_action(index, action)
    elif path == "/note":
        note = data.get("note", [""])[0].strip()
        state = pocket_soul.RoomState.load()
        if note:
            result = state.pin_note(note)
            state.save()
    elif path == "/ritual":
        kind = data.get("kind", ["wake"])[0]
        if kind == "wake":
            result = pocket_soul.ask_miri("Wake up, observe the room's state today, and give me one bold but doable daily ritual.")
            state = pocket_soul.RoomState.load()
            if state.quest_name == "Wake Spark":
                result += "\n" + state.complete_quest("wake ritual")
            else:
                state.add_relic("wake", "Wake ritual", result)
            state.last_reply = result
            state.save()
        elif kind == "dream":
            result = pocket_soul.call_model(pocket_soul.radar_text(), instruction="Turn this inspiration card into a cyber dream and one real-world action. Reply in English.")
            state = pocket_soul.RoomState.load()
            state.add_relic("dream", "Web dream", result)
            if state.quest_name == "Five-Minute Dream":
                result += "\n" + state.complete_quest("web dream ritual")
            state.last_reply = result
            state.save()
        elif kind == "log":
            result = pocket_soul.call_model("Generate the opening of today's captain log.", instruction="Keep it under 80 words, like sailing out with a digital life. Reply in English.")
            state = pocket_soul.RoomState.load()
            state.add_relic("log", "Web captain log", result)
            if state.quest_name == "Captain Log":
                result += "\n" + state.complete_quest("web captain log ritual")
            state.last_reply = result
            state.save()
        else:
            result = pocket_soul.radar_text()
            state = pocket_soul.RoomState.load()
            state.add_relic("radar", "Web radar", result)
            if state.quest_name == "Radar Seed":
                result += "\n" + state.complete_quest("web radar ritual")
            state.last_reply = result
            state.save()
        pocket_soul.append_log(f"web-ritual-{kind}", result)
    elif path == "/quest":
        action = data.get("action", ["complete"])[0]
        state = pocket_soul.RoomState.load()
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
        state = pocket_soul.RoomState.load()
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
        state = pocket_soul.RoomState.load()
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
    print(f"Miri web room: http://0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
