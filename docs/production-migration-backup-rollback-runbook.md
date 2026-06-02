# Production Migration, Backup, Restore, and Rollback Runbook

This runbook defines the required production release procedure for DB backups,
media backups, explicit migrations, restore checks, rollback, and post-migration
smoke verification.

Status: policy/runbook only. It does not authorize deployment, `.240` access,
production DB modification, production migration, API scope apply, merge, or PR.

## 1. Approval Gates

Do not start production work until all gates are approved and recorded:

- Phase approval explicitly authorizes the production target, host, date, and operator.
- Final `.env.production` exists outside Git and contains no `UNUSABLE_REPLACE_ME_*` values.
- Final `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are approved.
- HTTPS/HTTP and secure-cookie policy are approved.
- Backup destination and retention policy are approved.
- Rollback owner and decision window are approved.
- Migration command is approved as a one-off release action.
- `API_PERMISSION_MODE=enforce` is not enabled unless separately approved.

If any gate is missing, stop with **NO-GO**.

## 2. Pre-Change Evidence

Record this evidence before touching production:

```text
release_id=<YYYYMMDD-HHMMSS>-<short-commit>
target_host=<approved host>
app_dir=<approved production app directory>
compose_file=docker-compose.production.example.yml or approved production copy
env_file=.env.production
current_commit=<git rev-parse HEAD>
operator=<name>
approval_reference=<ticket/report/message>
```

Capture the current compose/env snapshot:

```bash
mkdir -p "backups/${release_id}"
cp "${compose_file}" "backups/${release_id}/compose-${release_id}.yml"
cp "${env_file}" "backups/${release_id}/env-${release_id}.backup"
docker compose --env-file "${env_file}" -f "${compose_file}" config \
  > "backups/${release_id}/compose-rendered-${release_id}.yml"
```

The env backup must be stored outside Git and handled as a secret.

## 3. DB Backup

Production DB backup is required before any migration.

Use the internal DB container/network. Do not publish MySQL to the host for
backup access.

```bash
mkdir -p "backups/${release_id}"

docker compose --env-file "${env_file}" -f "${compose_file}" exec -T db \
  sh -c 'mysqldump \
    -u"$MYSQL_USER" \
    -p"$MYSQL_PASSWORD" \
    --single-transaction \
    --quick \
    --routines \
    --triggers \
    --events \
    --default-character-set=utf8mb4 \
    "$MYSQL_DATABASE"' \
  | gzip -9 > "backups/${release_id}/db-${release_id}.sql.gz"
```

Required evidence:

- `db-${release_id}.sql.gz` exists.
- File size is non-zero.
- Backup command exit code is `0`.
- No production schema change has happened yet.

## 4. Media Backup and Checksums

Media backup is required before migration or deploy.

For production named volume `nghcc-admin-media-data`:

```bash
docker run --rm \
  -v nghcc-admin-media-data:/media:ro \
  -v "$(pwd)/backups/${release_id}:/backup" \
  alpine:3.20 \
  tar -C /media -czf "/backup/media-${release_id}.tar.gz" .
```

Capture static/media volume metadata when useful:

```bash
docker volume inspect nghcc-admin-media-data \
  > "backups/${release_id}/media-volume-${release_id}.json"
docker volume inspect nghcc-admin-static-data \
  > "backups/${release_id}/static-volume-${release_id}.json"
```

Generate checksums:

```bash
cd "backups/${release_id}"
sha256sum * > "SHA256SUMS-${release_id}.txt"
sha256sum -c "SHA256SUMS-${release_id}.txt"
```

Required evidence:

- `media-${release_id}.tar.gz` exists.
- `SHA256SUMS-${release_id}.txt` exists.
- `sha256sum -c` passes before migration.
- DB, media, compose, rendered compose, and env backup are included.

## 5. Restore Drill Requirement

Before production migration approval, perform a restore drill in a
staging-like environment using the same backup artifacts.

DB restore drill:

```bash
gzip -dc "backups/${release_id}/db-${release_id}.sql.gz" \
  | docker compose --env-file "${env_file}" -f "${compose_file}" exec -T db \
      sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"'
