from django.urls import path
from . import views

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('add/', views.client_add, name='client_add'),
    path('<int:pk>/', views.client_detail, name='client_detail'),
    path('<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('<int:pk>/delete/', views.client_delete, name='client_delete'),
    path('<int:client_pk>/agreement/add/', views.agreement_add, name='agreement_add'),
    path('agreement/<int:pk>/edit/', views.agreement_edit, name='agreement_edit'),
    path('agreement/<int:pk>/delete/', views.agreement_delete, name='agreement_delete'),
    path('agreement/<int:pk>/sheet/', views.agreement_sheet_excel, name='agreement_sheet_excel'),
]
