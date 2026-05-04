from django.contrib import admin
from clients.models import Agreement
from .models import Bill, BillItem, BillingBank, BillingTaxSettings


class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 1
    readonly_fields = ('amount',)


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'bill_number', 'client', 'invoice_date',
        'billing_bank', 'total_in_bdt', 'status',
    )
    list_filter = ('status', 'invoice_date')
    search_fields = ('invoice_number', 'bill_number', 'client__name')
    inlines = [BillItemInline]

    def save_model(self, request, obj, form, change):
        bb = obj.billing_bank
        if not bb:
            ag = getattr(obj, 'agreement', None)
            if ag is None and obj.agreement_id:
                ag = Agreement.objects.select_related('agreement_with').filter(pk=obj.agreement_id).first()
            co = ag.agreement_with if ag and ag.agreement_with_id else None
            bb = BillingBank.get_default_for_company(co) if co else None
        if bb:
            obj.billing_bank = bb
            bb.copy_to_bill(obj)
        else:
            BillingBank.clear_bill_bank_fields(obj)
            obj.billing_bank = None
        super().save_model(request, obj, form, change)

    readonly_fields = (
        'bill_number', 'invoice_number', 'subtotal', 'created_at',
        'bill_period_from', 'bill_period_to', 'bill_period',
        'project_base_value',
        'vat_amount', 'ait_amount', 'excluding_vat_ait', 'total_in_bdt',
        'bank_name', 'beneficiary', 'bank_branch', 'bank_address_line1', 'bank_address_line2',
        'account_number', 'swift_code', 'branch_routing_code', 'bin_number', 'tin_number',
    )


@admin.register(BillingBank)
class BillingBankAdmin(admin.ModelAdmin):
    list_display = ('label', 'company', 'is_default', 'bank_name', 'account_number')
    list_filter = ('company', 'is_default')
    search_fields = ('label', 'bank_name', 'beneficiary', 'account_number')
    autocomplete_fields = ('company',)
    fieldsets = (
        (None, {'fields': ('company', 'label', 'is_default', 'bank_name', 'beneficiary')}),
        ('Address', {'fields': ('bank_branch', 'bank_address_line1', 'bank_address_line2')}),
        ('Account', {'fields': ('account_number', 'swift_code', 'branch_routing_code')}),
        ('Tax IDs', {'fields': ('bin_number', 'tin_number')}),
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
