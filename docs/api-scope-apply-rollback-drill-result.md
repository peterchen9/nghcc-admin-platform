# API Scope Disposable Local Apply/Rollback Drill Result

Created: 2026-05-30

## Scope

This drill is local-only and disposable:

- Did not deploy to `.240`.
- Did not connect to `.240`.
- Did not modify `.240`.
- Did not enable `API_PERMISSION_MODE=enforce`.
- Did not change default API behavior.
- Used only `test_*` users and the `test_api_scope_drill_readers` test group.

## Reviewed Inputs

- Apply sample: `docs/samples/api-scope-disposable-reviewed-apply.csv`
- Rollback sample: `docs/samples/api-scope-disposable-reviewed-rollback.csv`

The rollback sample uses `rollback_of` values that point to the deterministic apply audit event ids from the apply sample:

| Apply action | Apply audit event id |
| --- | --- |
| `create_group_grant` | `3ada8ef54afc763a931f39fa25f089f4` |
| `assign_user_to_group` | `abc15862e5e603ec780151538a6b2163` |
| `create_user_grant` | `8ff83417cb3ee4b2ffaa8ce5848476db` |

## Drill Command

```powershell
.\scripts\run-api-scope-apply-rollback-drill.ps1
```

The script performs:

1. disposable test data preflight/reset for `test_user`, `test_staff_nomenu`, and `test_api_scope_drill_readers`;
2. apply dry-run;
3. apply with `--apply --confirm-apply`;
4. verification of grants, group membership, and apply audit rows;
5. rollback dry-run;
6. rollback with `--apply --confirm-rollback`;
7. verification that enabled grants are gone, membership is removed, and rollback audit rows link to apply audit rows through `rollback_of`.

## Current Result

Executed locally in Docker Compose volume environment on 2026-05-30 with:

```powershell
.\scripts\run-api-scope-apply-rollback-drill.ps1
```

Observed final state after successful rollback:

- `test_user` is not a member of `test_api_scope_drill_readers`.
- `test_api_scope_drill_readers` has no enabled API scope grants.
- `test_staff_nomenu` has no enabled direct API scope grant from this drill.
- Disabled grant rows remain for audit continuity.
- `SEC-API-DRILL-RB` audit rows have `rollback_of` values pointing at `SEC-API-DRILL` audit event ids.
- API permission mode remains at the default behavior; no enforce mode is required.

Verification output:

```text
rollback_verified
enabled_group_grants 0
enabled_user_grants 0
membership_exists False
apply_audit_events 4
rollback_audit_events 3
```

## Automated Coverage

`tests/security/test_api_scope_storage.py` includes `test_disposable_apply_rollback_drill_verifies_rollback_of_chain`, which exercises the same reviewed apply/rollback pattern in pytest and verifies rollback state plus the `rollback_of` chain.

Validation results:

| Command | Result |
| --- | --- |
| `.\scripts\check-local.ps1` | Passed |
| `.\scripts\run-smoke-tests.ps1` | 88 passed, 44 skipped |
| `.\scripts\run-csrf-tests.ps1` | 93 passed, 39 skipped |
| `docker-compose -f docker-compose.yml -f docker-compose.volume.yml run --rm ... pytest tests/smoke tests/integration tests/security` | 88 passed, 44 skipped |
| focused `pytest tests/security/test_api_scope_storage.py` in Docker Compose volume environment | 18 passed |
