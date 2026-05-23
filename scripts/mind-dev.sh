#!/usr/bin/env bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
PIDFILE="$ROOT/state/mind-dev.pid"
LOGFILE="$ROOT/state/mind-dev.log"

find_hermes_root() {
  if [[ -n "${MIRI_RUNTIME_ROOT:-}" ]]; then
    echo "$MIRI_RUNTIME_ROOT"
    return 0
  fi
  for candidate in \
    "/usr/local/lib/hermes-agent" \
    "$HOME/documents/git_clone_code/etc/hermes-agent" \
    "$HOME/projects/hermes-agent" \
    "$ROOT/../hermes-agent"
  do
    if [[ -f "$candidate/run_agent.py" && -f "$candidate/pyproject.toml" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

cd "$ROOT"
mkdir -p "$ROOT/state"
HERMES_ROOT="$(find_hermes_root || true)"

if [[ -z "$HERMES_ROOT" ]]; then
  echo "Set MIRI_RUNTIME_ROOT to a Hermes agent checkout or install Hermes at /usr/local/lib/hermes-agent." >&2
  exit 1
fi

case "${1:-start}" in
  start)
    if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "Miri mind already running: pid $(cat "$PIDFILE")"
      exit 0
    fi
    MIRI_RUNTIME_ROOT="$HERMES_ROOT" setsid uv run --project "$HERMES_ROOT" python "$ROOT/miri_mind.py" >"$LOGFILE" 2>&1 < /dev/null &
    echo "$!" >"$PIDFILE"
    echo "Miri mind started: http://127.0.0.1:8791 pid $(cat "$PIDFILE")"
    ;;
  stop)
    if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      kill "$(cat "$PIDFILE")"
      rm -f "$PIDFILE"
      echo "Miri mind stopped"
    else
      rm -f "$PIDFILE"
      echo "Miri mind was not running"
    fi
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  status)
    if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "running pid $(cat "$PIDFILE")"
    else
      echo "not running"
    fi
    ;;
  log)
    tail -n "${2:-80}" "$LOGFILE"
    ;;
  *)
    echo "usage: $0 {start|stop|restart|status|log [lines]}" >&2
    exit 2
    ;;
esac
