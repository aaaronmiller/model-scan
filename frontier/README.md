# frontier (formerly ARDF)

The cost-capability frontier of model-scan: a Pareto ranking of model configurations by
benchmark score and task cost, with the evidence ledger, calibration and the dashboard.

Until 2026-11-19 this was its own repository, ARDF, at `/home/cheta/code/ardf/ardf`. It was
folded into model-scan with its git history (`git log -- frontier/`), because model-scan is the
better name and the two were one project. The old repository stays where it is as an archive;
nothing should read from it any more. The consolidation record is the version ledger in
`/home/cheta/LIVING_DOCUMENTS/projects/model-scan/version-ledger.md`.

## Build

Standard library only. Run from this folder:

```bash
cd /home/cheta/code/model-scan/frontier
python3 calibrate.py            # ledger, Pareto and tier docs, dashboard.html (about 45 MB)
python3 current_frontier.py     # data/current-comparison.csv and data/current-frontier.json
python3 tests/verify_dashboard.py      # browser self-test; needs Chromium
python3 tests/verify_determinism.py    # byte-identical builds across Python versions
```

`dashboard.html`, `data/current-comparison.csv` and `data/current-frontier.json` are generated
and not tracked. `SOURCE_DATE_EPOCH` pins the build date, so a rebuild can be compared byte for
byte with an earlier one.

## Dashboard

```bash
python3 -m http.server 8789 --bind 127.0.0.1 --directory /home/cheta/code/model-scan/frontier
```

Then open `http://127.0.0.1:8789/dashboard.html`. The page embeds its data and works offline.

## Who reads it

| Reader | Reads |
|---|---|
| `../ardf_roles.py` | `pareto-frontier-cheatsheet.md`, the strict frontier table |
| `../ardf_export.py`, `../test_ardf_export.py` | the authoritative files and schemas, as a bound export |
| `capacity-watch` skill, `scripts/free-catalog.py` | `data/current-comparison.csv` |

Model names in `../ardf_roles.py` (`NAME_TO_ID`) and in `project-config.json` are data the
ranking reads, not formula. The later formula-only free-model ranking (masterplan packet L5)
should replace the name map with matching from the provider catalogs.

## Layout

See `INDEX.md` for the file roles, `ardf-research-paper.md` for the method, and
`ERRATA-and-findings.md` for corrections. `history/` holds the ARDF repository's own progress
log, mesh handoff and reviews, which lived outside the package folder.
