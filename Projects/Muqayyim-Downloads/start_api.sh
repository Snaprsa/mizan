#!/bin/bash
# Launch the existing FastAPI application with a migrated, backed-up local database.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
PYTHON_BIN="${MIZAN_PYTHON:-$PROJECT_DIR/../../.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo 'Create the workspace .venv and install requirements-local.txt first.' >&2
  exit 1
fi
export DATABASE_URL="sqlite+aiosqlite:///$PROJECT_DIR/storage/mizan.db"
export DATABASE_URL_SYNC="sqlite:///$PROJECT_DIR/storage/mizan.db"
export ENV=development
export DEBUG=false
"$PYTHON_BIN" scripts/prepare_mizan_database.py
exec "$PYTHON_BIN" -m uvicorn api.app.main:app --host 127.0.0.1 --port "${MIZAN_API_PORT:-8000}"
