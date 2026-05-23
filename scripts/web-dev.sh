#!/usr/bin/env bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
PIDFILE="$ROOT/state/web-dev.pid"
LOGFILE="$ROOT/state/web-dev.log"

cd "$ROOT"
mkdir -p "$ROOT/state"

case "${1:-start}" in
  start)
    if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "Miri web already running: pid $(cat "$PIDFILE")"
      exit 0
    fi
    setsid python3 pocket_web.py >"$LOGFILE" 2>&1 < /dev/null &
    echo "$!" >"$PIDFILE"
    echo "Miri web started: http://127.0.0.1:8787 pid $(cat "$PIDFILE")"
    ;;
  stop)
    if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      kill "$(cat "$PIDFILE")"
      rm -f "$PIDFILE"
      echo "Miri web stopped"
    else
      rm -f "$PIDFILE"
      echo "Miri web was not running"
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
