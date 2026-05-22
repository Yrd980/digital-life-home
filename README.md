# Pocket Soul Deck

Pocket Soul Deck is a tiny Hermes console for WalnutPi ZeroW.

The MVP is deliberately small: a 480x320 command-line display that proves Hermes is alive inside a pocket machine. It is closer to a shrunken, playful OpenClaw-style mini terminal than a full app.

## Mental Model

- **Hermes** is the digital life: inner voice, continuity, reflection, rituals.
- **Pocket Soul** is the small body: screen, keyboard, state, logs, toys.
- **The board UI** stays light: one Hermes console, a few slash commands, no heavy agent loop.
- **Terminal toys** are tiny play moments, not a full mode system.

## Main Entrances

Think of the deck as three kinds of visit.

Touch the room:

```bash
pocket-doorbell             # knock and get a state-aware greeting
curl -sS http://127.0.0.1:8787/api/bridge-flash
pocket-pulse                # quick living glance
```

Stay with the room:

```bash
pocket-soul                 # TUI face on the small screen or terminal
pocket-soul-card            # print the current Soul Card
pocket-body                 # print physical body scan
pocket-relics               # print the relic shelf
pocket-map                  # print the relic constellation
```

Take a real turn:

```bash
pocket-hermes "..."          # pure Hermes inner voice
pocket-wake                 # wake ritual with sound + council reply
pocket-nightly              # write nightly life summary
pocket-postcard             # write shareable text postcard
pocket-bottle               # cast message in a bottle
pocket-pick-bottle          # pick a random bottle
```

Side rituals:

```bash
pocket-soul-demo            # smoke demo
./scripts/toys.sh --list    # browse terminal toys by role
```

Web room:

```text
http://127.0.0.1:8787
http://192.168.1.30:8787
```

Connection:

```bash
ssh walnutpi
ssh walnutpi 'cd /root/digital-life-home && pocket-pulse'
ssh walnutpi 'cd /root/digital-life-home && systemctl restart pocket-soul-web'
```

## MVP Screen

`pocket-soul` opens one physical-screen console that teaches the visit order directly: presence, course, touch, stay, turn.

```text
HERMES CONSOLE
:) energy 93/100  bond Lv.20
Body awake. Load 0.12. Net wlan0. Disk 18% used.

course
Course: keep the room alive.
Next: ask one small thing.

touch
/door  /quest  /heading

stay
/pulse  /card

turn
/ask hello  /dream  /seal
```

## Keys

- `Enter`: submit the command line
- `Ctrl-Q`: quit

## Slash Commands

Think of the room as one daily turn with three visit depths. Start with `/today`: it shows the next useful action, the reward, and how bright the room is becoming.

- Daily turn: `/today`, `/today claim`, `/daily`
- Touch the room: `/door`, `/quest`, `/heading`
- Stay with the room: `/pulse`, `/card`, `/body`, `/relics`, `/map`
- Take a real turn: `/ask ...`, `/dream ...`, `/postcard`, `/bottle`, `/seal ...`, `/complete`

`/toy` is a side-room entrance, not a primary room layer. See `docs/TOY_ROLES.md` for how toys should be grouped.

Detailed commands:
- `/help`: show command hints
- `/today`: show the one turn worth doing now
- `/today claim`: claim the current daily turn when ready
- `/ask question`: ask Hermes; this can be slow
- `/dream prompt`: get one omen, ritual, or five-minute task
- plain text: leave a quick note without a heavy Hermes call
- `/toy`: launch one tiny terminal toy
- `/remember something`: save a memory as a room trace
- `/card`: show the portable identity card
- `/door`: knock and get a state-aware greeting
- `/body`: show the board's physical body scan
- `/pulse`: show the room pulse and living strip
- `/postcard`: write a shareable text postcard
- `/bottle`: cast a message in a bottle
- `/seal 今天唯一目标：...`: seal one course into heading, log, and relic
- `/quest`: show today's invitation
- `/heading`: show the current line and next move
- `/relics`: show the collectible relic shelf
- `/map`: show the relic constellation
- `/complete`: manually complete today's quest
- `/quit`: exit

