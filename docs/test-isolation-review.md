# Test Isolation Review

Updated: 2026-06-01

## Boundary

This review is documentation-only.

- No `.240` deployment.
- No `.240` connection.
- No business feature changes.
- No permission-system behavior changes.
- No production application logic changes.

## Reviewed Inputs

- `docs/testing-strategy.md`
- `.github/workflows/smoke-tests.yml`
- `tests/`
- `scripts/run-smoke-tests.ps1`
- `scripts/run-smoke-tests.sh`
- `scripts/run-csrf-tests.ps1`
- `scripts/run-csrf-tests.sh`

## Current Execution Model

`run-smoke-tests` and `run-csrf-tests` both execute the same pytest target set:

```text
tests/smoke tests/integration tests/security
```

The CSRF wrapper only adds a one-off `ENABLE_CSRF_PROTECTION=True` environment override. It does not select an isolated test subset and it does not allocate a separate database.

`tests/conftest.py` intentionally unblocks database access to the already-restored local database:

```text
Smoke tests read the already-restored local database, not a new test DB.
```

That means these suites are integration checks against shared local state, not isolated pytest database tests.

## Conflict Cause

The core conflict is caused by running two full pytest processes against the same restored Docker Compose database while both processes create, mutate, and delete rows in shared database state.

Historically, the highest-risk file was `tests/security/test_api_scope_storage.py` because it used fixed usernames, fixed group names, fixed audit tickets, and global count assertions. That module has since been refactored to use per-test namespace cleanup and namespace-scoped or target-specific count assertions. It no longer deletes durable `test_*` account matrix users as disposable mutation fixtures.

The remaining risk is broader than that one module: `run-smoke-tests` and `run-csrf-tests` still run the same broad suite against the same restored local database, and wrapper execution still has no marker selection, per-run database ownership, or xdist isolation.

The historical fixed-name failure sequence was:

1. Smoke process fixture deletes `api-apply-user`.
2. CSRF process fixture also deletes `api-apply-user`.
3. Smoke process creates `api-apply-user`.
4. CSRF process creates `api-apply-user`, hitting a duplicate username, or deletes it during cleanup.
5. Smoke process continues and observes missing users, missing groups, changed memberships, disabled grants, or changed audit rows.

This is not a CSRF-specific application bug. It is shared test-state contention.

## Namespace Status

`tests/security/test_api_scope_storage.py` now generates disposable usernames, groups, and audit tickets from a per-test namespace. Setup and teardown cleanup filter by namespace prefixes for users, groups, and audit tickets instead of deleting canonical or durable local account names.

The module also replaced the earlier global count checks with namespace-scoped or target-specific assertions for report-only, dry-run, rejected apply, rejected rollback, and invalid-plan paths.

The following deterministic names are now historical examples of the pre-namespace API scope storage fixture pattern rather than the current disposable row ownership model:

- `api-scope-user`
- `api-effective-user`
- `api-missing-user`
- `api-superuser`
- `api-staff-user`
- `api-report-user`
- `api-plan-user`
- `api-plan-staff`
- `api-plan-superuser`
- `api-apply-user`
- `api-apply-service`
- `api-apply-tx-user`
- `api-rollback-user`
- `api-rollback-service`
- `api-rollback-tx-user`
- `csrf-check-only`
- `no-write`

Some non-API-scope tests may still use deterministic request payload names such as `csrf-check-only` or `no-write`, usually in paths expected not to write rows. Those should still be reviewed before treating the whole suite as parallel-safe.

The test account matrix reserves durable `test_*` users for local smoke and permission checks. API scope storage tests no longer reuse those durable names directly; when they need analogous values, the generated namespace is prepended.

## Fixture Cleanup

`api_scope_storage_cleanup` now deletes usernames, groups, and audit tickets owned by the current test namespace before and after each test. This makes the module safer for serial reruns and less sensitive to unrelated local data than the earlier fixed-name cleanup.

Residual risk patterns:

- The wrapper scripts still run broad target sets against one restored DB.
- Other mutating tests may still share restored state unless they are classified and reviewed.
- Cleanup is namespace-based inside API scope storage, but it is not a replacement for per-worker DB ownership.
- Tests can still temporarily mutate canonical rows such as `ApiScope.active`, which remains unsafe under shared parallel execution.

The fixture is useful for serial execution and targeted cleanup, but it is not a full parallel isolation boundary.

## Transaction Scope

Some individual management-command paths are correctly tested for transaction rollback. That protects one command execution from its own injected failure.

It does not isolate the surrounding pytest process from another pytest process because:

- The suite bypasses pytest-django's normal test database lifecycle.
- Tests write to the shared restored database directly.
- API scope storage assertions now use namespace-scoped or target-specific counts for the previously global grant/audit checks.
- Any remaining global count assertions elsewhere can change if another process writes unrelated rows at the same time.
- Cleanup is performed outside a per-test transaction that would be rolled back by pytest.

The command-level transactions are valid application safeguards, but they do not make the test suite parallel-safe.

## Database Reuse

The current design explicitly reuses the Docker Compose `db` service database (`nghcc_admin` by default). The scripts mount tests into a one-off `web` container and run pytest against the same database used by local restored data.

This is appropriate for staging-like smoke checks that validate restored DB/media health, but it is not appropriate for concurrent mutation tests unless each concurrent run gets its own database, schema, or Compose project.

