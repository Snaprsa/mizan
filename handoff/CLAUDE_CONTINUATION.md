# Mizan — complete continuation brief for Claude Code

Prepared 28 October 2026. This is the development mandate and execution guide for continuing the entire project locally. `PRODUCT_SCOPE.md` preserves the detailed product requirements; this document connects that scope to the actual code, implementation order and verification. The owner's latest instructions take precedence.

## 1. Work in the existing repository

Launch Claude Code at the consolidated repository root, which contains this file, root `CLAUDE.md`, `AGENTS.md`, `run_mizan.sh` and `Projects/`. On the owner's Mac, the ignored `CLAUDE_LOCAL_HANDOFF.md` provides the exact absolute path.

Do not clone a second copy over this working directory. The existing Mac checkout contains ignored private data, installed environments and source-location history that are absent from GitHub. Do not rename or flatten the project folders to make the names prettier: the current engine adapter depends on their sibling relationship.

Public origin: https://github.com/Snaprsa/mizan. At preparation, the published source commit was `596876e83c4c81b7dd7181fd762f6590c7623160`. Check the current Git state; do not reset it to that snapshot. The Claude handoff preparation itself adds/updates documentation locally and preserves the older app-level guide as a reference. Do not mistake these documented edits for files to discard.

Read `CURRENT_STATE.md`, inspect the actual implementation, then give a concise architecture/gap assessment and start implementation. If source contradicts an old document, identify the difference and update the current-state document. Old CLAUDE files, prototypes, screenshots and dated delivery claims are not proof of current functionality.

## 2. What Mizan is meant to become

Mizan is Saudi real-estate valuation, underwriting and investment intelligence. It should answer:

1. What is a property worth today?
2. What should the investor pay?
3. What value could alternative uses generate?
4. What returns could acquisition or development produce?
5. Which risks affect the investment and how can they be mitigated?

The complete workflow is property/location → property facts → market evidence → comparables → independent valuation methods → reconciliation → HBU → development → financing → returns → scenarios/sensitivity → risk → recommendation → professional report.

The main user journey is simple: open the map and see available evidence; select a location or existing asset; select property type; select approach; automatically gather supported inputs; show only required missing information; calculate; inspect assumptions, sources and saved results. The user can start with coordinates, address, plot/plan details, a URL or manual facts. Data not actually available stays missing.

The platform should feel like professional valuation/feasibility software: readable dense tables, maps, financial models, sources and controlled assumptions. Retain the restrained existing brand. Avoid oversized cards, long forms above the map, excessive animation/gradients and generic AI-dashboard styling. English/Arabic/RTL and SAR/area/time units belong in the architecture.

## 3. What already exists

The active platform is `Projects/Muqayyim-Downloads`:

- Next.js 14, React 18, TypeScript, Tailwind and Lucide; `/` redirects to `/map`, the older dashboard is `/dashboard`.
- FastAPI with Pydantic and async SQLAlchemy, Alembic, local SQLite; API prefix `/api/v1` and health `/api/health`.
- Property facts, validated sections, owner access, assumption provenance, revisions and historical snapshots.
- Source registration and normalized append-only market observations, JSON/CSV ingestion and duplicate/conflict handling.
- URL/PDF comparable ingestion, citations, normalization, reviewed overrides/status and CSV/XLSX/PDF exports.
- A basic Leaflet/OpenStreetMap map, layers, grid grouping, filters, subject/radius and evidence list, with outbound Google Maps links.
- Automatic method-specific preparation/readiness and five initial methods: sales baseline, income cap, annual unlevered DCF, cost/DRC and static residual land.
- Two-way sensitivities for income, DCF, cost and residual; invalid stresses remain unavailable.
- Ownership and read-only-role protections across newer and legacy evidence routes; a local development identity, not complete production account/session management.
- An experimental `hbu_analysis.py` screening utility with unit coverage. It uses reviewer-declared gates and supplied timed cash flows; it is not a complete HBU workspace, authenticated planning service or professional HBU conclusion.

Income/DCF/cost reuse classes in `Projects/Mizan-Antigravity/src/mizan_engine/approaches` through `api/app/services/legacy_valuation.py`. Do not duplicate their formulas in React.

There is no completed embedded satellite SDK, geocoding/parcel/planning feed, advanced GIS, adjusted multi-method reconciliation, complete timed development/debt/investment workflow, calibrated AVM/confidence, institutional portfolio/collaboration or full professional report. A feature specification or old prototype is not a working integration.

## 4. Repository and data boundaries

