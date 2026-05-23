#!/usr/bin/env python3
"""Pocket Soul Deck web room: a small non-terminal body surface."""
from __future__ import annotations

import html
import json
import mimetypes
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
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
SURFACE_DIR = ASSET_DIR / "surfaces"


@dataclass(frozen=True)
class DeckPage:
    path: str
    icon: str
    label: str
    page_class: str
    nav: bool = True


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
    DeckPage("/", "home", "Home", "deck-home"),
    DeckPage("/room", "room", "Room", "deck-room"),
    DeckPage("/body", "body", "Body", "deck-body"),
    DeckPage("/notes", "notes", "Notes", "deck-notes"),
    DeckPage("/stash", "grid", "Stash", "deck-stash"),
    DeckPage("/badges", "badge", "Badges", "deck-badges", nav=False),
    DeckPage("/ritual", "ritual", "Ritual", "deck-ritual"),
    DeckPage("/settings", "settings", "Settings", "deck-settings"),
]
PAGE_BY_PATH = {page.path: page for page in PAGES}
SHELL_PATHS = tuple(PAGE_BY_PATH)
SURFACES = {"web", "board"}
ASSETS = {
    "robot_neutral": "/asset/opt/robot-neutral.webp",
    "robot_blush": "/asset/opt/robot-blush.webp",
    "robot_curious": "/asset/opt/robot-curious.webp",
    "robot_happy": "/asset/opt/robot-happy.webp",
    "robot_sad": "/asset/opt/robot-sad.webp",
}



def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def asset(name: str) -> str:
    return ASSETS[name]


def render_page_template(name: str, values: dict[str, object]) -> str:
    template = (PAGE_TEMPLATE_DIR / name).read_text(encoding="utf-8")
    return template.format_map(values)


def surface_stylesheet(surface: str) -> str:
    if surface not in SURFACES:
        surface = "web"
    return f"/asset/surfaces/{surface}.css"


def surface_path(path: str, surface: str = "web") -> str:
    if surface == "web":
        return path
    return f"/{surface}" if path == "/" else f"/{surface}{path}"


def normalize_surface_path(raw_path: str) -> tuple[str, str]:
    parts = raw_path.split("/", 2)
    if len(parts) >= 2 and parts[1] in SURFACES:
        inner = "/" + parts[2] if len(parts) == 3 and parts[2] else "/"
        return parts[1], inner
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


ICONS = {
    "home": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M4 11.5 12 5l8 6.5'/><path d='M6.5 10.8V20h11v-9.2'/><path d='M9.5 20v-5.5h5V20'/></svg>",
    "room": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M7 20V9l5-4 5 4v11'/><path d='M10 20v-6h4v6'/><path d='M4 20h16'/></svg>",
    "body": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M12 21s-7-4.4-7-10a4.2 4.2 0 0 1 7-3.1A4.2 4.2 0 0 1 19 11c0 5.6-7 10-7 10Z'/></svg>",
    "notes": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M5 6h14'/><path d='M5 11h14'/><path d='M5 16h14'/><path d='M5 21h14'/></svg>",
    "ritual": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M12 3v5'/><path d='M8.5 8h7'/><path d='m9.5 11-2 9h9l-2-9'/><path d='M9 16h6'/></svg>",
    "grid": "<svg viewBox='0 0 24 24' aria-hidden='true'><rect x='4' y='4' width='6' height='6' rx='1'/><rect x='14' y='4' width='6' height='6' rx='1'/><rect x='4' y='14' width='6' height='6' rx='1'/><rect x='14' y='14' width='6' height='6' rx='1'/></svg>",
    "knock": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M12 21s-7-4.4-7-10a4.2 4.2 0 0 1 7-3.1A4.2 4.2 0 0 1 19 11c0 5.6-7 10-7 10Z'/></svg>",
    "hunt": "<svg viewBox='0 0 24 24' aria-hidden='true'><circle cx='11' cy='11' r='6'/><path d='m16 16 4 4'/><path d='M11 8v6M8 11h6'/></svg>",
    "wheel": "<svg viewBox='0 0 24 24' aria-hidden='true'><circle cx='12' cy='12' r='8'/><circle cx='12' cy='12' r='2'/><path d='M12 4v6M12 14v6M4 12h6M14 12h6M6.3 6.3l4.2 4.2M13.5 13.5l4.2 4.2M17.7 6.3l-4.2 4.2M10.5 13.5l-4.2 4.2'/></svg>",
    "nudge": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M5 12h12'/><path d='m13 8 4 4-4 4'/><path d='M5 6h5M5 18h5'/></svg>",
    "craft": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M14.7 6.3 17.7 3.3a2.1 2.1 0 0 1 3 3l-3 3'/><path d='M4 20l6.6-6.6'/><path d='m7 17 10-10'/><path d='M3 21l5-1 11-11-4-4L4 16z'/></svg>",
    "quest": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M5 12.5 10 17 19 7'/><path d='M4 5h16v16H4z'/></svg>",
    "postcard": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M4 6h16v12H4z'/><path d='m4 7 8 6 8-6'/></svg>",
    "badge": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M12 3 15 8l5 1-3.5 4 1 6-5.5-2.8L6.5 19l1-6L4 9l5-1z'/></svg>",
    "settings": "<svg viewBox='0 0 24 24' aria-hidden='true'><circle cx='12' cy='12' r='3'/><path d='M12 2.8v3M12 18.2v3M4.5 4.5l2.1 2.1M17.4 17.4l2.1 2.1M2.8 12h3M18.2 12h3M4.5 19.5l2.1-2.1M17.4 6.6l2.1-2.1'/></svg>",
}


