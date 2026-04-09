from django.contrib import admin
from .models import Bill, BillItem


class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 1
    readonly_fields = ('amount',)


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'client', 'invoice_date', 'total_in_bdt', 'status')
    list_filter = ('status', 'invoice_date')
    search_fields = ('bill_number', 'client__name')
    inlines = [BillItemInline]
    readonly_fields = ('bill_number', 'subtotal', 'created_at')


@admin.register(BillItem)
class BillItemAdmin(admin.ModelAdmin):
    list_display = ('bill', 'description', 'quantity', 'unit', 'unit_price', 'amount')