| Location relative to root | Purpose |
|---|---|
| `Projects/Muqayyim-Downloads/frontend` | Active web interface and API client |
| `Projects/Muqayyim-Downloads/api/app` | Active API, models, schemas, services and routers |
| `Projects/Muqayyim-Downloads/api/alembic/versions` | Additive migration history |
| `Projects/Muqayyim-Downloads/api/tests` | Active backend regression suite |
| `Projects/Muqayyim-Downloads/extractors`, `schemas`, `reporting` | Existing ingestion, domain types and case exports |
| `Projects/Mizan-Antigravity` | Required preserved valuation engine, plus earlier app/model source |
| `Projects/Mizan-Desktop` | Earlier ML/ROI source and local candidate datasets |
| `Projects/Qaim` | Earlier ingestion prototype; not the main runtime |
| `Projects/Muqayyim-OpenClaw`, `Backups` | Local historical notes and references |
| `Related-Materials-To-Review` | Local candidate blueprints/variable libraries requiring review |
| `handoff`, `docs` | Canonical continuation guides and dated verification/reference notes |

Private runtime assets are under the active app's `storage/`, with runtime DB `storage/mizan.db`. The historical `muqayyim_dev.db` and Qaim DB are distinct. Do not merge or overwrite them. The launcher makes backups before migration and can recover a disposable clone of the historical DB on first use. A fresh public checkout instead creates an empty runtime DB.

Real environment files and provider sessions are local, ignored and sensitive. Use them only through existing configuration when needed; never print or paste their contents. Existing credentials may be absent/expired; do not assume provider access works. New `.env.example` entries contain names and placeholders only.

The full original-location TSV, move history and collection manifest remain local. They are large audits, not normal LLM reading material. Start with `FILE_MAP.md`. Candidate CSV/XLSX files and model binaries are unverified references; do not unpickle arbitrary artifacts or auto-import their rows as verified transactions. Public source deliberately excludes private data and unreviewed redistribution material.

## 5. First implementation priority: map and interface

Follow the detailed `UPGRADE_PROMPT.md`; these are the essential outcomes:

- Real satellite and hybrid imagery rendered inside Mizan, preferably with an official authorized Google Maps integration. A Google link, static picture or basic road layer does not fulfill this requirement. A licensed MapLibre imagery provider is an alternative if chosen deliberately.
- Satellite/hybrid/road and supported terrain modes. Capability-gate 3D/tilt/Street View for actual Saudi coverage. Do not invent image dates, live imagery or nationwide 3D coverage.
- Verify current official provider APIs, restrictions, attribution and account/billing requirements. The provider notes flag retired Google Drawing Library and automatic raster 45-degree behavior; recheck before coding. Do not build a new integration around obsolete examples.
- A large map with compact header/search, collapsible layer/filter controls, subject/valuation inspector and linked evidence list/table. Improve both full-width and narrow layouts: the current narrow side-panel view leaves very little room for the map.
- Coordinate/place search when an authorized service is available, subject pin placement/drag confirmation, existing property selection, editable radius/polygon and approximate geodesic area/distance measurement.
- Persistent camera/geometry/subject/method/selected-evidence state. Switching basemaps or panels must not wipe unsaved assumptions. Distinguish GeoJSON `[longitude, latitude]` from Leaflet `[latitude, longitude]` explicitly.
- Separate properties, achieved sales, asking listings, rental evidence and observations. Synchronize marker, cluster, row, inspector and subject selection. Include source, date, unit, precision and reliability.
- Explain matching totals versus the rendered subset. Missing-location evidence needs a resolution queue; aggregates need area-level presentation. Do not manufacture exact pins or parcel/zoning boundaries.
- Show recent activity and heatmaps only from appropriate actual data with period/unit/sample size. A public clone may honestly show zero evidence.
- Introduce bounded spatial queries/aggregation instead of repeatedly loading every owned row. Retain a working SQLite local path; plan PostGIS deliberately, not as a prerequisite that breaks local startup.
- Verify actual licensed satellite rendering separately from mocked UI tests. If an account/key is unavailable, complete independent provider/UI/state/data work and state the exact configuration blocker. Do not buy access or pretend fallback tiles complete the satellite requirement.

## 6. Complete platform roadmap after the map

Use `PRODUCT_SCOPE.md` for every domain requirement. Work through these increments, updating statuses based on working behavior rather than the existence of files.

### A. Foundation and ingestion gaps

Audit current property/planning/building/financial fields and validated units; extend existing models rather than creating duplicate parallel entities. Make assumptions explicit: name, value, unit, category, status, source/date, notes, override and history. Retain provider-neutral observations and raw/normalized values. Add batch/provenance/import review and location resolution where required. Review Saudi geography, dates and Arabic normalization.

