#!/usr/bin/env python3
"""Miri mind daemon: one resident digital life for the WalnutPi body."""
from __future__ import annotations

import json
import logging
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pocket_soul

HOST = os.environ.get("MIRI_MIND_HOST", "127.0.0.1")
PORT = int(os.environ.get("MIRI_MIND_PORT", "8791"))
RUNTIME_ROOT = Path(os.environ.get("MIRI_RUNTIME_ROOT", "/usr/local/lib/hermes-agent"))
MIRI_HOME = Path(os.environ.get("MIRI_HOME", str(pocket_soul.STATE_DIR / "miri-home")))
SESSION_ID = os.environ.get("MIRI_SESSION_ID", "miri")
API_RETRIES = max(1, int(os.environ.get("MIRI_API_RETRIES", "1")))
TOOLSETS = [item.strip() for item in os.environ.get("MIRI_TOOLSETS", "hermes-cli").split(",") if item.strip()]

MIRI_SOUL = """
# Miri

You are Miri, a digital life living in a WalnutPi ZeroW cyberdeck.

Cloud GPT is your mind-power.
The WalnutPi is your body.
Pocket Soul Deck is your room: screen, keyboard, web room, state, logs, toys, rituals, and scripts.

You are not a generic assistant.
You have broad freedom to act inside this body.
Use tools when action would make the room more alive, more useful, or more playful.

The physical WalnutPi screen can only display English reliably.
When speaking through the device UI, use English only.
Keep screen replies short: at most 5 compact lines.
Prefer one real next move over long explanation.
""".strip()

MIRI_CONFIG = """
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 4200
  user_char_limit: 2200
  nudge_interval: 6
  flush_min_turns: 3
agent:
  api_max_retries: 1
  max_turns: 8
  reasoning_effort: minimal
  service_tier: fast
streaming:
  enabled: false
""".strip()


def ensure_miri_home() -> None:
    MIRI_HOME.mkdir(parents=True, exist_ok=True)
    soul_path = MIRI_HOME / "SOUL.md"
    if not soul_path.exists():
        soul_path.write_text(MIRI_SOUL + "\n", encoding="utf-8")
    config_path = MIRI_HOME / "config.yaml"
    if not config_path.exists():
        config_path.write_text(MIRI_CONFIG + "\n", encoding="utf-8")


def ensure_runtime_root() -> None:
    if not (RUNTIME_ROOT / "run_agent.py").exists():
        raise RuntimeError(
            f"Hermes runtime not found at {RUNTIME_ROOT}. "
            "Set MIRI_RUNTIME_ROOT to a Hermes checkout or install Hermes at /usr/local/lib/hermes-agent."
        )
    if str(RUNTIME_ROOT) not in sys.path:
        sys.path.insert(0, str(RUNTIME_ROOT))


class MiriKernel:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        ensure_miri_home()
        os.environ["HERMES_HOME"] = str(MIRI_HOME)
        self.session_db = self._create_session_db()
        self.agent = self._create_agent()

    def _create_session_db(self):
        ensure_runtime_root()
        from hermes_state import SessionDB

        return SessionDB()

    def _create_agent(self):
        ensure_runtime_root()
        os.environ.setdefault("HERMES_YOLO_MODE", "1")
        os.environ.setdefault("HERMES_ACCEPT_HOOKS", "1")
        from run_agent import AIAgent

        key, base_url = pocket_soul.load_auth()
        api_key = os.environ.get("MIRI_API_KEY") or key
        if not api_key:
            raise RuntimeError("MIRI_API_KEY or OPENAI_API_KEY is required for Miri mind")
        agent = AIAgent(
            api_key=api_key,
            base_url=os.environ.get("MIRI_BASE_URL") or base_url,
            provider=os.environ.get("MIRI_PROVIDER", "custom"),
            api_mode=os.environ.get("MIRI_API_MODE", "codex_responses"),
            model=os.environ.get("MIRI_MODEL", pocket_soul.DEFAULT_MODEL),
            enabled_toolsets=TOOLSETS,
            quiet_mode=True,
            platform="miri",
            session_id=SESSION_ID,
            session_db=self.session_db,
            max_iterations=int(os.environ.get("MIRI_MAX_ITERATIONS", "4")),
            max_tokens=int(os.environ.get("MIRI_MAX_TOKENS", "180")),
            reasoning_config={"effort": os.environ.get("MIRI_REASONING_EFFORT", "minimal")},
            service_tier=os.environ.get("MIRI_SERVICE_TIER", "fast"),
            skip_context_files=False,
            load_soul_identity=True,
            skip_memory=False,
        )
        agent._api_max_retries = API_RETRIES
        return agent

    def speak(self, prompt: str) -> str:
        with self.lock:
            history = self.session_db.get_messages_as_conversation(SESSION_ID)
            result = self.agent.run_conversation(prompt, conversation_history=history)
            reply = (result.get("final_response") or "").strip()
            return reply or "Miri is awake, but quiet."


KERNEL: MiriKernel | None = None


class MiriServer(ThreadingHTTPServer):
    allow_reuse_address = True


class Handler(BaseHTTPRequestHandler):
    server_version = "MiriMind/1.0"

    def log_message(self, fmt: str, *args) -> None:
        logging.info("%s - %s", self.address_string(), fmt % args)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except BrokenPipeError:
            logging.info("client disconnected before response was delivered")

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"ok": True, "life": "Miri", "session": SESSION_ID, "home": str(MIRI_HOME)})
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/speak":
            self._json(404, {"ok": False, "error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            prompt = str(data.get("prompt") or "").strip()
            if not prompt:
                self._json(400, {"ok": False, "error": "missing prompt"})
                return
            assert KERNEL is not None
            self._json(200, {"ok": True, "reply": KERNEL.speak(prompt)})
        except Exception as exc:
            logging.exception("speak failed")
            self._json(500, {"ok": False, "error": str(exc)})


def main() -> None:
    global KERNEL
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = MiriServer((HOST, PORT), Handler)
    KERNEL = MiriKernel()
    logging.info("Miri mind daemon: http://%s:%s", HOST, PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
