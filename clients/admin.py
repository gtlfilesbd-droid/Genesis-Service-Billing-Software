from django.contrib import admin
from .models import Client, Agreement, Service


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1


class AgreementInline(admin.StackedInline):
    model = Agreement
    extra = 0
    show_change_link = True


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'email', 'phone', 'city', 'is_active', 'created_at')
    list_filter = ('is_active', 'country', 'city')
    search_fields = ('name', 'company', 'email', 'phone')
    inlines = [AgreementInline]


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'start_date', 'end_date', 'is_active', 'total_value')
    list_filter = ('is_active',)
    search_fields = ('title', 'client__name')
    inlines = [ServiceInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'agreement', 'service_type', 'charge', 'is_active')
    list_filter = ('service_type', 'is_active')
    search_fields = ('name', 'agreement__title')
