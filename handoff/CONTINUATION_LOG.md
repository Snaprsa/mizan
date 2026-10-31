# Continuation log

## 2026-10-31 — UI polish pass and in-app satellite setup (owner request: "improve the UI")

### Completed behaviour
- Satellite setup in the app: the map style panel shows three steps and a password-type field; the key is checked against Esri's `/self`, stored only in this browser (`mizan.arcgisKey`), applied with no rebuild, and removable. A build-time key still wins. The app never handles the Esri account password; sign-up stays with the owner.
- Style tiles use real map thumbnails instead of grey gradients. `/self` styles only gate modes if the listing names our style paths (its shape is unverified without a key).
- Map: tip-anchored subject pin; plain coloured dots; SAR/m² value pills at zoom >= 15; markers centred on their coordinates (they were slightly offset); fit/search frame the area not covered by the card or sheet; first load opens Explore, or the valuation in the URL.
- Valuation: value and middle-half range first, "Still needed", inputs, then disclosure rows (Adjust comparables, Evidence used, How this was calculated, Saved calculations, Settings). One Calculate button only when automatic is off. Adjustment statistics are a readable Raw/Adjusted table; raw JSON sits under Technical details.
- Shell and pages: light sidebar; "Not yet implemented" links removed from navigation (the stub routes still exist); Properties, Cases and Market data show data first with forms behind a button or disclosure; fade-in animation removed (content sat at opacity 0 when animations were paused).
- Fix: Unicode isolates stop Arabic text reordering dates in Explore rows.
- Launcher now started detached with `nohup` (log `Projects/Muqayyim-Downloads/logs/mizan-launcher.log`) because the previous background launcher stopped with the session. To stop it, TERM the `bash run_mizan.sh` process.

### Tests (31 Oct 2026)
- Backend 104 passed; frontend 18 passed (+ key precedence/placeholder/blocked storage); lint, type-check, production build pass.
- Browser (synthetic data, disposable API :8100, dev :3101 `.next-dev`): style panel, rejected key with a stubbed Esri response (not stored, message shown, nothing sent to Esri), framing, pin, valuation screens, Properties, Cases, case detail, Market data, 375 px phone layouts with no horizontal scroll. Real data viewed read-only on :3100 (19 records unchanged).
- Not verified: a real Esri key, live imagery, thumbnails with a key, address search. `docs/verify_*.py` remain outdated. Esri's terms of use, including commercial use on the free tier, have not been reviewed.

### Next step
Owner signs up and pastes the key in the map style panel; then verify satellite over Riyadh. Then structured comparable attributes and cross-method reconciliation.


## 2026-10-28 — Free imagery + Apple-style redesign (owner request)

### Decisions
- Owner: "must be free". Google Maps requires a billing-enabled Cloud project (developers.google.com/maps/get-started), so the Google renderer and `@types/google.maps` were removed. Imagery now uses Esri ArcGIS Location Platform's free tier (free account, no payment method; pay-as-you-go off by default so usage stops at the allowance). Static Basemap Tiles service URL format taken from Esri's own `esri-leaflet-static-basemap-tile` package source; no new runtime dependency. Endpoint confirmed live (returns 499 "Token Required" without a key).
- Owner: interface "should be way better, simpler, like Apple". Map page is now full-screen with one floating card (bottom sheet on phones) showing one thing at a time; navigation moved to a menu button; quiet glass controls; system font; Apple system colours.

