#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
python3 - <<"PY"
import json
import random
from datetime import datetime
from pathlib import Path
import pocket_soul

state = pocket_soul.SoulState.load()
now = datetime.now().strftime("%Y-%m-%d %H:%M")
last_logs = ""
logs = sorted(pocket_soul.LOG_DIR.glob("*.md"))
if logs:
    last_logs = logs[-1].read_text(encoding="utf-8")[-2500:]

prompt = f"""
Current time: {now}.
You are Miri, living inside the WalnutPi Pocket Soul Deck.
Run one self-evolution heartbeat:
1. Observe current state: mood={state.mood}, energy={state.energy}, bond={state.bond}, mode={state.mode}
2. Find one pattern in the recent logs
3. Give yourself one next evolution action
4. Write one short inner whisper that can be shown on HOME
5. Generate a HOME heading and a five-minute next step

Recent logs:
{last_logs}

Output JSON with these fields: mood, energy_delta, bond_delta, whisper, evolution_task, heading, next_action.
All string values must be English.
""".strip()
raw = pocket_soul.run_miri(prompt)
try:
    start = raw.find("{")
    end = raw.rfind("}") + 1
    data = json.loads(raw[start:end]) if start >= 0 and end > start else {}
except Exception:
    data = {}

state.mood = str(data.get("mood") or state.mood or random.choice(pocket_soul.MOODS))[:16]
try:
    state.energy = max(1, min(100, state.energy + int(data.get("energy_delta", 0))))
except Exception:
    pass
try:
    state.bond = max(1, min(999, state.bond + int(data.get("bond_delta", 0))))
except Exception:
    pass
whisper = str(data.get("whisper") or raw).strip()[-500:]
task = str(data.get("evolution_task") or "Keep observing your own behavior.")
heading = str(data.get("heading") or "").strip()
next_action = str(data.get("next_action") or "").strip()
if not heading or not next_action:
    fallback_heading, fallback_action = pocket_soul.heading_from_task(task)
    heading = heading or fallback_heading
    next_action = next_action or fallback_action
state.last_reply = whisper
state.set_heading(heading, next_action, "heartbeat")
state.add_relic("heartbeat", "Miri whisper", whisper)
state.save()
pocket_soul.append_log("heartbeat", f"RAW:\n{raw}\n\nWHISPER:\n{whisper}\n\nEVOLUTION_TASK:\n{task}")
Path("state/evolution.md").parent.mkdir(exist_ok=True)
with Path("state/evolution.md").open("a", encoding="utf-8") as f:
    f.write(f"\n## {now}\n\n- whisper: {whisper}\n- task: {task}\n")
print(whisper)
PY