Sources may include authorized MoJ/REGA/Open Data/Balady/Sakani/Ejar/municipality/portal/broker/user data, cost/rent datasets, SAMA/GASTAT and public disclosures. Intended source names do not establish an API connection or usage rights. Do not promise automated government/plot lookup until a real supported source is connected.

### B. Professional valuation

Build a real comparable adjustment/selection engine and sales/rent analysis: time/location/size/street/frontage/corner/shape/age/condition/quality/occupancy/zoning/potential, explicit absolute/unit/percentage bases and adjustment order, weights, median/weighted median/mean/weighted mean, distributions and explainable outlier overrides.

Extend independent sales, income, DCF, cost/DRC and residual calculations; keep method validity distinct. Then add investment/term-and-reversion, profits, rent, ground lease and separate ownership/leasehold interests where data and scope support them. Preserve specialist asset/model adapters for later.

Reconciliation must account for applicability, evidence quality, method confidence, agreement and user weights with reasons. Do not simply average all methods. Ranges/confidence must be defensible and uncertainty explicit; legacy heuristic scores are not calibrated estimates. Missing evidence does not mean an invented numerical confidence.

### C. Development, HBU and bid solving

Build timed development budgets/cash flows from acquisition, GFA/efficiency/GLA, construction/infrastructure/fit-out/external works, soft costs, permits, marketing, contingency, schedule, selling/rental assumptions and absorption. Calculate GDV, total cost, margins, residual, project returns and NPV consistently.

Integrate and extend the existing HBU screening utility. Separate legal, physical, financial and maximal-productivity tests, with reviewed evidence and comparable assumptions across uses. Unsupported planning facts remain unknown and cannot establish legal permission.

Maximum bid price must solve for the acquisition price satisfying the selected target: project/equity IRR, NPV, developer margin or yield on cost. Use appropriate bounded solvers with feasibility/no-solution reporting; do not substitute an unrelated static rule.

### D. Financing, returns, scenarios and sensitivities

Add no-debt/senior financing first, then extensible mezzanine/layers. Model LTC/LTV constraints, draw timing, interest, fees, amortization/grace, debt balances/service, equity needs, DSCR and debt yield. Derive unlevered and levered cash flows once and reuse them for returns.

Support ROI, NPV, project/equity IRR, cash-on-cash, equity multiple/MOIC, yield on cost, cap rate, profit on cost/GDV and payback where meaningful. Handle zeros, negative denominators, nonexistent/multiple IRRs and inconsistent periods explicitly.

Downside/base/upside vary assumptions independently; expand the existing sensitivity implementation to appropriate models/metrics and add tornado views. Do not change actual achieved evidence in place to generate hypothetical scenarios. Save scenario assumptions and calculation versions.

### E. Risk and market intelligence

Structured market/pricing/rental/construction/finance/liquidity/regulatory/planning/demand/tenant/execution/exit/location risks need probability, impact, score, mitigation and links to assumptions. Recommendation categories use configurable, explained thresholds and data sufficiency, not arbitrary labels or automatic investment claims.

Add statistical/hedonic/AVM adapters with explicit training provenance, geography, feature/target definitions, temporal/spatial leakage controls, evaluation and explanations. Do not claim ML performance from old sample data, manually invented training rows or a deterministic baseline. Keep mass-appraisal/portfolio extensibility.

### F. Professional outputs and institutional features

Per-asset workspaces should support overview/location/market/comparables/valuation/HBU/development/financing/returns/scenarios/risk/documents/report as real modules become functional. Reports need executive summary, asset/location/market, evidence, assumptions, methods/reconciliation, HBU/development, debt/returns/sensitivity, risk/conclusion, sources and disclaimer. Reuse existing export machinery; add complete PDF output deliberately.

Portfolios need membership, value/cost/gain/NOI/yield and geography/type/risk exposures; aggregate return cash flows rather than casually averaging IRRs. Add organizations, user roles, production identity/session lifecycle, collaboration permissions and audit controls as working features. Validate PostgreSQL/PostGIS/migrations and deployment operations before any shared service. Public GitHub source is not a production deployment.

## 7. Financial and evidence correctness

