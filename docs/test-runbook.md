# Test Runbook

Updated: 2026-06-01

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

## Auth Helper Marker Policy

The `read_only` marker is an advisory marker only. It is not a transaction guarantee, a no-session-write guarantee, or a `pytest-xdist` / parallel-safety guarantee.

Tests that use Django auth or session helpers should be treated as auth/session mutation risks unless a later review proves otherwise. This includes direct or fixture-mediated use of:

- `client.login()`
- `force_login()`
- `logged_in_client`
- `admin_client`
- other login or session fixtures

Authenticated GET tests can still save session state or trigger auth side effects. Do not place tests using these helpers into a truly parallel-safe read-only bucket unless there is explicit evidence that the project/runtime does not write session or auth state for that path.

Anonymous write-endpoint rejection tests also should not be automatically marked `read_only`; rejected POST, PUT, DELETE, upload, or user-management paths still exercise write surfaces. Settings reload tests may remain `read_only` when they do not touch the DB, but they are process-global mutations rather than proof of parallel safety. Global count assertions prove only the checked count at that point in one process; they are not evidence that the test is safe under concurrent writers.

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

P13 confirmed the previously observed repo-root directories `pytest.ini;C` and `tests;C` were empty and removed them.

Pytest discovery now points at the real `pytest.ini` file and `tests/` directory. This runbook note is historical governance context only; P13 was not a DB isolation, `pytest-xdist`, CI, backend, `tests/`, or test behavior change.
