# Continuation log

## 2026-10-28 — Increment A/B/C: map-first workspace and imagery provider

### Current task
Satellite-map and professional-interface upgrade (`handoff/UPGRADE_PROMPT.md`), steps A–D, in the existing app.

### Starting state (observed)
- Consolidated repository root on the owner's Mac, branch `main` at `596876e`, with the intentional uncommitted handoff docs preserved.
- Running: launcher `run_mizan.sh` → API :8000 (runtime `storage/mizan.db`), `next start` :3100. Runtime map data: 19 records (1 property, 18 comparables, 0 observations), only 1 located; 19 unreviewed local dataset files.
- Baseline: 93 backend tests, 7 frontend tests passed.
- **No Google Maps key exists anywhere locally** (searched without printing values).

### Provider decision
Google Maps JavaScript API, loaded with the documented async bootstrap (`loading=async`, `importLibrary`, `v=weekly`), no new runtime npm dependency (`@types/google.maps` dev-only). Uses core `Map`, `OverlayView` (markers/clusters/subject), `Circle`/`Polygon` (editable search areas), `Polyline`, `Geocoder` (`region=SA`, precision from `location_type`), `StreetViewService` (provider-reported `imageDate`). Avoids the retired Drawing library, legacy `Marker`, `setTilt(45)` raster imagery and the retired Heatmap layer (all checked against Google's deprecations page on 28 Oct 2026). Leaflet/OSM kept only as a labelled road-map fallback behind the same renderer contract.

### Completed behaviour
- Full-bleed `/map` workspace; nav collapses to an icon rail (persisted). Slim header with search + workflow stage; collapsible layers/filters (overlay below 1280 px); central map; resizable inspector (Evidence / Subject / Valuation / Coverage); optional linked sortable table. Below 768 px the inspector stacks under the map.
- Search: decimal coordinates (never swapped silently; swap suggested), saved records, Google geocoding when available (precision labelled); plot/plan lookup explicitly unavailable.
- Subject: place by click, drag, arrow-key nudge, explicit confirmation before "Start valuation"; coordinate source/precision stored on the property (`location.coordinate_source`, `coordinate_precision`).
- Geometry: polygon and radius search areas (editable, filter the evidence list only); approximate site outline saved to the property as RFC 7946 GeoJSON with `source: user_drawn`, `cadastral: false` and a fixed disclaimer; geodesic distance/area measurement labelled approximate; keyboard alternatives (add point at map centre, Enter/Backspace/Esc).
- Evidence: separate layers with located/loaded counts; status/source/precision/reliability filters; "matching filters / loaded / pinned / in view / without location" counts; per-type unit-value summaries (n, median, IQR, period) never pooling sales, listings or observations, suppressed below 3 values; activity windows; heatmap reported unavailable (<20 located sales); unavailable layers (rent, parcels, boundaries, zoning, amenities) listed as disabled with reasons; location-resolution queue; local-file review inventory; future evidence dates flagged; RTL-safe titles.
- Synchronisation: marker/cluster ↔ list row ↔ table row ↔ selected-record card; cluster click scopes the list.
- Persistence: camera, basemap preference, subject, geometry, selection, layers, filters, panels in `localStorage` (`mizan.mapWorkspace.v1`, validated on load). Valuation panel stays mounted across tabs; an outline save now re-syncs the valuation revision while keeping unsaved inputs (previously caused a revision conflict — found and fixed in browser testing).
- Backend `/api/v1/map/records`: `south/west/north/east` bounds ([lat, lng] semantics, antimeridian-safe, validated), `location_precision`, `coordinate_source`, `has_site_outline`, `returned`, `matching_filters`, `coordinate_order`, deterministic newest-first ordering. Frontend requests once per filter change and switches to debounced, abortable viewport queries only when truncated.
- Google robustness: "ready" only after first `tilesloaded`; slow-tile warning after 15 s; `gm_authFailure` → labelled fallback with reason; bounds reported from debounced `bounds_changed`.
- Dev tooling: `MIZAN_NEXT_DIST_DIR` (dev must use `.next-dev`), `MIZAN_API_ORIGIN` proxy target; `npm run test` / `test:map` scripts.

### Changed files
- Backend: `api/app/schemas/foundation.py` (SiteOutline, coordinate provenance), `api/app/schemas/analysis.py`, `api/app/routers/analysis.py`, `api/app/routers/map.py`, `api/app/services/analysis_workflow.py`, `api/tests/test_map.py` (+4 tests).
- Frontend new: `src/lib/geo.ts`, `map-clustering.ts`, `map-evidence.ts`, `map-workspace-state.ts`, `map-provider.ts`; `src/components/app-shell.tsx`; `src/components/map/{types.ts,markers.ts,google-renderer.tsx,leaflet-renderer.tsx,map-canvas.tsx,map-search.tsx,evidence-panels.tsx}`; `tests/map-workspace.test.mjs`.
- Frontend changed: `src/app/map/page.tsx` (rewritten), `src/app/layout.tsx`, `src/app/globals.css`, `src/lib/api.ts`, `src/components/valuation-workflow.tsx` (`refreshKey`), `next.config.js`, `tsconfig.json` (`allowImportingTsExtensions`), `package.json`/lock.
- Removed (superseded): `src/components/intelligence-map.tsx`, `src/lib/map-utils.ts`.
- Docs: this log, `CURRENT_STATE.md`, `SETUP_AND_TESTS.md`, root `CLAUDE.md`, `CLAUDE_CONTINUATION.md`, local `CLAUDE_LOCAL_HANDOFF.md`, `.env.example`, `.gitignore` (`.next-dev`), screenshots in `Projects/Muqayyim-Downloads/docs/screenshots/2026-10-28-map-workspace/` (synthetic only) and runtime screenshots in `Screenshots/2026-10-28-map-workspace-private/`; both are ignored by the root `Screenshots/` rule (case-insensitive on macOS) and stay local.
- **Migrations: none.** New fields live in the existing property JSON and are optional; existing records validate unchanged.

### Tests and actual results (28 Oct 2026)
- Backend: `97 passed` (isolated in-memory SQLite).
- Frontend: `npm run test` → 15/15 (7 valuation-state + 8 map: GeoJSON vs [lat,lng] order, geodesic distance/area, area membership, coordinate parsing, 10,000-point synthetic clustering < 250 ms with no lost records, summary separation/min sample, activity/filter rules, persisted-state validation).
- `tsc --noEmit`, `next lint`, `next build`: pass.
- Browser (synthetic fixtures, disposable API :8100, dev :3101 `.next-dev`): selection sync, subject place/nudge/confirm, start valuation, required-input display, unsaved input survives tab switches and outline save, outline persisted, state survives reload, 1024 px and 375 px layouts, invalid-Google-key fallback.
- Production :3100 rebuilt and restarted via `run_mizan.sh`; runtime DB still reports 19 records.
- **Not verified:** real Google imagery/terrain, geocoding, Street View, vector rotate/tilt — blocked on a key. `docs/verify_*.py` Playwright scripts are outdated for the new UI and Playwright is not installed.

### Incident
Running `next dev` against the default `.next` overwrote the production build served on :3100 (static chunks returned 500). Fixed by stopping the dev server, rebuilding and restarting the identified launcher. Docs now require `MIZAN_NEXT_DIST_DIR=.next-dev`. The launcher was restarted from this Claude session (background process); runtime data was unaffected.

### Remaining limitations
- Live satellite imagery unverified (configuration blocker below).
- Viewport queries still project all owned rows in Python before bbox filtering (honest totals, bounded payload); SQL/PostGIS spatial indexing remains future work.
- Rental evidence has no record type yet; parcel/boundary/zoning/amenity layers have no sources.
- Search polygon filters the map list only; valuation eligibility still uses the radius.
- Workspace state is per-browser (localStorage), not per-analysis on the server.
- Full Arabic translation not done (RTL-safe text only).

### Exact next step
1. Owner: create a billing-enabled Google Cloud project, enable Maps JavaScript API + Geocoding API, create a referrer-restricted browser key, put it in `Projects/Muqayyim-Downloads/frontend/.env.local` as `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=…`, rebuild and restart. Then verify satellite/hybrid/terrain, geocoding and Street View at a Saudi location and record results here.
2. Update `docs/verify_map_ui.py` / `verify_recheck_ui.py` / `verify_map_workflow_ui.py` to the new labels.
3. Roadmap step 3–4: foundation/provenance gaps, then the professional comparables adjustment engine and reconciliation.
