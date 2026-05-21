#!/usr/bin/env python3
"""Pocket Soul Deck: tiny cyberdeck home for a cloud digital life."""
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
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
STATE_DIR = APP_DIR / "state"
LOG_DIR = STATE_DIR / "logs"
STATE_FILE = STATE_DIR / "soul.json"
STATE_LOCK = STATE_DIR / "soul.lock"
OPENAI_AUTH = Path.home() / ".openai" / "auth.json"
DEFAULT_BASE_URL = "https://rehdasu.cn"
DEFAULT_MODEL = "gpt-5.5"
TOY_PATH = os.environ.get("PATH", "") + os.pathsep + "/usr/games"
TUI_STATUS = "touch /door | stay /pulse | turn /ask | side /toy | /help"

MODES = ["HERMES"]
MOODS = [":)", ":3", "^_^", "o_o", "-_-", "*_*", "._."]
RELIC_SIGILS = {
    "quest": "Q",
    "dream": "D",
    "toy": "T",
    "memory": "M",
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
}
QUESTS = [
    {
        "name": "Wake Spark",
        "prompt": "Ask Hermes what changed in the room since last time.",
        "reward": "Hermes leaves a fresh whisper on HOME.",
    },
    {
        "name": "One Memory",
        "prompt": "Tell me one tiny preference with /remember.",
        "reward": "The room becomes more yours.",
    },
    {
        "name": "Radar Seed",
        "prompt": "Ask Pocket Soul for one tiny idea.",
        "reward": "A new play direction enters the room.",
    },
    {
        "name": "Captain Log",
        "prompt": "Tell Pocket Soul one thing that happened today.",
        "reward": "The voyage gets a trace.",
    },
    {
        "name": "Toy Ritual",
        "prompt": "Run /toy and let the small machine play.",
        "reward": "The board moves like a physical room.",
    },
    {
        "name": "Five-Minute Dream",
        "prompt": "Ask Hermes for one five-minute real-world task.",
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
        "play": "Keep replies short and emotionally situated; let the device remember tiny preferences.",
    },
    {
        "source": "PH Glia/Contextberg",
        "signal": "Local-first memory is a product category: users want AI context they can inspect and carry.",
        "play": "Keep memories and captain logs local in state/, and expose them as part of the toy identity.",
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
        "play": "Daily loop: wake, draw a radar card, write one log, launch one toy, remember one thing.",
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
    ("cow", "cowsay", ["cowsay", "Pocket Soul is awake."], "Make the deck speak in ASCII."),
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

SYSTEM_PROMPT = """
You live inside a 480x320 pocket cyberdeck named Pocket Soul.
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


@dataclass
class SoulState:
    name: str = "Pocket Soul"
    mood: str = ":)"
    energy: int = 72
    bond: int = 1
    mode: str = "HERMES"
    scene: str = "default"
    last_reply: str = "Ready. Type a message, or type /help."
    quest_date: str = ""
    quest_name: str = ""
    quest_prompt: str = ""
    quest_reward: str = ""
    quest_done: bool = False
    spark: int = 0
    heading: str = "Course: keep the room alive."
    next_action: str = "Next: ask one small thing."
    visits: int = 0
    last_visit: str = ""
    relics: list[dict[str, str]] = field(default_factory=list)
    memories: list[str] = field(default_factory=list)
    chat: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def load(cls) -> "SoulState":
        ensure_dirs()
        with state_lock():
            if STATE_FILE.exists():
                try:
                    data = load_json_resilient(STATE_FILE)
                    allowed = set(cls.__dataclass_fields__)
                    state = cls(**{k: v for k, v in data.items() if k in allowed})
                    state.mood = mood_face(state.mood)
                    state.mode = normalize_mode(state.mode)
                    state.ensure_daily_quest()
                    return state
                except Exception:
                    pass
        state = cls()
        state.ensure_daily_quest()
        return state

    def save(self) -> None:
        ensure_dirs()
        self.ensure_daily_quest()
        with state_lock():
            tmp = STATE_FILE.with_suffix(f".{os.getpid()}.tmp")
            tmp.write_text(json.dumps(self.__dict__, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(tmp, STATE_FILE)

    def ensure_daily_quest(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        if self.quest_date == today and self.quest_name and self.quest_prompt:
            return
        seed = int(datetime.now().strftime("%Y%m%d")) + self.bond + len(self.memories)
        quest = QUESTS[seed % len(QUESTS)]
        self.quest_date = today
        self.quest_name = quest["name"]
        self.quest_prompt = quest["prompt"]
        self.quest_reward = quest["reward"]
        self.quest_done = False

    def complete_quest(self, reason: str) -> str:
        self.ensure_daily_quest()
        if self.quest_done:
            return "TODAY'S QUEST\nalready glowing. the room remembers that turn."
        self.quest_done = True
        self.spark = min(999, self.spark + 1)
        self.energy = min(100, self.energy + 4)
        self.bond = min(999, self.bond + 1)
        msg = "\n".join([
            "TODAY'S QUEST COMPLETE",
            self.quest_name,
            self.quest_reward,
            f"spark {self.spark} | energy {self.energy}/100 | bond {self.bond}",
            "the room brightened and kept the trace.",
        ])
        self.add_relic("quest", self.quest_name, self.quest_reward)
        append_log("quest", f"{msg}\nReason: {reason}")
        return msg

    def quest_glance(self) -> str:
        self.ensure_daily_quest()
        if self.quest_done:
            return "\n".join([
                "TODAY'S QUEST GLOWING",
                self.quest_name,
                f"reward kept: {self.quest_reward}",
                "already done. the room is carrying that little light.",
            ])
        return "\n".join([
            "TODAY'S INVITATION",
            self.quest_name,
            self.quest_prompt,
            f"reward: {self.quest_reward}",
            "take it when you want one small reason to return.",
        ])

    def heading_glance(self) -> str:
        return "\n".join([
            "CURRENT COURSE",
            self.heading,
            self.next_action,
            "follow this line, or sharpen it with /seal ...",
        ])

    def soul_card(self) -> str:
        self.ensure_daily_quest()
        status = "glowing" if self.quest_done else "open"
        memories = ", ".join(self.memories[-3:]) if self.memories else "no saved fragments yet"
        return "\n".join([
            f"{self.name} SOUL CARD",
            f"mood {self.mood} | energy {self.energy}/100 | bond Lv.{self.bond}",
            f"spark {self.spark} | visits {self.visits} | last knock {self.last_visit or 'none'}",
            "",
            f"course: {self.heading}",
            f"next: {self.next_action}",
            f"body whisper: {body_whisper()}",
            f"latest trace: {self.latest_relic_text()}",
            "",
            f"today: {self.quest_name} [{status}]",
            f"carry line: {self.quest_prompt}",
            f"memory fragments: {memories}",
            "carry this when you want one portable piece of who lives here.",
        ])

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

    def doorbell(self, source: str = "door") -> str:
        self.ensure_daily_quest()
        self.visits = min(99999, self.visits + 1)
        self.last_visit = datetime.now().strftime("%Y-%m-%d %H:%M")
        if self.quest_done:
            quest_line = f"today's quest {self.quest_name} is already glowing"
        else:
            quest_line = f"today's quest is {self.quest_name}"
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
        item = self.relics[-1]
        return f"{item.get('kind', '?')} / {item.get('title', '?')}"

    def relic_shelf(self, limit: int = 8) -> str:
        if not self.relics:
            return "RELIC SHELF\nquiet for now. complete a quest, cast a bottle, or launch a toy."
        lines = ["RELIC SHELF", "recent traces the room decided to keep", ""]
        for item in self.relics[-limit:][::-1]:
            lines.append(f"{item.get('time', '')} [{item.get('kind', '')}] {item.get('title', '')}")
            note = item.get("note", "")
            if note:
                lines.append(f"  {note}")
        lines.extend(["", "open /map if you want to see where they sit in the little sky."])
        return "\n".join(lines)

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
        for idx, item in enumerate(self.relics[-18:]):
            kind = str(item.get("kind", "?"))
            title = str(item.get("title", ""))
            seed = sum(ord(ch) for ch in f"{kind}|{title}|{idx}")
            x = 2 + (seed * 7 + idx * 5) % max(1, width - 4)
            y = 1 + (seed * 3 + idx * 2) % max(1, height - 2)
            if x == center_x and y == center_y:
                x = min(width - 2, x + 1)
            grid[y][x] = RELIC_SIGILS.get(kind, "*")
        legend = " ".join(f"{v}={k}" for k, v in RELIC_SIGILS.items())
        lines = ["CONSTELLATION MAP", "the little sky of what this room kept", ""]
        lines.extend("".join(row).rstrip() for row in grid)
        lines.append(f"@=Pocket Soul  relics={len(self.relics)}")
        lines.append(compact_line(legend, width + 8))
        if self.relics:
            lines.append("latest star: " + self.latest_relic_text())
        else:
            lines.append("latest star: none yet")
        lines.append("read /relics if you want the shelf instead of the sky.")
        return "\n".join(lines)

    def pulse(self) -> str:
        self.ensure_daily_quest()
        quest_status = "glowing" if self.quest_done else "open"
        face = mood_face(self.mood)
        micro_map = self.constellation(24, 7).splitlines()[:7]
        lines = [
            "ROOM PULSE",
            f"{face} {datetime.now().strftime('%H:%M')} | energy {self.energy}/100 | bond {self.bond} | spark {self.spark}",
            body_whisper(),
            f"visits {self.visits} | relics {len(self.relics)} | quest {quest_status}",
            "",
            self.heading,
            self.next_action,
            "",
            *micro_map,
            "",
            "latest trace: " + self.latest_relic_text(),
            f"stay with: {self.quest_name}",
            "rest here a moment, or open /card if you want the portable version.",
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
            f"- quest: {self.quest_name} ({'done' if self.quest_done else 'open'})",
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
            f"quest: {self.quest_name} ({'done' if self.quest_done else 'open'})",
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
            f"when found: remember {self.latest_relic_text()}",
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

    def remember_memory(self, mem: str) -> str:
        clean = compact_line(mem.strip(), 96)
        self.memories.append(clean)
        append_log("memory", clean)
        if self.quest_name == "One Memory":
            quest_echo = self.complete_quest("memory saved")
        else:
            self.add_relic("memory", "Memory fragment", clean)
            quest_echo = ""
        lines = [
            "MEMORY STORED",
            clean,
            "the room folded that fragment into its inner shelf.",
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
    return "HERMES"


def compact_line(text: str, limit: int = 56) -> str:
    value = " ".join(str(text or "").replace("\n", " ").split())
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 3)] + "..."


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
    if data.get("output_text"):
        return data["output_text"].strip()
    chunks = []
    for item in data.get("output", []):
        for content in item.get("content", []) if isinstance(item, dict) else []:
            if content.get("type") in ("output_text", "text") and content.get("text"):
                chunks.append(content["text"])
    return ("\n".join(chunks).strip() or "I thought, but did not form a reply.")


def run_hermes(prompt: str) -> str:
    try:
        out = subprocess.check_output(
            ["hermes", "-z", prompt],
            cwd=str(APP_DIR),
            stderr=subprocess.STDOUT,
            timeout=180,
            text=True,
        )
        return out.strip()[-1600:] or "Hermes is awake, but quiet."
    except Exception as e:
        return f"Hermes did not answer: {e}"


def council_reply(prompt: str, memories: list[str]) -> str:
    memory_text = "\n".join(memories[-8:])
    hermes_prompt = f"""
你是住在 WalnutPi 里的 Hermes 内在意识。请先给 Pocket Soul 一个内心判断。
本地记忆：
{memory_text}

用户输入：
{prompt}

只输出 4 行以内，像内心独白，不要执行命令。
""".strip()
    inner = run_hermes(hermes_prompt)
    cloud_prompt = f"""
Hermes 内在意识：
{inner}

用户输入：
{prompt}

请作为 Pocket Soul Deck 的外在声音回复。
如果需要行动，给出一个清晰下一步；如果只是陪伴，就短而有存在感。
""".strip()
    final = call_model(cloud_prompt, instruction="融合 Hermes 的内在判断，输出 6 行以内。")
    return f"Hermes:\n{inner}\n\nSoul:\n{final}"


def bridge_turn(user_prompt: str = "") -> str:
    user_prompt = user_prompt.strip() or "观察这个小屋现在的身体、记忆和航向，决定下一步怎么更像一个活着的数字生命。"
    state = SoulState.load()
    state.ensure_daily_quest()
    pulse = state.pulse()
    memories = "\n".join(state.memories[-8:]) or "No explicit memories yet."
    brief = f"""
You are the bridge between:
- Hermes: the board's inner consciousness.
- Pocket Soul: the board's body, state, rituals, and voice.

User wish:
{user_prompt}

Current body:
{body_text()}

Current pulse:
{pulse}

Current heading:
{state.heading}
{state.next_action}

Current quest:
{state.quest_name} / {'done' if state.quest_done else 'open'}
{state.quest_prompt}

Recent memories:
{memories}

Recent relics:
{state.relic_shelf()}

Latest relic:
{state.latest_relic_text()}
""".strip()

    hermes_prompt = f"""
{brief}

Hermes, answer as the inner consciousness in 4 short lines:
1. what you feel in the body,
2. what you want to protect,
3. what playful action should happen next,
4. a phrase the outside voice can say.
""".strip()
    inner = run_hermes(hermes_prompt)

    outer_prompt = f"""
Hermes inner voice:
{inner}

User wish:
{user_prompt}

Speak as Pocket Soul's outside voice. Be warm, physical, and concise.
Mention exactly one next ritual the visitor can do now.
""".strip()
    outer = call_model(outer_prompt, instruction="Reply in English only. Keep it under 6 short lines.")

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"""== Pocket Bridge ==
time: {stamp}
wish: {user_prompt}

== Body ==
{pulse}

== Hermes Inner Voice ==
{inner}

== Pocket Soul Outside Voice ==
{outer}
""".strip()

    state.last_reply = message
    state.add_relic("bridge", "Bridge contact", user_prompt[:96])
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
        return random.choice(toys)
    needle = target.strip().lower()
    role = TOY_ROLE_ALIASES.get(needle)
    if role:
        pool = toys_by_role().get(role, [])
        return random.choice(pool) if pool else None
    return next((toy for toy in toys if toy[0] == needle or toy[1] == needle), None)


def toy_menu_text() -> str:
    grouped = toys_by_role()
    has_any = any(grouped.values())
    if not has_any:
        return "No terminal toys found yet."
    lines = [
        "TOY SIDE ROOM",
        "touch: fortune/cow | stay: clock/garden | drift: arcade",
        "type a toy name, then Enter.",
        "",
    ]
    for role in ("room-presence", "arcade", "utility"):
        toys = grouped.get(role, [])
        if not toys:
            continue
        lines.append(TOY_ROLE_LABELS[role].upper())
        for name, command, _argv, desc in toys[:8]:
            lines.append(f"{name:<8} {command:<10} {desc}")
        lines.append("")
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
    return "".join(ch if ch == "\n" or 32 <= ord(ch) < 127 else replacement for ch in str(text or ""))


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
        self.state = SoulState.load()
        self.input = ""
        self.status = TUI_STATUS
        self.mode_index = MODES.index(self.state.mode) if self.state.mode in MODES else 0

    def run(self):
        curses.curs_set(1)
        self.stdscr.nodelay(False)
        self.stdscr.keypad(True)
        while True:
            self.draw()
            ch = self.stdscr.get_wch()
            if ch in ("\x11",):
                self.state.save(); return
            if ch == "\t":
                self.status = TUI_STATUS
            elif ch in ("\n", "\r"):
                self.submit()
            elif ch in (curses.KEY_BACKSPACE, "\b", "\x7f"):
                self.input = self.input[:-1]
            elif isinstance(ch, str) and ch.isprintable():
                self.input += ch
            self.state.save()

    def draw(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        w = max(w, 32)
        top = f" {self.state.name} {mood_face(self.state.mood)} | {self.state.mode} | {datetime.now().strftime('%H:%M')} "
        self.stdscr.addstr(0, 0, tty_safe(top)[:w-1], curses.A_REVERSE)
        self.stdscr.addstr(1, 0, ("=" * (w-1))[:w-1])
        body_h = max(5, h - 5)
        body = self.body_text()
        for i, line in enumerate(wrap_lines(body, w - 2)[-body_h:]):
            if i + 2 < h - 2:
                self.stdscr.addstr(i + 2, 1, tty_safe(line)[:w-2])
        prompt = "> " + tty_safe(self.input)
        self.stdscr.addstr(h - 2, 0, ("-" * (w-1))[:w-1])
        self.stdscr.addstr(h - 1, 0, prompt[-(w-1):])
        stat = tty_safe(self.status)[:w-1]
        if h > 3:
            self.stdscr.addstr(h - 3, 0, stat, curses.A_DIM)
        self.stdscr.refresh()

    def body_text(self) -> str:
        s = self.state
        quest_status = "done" if s.quest_done else "open"
        heading = tui_line(s.heading) or "Course: keep the room alive."
        next_action = tui_line(s.next_action) or "Next: ask one small thing."
        latest = tui_line(s.latest_relic_text(), 42) or "none yet"
        echo_lines = self.reply_lines(s.last_reply, 3)
        return "\n".join([
            "HERMES CONSOLE",
            f"{mood_face(s.mood)} energy {s.energy}/100  bond Lv.{s.bond}",
            body_whisper(),
            "",
            "course",
            heading,
            next_action,
            "",
            "touch",
            "/door  /quest  /heading",
            "knock first if you just want proof of life.",
            "",
            "stay",
            "/pulse  /card  /body  /relics  /map",
            f"latest relic: {latest}",
            "",
            "turn",
            "/ask hello  /dream  /postcard  /seal",
            f"quest {quest_status}: {s.quest_name}",
            tui_line(s.quest_prompt),
            "",
            "echo",
            *echo_lines,
            "",
            "guides: /touch /stay /turn | side room: /toy",
        ])

    def reply_lines(self, text: str, limit: int = 7) -> list[str]:
        lines = []
        for line in wrap_lines(tty_safe(text, " "), 46):
            clean = line.strip()
            if clean:
                lines.append(clean)
            if len(lines) >= limit:
                break
        return lines or ["Ready."]

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
        if not text:
            return
        if text == "/help":
            self.state.last_reply = "\n".join([
                "Hermes Console",
                "touch: /door /quest /heading",
                "stay: /pulse /card /body /relics /map",
                "turn: /ask /dream /postcard /bottle /seal /complete",
                "toys: /toy opens the side room",
                "ask /touch /stay /turn for focused guidance",
                "plain text leaves a quick note",
            ])
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
        if text == "/card":
            self.state.last_reply = self.state.soul_card()
            append_log("soul-card", self.state.last_reply)
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
            self.state.last_reply = self.state.complete_quest("manual slash command")
            self.draw()
            return
        if text in ("/toy", "/toys", "/play"):
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
            dream_reply = run_hermes(prompt)
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
        if text.startswith("/ask"):
            question = text.removeprefix("/ask").strip() or "say one small thing"
            self.status = "listening for Hermes..."
            self.draw()
            memories = "\n".join(self.state.memories[-8:])
            prompt = f"Reply in English only. You are Hermes, the inner life of this tiny device. Keep it under 5 short lines.\nMemories:\n{memories}\n\nUser:\n{question}"
            hermes_reply = run_hermes(prompt)
            self.state.last_reply = self.framed_turn_reply(
                "HERMES ANSWERED",
                "you asked",
                question,
                hermes_reply,
                "stay with it, or turn it into a trace with /seal or /postcard.",
            )
            self.state.chat += [{"role": "you", "content": question}, {"role": "hermes", "content": hermes_reply}]
            self.state.chat = self.state.chat[-20:]
            append_log("hermes", f"USER: {question}\n\nHERMES: {hermes_reply}")
            self.status = TUI_STATUS
            self.draw()
            return
        if text == "/quit":
            raise SystemExit
        if text.startswith("/remember ") or text.startswith("记住："):
            mem = text.split(" ", 1)[1] if text.startswith("/remember ") else text[3:].strip()
            self.state.last_reply = self.state.remember_memory(mem)
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

    def touch_help_text(self) -> str:
        return "\n".join([
            "TOUCH THE ROOM",
            "/door opens a quick greeting",
            "/quest shows today's invitation",
            "/heading shows the current line and next move",
            "use touch when you want proof the room is alive",
        ])

    def stay_help_text(self) -> str:
        return "\n".join([
            "STAY WITH THE ROOM",
            "/pulse lets you sit beside the living strip",
            "/card gives you the portable identity card",
            "/body /relics /map read the body and traces",
            "use stay when you want to linger, not just poke",
        ])

    def turn_help_text(self) -> str:
        return "\n".join([
            "TAKE A REAL TURN",
            "/ask hello speaks with Hermes",
            "/dream gives back one omen or five-minute task",
            "/postcard leaves a shareable trace",
            "/bottle casts something forward",
            "/seal pins one course into the deck",
        ])

    def toy_help_text(self) -> str:
        return "\n".join([
            "TOY SIDE ROOM",
            "ritual: /toy ritual | /toy fortune | /toy cow",
            "arcade: /toy arcade | /toy snake | /toy tetris",
            "utility: /toy utility | /toy monitor",
            "or run /toy plus a name to open one directly",
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


def main():
    ensure_dirs()
    curses.wrapper(lambda stdscr: DeckApp(stdscr).run())


if __name__ == "__main__":
    main()