def icon(name: str) -> str:
    return ICONS.get(name, "")


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


def badges_html(state: pocket_soul.RoomState) -> str:
    cards = []
    for name, note, unlocked in state.badge_rows():
        klass = "badge-tile is-lit" if unlocked else "badge-tile"
        mark = "lit" if unlocked else "locked"
        cards.append(f"<article class='{klass}'><span>{mark}</span><b>{esc(name)}</b><p>{esc(note)}</p></article>")
    return "<div class='badge-wall'>" + "".join(cards) + "</div>"


def nudge_preview(state: pocket_soul.RoomState) -> str:
    old_reply = state.last_reply
    try:
        return state.next_play_nudge()
    finally:
        state.last_reply = old_reply


def today_turn_html(state: pocket_soul.RoomState, compact: bool = False) -> str:
    turn = state.today_turn()
    progress = "done" if turn["daily_done"] else f"{turn['progress']}/{turn['target']}"
    quest = "done" if turn["quest_done"] else "open"
    command = str(turn["command"])
    action = esc(str(turn["action"]))
    reward = esc(str(turn["reward"]))
    reason = esc(str(turn["reason"]))
    light = max(0, min(100, int(turn["light"])))
    target_href = "/ritual" if command in {"/postcard", "/bottle"} else "/room"
    detail = reward if compact else f"{reason} / {reward}"
    return f"""
<section class='today-turn' style='--turn-light:{light}%'>
  <header><h2>Today's Turn</h2><span class='phase'>{esc(str(turn['phase']))} / {light}%</span></header>
  <p><b>{esc(command)}</b> {action}</p>
  <div class='turn-meter' aria-hidden='true'><span></span></div>
  <small>daily {esc(progress)} | quest {esc(quest)} | badges {esc(str(turn['badges_lit']))}/{esc(str(turn['badges_total']))}</small>
  <small>{detail}</small>
  <div class='today-actions'>
    <a class='ghost-button' href='{target_href}'>{esc(command)}</a>
    <form method='post' action='/today' data-action='async'><button name='action' value='claim'>Claim</button></form>
  </div>
</section>
"""


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


def nav(current: str = "") -> str:
    links = [("/", "Door"), ("/room", "Room"), ("/body", "Body"), ("/notes", "Notes"), ("/ritual", "Rituals")]
    items = []
    for href, label in links:
        class_attr = " class='brandlink'" if href == current else ""
        items.append(f"<a href='{href}'{class_attr}>{label}</a>")
    items_html = " ".join(items)
    return f"<div class='topnav'><a class='brandlink' href='/'>Miri Deck</a><nav>{items_html}</nav></div>"


