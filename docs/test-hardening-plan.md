# Test-only Hardening Plan

Updated: 2026-06-01

## Scope

This phase is planning-only.

- Do not modify production application logic.
- Do not modify the permission system.
- Do not modify production workflow.
- Do not enable `API_PERMISSION_MODE=enforce`.
- Do not implement test changes in this phase.

This plan is based on current `main`, especially `docs/test-isolation-review.md`, `pytest.ini`, `tests/conftest.py`, `scripts/run-smoke-tests.ps1`, and `scripts/run-csrf-tests.ps1`.

## 1. Why Smoke and CSRF Must Run Serially Today

`scripts/run-smoke-tests.ps1` and `scripts/run-csrf-tests.ps1` both execute:

```text
pytest tests/smoke tests/integration tests/security
```

The CSRF wrapper only adds a one-off `ENABLE_CSRF_PROTECTION=True` override. It does not select a smaller CSRF-only subset, allocate a separate database, or isolate fixture ownership.

`tests/conftest.py` intentionally unblocks access to the already-restored local Docker Compose database. These checks therefore run against shared restored state, not a pytest-managed disposable test database.

Previously observed mutating tests used fixed usernames, fixed group names, fixed audit tickets, name-based cleanup, and global count assertions. The highest-risk area was API scope apply/rollback coverage in `tests/security/test_api_scope_storage.py`; that module has since been refactored to use per-test namespace cleanup and namespace-scoped or target-specific assertions.

The serial policy still applies because smoke and CSRF wrappers run the same broad suite against one restored Compose database. If both wrappers run at the same time, unrelated mutating tests or canonical-row changes can still contend even though API scope storage no longer uses fixed disposable names.

Until database ownership and fixture namespaces are isolated, the required policy is:

1. Run `run-smoke-tests` first.
2. Run `run-csrf-tests` after smoke completes.
3. Do not run both wrappers concurrently against the same restored DB.

## 2. Read-only and Mutating Test Split Strategy

The next hardening step should classify tests by database behavior before changing execution parallelism.

Read-only tests should include checks that only inspect restored state, settings, routing, response status, template content, static permission maps, or command dry-run output that provably writes nothing.

Mutating tests should include checks that create, update, delete, enable, disable, assign, unassign, upload, or write audit rows, even when they clean up after themselves.

Proposed buckets:

| Bucket | Purpose | Initial execution policy |
| --- | --- | --- |
| `read_only` | Smoke, readonly API, static settings, route visibility, and parser/report checks that do not write rows | Parallel-eligible after marker accuracy is reviewed |
| `mutating` | API scope apply/rollback, user/group/grant changes, uploads, and any test that creates disposable rows | Serial until unique namespaces and isolated DBs exist |
| `csrf` | Tests that specifically require `ENABLE_CSRF_PROTECTION=True` or verify CSRF token behavior | Serial with mutating CSRF tests separated from read-only CSRF checks |
| `api_scope` | API permission scope storage, planning, apply, rollback, audit, and effective-scope behavior | Split internally into read-only/dry-run and confirmed mutation cases |

The split should be declarative first: add markers and selection commands, then verify that the selected sets match actual behavior. Wrapper changes should come only after the marker audit is complete.

## 3. Current Pytest Marker Usage

The current `pytest.ini` registers these markers:

```ini
markers =
    read_only: test should not mutate database rows, files, or durable local fixtures
    mutating: test creates, updates, deletes, uploads, assigns, disables, or writes audit data
    csrf: test depends on or verifies ENABLE_CSRF_PROTECTION=True behavior
    api_scope: test covers API permission scope storage, planning, apply, rollback, audit, or effective-scope logic
```

Current classification status:

| Marker | Current use | Execution policy |
| --- | --- | --- |
| `read_only` | Registered and now applied to smoke/security tests that inspect state or validate static behavior without durable writes. Coverage has expanded beyond the initial P7 API scope storage classification, but still needs review before driving wrapper behavior. | Advisory local selection only; review marker accuracy before using it to change wrapper behavior. |
| `mutating` | Applied to `tests/security/test_api_scope_storage.py` at module level. | Serial only. Do not run mutating selections concurrently against the shared restored Compose DB. |
| `csrf` | Registered and applied to CSRF behavior tests at function level where CSRF-enabled behavior is required or verified. | Serial only when run through the CSRF wrapper. |
| `api_scope` | Applied to `tests/security/test_api_scope_storage.py` at module level and to read-only API permission/log/feature-flag coverage where appropriate. | Serial when combined with `mutating`; do not parallelize until DB isolation exists. |

