# API Scope Final Apply/Rollback CSV Dry-run Review

Created: 2026-05-31

## Scope

This phase converts the reviewed backfill sample CSVs into final checksum-pinned reviewed CSV artifacts for local dry-run review only.

Constraints preserved:

- No deployment to `.240`.
- No connection to `.240`.
- No modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- No `--apply`.
- No default API behavior change.
- No business feature change.

## Final Reviewed Artifacts

| Artifact | Rows | SHA-256 |
| --- | ---: | --- |
| `docs/reviewed/api-scope-final-reviewed-apply.csv` | 13 | `aabbeda8c4382330281cfd897eb6562813db6beb50bc5fbcf53d093a4c473f12` |
| `docs/reviewed/api-scope-final-reviewed-rollback.csv` | 8 | `45c59e89d01a9f8fdc3b04f4749a5686ac81a5918f5eefd348131c85144ad4fb` |

Metadata used in both CSVs:

- `reviewed_by`: `peterchen9`
- `reviewed_at`: `2026-05-31T00:00:00+08:00`
- `ticket`: `SEC-API-FINAL-CSV-DRYRUN-001`
- `plan_version`: `2` for apply rows
- `reason`: row-specific final dry-run review reasons

Checksum sidecar files:

- `docs/reviewed/api-scope-final-reviewed-apply.csv.sha256`
- `docs/reviewed/api-scope-final-reviewed-rollback.csv.sha256`

## Pending Candidate Assignments

The following `peterchen` assignments remain candidates only. They were intentionally not included in the final apply CSV, so they cannot be applied by this reviewed artifact without a later explicit approval and a new checksum.

| Username | Candidate group | Status | Reason |
| --- | --- | --- | --- |
| `peterchen` | `api_hymns_editors` | Pending | No explicit approval for hymn metadata write access. |
| `peterchen` | `api_hymns_uploaders` | Pending | No explicit approval for hymn upload access. |
| `peterchen` | `api_humnos_operators` | Pending | No explicit approval for humnos operator access. |

## Apply Dry-run

Command:

```powershell
docker-compose -f docker-compose.yml -f docker-compose.volume.yml run --rm `
  -v "${PWD}\docs\reviewed:/app/docs/reviewed:ro" `
  web python manage.py apply_api_scope_reviewed_plan `
  --plan-file docs/reviewed/api-scope-final-reviewed-apply.csv `
  --expected-plan-version 2 `
  --expected-checksum aabbeda8c4382330281cfd897eb6562813db6beb50bc5fbcf53d093a4c473f12 `
  --reviewed-by peterchen9 `
  --ticket SEC-API-FINAL-CSV-DRYRUN-001
```

Result:

- Exit code: `0`
- Preview rows: `13`
- `status=ok`: `13`
- `dry_run=true`: `13`
- `--apply`: not used
- Writes: none

Observed preview notes:

- Five role groups would be created.
- Eight group grant rows validated.
- Current local state reports missing groups for grant rows because this phase did not create groups; this is expected in dry-run review.

## Rollback Dry-run

Command:

```powershell
docker-compose -f docker-compose.yml -f docker-compose.volume.yml run --rm `
  -v "${PWD}\docs\reviewed:/app/docs/reviewed:ro" `
  web python manage.py rollback_api_scope_reviewed_plan `
  --plan-file docs/reviewed/api-scope-final-reviewed-rollback.csv `
  --expected-checksum 45c59e89d01a9f8fdc3b04f4749a5686ac81a5918f5eefd348131c85144ad4fb `
  --reviewed-by peterchen9 `
  --ticket SEC-API-FINAL-CSV-DRYRUN-001
```

Result:

- Exit code: `0`
- Preview rows: `8`
- `status=ok`: `8`
- `dry_run=true`: `8`
- `--apply`: not used
- Writes: none

Observed preview notes:

- Rollback rows are explicit `disable_group_grant` rows for the eight final group grants.
- Current local state reports rollback would be a no-op because the grants were not applied; this is expected in dry-run review.
- Groups are kept by default; no `delete_empty_group` rows were included.

## Acceptance

- Final reviewed CSVs exist under `docs/reviewed/`.
- Checksum metadata exists in this review document and `.sha256` sidecar files.
- `peterchen` assignments are pending and not applyable from the final apply CSV.
- Apply and rollback dry-runs passed with checksum, reviewer, and ticket pinning.
- No apply or rollback mutation was executed.
- Enforcement remains disabled and default API behavior remains unchanged.

## Local Verification

Commands executed:

- `.\scripts\check-local.ps1`: passed.
- `.\scripts\run-api-permission-staging-like-recheck.ps1 -ExecuteLocal`: passed.
- `.\scripts\run-smoke-tests.ps1`: `88 passed`, `44 skipped`.
- `.\scripts\run-csrf-tests.ps1`: `93 passed`, `39 skipped`.
- Full Docker pytest for `tests/smoke tests/integration tests/security`: `88 passed`, `44 skipped`.

The staging-like recheck also refreshed the local report-only sample with `16` rows: `allow/superuser=8` and `deny/missing_scope=8`.

## Next Step

Have an operational reviewer explicitly approve or reject each pending `peterchen` assignment. If any assignment is approved, create a separate reviewed assignment CSV and matching rollback CSV with a new ticket, new checksum, and another dry-run review before any local apply is considered.