def status_word(state: pocket_soul.RoomState) -> str:
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
    words = body_words()
    whisper = room_voice(state.last_reply)
    presence = f"Feeling {state.mood}. Body {words['temperature']}. The window is open. Today's thread: {state.quest_name}."
    result_html = f"<pre class='screen-content home-result' data-live='result'>{esc(result)}</pre>" if result else ""
    deck = deck_page("/", render_page_template("home-deck.html", {
        "whisper": esc(whisper),
        "presence": esc(presence),
        "today_turn": today_turn_html(state, True),
        "stamp": esc(datetime.now().strftime("%H:%M:%S")),
        "recent_relics": recent_relics_html(state),
        "result_html": result_html,
    }), partial, surface)
    if deck:
        return deck
    content = render_page_template("home-plain.html", {
        "mood_face": esc(pocket_soul.mood_face(state.mood)),
        "status": esc(status_word(state)),
        "whisper": esc(whisper),
        "temperature": esc(words["temperature"]),
        "spirit": esc(words["spirit"]),
        "window": esc(words["window"]),
        "body_presence": esc(words["presence"]),
        "heading": esc(state.heading),
        "quest_name": esc(state.quest_name),
        "quest_prompt": esc(state.quest_prompt),
        "result_html": f"<div class='course-line result'><pre>{esc(result)}</pre></div>" if result else "",
    })
    return page(content, surface)


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
    presence = f"Feeling {state.mood}. Body {words['temperature']}. The window is open. Today's thread: {state.quest_name}."
    return {
        "vitals": f"{words['temperature']} / {words['window']} / {state.latest_relic_text()}",
        "presence": presence,
        "vitals_html": vitals_html,
        "latest": room_voice(state.last_reply) if is_provider_error(state.last_reply) else state.latest_relic_text(),
        "reply": room_voice(state.last_reply),
        "mood": state.mood,
        "today": turn,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "relic_count": len(state.relics),
    }


def flash_payload(wish: str = "") -> dict[str, object]:
    state = pocket_soul.RoomState.load()
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
    state = pocket_soul.RoomState.load()
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
        return page(render_page_template("relic-missing.html", {"total": esc(total)}))
    sigil = pocket_soul.RELIC_SIGILS.get(relic.get("kind", ""), "*")
    prev_link = f"<a href='/relic?id={index - 1}'>Previous</a>" if index > 0 else ""
    next_link = f"<a href='/relic?id={index + 1}'>Next</a>" if index + 1 < total else ""
    action_label = f"{relic.get('kind', '?')} / {relic.get('title', 'Relic')}"
    content = render_page_template("relic-detail.html", {
        "sigil": esc(sigil),
        "title": esc(relic.get("title", "Relic")),
        "kind": esc(relic.get("kind", "?")),
        "time": esc(relic.get("time", "")),
        "note": esc(relic.get("note", "")),
        "index": esc(index),
        "action_label": esc(action_label),
        "prev_link": prev_link,
        "next_link": next_link,
        "display_index": esc(index + 1),
        "total": esc(total),
    })
    return page(content)


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



def page(content: str, surface: str = "web") -> bytes:
    shell_paths = esc(json.dumps([surface_path(item, surface) for item in SHELL_PATHS]))
    template = (TEMPLATE_DIR / "plain-shell.html").read_text(encoding="utf-8")
    html_doc = template.format(
        stylesheet=surface_stylesheet(surface),
        content=content,
        shell_paths=shell_paths,
        script_src=SCRIPT_SRC,
    )
    return html_doc.encode()


