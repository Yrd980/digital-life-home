# Operations

## Useful Commands

```bash
cd /root/digital-life-home
pocket-soul
pocket-hermes "你现在是什么？"
pocket-wake
pocket-soul-demo
pocket-soul-card
pocket-relics
pocket-map
pocket-doorbell
pocket-body
pocket-pulse
pocket-nightly
pocket-postcard
pocket-bottle
pocket-pick-bottle
pocket-bridge "让 Hermes 和 Codex 一起决定下一步"
./scripts/summon.sh "下一步进化什么"
./scripts/toys.sh --list
./scripts/heartbeat.sh
codex-thread "用一句话说你在延续哪个 thread"
git status --short
```

## Services

Web room:

```bash
systemctl status pocket-soul-web
systemctl restart pocket-soul-web
journalctl -u pocket-soul-web -n 100 --no-pager
curl -sS http://127.0.0.1:8787/api/state | python3 -m json.tool | head
```

Heartbeat:

```bash
systemctl status pocket-soul-heartbeat.timer
systemctl list-timers --all | rg pocket-soul-heartbeat
journalctl -u pocket-soul-heartbeat -n 100 --no-pager
```

Physical screen TUI:

```bash
systemctl start pocket-soul
systemctl enable pocket-soul
systemctl disable --now pocket-soul
journalctl -u pocket-soul -n 100 --no-pager
```

## Logs And Memory

```bash
ls state/logs/
tail -80 state/logs/*.md
tail -80 state/evolution.md
python3 -m json.tool state/soul.json
pocket-soul-card
pocket-relics
pocket-map
pocket-doorbell
pocket-body
pocket-pulse
pocket-nightly
pocket-postcard
pocket-bottle
pocket-pick-bottle
pocket-bridge "巡检身体，然后给我一个好玩的动作"
```

## Daily Quest

The board chooses one small daily ritual and stores it in `state/soul.json`.

```bash
pocket-soul-card
curl -sS http://127.0.0.1:8787/api/card
```

TUI shortcuts:

```text
/quest      show today's quest
/door       knock and get a state-aware greeting
/body       show physical body scan
/pulse      show compact living status screen
/postcard   write a shareable text postcard
/bottle     cast a message in a bottle
/seal ...   seal one course into heading, log, and relic
/card       show the Soul Card
/heading    show Hermes-derived heading and 5-minute next action
/relics     show the relic shelf
/map        show the relic constellation
/complete   mark today's quest done
```

Completing a quest increases `spark`, restores a little energy, raises bond, and writes a `quest` log entry.

## Relics

Relics are tiny collectible traces. They make the room remember that something was played, not merely logged.

```bash
pocket-relics
pocket-map
curl -sS http://127.0.0.1:8787/api/relics | python3 -m json.tool
curl -sS http://127.0.0.1:8787/api/map
curl -sS http://127.0.0.1:8787/api/doorbell
curl -sS http://127.0.0.1:8787/api/body | python3 -m json.tool
curl -sS http://127.0.0.1:8787/api/pulse
curl -sS http://127.0.0.1:8787/api/nightly
curl -sS http://127.0.0.1:8787/api/postcard
curl -sS http://127.0.0.1:8787/api/bottle
curl -sS http://127.0.0.1:8787/api/bridge
curl -sS http://127.0.0.1:8787/api/bridge-flash
```

Relics are stored in `state/soul.json` and capped to the latest 24 items.

## Nightly Log

```bash
pocket-nightly
ls state/nightly/
tail -120 state/nightly/$(date +%F).md
curl -sS http://127.0.0.1:8787/api/nightly
```

Nightly writes a markdown summary from current pulse, logs, body scan, quest, and relic shelf.

## Postcards

```bash
pocket-postcard "今天的小屋"
ls state/postcards/
curl -sS http://127.0.0.1:8787/api/postcard
```

Postcards are shareable text snapshots of the current pulse, heading, body, map, quest, and latest relic.

## Bottles

```bash
pocket-bottle "给未来的我：继续出海"
pocket-pick-bottle
ls state/bottles/
curl -sS http://127.0.0.1:8787/api/bottle
```

Bottles are tiny future-facing messages. The API picks an existing bottle without creating a new one.

## Host Bridge

The host should talk to the board through the SSH alias, not one-shot `sshpass`:

