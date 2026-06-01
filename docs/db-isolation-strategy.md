# DB Isolation Strategy

Updated: 2026-06-01

## Boundary

P11 was documentation-only. P14 is documentation-only reference alignment after P13.

- `pytest.ini;C` and `tests;C` were previously observed and were removed in P13 after both were confirmed empty.
- Do not modify fixtures.
- Do not modify the database.
- Do not enable `pytest-xdist`.
- Do not change CI.
- Do not run pytest.

P13 repo-root hygiene closure is limited to the two previously documented empty directories:

- Confirm and remove `pytest.ini;C`.
- Confirm and remove `tests;C`.
- Do not change DB isolation, fixtures, CI, test behavior, `pytest-xdist`, deploy behavior, `.240`, or API scope assignments.
- Do not run pytest.

## Empty Directory Risk Review

P11 observed two unexpected repo-root directories before cleanup:

| Path | Type | Created | Last written | Contents |
| --- | --- | --- | --- | --- |
| `pytest.ini;C` | Directory | 2026-05-29 15:36:33 | 2026-05-29 15:36:33 | Empty |
| `tests;C` | Directory | 2026-05-29 15:36:33 | 2026-05-29 15:36:33 | Empty |

`Get-ChildItem -LiteralPath 'pytest.ini;C' -Force -Recurse` and `Get-ChildItem -LiteralPath 'tests;C' -Force -Recurse` returned no child files or directories.

The exact generation cause is not recorded in the repo. The shared timestamp and `;C` suffix suggest a command-line typo or shell parsing artifact around a Windows-style mount or command fragment, but that is an inference only.

Search did not find any script or workflow intentionally referencing `pytest.ini;C` or `tests;C`. Existing scripts mount the real `pytest.ini` and `tests` paths:

- `scripts/run-smoke-tests.ps1`
- `scripts/run-smoke-tests.sh`
- `scripts/run-csrf-tests.ps1`
- `scripts/run-csrf-tests.sh`
- `scripts/run-api-permission-staging-like-recheck.ps1`

`pytest.ini` sets:

```ini
testpaths = tests
```

That points pytest discovery at the real `tests` directory. The previously observed empty `tests;C` directory was not expected to be collected by normal repo-root pytest discovery because it was not named `tests` and was not listed in `testpaths`.

Current CI is not affected by these directories. `.github/workflows/smoke-tests.yml` builds containers and prints a placeholder message. It does not run pytest, `run-smoke-tests`, or `run-csrf-tests`.

P13 closure confirmed both directories were still empty, confirmed no active references in `scripts/`, `.github/`, `tests/`, or `backend/`, and removed them. Documentation references remain as historical governance records.

## Current State

The current test model uses a shared restored database, not a pytest-managed disposable database.

`tests/conftest.py` has an autouse fixture that unblocks database access:

```text
Smoke tests read the already-restored local database, not a new test DB.
```

The default Docker Compose database is MySQL via the `db` service. `backend/nads26/settings.py` defaults to `django.db.backends.mysql`, and `docker-compose.yml` points the web container at `DB_HOST=db` and `DB_NAME=nghcc_admin` by default.

The risk profile is the same as a shared sqlite-style local test database: multiple pytest processes can see and mutate the same durable state unless a wrapper, fixture, or worker-level strategy gives each run independent ownership.

## Current Mitigations

`tests/security/test_api_scope_storage.py` has moved away from historical fixed disposable names. It now uses per-test namespace values for usernames, groups, and audit tickets.

Setup and teardown cleanup are namespace-scoped. They delete rows whose usernames, group names, or audit tickets start with the current test namespace rather than deleting durable local account-matrix users.

Assertions have also been narrowed. Previously risky global count checks were replaced with namespace-scoped or target-specific assertions for report-only, dry-run, rejected apply, rejected rollback, and invalid-plan paths.

These mitigations help serial reruns and reduce unrelated-data sensitivity. They do not create process-level database isolation.

## Existing Risks

Parallel execution remains unsafe when processes share one restored database.

Main risks:

