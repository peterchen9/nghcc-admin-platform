from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class ApiScope(models.Model):
    scope = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True, default='')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scope']

    def __str__(self):
        return self.scope


class UserApiScopeGrant(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='api_scope_grants',
    )
    scope = models.ForeignKey(
        ApiScope,
        on_delete=models.CASCADE,
        related_name='user_grants',
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_api_scope_grants',
    )
    reason = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'scope'],
                name='unique_user_api_scope_grant',
            ),
        ]
        ordering = ['user__username', 'scope__scope']

    def __str__(self):
        return f'{self.user.username}: {self.scope.scope}'


class GroupApiScopeGrant(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='api_scope_grants',
    )
    scope = models.ForeignKey(
        ApiScope,
        on_delete=models.CASCADE,
        related_name='group_grants',
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_group_api_scope_grants',
    )
    reason = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'scope'],
                name='unique_group_api_scope_grant',
            ),
        ]
        ordering = ['group__name', 'scope__scope']

    def __str__(self):
        return f'{self.group.name}: {self.scope.scope}'

class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='profile', verbose_name='使用者',
    )
    worker_ename = models.CharField(
        '同工英文名', max_length=50, blank=True, default='',
    )
    display_name = models.CharField(
        '顯示名稱（中文姓名）', max_length=100, blank=True, default='',
    )
    department = models.CharField('部門', max_length=50, blank=True, default='')
    worker_id = models.CharField('同工編號', max_length=20, blank=True, default='')
    role = models.CharField('角色', max_length=50, blank=True, default='')
    allowed_menu_items = models.ManyToManyField(
        'menu.MenuItem', blank=True, verbose_name='可存取的選單項目'
    )

    class Meta:
        verbose_name = '使用者擴充資料'
        verbose_name_plural = '使用者擴充資料'

    def __str__(self):
        return f'{self.user.username} — {self.display_name or self.worker_ename}'

class SystemSetting(models.Model):
    key = models.CharField("設定鍵", max_length=50, unique=True, help_text="系統內部識別碼，請勿修改。")
    value = models.TextField("設定值", blank=True)
    description = models.CharField("描述", max_length=200, blank=True)

    class Meta:
        verbose_name = "系統設定"
        verbose_name_plural = "系統設定"

    def __str__(self):
        return f"{self.description} ({self.key})"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            worker_ename=instance.username,
        )