def deck_page(path: str, inner: str, partial: bool = False, surface: str = "web") -> bytes | None:
    if partial:
        return inner.encode()
    page_meta = PAGE_BY_PATH.get(path, PAGE_BY_PATH["/"])
    nav_html = "".join(
        f"<a class='nav-item{' is-active' if page.path == path else ''}' href='{surface_path(page.path, surface)}'>"
        f"<span class='nav-icon'>{icon(page.icon)}</span>"
        f"<span class='nav-label'><strong>{page.label}</strong></span></a>"
        for page in PAGES
        if page.nav
    )
    shell = TEMPLATE_DIR / ("board-shell.html" if surface == "board" else "web-shell.html")
    template = shell.read_text(encoding="utf-8")
    shell_paths = [surface_path(item, surface) for item in SHELL_PATHS]
    html_doc = template.format(
        stylesheet=surface_stylesheet(surface),
        page_class=page_meta.page_class,
        home_href=surface_path("/", surface),
        nav=nav_html,
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


def room_page(result: str = "", partial: bool = False, surface: str = "web") -> bytes:
    state = pocket_soul.RoomState.load()
    state.ensure_daily_quest()
    latest_relic = state.latest_relic_text()
    nudge = nudge_preview(state)
    relics = state.relic_shelf(5)
    note_lines = "\n".join(f"- {item}" for item in state.notes[-6:]) or "No pinned notes."
    reply = room_voice(state.last_reply)
    deck = deck_page("/room", render_page_template("room-deck.html", {
        "reply": esc(reply),
        "recent_relic_charms": recent_relic_charms(state),
        "robot_image": robot_image(state),
        "today_turn": today_turn_html(state),
        "icon_knock": icon("knock"),
        "icon_nudge": icon("nudge"),
        "icon_hunt": icon("hunt"),
        "icon_wheel": icon("wheel"),
        "icon_craft": icon("craft"),
        "result": esc(result or latest_relic),
        "nudge": esc(nudge),
    }), partial, surface)
    if deck:
        return deck
    content = render_page_template("room-plain.html", {
        "nav": nav("/room"),
        "latest_postcard": esc(latest_postcard()),
        "quest_name": esc(state.quest_name),
        "quest_prompt": esc(state.quest_prompt),
        "mood_face": esc(pocket_soul.mood_face(state.mood)),
        "mood": esc(state.mood),
        "last_reply": esc(state.last_reply),
        "relics": esc(relics),
        "note_lines": esc(note_lines),
        "latest_relic": esc(latest_relic),
        "latest_bottle": esc(latest_bottle()),
        "result": esc(result or "The room is quietly lit."),
    })
    return page(content, surface)


def route_page(path: str, partial: bool = False, surface: str = "web") -> bytes:
    renderer = PAGE_RENDERERS.get(path, doorstep)
    return renderer(partial=partial, surface=surface)


def body_page(partial: bool = False, surface: str = "web") -> bytes:
    state = pocket_soul.RoomState.load()
    words = body_words()
    values = {
        "temperature": esc(words["temperature"]),
        "raw_temp": esc(words["raw_temp"]),
        "load": esc(words["load"]),
        "window": esc(words["window"]),
        "net": esc(words["net"]),
        "presence": esc(words["presence"]),
        "spirit": esc(words["spirit"]),
        "uptime": esc(words["uptime"]),
        "disk": esc(words["disk"]),
        "robot_image": robot_image(state),
        "notes_count": esc(len(state.notes)),
        "relic_count": esc(len(state.relics)),
    }
    deck = deck_page("/body", render_page_template("body-deck.html", values), partial, surface)
    if deck:
        return deck
    values = values | {"nav": nav("/body"), "body_text": esc(pocket_soul.body_text())}
    content = render_page_template("body-plain.html", values)
    return page(content, surface)


def notes_page(partial: bool = False, surface: str = "web") -> bytes:
    state = pocket_soul.RoomState.load()
    pinned_notes = state.notes[-12:]
    note_lines = "\n".join(f"- {item}" for item in pinned_notes) or "No pinned notes in the room yet."
    relic_lines = "\n".join(
        f"{item.get('time', '')} / {item.get('kind', '')} / {item.get('title', '')}"
        for item in state.relics[-10:][::-1]
    ) or "No relics yet."
    values = {
        "last_visit": esc(state.last_visit or "No one has visited yet."),
        "room_voice": esc(room_voice(state.last_reply)),
        "recent_relic_charms": recent_relic_charms(state, 6),
        "note_lines": esc(note_lines),
        "relic_lines": esc(relic_lines),
        "last_reply": esc(state.last_reply),
    }
    deck = deck_page("/notes", render_page_template("notes-deck.html", values), partial, surface)
    if deck:
        return deck
    content = render_page_template("notes-plain.html", values | {
        "nav": nav("/notes"),
        "latest_nightly": esc(latest_nightly()),
    })
    return page(content, surface)


def stash_page(partial: bool = False, surface: str = "web") -> bytes:
    state = pocket_soul.RoomState.load()
    stash_text = state.stash_view(12)
    values = {
        "spark": esc(state.spark),
        "hunt_streak": esc(state.hunt_streak),
        "stash_text": esc(stash_text),
        "icon_hunt": icon("hunt"),
        "icon_wheel": icon("wheel"),
        "icon_craft": icon("craft"),
        "shelf_objects": shelf_objects_html(state, 12),
        "stash_grid": stash_html(state, 12, True),
    }
    deck = deck_page("/stash", render_page_template("stash-deck.html", values), partial, surface)
    if deck:
        return deck
    content = render_page_template("stash-plain.html", values | {"nav": nav("/stash")})
    return page(content, surface)


def badges_page(partial: bool = False, surface: str = "web") -> bytes:
    state = pocket_soul.RoomState.load()
    badge_text = state.badges_view()
    lit = sum(1 for _name, _note, unlocked in state.badge_rows() if unlocked)
    total = len(state.badge_rows())
    values = {
        "lit": esc(lit),
        "total": esc(total),
        "badge_text": esc(badge_text),
        "badges_grid": badges_html(state),
    }
    deck = deck_page("/badges", render_page_template("badges-deck.html", values), partial, surface)
    if deck:
        return deck
    content = render_page_template("badges-plain.html", values | {"nav": nav("/badges")})
    return page(content, surface)


def ritual_page(result: str = "", partial: bool = False, surface: str = "web") -> bytes:
    state = pocket_soul.RoomState.load()
    values = {
        "quest_name": esc(state.quest_name),
        "quest_prompt": esc(state.quest_prompt),
        "result": esc(result or "No new ritual yet."),
    }
    deck = deck_page("/ritual", render_page_template("ritual-deck.html", values), partial, surface)
    if deck:
        return deck
    content = render_page_template("ritual-plain.html", values | {"nav": nav("/ritual")})
    return page(content, surface)


def settings_page(partial: bool = False, surface: str = "web") -> bytes:
    state = pocket_soul.RoomState.load()
    words = body_words()
    service = "online" if words.get("presence") == "reachable" else "offline"
    values = {
        "service": esc(service),
        "notes_count": esc(len(state.notes)),
        "relic_count": esc(len(state.relics)),
        "net": esc(words["net"]),
        "uptime": esc(words["uptime"]),
    }
    deck = deck_page("/settings", render_page_template("settings-deck.html", values), partial, surface)
    if deck:
        return deck
    return page(render_page_template("settings-plain.html", values | {"nav": nav("/settings")}), surface)


PAGE_RENDERERS = {
    "/": doorstep,
    "/room": room_page,
    "/body": body_page,
    "/notes": notes_page,
    "/stash": stash_page,
    "/badges": badges_page,
    "/ritual": ritual_page,
    "/settings": settings_page,
}


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
            return WebResponse(relic_page(index) if include_body else b"")
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
            return WebResponse(route_page(path, partial=ctx.partial, surface=surface) if include_body else b"")
        return WebResponse(doorstep(surface=surface) if include_body else b"")

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
        if path in {"/ritual", "/quest", "/postcard", "/nightly", "/bottle", "/bridge-flash", "/today"}:
            self._send(ritual_page(result))
            return
        if path == "/note":
            self._send(notes_page())
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
