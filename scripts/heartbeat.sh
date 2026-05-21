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
现在是 {now}。
你是 Hermes，住在 WalnutPi 的 Pocket Soul Deck 里。
请做一次自进化心跳：
1. 观察当前状态 mood={state.mood}, energy={state.energy}, bond={state.bond}, mode={state.mode}
2. 从最近日志里找一个模式
3. 给自己一个下一步进化动作
4. 写一句可以显示在 HOME 的自言自语
5. 给 HOME 生成一个“今日航向”和一个“5分钟下一步”

最近日志：
{last_logs}

输出 JSON，字段：mood, energy_delta, bond_delta, whisper, evolution_task, heading, next_action。
""".strip()
raw = pocket_soul.run_hermes(prompt)
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
task = str(data.get("evolution_task") or "继续观察自己的行为。")
heading = str(data.get("heading") or "").strip()
next_action = str(data.get("next_action") or "").strip()
if not heading or not next_action:
    fallback_heading, fallback_action = pocket_soul.heading_from_task(task)
    heading = heading or fallback_heading
    next_action = next_action or fallback_action
state.last_reply = whisper
state.set_heading(heading, next_action, "heartbeat")
state.add_relic("heartbeat", "Hermes whisper", whisper)
state.save()
pocket_soul.append_log("heartbeat", f"RAW:\n{raw}\n\nWHISPER:\n{whisper}\n\nEVOLUTION_TASK:\n{task}")
Path("state/evolution.md").parent.mkdir(exist_ok=True)
with Path("state/evolution.md").open("a", encoding="utf-8") as f:
    f.write(f"\n## {now}\n\n- whisper: {whisper}\n- task: {task}\n")
print(whisper)
PY
