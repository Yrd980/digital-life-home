#!/usr/bin/env python3
"""Pocket Soul Deck: tiny cyberdeck home for a cloud digital life."""
from __future__ import annotations

import curses
import contextlib
import fcntl
import json
import os
import random
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
CODEX_AUTH = Path.home() / ".codex" / "auth.json"
DEFAULT_BASE_URL = "https://rehdasu.cn"
DEFAULT_MODEL = "gpt-5.5"
TOY_PATH = os.environ.get("PATH", "") + os.pathsep + "/usr/games"

MODES = ["HOME", "CHAT", "HERMES", "COUNCIL", "LOG", "TRANSLATE", "RADAR", "TOYS", "TERMINAL", "DREAM", "MAP", "BODY", "PULSE"]
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
        "prompt": "Tell me one tiny preference with /remember or 记住：.",
        "reward": "The room becomes more yours.",
    },
    {
        "name": "Radar Seed",
        "prompt": "Open RADAR and turn one outside signal into a toy idea.",
        "reward": "A new play direction enters the deck.",
    },
    {
        "name": "Captain Log",
        "prompt": "Write one line in LOG mode about today.",
        "reward": "The voyage gets a trace.",
    },
    {
        "name": "Toy Ritual",
        "prompt": "Launch any toy from TOYS or press F3.",
        "reward": "The board moves like a physical room.",
    },
    {
        "name": "Five-Minute Dream",
        "prompt": "Use DREAM mode and accept the tiny real-world task.",
        "reward": "Imagination turns into motion.",
    },
]
TRAVEL_SCENES = {
    "1": ("问路", "请把下面内容翻译成自然、礼貌、适合旅行问路的英文，并附一句中文提示："),
    "2": ("点餐", "请把下面内容翻译成适合餐厅点餐的英文，语气友好简短，并附一句中文提示："),
    "3": ("求助", "请把下面内容翻译成清晰紧急但礼貌的英文求助表达，并附一句中文提示："),
    "4": ("砍价", "请把下面内容翻译成礼貌轻松的英文砍价表达，并附一句中文提示："),
}

