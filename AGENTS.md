# Mizan working instructions

- Human instructions for the current task take precedence over this handoff.
- Read `00_START_HERE.md`, `handoff/CURRENT_STATE.md` and the requested task before editing.
- Active platform: `Projects/Muqayyim-Downloads` (Next.js/React/TypeScript frontend, FastAPI/SQLAlchemy backend). The folder name is historical.
- Reused valuation engine: `Projects/Mizan-Antigravity/src/mizan_engine/approaches`. Its sibling location is required by the current adapter. Preserve relative paths until deliberately migrating and testing the adapter.
- `Projects/Mizan-Desktop`, `Projects/Qaim`, `Projects/Muqayyim-OpenClaw` and `Backups` are preserved legacy/reference work. Do not launch them as the primary platform or merge their data blindly.
- Inspect existing code and reuse working ingestion, citations, overrides, property revisions, valuation calculations and tests. Make incremental changes; no wholesale rebuild.
- The map workspace uses Leaflet with Esri's free ArcGIS Location Platform imagery (owner requirement: free services; Google was removed because it needs billing) and a labelled OpenStreetMap fallback. Live satellite imagery is unverified until the free key is configured; complete GIS (parcels, zoning, PostGIS) is still requested work. See `handoff/CONTINUATION_LOG.md`.
- Read `handoff/UPGRADE_PROMPT.md` when implementing the map/UI upgrade. Check current provider documentation and deprecations before using an API.
- No fabricated market transactions, parcel boundaries, imagery dates, planning rules, confidence scores or predictions. Preserve observed values, user assumptions and provenance separately.
- Private databases, credentials, auth sessions and installed dependencies are intentionally absent from the transfer archive. Fresh startup is empty; never auto-seed plausible market data to conceal missing coverage.
- Use isolated databases for tests. Never reset or seed a user's runtime database. Preserve history and original-location provenance.
- Run the targeted checks in `handoff/SETUP_AND_TESTS.md`. Report what was actually tested, provider/API configuration blockers and remaining limitations.
- The primary current-state handoff is `handoff/CURRENT_STATE.md`. Older assessments describe historical stages; treat them as context, not claims of current implementation.
