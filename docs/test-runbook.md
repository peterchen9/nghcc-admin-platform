# Test Runbook

Updated: 2026-05-31

This runbook is for local test execution on current `main`. It does not change production application logic, permission behavior, production workflow, `API_PERMISSION_MODE`, database isolation, or CI behavior.

## Marker Reference

Registered markers are listed in `pytest.ini`:

| Marker | Meaning | Current policy |
| --- | --- | --- |
| `read_only` | Test should not mutate database rows, files, or durable local fixtures. | Local selection aid; coverage has expanded but does not change wrapper behavior. |
| `mutating` | Test creates, updates, deletes, uploads, assigns, disables, or writes audit data. | Serial only against the shared restored local DB. |
| `csrf` | Test depends on or verifies `ENABLE_CSRF_PROTECTION=True` behavior. | Run through the CSRF wrapper, serially. |
| `api_scope` | Test covers API permission scope storage, planning, apply, rollback, audit, or effective-scope logic. | Serial when combined with mutating tests. |

After P9, marker coverage is broader than the initial P7 API scope storage marker pass:

- `pytest.ini` registers `read_only`, `mutating`, `csrf`, and `api_scope`.
- Smoke checks include module-level `read_only` markers.
- Security coverage includes module-level and function-level `read_only` markers for static, matrix, validation, and compatibility checks.
- CSRF behavior checks include function-level `csrf` markers where CSRF-enabled behavior is required or verified.
- API permission scope review/log/feature-flag coverage includes `api_scope` markers where appropriate.
- `tests/security/test_api_scope_storage.py` remains marked at module level with `api_scope` and `mutating`.

This marker coverage is for local selection and review. It does not mean the wrappers use marker selection.

## Local Marker Commands

Use these commands to inspect or run marker-selected subsets locally:

```powershell
pytest --markers
pytest -m read_only
pytest -m mutating
pytest -m api_scope
pytest -m "api_scope and mutating"
```

These commands are advisory. They do not replace the existing wrapper scripts and do not make the suite parallel-safe.

## Required Serial Commands

Smoke and CSRF wrappers must still run one at a time:

```powershell
.\scripts\run-smoke-tests.ps1
.\scripts\run-csrf-tests.ps1
```

Do not start the CSRF wrapper until the smoke wrapper has completed. Both wrappers run broad test selections against the local Docker Compose test environment and shared restored database state.

The wrappers currently do not use marker selection. They still run broad suite targets, and no parallel or `pytest-xdist` behavior has been added.

## Focused API Scope Check

For the current API scope storage module:

```powershell
pytest tests/security/test_api_scope_storage.py
```

This module is marked `api_scope` and `mutating`, so it should remain serial until per-worker DB ownership and fixture isolation exist.

## Parallel Execution Policy

Do not enable `pytest-xdist` or parallel CI for this suite today.

Parallel execution is not recommended because mutating tests still share restored local database state, wrapper scripts do not allocate isolated databases, and marker coverage is not broad enough to treat `read_only` selections as a complete safe parallel set.

Before considering xdist or parallel CI, the project needs reviewed marker coverage, per-worker DB isolation, per-worker media/temp paths, namespace-scoped fixtures, and scoped assertions that do not depend on global row counts.

## Repo Root Hygiene Note

The repo root currently contains unexpected empty directories named `pytest.ini;C` and `tests;C`. They are not handled by this runbook update.

Until those directories are removed in a separate cleanup, do not describe marker discovery or working-directory behavior as completely clean.
