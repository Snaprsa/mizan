# Mizan: satellite property-intelligence map and professional interface upgrade

You are continuing an existing application called Mizan, a Saudi real-estate valuation, underwriting and investment-intelligence platform. Work directly in the attached source repository. Do not rebuild it from scratch, replace functioning modules with placeholders, or spend the task producing another plan without implementation.

Read `00_START_HERE.md`, `handoff/CURRENT_STATE.md`, `handoff/FILE_MAP.md` and `handoff/SETUP_AND_TESTS.md` first. Inspect the actual implementation before editing. Preserve the user's latest instructions and all usable existing work.

The wider platform requirements are preserved in `handoff/PRODUCT_SCOPE.md`. Keep that architecture extensible, while completing this map/interface upgrade as the immediate task.

## 1. The result I want

Make Mizan feel like a professional property-intelligence workstation whose main workspace is a rich interactive map with real satellite imagery. The map must support examining a site and the evidence around it, not merely display a few pins on a basic road basemap.

The core journey is:

**Explore map and existing evidence → select a site or existing asset → select property type → select valuation approach → automatically gather supported information → show only required missing inputs → calculate → inspect assumptions, evidence and saved results.**

Before starting an analysis, the user should already be able to understand what data exists in the visible area: properties, completed transactions, asking listings, rental evidence and registered market observations. Keep that context accessible during valuation. A satellite map must render *inside Mizan*; a Google Maps link, iframe-only substitute, static screenshot, decorative background or AI-generated aerial image does not satisfy this requirement.

## 2. Inspect and preserve the foundation

The active app is `Projects/Muqayyim-Downloads`: Next.js 14, React 18, TypeScript, Tailwind and Lucide; FastAPI, Pydantic, async SQLAlchemy, SQLite locally and PostgreSQL-oriented Alembic migrations. The current map is Leaflet/OpenStreetMap.

Reuse the owner-scoped map projection, reviewed field overrides, property/case entities, method requirements catalog, preparation service, source registry, assumption provenance, immutable revisions and calculation snapshots. Retain the existing five initial calculation methods and their tests. Income/DCF/cost use preserved Mizan classes through a sibling-project adapter.

Replacing or refactoring the map renderer and map screen is authorized because those are the requested upgrade. Rebuilding authentication, every valuation model or the entire app simultaneously is not the task. Preserve existing case/source/comparable review and exports. Record necessary migrations and dependency changes explicitly.

## 3. Use a real imagery provider

Prefer an official Google Maps JavaScript API integration with actual satellite and hybrid imagery, if an appropriately configured project/key is available. Keep a thin provider boundary so a licensed MapLibre-based imagery implementation can be substituted deliberately if Google is unsuitable. Implement one primary provider well rather than two incomplete engines.

Required basemap modes:

- **Satellite**: actual aerial/satellite imagery.
- **Hybrid**: imagery with readable road/place labels.
- **Road map**: contextual reference.
- **Terrain**: where the chosen provider supports it, otherwise clearly unavailable.

Satellite or hybrid should be the default for site inspection. Switching basemaps must preserve subject selection, evidence overlays, camera position, radius/polygon, selected comparable and unsaved valuation inputs.

Add provider-supported 3D/tilt/rotation, terrain and Street View as capability-gated enhancements. Check coverage at the selected Saudi location. Do not promise photorealistic buildings, historical imagery, a particular image date or nationwide feature coverage without provider evidence. Display available imagery attribution and dates accurately; say unavailable when the provider does not expose them. Never call provider imagery a live camera feed.

Use official SDKs/services and permitted tile sources. Preserve attribution. Do not scrape Google tiles or copy an unrestricted public imagery endpoint without checking its intended use and licensing. Client map keys must be appropriate restricted browser keys; server secrets must remain server-side. Document enabled APIs, domains, map IDs where needed, configuration variables and billing implications without inventing exact current prices.

