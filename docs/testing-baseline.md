# Testing Baseline

Updated: 2026-06-01

## Scope

P12 is documentation governance only.

- No `tests/` changes.
- No `backend/` changes.
- No CI changes.
- No DB changes.
- No pytest execution.
- No `pytest-xdist` enablement.

This baseline consolidates the decisions from P7 through P16 and records the current safe testing posture for later work.

## Current Baseline

The current local test model uses the restored local Docker Compose database and restored media volume. It is not a pytest-managed disposable database model.

Smoke and CSRF wrappers remain serial-only:

```powershell
.\scripts\run-smoke-tests.ps1
.\scripts\run-csrf-tests.ps1
```

Do not run these wrappers at the same time against the same restored local DB.

Marker selection is advisory only. `pytest.ini` registers:

| Marker | Baseline meaning | Execution policy |
| --- | --- | --- |
| `read_only` | Test should not mutate database rows, files, or durable local fixtures. | Local review aid only. |
| `mutating` | Test creates, updates, deletes, uploads, assigns, disables, or writes audit data. | Serial only against the shared restored DB. |
| `csrf` | Test depends on or verifies `ENABLE_CSRF_PROTECTION=True` behavior. | Serial through the CSRF wrapper. |
| `api_scope` | Test covers API permission scope storage, planning, apply, rollback, audit, or effective-scope logic. | Serial when combined with mutating tests. |

Marker coverage is broader after P9, but it is not yet a control plane for wrapper behavior or CI parallelization.

## Completed Governance Inputs

| Phase | Result | Reference |
| --- | --- | --- |
| P7 namespace cleanup | API scope storage tests moved to generated namespaces and scoped assertions. | `docs/test-hardening-plan.md` |
| P8 marker classification | Marker taxonomy and conservative classification policy documented. | `docs/test-runbook.md` |
| P9 marker coverage review | Low-risk marker coverage expanded and unresolved cases documented. | `docs/test-marker-coverage-review.md` |
| P10 documentation alignment | Runbook and hardening docs aligned around serial wrapper execution and advisory markers. | `docs/test-runbook.md` |
| P11 DB isolation strategy review | Current shared-restored-DB model retained; future isolation options recorded. | `docs/db-isolation-strategy.md` |
| P13 repo-root hygiene closure | Verified and removed the two empty `;C` repo-root directories. | `docs/db-isolation-strategy.md` |
| P14 active governance reference alignment | Stale active references to the removed `;C` directories were rewritten as historical P13 context. | `docs/test-runbook.md`, `docs/test-isolation-review.md`, `docs/test-hardening-plan.md`, `docs/test-marker-coverage-review.md`, `docs/db-isolation-strategy.md` |
| P16 auth helper marker policy | Documented that auth/session helpers are mutation risks and that `read_only` is advisory, not a transaction or parallel-safety guarantee. | `docs/test-runbook.md`, `docs/test-marker-coverage-review.md` |

## Baseline Decisions

1. Serial execution is the known-good local policy.
2. `pytest-xdist` remains disabled.
3. CI must not be changed to parallel test execution until DB ownership is explicit.
4. The current shared restored DB is acceptable for local smoke/staging-like verification, but not for concurrent mutating pytest processes.
5. Namespace cleanup and scoped assertions reduce collision risk, but they do not replace per-worker DB isolation.
6. P13 removed the previously documented empty repo-root directories `pytest.ini;C` and `tests;C` after confirming they were empty and had no active references in `scripts/`, `.github/`, `tests/`, or `backend/`.
7. `read_only` is an advisory marker only. It is not a transaction guarantee, no-session-write guarantee, or `pytest-xdist` / parallel-safety guarantee.
8. Tests using `client.login()`, `force_login()`, `logged_in_client`, `admin_client`, or other login/session fixtures are auth/session mutation risks unless later evidence proves otherwise.
9. Authenticated GET tests, anonymous write-endpoint rejection tests, settings reload tests, and global count assertions require conservative interpretation before they can support any parallel-safe read-only bucket.

## Repo Root Hygiene

P13 confirmed `pytest.ini;C` and `tests;C` were empty directories and removed them.

P14 aligned active governance wording so readers do not infer those directories still exist. Pytest discovery now points at the real `pytest.ini` file and `tests/` directory.

This closure and alignment did not change DB isolation, `pytest-xdist`, CI, deploy behavior, `.240`, API scope assignment, tests, backend code, or pytest behavior. Pytest was not executed.

## Future Change Gate

Before any future parallelization or wrapper behavior change, require a reviewed proposal that covers:

- Marker accuracy for all DB-touching tests.
- Read-only versus mutating split.
- Per-worker DB or per-run DB ownership.
- Per-worker media/temp paths.
- Isolation for durable account-matrix users.
- Rollback path to serial wrapper execution.
- CI behavior and failure-mode review.

Until those gates are satisfied, keep smoke, CSRF, API scope, and mutating coverage serial.
