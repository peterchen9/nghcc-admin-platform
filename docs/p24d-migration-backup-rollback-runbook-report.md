# P24D Migration/Backup/Rollback Runbook Report

Scope: documentation-only production migration, backup, restore, rollback, and
post-migration verification runbook.

Guardrails preserved:

- No deploy.
- No `.240` connection.
- No production env creation or modification.
- No production DB modification.
- No production migration execution.
- No API scope apply.
- No `API_PERMISSION_MODE=enforce`.
- No merge.
- No PR.

## Changes made

| File | Change |
| --- | --- |
| `docs/production-migration-backup-rollback-runbook.md` | Added production runbook covering DB backup, media backup/checksum, restore drill, explicit migration execution, rollback strategy, and post-migration smoke verification. |
| `docs/p24d-migration-backup-rollback-runbook-report.md` | Added this decision report. |

## Runbook decisions

| Area | Decision |
| --- | --- |
| DB backup | Required before any production migration; use internal DB container/network and `mysqldump`; do not publish MySQL. |
| Media backup | Required before any production migration/deploy; back up named media volume and generate checksums. |
| Checksums | Required for DB, media, compose/env snapshots, and rendered compose evidence. |
| Restore drill | Required in staging-like environment before production migration approval. |
| Migration execution | Separate one-off release-profile command; never part of web startup or automatic restart. |
| Static collection | Separate one-off release-profile command. |
| Smoke verification | Required after migration through the final public URL/reverse proxy. |
| Rollback | Depends on failure point; DB restore after migration requires explicit incident approval because it replaces later DB changes. |
| API rollback lever | Keep `API_PERMISSION_MODE=off`; do not enable `enforce` in this phase. |

## Validation results

Validation performed:

- Read back `AGENTS.md`.
- Reviewed P24A, P24B, and P24C reports.
- Reviewed existing backup/restore script inventory.
- `docker compose --env-file .env.production.example -f docker-compose.production.example.yml config`: PASS; production compose config rendered without starting containers.
- `docker compose --env-file .env.production.example -f docker-compose.production.example.yml --profile release config`: PASS; release-profile `migrate` and `collectstatic` services rendered without starting containers.
- Added docs only.
- No runtime tests were run because this phase changes no application behavior, compose behavior, settings, or scripts.

No production action was performed:

- No deploy.
- No `.240` access.
- No production DB access.
- No backup command executed against production.
- No restore command executed against production.
- No migration command executed.
- No containers started.

## Remaining production NO-GO blockers

Production remains **NO-GO** until:

- The runbook receives explicit phase approval for a specific production target.
- Real production `.env.production` exists outside Git and passes P24C policy.
- Final host/origin/HTTPS/cookie decisions are approved.
- Backup destination and retention policy are approved.
- Restore drill is actually performed and recorded.
- Production-like static/media and smoke verification are performed through the final URL.
- Any production migration receives explicit approval.

## GO / NO-GO

| Question | Decision | Reason |
| --- | --- | --- |
| GO for docs-only P24D runbook? | GO | Required backup, restore, migration, rollback, and smoke verification procedures are documented. |
| GO for production action? | NO-GO | This phase does not approve deploy, `.240` access, production DB access, backup execution, restore, or migration. |
| GO for automatic production migration? | NO-GO | Runbook requires migration to remain a separate approved one-off command. |
| GO for merge/PR? | NO-GO | User requested commit only; no merge or PR. |