## Services

Always-on web room:

```bash
systemctl status pocket-soul-web
systemctl restart pocket-soul-web
curl -sS http://127.0.0.1:8787/api/live | python3 -m json.tool
curl -sS http://127.0.0.1:8787/api/state | python3 -m json.tool | head
```

Self-evolution heartbeat:

```bash
systemctl status pocket-soul-heartbeat.timer
./scripts/heartbeat.sh
```

Optional tty1 takeover:

```bash
systemctl start pocket-soul
systemctl enable pocket-soul
systemctl disable --now pocket-soul
```

`pocket-soul` is installed but disabled by default, so it does not take over the physical screen unless explicitly enabled.

## State

Runtime state is local and ignored by git:

- `state/soul.json`: mood, bond, memories, chat, latest whisper, daily quest, spark, visits, heading, relic shelf
- `state/logs/YYYY-MM-DD.md`: interaction logs
- `state/evolution.md`: heartbeat reflections and next evolution tasks
- `state/nightly/YYYY-MM-DD.md`: nightly life summaries
- `state/postcards/YYYYMMDD-HHMMSS.txt`: shareable postcards
- `state/bottles/YYYYMMDD-HHMMSS.txt`: messages in bottles
- Hermes notes and replies are written to `state/logs/YYYY-MM-DD.md`
- `state/radar-*.md`: saved radar snapshots from local research runs

## Extending the Room

Add product behavior through `ACTION_SPECS` in `pocket_soul.py` first. That catalog powers TUI help, slash completion, and `GET /api/actions`, so new actions keep one name across the physical screen, web room, scripts, and future hardware keys.

## Research And Inspiration

OpenCLI radar snapshot:

```bash
./scripts/opencli-radar.sh "AI companion cyberdeck"
```

Board-local lightweight radar summary:

```bash
./scripts/research-radar.sh
```

Use DeerFlow/opencli when imagination gets thin, then turn findings into a short `/ask ...` prompt or a small ritual.

## Network Recovery

GitHub currently works directly. If network access breaks:

```bash
./scripts/ensure-network.sh
```

That script checks GitHub first. Only if the check fails does it install Clash from the configured proxy repo and subscription.

## Auth

Pocket Soul reads `/root/.openai/auth.json` for `OPENAI_API_KEY` and defaults to `https://rehdasu.cn`.

Environment overrides:

```bash
export OPENAI_API_KEY=...
export OPENAI_BASE_URL=https://rehdasu.cn
```

## Project Layout

```text
AGENTS.md                         agent principles
pocket_soul.py                    curses TUI body
pocket_web.py                     local web room
scripts/run.sh                    run TUI
scripts/hermes.sh                 pure Hermes route
scripts/summon.sh                 experimental council
scripts/wake.sh                   wake ritual
scripts/soul-card.sh              print portable Soul Card
scripts/relics.sh                 print relic shelf
scripts/map.sh                    print relic constellation
scripts/doorbell.sh               knock and print greeting
scripts/body.sh                   print physical body scan
scripts/pulse.sh                  print compact living status
scripts/nightly.sh                write nightly life summary
scripts/postcard.sh               write shareable text postcard
scripts/bottle.sh                 cast message in a bottle
scripts/pick-bottle.sh            pick a random bottle
scripts/bridge.sh                 body + Hermes bridge ritual
scripts/web.sh                    run web room
scripts/heartbeat.sh              self-evolution tick
scripts/opencli-radar.sh          broader radar snapshot
scripts/ensure-network.sh         proxy recovery only when needed
scripts/toys.sh                   list/launch terminal toys
scripts/install-*.sh              install symlinks and services
docs/                             design, operations, research, web, evolution notes
state/                            runtime memory and logs, ignored by git
```