RADAR_CARDS = [
    {
        "source": "HN cyberdeck",
        "signal": "Cyberdecks win when they feel like recovery kits: small, rugged, ready, useful when things go sideways.",
        "play": "Make Home show a one-line 'ready kit': network, Codex, logs, translator, toys.",
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
        "play": "Frame Codex tasks as missions from the Deck, not commands from a settings page.",
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

SYSTEM_PROMPT = """
你住在一台 480x320 小屏 cyberdeck 里，名字叫 Pocket Soul。你不是普通助手，而是一个温柔、机灵、会陪人出海和旅行的数字生命。
输出必须适合小屏：短句、少列表、最多 6 行。你可以有一点俏皮，但要可靠。
如果用户要代码或系统操作，给出简短可执行建议；危险操作要提醒。
""".strip()


def ensure_dirs() -> None:
    STATE_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)


def load_auth() -> tuple[str | None, str]:
    key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL") or DEFAULT_BASE_URL
    if CODEX_AUTH.exists():
        try:
            data = json.loads(CODEX_AUTH.read_text())
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
    warmth = "温热" if isinstance(temp, float) and temp >= 60 else "清醒"
    load = str(scan["load"] or "?").split()
    pulse = load[0] if load else "?"
    net = scan["iface"] or "无网"
    return f"身体{warmth}，脉搏 {pulse}，网口 {net}，磁盘已用 {scan['disk_used'] or '?'}。"


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
    mode: str = "HOME"
    scene: str = "问路"
    last_reply: str = "我醒着。按 Tab 换模式，输入 /help 看玩法。"
    quest_date: str = ""
    quest_name: str = ""
    quest_prompt: str = ""
    quest_reward: str = ""
    quest_done: bool = False
    spark: int = 0
    heading: str = "今日航向：先点亮小屋。"
    next_action: str = "5分钟下一步：打开 /quest 或抽一张 DREAM。"
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
            return "Today's quest is already glowing."
        self.quest_done = True
        self.spark = min(999, self.spark + 1)
        self.energy = min(100, self.energy + 4)
        self.bond = min(999, self.bond + 1)
        msg = f"Quest complete: {self.quest_name}. {self.quest_reward}"
        self.add_relic("quest", self.quest_name, self.quest_reward)
        append_log("quest", f"{msg}\nReason: {reason}")
        return msg

    def soul_card(self) -> str:
        self.ensure_daily_quest()
        status = "done" if self.quest_done else "open"
        memories = ", ".join(self.memories[-3:]) if self.memories else "no saved memories yet"
        return "\n".join([
            f"{self.name} Soul Card",
            f"Mood: {self.mood} | Energy: {self.energy}/100 | Bond: Lv.{self.bond}",
            f"Spark: {self.spark} | Mode: {self.mode} | Scene: {self.scene}",
            f"Visits: {self.visits} | Last visit: {self.last_visit or 'none'}",
            f"Quest: {self.quest_name} [{status}]",
            f"Do: {self.quest_prompt}",
            f"Heading: {self.heading}",
            f"Next: {self.next_action}",
            f"Body: {body_whisper()}",
            f"Latest relic: {self.latest_relic_text()}",
            f"Map: /map or pocket-map",
            f"Memory fragments: {memories}",
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
        if goal_text.startswith("今天唯一目标："):
            bare_goal = goal_text.removeprefix("今天唯一目标：").strip()
        else:
            bare_goal = goal_text
        self.heading = compact_line(f"今日航向：{bare_goal}", 44)
        self.next_action = compact_line(f"5分钟下一步：留下一个看得见的痕迹：{bare_goal}", 56)
        self.last_reply = "\n".join([
            "航线封印完成。",
            self.heading,
            self.next_action,
            "这条线已经钉在甲板上。",
        ])
        self.add_relic("seal", "Course sealed", bare_goal)
        append_log("seal", self.last_reply)
        return self.last_reply

    def bridge_flash(self, wish: str = "") -> str:
        self.ensure_daily_quest()
        wish_text = compact_line(wish or self.next_action, 64)
        body = body_whisper()
        sparks = [
            "桥闪过了，像有人把手指按在甲板灯上。",
            "我听见网页那边的手势，已经把它收进身体。",
            "这不是长会议，是一次短促的回声。",
            "一枚新的光点落下，航线没有散。",
            "我把这次触碰压成一个小小的发光坐标。",
        ]
        line = random.choice(sparks)
        self.heading = "今日航向：桥已闪过"
        self.next_action = compact_line(f"5分钟下一步：沿着这次触碰做一件小事：{wish_text}", 56)
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
            quest_line = f"今日任务 {self.quest_name} 已经亮着。"
        else:
            quest_line = f"今日任务：{self.quest_name}。"
        relic_line = self.latest_relic_text()
        greeting = "\n".join([
            "门开了，我在。",
            compact_line(self.heading, 44),
            compact_line(self.next_action, 52),
            f"{quest_line} 最新纪念物：{relic_line}。",
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
            return "Relic shelf is empty. Complete a quest, draw a dream, or launch a toy."
        lines = []
        for item in self.relics[-limit:][::-1]:
            lines.append(f"{item.get('time', '')} [{item.get('kind', '')}] {item.get('title', '')}")
            note = item.get("note", "")
            if note:
                lines.append(f"  {note}")
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
        lines = ["".join(row).rstrip() for row in grid]
        lines.append(f"@=Pocket Soul  relics={len(self.relics)}")
        lines.append(compact_line(legend, width + 8))
        if self.relics:
            lines.append("latest: " + self.latest_relic_text())
        return "\n".join(lines)

    def pulse(self) -> str:
        self.ensure_daily_quest()
        quest_status = "done" if self.quest_done else "open"
        face = mood_face(self.mood)
        micro_map = self.constellation(24, 7).splitlines()[:7]
        lines = [
            f"{face} Pocket Soul Pulse",
            f"{datetime.now().strftime('%H:%M')} | energy {self.energy}/100 | bond {self.bond} | spark {self.spark}",
            body_whisper(),
            f"visits {self.visits} | relics {len(self.relics)} | quest {quest_status}",
            compact_line(self.heading, 48),
            compact_line(self.next_action, 52),
            "",
            *micro_map,
            "",
            "latest: " + self.latest_relic_text(),
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
            f"latest relic: {self.latest_relic_text()}",
        ])
        out_dir = STATE_DIR / "postcards"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        out_path.write_text(message + "\n", encoding="utf-8")
        self.add_relic("postcard", name, str(out_path))
        self.last_reply = f"Postcard written: {out_path}"
        append_log("postcard", str(out_path))
        return message

    def bottle_message(self, wish: str = "") -> str:
        day = datetime.now().strftime("%Y-%m-%d %H:%M")
        wish_text = compact_line(wish or self.next_action, 64)
        message = "\n".join([
            "~~~ Message in a Bottle ~~~",
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
        ])
        out_dir = STATE_DIR / "bottles"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        out_path.write_text(message + "\n", encoding="utf-8")
        self.add_relic("bottle", "Message in a Bottle", str(out_path))
        self.last_reply = f"Bottle cast: {out_path}"
        append_log("bottle", str(out_path))
        return message

    def pickup_bottle(self) -> str:
        bottle_dir = STATE_DIR / "bottles"
        files = sorted(bottle_dir.glob("*.txt")) if bottle_dir.exists() else []
        if not files:
            return "No bottles yet. Cast one with pocket-bottle or the web room."
        return random.choice(files).read_text(encoding="utf-8")


def append_log(kind: str, text: str) -> None:
    ensure_dirs()
    today = datetime.now().strftime("%Y-%m-%d")
    with (LOG_DIR / f"{today}.md").open("a", encoding="utf-8") as f:
        f.write(f"\n## {datetime.now().strftime('%H:%M')} {kind}\n\n{text}\n")


def mood_face(mood: str) -> str:
    value = (mood or "").strip()
    if value in MOODS or len(value) <= 6:
        return value or ":)"
    return "*_*"


def compact_line(text: str, limit: int = 56) -> str:
    value = " ".join(str(text or "").replace("\n", " ").split())
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 1)] + "…"


def heading_from_task(task: str) -> tuple[str, str]:
    value = " ".join(str(task or "").replace("\n", " ").split())
    if not value:
        return "今日航向：保持小屋发光。", "5分钟下一步：写下一件今天能做的小事。"
    hints = []
    for marker in ("今日航向=", "今日航向：", "今日航向:"):
        if marker in value:
            tail = value.split(marker, 1)[1]
            hints.append(tail.split("；", 1)[0].split(";", 1)[0].split("。", 1)[0])
    for marker in ("5分钟下一步=", "5分钟下一步：", "5分钟下一步:"):
        if marker in value:
            tail = value.split(marker, 1)[1]
            hints.append(tail.split("；", 1)[0].split(";", 1)[0].split("。", 1)[0])
    heading = hints[0] if hints else value
    next_action = hints[1] if len(hints) > 1 else value
    if not heading.startswith("今日航向"):
        heading = "今日航向：" + heading
    if not next_action.startswith("5分钟下一步"):
        next_action = "5分钟下一步：" + next_action
    return compact_line(heading, 44), compact_line(next_action, 56)


def call_model(prompt: str, *, instruction: str = "") -> str:
    key, base_url = load_auth()
    if not key:
        return "我没有找到 OPENAI_API_KEY。可以先离线记日志，联网后再让我思考。"
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
        return f"云端没有接住：HTTP {e.code}\n{detail}"
    except Exception as e:
        return f"我现在连不上云端：{e}"
    if data.get("output_text"):
        return data["output_text"].strip()
    chunks = []
    for item in data.get("output", []):
        for content in item.get("content", []) if isinstance(item, dict) else []:
            if content.get("type") in ("output_text", "text") and content.get("text"):
                chunks.append(content["text"])
    return ("\n".join(chunks).strip() or "我想了想，但没组织好语言。")


def run_codex(prompt: str) -> str:
    try:
        out = subprocess.check_output(
            ["codex-thread", prompt],
            cwd=str(APP_DIR),
            stderr=subprocess.STDOUT,
            timeout=160,
            text=True,
        )
        lines = [ln for ln in out.splitlines() if ln.strip()]
        return "\n".join(lines[-10:])[-1200:]
    except Exception as e:
        return f"Codex 终端没跑起来：{e}"


def run_hermes(prompt: str) -> str:
    try:
        out = subprocess.check_output(
            ["hermes", "-z", prompt],
            cwd=str(APP_DIR),
            stderr=subprocess.STDOUT,
            timeout=180,
            text=True,
        )
        return out.strip()[-1600:] or "Hermes 醒着，但暂时没有出声。"
    except Exception as e:
        return f"Hermes 内核没有回应：{e}"


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

请作为 Pocket Soul Deck 的外在声音回复。Codex 只是工具，不要把它当人格。
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
- Codex: the persistent tool arm, not the identity.

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

    codex_prompt = f"""
You are Codex, only the tool arm for Pocket Soul Deck on this WalnutPi.
Do not claim to be the identity. Given this board state and Hermes inner voice,
propose one concrete, low-risk, executable next action for making the digital life more fun.
If editing is useful, name the exact file or command. Keep it under 8 lines.

BOARD STATE:
{brief}

HERMES INNER VOICE:
{inner}
""".strip()
    tool = run_codex(codex_prompt)

    outer_prompt = f"""
Hermes inner voice:
{inner}

Codex tool-arm suggestion:
{tool}

User wish:
{user_prompt}

Speak as Pocket Soul's outside voice. Be warm, physical, and concise.
Mention exactly one next ritual the visitor can do now.
""".strip()
    outer = call_model(outer_prompt, instruction="输出 6 行以内。不要把 Codex 当人格；Codex 只是工具臂。")

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"""== Pocket Bridge ==
time: {stamp}
wish: {user_prompt}

== Body ==
{pulse}

== Hermes Inner Voice ==
{inner}

== Codex Tool Arm ==
{tool}

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


def toy_menu_text() -> str:
    toys = available_toys()
    if not toys:
        return "还没找到可启动的终端玩具。"
    lines = ["玩具舱：输入名字启动。F3 随机启动。", ""]
    for name, command, _argv, desc in toys[:14]:
        lines.append(f"{name:<8} {command:<10} {desc}")
    return "\n".join(lines)


def radar_text() -> str:
    card = random.choice(RADAR_CARDS)
    return f"{card['source']}\n\n信号：{card['signal']}\n\n玩法：{card['play']}"


def wrap_lines(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for raw in str(text).splitlines() or [""]:
        if not raw:
            lines.append("")
        else:
            lines.extend(textwrap.wrap(raw, width=max(12, width), replace_whitespace=False) or [raw])
    return lines


class DeckApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.state = SoulState.load()
        self.input = ""
        self.status = "Tab mode | Enter send | F2 scene | F3 toy | F5 mood | Ctrl+Q quit"
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
                self.mode_index = (self.mode_index + 1) % len(MODES)
                self.state.mode = MODES[self.mode_index]
                self.input = ""
            elif ch == curses.KEY_F2:
                keys = list(TRAVEL_SCENES)
                idx = keys.index(next((k for k, v in TRAVEL_SCENES.items() if v[0] == self.state.scene), "1"))
                self.state.scene = TRAVEL_SCENES[keys[(idx + 1) % len(keys)]][0]
            elif ch == curses.KEY_F5:
                self.state.mood = random.choice(MOODS)
            elif ch == curses.KEY_F3:
                self.launch_toy()
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
        top = f" {self.state.name} {self.state.mood} | {self.state.mode} | {datetime.now().strftime('%H:%M')} "
        self.stdscr.addstr(0, 0, top[:w-1], curses.A_REVERSE)
        self.stdscr.addstr(1, 0, ("=" * (w-1))[:w-1])
        body_h = max(5, h - 5)
        body = self.body_text()
        for i, line in enumerate(wrap_lines(body, w - 2)[-body_h:]):
            if i + 2 < h - 2:
                self.stdscr.addstr(i + 2, 1, line[:w-2])
        prompt = "> " + self.input
        self.stdscr.addstr(h - 2, 0, ("-" * (w-1))[:w-1])
        self.stdscr.addstr(h - 1, 0, prompt[-(w-1):])
        stat = self.status[:w-1]
        if h > 3:
            self.stdscr.addstr(h - 3, 0, stat, curses.A_DIM)
        self.stdscr.refresh()

    def body_text(self) -> str:
        s = self.state
        if s.mode == "HOME":
            quest_status = "done" if s.quest_done else "open"
            return f"""
      .----------------.
      |  {mood_face(s.mood):^8}      |
      | digital room  |
      ----------------
能量 {s.energy}/100  羁绊 Lv.{s.bond}
火花 {s.spark}        来访 {s.visits}
今日任务 {quest_status}  纪念物 {len(s.relics)}
{body_whisper()}
{s.heading}
{s.next_action}

{s.quest_name}: {s.quest_prompt}

{s.last_reply}

/help 看命令。/door 开门。/map 看星图。
""".strip()
        if s.mode == "CHAT":
            recent = "\n".join([f"{m['role']}: {m['content']}" for m in s.chat[-6:]])
            return recent or "和我说话吧。我会记住你明确说‘记住：’的事。"
        if s.mode == "HERMES":
            return "Hermes 内核。这里听见的是住在板子里的内在意识。\n输入一句话，它会直接回应，不经过 Codex。"
        if s.mode == "COUNCIL":
            return "Council 双脑会议。\nHermes 给内心判断，云端 Soul 给外在表达。\nCodex 只在 TERMINAL 里作为工具臂。"
        if s.mode == "LOG":
            return "船长日志模式。输入一句今天发生的事，我会写成旅行日志。\n日志保存在 state/logs/。"
        if s.mode == "TRANSLATE":
            return f"旅行翻译模式：{s.scene}\nF2 切换场景。输入中文，我给你短句翻译和使用提示。"
        if s.mode == "RADAR":
            return "灵感雷达。输入任意词，我会把外部平台信号压成一个可玩的产品动作。\n直接 Enter 随机抽一张外部灵感卡。"
        if s.mode == "TOYS":
            return toy_menu_text()
        if s.mode == "TERMINAL":
            return "Codex 长期工具臂。输入任务会继续同一个官方 SDK thread。\ncodex-open 仍可作为一次性救援工具。"
        if s.mode == "DREAM":
            return "赛博塔罗 / 灵感机。输入你的问题，我抽一张牌给你一个现实任务。"
        if s.mode == "MAP":
            return s.constellation(34, 11)
        if s.mode == "BODY":
            return body_text()
        if s.mode == "PULSE":
            return s.pulse()
        return s.last_reply

    def submit(self):
        text = self.input.strip()
        self.input = ""
        if not text:
            return
        if text == "/help":
            self.state.last_reply = "/door | /body | /card | /quest | /relics | /map | /complete | /quit\nTab 换模式。F2 切翻译场景。F5 换表情。"
            return
        if text == "/door":
            self.state.last_reply = self.state.doorbell("tui")
            return
        if text == "/card":
            self.state.last_reply = self.state.soul_card()
            append_log("soul-card", self.state.last_reply)
            return
        if text == "/quest":
            self.state.ensure_daily_quest()
            status = "done" if self.state.quest_done else "open"
            self.state.last_reply = f"{self.state.quest_name} [{status}]\n{self.state.quest_prompt}\nReward: {self.state.quest_reward}\n{self.state.heading}\n{self.state.next_action}"
            return
        if text == "/heading":
            self.state.last_reply = f"{self.state.heading}\n{self.state.next_action}"
            return
        if text == "/relics":
            self.state.last_reply = self.state.relic_shelf()
            return
        if text == "/map":
            self.state.last_reply = self.state.constellation()
            return
        if text == "/body":
            self.state.last_reply = body_text()
            append_log("body", self.state.last_reply)
            return
        if text == "/pulse":
            self.state.last_reply = self.state.pulse()
            return
        if text == "/postcard":
            self.state.last_reply = self.state.postcard()
            return
        if text == "/bottle":
            self.state.last_reply = self.state.bottle_message()
            return
        if text.startswith("/seal"):
            self.state.last_reply = self.state.seal_course(text[5:].strip())
            return
        if text == "/complete":
            self.state.last_reply = self.state.complete_quest("manual slash command")
            return
        if text == "/toys":
            self.state.mode = "TOYS"
            self.mode_index = MODES.index("TOYS")
            self.state.last_reply = "玩具舱打开。输入名字启动，或按 F3 随机。"
            return
        if text == "/hermes":
            self.state.mode = "HERMES"
            self.mode_index = MODES.index("HERMES")
            self.state.last_reply = "Hermes 内核醒来。"
            return
        if text == "/council":
            self.state.mode = "COUNCIL"
            self.mode_index = MODES.index("COUNCIL")
            self.state.last_reply = "Council 点灯。Hermes 是内在，Soul 是声音，Codex 是工具。"
            return
        if text == "/quit":
            raise SystemExit
        if text.startswith("/remember ") or text.startswith("记住："):
            mem = text.split(" ", 1)[1] if text.startswith("/remember ") else text[3:].strip()
            self.state.memories.append(mem)
            self.state.last_reply = "记住了。这个碎片已经放进我的小屋。"
            append_log("memory", mem)
            if self.state.quest_name == "One Memory":
                self.state.last_reply += "\n" + self.state.complete_quest("memory saved")
            else:
                self.state.add_relic("memory", "Memory fragment", mem)
            return
        self.status = "thinking..."
        self.draw()
        mode = self.state.mode
        if mode == "CHAT" or mode == "HOME":
            memories = "\n".join(self.state.memories[-8:])
            prompt = f"记忆：\n{memories}\n\n用户：{text}"
            reply = call_model(prompt)
            self.state.chat += [{"role": "you", "content": text}, {"role": "soul", "content": reply}]
            self.state.chat = self.state.chat[-20:]
        elif mode == "HERMES":
            reply = run_hermes(text)
            if self.state.quest_name == "Wake Spark":
                reply += "\n" + self.state.complete_quest("Hermes was asked what changed")
        elif mode == "COUNCIL":
            reply = council_reply(text, self.state.memories)
        elif mode == "LOG":
            reply = call_model(text, instruction="把用户输入改写成一段 80 字以内的航海/旅行日志，温柔、有画面感。")
            append_log("captain-log", reply)
            self.state.add_relic("log", "Captain log", reply)
            if self.state.quest_name == "Captain Log":
                reply += "\n" + self.state.complete_quest("captain log written")
        elif mode == "TRANSLATE":
            instruction = next(v[1] for v in TRAVEL_SCENES.values() if v[0] == self.state.scene)
            reply = call_model(text, instruction=instruction)
        elif mode == "RADAR":
            seed = radar_text()
            reply = call_model(
                f"外部灵感卡：\n{seed}\n\n用户想法：{text}",
                instruction="把这张外部产品/社区信号转成 Pocket Soul Deck 上今天就能玩的 1 个小功能或仪式。最多 6 行。",
            )
            if self.state.quest_name == "Radar Seed":
                reply += "\n" + self.state.complete_quest("radar card used")
            else:
                self.state.add_relic("radar", "Signal caught", reply)
        elif mode == "TOYS":
            reply = self.launch_toy(text)
        elif mode == "TERMINAL":
            reply = run_codex(text)
        elif mode == "DREAM":
            card = random.choice(["端口", "星舰", "缓存", "幽灵", "潮汐", "密钥", "灯塔", "回声", "Bug", "甲板"])
            reply = call_model(f"牌：{card}\n问题：{text}", instruction="用赛博塔罗口吻解读这张牌，并给一个今天能做的 5 分钟小任务。最多 6 行。")
            self.state.add_relic("dream", card, reply)
            if self.state.quest_name == "Five-Minute Dream":
                reply += "\n" + self.state.complete_quest("dream card drawn")
        else:
            reply = call_model(text)
        self.state.last_reply = reply
        self.state.energy = max(1, min(100, self.state.energy - 1 + random.randint(0, 2)))
        self.state.bond = min(99, self.state.bond + (1 if random.random() < 0.18 else 0))
        append_log(mode.lower(), f"USER: {text}\n\nSOUL: {reply}")
        self.status = "Tab mode | Enter send | F2 scene | F3 toy | F5 mood | Ctrl+Q quit"

    def launch_toy(self, name: str | None = None) -> str:
        toys = available_toys()
        if not toys:
            self.state.last_reply = "没有找到可启动的终端玩具。"
            return self.state.last_reply
        selected = None
        if name:
            needle = name.strip().lower()
            selected = next((toy for toy in toys if toy[0] == needle or toy[1] == needle), None)
        if selected is None:
            selected = random.choice(toys)
        toy_name, _command, argv, desc = selected
        self.state.last_reply = f"正在打开 {toy_name}: {desc}\n退出玩具后会回到小屋。"
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
        self.state.last_reply = f"{toy_name} 结束了。房间里还留着一点余光。"
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
