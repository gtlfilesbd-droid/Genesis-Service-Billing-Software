from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_dashboard, name='report_dashboard'),
    path('export/csv/', views.export_bills_csv, name='export_bills_csv'),
    path('export/excel/', views.export_bills_excel, name='export_bills_excel'),
]