`pytest.ini` has no xdist configuration and no per-worker database suffixing. It does register `read_only`, `mutating`, `csrf`, and `api_scope`, and marker coverage has expanded beyond the initial P7 API scope storage module. However, the smoke and CSRF wrappers still do not select by marker, so marker coverage does not yet provide execution isolation.

P13 confirmed the previously observed repo-root directories `pytest.ini;C` and `tests;C` were empty and removed both. Pytest discovery now points at the real `pytest.ini` file and `tests/` directory. This was repo-root hygiene only, not a DB isolation, `pytest-xdist`, CI, backend, `tests/`, or test behavior change.

## Pytest Parallel Safety

The current suite is not safe for parallel execution at the process level when processes share the same DB.

Safe or lower-risk areas:

- Read-only smoke checks.
- Read-only integration checks.
- Static security assertions.
- CSRF GET/POST rejection checks that do not reach a successful write.

Unsafe areas:

- Tests that create users or groups in shared restored DB state without reviewed namespace ownership.
- Tests that apply or rollback reviewed API scope plans with `--apply --confirm-*`.
- Tests that assert global database counts outside an isolated DB.
- Tests that mutate canonical `ApiScope.active`.
- Tests depending on durable local `test_*` accounts while another test can delete or recreate those accounts.

## Single-Machine Strategy

Use one of these strategies locally:

1. Serial wrapper execution.
   - Run `scripts/run-smoke-tests.ps1`.
   - Then run `scripts/run-csrf-tests.ps1`.
   - Do not run both wrappers at the same time against the same Docker Compose project.

2. Separate database ownership for true parallel local runs.
   - Use distinct `COMPOSE_PROJECT_NAME` values.
   - Use distinct database volumes.
   - Restore DB/media fixtures separately per project.
   - Use separate `DB_NAME` values if sharing the same MySQL service is ever attempted.

3. Split read-only and mutating tests.
   - Allow read-only smoke/integration/static security tests to run in parallel.
   - Run database-mutating tests serially until they use unique fixture namespaces and isolated databases.

Recommended immediate local policy: serial wrapper execution.

## CI Strategy

Current CI is not affected by this conflict because `.github/workflows/smoke-tests.yml` only builds containers and prints a placeholder. It does not run `run-smoke-tests`, `run-csrf-tests`, or pytest.

When CI starts running these suites for real:

- Run smoke and CSRF jobs sequentially if they share one restored DB fixture.
- Prefer separate jobs with separate service databases and separately restored fixtures.
- Do not let two jobs mount or connect to the same mutable DB fixture.
- Treat restored DB/media smoke checks as integration tests, not unit tests.
- Keep mutation-heavy API scope storage tests in a serial job until isolated.
- Add CI concurrency naming only after database ownership is explicit; GitHub job isolation alone is not enough if jobs point to a shared external DB.

Recommended first CI implementation: one job builds/restores fixtures, runs smoke, then runs CSRF in the same job serially.

## Future xdist Strategy

Before enabling `pytest-xdist`:

- Create a true pytest test database path instead of unblocking the restored local database for mutating tests.
- Add per-worker database naming, for example `nghcc_admin_test_gw0`, `nghcc_admin_test_gw1`.
- Generate unique fixture usernames, group names, audit tickets, and CSV content per worker.
- Replace global count assertions with scoped assertions tied to the rows created by the current test.
- Avoid deleting durable `test_*` account matrix users from worker tests.
- Mark tests by isolation level, for example `readonly`, `db_mutation`, and `shared_restored_db`.
- Keep `shared_restored_db` tests serial.

Recommended future shape:

- `pytest -n auto -m "readonly"` for parallel read-only coverage.
- `pytest -n auto -m "db_mutation"` only after worker database isolation and unique fixture naming are implemented.
- `pytest -m "shared_restored_db"` serial for restored-data smoke checks.

## Recommended Fix Plan

Immediate, no application logic changes:

1. Document that `run-smoke-tests` and `run-csrf-tests` must not run in parallel against the same local Compose database.
2. In local/recheck instructions, run the two wrappers serially.
3. In CI, keep the current placeholder safe or add serial execution only after sanitized DB/media fixtures exist.

Next test-only hardening:

1. Split mutating tests from restored-DB smoke tests.
2. Stop using durable `test_*` account names inside disposable apply/rollback tests.
3. Continue reviewing namespace ownership for mutating tests beyond API scope storage.
4. Continue replacing any remaining global count assertions with scoped assertions.
5. Continue expanding and auditing markers for read-only versus mutating tests.

Future parallelization:

1. Add isolated test databases per worker.
2. Add unique per-worker fixture namespaces.
3. Enable xdist only for tests whose fixtures have no shared restored-DB dependency.

## CI Impact

Current CI impact: none. The configured workflow does not run the conflicting scripts.

Future CI impact: high if smoke and CSRF are added as parallel jobs sharing the same restored DB fixture. The failure mode would be flaky duplicate-key errors, missing fixture rows, unexpected global counts, or inconsistent permission/audit state.

## Conclusion

The data conflict comes from shared database reuse plus mutating fixtures that do not yet have process-level database ownership. API scope storage has already moved from fixed disposable names and global counts to namespace cleanup and scoped assertions, but the safest immediate execution policy remains unchanged: run `run-smoke-tests` and `run-csrf-tests` serially unless each run owns a separate database. Longer term, keep mutating tests on unique fixture namespaces and per-worker databases before enabling pytest parallelism.
