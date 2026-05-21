#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(dirname "$(readlink -f "$0")")")"
python3 - <<"PY"
import pocket_soul

checks = [
    ("cloud", lambda: pocket_soul.call_model("Say only: 小屋已点亮")),
    ("translate", lambda: pocket_soul.call_model("请问最近的地铁站在哪里？", instruction="翻译成自然英文，只输出英文短句。")),
    ("dream", lambda: pocket_soul.call_model("我今天该做什么？", instruction="用赛博塔罗口吻，最多三行，给一个 5 分钟任务。")),
]

print("== Pocket Soul Deck demo ==")
for name, fn in checks:
    print(f"\n-- {name} --")
    print(fn())
PY
