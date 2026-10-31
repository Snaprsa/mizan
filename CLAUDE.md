# Mizan — Claude Code project instructions

@AGENTS.md

## Start here

Continue the existing Mizan platform. The human's latest task controls scope. Inspect first, reuse working code, then implement verified increments; do not rebuild the platform or stop after writing a plan.

Before changing source, read:

1. `00_START_HERE.md`
2. `handoff/CURRENT_STATE.md`
3. `handoff/CLAUDE_CONTINUATION.md`
4. `handoff/PRODUCT_SCOPE.md` — the complete platform direction
5. `handoff/UPGRADE_PROMPT.md` — immediate satellite map and interface requirements
6. `handoff/FILE_MAP.md`, `handoff/SETUP_AND_TESTS.md`, `handoff/DECISIONS_AND_LIMITS.md`

If present, `handoff/CLAUDE_LOCAL_HANDOFF.md` records this Mac's exact paths and startup snapshot. That file is intentionally ignored by Git and is not required on another machine.

## Canonical architecture

- Active app: `Projects/Muqayyim-Downloads`. Historical name; product name is Mizan / ميزان.
- Frontend: Next.js 14 / React 18 / TypeScript / Tailwind / Lucide.
- Backend: FastAPI / Pydantic / async SQLAlchemy / Alembic; local SQLite. PostgreSQL-oriented schema is not proof of verified PostGIS deployment.
- Reused calculations: `Projects/Mizan-Antigravity/src/mizan_engine/approaches`. Preserve the sibling layout; `legacy_valuation.py` loads it by relative path.
- `Mizan-Desktop`, `Qaim`, OpenClaw notes and backups are reference work, not competing main apps. Never silently merge their data or run their demo seeds.
- The old app-level Claude guide is preserved at `Projects/Muqayyim-Downloads/docs/archive/CLAUDE-2026-03.reference.md`. It is historical context, not current instructions.

## Priorities

The map-first workspace has live Esri satellite imagery through a server-side proxy; the key is in the macOS Keychain and must never reach the browser, files or Git (see `handoff/SETUP_AND_TESTS.md`). The owner requires free services and a simple, Apple-like interface: keep the single-card design and avoid paid providers. Evidence must be visible before analysis and remain accessible while selecting location → property type → method → sourced required inputs → calculation → saved results.

Then progress through professional comparables and reconciliation, development/HBU/maximum bid, financing/returns/scenarios, intelligence and professional outputs. Use the full scope and continuation guide for acceptance criteria. Do not add empty navigation or label unfinished modules as complete.

## Data, calculations and privacy

- No invented market records, geometry, legal planning facts, imagery dates or confidence. Listings, achieved sales, rent, area aggregates and precise observations are different evidence types.
- Private databases, `.env`, provider sessions, uploaded evidence and original-location logs may exist locally. Preserve them. Never print credentials or add them to Git, prompts, reports or public releases.
- A public clone starts empty; this existing local workspace may contain real records. Do not run fresh-setup commands that overwrite its `.env`, database or installed environment.
- Keep source/unit/date/status/override with assumptions; preserve IDs, immutable revisions, evidence/input snapshots and calculation versions. Separate financial calculations from presentation logic.
- Maintain saved-result freshness checks, unsaved-edit protection, duplicate-run prevention and owner/read-only access controls.
- Use additive migrations with a consistent backup and an isolated rehearsal. Do not delete a runtime DB or use it for tests.

## Run and verify

Check listeners before starting services. `bash run_mizan.sh` runs the local app on web port 3100 and API port 8000. UI: `/map`; API docs: `/docs`. The frontend proxy currently targets API port 8000. Do not stop an unknown process to free a port.

The launcher serves a production frontend build: changing files does not hot reload. Rebuild and deliberately restart only the identified Mizan processes when needed. For iterative development, use a separately chosen frontend port **and** `MIZAN_NEXT_DIST_DIR=.next-dev` (sharing `.next` breaks the running production build). `MIZAN_API_ORIGIN` retargets the dev proxy, e.g. to a disposable API on 8100. Avoid duplicate backends against the same SQLite DB.

Run from repository root:

```bash
ENV=development DATABASE_URL='sqlite+aiosqlite://' DATABASE_URL_SYNC='sqlite://' \
  .venv/bin/python -m pytest Projects/Muqayyim-Downloads/api/tests -q
npm --prefix Projects/Muqayyim-Downloads/frontend run test
npm --prefix Projects/Muqayyim-Downloads/frontend run build
```

Last verified local baseline (comparable adjustment grid, 28 October 2026): 112 backend tests, 17 frontend tests and a production build (31 October 2026: protected Esri imagery). Recheck after source changes; this is a baseline, not a permanent required test count. Browser checks use disposable APIs and clearly synthetic fixtures; mocked tiles do not verify live imagery.

## Execution and handoff

Make routine reversible implementation decisions and keep progressing. Ask only for genuinely missing information, provider/account configuration or actions outside the user's authorization. A missing paid imagery key should not stop independent UI/state/data work; identify the live-imagery blocker honestly.

Keep a small continuation log in `handoff/CONTINUATION_LOG.md` when work starts: completed behavior, files, checks, remaining blockers and next step. Update current-state/setup docs when behavior changes. Review `git diff` and the public-tree policy before committing. Do not push local private material. Do not deploy a public service or purchase provider access merely because source is public.