Recommended marker rules remain:

- Every test that touches the database should have either `read_only` or `mutating`.
- Any test that calls confirmed apply/rollback paths must be `mutating` and `api_scope`.
- Any test guarded by `ENABLE_CSRF_PROTECTION` should be `csrf`; if it reaches a write path, it should also be `mutating`.
- Dry-run command tests may be `read_only` only after assertions prove scoped row counts are unchanged.
- Marker selection should fail closed during review: unmarked DB tests stay in the serial full suite until classified.

Local marker inspection:

```text
pytest --markers
```

Recommended local marker-selected commands:

```text
pytest -m read_only
pytest -m "mutating"
pytest -m api_scope
pytest -m "api_scope and mutating"
```

These commands are documentation and local triage aids. They do not replace the existing smoke or CSRF wrapper scripts, and they do not imply parallel execution is supported.

## 4. Unique Namespace Fixture Plan

Fixed fixture names should be replaced by a generated namespace owned by the current test run. This has been completed for `tests/security/test_api_scope_storage.py`; the pattern remains the standard for any additional mutating tests.

Recommended namespace format:

```text
t_<yyyymmddhhmmss>_<pid>_<worker>_<shortuuid>
```

Example generated values:

| Entity | Current pattern | Future pattern |
| --- | --- | --- |
| Username | `api-apply-user` | `t_20260531143000_1234_gw0_a1b2_api_apply_user` |
| Group | `api_humnos_readers` | `t_20260531143000_1234_gw0_a1b2_api_humnos_readers` |
| Audit ticket | `SEC-API-001` | `SEC-API-TEST-20260531143000-1234-gw0-a1b2-001` |
| CSV file | `reviewed-api-scope-plan.csv` | `reviewed-api-scope-plan-t_...csv` |

Implementation constraints for the future test phase:

- Generate the namespace once per pytest run or per test, then pass it through fixtures.
- Include xdist worker id when available, for example `gw0`.
- Do not reuse durable local account matrix names such as `test_user` or `test_staff_nomenu` inside disposable mutation tests.
- Cleanup should filter by namespace prefix, not by canonical or durable names.
- CSV content should be generated from the namespace so usernames, groups, tickets, and rollback references are owned by the current test.
- Canonical API scope rows can remain canonical, but tests that temporarily change canonical fields such as `active` must be serial or use an isolated DB.

## 5. Global Count Assertion Strategy

Global count assertions are fragile when another test process can write unrelated rows.

Current risky pattern:

```text
before = Model.objects.count()
run command
assert Model.objects.count() == before
```

Preferred rewrites:

1. Assert by namespace ownership:
   - No rows exist where `username__startswith=namespace`.
   - No groups exist where `name__startswith=namespace`.
   - No audit rows exist where `ticket__startswith=namespace_ticket_prefix`.

2. Assert specific target state:
   - The planned user was not assigned to the planned group.
   - The planned grant for the planned group and scope does not exist.
   - The planned audit ticket did not produce rows.

3. For dry-run behavior, assert both output and scoped non-existence:
   - Output rows have `dry_run=true`.
   - Scoped target rows are absent.

4. Keep true global count assertions only in serial tests that run against an isolated DB and explicitly document that requirement.

This change reduces false failures and makes tests compatible with unrelated local state.

## 6. xdist and Per-worker DB Isolation Prerequisites

`pytest-xdist` should not be enabled for mutating tests until each worker owns its database state.

Required conditions:

- A pytest test database path exists for mutating tests instead of writing directly to the restored local DB.
- Each xdist worker gets a unique DB name, for example `nghcc_admin_test_gw0`, `nghcc_admin_test_gw1`.
- Migrations and seed data can be applied per worker without relying on shared mutable restored state.
- File/media writes use per-worker temporary directories or volumes.
- Fixture usernames, group names, tickets, and generated CSVs include the worker namespace.
- Cleanup is scoped to the namespace and does not delete durable local test accounts.
- Tests that depend on restored production-like data are marked separately and remain serial.
- Wrapper scripts and CI jobs never point multiple mutating pytest processes at the same DB.

Until these conditions are met, xdist should be limited to reviewed `read_only` tests or avoided entirely.