**Compatibility matters:** as checked on 28 October 2026, Google's old Drawing Library and automatic raster 45-degree imagery were retired in May 2026. Do not build on `google.maps.drawing.DrawingManager`, `libraries=drawing`, or the old automatic `setTilt(45)` raster-imagery behavior. Recheck current documentation and use a supported drawing implementation, such as a verified compatible Terra Draw adapter or a properly tested custom interaction. Modern vector/3D camera features must be evaluated on their own supported API.

If a paid account/key is missing, complete the provider abstraction, configuration, UI, state preservation, overlays and independent tests first. Clearly identify what remains blocked on configuration. Do not purchase services or claim imagery is working when only a road-map fallback or mocked tiles were tested. Keep the app usable while the user configures access.

## 4. Build a map-first interface

The map should occupy roughly two-thirds or more of the working area on desktop, with resizable/collapsible panels. Reuse Mizan's restrained blue/slate brand and improve its composition, density and interaction quality.

Suggested structure:

- Slim header: project/subject name, search, current workflow stage and essential actions.
- Compact left layer/filter drawer, collapsible to icons.
- Large central map canvas.
- Right inspector with clear Evidence / Subject / Valuation / Results modes or tabs.
- Optional collapsible bottom comparable table linked to the same selection.

Do not stack long configuration forms and large cards above the map. Keep essential spatial context visible while editing assumptions or comparing evidence. Show compact financial values; put provenance and explanatory details behind accessible disclosure controls. Use readable tables and meaningful empty/loading/error states. Avoid excessive gradients, animation and generic dashboard cards.

Keep the evidence list/table accessible while a valuation is open. Selected markers, table rows, inspector details and highlighted map geometry must stay synchronized. Keyboard users need a coordinate-entry/search alternative to mouse-only point placement. Use sensible focus management, labels, contrast, touch targets, responsive layouts and English/Arabic/RTL-ready formatting. Financial values must retain clear SAR and area/time units.

## 5. Map interactions

Implement:

1. Search by coordinates, address or place name through an available authorized service; distinguish exact selection from approximate geocoding. Plot/plan-number lookup must not pretend to work without a supporting source.
2. Place, drag and confirm a subject pin; select an existing property as the subject.
3. Draw/edit a search polygon or radius. Save geometry and its provenance with the asset/analysis.
4. Geodesic distance and area measurement, labelled approximate. A user-drawn outline is not a certified cadastral boundary.
5. Fit subject, fit evidence, reset north, scale and fullscreen controls.
6. Record selection, cluster expansion and a spatial query that updates the adjacent evidence/table.
7. Persist relevant map/workflow state so navigation, method changes, imagery switches and refresh do not lose the user's work.

Use GeoJSON consistently at boundaries: GeoJSON positions are `[longitude, latitude]`, while the existing Leaflet records use `[latitude, longitude]`. Make conversion explicit and test it. Retain source CRS/precision metadata when importing geometry. Never swap coordinates silently.

## 6. Evidence layers and spatial intelligence

Provide independently controlled, clearly styled layers for subject/owned properties, achieved sales, asking listings, rental evidence when genuinely available, and market observations. Make the legend and data provenance accessible.

Support clustering, selected-record highlighting, date ranges, property-type filters, source/status/reliability filters and search within the visible area or drawn geometry. Distinguish the total matching records from the loaded/rendered subset. Preserve stable IDs and explain truncation instead of hiding data.

Show recent activity counts, price/rent summaries and distributions only when records have compatible units, geography and evidence types. Never merge asking prices with achieved sales, or annual rents with sale prices. Deduplicate equivalent evidence conservatively and disclose uncertainty in record-level counts.

Density/price heatmaps must be calculated from actual suitable observations, with sample size, metric/unit, period and clear legend. Insufficient samples mean unavailable/insufficient data, not a fabricated colorful heatmap. Aggregated area observations can be represented by appropriate sourced geography or an area-level data panel; never turn an aggregate or missing coordinate into an exact transaction pin.

Design layer adapters for authorized parcel boundaries, district/municipality boundaries, zoning, amenities, roads and development projects. Render only datasets actually connected, with source and update information. Unavailable layers must be clearly disabled. Do not infer legal ownership, permitted uses, FAR, building age, occupancy or sale prices merely from satellite images.

All existing data must be accounted for in the workspace:

