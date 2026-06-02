# P23D Local/Staging CSRF Default Change Report

## Scope

P23D changes local/staging defaults only. It does not approve production CSRF enablement or production deployment.

Guardrails preserved:

- No merge.
- No PR.
- No deploy.
- No `.240` connection.
- No production env change.
- No production DB change.
- No API scope apply.
- No `API_PERMISSION_MODE=enforce`.
- No Eureka GET delete change.
- No production static/media change.
- No production DB port or startup migration change.

## Modified Files

| File | Change |
| --- | --- |
| `.env` | Local ignored env changed to `ENABLE_CSRF_PROTECTION=True` for this workspace. Not committed. |
| `.env.example` | Local sample default changed to `ENABLE_CSRF_PROTECTION=True`. |
| `.env.test.example` | Test/local-staging sample default changed to `ENABLE_CSRF_PROTECTION=True`. |
| `backend/nads26/settings.py` | `ENABLE_CSRF_PROTECTION` fallback default changed from `False` to `True`. |
| `docs/p23c-csrf-enablement-decision.md` | Updated decision evidence to record P23D default change. |
| `docs/p23d-local-staging-csrf-default-change-report.md` | Added this report. |

`.env.production.example` remains explicitly `ENABLE_CSRF_PROTECTION=False`; production is still NO-GO.

## Setting Change

Local/staging default is now:

```text
ENABLE_CSRF_PROTECTION=True
```

Rollback remains available by explicitly setting:

```text
ENABLE_CSRF_PROTECTION=False
```

## Test Results

| Command | Result |
| --- | --- |
| `docker compose -f docker-compose.yml -f docker-compose.volume.yml build web` | PASS |
| `.\scripts\run-csrf-tests.ps1` | 99 passed, 0 failed, 39 skipped |
| `.\scripts\run-smoke-tests.ps1` | 99 passed, 0 failed, 39 skipped |

## Production NO-GO Reasons

Production remains NO-GO because the following blockers are still open:

| Blocker | Status |
| --- | --- |
| Eureka GET delete method safety | Open; CSRF does not protect destructive GET. |
| Static/media serving when `DEBUG=False` | Open. |
| `SECRET_KEY` production handling | Open. |
| `ALLOWED_HOSTS` finalization | Open. |
| DB port exposure | Open. |
| Auto migration on startup | Open. |
| Secure cookie / HTTPS policy | Open. |

## Completed CSRF Remediations

| Item | Status |
| --- | --- |
| CKEditor upload CSRF gap | Fixed in P23B. |
| humnos AJAX token fallback | Fixed in P23B. |
| logout positive-path verification | Covered in P23B. |
| credentialed admin/users/hymns/humnos page access | Covered in P23B. |

## Remaining Blockers

1. Eureka delete must become POST-only and CSRF-protected before production CSRF enablement.
2. Production static/media serving must be verified under `DEBUG=False`.
3. Production secret, host, DB exposure, and startup migration gates must be closed.

## Next Phase Recommendation

Recommended next phase: **P23E Eureka Delete Method Safety Fix**.

Reason: local/staging CSRF default is now enabled, so the nearest remaining CSRF-adjacent production blocker is the destructive GET delete flow. That fix should be tested under the new local/staging CSRF default.
