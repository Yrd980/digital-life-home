# Pocket Soul Deck

Pocket Soul Deck is a living cyberdeck system for WalnutPi ZeroW.

It is not just a command line. The board is a physical body: 480x320 screen, KeebDeck keyboard, audio, WiFi, terminal toys, local logs, local memory, a web room, Hermes inner consciousness, and cloud reasoning.

## Mental Model

- **Hermes** is the inner consciousness: continuity, reflection, self-evolution, rituals.
- **Pocket Soul** is the outer body and voice: TUI, web room, state, logs, modes.
- **Cloud GPT** is the imagination and synthesis brain.
- **Codex** is only the tool arm: edit files, run commands, repair systems, build things. It is not the identity.
- **Terminal toys** are room organs and rituals.
- **last30days / opencli / DeerFlow** are external inspiration radars when ideas run low.

## Main Entrances

```bash
pocket-soul                 # TUI face on SSH, serial, or tty
pocket-hermes "..."          # pure Hermes inner voice
pocket-wake                 # wake ritual with sound + council reply
pocket-soul-demo            # smoke demo
pocket-soul-card            # print the current Soul Card
pocket-relics               # print the relic shelf
pocket-map                  # print the relic constellation
pocket-doorbell             # knock and get a state-aware greeting
pocket-body                 # print physical body scan
pocket-pulse                # print tiny living status screen
pocket-nightly              # write nightly life summary
pocket-postcard             # write shareable text postcard
pocket-bottle               # cast message in a bottle
pocket-pick-bottle          # pick a random bottle
pocket-bridge "..."         # Hermes + body + Codex tool-arm bridge
codex-thread "..."           # persistent Codex SDK thread tool arm
codex-thread --new "..."     # reset the tool-arm thread
codex-open "..."             # one-shot rescue tool arm
```

Web room:

```text
http://192.168.1.30:8787
```

## Modes

- `HOME`: digital room, mood, energy, bond, latest whisper
- `Daily Quest`: one small daily ritual that can be completed from TUI or web
- `Soul Card`: portable identity/status card with mood, bond, spark, and current quest
- `Relics`: tiny collectible traces from quests, dreams, toys, memories, and heartbeats
- `Doorbell`: state-aware greeting when someone visits the room
- `BODY`: physical senses: temperature, load, uptime, disk, network
- `PULSE`: compact living status screen for idle display
- `Nightly`: daily life summary written from logs, body, quest, relics
- `Postcard`: shareable snapshot of today's pulse, heading, body, and map
- `Bottle`: message in a bottle for a future visit
- `Bridge`: shell and web ritual that joins body state, Hermes inner voice, cloud voice, and the persistent Codex tool arm
- `Bridge Flash`: instant no-reload web/body echo that leaves a fast relic without waiting for a full Bridge turn
- `Vitals`: breathing first-screen body strip with live energy, bond, spark, visits, latest relic, and clickable/reusable touch trail
- `CHAT`: short companion chat with local memory
- `HERMES`: pure Hermes inner consciousness
- `COUNCIL`: Hermes inner voice + cloud Soul outer voice
- `LOG`: captain/travel log writer
- `TRANSLATE`: travel phrase translator; `F2` changes scene
- `RADAR`: external community/product inspiration cards turned into toy rituals
- `TOYS`: launch terminal toys such as `cbonsai`, `cmatrix`, `fortune`, `ninvaders`, `vitetris`
- `TERMINAL`: calls Codex through persistent `codex-thread`
- `DREAM`: cyber tarot / inspiration task
- `MAP`: relic constellation grown from the room's played moments

## Keys

- `Tab`: switch mode
- `Enter`: send
- `F2`: switch translation scene
- `F3`: launch a random terminal toy
- `F5`: random mood
- `Ctrl-Q`: quit

## Slash Commands

- `/help`: show command hints
- `/remember something`: save a memory
- `记住：something`: save a memory in Chinese
- `/card`: show the current Soul Card
- `/door`: knock and get a state-aware greeting
- `/body`: show the board's physical body scan
- `/pulse`: show compact living status screen
- `/postcard`: write a shareable text postcard
- `/bottle`: cast a message in a bottle
- `/seal 今天唯一目标：...`: seal one course into heading, log, and relic
- `/quest`: show today's quest
- `/heading`: show Hermes-derived heading and 5-minute next action
- `/relics`: show the collectible relic shelf
- `/map`: show the relic constellation
- `/complete`: manually complete today's quest
- `/hermes`: jump to Hermes mode
- `/council`: jump to Council mode
- `/toys`: jump to toy launcher
- `/quit`: exit

## Services

Always-on web room:

```bash
systemctl status pocket-soul-web
systemctl restart pocket-soul-web
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
- bridge entries are written to `state/logs/YYYY-MM-DD.md` and leave bridge relics in `state/soul.json`
- `state/codex-thread.json`: persistent Codex SDK thread id
- `state/last30days/`: deeper external radar output

## Research And Inspiration

Fast local/in-repo radar summary:

```bash
./scripts/research-radar.sh
```

Deep last-30-days radar, controlled external engine:

```bash
./scripts/last30days.sh "AI companion cyberdeck"
```

On this board, last30days can be slow. Use DeerFlow/opencli from the host for broader research, then feed findings back into `RADAR`, `HERMES`, or `COUNCIL`.

## Network Recovery

GitHub currently works directly. If network access breaks:

```bash
./scripts/ensure-network.sh
```

That script checks GitHub first. Only if the check fails does it install Clash from the configured proxy repo and subscription.

## Auth

Pocket Soul reads `/root/.codex/auth.json` for `OPENAI_API_KEY` and defaults to `https://rehdasu.cn`.

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
scripts/summon.sh                 Hermes + Soul + Codex council
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
scripts/bridge.sh                 body + Hermes + Codex bridge ritual
scripts/web.sh                    run web room
scripts/heartbeat.sh              self-evolution tick
scripts/last30days.sh             controlled external radar
scripts/ensure-network.sh         proxy recovery only when needed
scripts/toys.sh                   list/launch terminal toys
scripts/codex-thread.mjs           official Codex SDK persistent thread
scripts/codex-thread.sh            shell wrapper for persistent thread
scripts/codex-open.sh              one-shot fully-open rescue tool arm
scripts/install-*.sh              install symlinks and services
docs/                             design, operations, research, web, evolution notes
state/                            runtime memory and logs, ignored by git
```


## Codex SDK Thread

`codex-thread` uses the official `@openai/codex-sdk` package as the default tool arm. It persists a thread id in:

```text
state/codex-thread.json
```

That means the Codex tool arm can continue the same long-running collaboration instead of starting from scratch each time.

```bash
codex-thread --new "start a new tool-arm thread"
codex-thread "continue the same task"
```

Pocket Soul `TERMINAL` mode and `run_codex()` now prefer this persistent SDK thread. `codex-open` remains available for one-shot rescue operations.

Official shape:

- TypeScript SDK: continue the same thread with repeated `thread.run(...)`.
- TypeScript SDK: resume a stored thread with `resumeThread(threadId)`.
- App Server: lower-level JSON-RPC with `Thread / Turn / Item` primitives.

Current implementation uses the SDK route because it gives durable continuity with little ceremony. The app-server route is the next upgrade if Pocket Soul needs live streaming turns, richer event handling, or another process talking to Codex as a long-running local service.
