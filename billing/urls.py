from django.urls import path
from . import views

urlpatterns = [
    path('', views.bill_list, name='bill_list'),
    path('queue/pending/', views.bill_queue_pending, name='bill_queue_pending'),
    path('queue/submitted/', views.bill_queue_submitted, name='bill_queue_submitted'),
    path('queue/paid/', views.bill_queue_paid, name='bill_queue_paid'),
    path('queue/submit-bulk/', views.bills_submit_bulk, name='bills_submit_bulk'),
    path('queue/mark-paid-bulk/', views.bills_mark_paid_bulk, name='bills_mark_paid_bulk'),
    path('create/', views.bill_create, name='bill_create'),
    path('<int:pk>/', views.bill_detail, name='bill_detail'),
    path('<int:pk>/edit/', views.bill_edit, name='bill_edit'),
    path('<int:pk>/submit/', views.bill_submit, name='bill_submit'),
    path('<int:pk>/set-invoice-today/', views.bill_set_invoice_today, name='bill_set_invoice_today'),
    path('<int:pk>/pdf/', views.bill_pdf, name='bill_pdf'),
    path('<int:pk>/print/', views.bill_print, name='bill_print'),
    path('<int:pk>/excel/', views.bill_excel, name='bill_excel'),
    path('<int:pk>/mark-paid/', views.mark_paid, name='mark_paid'),
    path('<int:pk>/delete/', views.bill_delete, name='bill_delete'),
    path('api/client/<int:client_id>/agreements/', views.get_client_agreements, name='get_client_agreements'),
    path('api/agreement/<int:agreement_id>/services/', views.get_agreement_services, name='get_agreement_services'),
    path('api/preview-invoice-number/', views.preview_invoice_number, name='preview_invoice_number'),
    path('api/preview-bill-period/', views.preview_bill_period, name='preview_bill_period'),
]
