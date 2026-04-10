from django.contrib import admin
from .models import Bill, BillItem, BillingTaxSettings


class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 1
    readonly_fields = ('amount',)


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'bill_number', 'client', 'invoice_date', 'total_in_bdt', 'status')
    list_filter = ('status', 'invoice_date')
    search_fields = ('invoice_number', 'bill_number', 'client__name')
    inlines = [BillItemInline]
    readonly_fields = (
        'bill_number', 'invoice_number', 'subtotal', 'created_at',
        'bill_period_from', 'bill_period_to', 'bill_period',
        'project_base_value', 'vat_rate_percent', 'ait_rate_percent',
        'vat_amount', 'ait_amount', 'excluding_vat_ait', 'total_in_bdt',
    )


@admin.register(BillingTaxSettings)
class BillingTaxSettingsAdmin(admin.ModelAdmin):
    fields = ('vat_percent', 'ait_percent')

    def has_add_permission(self, request):
        return not BillingTaxSettings.objects.filter(pk=1).exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BillItem)
class BillItemAdmin(admin.ModelAdmin):
    list_display = ('bill', 'description', 'quantity', 'unit', 'unit_price', 'amount')
