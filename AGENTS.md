# Repository Rules

These rules apply to all work in this repository. They consolidate the
long-term guardrails established across the P20-P24 governance, security,
testing, and production-readiness phases.

## Production Safety

- Never deploy without explicit phase approval.
- Never access `.240` without explicit instruction.
- Never modify the production DB without explicit approval.
- Never run production migration automatically.
- Treat production readiness as gated work: backup, rollback, static/media,
  CSRF, env, and smoke evidence must be reviewed before production changes.

## Git Workflow

- Never merge automatically.
- Never create PR automatically.
- Keep changes minimal and scoped.
- Prefer documentation-only changes when the approved phase is docs only.
- Do not include unrelated working-tree changes in commits.

## Security

- `API_PERMISSION_MODE=enforce` requires explicit approval.
- Applying or enforcing API scopes requires explicit approval.
- Security changes require verification.
- CSRF, auth, permission, API scope, cookie, host, secret, migration, and DB
  exposure changes must be treated as security-sensitive.
- Production security posture remains NO-GO until the relevant decision report
  or phase approval says otherwise.

## Testing

- Run smoke tests after security-sensitive changes.
- Run CSRF tests after CSRF/auth changes.
- Prefer existing wrapper scripts.
- Use local/staging-like validation before production-facing decisions.
- For docs-only governance changes, record why runtime tests were not required.

## Documentation

- Update related docs when behavior changes.
- Record decision reports for governance/security phases.
- Preserve phase guardrails in reports, especially no deploy, no `.240`, no
  production DB change, no automatic production migration, no merge, and no PR.
- Include GO / NO-GO decisions for production, security, and release gates.

## Response Format

Every task completion should include:

- Modified files.
- Validation results.
- Git diff summary.
- Git status.
- Commit hash.
- GO / NO-GO.