## 7. Recommended Phased Implementation Order

### Phase 0: Documentation and Execution Policy

Keep smoke and CSRF wrapper execution serial. Document that concurrent wrapper execution against one Compose project is unsupported.

No code, test, workflow, or permission behavior changes.

### Phase 1: Marker Taxonomy

Add pytest marker definitions and mark tests by actual behavior:

- `read_only`
- `mutating`
- `csrf`
- `api_scope`

Do not change wrapper execution yet. Run marker-selected reports only to confirm classification.

### Phase 2: Read-only Selection

Create explicit read-only selection commands for local use. Keep mutating tests serial.

Smoke and CSRF wrappers can remain full serial wrappers while a separate read-only command is validated.

### Phase 3: Unique Fixture Namespaces

Refactor mutating fixtures and generated CSV rows to use unique namespaces. Remove dependency on fixed disposable usernames, groups, and audit tickets. API scope storage has already completed this step; future work should apply the same rule to any newly identified mutating fixtures.

Keep execution serial after this phase until scoped assertions are complete.

### Phase 4: Scoped Assertions

Replace global count assertions with namespace-scoped or target-specific assertions. API scope storage has already completed this step for its previously global count checks.

Keep any truly global state assertions in an explicitly serial bucket.

### Phase 5: Per-worker Isolation Design Spike

Design and validate per-worker DB naming, migration/seeding, media temp paths, and xdist worker integration in a local-only branch.

Do not enable xdist for mutating tests until the design proves isolated DB ownership.

### Phase 6: Controlled Parallelization

Enable parallel execution only for reviewed safe sets:

1. `read_only` tests first.
2. `csrf and read_only` only after CSRF mode selection is stable.
3. `mutating` only after per-worker DB isolation and unique namespaces are proven.

## 8. Rollback and Verification by Phase

| Phase | Rollback | Verification |
| --- | --- | --- |
| Phase 0 | Revert documentation-only commit | `git diff --name-only HEAD~1..HEAD` shows only docs; smoke and CSRF remain serial policy |
| Phase 1 | Remove marker additions and marker annotations | `pytest --collect-only`; full serial `pytest tests/smoke tests/integration tests/security` has same behavior as before |
| Phase 2 | Remove read-only selection command or wrapper addition | Full serial wrappers still pass; marker-selected read-only run is advisory only |
| Phase 3 | Revert namespace fixture refactor | Focused `pytest tests/security/test_api_scope_storage.py`; verify no durable `test_*` account deletion |
| Phase 4 | Revert assertion rewrites | Focused API scope tests plus full serial suite; confirm dry-run tests assert scoped non-existence |
| Phase 5 | Drop experimental xdist/per-worker DB config | Serial wrappers continue to use existing Compose DB; no production workflow impact |
| Phase 6 | Disable xdist and return to serial marker commands | Serial `run-smoke-tests` then `run-csrf-tests`; compare failures against pre-parallel baseline |

Global rollback rule: if any hardening phase creates flaky behavior, return to serial full-suite execution before investigating. Serial execution remains the known-good baseline until per-worker DB isolation is complete.

## Non-goals

- No production deployment.
- No `.240` connection or modification.
- No permission enforcement rollout.
- No production workflow change.
- No default `API_PERMISSION_MODE` change.
- No change to business feature behavior.

## Acceptance Criteria for This Planning Phase

- `docs/test-hardening-plan.md` exists.
- The plan explains why smoke and CSRF currently require serial execution.
- The plan defines read-only versus mutating split strategy.
- The plan proposes `read_only`, `mutating`, `csrf`, and `api_scope` markers.
- The plan describes unique namespace fixture naming for usernames, groups, tickets, and CSV content.
- The plan explains how to remove or rewrite global count assertions.
- The plan lists prerequisites for xdist/per-worker DB isolation.
- The plan recommends phased implementation order.
- The plan includes rollback and verification for each phase.

## Phase 1 Result: Initial Marker Registration and API Scope Storage Classification

Updated: 2026-05-31

This phase registered the pytest markers `read_only`, `mutating`, `csrf`, and `api_scope` in `pytest.ini`.

Initial test classification was intentionally limited to `tests/security/test_api_scope_storage.py`. The module is marked `api_scope` and `mutating` because its tests use cleanup that deletes test-owned users, groups, and audit rows, and the cases create or modify users, groups, grants, scope active state, memberships, or audit rows. No tests in this module were marked `read_only` in this phase.

