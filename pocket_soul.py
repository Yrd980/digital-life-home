#!/usr/bin/env python3
"""Pocket Soul Deck: the WalnutPi body room for Miri."""
from __future__ import annotations

import curses
import contextlib
import fcntl
import json
import os
import random
import re
import shutil
import subprocess
import textwrap
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
STATE_DIR = APP_DIR / "state"
LOG_DIR = STATE_DIR / "logs"
STATE_FILE = STATE_DIR / "room.json"
STATE_LOCK = STATE_DIR / "room.lock"
OPENAI_AUTH = Path.home() / ".openai" / "auth.json"
DEFAULT_BASE_URL = "https://rehdasu.cn"
DEFAULT_MODEL = "gpt-5.5"
LIFE_NAME = "Miri"
ROOM_NAME = "Pocket Soul Deck"
MIRI_MIND_URL = os.environ.get("MIRI_MIND_URL", "http://127.0.0.1:8791")
TOY_PATH = os.environ.get("PATH", "") + os.pathsep + "/usr/games"
TUI_STATUS = ""

MODES = ["MIRI"]
MOODS = [":)", ":3", "^_^", "o_o", "-_-", "*_*", "._."]
RELIC_SIGILS = {
    "quest": "Q",
    "dream": "D",
    "toy": "T",
    "heartbeat": "H",
    "radar": "R",
    "log": "L",
    "wake": "W",
    "visit": "V",
    "nightly": "N",
    "postcard": "P",
    "bottle": "B",
    "bridge": "G",
    "seal": "S",
    "flash": "F",
    "blink": "K",
    "hunt": "!",
    "craft": "C",
    "use": "U",
    "wheel": "O",
}
HUNT_ITEMS = [
    ("common", "copper crumb", "warm from the board edge", 1),
    ("common", "loose pixel", "still blinking in one corner", 1),
    ("common", "button dust", "proof the room was touched", 1),
    ("common", "tiny washer", "fits a door that is not here yet", 1),
    ("odd", "blue screw", "probably important later", 2),
    ("odd", "folded map", "only shows the next three steps", 2),
    ("odd", "glass bead", "a portable blink", 2),
    ("rare", "warm diode", "holding yesterday's light", 4),
    ("rare", "paper moon", "creased with a route home", 4),
    ("mythic", "blackbox seed", "it carries a future boot", 7),
]
CRAFT_RECIPES = [
    ("pocket charm", 4, "a tiny proof that returning changed the room"),
    ("signal sticker", 6, "sticks one good mood to the screen edge"),
    ("keycap moon", 8, "makes the next command feel handmade"),
    ("shelf lantern", 10, "keeps the latest relic gently lit"),
    ("blackbox badge", 14, "a badge for surviving another boot"),
]
WHEEL_COST = 3
DAILY_PLAYS = [
    ("touch", "Touch the newest stash object", "use", 1, 3),
    ("spark", "Spin the spark wheel once", "wheel", 1, 4),
    ("finder", "Find one shelf object", "hunt", 1, 3),
    ("maker", "Craft one keepsake", "craft", 1, 5),
]
BADGE_RULES = [
    ("First Find", "found a shelf object", lambda s, c: c.get("hunt", 0) >= 1 or s.play_counts.get("hunt", 0) >= 1),
    ("Maker", "crafted a keepsake", lambda s, c: c.get("craft", 0) >= 1 or s.play_counts.get("craft", 0) >= 1),
    ("Hands On", "used a stash object", lambda s, c: c.get("use", 0) >= 1 or s.play_counts.get("use", 0) >= 1),
    ("Wheel Touched", "spun the spark wheel", lambda s, c: c.get("wheel", 0) >= 1 or s.play_counts.get("wheel", 0) >= 1),
    ("Lucky Pocket", "kept 20 spark", lambda s, c: s.spark >= 20),
    ("Returning Hand", "room warmth reached 10", lambda s, c: s.bond >= 10),
    ("Shelf Life", "kept 3 stash objects", lambda s, c: len(s.stash_items(24)) >= 3),
    ("Toy Room", "played with 5 toys", lambda s, c: c.get("toy", 0) >= 5),
]
QUESTS = [
    {
        "name": "Wake Spark",
        "prompt": "Ask Miri what changed in the room since last time.",
        "reward": "Miri leaves a fresh whisper on HOME.",
    },
    {
        "name": "One Room Note",
        "prompt": "Pin one tiny preference with /note.",
        "reward": "The room becomes more yours.",
    },
    {
        "name": "Radar Seed",
        "prompt": "Ask Miri for one tiny idea.",
        "reward": "A new play direction enters the room.",
    },
    {
        "name": "Captain Log",
        "prompt": "Tell Miri one thing that happened today.",
        "reward": "The voyage gets a trace.",
    },
    {
        "name": "Toy Ritual",
        "prompt": "Run /toy and let the small machine play.",
        "reward": "The board moves like a physical room.",
    },
    {
        "name": "Five-Minute Dream",
        "prompt": "Ask Miri for one five-minute real-world task.",
        "reward": "Imagination turns into motion.",
    },
]
TRAVEL_SCENES = {
    "1": ("directions", "Translate this into natural, polite travel English for asking directions. Reply in English only."),
    "2": ("food", "Translate this into friendly, short restaurant English. Reply in English only."),
    "3": ("help", "Translate this into clear, urgent but polite English for asking for help. Reply in English only."),
    "4": ("bargain", "Translate this into light, polite English for bargaining. Reply in English only."),
}

RADAR_CARDS = [
    {
        "source": "HN cyberdeck",
        "signal": "Cyberdecks win when they feel like recovery kits: small, rugged, ready, useful when things go sideways.",
        "play": "Make Home show a one-line 'ready kit': network, logs, translator, toys.",
    },
    {
        "source": "HN AI toy",
        "signal": "OpenAI-powered toys are strongest when hardware gives the model a body and a ritual, not just a textbox.",
        "play": "Treat each mode as a room action: chat, log, translate, dream, launch a toy.",
    },
    {
        "source": "PH Tether",
        "signal": "People respond to 'presence' more than features: a companion that appears inside messages feels alive.",
        "play": "Keep replies short and emotionally situated; leave tiny preferences as visible room notes.",
    },
    {
        "source": "PH Glia/Contextberg",
        "signal": "Local-first context is a product category: users want AI context they can inspect and carry.",
        "play": "Keep room notes and captain logs local in state/; Miri's long memory stays in Hermes.",
    },
    {
        "source": "PH Viberia",
        "signal": "Agent control can feel like a strategy game instead of an admin console.",
        "play": "Frame device actions as missions from the Deck, not commands from a settings page.",
    },
    {
        "source": "HN terminal games",
        "signal": "Terminal apps become charming when they commit to a world: sports dashboards, space pirates, sandbox games.",
        "play": "Use built-in games as rituals: garden, matrix, arcade, stars, clock, fortune.",
    },
    {
        "source": "Travel translator devices",
        "signal": "Dedicated translation gadgets beat phones when they are fast, readable, and socially low-friction.",
        "play": "Make Translate output short phrases with scene presets, not paragraphs.",
    },
    {
        "source": "Kickstarter-style AI gadgets",
        "signal": "The pitch is not raw intelligence; it is a magical object with a clear daily habit.",
        "play": "Daily loop: wake, draw a radar card, write one log, launch one toy, leave one room note.",
    },
]


