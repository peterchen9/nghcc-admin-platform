# Testing Decision Log

Updated: 2026-05-31

## Scope

This log records testing governance decisions only. P12 did not modify tests, backend code, CI, database state, or parallel execution settings, and did not run pytest.

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

## Current Guardrails

- Do not run smoke and CSRF wrappers concurrently against the same restored DB.
- Do not enable `pytest-xdist`.
- Do not add parallel CI test jobs that share DB state.
- Do not use markers as wrapper selection until marker accuracy is reviewed.
- `pytest.ini;C` and `tests;C` were removed in P13 after explicit cleanup approval and safety checks.
- Do not infer production permission readiness from local marker coverage.

## Next Decision Required

The next real change should be explicitly scoped before implementation. The likely candidates are:

1. Further marker audit for login/auth helper write behavior.
2. Separate design spike for per-worker DB isolation.
3. A documentation-only review of stale historical references to the removed `;C` directories, if desired.

None of these are approved by P13.

## P13 Verification Record

- `pytest.ini;C` existed before cleanup and was empty.
- `tests;C` existed before cleanup and was empty.
- No active references were found in `scripts/`, `.github/`, `tests/`, or `backend/`.
- `pytest.ini` remains the real pytest config.
- `pytest.ini` sets `testpaths = tests`, pointing discovery at the real `tests/` directory.
- Both empty `;C` directories were removed.
- P13 did not change DB isolation, `pytest-xdist`, CI, deploy behavior, `.240`, API scope assignment, tests, backend code, or pytest behavior.
- Pytest was not executed.
