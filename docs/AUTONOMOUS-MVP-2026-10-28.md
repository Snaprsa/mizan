# Mizan incremental MVP delivery

28 October 2026 · MVP DONE · Active project updated in place.

The application now shows two-way sensitivity tables for income capitalization, property DCF, cost and residual land workflows. Each table uses the same calculation logic as the saved base case. Invalid stresses remain visibly unavailable. Observed sales evidence is not silently altered to generate scenarios.

The older case, source, extraction, comparable and export routes now enforce case ownership; read-only roles cannot mutate evidence. PDF uploads reject path components before writing files.

## Delivery files

- `implementation.patch`: changes against the original source files.
- `original_files_backup.zip`: the eight files preserved before editing; remove the four newly added files to fully roll back.
- `changed_source_files.zip`: twelve current source/test files, preserving project-relative paths.
- `changed_files.json`: project location, changed-file inventory and SHA-256 hashes.
- `PRD.md`, `ARCHITECTURE.md`, `valuation_method_registry.md`, `assumptions_model.md`, `benchmark_cases.json`, `VERIFICATION.md`.
- `sensitivity_workflow.png`: disposable-database browser verification, not actual market data.

## Existing project

`Projects/Muqayyim-Downloads` remains the active Next.js/FastAPI platform. Its sibling `Mizan-Antigravity` remains required by the preserved calculation adapter. No runtime database was reset, seeded or migrated. No credentials or private database files are in these delivery archives.

Restart the normal local app to load the updated API and frontend. Existing saved runs remain historical; the calculation version increment makes stale calculations distinguishable. The currently running normal server was not stopped.

## Verification

83 backend tests, 7 frontend valuation-state tests, production build/type/lint checks, and a full browser-to-API workflow passed. The browser used disposable database/ports and explicit test assumptions. Test details and limits are in `VERIFICATION.md`.

Production authentication, tenant collaboration, verified provider feeds, licensed imagery and formal standards compliance remain separate work. These changes close a specific ownership gap; they do not certify the entire application secure or compliant.

Full delivery: a separate local delivery (not included in the public repository)