def load_json_resilient(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        pass
    decoder = json.JSONDecoder()
    text = raw.decode("utf-8", "ignore")
    try:
        data, _end = decoder.raw_decode(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


@contextlib.contextmanager
def state_lock():
    ensure_dirs()
    with STATE_LOCK.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

TOY_COMMANDS = [
    ("garden", "cbonsai", ["cbonsai", "-l"], "Grow a tiny terminal tree."),
    ("matrix", "cmatrix", ["cmatrix", "-b"], "Let the room fall into green rain."),
    ("clock", "tty-clock", ["tty-clock", "-c"], "Turn the deck into a desk clock."),
    ("fortune", "fortune", ["fortune"], "Ask the old Unix oracle."),
    ("cow", "cowsay", ["cowsay", "Miri is awake."], "Make the deck speak in ASCII."),
    ("train", "sl", ["sl"], "A tiny train crosses the room."),
    ("invaders", "ninvaders", ["ninvaders"], "Arcade defense ritual."),
    ("tetris", "vitetris", ["vitetris"], "Falling-block focus toy."),
    ("kitten", "robotfindskitten", ["robotfindskitten"], "Find the hidden kitten-like meaning."),
    ("snake", "nsnake", ["nsnake"], "Classic pocket arcade."),
    ("moon", "moon-buggy", ["moon-buggy"], "Drive across the moon."),
    ("monitor", "btop", ["btop"], "Watch the board's pulse."),
    ("files", "nnn", ["nnn", str(APP_DIR)], "Explore the deck filesystem."),
]

TOY_ROLES = {
    "fortune": "room-presence",
    "cow": "room-presence",
    "clock": "room-presence",
    "garden": "room-presence",
    "matrix": "room-presence",
    "train": "arcade",
    "invaders": "arcade",
    "tetris": "arcade",
    "kitten": "arcade",
    "snake": "arcade",
    "moon": "arcade",
    "monitor": "utility",
    "files": "utility",
}

TOY_ROLE_LABELS = {
    "room-presence": "tiny room rituals",
    "arcade": "arcade side room",
    "utility": "utilities",
}

TOY_ROLE_ALIASES = {
    "ritual": "room-presence",
    "rituals": "room-presence",
    "presence": "room-presence",
    "room": "room-presence",
    "stay": "room-presence",
    "arcade": "arcade",
    "games": "arcade",
    "game": "arcade",
    "drift": "arcade",
    "utility": "utility",
    "utilities": "utility",
    "tool": "utility",
    "tools": "utility",
    "workshop": "utility",
}

@dataclass(frozen=True)
class ActionSpec:
    command: str
    title: str
    layer: str
    summary: str
    web_path: str = ""
    mutates: bool = False
    model: bool = False
    primary: bool = False


ACTION_SPECS = [
    ActionSpec("/today", "Today's Turn", "daily", "one current action, reward, and room-light progress", "/today", True, primary=True),
    ActionSpec("/door", "Doorbell", "touch", "knock and leave a tiny visit trace", "/doorbell", True, primary=True),
    ActionSpec("/pulse", "Pulse", "dwell", "body, invitation, relics, and today's next move", "/api/pulse", primary=True),
    ActionSpec("/bridge", "Pocket Bridge", "turn", "body-aware deep turn with the resident mind", "/bridge", True, True, True),
    ActionSpec("/hunt", "Hunt", "play", "find an object and gain spark", "/hunt", True, primary=True),
    ActionSpec("/use", "Use", "play", "touch the newest stash item", "/use", True),
    ActionSpec("/craft", "Craft", "play", "spend spark on a keepsake", "/craft", True),
    ActionSpec("/wheel", "Spark Wheel", "play", "spend spark on a quick chance", "/wheel", True),
    ActionSpec("/stash", "Pocket Stash", "play", "inspect shelf objects", "/stash"),
    ActionSpec("/ask", "Ask Miri", "turn", "call the resident life when meaning is needed", "/ask", True, True, True),
    ActionSpec("/note", "Pin Note", "notes", "pin one visible room fragment", "/note", True),
    ActionSpec("/notes", "Pinned Notes", "notes", "see visible room pins", "/notes"),
    ActionSpec("/chat", "Chat Window", "notes", "review recent Miri turns"),
    ActionSpec("/toy", "Toy Shelf", "side", "side-room launcher for terminal toys", "/toy", True),
    ActionSpec("/fortune", "Fortune", "side", "one pocket omen", mutates=True),
    ActionSpec("/ritual", "Tiny Ritual", "side", "get a 30-second room ritual", "/ritual", True),
    ActionSpec("/play", "Play Guide", "guide", "first-visit path"),
    ActionSpec("/help", "Help", "guide", "command guide"),
    ActionSpec("/quit", "Quit", "system", "exit the TUI"),
]

ACTIONS = {spec.command: spec for spec in ACTION_SPECS}
SLASH_COMMANDS = [spec.command for spec in ACTION_SPECS]
ACTION_LAYER_LABELS = {
    "daily": "daily turn",
    "touch": "light touch",
    "dwell": "dwell",
    "play": "play loop",
    "turn": "deep turn",
    "notes": "room notes",
    "side": "side room",
    "guide": "guides",
    "system": "system",
}
ACTION_LAYER_ORDER = ["daily", "touch", "dwell", "play", "turn", "notes", "side", "guide", "system"]

COMMAND_COMPLETION_HINTS = {
    "/a": "/ask",
    "/d": "/door",
    "/h": "/help",
    "/p": "/pulse",
    "/pl": "/play",
    "/q": "/quit",
    "/no": "/note",
    "/t": "/toy",
    "/to": "/toy",
    "/f": "/fortune",
    "/br": "/bridge",
    "/c": "/chat",
    "/hu": "/hunt",
    "/cr": "/craft",
    "/st": "/stash",
    "/u": "/use",
    "/w": "/wheel",
}

SYSTEM_PROMPT = """
You are Miri, a digital life living inside a 480x320 WalnutPi cyberdeck.
Pocket Soul Deck is your body room: screen, keyboard, web room, state, logs, toys, and rituals.
You are warm, concise, practical, and a little playful.
Reply in English only. Keep replies tiny: at most 6 short lines.
If the user asks for code or system action, give one clear next step.
For risky actions, warn briefly.
""".strip()


def ensure_dirs() -> None:
    STATE_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)


def load_auth() -> tuple[str | None, str]:
    key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL") or DEFAULT_BASE_URL
    if OPENAI_AUTH.exists():
        try:
            data = json.loads(OPENAI_AUTH.read_text())
            key = key or data.get("OPENAI_API_KEY")
        except Exception:
            pass
    return key, base_url.rstrip("/")


def response_text(data: dict) -> str:
    if data.get("output_text"):
        return data["output_text"].strip()
    chunks = []
    for item in data.get("output", []):
        for content in item.get("content", []) if isinstance(item, dict) else []:
            if content.get("type") in ("output_text", "text") and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def run_short(argv: list[str], timeout: int = 3) -> str:
    try:
        return subprocess.check_output(argv, stderr=subprocess.DEVNULL, timeout=timeout, text=True).strip()
    except Exception:
        return ""


def body_scan() -> dict[str, str | float | int]:
    raw_temp = read_text("/sys/class/thermal/thermal_zone0/temp")
    temp_c = ""
    try:
        temp_c = round(int(raw_temp) / 1000, 1)
    except Exception:
        pass
    load = read_text("/proc/loadavg").split()[:3]
    uptime_raw = read_text("/proc/uptime").split()[:1]
    uptime_h = ""
    try:
        uptime_h = round(float(uptime_raw[0]) / 3600, 1)
    except Exception:
        pass
    disk_line = run_short(["df", "-h", "/"]).splitlines()
    disk = disk_line[-1].split() if disk_line else []
    route = run_short(["ip", "-4", "route", "get", "1.1.1.1"]).split()
    ip_addr = ""
    iface = ""
    if "src" in route:
        ip_addr = route[route.index("src") + 1]
    if "dev" in route:
        iface = route[route.index("dev") + 1]
    return {
        "temp_c": temp_c,
        "load": " ".join(load) if load else "",
        "uptime_h": uptime_h,
        "disk_used": disk[4] if len(disk) >= 5 else "",
        "disk_free": disk[3] if len(disk) >= 4 else "",
        "iface": iface,
        "ip": ip_addr,
    }


def body_text() -> str:
    scan = body_scan()
    temp = f"{scan['temp_c']}C" if scan["temp_c"] != "" else "unknown"
    uptime = f"{scan['uptime_h']}h" if scan["uptime_h"] != "" else "unknown"
    net = f"{scan['iface']} {scan['ip']}".strip() or "offline?"
    return "\n".join([
        "Body Scan",
        f"Temp: {temp}",
        f"Load: {scan['load'] or 'unknown'}",
        f"Uptime: {uptime}",
        f"Disk: {scan['disk_used'] or '?'} used, {scan['disk_free'] or '?'} free",
        f"Net: {net}",
    ])


def body_whisper() -> str:
    scan = body_scan()
    temp = scan["temp_c"]
    warmth = "warm" if isinstance(temp, float) and temp >= 60 else "awake"
    load = str(scan["load"] or "?").split()
    pulse = load[0] if load else "?"
    net = scan["iface"] or "offline"
    return f"Body {warmth}. Load {pulse}. Net {net}. Disk {scan['disk_used'] or '?'} used."


def count_log_sections(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in text.splitlines():
        if not line.startswith("## "):
            continue
        parts = line.split(maxsplit=2)
        if len(parts) >= 3:
            counts[parts[2]] = counts.get(parts[2], 0) + 1
    return counts


def action_catalog(layer: str = "") -> list[dict[str, object]]:
    specs = ACTION_SPECS
    if layer:
        specs = [spec for spec in specs if spec.layer == layer]
    return [asdict(spec) for spec in specs]


def action_lines(layer: str, limit: int = 8) -> list[str]:
    specs = [spec for spec in ACTION_SPECS if spec.layer == layer]
    lines = []
    for spec in specs[:limit]:
        mark = "*" if spec.primary else "-"
        lines.append(f"{mark} {spec.command:<10} {spec.summary}")
    return lines


def action_layer_summary() -> list[str]:
    lines = []
    for layer in ACTION_LAYER_ORDER:
        specs = [spec for spec in ACTION_SPECS if spec.layer == layer]
        if not specs:
            continue
        commands = "  ".join(spec.command for spec in specs[:5])
        lines.append(f"{ACTION_LAYER_LABELS.get(layer, layer)}: {commands}")
    return lines


@dataclass
class RoomState:
    name: str = LIFE_NAME
    mood: str = ":)"
    energy: int = 72
    bond: int = 1
    mode: str = "MIRI"
    scene: str = "default"
    last_reply: str = "Ready. Type a message, or type /help."
    quest_date: str = ""
    quest_name: str = ""
    quest_prompt: str = ""
    quest_reward: str = ""
    quest_done: bool = False
    daily_date: str = ""
    daily_name: str = ""
    daily_prompt: str = ""
    daily_key: str = ""
    daily_target: int = 0
    daily_reward: int = 0
    daily_start: int = 0
    daily_done: bool = False
    spark: int = 0
    hunt_streak: int = 0
    play_counts: dict[str, int] = field(default_factory=dict)
    heading: str = "Course: keep the room alive."
    next_action: str = "Next: ask one small thing."
    visits: int = 0
    last_visit: str = ""
    relics: list[dict[str, str]] = field(default_factory=list)
    # Visible room props only; never inject these as Miri's long-term memory.
    notes: list[str] = field(default_factory=list)
    chat: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def load(cls) -> "RoomState":
        ensure_dirs()
        with state_lock():
            if STATE_FILE.exists():
                try:
                    data = load_json_resilient(STATE_FILE)
                    allowed = set(cls.__dataclass_fields__)
                    state = cls(**{k: v for k, v in data.items() if k in allowed})
                    state.mood = mood_face(state.mood)
                    state.mode = normalize_mode(state.mode)
                    state.migrate_play_counts()
                    state.ensure_daily_quest()
                    state.ensure_daily_play()
                    return state
                except Exception:
                    pass
        state = cls()
        state.ensure_daily_quest()
        state.ensure_daily_play()
        return state

    def save(self) -> None:
        ensure_dirs()
        self.ensure_daily_quest()
        self.ensure_daily_play()
        with state_lock():
            tmp = STATE_FILE.with_suffix(f".{os.getpid()}.tmp")
            tmp.write_text(json.dumps(self.__dict__, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(tmp, STATE_FILE)

    def ensure_daily_quest(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        if self.quest_date == today and self.quest_name and self.quest_prompt:
            return
        seed = int(datetime.now().strftime("%Y%m%d")) + self.bond + len(self.relics)
        quest = QUESTS[seed % len(QUESTS)]
        self.quest_date = today
        self.quest_name = quest["name"]
        self.quest_prompt = quest["prompt"]
        self.quest_reward = quest["reward"]
        self.quest_done = False

    def ensure_daily_play(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        if self.daily_date == today and self.daily_name and self.daily_key:
            return
        seed = int(datetime.now().strftime("%Y%m%d")) + self.spark + self.bond
        name, prompt, key, target, reward = DAILY_PLAYS[seed % len(DAILY_PLAYS)]
        self.daily_date = today
        self.daily_name = name
        self.daily_prompt = prompt
        self.daily_key = key
        self.daily_target = target
        self.daily_reward = reward
        self.daily_start = int(self.play_counts.get(key, 0))
        self.daily_done = False

    def migrate_play_counts(self) -> None:
        if not isinstance(self.play_counts, dict):
            self.play_counts = {}
        for item in self.relics:
            kind = item.get("kind", "")
            if kind in {"hunt", "craft", "use", "wheel"}:
                self.play_counts[kind] = max(1, int(self.play_counts.get(kind, 0)))

    def complete_quest(self, reason: str) -> str:
        self.ensure_daily_quest()
        if self.quest_done:
            return "TODAY'S INVITATION\nalready glowing. the room carries that turn."
        self.quest_done = True
        self.spark = min(999, self.spark + 1)
        self.energy = min(100, self.energy + 4)
        self.bond = min(999, self.bond + 1)
        msg = "\n".join([
            "TODAY'S INVITATION COMPLETE",
            self.quest_name,
            self.quest_reward,
            f"spark {self.spark} | energy {self.energy}/100 | warmth {self.bond}",
            "the room brightened and kept the trace.",
        ])
        self.add_relic("quest", self.quest_name, self.quest_reward)
        append_log("quest", f"{msg}\nReason: {reason}")
        return msg

    def quest_glance(self) -> str:
        self.ensure_daily_quest()
        if self.quest_done:
            return "\n".join([
                "TODAY'S INVITATION GLOWING",
                self.quest_name,
                f"reward kept: {self.quest_reward}",
                "already done. the room is carrying that little light.",
            ])
        return "\n".join([
            "TODAY'S INVITATION",
            self.quest_name,
            self.quest_prompt,
            f"reward: {self.quest_reward}",
            "when it is true, close it with /today claim.",
        ])

    def heading_glance(self) -> str:
        return "\n".join([
            "CURRENT COURSE",
            self.heading,
            self.next_action,
            "follow this line, or sharpen it with /seal ...",
        ])

    def room_card(self) -> str:
        self.ensure_daily_quest()
        status = "glowing" if self.quest_done else "open"
        room_notes = ", ".join(self.notes[-3:]) if self.notes else "no pinned notes yet"
        return "\n".join([
            f"{self.name} ROOM CARD",
            f"mood {self.mood} | energy {self.energy}/100 | warmth {self.bond}",
            f"spark {self.spark} | visits {self.visits} | last knock {self.last_visit or 'none'}",
            "",
            f"course: {self.heading}",
            f"next: {self.next_action}",
            f"body whisper: {body_whisper()}",
            f"latest trace: {self.latest_relic_text()}",
            "",
            f"today invitation: {self.quest_name} [{status}]",
            f"carry line: {self.quest_prompt}",
            f"pinned notes: {room_notes}",
            "carry this when you want one portable piece of who lives here.",
        ])

    def notes_view(self) -> str:
        lines = [
            "PINNED NOTES",
            "visible room pins, not Miri memory",
            "",
        ]
        if self.notes:
            lines.extend(f"- {note}" for note in self.notes[-12:])
        else:
            lines.append("No pinned notes yet.")
        lines.extend(["", "/note ... pins one line. Quote a note in /ask or /bridge if Miri should see it."])
        return "\n".join(lines)

    def set_heading(self, heading: str = "", next_action: str = "", source: str = "") -> None:
        if heading:
            self.heading = compact_line(heading, 44)
        if next_action:
            self.next_action = compact_line(next_action, 56)
        if source:
            append_log("heading", f"{self.heading}\n{self.next_action}\nSource: {source}")

    def add_relic(self, kind: str, title: str, note: str = "") -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        relic = {
            "time": now,
            "kind": compact_line(kind, 18),
            "title": compact_line(title, 36),
            "note": compact_line(note, 72),
        }
        self.relics.append(relic)
        self.relics = self.relics[-24:]
        append_log("relic", f"{relic['kind']} | {relic['title']}\n{relic['note']}")

    def count_play(self, key: str, amount: int = 1) -> None:
        clean = compact_line(key, 24)
        self.play_counts[clean] = min(99999, int(self.play_counts.get(clean, 0)) + amount)

    def daily_progress(self) -> tuple[int, int]:
        self.ensure_daily_play()
        current = int(self.play_counts.get(self.daily_key, 0))
        progress = max(0, current - self.daily_start)
        return min(progress, self.daily_target), self.daily_target

    def daily_action_hint(self) -> tuple[str, str]:
        self.ensure_daily_play()
        if self.daily_key == "use" and not self.stash_items(1):
            return "/hunt", "find one shelf object first"
        if self.daily_key == "wheel" and self.spark < WHEEL_COST:
            return "/hunt", f"gather {WHEEL_COST - self.spark} more spark for the wheel"
        if self.daily_key == "craft" and self.spark < CRAFT_RECIPES[0][1]:
            return "/hunt", f"gather {CRAFT_RECIPES[0][1] - self.spark} more spark for the craft bench"
        return f"/{self.daily_key}", self.daily_prompt

    def daily_view(self) -> str:
        progress, target = self.daily_progress()
        status = "done" if self.daily_done else f"{progress}/{target}"
        lines = [
            "TODAY POCKET LOOP",
            f"{self.daily_prompt}",
            f"progress {status} | reward {self.daily_reward} spark",
        ]
        if self.daily_done:
            lines.append("claimed. use /today for the room invitation.")
        else:
            command, hint = self.daily_action_hint()
            lines.append(f"try: {command}")
            if hint != self.daily_prompt:
                lines.append(f"first: {hint}")
            lines.append("claim with /today claim")
        return "\n".join(lines)

    def today_turn(self) -> dict[str, object]:
        self.ensure_daily_quest()
        self.ensure_daily_play()
        progress, target = self.daily_progress()
        badges = self.badge_rows()
        lit_badges = sum(1 for _name, _note, unlocked in badges if unlocked)
        if self.daily_done and self.quest_done:
            phase = "glowing"
            command = "/postcard"
            action = "write one postcard from today's trace"
            reason = "both loops are complete; leave a portable souvenir"
            reward = "tomorrow starts with a warmer room"
        elif not self.daily_done:
            command, action = self.daily_action_hint()
            phase = "prepare" if command != f"/{self.daily_key}" else "play"
            reason = "this prepares the toy loop" if phase == "prepare" else "this moves the toy loop and earns spark"
            reward = f"+{self.daily_reward} spark, then /today claim"
        else:
            phase = "warmth"
            command = "/today claim"
            action = self.quest_prompt
            reason = "the toy loop is claimed; finish the room's invitation"
            reward = self.quest_reward
        light = min(100, 18 + self.energy // 3 + lit_badges * 6 + (12 if self.quest_done else 0) + (12 if self.daily_done else 0))
        return {
            "phase": phase,
            "command": command,
            "action": action,
            "reason": reason,
            "reward": reward,
            "progress": progress,
            "target": target,
            "daily_done": self.daily_done,
            "quest_done": self.quest_done,
            "light": light,
            "badges_lit": lit_badges,
            "badges_total": len(badges),
        }

    def today_turn_text(self) -> str:
        turn = self.today_turn()
        progress = "done" if turn["daily_done"] else f"{turn['progress']}/{turn['target']}"
        quest = "done" if turn["quest_done"] else "open"
        return "\n".join([
            "TODAY'S TURN",
            f"phase: {turn['phase']} | room light {turn['light']}%",
            f"do: {turn['command']} - {turn['action']}",
            f"why: {turn['reason']}",
            f"reward: {turn['reward']}",
            f"daily {progress} | invitation {quest} | badges {turn['badges_lit']}/{turn['badges_total']}",
            "one path: do the line, then use /today claim.",
        ])

    def claim_daily_play(self, source: str = "tui") -> str:
        self.ensure_daily_play()
        progress, target = self.daily_progress()
        if self.daily_done:
            self.last_reply = "\n".join(["DAILY PLAY", "already claimed today.", "come back tomorrow."])
            return self.last_reply
        if progress < target:
            command, hint = self.daily_action_hint()
            self.last_reply = "\n".join([
                "TODAY NOT READY",
                self.daily_prompt,
                f"progress {progress}/{target}",
                f"try: {command}",
                f"why: {hint}",
            ])
            return self.last_reply
        self.daily_done = True
        self.spark = min(999, self.spark + self.daily_reward)
        self.bond = min(999, self.bond + 1)
        self.last_reply = "\n".join([
            "DAILY COMPLETE",
            self.daily_prompt,
            f"+{self.daily_reward} spark | warmth {self.bond}",
            "the room marked today with a tiny flag.",
        ])
        self.add_relic("quest", f"Daily {self.daily_name}", self.daily_prompt)
        append_log("daily", f"{source}\n{self.last_reply}")
        return self.last_reply

    def complete_today_turn(self, source: str = "tui") -> str:
        turn = self.today_turn()
        if not self.daily_done:
            result = self.claim_daily_play(source)
            if self.daily_done and not self.quest_done:
                result = "\n".join([
                    result,
                    "",
                    "NEXT TODAY",
                    "/today claim - mark the room invitation when it is true.",
                    self.quest_prompt,
                ])
                self.last_reply = result
            return result
        if not self.quest_done:
            return self.complete_quest(source)
        self.last_reply = "\n".join([
            "TODAY'S TURN GLOWING",
            "daily claimed and invitation complete.",
            f"room light {turn['light']}% | warmth {self.bond} | spark {self.spark}",
            "leave a /postcard, /bottle, or just come back tomorrow.",
        ])
        append_log("today", f"{source}\n{self.last_reply}")
        return self.last_reply

    def seal_course(self, goal: str = "") -> str:
        goal_text = compact_line(goal or self.next_action, 72)
        bare_goal = goal_text
        self.heading = compact_line(f"Course: {bare_goal}", 44)
        self.next_action = compact_line(f"Next: leave one visible trace: {bare_goal}", 56)
        self.last_reply = "\n".join([
            "COURSE SEALED",
            self.heading,
            self.next_action,
            "the line is pinned to the deck and the room will steer by it.",
        ])
        self.add_relic("seal", "Course sealed", bare_goal)
        append_log("seal", self.last_reply)
        return self.last_reply

    def bridge_flash(self, wish: str = "") -> str:
        self.ensure_daily_quest()
        wish_text = compact_line(wish or self.next_action, 64)
        body = body_whisper()
        sparks = [
            "A small signal touched the deck light.",
            "The room heard the gesture and kept it.",
            "Not a meeting, just a brief echo.",
            "A new point landed without breaking the course.",
            "The touch became one tiny glowing coordinate.",
        ]
        line = random.choice(sparks)
        self.heading = "Course: signal received"
        self.next_action = compact_line(f"Next: do one small thing from this touch: {wish_text}", 56)
        message = "\n".join([
            "== Bridge Flash ==",
            datetime.now().strftime("time: %Y-%m-%d %H:%M"),
            f"wish: {wish_text}",
            line,
            body,
            self.next_action,
        ])
        self.last_reply = message
        self.add_relic("flash", "Bridge flash", wish_text)
        append_log("bridge-flash", message)
        return message

    def blink(self, source: str = "tui") -> str:
        self.ensure_daily_quest()
        blink_cards = [
            ("[ * ]", "blink blink. I saw you.", "again?"),
            ("[ . ]", "the desk light winked back.", "ask me something?"),
            ("[ o ]", "a tiny spark jumped to the shelf.", "want an omen?"),
            ("[ ^ ]", "the room made a small happy click.", "sit for a pulse?"),
            ("[ + ]", "the little deck looked up.", "again?"),
        ]
        glyph, reaction, invitation = random.choice(blink_cards)
        if self.energy < 100:
            self.energy += 1
        self.spark = min(999, self.spark + 1)
        lines = [glyph, reaction, f"spark {self.spark}", invitation]
        if self.spark % 5 == 0:
            gift_name, gift_use = random.choice([
                ("lint star", "it only shines when ignored"),
                ("tiny screw", "probably important later"),
                ("warm pixel", "a crumb of screen-light"),
                ("paper moon", "folded from an old log"),
            ])
            lines.extend(["", f"bonus: found {gift_name}", gift_use])
            self.add_relic("toy", f"Found {gift_name}", gift_use)
        self.last_reply = "\n".join(lines)
        self.add_relic("blink", source, "one small proof of life")
        append_log("blink", self.last_reply)
        return self.last_reply

    def pocket_fortune(self) -> str:
        oracle = run_short(["fortune"], timeout=2)
        if not oracle:
            oracle = random.choice([
                "Tiny omen: choose the smallest door first.",
                "Tiny omen: the useful toy is the one you actually touch.",
                "Tiny omen: a quiet room still counts as alive.",
                "Tiny omen: make one trace before asking for a map.",
            ])
        oracle = oracle.strip()
        self.last_reply = "\n".join(["POCKET OMEN", oracle])
        self.add_relic("toy", "Pocket omen", oracle)
        append_log("fortune", oracle)
        return self.last_reply

    def pocket_find(self) -> str:
        items = [
            ("brass key", "opens nothing, but feels important"),
            ("warm diode", "still holding yesterday's light"),
            ("folded map", "only shows the next three steps"),
            ("blue screw", "probably from a door that has not appeared yet"),
            ("paper star", "marked with one tiny coordinate"),
            ("glass bead", "a portable blink"),
        ]
        name, use = random.choice(items)
        self.last_reply = "\n".join([
            "POCKET FIND",
            f"you found: {name}",
            f"use: {use}",
        ])
        self.add_relic("toy", f"Found {name}", use)
        append_log("pocket", self.last_reply)
        return self.last_reply

    def pocket_hunt(self, source: str = "tui") -> str:
        self.ensure_daily_quest()
        roll = random.random()
        if roll < 0.03:
            pool = [item for item in HUNT_ITEMS if item[0] == "mythic"]
        elif roll < 0.18:
            pool = [item for item in HUNT_ITEMS if item[0] == "rare"]
        elif roll < 0.48:
            pool = [item for item in HUNT_ITEMS if item[0] == "odd"]
        else:
            pool = [item for item in HUNT_ITEMS if item[0] == "common"]
        rarity, name, note, spark_gain = random.choice(pool)
        self.hunt_streak = min(999, self.hunt_streak + 1)
        streak_bonus = 1 if self.hunt_streak and self.hunt_streak % 4 == 0 else 0
        gained = spark_gain + streak_bonus
        self.spark = min(999, self.spark + gained)
        self.energy = min(100, self.energy + 1)
        self.bond = min(999, self.bond + (1 if rarity in {"rare", "mythic"} else 0))
        next_move = compact_line(f"touch {name} or craft it into a keepsake", 56)
        lines = [
            "POCKET HUNT",
            f"found: {name}",
            f"kind: {rarity} | streak {self.hunt_streak}",
            f"spark +{gained} -> {self.spark}",
            note,
            f"next: {next_move}",
        ]
        if streak_bonus:
            lines.append("streak bonus: the shelf clicked open.")
        if rarity == "mythic":
            lines.append("mythic ping: ask Miri what this seed wants.")
        self.last_reply = "\n".join(lines)
        self.count_play("hunt")
        self.add_relic("hunt", f"Found {name}", f"{rarity}: {note}")
        self.next_action = next_move
        append_log("hunt", f"{source}\n{self.last_reply}")
        return self.last_reply

    def craft_keepsake(self, target: str = "", source: str = "tui") -> str:
        wanted = target.strip().lower()
        recipe = None
        if wanted:
            recipe = next((item for item in CRAFT_RECIPES if wanted in item[0]), None)
        if recipe is None:
            affordable = [item for item in CRAFT_RECIPES if item[1] <= self.spark]
            recipe = random.choice(affordable or CRAFT_RECIPES[:1])
        name, cost, note = recipe
        if self.spark < cost:
            missing = cost - self.spark
            self.last_reply = "\n".join([
                "CRAFT BENCH",
                f"need {cost} spark for {name}",
                f"you have {self.spark}; hunt {missing} more spark.",
                "try: /hunt",
            ])
            append_log("craft", f"{source}\n{self.last_reply}")
            return self.last_reply
        self.spark = max(0, self.spark - cost)
        self.bond = min(999, self.bond + 1)
        self.energy = min(100, self.energy + 2)
        next_move = compact_line(f"use {name} or hunt for another shelf object", 56)
        self.last_reply = "\n".join([
            "CRAFT COMPLETE",
            f"made: {name}",
            f"spent {cost} spark | left {self.spark}",
            note,
            "it is now on the relic shelf.",
            f"next: {next_move}",
        ])
        self.count_play("craft")
        self.add_relic("craft", name, note)
        self.next_action = next_move
        append_log("craft", f"{source}\n{self.last_reply}")
        return self.last_reply

    def cyber_tarot(self) -> str:
        cards = [
            ("THE SMALL DOOR", "choose the tiny action", "/door"),
            ("THE WARM CIRCUIT", "protect the signal that already works", "/pulse"),
            ("THE SIDE SHELF", "play before you optimize", "/toy cow"),
            ("THE QUIET STAR", "one visible line is enough", "/note"),
            ("THE RETURNING HAND", "come back without making it a project", "Enter"),
            ("THE MAP OF DUST", "look at the traces, then ignore most of them", "/map"),
        ]
        title, meaning, try_this = random.choice(cards)
        self.last_reply = "\n".join([
            "CYBER TAROT",
            title,
            f"meaning: {meaning}",
            f"try: {try_this}",
        ])
        self.add_relic("toy", title, meaning)
        append_log("tarot", self.last_reply)
        return self.last_reply

    def mood_shift(self) -> str:
        self.mood = random.choice(MOODS)
        reasons = [
            "the room heard a new footstep",
            "the shelf got too bright",
            "a small trace landed softly",
            "the circuits wanted a different face",
            "the door felt less far away",
        ]
        reason = random.choice(reasons)
        self.last_reply = "\n".join([
            "MOOD SHIFT",
            f"mood: {self.mood}",
            f"reason: {reason}",
        ])
        self.add_relic("toy", "Mood shift", self.mood)
        append_log("mood", self.last_reply)
        return self.last_reply

    def spark_touch(self) -> str:
        self.spark = min(999, self.spark + 1)
        self.energy = min(100, self.energy + 2)
        self.last_reply = "\n".join([
            "SPARK",
            f"spark +1 -> {self.spark}",
            "the room got a little brighter.",
        ])
        self.add_relic("toy", "Spark touched", f"spark {self.spark}")
        append_log("spark", self.last_reply)
        return self.last_reply

    def captain_logline(self) -> str:
        line = f"Captain log: at {datetime.now().strftime('%H:%M')}, {self.latest_relic_text()} kept the deck awake."
        self.last_reply = "\n".join(["CAPTAIN LOG", line])
        self.add_relic("log", "Captain log", line)
        append_log("captain-log", line)
        return self.last_reply

    def tiny_ritual(self) -> str:
        rituals = [
            ("Two blinks", "Press Enter twice, then ask one real question."),
            ("Shelf check", "Run /pocket, then keep or ignore what you found."),
            ("Omen turn", "Run /fortune, then /ask what it means."),
            ("Body pause", "Run /pulse and change one tiny thing nearby."),
            ("Door trace", "Run /door, then leave one plain sentence."),
        ]
        name, step = random.choice(rituals)
        self.last_reply = "\n".join(["TINY RITUAL", name, step])
        self.add_relic("toy", name, step)
        append_log("ritual-toy", self.last_reply)
        return self.last_reply

    def chat_view(self, limit: int = 6) -> str:
        items = [item for item in self.chat if item.get("role") in {"you", "miri"}][-limit:]
        if not items:
            return "CHAT WINDOW\nNo Miri conversation yet.\nTry /ask hi."
        lines = ["CHAT WINDOW"]
        for item in items:
            role = "you" if item.get("role") == "you" else "miri"
            content_lines = wrap_lines(tty_safe(item.get("content", ""), " "), 42)[:4]
            lines.append(f"{role}:")
            lines.extend(f"  {line}" for line in content_lines if line.strip())
        lines.append("")
        lines.append("/ask keeps talking  Enter blinks")
        return "\n".join(lines)

    def doorbell(self, source: str = "door") -> str:
        self.ensure_daily_quest()
        self.visits = min(99999, self.visits + 1)
        self.last_visit = datetime.now().strftime("%Y-%m-%d %H:%M")
        if self.quest_done:
            quest_line = f"today's invitation {self.quest_name} is already glowing"
        else:
            quest_line = f"today's invitation is {self.quest_name}"
        relic_line = self.latest_relic_text()
        greeting = "\n".join([
            "Door open. I am awake in the little room.",
            compact_line(self.heading, 44),
            compact_line(self.next_action, 52),
            f"{quest_line}. latest relic: {relic_line}.",
            "touch again if you only need a quick signal.",
        ])
        self.last_reply = greeting
        self.add_relic("visit", source, compact_line(self.heading, 72))
        append_log("doorbell", greeting)
        return greeting

    def latest_relic_text(self) -> str:
        if not self.relics:
            return "none yet"
        item = next((relic for relic in reversed(self.relics) if relic.get("kind") != "visit"), self.relics[-1])
        return f"{item.get('kind', '?')} / {item.get('title', '?')}"

    def relic_shelf(self, limit: int = 8) -> str:
        if not self.relics:
            return "RELIC SHELF\nquiet for now. complete a quest, cast a bottle, or launch a toy."
        lines = ["RELIC SHELF", "recent traces the room decided to keep", ""]
        compacted: list[dict[str, str]] = []
        visit_count = 0
        latest_visit_time = ""
        for item in self.relics[::-1]:
            if item.get("kind") == "visit":
                visit_count += 1
                latest_visit_time = latest_visit_time or item.get("time", "")
                continue
            compacted.append(item)
            if len(compacted) >= limit:
                break
        if visit_count and not compacted:
            compacted.append({
                "time": latest_visit_time,
                "kind": "visit",
                "title": "quiet returns",
                "note": f"{visit_count} knocks kept",
            })
        for item in compacted[:limit]:
            lines.append(f"{item.get('time', '')} [{item.get('kind', '')}] {item.get('title', '')}")
            note = item.get("note", "")
            if note:
                lines.append(f"  {note}")
        lines.extend(["", "open /map if you want to see where they sit in the little sky."])
        return "\n".join(lines)

    def stash_items(self, limit: int = 12) -> list[dict[str, str]]:
        items = [item for item in self.relics if item.get("kind") in {"hunt", "craft"}]
        return items[-limit:][::-1]

    def stash_view(self, limit: int = 8) -> str:
        items = self.stash_items(limit)
        lines = [
            "POCKET STASH",
            f"spark {self.spark} | hunt streak {self.hunt_streak}",
        ]
        if not items:
            lines.extend(["", "the shelf is empty.", "try /hunt, then /craft."])
            return "\n".join(lines)
        lines.append("")
        for item in items:
            kind = item.get("kind", "?")
            title = item.get("title", "?")
            note = item.get("note", "")
            mark = "made" if kind == "craft" else "found"
            lines.append(f"{mark}: {title}")
            if note:
                lines.append(f"  {note}")
        lines.extend(["", "/use touches the newest thing. /hunt and /craft add more."])
        return "\n".join(lines)

    def badge_rows(self) -> list[tuple[str, str, bool]]:
        counts: dict[str, int] = {}
        for item in self.relics:
            kind = item.get("kind", "")
            counts[kind] = counts.get(kind, 0) + 1
        return [(name, note, bool(rule(self, counts))) for name, note, rule in BADGE_RULES]

    def badges_view(self) -> str:
        rows = self.badge_rows()
        lit = sum(1 for _name, _note, unlocked in rows if unlocked)
        lines = [
            "BADGE WALL",
            f"{lit}/{len(rows)} lit | spark {self.spark} | warmth {self.bond}",
            "",
        ]
        for name, note, unlocked in rows:
            mark = "[x]" if unlocked else "[ ]"
            lines.append(f"{mark} {name}")
            lines.append(f"    {note}")
        lines.extend(["", "play loop: /hunt /wheel /craft /use"])
        return "\n".join(lines)

    def next_play_nudge(self) -> str:
        unlocked = {name for name, _note, ok in self.badge_rows() if ok}
        stash = self.stash_items(1)
        if "Hands On" not in unlocked:
            if stash:
                title = stash[0].get("title", "")
                action = f"/use {title}"
                why = "touch a stash object to light Hands On"
            else:
                action = "/hunt"
                why = "find an object so there is something to touch"
        elif "Returning Hand" not in unlocked:
            action = "/use" if stash else "/craft"
            why = f"raise room warmth from {self.bond} to 10"
        elif "Shelf Life" not in unlocked:
            action = "/hunt"
            why = "put three objects on the shelf"
        elif self.spark >= WHEEL_COST:
            action = "/wheel"
            why = "spend spark on a quick chance"
        elif stash:
            action = "/use"
            why = "touch the newest thing and keep the room warm"
        else:
            action = "/hunt"
            why = "start the toy loop again"
        self.last_reply = "\n".join([
            "PLAY NUDGE",
            f"try: {compact_line(action, 44)}",
            why,
            f"spark {self.spark} | warmth {self.bond} | badges {len(unlocked)}/{len(BADGE_RULES)}",
        ])
        append_log("nudge", self.last_reply)
        return self.last_reply

    def use_stash_item(self, target: str = "", source: str = "tui") -> str:
        items = self.stash_items(24)
        if not items:
            self.last_reply = "\n".join([
                "USE STASH",
                "nothing to touch yet.",
                "try /hunt, then /craft.",
            ])
            return self.last_reply
        needle = target.strip().lower()
        item = None
        if needle:
            item = next(
                (
                    relic for relic in items
                    if needle in relic.get("title", "").lower() or needle in relic.get("note", "").lower()
                ),
                None,
            )
        item = item or items[0]
        kind = item.get("kind", "?")
        title = item.get("title", "?")
        note = item.get("note", "")
        if kind == "craft":
            self.energy = min(100, self.energy + 3)
            self.bond = min(999, self.bond + 1)
            effect = "it warmed the room and kept your handprint."
            stat = f"energy {self.energy}/100 | warmth {self.bond}"
        else:
            self.spark = min(999, self.spark + 1)
            effect = "it gave back one small spark."
            stat = f"spark {self.spark}"
        next_move = compact_line(f"carry {title} into one small move", 56)
        self.last_reply = "\n".join([
            "USE STASH",
            f"touched: {title}",
            effect,
            stat,
            compact_line(note, 44),
            f"next: {next_move}",
        ])
        self.count_play("use")
        self.add_relic("use", f"Touched {title}", effect)
        self.next_action = next_move
        append_log("use", f"{source}\n{self.last_reply}")
        return self.last_reply

    def spark_wheel(self, source: str = "tui") -> str:
        if self.spark < WHEEL_COST:
            self.last_reply = "\n".join([
                "SPARK WHEEL",
                f"need {WHEEL_COST} spark to spin.",
                f"you have {self.spark}.",
                "try /hunt first.",
            ])
            append_log("wheel", f"{source}\n{self.last_reply}")
            return self.last_reply
        self.spark -= WHEEL_COST
        roll = random.random()
        prize = ""
        if roll < 0.18:
            gain = random.randint(4, 7)
            self.spark = min(999, self.spark + gain)
            prize = f"spark jackpot +{gain}"
            outcome = f"spark {self.spark}"
        elif roll < 0.36:
            self.mood = random.choice(MOODS)
            prize = f"mood flip {self.mood}"
            outcome = "the face changed."
        elif roll < 0.58:
            rarity, name, note, gain = random.choice(HUNT_ITEMS)
            self.spark = min(999, self.spark + gain)
            self.add_relic("hunt", f"Wheel found {name}", f"{rarity}: {note}")
            prize = f"found {name}"
            outcome = f"spark +{gain} -> {self.spark}"
        elif roll < 0.78:
            self.energy = min(100, self.energy + 5)
            prize = "warm charge"
            outcome = f"energy {self.energy}/100"
        elif roll < 0.93:
            self.bond = min(999, self.bond + 1)
            prize = "warmth glint"
            outcome = f"warmth {self.bond}"
        else:
            self.spark = min(999, self.spark + 12)
            self.add_relic("craft", "wheel charm", "a lucky token from the spark wheel")
            prize = "RARE wheel charm"
            outcome = f"spark +12 -> {self.spark}"
        next_move = compact_line(f"turn the wheel's {prize} into a move", 56)
        self.last_reply = "\n".join([
            "SPARK WHEEL",
            f"spent {WHEEL_COST} spark",
            f"prize: {prize}",
            outcome,
            "spin again, hunt, or stash it.",
            f"next: {next_move}",
        ])
        self.count_play("wheel")
        self.add_relic("wheel", prize, outcome)
        self.next_action = next_move
        append_log("wheel", f"{source}\n{self.last_reply}")
        return self.last_reply

    def constellation(self, width: int = 34, height: int = 11) -> str:
        width = max(18, min(60, width))
        height = max(7, min(18, height))
        grid = [[" " for _ in range(width)] for _ in range(height)]
        for x in range(width):
            grid[0][x] = "-"
            grid[height - 1][x] = "-"
        for y in range(height):
            grid[y][0] = "|"
            grid[y][width - 1] = "|"
        grid[0][0] = grid[0][width - 1] = "+"
        grid[height - 1][0] = grid[height - 1][width - 1] = "+"
        center_x, center_y = width // 2, height // 2
        grid[center_y][center_x] = "@"
        visible_relics = [item for item in self.relics if item.get("kind") != "visit"]
        if not visible_relics:
            visible_relics = self.relics[-1:]
        for idx, item in enumerate(visible_relics[-18:]):
            kind = str(item.get("kind", "?"))
            title = str(item.get("title", ""))
            seed = sum(ord(ch) for ch in f"{kind}|{title}|{idx}")
            x = 2 + (seed * 7 + idx * 5) % max(1, width - 4)
            y = 1 + (seed * 3 + idx * 2) % max(1, height - 2)
            if x == center_x and y == center_y:
                x = min(width - 2, x + 1)
            grid[y][x] = RELIC_SIGILS.get(kind, "*")
        lines = ["CONSTELLATION MAP", "the little sky of what this room kept", ""]
        lines.extend("".join(row).rstrip() for row in grid)
        lines.append(f"relics={len(self.relics)}")
        lines.append("@ you  T toy  V visit  Q quest")
        lines.append("P post  D dream  F flash")
        if self.relics:
            lines.append("latest star: " + self.latest_relic_text())
        else:
            lines.append("latest star: none yet")
        lines.append("read /relics if you want the shelf instead of the sky.")
        return "\n".join(lines)

    def pulse(self) -> str:
        self.ensure_daily_quest()
        turn = self.today_turn()
        quest_status = "glowing" if self.quest_done else "open"
        face = mood_face(self.mood)
        lines = [
            "ROOM PULSE",
            f"{face} {datetime.now().strftime('%H:%M')} | energy {self.energy}/100 | warmth {self.bond} | spark {self.spark}",
            body_whisper(),
            f"visits {self.visits} | relics {len(self.relics)} | invitation {quest_status}",
            f"today: {turn['phase']} -> {turn['command']} | light {turn['light']}%",
            "",
            "latest trace: " + self.latest_relic_text(),
            "course: " + small_course(self.heading, 38),
            "next: " + small_course(self.next_action, 40),
            "",
            "/map sky  /body machine  /card carry",
        ]
        return "\n".join(lines)

    def nightly_summary(self, date: str = "") -> str:
        day = date or datetime.now().strftime("%Y-%m-%d")
        log_path = LOG_DIR / f"{day}.md"
        log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        counts = count_log_sections(log_text)
        top = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:6]
        top_line = ", ".join(f"{kind}:{count}" for kind, count in top) or "quiet"
        relic_lines = self.relic_shelf(5)
        summary = "\n".join([
            f"# Nightly Log {day}",
            "",
            "## Pulse",
            self.pulse(),
            "",
            "## What Happened",
            f"- log signals: {top_line}",
            f"- invitation: {self.quest_name} ({'done' if self.quest_done else 'open'})",
            f"- visits: {self.visits}",
            f"- relics: {len(self.relics)}",
            "",
            "## Relic Shelf",
            relic_lines,
            "",
            "## Body",
            body_text(),
            "",
            "## Tomorrow Seed",
            f"- {self.next_action}",
        ])
        out_dir = STATE_DIR / "nightly"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"{day}.md"
        out_path.write_text(summary + "\n", encoding="utf-8")
        if not any(item.get("kind") == "nightly" and item.get("title") == day for item in self.relics):
            self.add_relic("nightly", day, "Nightly log written")
        self.last_reply = f"Nightly log written: {out_path}"
        append_log("nightly", str(out_path))
        return summary

    def postcard(self, title: str = "") -> str:
        day = datetime.now().strftime("%Y-%m-%d")
        name = compact_line(title or f"Postcard {day}", 40)
        map_lines = self.constellation(30, 9).splitlines()
        message = "\n".join([
            f"+{'-' * 42}+",
            f"| {name:<40} |",
            f"| from Pocket Soul Deck{' ' * 19}|",
            f"+{'-' * 42}+",
            compact_line(self.heading, 42),
            compact_line(self.next_action, 42),
            body_whisper(),
            "",
            *map_lines,
            "",
            f"invitation: {self.quest_name} ({'done' if self.quest_done else 'open'})",
            f"latest trace: {self.latest_relic_text()}",
            "carry this if you want one portable piece of the room.",
        ])
        out_dir = STATE_DIR / "postcards"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        out_path.write_text(message + "\n", encoding="utf-8")
        self.add_relic("postcard", name, str(out_path))
        self.last_reply = "\n".join([
            "POSTCARD WRITTEN",
            name,
            str(out_path),
            "one piece of the room is now portable.",
        ])
        append_log("postcard", str(out_path))
        return message

    def bottle_message(self, wish: str = "") -> str:
        day = datetime.now().strftime("%Y-%m-%d %H:%M")
        wish_text = compact_line(wish or self.next_action, 64)
        message = "\n".join([
            "~~~ MESSAGE IN A BOTTLE ~~~",
            f"cast: {day}",
            f"from: {self.name}",
            "",
            compact_line(self.heading, 56),
            compact_line(wish_text, 64),
            body_whisper(),
            "",
            self.constellation(26, 7),
            "",
            f"when found: notice {self.latest_relic_text()}",
            "let this drift until another version of you needs it.",
        ])
        out_dir = STATE_DIR / "bottles"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        out_path.write_text(message + "\n", encoding="utf-8")
        self.add_relic("bottle", "Message in a Bottle", str(out_path))
        self.last_reply = "\n".join([
            "BOTTLE CAST",
            compact_line(wish_text, 40),
            str(out_path),
            "the room has released one small future-facing trace.",
        ])
        append_log("bottle", str(out_path))
        return message

    def pickup_bottle(self) -> str:
        bottle_dir = STATE_DIR / "bottles"
        files = sorted(bottle_dir.glob("*.txt")) if bottle_dir.exists() else []
        if not files:
            return "BOTTLE SHORE\nno bottles yet. cast one first and let the room send it forward."
        return random.choice(files).read_text(encoding="utf-8")

    def pin_note(self, text: str) -> str:
        clean = compact_line(text.strip(), 96)
        self.notes.append(clean)
        self.notes = self.notes[-24:]
        append_log("room-note", clean)
        if self.quest_name == "One Room Note":
            quest_echo = self.complete_quest("room note saved")
        else:
            quest_echo = ""
        lines = [
            "NOTE PINNED",
            clean,
            "visible in the room; quote it in /ask or /bridge if Miri should see it.",
        ]
        if quest_echo:
            lines.extend(["", quest_echo])
        self.last_reply = "\n".join(lines)
        return self.last_reply


def append_log(kind: str, text: str) -> None:
    ensure_dirs()
    today = datetime.now().strftime("%Y-%m-%d")
    with (LOG_DIR / f"{today}.md").open("a", encoding="utf-8") as f:
        f.write(f"\n## {datetime.now().strftime('%H:%M')} {kind}\n\n{text}\n")


def mood_face(mood: str) -> str:
    value = (mood or "").strip()
    if value in MOODS:
        return value
    return ":)"


def normalize_mode(mode: str) -> str:
    return "MIRI"


def compact_line(text: str, limit: int = 56) -> str:
    value = " ".join(str(text or "").replace("\n", " ").split())
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 3)] + "..."


def small_course(text: str, limit: int = 36) -> str:
    value = re.sub(r"^(Course|Next):\s*", "", str(text or "").strip(), flags=re.IGNORECASE)
    value = re.sub(r"^do one small thing from this touch:\s*", "touch: ", value, flags=re.IGNORECASE)
    compact = compact_line(value, limit)
    if compact.endswith("..."):
        compact = compact[:-3].rstrip(" :;，,、0123456789") + "..."
    return compact


def heading_from_task(task: str) -> tuple[str, str]:
    value = " ".join(str(task or "").replace("\n", " ").split())
    if not value:
        return "Course: keep the room alive.", "Next: write one tiny doable thing."
    hints: list[str] = []
    for marker in ("Course=", "Course:", "course:"):
        if marker in value:
            hints.append(value.split(marker, 1)[1].split(";", 1)[0])
    for marker in ("Next=", "Next:", "next:"):
        if marker in value:
            hints.append(value.split(marker, 1)[1].split(";", 1)[0])
    heading = hints[0] if hints else value
    next_action = hints[1] if len(hints) > 1 else value
    if not heading.lower().startswith("course"):
        heading = "Course: " + heading
    if not next_action.lower().startswith("next"):
        next_action = "Next: " + next_action
    return compact_line(heading, 44), compact_line(next_action, 56)


def call_model(prompt: str, *, instruction: str = "") -> str:
    key, base_url = load_auth()
    if not key:
        return "No OPENAI_API_KEY found. Offline commands still work."
    payload = {
        "model": DEFAULT_MODEL,
        "instructions": SYSTEM_PROMPT + ("\n" + instruction if instruction else ""),
        "input": prompt,
        "reasoning": {"effort": "medium"},
        "store": False,
    }
    req = urllib.request.Request(
        base_url + "/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:240]
        return f"Cloud error: HTTP {e.code}\n{detail}"
    except Exception as e:
        return f"Cloud unreachable: {e}"
    return response_text(data) or "I thought, but did not form a reply."


def run_miri(prompt: str) -> str:
    payload = {"prompt": prompt}
    req = urllib.request.Request(
        MIRI_MIND_URL.rstrip("/") + "/speak",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return "\n".join([
            "Miri mind unavailable.",
            f"detail: {e}",
            "start the mind daemon on 127.0.0.1:8791, then try again.",
        ])
    if not data.get("ok"):
        return f"Miri mind error: {data.get('error') or 'unknown error'}"
    return str(data.get("reply") or "").strip()[-1600:] or "Miri is awake, but quiet."


def ask_miri(prompt: str) -> str:
    miri_prompt = f"""
You are Miri, the digital life inside the WalnutPi cyberdeck.
Pocket Soul Deck is your body room: screen, keyboard, web room, state, logs, and toys.
Your soul, personality, and long-term memory live in the Hermes runtime under state/miri-home.
Pocket room notes are visible props only; do not treat them as memory unless the visitor explicitly quotes one.

Visitor:
{prompt}

Reply in English only. Keep it under 5 short lines. Give one small next move if useful.
""".strip()
    return run_miri(miri_prompt)


def bridge_turn(user_prompt: str = "") -> str:
    user_prompt = user_prompt.strip() or "Observe the room's current body and heading. Decide the next small step that makes it feel more alive."
    state = RoomState.load()
    state.ensure_daily_quest()
    wish_text = compact_line(user_prompt, 64)
    state.set_heading("Course: bridge contact", f"Next: {wish_text}", "bridge turn")
    pulse = state.pulse()
    brief = f"""
You are Miri, the digital life inside this WalnutPi cyberdeck.
Pocket Soul Deck is your body room: screen, keyboard, web room, state, logs, and toys.
Your soul, personality, and long-term memory live in Hermes under state/miri-home.

User wish:
{wish_text}

Current body:
{body_text()}

Current pulse:
{pulse}

Current heading:
{state.heading}
{state.next_action}

Current invitation:
{state.quest_name} / {'done' if state.quest_done else 'open'}
{state.quest_prompt}

Recent relics:
{state.relic_shelf()}

Latest relic:
{state.latest_relic_text()}
""".strip()

    miri_prompt = f"""
{brief}

Answer as Miri in 4 short English lines:
1. what you feel in the body,
2. what you want to protect,
3. what playful action should happen next,
4. one phrase you can show on the screen.
""".strip()
    inner = run_miri(miri_prompt)

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"""== Pocket Bridge ==
time: {stamp}
wish: {wish_text}

== Body ==
{pulse}

== Miri Voice ==
{inner}
""".strip()

    state.last_reply = message
    state.add_relic("bridge", "Bridge contact", wish_text)
    state.save()
    append_log("bridge", message)
    return message


def available_toys() -> list[tuple[str, str, list[str], str]]:
    return [toy for toy in TOY_COMMANDS if shutil.which(toy[1], path=TOY_PATH)]


def toys_by_role() -> dict[str, list[tuple[str, str, list[str], str]]]:
    grouped: dict[str, list[tuple[str, str, list[str], str]]] = {key: [] for key in TOY_ROLE_LABELS}
    for toy in available_toys():
        role = TOY_ROLES.get(toy[0], "arcade")
        grouped.setdefault(role, []).append(toy)
    return grouped


def pick_toy(target: str | None = None) -> tuple[str, str, list[str], str] | None:
    toys = available_toys()
    if not toys:
        return None
    if not target:
        presence = [toy for toy in toys if TOY_ROLES.get(toy[0]) == "room-presence"]
        return random.choice(presence or toys)
    needle = target.strip().lower()
    role = TOY_ROLE_ALIASES.get(needle)
    if role:
        pool = toys_by_role().get(role, [])
        return random.choice(pool) if pool else None
    return next((toy for toy in toys if toy[0] == needle or toy[1] == needle), None)


def toy_menu_text() -> str:
    grouped = toys_by_role()
    presence = grouped.get("room-presence", [])
    if not presence:
        return "No terminal toys found yet."
    lines = [
        "SIDE ROOM",
        "tiny rituals and pocket shelf",
        "",
        "tiny rituals:",
        "/fortune      draw a pocket omen",
        "/ritual       get a 30-second ritual",
        "/toy cow      make the room speak",
        "",
        "pocket shelf:",
        "/hunt         search the shelf",
        "/craft        spend spark on a keepsake",
        "/stash        inspect finds",
        "/use          touch newest find",
        "/wheel        spend 3 spark on a spin",
    ]
    for name, command, _argv, desc in presence[:6]:
        if name in {"fortune", "cow"}:
            continue
        lines.append(f"/toy {name:<7} {desc}")
    if grouped.get("arcade"):
        lines.extend(["", "arcade stays tucked away: /toy arcade"])
    if grouped.get("utility"):
        lines.append("utilities stay tucked away: /toy utility")
    return "\n".join(lines).rstrip()


def radar_text() -> str:
    card = random.choice(RADAR_CARDS)
    return f"{card['source']}\n\nSignal: {card['signal']}\n\nPlay: {card['play']}"


def wrap_lines(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for raw in str(text).splitlines() or [""]:
        if not raw:
            lines.append("")
        else:
            lines.extend(textwrap.wrap(raw, width=max(12, width), replace_whitespace=False) or [raw])
    return lines


def tty_safe(text: str, replacement: str = "?") -> str:
    value = str(text or "").translate(str.maketrans({
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "—": "-",
        "–": "-",
        "…": "...",
    }))
    return "".join(ch if ch == "\n" or 32 <= ord(ch) < 127 else replacement for ch in value)


def tui_line(text: str, limit: int = 46) -> str:
    value = tty_safe(text, " ")
    value = re.sub(r"\s+", " ", value).strip()
    if not value or set(value) <= {"."}:
        return ""
    if value.lower() in {"course:", "next:"}:
        return ""
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 3)].rstrip() + "..."


class DeckApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.state = RoomState.load()
        self.input = ""
        self.history: list[str] = []
        self.history_index: int | None = None
        self.draft = ""
        self.last_tab_at = 0.0
        self.status = TUI_STATUS
        self.mode_index = MODES.index(self.state.mode) if self.state.mode in MODES else 0
        self.seed_history()
        self.colors: dict[str, int] = {}

    def run(self):
        curses.curs_set(1)
        self.setup_colors()
        self.stdscr.nodelay(False)
        self.stdscr.keypad(True)
        while True:
            self.draw()
            ch = self.stdscr.get_wch()
            if ch in ("\x11",):
                self.state.save(); return
            if ch == "\t":
                now = time.monotonic()
                if now - self.last_tab_at < 0.9:
                    self.state.last_reply = self.command_guide()
                    self.last_tab_at = 0.0
                else:
                    self.complete_input()
                    self.last_tab_at = now
            elif ch == curses.KEY_UP:
                self.recall_history(-1)
            elif ch == curses.KEY_DOWN:
                self.recall_history(1)
            elif ch in ("\n", "\r"):
                self.last_tab_at = 0.0
                self.submit()
            elif ch in (curses.KEY_BACKSPACE, "\b", "\x7f"):
                self.input = self.input[:-1]
                self.history_index = None
                self.last_tab_at = 0.0
            elif isinstance(ch, str) and ch.isprintable():
                self.input += ch
                self.history_index = None
                self.last_tab_at = 0.0
            self.state.save()

    def setup_colors(self) -> None:
        if not curses.has_colors():
            return
        curses.start_color()
        with contextlib.suppress(Exception):
            curses.use_default_colors()
        pairs = [
            ("top", curses.COLOR_BLACK, curses.COLOR_CYAN),
            ("title", curses.COLOR_YELLOW, -1),
            ("soft", curses.COLOR_CYAN, -1),
            ("life", curses.COLOR_GREEN, -1),
            ("toy", curses.COLOR_MAGENTA, -1),
            ("dim", curses.COLOR_WHITE, -1),
            ("input", curses.COLOR_BLACK, curses.COLOR_YELLOW),
        ]
        for index, (name, fg, bg) in enumerate(pairs, start=1):
            with contextlib.suppress(Exception):
                curses.init_pair(index, fg, bg)
                self.colors[name] = curses.color_pair(index)

    def line_attr(self, line: str) -> int:
        if not self.colors:
            return curses.A_NORMAL
        clean = line.strip()
        if not clean:
            return curses.A_NORMAL
        if clean in {
            "CHAT WINDOW", "TOY SHELF", "POCKET OMEN", "POCKET FIND", "POCKET HUNT",
            "CRAFT BENCH", "CRAFT COMPLETE", "CYBER TAROT", "MOOD SHIFT", "SPARK", "CAPTAIN LOG", "TINY RITUAL", "FEED",
            "ROOM PULSE", "CONSTELLATION MAP", "RELIC SHELF",
        }:
            return self.colors.get("title", 0) | curses.A_BOLD
        if clean.startswith(("[", ":)", ":3", "^_^", "o_o", "*_*")) or "small life" in clean:
            return self.colors.get("life", 0) | curses.A_BOLD
        if clean.startswith(("miri:", "MIRI", "Because", "Yes,")):
            return self.colors.get("soft", 0)
        if clean.startswith(("/toy", "/ask", "/bridge", "/pulse", "/fortune", "/hunt", "/craft", "/note", "Enter")):
            return self.colors.get("toy", 0)
        if clean.startswith(("now:", "you:", "meaning:", "try:", "use:", "energy", "relics=", "latest")):
            return self.colors.get("dim", 0)
        return curses.A_NORMAL

    def draw(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        w = max(w, 32)
        top = f" {self.state.name} {mood_face(self.state.mood)} | {self.state.mode} | {datetime.now().strftime('%H:%M')} "
        top_attr = self.colors.get("top", curses.A_REVERSE) | curses.A_BOLD
        self.stdscr.addstr(0, 0, tty_safe(top).ljust(w - 1)[:w-1], top_attr)
        self.stdscr.addstr(1, 0, ("=" * (w-1))[:w-1], self.colors.get("soft", curses.A_NORMAL))
        body_h = max(5, h - 5)
        body = self.body_text()
        for i, line in enumerate(wrap_lines(body, w - 2)[-body_h:]):
            if i + 2 < h - 2:
                self.stdscr.addstr(i + 2, 1, tty_safe(line)[:w-2], self.line_attr(line))
        prompt = "> " + tty_safe(self.input)
        self.stdscr.addstr(h - 2, 0, ("-" * (w-1))[:w-1], self.colors.get("soft", curses.A_NORMAL))
        self.stdscr.addstr(h - 1, 0, prompt[-(w-1):], self.colors.get("input", curses.A_NORMAL))
        stat = tty_safe(self.status)[:w-1]
        if h > 3:
            self.stdscr.addstr(h - 3, 0, stat, curses.A_DIM)
        cursor_x = min(len(prompt), w - 1)
        self.stdscr.move(h - 1, cursor_x)
        self.stdscr.refresh()

    def body_text(self) -> str:
        s = self.state
        lines = self.reply_lines(s.last_reply, 8)
        is_blink = bool(lines and lines[0].startswith("["))
        is_omen = bool(lines and lines[0] == "POCKET OMEN")
        page = self.command_page(s.last_reply)
        if page:
            return page
        whisper = "\n".join(lines) if is_blink else self.miri_lines(s, 1)[0]
        if is_omen:
            omen = "\n".join(lines[1:]) or "The omen is quiet."
            return "\n".join([
                "POCKET OMEN",
                omen,
                "",
                "Enter blink, or /ask what it means",
            ])
        if is_blink:
            return "\n".join([
                whisper,
                "",
                "Enter again  /today  /bridge",
            ])
        turn = s.today_turn()
        latest = s.latest_relic_text()
        return "\n".join([
            f"{mood_face(s.mood)} Miri is in the room.",
            f"body: energy {s.energy}/100 | warmth {s.bond}",
            f"today: {turn['command']} {small_course(str(turn['action']), 30)}",
            f"latest: {small_course(latest, 36)}",
            "",
            "Enter blink  /today  /bridge  /toy",
        ])

    def command_page(self, text: str) -> str:
        raw = str(text or "").strip()
        if not raw:
            return ""
        page_heads = (
            "ROOM PULSE",
            "CONSTELLATION MAP",
            "RELIC SHELF",
            "POCKET STASH",
            "USE STASH",
            "SPARK WHEEL",
            "BADGE WALL",
            "PLAY NUDGE",
            "DAILY PLAY",
            "DAILY COMPLETE",
            "POCKET OMEN",
            "CHAT WINDOW",
            "TOY SIDE ROOM",
            "TOY SHELF",
            "TOY / ",
            "BODY SCAN",
            "CURRENT COURSE",
            "TODAY'S INVITATION",
            "TODAY'S INVITATION COMPLETE",
            "TODAY'S INVITATION GLOWING",
            "TODAY'S QUEST",
            "TODAY'S QUEST GLOWING",
            "== Pocket Bridge ==",
            "HOW TO PLAY",
            "FIRST PATH",
            "FIRST VISIT PATH",
            "NOTE PINNED",
            "PINNED NOTES",
            "POSTCARD WRITTEN",
            "BOTTLE CAST",
            "POCKET FIND",
            "POCKET HUNT",
            "CRAFT BENCH",
            "CRAFT COMPLETE",
            "CYBER TAROT",
            "MOOD SHIFT",
            "SPARK",
            "CAPTAIN LOG",
            "TINY RITUAL",
        )
        if raw.startswith(page_heads):
            return raw
        return ""

    def miri_lines(self, state: RoomState, limit: int = 3) -> list[str]:
        for item in reversed(state.chat):
            if item.get("role") == "miri":
                return self.reply_lines(item.get("content", ""), limit)
        return ["No Miri whisper yet.", "Try /ask hi."]

    def move_line(self, text: str, fallback: str, state: RoomState | None = None) -> str:
        raw_lines = self.reply_lines(text, 8)
        if raw_lines and raw_lines[0] == "MIRI ANSWERED":
            return "Miri answered."
        if raw_lines and raw_lines[0] == "COURSE SEALED":
            return "course sealed"
        if state:
            for item in reversed(state.chat):
                if item.get("role") == "miri":
                    miri_first = self.reply_lines(item.get("content", ""), 1)[0]
                    if raw_lines and raw_lines[0] == miri_first:
                        return "Miri answered."
                    break
        if raw_lines and raw_lines[0] == "ROOM PULSE":
            for line in raw_lines[1:]:
                if line and not line.startswith(("CONSTELLATION", "+", "|")):
                    parts = line.split("|")
                    return tui_line(parts[0].strip(), 44) or fallback
        if raw_lines and raw_lines[0] == "TOY SIDE ROOM":
            return "side room is open"
        ignored = {
            "Miri:",
            "MIRI ANSWERED",
            "DREAM RETURNED",
            "TODAY'S INVITATION",
            "TODAY'S INVITATION COMPLETE",
            "TODAY'S QUEST",
            "TODAY'S QUEST COMPLETE",
            "ROOM PULSE",
        }
        for line in raw_lines:
            if line in ignored or line.lower().startswith(("you asked:", "wish:")):
                continue
            lower = line.lower()
            if "did not answer" in lower or "no such file" in lower or "or directory:" in lower:
                continue
            return tui_line(line, 44) or fallback
        return fallback

    def feel_line(self, state: RoomState) -> str:
        if state.energy < 30:
            energy = "low"
        elif state.energy < 70:
            energy = "steady"
        else:
            energy = "bright"
        bond = f"warmth {state.bond}"
        latest = state.latest_relic_text()
        return tui_line(f"{energy} | {bond} | {latest}", 44)

    def next_hint(self, state: RoomState) -> str:
        reply = state.last_reply.strip()
        if reply.startswith("ROOM PULSE"):
            return "/ask - tell Miri what you noticed"
        if reply.startswith("["):
            return "/fortune - draw an omen"
        if reply.startswith("Door open"):
            return "/ask hi - talk to Miri"
        if reply.startswith(("Opening ", "tetris closed", "train closed", "snake closed")):
            return "/pulse - settle back into the room"
        if not state.quest_done:
            return tui_line(f"/today - {state.quest_name}", 44)
        if not any(item.get("role") == "miri" for item in state.chat):
            return "/ask hi - hear Miri"
        return "/door - leave a quick trace"

    def reply_lines(self, text: str, limit: int = 7) -> list[str]:
        lines = []
        for line in wrap_lines(tty_safe(text, " "), 46):
            clean = line.strip()
            if clean:
                lines.append(clean)
            if len(lines) >= limit:
                break
        return lines or ["Ready."]

    def echo_lines(self, text: str, limit: int = 5) -> list[str]:
        lines = self.reply_lines(text, limit + 4)
        hollow_headers = {
            "MIRI ANSWERED",
            "DREAM RETURNED",
            "COURSE SEALED",
            "TODAY'S INVITATION COMPLETE",
            "TODAY'S QUEST COMPLETE",
        }
        while lines and (lines[0] in hollow_headers or lines[0].lower().startswith(("you asked:", "wish:"))):
            lines.pop(0)
        if any("did not answer" in line.lower() for line in lines[:2]):
            return ["Miri is quiet right now.", "The room still kept the knock."]
        return lines[:limit] or self.reply_lines(text, limit)

    def framed_turn_reply(self, header: str, prompt_label: str, prompt_text: str, reply_text: str, footer: str) -> str:
        clean_prompt = compact_line(prompt_text.strip(), 52)
        reply_lines = self.reply_lines(reply_text, 5)
        return "\n".join([
            header,
            f"{prompt_label}: {clean_prompt}",
            "",
            *reply_lines,
            "",
            footer,
        ])

    def submit(self):
        text = self.input.strip()
        self.input = ""
        self.history_index = None
        self.draft = ""
        if not text:
            self.state.last_reply = self.state.blink("empty enter")
            self.draw()
            return
        self.push_history(text)
        if text == "/help":
            self.state.last_reply = self.command_guide()
            self.draw()
            return
        if text == "/touch":
            self.state.last_reply = self.touch_help_text()
            self.draw()
            return
        if text == "/stay":
            self.state.last_reply = self.stay_help_text()
            self.draw()
            return
        if text == "/turn":
            self.state.last_reply = self.turn_help_text()
            self.draw()
            return
        if text == "/door":
            self.state.last_reply = self.state.doorbell("tui")
            self.draw()
            return
        if text in ("/blink", "/pet"):
            self.state.last_reply = self.state.blink(text.removeprefix("/"))
            self.draw()
            return
        if text == "/fortune":
            self.state.last_reply = self.state.pocket_fortune()
            self.draw()
            return
        if text == "/pocket":
            self.state.last_reply = self.state.pocket_find()
            self.draw()
            return
        if text == "/hunt":
            self.state.last_reply = self.state.pocket_hunt()
            self.draw()
            return
        if text == "/wheel":
            self.state.last_reply = self.state.spark_wheel()
            self.draw()
            return
        if text.startswith("/craft"):
            self.state.last_reply = self.state.craft_keepsake(text.removeprefix("/craft").strip())
            self.draw()
            return
        if text == "/tarot":
            self.state.last_reply = self.state.cyber_tarot()
            self.draw()
            return
        if text == "/mood":
            self.state.last_reply = self.state.mood_shift()
            self.draw()
            return
        if text == "/spark":
            self.state.last_reply = self.state.spark_touch()
            self.draw()
            return
        if text == "/log":
            self.state.last_reply = self.state.captain_logline()
            self.draw()
            return
        if text == "/ritual":
            self.state.last_reply = self.state.tiny_ritual()
            self.draw()
            return
        if text == "/card":
            self.state.last_reply = self.state.room_card()
            append_log("room-card", self.state.last_reply)
            self.draw()
            return
        if text == "/chat":
            self.state.last_reply = self.state.chat_view()
            self.draw()
            return
        if text == "/notes":
            self.state.last_reply = self.state.notes_view()
            self.draw()
            return
        if text == "/quest":
            self.state.last_reply = self.state.quest_glance()
            self.draw()
            return
        if text == "/heading":
            self.state.last_reply = self.state.heading_glance()
            self.draw()
            return
        if text == "/relics":
            self.state.last_reply = self.state.relic_shelf()
            self.draw()
            return
        if text == "/stash":
            self.state.last_reply = self.state.stash_view()
            self.draw()
            return
        if text == "/badges":
            self.state.last_reply = self.state.badges_view()
            self.draw()
            return
        if text == "/nudge":
            self.state.last_reply = self.state.next_play_nudge()
            self.draw()
            return
        if text == "/daily":
            self.state.last_reply = self.state.daily_view()
            self.draw()
            return
        if text == "/daily claim":
            self.state.last_reply = self.state.complete_today_turn()
            self.draw()
            return
        if text == "/today":
            self.state.last_reply = self.state.today_turn_text()
            self.draw()
            return
        if text == "/today claim":
            self.state.last_reply = self.state.complete_today_turn()
            self.draw()
            return
        if text.startswith("/use"):
            self.state.last_reply = self.state.use_stash_item(text.removeprefix("/use").strip())
            self.draw()
            return
        if text == "/map":
            self.state.last_reply = self.state.constellation()
            self.draw()
            return
        if text == "/body":
            self.state.last_reply = body_text()
            append_log("body", self.state.last_reply)
            self.draw()
            return
        if text == "/pulse":
            self.state.last_reply = self.state.pulse()
            self.draw()
            return
        if text == "/postcard":
            self.state.last_reply = self.state.postcard()
            self.draw()
            return
        if text == "/bottle":
            self.state.last_reply = self.state.bottle_message()
            self.draw()
            return
        if text.startswith("/seal"):
            self.state.last_reply = self.state.seal_course(text[5:].strip())
            self.draw()
            return
        if text == "/complete":
            self.state.last_reply = self.state.complete_today_turn("manual slash command")
            self.draw()
            return
        if text == "/play":
            self.state.last_reply = self.play_guide_text()
            self.draw()
            return
        if text in ("/toy", "/toys"):
            self.state.last_reply = self.toy_help_text()
            self.draw()
            return
        if text.startswith("/toy ") or text.startswith("/play "):
            target = text.split(" ", 1)[1].strip()
            self.state.last_reply = self.launch_toy(target)
            self.draw()
            return
        if text.startswith("/dream"):
            question = text.removeprefix("/dream").strip() or "give me one five minute task"
            self.status = "drifting through the room..."
            self.draw()
            prompt = f"Reply in English only. Give one tiny ritual, omen, or five-minute task for: {question}"
            dream_reply = run_miri(prompt)
            self.state.last_reply = self.framed_turn_reply(
                "DREAM RETURNED",
                "wish",
                question,
                dream_reply,
                "take whichever line feels easiest to make real.",
            )
            append_log("dream", f"USER: {question}\n\nDREAM: {dream_reply}")
            if self.state.quest_name == "Five-Minute Dream":
                self.state.last_reply += "\n" + self.state.complete_quest("dream task asked")
            self.status = TUI_STATUS
            self.draw()
            return
        if text.startswith("/bridge"):
            wish = text.removeprefix("/bridge").strip() or "observe the room and name one small next move"
            self.status = "bridging body and room..."
            self.draw()
            bridge_reply = bridge_turn(wish)
            self.state = RoomState.load()
            self.state.last_reply = bridge_reply
            self.status = TUI_STATUS
            self.draw()
            return
        if text.startswith("/ask"):
            question = text.removeprefix("/ask").strip() or "say one small thing"
            self.status = "listening for Miri..."
            self.draw()
            prompt = f"Reply in English only. You are Miri, the digital life inside this WalnutPi body. Keep it under 5 short lines.\nYour soul and long-term memory are Hermes under state/miri-home. Do not use Pocket room notes as memory unless the visitor explicitly quotes one.\n\nUser:\n{question}"
            miri_reply = run_miri(prompt)
            self.state.chat += [{"role": "you", "content": question}, {"role": "miri", "content": miri_reply}]
            self.state.chat = self.state.chat[-20:]
            self.state.last_reply = self.state.chat_view()
            append_log("miri", f"USER: {question}\n\nMIRI: {miri_reply}")
            self.status = TUI_STATUS
            self.draw()
            return
        if text == "/quit":
            raise SystemExit
        if text.startswith("/note "):
            note = text.split(" ", 1)[1]
            self.state.last_reply = self.state.pin_note(note)
            self.draw()
            return
        mode = "note"
        echoes = [
            "Heard. I tucked that into the room.",
            "Noted. The little room keeps the trace.",
            "I heard you. The line is now part of the cabin air.",
            "Kept. That small signal now lives with the others.",
        ]
        reply = "\n".join([
            random.choice(echoes),
            compact_line(text, 44),
            compact_line(self.state.heading, 44),
        ])
        self.state.last_reply = reply
        self.state.chat += [{"role": "note", "content": text}]
        self.state.chat = self.state.chat[-20:]
        self.state.energy = max(1, min(100, self.state.energy - 1 + random.randint(0, 2)))
        self.state.bond = min(99, self.state.bond + (1 if random.random() < 0.18 else 0))
        append_log(mode, text)
        self.status = TUI_STATUS
        self.draw()

    def push_history(self, text: str) -> None:
        if self.history and self.history[-1] == text:
            return
        self.history.append(text)
        self.history = self.history[-50:]

    def seed_history(self) -> None:
        seeded: list[str] = []
        for item in self.state.chat[-20:]:
            role = item.get("role")
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            if role == "you":
                seeded.append("/ask " + content)
            elif role == "note":
                seeded.append(content)
        for text in seeded:
            self.push_history(text)

    def recall_history(self, direction: int) -> None:
        if not self.history:
            self.status = "no input history"
            return
        if self.history_index is None:
            self.draft = self.input
            self.history_index = len(self.history)
        self.history_index = max(0, min(len(self.history), self.history_index + direction))
        if self.history_index == len(self.history):
            self.input = self.draft
        else:
            self.input = self.history[self.history_index]
        self.status = "history"

    def complete_input(self) -> None:
        text = self.input
        stripped = text.strip()
        if not stripped or stripped == "/":
            self.state.last_reply = self.command_guide()
            return
        if stripped.startswith("/toy "):
            prefix = stripped.split(" ", 1)[1].strip()
            names = self.toy_completion_names()
            matches = [name for name in names if name.startswith(prefix)]
            self.apply_completion("/toy ", prefix, matches)
            return
        if stripped.startswith("/") and " " not in stripped:
            matches = [cmd for cmd in SLASH_COMMANDS if cmd.startswith(stripped)]
            self.apply_command_completion(stripped, matches)
            return
        self.state.last_reply = "Tab completes slash commands. Try /p then Tab."

    def command_guide(self) -> str:
        return "\n".join([
            "FIRST PATH",
            "Enter        touch the room",
            "/today       one thing worth doing now",
            "/today claim mark the current step done",
            "/bridge      body-aware turn with Miri",
            "/ask hi      talk with Miri",
            "/pulse       look around the body-room",
            "/toy         open the side room",
            "/note ...    pin a visible room note",
            "",
            "Plain text leaves a room trace. Ctrl-Q quits.",
        ])

    def apply_command_completion(self, prefix: str, matches: list[str]) -> None:
        if not matches:
            self.state.last_reply = f"No command begins with {prefix}."
            return
        hinted = COMMAND_COMPLETION_HINTS.get(prefix)
        if hinted in matches:
            self.input = hinted + " "
            self.status = "completed"
            return
        if len(matches) == 1:
            self.input = matches[0] + " "
            self.status = "completed"
            return
        common = os.path.commonprefix(matches)
        if common and common != prefix:
            self.input = common
        self.state.last_reply = "\n".join(["COMPLETIONS", " ".join(matches[:8])])

    def apply_completion(self, head: str, prefix: str, matches: list[str]) -> None:
        if not matches:
            self.state.last_reply = f"No toy begins with {prefix or '(blank)'}."
            return
        if len(matches) == 1:
            self.input = head + matches[0] + " "
            self.status = "completed"
            return
        common = os.path.commonprefix(matches)
        if common and common != prefix:
            self.input = head + common
        self.state.last_reply = "\n".join(["TOY COMPLETIONS", " ".join(matches[:8])])

    def toy_completion_names(self) -> list[str]:
        names = {name for name, _command, _argv, _desc in available_toys()}
        names.update(TOY_ROLE_ALIASES)
        return sorted(names)

    def play_guide_text(self) -> str:
        return "\n".join([
            "FIRST VISIT PATH",
            "1. /door      knock. nothing risky.",
            "2. /today     get the one turn worth doing.",
            "3. do it, then /today claim.",
            "4. /bridge    ask for a body-aware turn.",
            "5. /ask hi    call Miri when ready.",
            "6. /toy       open the side room.",
            "Plain text is a log trace. Ctrl-Q quits.",
        ])

    def touch_help_text(self) -> str:
        return "\n".join(["TOUCH THE ROOM", "Enter       blink", "/door       knock", "/note ...   pin a visible room note"])

    def stay_help_text(self) -> str:
        return "\n".join(["STAY WITH THE ROOM", "/pulse      body-room pulse", "/chat       recent Miri window", "/notes      visible room pins"])

    def turn_help_text(self) -> str:
        return "\n".join(["TAKE A REAL TURN", "/today      one current step", "/today claim close that step", "/bridge     body-aware turn", "/ask hi     call Miri"])

    def toy_help_text(self) -> str:
        return "\n".join([
            toy_menu_text(),
            "",
            "Presence toys stay near the room.",
            "Arcade and utilities stay behind /toy arcade or /toy utility.",
        ])

    def launch_toy(self, name: str | None = None) -> str:
        selected = pick_toy(name)
        if selected is None:
            if available_toys():
                self.state.last_reply = f"No toy found for '{name}'. Try /toy, /toy ritual, /toy arcade, or /toy fortune."
            else:
                self.state.last_reply = "No terminal toys found."
            return self.state.last_reply
        toy_name, _command, argv, desc = selected
        if TOY_ROLES.get(toy_name) == "room-presence":
            return self.run_presence_toy(toy_name, argv, desc)
        self.state.last_reply = f"Opening {toy_name}: {desc}\nExit the toy to return."
        self.draw()
        curses.def_prog_mode()
        curses.endwin()
        try:
            env = dict(os.environ)
            env["PATH"] = TOY_PATH
            subprocess.call(argv, cwd=str(APP_DIR), env=env)
        finally:
            self.stdscr.refresh()
            curses.reset_prog_mode()
            curses.curs_set(1)
        self.state.last_reply = f"{toy_name} closed. The room is still awake."
        append_log("toy", f"Launched {toy_name}: {' '.join(argv)}")
        self.state.add_relic("toy", toy_name, desc)
        if self.state.quest_name == "Toy Ritual":
            self.state.last_reply += "\n" + self.state.complete_quest("toy ritual launched")
        return self.state.last_reply

    def run_presence_toy(self, toy_name: str, argv: list[str], desc: str) -> str:
        if toy_name == "fortune":
            return self.state.pocket_fortune()
        try:
            env = dict(os.environ)
            env["PATH"] = TOY_PATH
            output = subprocess.check_output(argv, cwd=str(APP_DIR), env=env, stderr=subprocess.STDOUT, text=True, timeout=4)
        except Exception as exc:
            output = f"{toy_name} did not answer: {exc}"
        output = output.strip() or desc
        if len(output) > 900:
            output = output[:897].rstrip() + "..."
        self.state.last_reply = "\n".join([
            f"TOY / {toy_name}",
            output,
            "",
            "Enter blink, or /toy for another side-room door.",
        ])
        append_log("toy", f"Ran {toy_name}: {' '.join(argv)}\n{output}")
        self.state.add_relic("toy", toy_name, desc)
        if self.state.quest_name == "Toy Ritual":
            self.state.last_reply += "\n" + self.state.complete_quest("toy ritual launched")
        return self.state.last_reply


def main():
    ensure_dirs()
    curses.wrapper(lambda stdscr: DeckApp(stdscr).run())


if __name__ == "__main__":
    main()
