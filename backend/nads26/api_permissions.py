import logging
from dataclasses import dataclass
from functools import wraps

from django.conf import settings
from rest_framework.response import Response


logger = logging.getLogger(__name__)

API_PERMISSION_MODE_OFF = 'off'
API_PERMISSION_MODE_REPORT_ONLY = 'report-only'
API_PERMISSION_MODE_ENFORCE = 'enforce'
VALID_API_PERMISSION_MODES = {
    API_PERMISSION_MODE_OFF,
    API_PERMISSION_MODE_REPORT_ONLY,
    API_PERMISSION_MODE_ENFORCE,
}

API_PERMISSION_SCOPE_MAP = {
    ('GET', '/api/hymns/'): 'api:hymns:read',
    ('POST', '/api/hymns/'): 'api:hymns:write',
    ('GET', '/api/hymns/<pk>/'): 'api:hymns:read',
    ('PUT', '/api/hymns/<pk>/'): 'api:hymns:write',
    ('DELETE', '/api/hymns/<pk>/'): 'api:hymns:write',
    ('POST', '/api/hymns/<pk>/upload/'): 'api:hymns:upload',
    ('POST', '/api/humnos/info/'): 'api:humnos:read',
    ('POST', '/api/humnos/download/'): 'api:humnos:write',
}


CANONICAL_API_SCOPES = tuple(sorted(set(API_PERMISSION_SCOPE_MAP.values())))


@dataclass(frozen=True)
class ApiScopeDecision:
    allowed: bool
    reason: str
    effective_scopes: frozenset


def get_api_permission_mode():
    mode = getattr(settings, 'API_PERMISSION_MODE', API_PERMISSION_MODE_OFF)
    mode = str(mode).strip().lower()
    if mode not in VALID_API_PERMISSION_MODES:
        return API_PERMISSION_MODE_OFF
    return mode


def api_permission_enabled():
    return get_api_permission_mode() != API_PERMISSION_MODE_OFF


def get_effective_api_scopes(user):
    """Return explicit stored scopes from active user and group grants."""
    if not getattr(user, 'is_authenticated', False):
        return frozenset()

    from modules.accounts.models import GroupApiScopeGrant, UserApiScopeGrant

    user_scope_values = UserApiScopeGrant.objects.filter(
        user=user,
        enabled=True,
        scope__active=True,
    ).values_list('scope__scope', flat=True)
    group_scope_values = GroupApiScopeGrant.objects.filter(
        group__user=user,
        enabled=True,
        scope__active=True,
    ).values_list('scope__scope', flat=True)

    return frozenset(set(user_scope_values) | set(group_scope_values))


def get_effective_api_scope_decision(user, scope):
    """Report-only storage decision helper; not wired to request blocking."""
    if not scope:
        return ApiScopeDecision(False, 'missing_scope_mapping', frozenset())
    if not getattr(user, 'is_authenticated', False):
        return ApiScopeDecision(False, 'anonymous_user', frozenset())
    if getattr(user, 'is_superuser', False):
        return ApiScopeDecision(True, 'superuser', frozenset())

    effective_scopes = get_effective_api_scopes(user)
    if scope in effective_scopes:
        return ApiScopeDecision(True, 'effective_scope', effective_scopes)
    return ApiScopeDecision(False, 'missing_scope', effective_scopes)


def user_has_api_scope(user, scope):
    """Future enforcement hook; intentionally conservative until scope storage is designed."""
    if not scope or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    explicit_scopes = getattr(user, 'api_scopes', ())
    return scope in explicit_scopes


def get_api_permission_decision(user, scope):
    if not scope:
        return False, 'missing_scope_mapping'
    if not getattr(user, 'is_authenticated', False):
        return False, 'anonymous_user'
    if getattr(user, 'is_superuser', False):
        return True, 'superuser'
    if scope in getattr(user, 'api_scopes', ()):
        return True, 'explicit_scope'
    return False, 'missing_scope'


def log_api_permission_report(mode, request, endpoint, scope, decision, reason):
    logger.info(
        (
            'api_permission_report mode=%s endpoint=%s method=%s scope=%s '
            'user_id=%s user_authenticated=%s user_is_superuser=%s '
            'decision=%s reason=%s'
        ),
        mode,
        endpoint,
        request.method,
        scope or '',
        getattr(request.user, 'id', None),
        getattr(request.user, 'is_authenticated', False),
        getattr(request.user, 'is_superuser', False),
        decision,
        reason,
    )


def api_permission_required(scope_by_method, endpoint):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            mode = get_api_permission_mode()
            if mode == API_PERMISSION_MODE_OFF:
                return view_func(request, *args, **kwargs)

            scope = scope_by_method.get(request.method)
            allowed, reason = get_api_permission_decision(request.user, scope)
            decision = 'allow' if allowed else 'deny'
            log_api_permission_report(mode, request, endpoint, scope, decision, reason)

            if mode == API_PERMISSION_MODE_REPORT_ONLY:
                return view_func(request, *args, **kwargs)

            if allowed:
                return view_func(request, *args, **kwargs)

            return Response(
                {
                    'detail': 'Missing API permission scope.',
                    'required_scope': scope,
                },
                status=403,
            )

        return wrapped

    return decorator
