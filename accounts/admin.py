from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
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


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
