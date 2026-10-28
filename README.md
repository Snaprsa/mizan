# Mizan | ميزان

Saudi real-estate valuation and investment intelligence, built around a map-first property workspace.

**Development status:** a working local application with sourced assumptions, comparable review and initial valuation methods. The current map uses Leaflet/OpenStreetMap. Embedded satellite imagery and the richer interface are specified as the next upgrade; they are not implemented yet. This repository publishes source code, not a hosted service or a market-data feed.

## Start here

- [Project guide](00_START_HERE.md): reading order for contributors and other LLMs.
- [Current architecture and capabilities](handoff/CURRENT_STATE.md).
- [Satellite map and interface implementation brief](handoff/UPGRADE_PROMPT.md).
- [Broader product requirements](handoff/PRODUCT_SCOPE.md).
- [Code map](handoff/FILE_MAP.md) and [setup / verification](handoff/SETUP_AND_TESTS.md).
- [Public repository scope and local provenance](docs/PUBLICATION.md).

## What works

- Map-based subject selection, property type and method-specific valuation workflow, with a linked evidence list.
- Central property records, revisions, sourced assumptions, overrides and immutable calculation snapshots.
- Provider-neutral sources and normalized market observations, with JSON/CSV ingestion and conflict checks.
- Comparable URL/PDF extraction, citations, review and CSV/XLSX/PDF exports.
- Initial sales comparison, income capitalization, annual unlevered DCF, cost/DRC and static residual land calculations.
- Two-way sensitivities for income, DCF, cost and residual calculations.
- Ownership checks across property and legacy evidence routes, with read-only role protections.

Fresh checkouts contain **no private properties, transactions, provider sessions or training datasets**. Start empty, register sources and supply data you are authorized to use. No verified transaction feed or calibrated AVM is bundled.

## Repository layout

```text
Projects/
  Muqayyim-Downloads/    Active Mizan application (historical folder name)
    frontend/           Next.js 14, React, TypeScript, Tailwind
    api/                FastAPI, SQLAlchemy, Alembic and tests
    extractors/         Source ingestion and normalization
    reporting/          Existing case exports
  Mizan-Antigravity/     Preserved valuation engine; required by the adapter
  Mizan-Desktop/         Earlier valuation / ML / ROI source for reference
  Qaim/                 Earlier ingestion prototype, not the main application
handoff/                Architecture, requirements and LLM implementation brief
docs/                   Dated implementation notes and public repository guidance
scripts/                Packaging utilities
run_mizan.sh            Local launcher
```

The active app imports preserved calculations from its sibling Mizan-Antigravity folder. Keep these paths together. Legacy prototypes are preserved for reuse; they do not share a synchronized runtime database and may require separately supplied datasets/models.

## Run locally

Use Python 3.13 or 3.14 and Node 24. The preparation checks were run with the existing Python 3.14 / Node 24 environment on macOS; CI also checks a clean Linux environment.

```bash
git clone https://github.com/Snaprsa/mizan.git
cd mizan
python3 -m venv .venv
.venv/bin/python -m pip install -r Projects/Muqayyim-Downloads/requirements-local.txt
npm --prefix Projects/Muqayyim-Downloads/frontend ci
npm --prefix Projects/Muqayyim-Downloads/frontend run build
bash run_mizan.sh
```

Open **http://127.0.0.1:3100/map**. API documentation: **http://127.0.0.1:8000/docs**. The launcher needs available ports 3100 and 8000, creates/migrates an empty local SQLite database on a fresh checkout, and binds to loopback. Ctrl+C stops its processes. `MIZAN_WEB_PORT` selects another frontend port.

No provider key is required for the current road basemap. Optional authenticated ingestion requires your own credentials in a local `.env`; start from the blank `.env.example`. Proposed Google imagery configuration is documented in [provider notes](handoff/MAP_PROVIDER_NOTES.md).

## Verify

```bash
.venv/bin/python -m pytest Projects/Muqayyim-Downloads/api/tests -q
npm --prefix Projects/Muqayyim-Downloads/frontend run test:valuation
npm --prefix Projects/Muqayyim-Downloads/frontend run build
```

Tests use disposable data. Do not run integration/browser scripts against a database containing real assets. See the setup guide for browser fixtures and exact limits.

## Scope and deployment

These are initial valuation indications, with transparent input and evidence limits. Professional adjusted appraisals, full financing/development workflows, reconciled valuations, calibrated confidence, portfolios and institutional collaboration remain incomplete. An experimental HBU screening utility has unit coverage; it is not a complete integrated HBU workspace.

The local launcher uses a development identity. Publishing this source does not deploy the application. Shared hosting requires production authentication/session management, tenant controls, configuration and database/deployment verification. See [SECURITY.md](SECURITY.md).

Private databases, sessions, personal filesystem histories, screenshots, model binaries and datasets without reviewed sharing rights remain outside Git. The original collection and its detailed location history are preserved locally. Public visibility does not imply that external data/provider rights have been granted.
