param(
    [string]$ComposeCommand = "docker-compose",
    [string]$ApplyPlan = "docs/samples/api-scope-disposable-reviewed-apply.csv",
    [string]$RollbackPlan = "docs/samples/api-scope-disposable-reviewed-rollback.csv"
)

$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Get-ComposeArgs {
    param([string[]]$ExtraArgs)

    $composeFileArgs = @("-f", "docker-compose.yml", "-f", "docker-compose.volume.yml")
    return $composeFileArgs + $ExtraArgs
}

function Invoke-Compose {
    param([string[]]$Arguments)

    & $ComposeCommand @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$ComposeCommand failed with exit code $LASTEXITCODE."
    }
}

function Invoke-ComposeText {
    param([string[]]$Arguments)

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = (& $ComposeCommand @Arguments 2>$null | Out-String)
        if ($LASTEXITCODE -ne 0) {
            throw "$ComposeCommand failed with exit code $LASTEXITCODE.`n$output"
        }
        return $output
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Invoke-WebPython {
    param(
        [string]$Name,
        [string]$Code
    )

    $tempPath = Join-Path ([System.IO.Path]::GetTempPath()) "$Name.py"
    [System.IO.File]::WriteAllText(
        $tempPath,
        $Code,
        [System.Text.UTF8Encoding]::new($false)
    )
    try {
        & docker cp $tempPath "nghcc-admin-web:/tmp/$Name.py"
        if ($LASTEXITCODE -ne 0) {
            throw "docker cp failed with exit code $LASTEXITCODE."
        }
        Invoke-Compose @(
            "exec", "-T",
            "web", "python", "manage.py", "shell",
            "-c", "exec(open('/tmp/$Name.py').read())"
        )
    }
    finally {
        Remove-Item -LiteralPath $tempPath -ErrorAction SilentlyContinue
    }
}

$applyPath = (Resolve-Path $ApplyPlan).Path
$rollbackPath = (Resolve-Path $RollbackPlan).Path
$applyMount = "${applyPath}:/tmp/api-scope-disposable-reviewed-apply.csv:ro"
$rollbackMount = "${rollbackPath}:/tmp/api-scope-disposable-reviewed-rollback.csv:ro"

$preflight = @'
from django.contrib.auth.models import Group, User
from modules.accounts.models import ApiScopeGrantAudit, GroupApiScopeGrant, UserApiScopeGrant

usernames = ["test_user", "test_staff_nomenu"]
group_name = "test_api_scope_drill_readers"
tickets = ["SEC-API-DRILL", "SEC-API-DRILL-RB"]

for username in usernames:
    if not username.startswith("test_"):
        raise RuntimeError(f"unsafe username: {username}")
if not group_name.startswith("test_"):
    raise RuntimeError(f"unsafe group: {group_name}")

ApiScopeGrantAudit.objects.filter(ticket__in=tickets).delete()
groups = Group.objects.filter(name=group_name)
UserApiScopeGrant.objects.filter(user__username__in=usernames).delete()
GroupApiScopeGrant.objects.filter(group__in=groups).delete()
groups.delete()

for username in usernames:
    user, _ = User.objects.get_or_create(username=username)
    user.is_active = True
    user.is_staff = username == "test_staff_nomenu"
    user.is_superuser = False
    user.set_password("local-test-password-12345")
    user.save()

print("preflight_ready")
'@

$verifyAfterApply = @'
from django.contrib.auth.models import Group, User
from modules.accounts.models import ApiScopeGrantAudit, ApiScope, GroupApiScopeGrant, UserApiScopeGrant

group = Group.objects.get(name="test_api_scope_drill_readers")
test_user = User.objects.get(username="test_user")
service_user = User.objects.get(username="test_staff_nomenu")
scope = ApiScope.objects.get(scope="api:humnos:read", active=True)

assert test_user.groups.filter(name=group.name).exists()
assert GroupApiScopeGrant.objects.filter(group=group, scope=scope, enabled=True).exists()
assert UserApiScopeGrant.objects.filter(user=service_user, scope=scope, enabled=True).exists()
assert ApiScopeGrantAudit.objects.filter(ticket="SEC-API-DRILL", dry_run=False, status="applied").count() == 4
assert not ApiScopeGrantAudit.objects.filter(ticket="SEC-API-DRILL", dry_run=True).exists()
print("apply_verified")
'@

$verifyAfterRollback = @'
from django.contrib.auth.models import Group, User
from modules.accounts.models import ApiScopeGrantAudit, ApiScope, GroupApiScopeGrant, UserApiScopeGrant

group = Group.objects.get(name="test_api_scope_drill_readers")
test_user = User.objects.get(username="test_user")
service_user = User.objects.get(username="test_staff_nomenu")
scope = ApiScope.objects.get(scope="api:humnos:read", active=True)

assert not test_user.groups.filter(name=group.name).exists()
assert GroupApiScopeGrant.objects.filter(group=group, scope=scope, enabled=False).exists()
assert UserApiScopeGrant.objects.filter(user=service_user, scope=scope, enabled=False).exists()
assert not GroupApiScopeGrant.objects.filter(group=group, scope=scope, enabled=True).exists()
assert not UserApiScopeGrant.objects.filter(user=service_user, scope=scope, enabled=True).exists()

apply_events = set(ApiScopeGrantAudit.objects.filter(ticket="SEC-API-DRILL").values_list("event_id", flat=True))
rollback_events = ApiScopeGrantAudit.objects.filter(ticket="SEC-API-DRILL-RB", dry_run=False).order_by("row_number")
assert rollback_events.count() == 3
assert {event.status for event in rollback_events} == {"rolled_back"}
assert {event.rollback_of for event in rollback_events} <= apply_events
assert {event.rollback_of for event in rollback_events}
print("rollback_verified")
print("enabled_group_grants", GroupApiScopeGrant.objects.filter(group=group, enabled=True).count())
print("enabled_user_grants", UserApiScopeGrant.objects.filter(user__username__in=["test_user", "test_staff_nomenu"], enabled=True).count())
print("membership_exists", test_user.groups.filter(name=group.name).exists())
print("apply_audit_events", len(apply_events))
print("rollback_audit_events", rollback_events.count())
'@

Write-Host "Checking Docker Compose containers..."
Invoke-Compose (Get-ComposeArgs @("ps"))

Write-Host "Preparing disposable test_* drill data..."
Invoke-WebPython -Name "api_scope_drill_preflight" -Code $preflight

Write-Host "Apply dry-run..."
$applyDryRun = Invoke-ComposeText (Get-ComposeArgs @(
    "run", "--rm",
    "-v", $applyMount,
    "web", "python", "manage.py", "apply_api_scope_reviewed_plan",
    "--plan-file", "/tmp/api-scope-disposable-reviewed-apply.csv",
    "--expected-plan-version", "1",
    "--reviewed-by", "peter",
    "--ticket", "SEC-API-DRILL"
))
$applyDryRun.Trim()

Write-Host "Apply with confirm..."
$applyResult = Invoke-ComposeText (Get-ComposeArgs @(
    "run", "--rm",
    "-v", $applyMount,
    "web", "python", "manage.py", "apply_api_scope_reviewed_plan",
    "--plan-file", "/tmp/api-scope-disposable-reviewed-apply.csv",
    "--expected-plan-version", "1",
    "--reviewed-by", "peter",
    "--ticket", "SEC-API-DRILL",
    "--apply",
    "--confirm-apply"
))
$applyResult.Trim()

Write-Host "Verifying apply grants, membership, and audit..."
Invoke-WebPython -Name "api_scope_drill_verify_apply" -Code $verifyAfterApply

Write-Host "Rollback dry-run..."
$rollbackDryRun = Invoke-ComposeText (Get-ComposeArgs @(
    "run", "--rm",
    "-v", $rollbackMount,
    "web", "python", "manage.py", "rollback_api_scope_reviewed_plan",
    "--plan-file", "/tmp/api-scope-disposable-reviewed-rollback.csv",
    "--reviewed-by", "peter",
    "--ticket", "SEC-API-DRILL-RB"
))
$rollbackDryRun.Trim()

Write-Host "Rollback with confirm..."
$rollbackResult = Invoke-ComposeText (Get-ComposeArgs @(
    "run", "--rm",
    "-v", $rollbackMount,
    "web", "python", "manage.py", "rollback_api_scope_reviewed_plan",
    "--plan-file", "/tmp/api-scope-disposable-reviewed-rollback.csv",
    "--reviewed-by", "peter",
    "--ticket", "SEC-API-DRILL-RB",
    "--apply",
    "--confirm-rollback"
))
$rollbackResult.Trim()

Write-Host "Verifying rollback state and rollback_of audit chain..."
Invoke-WebPython -Name "api_scope_drill_verify_rollback" -Code $verifyAfterRollback

Write-Host "API scope disposable apply/rollback drill completed."