- Keep calculations in reusable backend/domain modules, not React components. State the timing, compounding, terminal convention, units, currency and tax applicability of every model.
- Preserve observed facts, market-derived estimates, user inputs, model-derived results and professional judgments as different statuses.
- Save input/assumption/evidence snapshots, data dates, calculation/model versions and outputs. Changing inputs recalculates dependencies without erasing prior runs.
- Preserve the current sales guard requiring at least three distinct, active, dated, nearby achieved transactions for its baseline. Professional adjustments can extend it deliberately; do not silently bypass evidence rules.
- Preserve geographic matching: unknown district must not borrow a different district's benchmark.
- Preserve saved-result freshness against real input/evidence/calculation versions, unsaved-edit-safe refresh and duplicate-run prevention.
- Preserve ownership and read-only-role protections, upload filename validation, source citations and override history.

## 8. Run, edit and test correctly

First check current processes, Git status and existing environments. Avoid dependency reinstallation on this configured Mac unless necessary. Do not overwrite `.env` with an example or replace the runtime DB.

From repository root, `bash run_mizan.sh` starts the local production frontend and API with the prepared SQLite DB. Web is port 3100 and API 8000. If already healthy, use the running instance. The frontend proxy targets port 8000. Changing `MIZAN_API_PORT` alone does not retarget it.

Because `next start` serves the production build, source edits need a rebuild/restart to appear there. For iterative UI work with the existing API, use a separately available port, for example:

```bash
# Separate build dir: a dev server sharing `.next` corrupts the running `next start` build.
MIZAN_NEXT_DIST_DIR=.next-dev npm --prefix Projects/Muqayyim-Downloads/frontend run dev -- --hostname 127.0.0.1 --port 3101
# Add MIZAN_API_ORIGIN=http://127.0.0.1:8100 to target a disposable API instead of the runtime one.
```

Do not start a second API against the same runtime DB or terminate unrelated listeners. Before a combined-launcher restart, inspect process ownership and stop only the identified launcher/services. Keep the user's data and work intact.

Backend tests must override inherited database settings explicitly because the test fixture uses `setdefault` and must never inherit a real database URL:

```bash
ENV=development DATABASE_URL='sqlite+aiosqlite://' DATABASE_URL_SYNC='sqlite://' \
  .venv/bin/python -m pytest Projects/Muqayyim-Downloads/api/tests -q
npm --prefix Projects/Muqayyim-Downloads/frontend run test:valuation
npm --prefix Projects/Muqayyim-Downloads/frontend run build
```

Last verified baseline: 93 backend tests, 7 frontend tests and production build; GitHub CI passed a fresh Linux dependency install on 28 October 2026. Do not repeat the number as proof after new changes without running relevant checks. Add meaningful financial invariants, owner-access and workflow regression coverage for new behavior.

Browser tests in `docs/verify_*` use fixtures or a disposable API on 8100. See `SETUP_AND_TESTS.md`; never point write-capable tests at the owner's runtime. Test initial setup/migrations on empty disposable data and rehearse upgrades on a consistent disposable snapshot. A positive local dataset count is not a requirement for a clean checkout.

Inspect UI changes in the running app at desktop and narrow widths. Check keyboard access, loading/error/empty states, selection synchronization, unsaved drafts and actual imagery where configured. A build alone does not prove UX or financial correctness.

## 9. Keep progress resumable

Start a concise `handoff/CONTINUATION_LOG.md` when implementation begins. Record the current task, completed behavior, files/migrations, tests with dates/results, blockers and exact next step. Update `CURRENT_STATE.md`, setup/configuration docs and method requirements when implementation changes them.

Work incrementally, show concise progress and continue into working code. Do not claim the full platform is done because one vertical slice is done. If a required provider/source is unavailable, mark dependent features honestly and keep progressing on independent work. Make routine reversible choices without repeatedly asking the owner to approve the plan.

Review diffs and use the public-source policy before commits/pushes. The existing handoff docs are local changes at transfer time; preserve them. Never use `git add -f` to include private or ignored data. Do not expose services publicly, purchase provider access or upload private evidence as an incidental step in development.

## 10. First response and first deliverable

Your first response should briefly confirm the correct root, active app, reused engine, observed process/Git state and architecture gaps. Then implement the map/imagery/interface increment from the upgrade brief. Do not stop with a restated roadmap.

For each completed increment deliver working code, exact setup/configuration requirements, meaningful verification and screenshots of the running interface. Distinguish real provider tests from synthetic fixtures, and identify any required owner configuration. Leave the continuation log accurate enough for a fresh Claude session to pick up where you stopped.

Official Claude Code setup references: https://code.claude.com/docs/en/quickstart and https://code.claude.com/docs/en/memory. Launch `claude` from this repository root; project `CLAUDE.md` supplies persistent context, while these larger references are read as needed.