### Completed behaviour
- `map-provider.ts`: Esri tile URLs, `/self` style listing (gates Satellite/Hybrid/Standard/Terrain), attribution from the service's `copyrightText`, Esri geocoding (country SAU, not stored, results only move the map + temporary blue marker), OSM fallback with reason.
- `map-renderer.tsx`: single Leaflet renderer (replaces google/leaflet renderers + map-canvas); handle passed as a prop (`next/dynamic` doesn't forward refs — this had broken zoom/fit in the first draft); camera reported on zoomend.
- `app/map/page.tsx` redesign: Explore (Value a property button, Sales/Listings/Properties tiles with median SAR/m², In view/All segmented control, evidence list, Data to review), record detail (grouped rows), Value a property (Location → Property type chips → Approach → Start), Filters (switches, period segmented control, place/type, quality), Data to review, open valuation (headline value first). Map style popover, Tools popover (search area, outline, measure, radius), show pin, show evidence, table, full screen, zoom. First visit frames the evidence.
- Valuation component: settings and per-input sources folded into disclosures; headline estimated value at the top; sales description updated.
- App shell: no sidebar on /map.

### Tests (28 Oct 2026)
- Backend 104 passed. Frontend 17 passed (+ Esri tile URL / geocode coordinate order / key error). Lint, type-check, production build pass.
- Browser (synthetic fixtures, disposable API :8100, dev :3101 `.next-dev`): explore, flow (pin by tap and by typed coordinates, confirm, type, approach, start), auto-calculated value, zoom/camera persistence, phone layout. Screenshots 06–09 (local).
- Not verified: live Esri imagery, terrain, geocoding — no key on this machine.

### Next step
Owner creates the free Esri key (steps in SETUP_AND_TESTS.md) → rebuild → verify satellite at a Riyadh coordinate. Then structured comparable attributes and cross-method reconciliation.


## 2026-10-28 — Increment B (part 1): professional comparable adjustment grid

### Completed behaviour
- `api/app/services/comparable_adjustments.py` (pure): per-comparable adjustment trail in SAR/m² of the comparable; transactional factors (conditions of sale → financing → market conditions) compound in order; a sourced annual time rule is compounded from each sale date to the valuation date; property factors are additive on the transaction-adjusted value; SAR lump sums ÷ comparable area (rejected without area). Only `approved` lines apply. Gross/net adjustment, heavy-adjustment (>25%) and Tukey-fence outlier flags (informational only). Exclusions require reasons and ≥3 comparables must remain. Weights: equal, inverse gross (1/(5%+gross)), manual (needs every weight + rationale). Raw vs adjusted mean/median/weighted mean/weighted median/IQR/std/CV; conclusion basis selectable; low/base/high = IQR × subject area, labelled not a confidence interval.
- Stored as `property.analysis.adjustments` (validated `AdjustmentSetup`), saved via `PUT /api/v1/analysis/{id}/adjustments` with expected revision + reason → new revision, snapshot, audit log. `save_inputs` now preserves other analysis settings (previously it would have dropped them).
- `prepare` returns `adjustment_setup` and a server-computed `adjustment_analysis` preview; runs snapshot `adjustment_setup` and the full grid in outputs. Calculation version → `mizan.map-workflow.3` (older runs show as previous versions).
- Frontend `AdjustmentGrid` in the Valuation tab: concluded value/indication, stats table, time rule, weighting/basis, per-comparable cards (trail, add/edit/approve/remove lines, manual weight, exclude/include), unsaved-change protection, reason for revision. No formulas in React; preview reflects the saved grid. Freshness signature includes the grid.
- Fixes: site outline no longer leaks from one analysis to another; selected-record card collapses to a one-line strip in the Valuation tab.

### Tests (28 Oct 2026)
- Backend 104 passed (+7 adjustment tests: default = unadjusted median, compounding order and arithmetic, approval gating, weighting/weighted median, exclusions/outliers, lump-sum/heavy flags, API persistence/stale-revision 409/inputs-save preservation/run snapshot/revision history).
- Frontend 16 passed (+ stale-on-adjustment-change). Lint, type-check, production build pass.
- Browser (synthetic fixtures, disposable API :8100, dev :3101 `.next-dev`): add/approve location +10%, approved 5%/yr time rule, inverse weights → conclusion 3,343 → 3,459 SAR/m²; auto-calculated run equals preview; exclusion → n=15; manual weighting without weights/rationale blocks conclusion; state survives reload. Screenshot `05-synthetic-adjustment-grid.jpg` (local).
- Runtime :3100/:8000 rebuilt/restarted; runtime property prepares unchanged (no grid: <3 eligible sales).

### Remaining / next
- Structured comparable attributes (street width, frontage, corner, age, condition, zoning) are not captured, so no automatic adjustment proposals or paired-sales derivation yet.
- Rental comparables / comparable-rent method, multi-method reconciliation with applicability/evidence-quality weights, and the HBU/development increment remain.
- Next: add structured comparable attributes to evidence review + subject-vs-comparable attribute grid, then reconciliation across methods.


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
