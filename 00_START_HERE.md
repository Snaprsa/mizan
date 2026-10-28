# Mizan — start here

Prepared 28 October 2026. This is one consolidated workspace containing one active platform, two reusable Mizan engines and preserved earlier prototypes.

## For another LLM or developer

1. Read `handoff/CURRENT_STATE.md` for what actually works and what does not.
2. Read `handoff/UPGRADE_PROMPT.md` for the requested satellite-map and interface upgrade.
3. Use `handoff/FILE_MAP.md` to inspect the relevant implementation. Do not start from a historical prototype.
4. Follow `handoff/SETUP_AND_TESTS.md` to install, run and verify the application.
5. Check `handoff/DECISIONS_AND_LIMITS.md` before changing data, assumptions, providers or authentication.
6. Use `handoff/PRODUCT_SCOPE.md` for the broader platform requirements; the map/UI brief is the immediate priority.

The active application is `Projects/Muqayyim-Downloads/`. The name is historical; the product is Mizan. The preserved calculation adapter also needs `Projects/Mizan-Antigravity/`. Relative paths are intentionally preserved so the working application is not broken by repackaging.

## Public GitHub checkout

This repository contains reviewed source, tests and development guides. Share the GitHub URL or download its source ZIP. Begin with the files above; do not launch a historical prototype.

Private databases, provider sessions, real environment files, raw datasets/model binaries, personal file-location histories and installed dependencies are not committed. Fresh startup is empty. Component lineage and publication scope are in `docs/PUBLICATION.md`. Detailed original-location records remain on the owner's Mac.

A separately generated local `deliverables/Mizan-LLM-Handoff.zip` is a private-development handoff with broader reference material; it is not the public source release. Do not upload it as a public GitHub asset. Use the repository's source ZIP or `git archive` for public sharing.

## What this delivery does

It organizes the project for transfer and specifies the next upgrade. It does not claim that satellite imagery or a redesigned interface has already been implemented. Current imagery is a basic Leaflet/OpenStreetMap basemap with Google Maps links. The requested upgrade requires a real licensed imagery provider and a materially better map-first interface.

The public repository contains source code, not verified market evidence, trained model artifacts or a credential export.