- Located records appear in the correct map layer.
- Approximate/area-only observations expose their spatial precision.
- Missing-location records remain searchable in a location-resolution queue.
- Local CSV/XLSX candidate files appear in an import/review inventory with status and source limitations.

The current data pool is sparse and contains unverified legacy material. Inspect and classify it before import. Do not rename sample/synthetic/aggregate data as verified transactions just to populate the map.

## 7. Valuation integration

After the user chooses location, property type and approach, open that method's required-input panel. Prefill only from compatible saved facts, assumptions and authorized observations. Show origin, unit, date and uncertainty for important values. Missing facts stay missing; manual entries are clearly user assumptions.

Preserve automatic calculation once both the input requirements and evidence/readiness rules are satisfied. Do not require repetitive source forms for every manual entry: use explicit user-input provenance with editable details. Keep saved assumptions, revisions and prior results accessible.

Maintain existing protections:

- Three distinct, active, dated, nearby achieved transactions are required for the current sales baseline.
- Unknown district cannot borrow a different district's benchmark.
- Saved result freshness compares actual inputs, selected evidence and calculation version, not just property revision.
- Refresh fills untouched missing fields without overwriting unsaved edits.
- Reopening unchanged analysis does not create duplicate runs.
- Confidence remains uncalibrated/unknown unless there is a defensible model.

The existing methods are initial sales comparison, income capitalization, annual unlevered DCF, cost/DRC and static residual land. Do not imply that complete institutional underwriting, debt, HBU, recommendations or automated public-market ingestion already exists.

## 8. Technical quality and scope

Separate map rendering, provider integration, spatial state, data querying, inspector UI and financial calculation logic. Preserve backend ownership/provenance rules and historical IDs. Use additive migrations where required; never drop the user's database to make the new map work.

For larger datasets, implement bounded geographic queries and aggregation rather than loading every record and filtering all rows on each move. Plan PostGIS for deployment while retaining a working local development path. Test rendering/state with a 10,000-point *test fixture*, without adding fictional records to the runtime DB or hammering real imagery endpoints.

Debounce/cancel stale requests, preserve unsaved edits, dispose map listeners/resources correctly and avoid remounting the map on every form change. Provider errors, quota failures, unavailable imagery and missing keys need explicit recoverable states. Keep the comparable list usable when the basemap fails.

## 9. Acceptance criteria

The upgrade is complete only when you can demonstrate:

1. Real satellite imagery renders inside Mizan for a supported Saudi location with an authorized provider configuration.
2. Satellite/hybrid/road modes work and keep all selections, layers and unsaved inputs intact.
3. The user can choose a site and approach without leaving the map, and the correct required inputs appear.
4. Subject selection, markers/clusters, evidence rows and details stay synchronized.
5. Polygon/radius selection and measurement work, with geometry/precision persisted and labelled correctly.
6. Located, area-level, missing-location and unreviewed-file data each have an honest visible place in the interface.
7. Missing data never produces invented transactions, parcel boundaries, valuation values or confidence.
8. Saved input/history, geography-specific filling and stale-evidence regression tests still pass.
9. Desktop and narrower layouts remain usable, with keyboard-accessible alternatives.
10. Build/tests pass and the report distinguishes mocked tests from actual provider/imagery verification.

## 10. How to execute

Start with a short assessment of the current map/UX and a concrete provider decision with configuration implications. Then implement incrementally:

A. Real imagery provider plus the new map-dominant shell.
B. Synchronized evidence/inspector, spatial selection and saved state.
C. Data coverage/import/location-resolution UX and scalable spatial querying.
D. Valuation integration polish, regression tests, responsive/accessibility checks and verification.

Do not redesign every unrelated screen. Do not stop after planning or build inert navigation to look complete. If a provider key blocks live imagery, complete independent work and show the exact remaining setup step.

Finish with working code, updated setup/configuration instructions, migration notes, tests, screenshots from the running interface and an honest list of remaining limitations. Report actual live imagery verification separately from synthetic test results.

Reference current official provider documentation; `handoff/MAP_PROVIDER_NOTES.md` records the links checked for this brief.
