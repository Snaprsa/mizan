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

### Map imagery (Google Maps JavaScript API)

Frontend variables are inlined at build time. Put them in `Projects/Muqayyim-Downloads/frontend/.env.local` (ignored by Git), then run `npm run build` and restart the launcher.

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` | Required for satellite/hybrid/road/terrain imagery. Use a **browser key restricted** to HTTP referrers (e.g. `http://127.0.0.1:3100/*`, `http://localhost:3100/*`) and to the APIs below. |
| `NEXT_PUBLIC_GOOGLE_MAPS_MAP_ID` | Optional. A *vector* Map ID enables heading/tilt where Google supports it. Without it, rotate/tilt stay disabled. |
| `NEXT_PUBLIC_MAP_PROVIDER` | `google` (default) or `leaflet` to force the road-map fallback. |
| `NEXT_PUBLIC_MAP_TILE_URL`, `NEXT_PUBLIC_MAP_ATTRIBUTION` | Fallback road tiles (default OpenStreetMap). Never presented as satellite imagery. |

In Google Cloud: create/choose a project with **billing enabled**, enable **Maps JavaScript API** (imagery, Street View panoramas) and **Geocoding API** (address search), then create the restricted key. Usage is billed per Google's current SKU pricing; check the Google Maps Platform pricing page rather than any figure in this repo. Not used: the retired Drawing library, the legacy `Marker`, 45° raster imagery, Places, photorealistic 3D tiles.

If the key is missing, invalid, referrer-restricted or billing is disabled, Google calls `gm_authFailure`; Mizan then switches to the labelled road map with the reason shown and keeps all selections, geometry and unsaved inputs. "Ready" is reported only after Google imagery tiles actually load. Google does not expose satellite capture dates through this API, so none are shown; Street View shows the provider-reported panorama date when present.

Verifying live imagery: after configuring the key, open `/map`, choose **Satellite**, search a Saudi coordinate (e.g. `24.7136, 46.6753`) and confirm imagery, Google attribution and the absence of the fallback banner.

### Other

Existing backend settings are defined in `api/app/config.py`. `MIZAN_API_ORIGIN` (frontend server env) retargets the `/api` proxy (default `http://127.0.0.1:8000`). `MIZAN_NEXT_DIST_DIR` sets the Next.js build directory; use `.next-dev` for any dev server so it cannot overwrite the production build served by the launcher.

Preserve `Projects/Mizan-Antigravity` alongside the active app: the current calculation adapter loads its preserved classes by relative path.

## Backend tests

```bash
cd Projects/Muqayyim-Downloads
../../.venv/bin/python -m pytest api/tests -q
```

Tests use isolated SQLite. The map-upgrade run on 28 October 2026 passed 97 backend tests (93 at public-source preparation). Follow the current CI result for clean-install verification.

## Frontend checks

```bash
npm --prefix Projects/Muqayyim-Downloads/frontend run test        # valuation-state + map workspace tests
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
