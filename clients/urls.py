from django.urls import path
from . import views

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('add/', views.client_add, name='client_add'),
    path('<int:pk>/', views.client_detail, name='client_detail'),
    path('<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('<int:client_pk>/agreement/add/', views.agreement_add, name='agreement_add'),
    path('agreement/<int:pk>/edit/', views.agreement_edit, name='agreement_edit'),
]