```

Media restore drill into a non-production named volume:

```bash
docker volume create nghcc-admin-media-restore-drill
docker run --rm \
  -v nghcc-admin-media-restore-drill:/media \
  -v "$(pwd)/backups/${release_id}:/backup:ro" \
  alpine:3.20 \
  tar -C /media -xzf "/backup/media-${release_id}.tar.gz"
```

Then run media integrity checks where available:

```bash
scripts/check-media-integrity.sh volume nghcc-admin-media-restore-drill
```

The restore drill must be documented before production migration. If the drill
fails, production migration is **NO-GO**.

## 6. Migration Execution

Production web startup must not run migrations automatically.

Approved production startup remains:

```text
web: gunicorn nads26.wsgi:application --bind 0.0.0.0:8000
```

Approved migration execution is a separate one-off release command:

```bash
docker compose --env-file "${env_file}" \
  -f "${compose_file}" \
  --profile release run --rm migrate
```

Rules:

- Run migration only after DB backup, media backup, checksums, and restore drill evidence are approved.
- Do not run migration as part of `web` container startup.
- Do not run migration automatically on container restart.
- Record migration output and exit code.
- If migration fails, stop and enter rollback/incident decision mode.

Static collection is also a separate release command:

```bash
docker compose --env-file "${env_file}" \
  -f "${compose_file}" \
  --profile release run --rm collectstatic
```

## 7. Post-Migration Smoke Verification

Run smoke verification through the final public URL and reverse proxy, not by
bypassing Nginx to Django directly.

Required checks:

- `GET /api/health/` returns healthy DB status.
- Login page loads.
- Admin page loads for an approved staff account.
- Logout uses the expected protected flow.
- Static asset probe returns `200`, for example `/static/admin/css/base.css`.
- Known media probe returns `200` and no directory listing is exposed.
- CKEditor upload flow is verified with CSRF protection.
- Humnos and hymns representative pages/API endpoints load.
- Eureka delete remains POST-only.
- Cookie headers match final HTTPS/HTTP policy.
- Unknown host probe returns rejected/invalid host behavior where practical.

Preferred wrapper scripts for local/staging-like validation:

```powershell
.\scripts\run-smoke-tests.ps1
.\scripts\run-csrf-tests.ps1
```

Production smoke execution must be separately approved and must use the final
production URL and approved credentials.

## 8. Rollback Strategy

Rollback must be chosen based on the failure point.

### Before migration

If failure happens before migration:

- Do not run migration.
- Restore previous compose/env if they were changed.
- Keep DB and media untouched.
- Re-run config validation and smoke checks.

### After deploy but before migration

If runtime/proxy/static changes fail before migration:

- Revert to previous compose/env snapshot.
- Restart only the approved runtime services.
- Do not restore DB unless data was modified.
- Re-run smoke checks through the final URL.

### After migration

If migration has modified schema/data:

- Prefer a reviewed forward fix when data loss risk is lower than full DB restore.
- Use DB restore only with explicit incident approval because it replaces all
  DB changes after the backup timestamp.
- Media restore is required only if media changed or integrity checks fail.
- Keep `API_PERMISSION_MODE=off` as the rollback lever for API permission issues.

DB restore command pattern:

```bash
gzip -dc "backups/${release_id}/db-${release_id}.sql.gz" \
  | docker compose --env-file "${env_file}" -f "${compose_file}" exec -T db \
      sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"'
```

Media restore command pattern:

```bash
docker run --rm \
  -v nghcc-admin-media-data:/media \
  -v "$(pwd)/backups/${release_id}:/backup:ro" \
  alpine:3.20 \
  sh -c 'rm -rf /media/* && tar -C /media -xzf "/backup/media-${release_id}.tar.gz"'
```

Media restore deletes current media volume contents before restoring the backup.
Use it only with explicit approval and confirmed backup checksums.

## 9. Final Release Record

Every production migration/release record must include:

- Approval reference.
- Commit hash.
- Final host/origin/cookie decision.
- DB backup path, size, and checksum result.
- Media backup path, size, and checksum result.
- Compose/env snapshot paths.
- Restore drill result.
- Migration command and exit code.
- Static collection command and exit code.
- Smoke verification results.
- Rollback decision: not needed, forward fix, or restore performed.
- Final GO / NO-GO.
