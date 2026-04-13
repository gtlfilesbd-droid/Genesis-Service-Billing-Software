from django.contrib import admin
from .models import Company, Client, Agreement, AgreementTitlePreset, Service


@admin.register(AgreementTitlePreset)
class AgreementTitlePresetAdmin(admin.ModelAdmin):
    list_display = ('title', 'sort_order', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title',)
    ordering = ('sort_order', 'title')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_form', 'email', 'phone', 'city', 'is_active', 'created_at')
    list_filter = ('is_active', 'country', 'city')
    search_fields = ('name', 'short_form', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('name', 'short_form'),
        }),
        ('Contact', {
            'fields': ('email', 'phone'),
        }),
        ('Address', {
            'fields': ('address', 'city', 'country'),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial['created_by'] = request.user.pk
        return initial

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1


class AgreementInline(admin.StackedInline):
    model = Agreement
    extra = 0
    show_change_link = True


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_form', 'email', 'phone', 'city', 'is_active', 'created_at')
    list_filter = ('is_active', 'country', 'city')
    search_fields = ('name', 'short_form', 'email', 'phone')
    inlines = [AgreementInline]


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'agreement_with', 'start_date', 'end_date', 'is_active', 'total_value')
    list_filter = ('is_active',)
    search_fields = ('title', 'client__name', 'agreement_with__name', 'agreement_with__short_form')
    inlines = [ServiceInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'agreement', 'service_type', 'charge', 'is_active')
    list_filter = ('service_type', 'is_active')
    search_fields = ('name', 'agreement__title')
