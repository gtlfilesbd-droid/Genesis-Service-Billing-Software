from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Permissions & Profile'
    fieldsets = (
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


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
