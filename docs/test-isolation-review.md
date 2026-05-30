# Test Isolation Review

Updated: 2026-05-31

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

The conflict is caused by running two full pytest processes against the same restored Docker Compose database while both processes create, mutate, and delete the same fixed fixture rows.

The highest-risk file is `tests/security/test_api_scope_storage.py`. It uses fixed usernames, fixed group names, and fixed audit tickets, then deletes and recreates those rows in a fixture before and after each test. When `run-smoke-tests` and `run-csrf-tests` run in parallel, both processes operate on the same names in the same database.

Typical failure sequence:

1. Smoke process fixture deletes `api-apply-user`.
2. CSRF process fixture also deletes `api-apply-user`.
3. Smoke process creates `api-apply-user`.
4. CSRF process creates `api-apply-user`, hitting a duplicate username, or deletes it during cleanup.
5. Smoke process continues and observes missing users, missing groups, changed memberships, disabled grants, or changed audit rows.

This is not a CSRF-specific application bug. It is shared test-state contention.

## Duplicate Usernames

The suite contains deterministic usernames that are reused on every run:

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
- `test_user`
- `test_staff_nomenu`
- `csrf-check-only`
- `no-write`

Some names are only used in requests expected to fail, but the API scope storage tests create actual Django `User` rows with fixed names. Because `auth_user.username` is unique, parallel processes can collide directly on insert.

The test account matrix also reserves `test_*` users for local smoke and permission checks. Reusing those names inside write/apply/rollback tests raises the risk because cleanup can remove durable local test accounts expected by other tests.

## Fixture Cleanup

`api_scope_storage_cleanup` deletes shared usernames, groups, and audit tickets both before and after each test. This makes single-process reruns repeatable, but it is unsafe across concurrent pytest processes sharing the same database.

Risk patterns:

- Setup cleanup from one process can delete rows just created by the other process.
- Teardown cleanup from one process can delete rows still needed by the other process.
- Cleanup is name-based, not ownership-based.
- Cleanup includes `test_user` and `test_staff_nomenu`, which overlap with the managed local account matrix.
- Cleanup resets canonical `ApiScope.active=True`, while tests can temporarily set a canonical scope inactive.

The fixture is useful for serial execution, but it is not a parallel isolation boundary.

## Transaction Scope

Some individual management-command paths are correctly tested for transaction rollback. That protects one command execution from its own injected failure.

It does not isolate the surrounding pytest process from another pytest process because:

- The suite bypasses pytest-django's normal test database lifecycle.
- Tests write to the shared restored database directly.
- Several assertions compare global counts such as `UserApiScopeGrant.objects.count()`, `GroupApiScopeGrant.objects.count()`, `ApiScopeGrantAudit.objects.count()`, and group membership counts.
- Global count assertions can change if another process writes unrelated rows at the same time.
- Cleanup is performed outside a per-test transaction that would be rolled back by pytest.

The command-level transactions are valid application safeguards, but they do not make the test suite parallel-safe.

## Database Reuse

The current design explicitly reuses the Docker Compose `db` service database (`nghcc_admin` by default). The scripts mount tests into a one-off `web` container and run pytest against the same database used by local restored data.

This is appropriate for staging-like smoke checks that validate restored DB/media health, but it is not appropriate for concurrent mutation tests unless each concurrent run gets its own database, schema, or Compose project.

`pytest.ini` also has no xdist configuration, no per-worker database suffixing, and no marker split between read-only smoke checks and database-mutating security tests.

## Pytest Parallel Safety

The current suite is not safe for parallel execution at the process level when processes share the same DB.

Safe or lower-risk areas:

- Read-only smoke checks.
- Read-only integration checks.
- Static security assertions.
- CSRF GET/POST rejection checks that do not reach a successful write.

Unsafe areas:

- Tests that create fixed users or groups.
- Tests that apply or rollback reviewed API scope plans with `--apply --confirm-*`.
- Tests that assert global database counts.
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
   - Run database-mutating tests serially until they use unique per-run fixture names and isolated databases.

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
3. Generate per-test or per-run usernames/groups/tickets for API scope storage tests.
4. Replace global count assertions with scoped assertions.
5. Add markers for read-only versus mutating tests.

Future parallelization:

1. Add isolated test databases per worker.
2. Add unique per-worker fixture namespaces.
3. Enable xdist only for tests whose fixtures have no shared restored-DB dependency.

## CI Impact

Current CI impact: none. The configured workflow does not run the conflicting scripts.

Future CI impact: high if smoke and CSRF are added as parallel jobs sharing the same restored DB fixture. The failure mode would be flaky duplicate-key errors, missing fixture rows, unexpected global counts, or inconsistent permission/audit state.

## Conclusion

The data conflict comes from shared database reuse plus fixed-name mutating fixtures. The safest immediate correction is execution policy: run `run-smoke-tests` and `run-csrf-tests` serially unless each run owns a separate database. Longer term, isolate mutating tests with unique fixture namespaces and per-worker databases before enabling pytest parallelism.