Smoke and CSRF wrapper execution remains serial-only. No wrapper, workflow, fixture behavior, database isolation behavior, production permission behavior, or test assertion was changed.

## P7 Phase 2 Result: API Scope Storage Test Namespace

Updated: 2026-05-31

This phase refactored `tests/security/test_api_scope_storage.py` to use a unique per-test namespace for disposable usernames, groups, and audit tickets. The namespace uses a short random suffix so generated usernames remain compatible with the existing local `UserProfile.worker_ename` length constraint.

Setup and teardown cleanup now deletes only rows whose usernames, group names, or audit tickets start with the current test namespace. Durable local accounts such as `test_user` and `test_staff_nomenu` are no longer used as disposable mutation fixtures in this module.

Existing test semantics and assertion purposes were preserved. Existing global count assertions were left in place and marked with `TODO(P7 Phase 4)` for a later scoped-assertion pass.

Smoke and CSRF wrapper execution remains serial-only. No production application logic, permission system behavior, production workflow, `API_PERMISSION_MODE`, database isolation behavior, or parallel test execution setting was changed.

## P7 Phase 3 Result: Marker Runbook and Serial Policy

Updated: 2026-05-31

This phase documents the current marker usage and recommended local marker-selected commands without changing tests, application logic, permission behavior, workflow files, database isolation, or CI jobs.

Recommended local commands:

```text
pytest --markers
pytest -m read_only
pytest -m mutating
pytest -m api_scope
pytest -m "api_scope and mutating"
pytest tests/security/test_api_scope_storage.py
.\scripts\run-smoke-tests.ps1
.\scripts\run-csrf-tests.ps1
```

Execution policy remains conservative:

- Run smoke and CSRF wrappers with serial execution only.
- Do not run `.\scripts\run-smoke-tests.ps1` and `.\scripts\run-csrf-tests.ps1` at the same time against the same restored local DB.
- Do not enable `pytest-xdist`.
- Do not add parallel CI jobs.
- Do not enable `API_PERMISSION_MODE=enforce`.
- Do not change DB isolation.
- Treat marker selections as local review aids until marker coverage and isolation prerequisites are complete.

## P7 Phase 4 Result: Scoped API Scope Storage Assertions

Updated: 2026-05-31

This phase replaced the remaining `TODO(P7 Phase 4)` global count assertions in `tests/security/test_api_scope_storage.py` with namespace-scoped or target-specific assertions.

Dry-run, missing-confirmation, validation-error, and report-only assertions now compare only rows owned by the current test namespace: usernames under the generated user prefix, groups under the generated group prefix, and audit rows under the generated ticket prefix. Existing target user group-membership assertions remain target-specific.

The test semantics were preserved: these cases still prove that report-only, dry-run, rejected apply, rejected rollback, and invalid-plan paths do not write the data that the test owns. The assertions are now less sensitive to unrelated rows created by another process against the same shared database.

Smoke and CSRF wrapper execution remains serial-only. No production application logic, permission system behavior, production workflow, `API_PERMISSION_MODE`, database isolation behavior, or parallel test execution setting was changed.

## P9 Result: Marker Coverage Expansion

Updated: 2026-05-31

This phase expanded marker coverage beyond the initial P7 API scope storage classification. `pytest.ini` still registers `read_only`, `mutating`, `csrf`, and `api_scope`.

Current marker coverage includes module-level `read_only` markers for smoke checks and selected security modules, function-level `read_only` markers for security matrix and validation checks, function/module-level `api_scope` markers for API permission scope review/log/feature-flag coverage, and function-level `csrf` markers for CSRF behavior checks. `tests/security/test_api_scope_storage.py` remains module-level `api_scope` and `mutating`.

The marker expansion did not change wrapper execution. `.\scripts\run-smoke-tests.ps1` and `.\scripts\run-csrf-tests.ps1` still run broad suite targets rather than marker-selected subsets, and there was no parallel or xdist change.

Repo-root hygiene note: P13 confirmed the previously observed `pytest.ini;C` and `tests;C` paths were empty directories, removed both, and left pytest discovery pointed at the real `pytest.ini` file and `tests/` directory. This was not a DB isolation, `pytest-xdist`, CI, backend, `tests/`, or test behavior change.
