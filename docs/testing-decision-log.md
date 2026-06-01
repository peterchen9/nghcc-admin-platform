# Testing Decision Log

Updated: 2026-06-01

## Scope

This log records testing governance decisions only. P16 did not modify tests, backend code, CI, database state, pytest discovery settings, or parallel execution settings, and did not run pytest.

## Decisions

| Date | Phase | Decision | Reason | Status |
| --- | --- | --- | --- | --- |
| 2026-05-31 | P7 | Keep API scope storage tests serial, but move disposable users, groups, tickets, and assertions to generated namespaces. | Fixed names and global counts were unsafe against shared restored DB state. Namespace ownership reduces serial rerun and local collision risk. | Completed |
| 2026-05-31 | P7 | Do not treat namespace cleanup as parallel isolation. | Multiple pytest processes would still share canonical DB rows and restored local state. | Completed |
| 2026-05-31 | P8 | Use `read_only`, `mutating`, `csrf`, and `api_scope` as the marker taxonomy. | The suite needs explicit behavior labels before any selection or execution-policy change. | Completed |
| 2026-05-31 | P8 | Keep marker-selected commands advisory. | Marker coverage was not yet broad or verified enough to drive wrappers or CI. | Completed |
| 2026-05-31 | P9 | Expand markers only for low-risk or clearly classified tests. | Auth helpers, write endpoints, login side effects, and shared restored data still require conservative handling. | Completed |
| 2026-05-31 | P9 | Leave ambiguous DB-auth and write-path cases unclassified as `read_only`. | `client.login()` and `force_login()` may write `last_login`; write endpoints may mutate on non-obvious paths. | Completed |
| 2026-05-31 | P10 | Align documentation around serial smoke then CSRF execution. | Both wrappers run broad overlapping suites against the same restored local DB. | Completed |
| 2026-05-31 | P10 | Do not change wrapper commands, CI workflow, DB isolation, or production behavior as part of documentation alignment. | Documentation alignment should not alter runtime behavior. | Completed |
| 2026-05-31 | P11 | Retain the current shared restored DB model for now. | It matches current local smoke/staging-like verification and avoids unreviewed fixture/settings changes. | Completed |
| 2026-05-31 | P11 | Do not enable `pytest-xdist`. | Worker-level DB ownership, media/temp isolation, and marker accuracy are not yet ready. | Completed |
| 2026-05-31 | P11 | Treat `pytest.ini;C` and `tests;C` as a separate repo-hygiene cleanup item. | They appear empty and not active in normal discovery, but deletion was outside the approved phase. | Completed |
| 2026-05-31 | P12 | Establish `testing-baseline` and `testing-decision-log` as governance records. | Future testing changes need a stable baseline and auditable decision trail. | Completed |
| 2026-05-31 | P13 | Remove `pytest.ini;C` and `tests;C` after confirming both were empty and had no active references in `scripts/`, `.github/`, `tests/`, or `backend/`. | Repo-root hygiene closure reduces discovery and working-directory noise without changing test behavior. | Completed |
| 2026-06-01 | P14 | Align active governance references to describe `pytest.ini;C` and `tests;C` as previously observed and removed in P13. | Readers should not infer the empty `;C` directories still exist after P13. | Completed |
| 2026-06-01 | P16 | Treat Django auth/session helpers as mutation risks for marker policy. | `read_only` is advisory only and does not prove transaction isolation, no session writes, or parallel safety. | Completed |

## Current Guardrails

- Do not run smoke and CSRF wrappers concurrently against the same restored DB.
- Do not enable `pytest-xdist`.
- Do not add parallel CI test jobs that share DB state.
- Do not use markers as wrapper selection until marker accuracy is reviewed.
- `pytest.ini;C` and `tests;C` were removed in P13 after explicit cleanup approval and safety checks.
- Pytest discovery points at the real `pytest.ini` file and `tests/` directory.
- `read_only` is not a transaction guarantee, no-session-write guarantee, or `pytest-xdist` / parallel-safety guarantee.
- Tests using `client.login()`, `force_login()`, `logged_in_client`, `admin_client`, or other login/session fixtures stay out of any truly parallel-safe read-only bucket unless later evidence proves no session or auth writes.
- Do not infer production permission readiness from local marker coverage.

## Next Decision Required

The next real change should be explicitly scoped before implementation. The likely candidates are:

1. Further marker audit for login/auth helper write behavior.
2. Separate design spike for per-worker DB isolation.
3. Review stale historical references only if new active wording implies the removed `;C` directories still exist.

None of these are approved by P16.

## P13 Verification Record

- `pytest.ini;C` existed before cleanup and was empty.
- `tests;C` existed before cleanup and was empty.
- No active references were found in `scripts/`, `.github/`, `tests/`, or `backend/`.
- `pytest.ini` remains the real pytest config.
- `pytest.ini` sets `testpaths = tests`, pointing discovery at the real `tests/` directory.
- Both empty `;C` directories were removed.
- P13 did not change DB isolation, `pytest-xdist`, CI, deploy behavior, `.240`, API scope assignment, tests, backend code, or pytest behavior.
- Pytest was not executed.

## P14 Reference Alignment Record

- Active governance references now describe `pytest.ini;C` and `tests;C` as previously observed and removed in P13.
- P14 did not change DB isolation, `pytest-xdist`, CI, deploy behavior, `.240`, API scope assignment, tests, backend code, pytest config, or pytest behavior.
- Pytest was not executed.

## P16 Auth Helper Marker Policy Record

- `read_only` is advisory only. It is not a transaction guarantee, no-session-write guarantee, or `pytest-xdist` / parallel-safety guarantee.
- `client.login()`, `force_login()`, `logged_in_client`, `admin_client`, and other login/session fixtures are treated as auth/session mutation risks until proven otherwise.
- Authenticated GET tests can still save session state or trigger auth side effects.
- Anonymous write-endpoint rejection tests are not automatically `read_only`.
- Settings reload tests may remain `read_only` when DB-free, but they are process-global mutations rather than parallel-safety evidence.
- Global count assertions are not proof that a test is safe under concurrent writers.
- P16 did not change DB isolation, `pytest-xdist`, CI, deploy behavior, `.240`, API scope assignment, tests, backend code, pytest config, or pytest behavior.
- Pytest was not executed.
