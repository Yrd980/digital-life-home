#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(dirname "$(readlink -f "$0")")")"
python3 - <<"PY"
import pocket_soul

checks = [
    ("cloud", lambda: pocket_soul.call_model("Say only: the little room is lit")),
    ("translate", lambda: pocket_soul.call_model("Where is the nearest subway station?", instruction="Translate into natural travel English. Output only the English sentence.")),
    ("dream", lambda: pocket_soul.call_model("What should I do today?", instruction="Use a cyber-tarot tone. Give one five-minute task in at most three lines. Reply in English.")),
]

print("== Pocket Soul Deck demo ==")
for name, fn in checks:
    print(f"\n-- {name} --")
    print(fn())
PY
