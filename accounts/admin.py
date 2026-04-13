from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, AuditLog


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    min_num = 1
    max_num = 1
    verbose_name_plural = 'Permissions & Profile'
    fieldsets = (
        ('Dashboard', {
            'fields': (
                'can_access_dashboard',
                ('dashboard_show_financial_summary', 'dashboard_show_workflow_queues', 'dashboard_show_activity'),
            ),
            'description': 'Who may open the dashboard and which sections they see.',
        }),
        ('Billing workflow', {
            'fields': (
                ('can_submit_bill', 'can_mark_bill_paid'),
            ),
            'description': 'Submit = pending → submitted (e.g. service). Mark paid = submitted → paid (e.g. accounts).',
        }),
        ('Permissions', {
            'fields': (
                ('can_add_client', 'can_edit_client', 'can_delete_client'),
                ('can_generate_bill', 'can_edit_bill', 'can_delete_bill'),
                ('can_view_reports', 'can_export_reports'),
            )
        }),
        ('Personal Info', {
            'fields': ('phone', 'department', 'profile_picture')
        }),
    )


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active',
                    'get_can_add_client', 'get_can_generate_bill')

    def get_can_add_client(self, obj):
        try:
            return obj.profile.can_add_client
        except UserProfile.DoesNotExist:
            return False
    get_can_add_client.short_description = 'Add Client'
    get_can_add_client.boolean = True

    def get_can_generate_bill(self, obj):
        try:
            return obj.profile.can_generate_bill
        except UserProfile.DoesNotExist:
            return False
    get_can_generate_bill.short_description = 'Generate Bill'
    get_can_generate_bill.boolean = True


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'can_access_dashboard', 'can_submit_bill', 'can_mark_bill_paid',
        'dashboard_show_financial_summary', 'dashboard_show_workflow_queues', 'dashboard_show_activity',
    )
    list_filter = (
        'can_access_dashboard', 'can_submit_bill', 'can_mark_bill_paid',
        'dashboard_show_financial_summary', 'dashboard_show_workflow_queues', 'dashboard_show_activity',
    )
    search_fields = ('user__username', 'user__email', 'department')
    raw_id_fields = ('user',)
    fieldsets = UserProfileInline.fieldsets


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'target_model', 'object_pk', 'object_repr_short', 'ip_address')
    list_filter = ('action', 'target_model', 'created_at')
    search_fields = ('object_repr', 'object_pk', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('user', 'action', 'target_model', 'object_pk', 'object_repr', 'ip_address', 'created_at')

    @admin.display(description='Description')
    def object_repr_short(self, obj):
        text = (obj.object_repr or '')[:80]
        return text + ('…' if len(obj.object_repr or '') > 80 else '')

    def _can_view_logs(self, request):
        return request.user.is_active and request.user.is_staff and (
            request.user.is_superuser or request.user.has_perm('accounts.view_auditlog')
        )

    def has_module_permission(self, request):
        return self._can_view_logs(request)

    def has_view_permission(self, request, obj=None):
        return self._can_view_logs(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
