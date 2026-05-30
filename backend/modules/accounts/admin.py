from django.contrib import admin
from .models import (
    ApiScope,
    ApiScopeGrantAudit,
    GroupApiScopeGrant,
    SystemSetting,
    UserApiScopeGrant,
    UserProfile,
)


@admin.register(ApiScope)
class ApiScopeAdmin(admin.ModelAdmin):
    list_display = ('scope', 'label', 'category', 'active')
    list_filter = ('active', 'category')
    search_fields = ('scope', 'label', 'description')


@admin.register(UserApiScopeGrant)
class UserApiScopeGrantAdmin(admin.ModelAdmin):
    list_display = ('user', 'scope', 'enabled', 'created_at', 'created_by')
    list_filter = ('enabled', 'scope')
    search_fields = ('user__username', 'scope__scope', 'reason')


@admin.register(GroupApiScopeGrant)
class GroupApiScopeGrantAdmin(admin.ModelAdmin):
    list_display = ('group', 'scope', 'enabled', 'created_at', 'created_by')
    list_filter = ('enabled', 'scope')
    search_fields = ('group__name', 'scope__scope', 'reason')


@admin.register(ApiScopeGrantAudit)
class ApiScopeGrantAuditAdmin(admin.ModelAdmin):
    list_display = (
        'event_id',
        'plan_version',
        'action',
        'status',
        'dry_run',
        'ticket',
        'created_at',
    )
    list_filter = ('dry_run', 'status', 'action')
    search_fields = (
        'event_id',
        'plan_checksum',
        'principal_name',
        'ticket',
        'reviewed_by',
    )
    readonly_fields = ('created_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'worker_ename')
    search_fields = ('user__username', 'display_name', 'worker_ename')

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('description', 'key', 'value')
    fields = ('description', 'key', 'value')
    readonly_fields = ('key',)  # Keep key read-only to avoid breaking logic
