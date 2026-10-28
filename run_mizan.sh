#!/bin/bash
set -euo pipefail
MIZAN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIZAN_APP="$MIZAN_ROOT/Projects/Muqayyim-Downloads"
MIZAN_WEB_PORT="${MIZAN_WEB_PORT:-3100}"
export MIZAN_PYTHON="${MIZAN_PYTHON:-$MIZAN_ROOT/.venv/bin/python}"
for port in 8000 "$MIZAN_WEB_PORT"; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $port is already in use. Stop that service before launching Mizan." >&2
    exit 1
  fi
done
if [[ ! -x "$MIZAN_PYTHON" || ! -x "$MIZAN_APP/frontend/node_modules/.bin/next" ]]; then
  echo 'Install local dependencies using README.md before launching.' >&2
  exit 1
fi
if [[ ! -f "$MIZAN_APP/frontend/.next/BUILD_ID" ]]; then
  npm --prefix "$MIZAN_APP/frontend" run build
fi
api_pid=''
web_pid=''
cleanup() {
  [[ -z "$web_pid" ]] || kill "$web_pid" 2>/dev/null || true
  [[ -z "$api_pid" ]] || kill "$api_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
bash "$MIZAN_APP/start_api.sh" &
api_pid=$!
(cd "$MIZAN_APP/frontend" && exec ./node_modules/.bin/next start --hostname 127.0.0.1 --port "$MIZAN_WEB_PORT") &
web_pid=$!
echo "Mizan: http://127.0.0.1:$MIZAN_WEB_PORT/map"
# Wait for either service to exit, without requiring a newer macOS bash.
while kill -0 "$api_pid" 2>/dev/null && kill -0 "$web_pid" 2>/dev/null; do
  sleep 1
done
exit 1
