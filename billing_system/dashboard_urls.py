from django.urls import path
from billing_system import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
