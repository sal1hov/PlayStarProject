from django.urls import path
from . import views

urlpatterns = [
    path('client/', views.client_dashboard, name='client_dashboard'),
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
]