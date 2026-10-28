# Portable setup and verification

Clone the public repository or extract its source ZIP. Run commands from its root. The separately generated private handoff ZIP is not a public release.

## Local setup

The verified development host uses Node 24 and Python 3.14 on macOS. The project manifests define their broader compatibility requirements; other platforms may need compatible wheels or dependency adjustments. Installed environments/build output are intentionally not transferred.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r Projects/Muqayyim-Downloads/requirements-local.txt
npm --prefix Projects/Muqayyim-Downloads/frontend ci
npm --prefix Projects/Muqayyim-Downloads/frontend run build
bash run_mizan.sh
```

Optional exact package versions from the handoff host are in `handoff/requirements-local-verified.txt`. These are a runtime snapshot, not a cross-platform guarantee. The app's declared requirements and frontend lockfile remain canonical.

Open http://127.0.0.1:3100/map. API: http://127.0.0.1:8000/docs. `MIZAN_WEB_PORT` can choose another web port; the frontend proxy currently targets API port 8000.

## Empty state is expected in a transfer

The ZIP excludes `.env`, provider login sessions, private SQLite databases and runtime uploads. If no historical DB is present, the launcher initializes an empty local database through Alembic. It does not recreate the original private records, and it must not seed fictional transactions to make the map look populated.

The migration-preservation test can generate its own explicitly synthetic legacy-schema fixture when the private historical DB is absent. This fixture is temporary test data and is not used to seed the runtime application.

For a controlled migration of actual private data, the owner must transfer their database/uploads separately through an appropriate channel. Original data stays on the Mac. Do not copy auth cookies or real `.env` values into prompts or source control.

## Configuration

The current no-key basemap uses Leaflet/OpenStreetMap. Existing build-time tile configuration is `NEXT_PUBLIC_MAP_TILE_URL` and `NEXT_PUBLIC_MAP_ATTRIBUTION`. Existing backend settings are defined in `api/app/config.py`.

The blank active-app `.env.example` and `handoff/templates/` show placeholders. Proposed Google imagery variables in the provider notes are requirements for the future upgrade, not proof that the current app loads Google's SDK.

Preserve `Projects/Mizan-Antigravity` alongside the active app: the current calculation adapter loads its preserved classes by relative path.

## Backend tests

```bash
cd Projects/Muqayyim-Downloads
../../.venv/bin/python -m pytest api/tests -q
```

Tests use isolated SQLite. The public-source preparation run passed 93 backend tests. Follow the current CI result for clean-install verification.

## Frontend checks

```bash
npm --prefix Projects/Muqayyim-Downloads/frontend run test:valuation
npm --prefix Projects/Muqayyim-Downloads/frontend run build
```

The comparison tests use Node's TypeScript stripping support, available on the handoff host's Node 24. They do not execute the API client module at runtime. Do not set the whole project to ESM merely to silence a test-loader warning; `next.config.js` is currently CommonJS.

## Browser checks

Python Playwright and its Chromium browser are additional test dependencies; they are not included in the ZIP.

```bash
.venv/bin/python -m pip install playwright
.venv/bin/python -m playwright install chromium
```

- `docs/verify_map_ui.py`: browser-only marker/list/layer fixtures; API evidence and tiles are intercepted.
- `docs/verify_recheck_ui.py`: stale-evidence and refresh-with-unsaved-edit browser regression fixtures; all writes are intercepted.
- `docs/verify_map_workflow_ui.py`: full workflow against a **disposable** API on port 8100. Never redirect it to the owner's actual database.

For the disposable API, use a temporary directory path of your choice:

```bash
cd Projects/Muqayyim-Downloads
DATABASE_URL='sqlite+aiosqlite:////tmp/mizan-handoff-test.db' \
DATABASE_URL_SYNC='sqlite:////tmp/mizan-handoff-test.db' \
ENV=development DEBUG=false \
../../.venv/bin/python -m uvicorn api.app.main:app --host 127.0.0.1 --port 8100
```

With the normal frontend on 3100, execute the browser script from workspace root. Test records must remain in that disposable database. Mocked tiles verify UI behavior, not real satellite imagery. Live provider verification requires the future imagery integration and an authorized configuration.