- `run-smoke-tests` and `run-csrf-tests` still execute broad overlapping target sets.
- Wrapper scripts do not allocate separate databases per run.
- Future `pytest-xdist` workers would share the same DB unless worker-level DB naming is added.
- Flaky data collisions can still occur if two workers create, update, delete, or assert against overlapping rows.
- Namespace cleanup protects only reviewed namespaced data, not every mutable table or canonical row.
- Tests can temporarily mutate canonical state such as `ApiScope.active`.
- Any remaining global count assertion can become flaky if another process writes unrelated rows.

## Candidate Options

### Option A: Temporary SQLite Per Test Session

Create one temporary sqlite database for each pytest session and point Django at it for tests.

Benefits:

- Lower risk than the current shared restored DB for local test runs.
- Good fit for serial test sessions.
- Avoids durable local DB mutation.

Costs and limits:

- Requires fixture/settings work to switch DB settings for tests.
- May diverge from production-like MySQL behavior.
- Still not enough for `xdist` if multiple workers share the same sqlite file.
- Needs seed/migration strategy for tests that currently depend on restored data.

### Option B: Temporary SQLite Per Worker

Create one temporary sqlite database per pytest worker, for example using worker-specific paths.

Benefits:

- Lowest collision risk among the candidate options.
- Best future fit for `pytest-xdist`.
- Each worker owns its DB file and cleanup boundary.

Costs and limits:

- Highest implementation cost.
- Requires worker-aware DB settings, migrations/seeding, and fixture naming.
- Any tests that must validate restored MySQL/media behavior still need a separate serial lane.
- Requires careful CI wiring so worker DBs are created and destroyed predictably.

### Option C: Transaction Rollback Fixture

Use a test fixture that wraps each test in a transaction and rolls it back afterward.

Benefits:

- Can reduce durable writes within one process.
- Preserves one shared DB target while improving per-test cleanup.
- Useful for many Django unit/integration tests when they do not need cross-transaction behavior.

Costs and limits:

- Higher cost in this repo because current tests intentionally unblock access to restored DB state.
- Does not isolate separate pytest processes or `xdist` workers if they share one DB.
- Management commands, explicit commits, connection boundaries, file/media writes, and external side effects may escape the transaction boundary.
- CI compatibility is only medium unless test categories are split carefully.

### Option D: Current Namespace Strategy

Keep the current shared restored database model and rely on serial execution plus namespace cleanup and scoped assertions.

Benefits:

- Lowest implementation cost.
- Matches the current smoke-test purpose: validate restored local DB/media behavior.
- No fixture, DB, CI, or xdist changes required.
- Works with the current placeholder CI because CI does not run pytest.

Costs and limits:

- Parallel execution remains unsafe.
- Future xdist remains blocked for mutating tests.
- Flaky collisions remain possible if broad wrappers are run concurrently.
- Namespace ownership must keep expanding before mutating tests can be trusted in shared state.

## Comparison

| 方案 | 風險 | 成本 | CI相容 |
| --- | --- | --- | --- |
| A | 低 | 中 | 高 |
| B | 最低 | 高 | 高 |
| C | 中 | 高 | 中 |
| D | 現況 | 最低 | 中 |

## Recommendation

```text
維持 D
→ 未來若要 xdist
→ 優先升級到 B
```

For the next phase, keep serial wrapper execution and avoid parallel CI changes.

## P13 Repo Root Hygiene Closure

Updated: 2026-05-31

P13 confirmed:

- `pytest.ini;C` existed before cleanup and was an empty directory.
- `tests;C` existed before cleanup and was an empty directory.
- `scripts/`, `.github/`, `tests/`, and `backend/` had no references to `pytest.ini;C` or `tests;C`.
- Existing documentation references were historical governance notes, not active runtime references.
- `pytest.ini` is the real pytest config file.
- `pytest.ini` sets `testpaths = tests`, so discovery points at the real `tests/` directory.

P13 removed:

- `pytest.ini;C`
- `tests;C`

This was repo-root hygiene only. It was not a DB isolation change, `pytest-xdist` change, CI change, deploy change, `.240` change, API scope assignment, or test behavior change.

Pytest was not executed for P13.