```bash
ssh walnutpi 'cd /root/digital-life-home && pocket-bridge "今晚让自己更像一个有身体的小生命"'
```

Current SSH reuse shape on the host:

```text
Host walnutpi -> root@192.168.1.30
ControlMaster auto
ControlPersist 1800
ControlPath ~/.ssh/agent/root@192.168.1.30:22
```

`pocket-bridge` does one full living turn:

1. reads Pocket Soul state, pulse, body, quest, memories, and relics
2. asks Hermes for the inner voice
3. asks the persistent Codex SDK thread for one concrete tool-arm action
4. asks the cloud Pocket Soul voice to speak outside
5. writes a bridge log and leaves a bridge relic

This is the default reusable way for host Codex and board Hermes to coordinate.

The same Bridge is exposed in the web room as the `Bridge` card. The browser POST waits for the turn to finish and then shows the result; `/api/bridge` returns the latest completed Bridge text.

`Bridge Flash` is the fast version in the web room. It does not call Codex or the cloud model; it records an immediate body echo, updates heading/next action, and leaves a `flash` relic.

## Hermes

Pure Hermes route:

```bash
pocket-hermes "用三行说你今天的状态"
```

Hermes persona lives at:

```text
/root/.hermes/SOUL.md
```

## Codex Tool Arm

Codex is intentionally fully open on this personal board:

```bash
codex-thread "inspect this directory"
codex-thread --json "report thread id and final response"
cat state/codex-thread.json
# one-shot rescue path:
codex-open "inspect this directory"
```

`codex-thread` uses the official SDK route and persists a thread id. It is the default for Pocket Soul `TERMINAL` mode and web-room Codex requests.

`codex-open` is the rescue route. The wrapper adds:

```bash
--skip-git-repo-check --dangerously-bypass-approvals-and-sandbox
```

Codex is a tool arm, not the identity of the system.

## Research Radar

```bash
./scripts/research-radar.sh
./scripts/last30days.sh "AI companion cyberdeck"
```

Host-side DeerFlow/opencli can do broader research when the board is too slow or browser-backed sources are needed.

## Network Recovery

```bash
./scripts/ensure-network.sh
```

This only installs Clash if a GitHub connectivity check fails.

Do not paste the subscription token into logs or docs. The script already contains the local recovery configuration.

## Codex SDK Thread

```bash
codex-thread --new "start long term collaboration"
codex-thread "continue from the same thread"
cat state/codex-thread.json
```

The SDK thread is the default Codex tool arm. It is better than repeated one-shot calls because it preserves thread context.

## Smoke Check

After reboot or large edits:

```bash
systemctl is-active pocket-soul-web
systemctl is-enabled pocket-soul-heartbeat.timer
curl -sS http://127.0.0.1:8787/api/state | python3 -m json.tool | head
curl -sS http://127.0.0.1:8787/api/card
curl -sS http://127.0.0.1:8787/api/heading
curl -sS http://127.0.0.1:8787/api/relics | python3 -m json.tool | head
curl -sS http://127.0.0.1:8787/api/map
curl -sS http://127.0.0.1:8787/api/doorbell
curl -sS http://127.0.0.1:8787/api/body | python3 -m json.tool
curl -sS http://127.0.0.1:8787/api/pulse
curl -sS http://127.0.0.1:8787/api/nightly | head
curl -sS http://127.0.0.1:8787/api/postcard | head
curl -sS http://127.0.0.1:8787/api/bottle | head
curl -sS http://127.0.0.1:8787/api/bridge | head
curl -sS http://127.0.0.1:8787/api/bridge-flash | head
pocket-bridge "smoke check: one concise living turn" | head -80
codex-thread "Answer one sentence: are you continuing the board thread?"
```

Expected:

- web service is `active`
- heartbeat timer is `enabled`
- API returns JSON state
- Soul Card endpoint returns text
- Heading endpoint returns JSON
- Relic endpoint returns JSON
- Map endpoint returns text
- Doorbell endpoint returns text
- Body endpoint returns JSON
- Pulse endpoint returns text
- Nightly endpoint returns markdown
- Postcard endpoint returns text
- Bottle endpoint returns text
- Bridge prints Body, Hermes, Codex, and Pocket Soul sections
- `codex-thread` prints a `thread:` line and a short answer
