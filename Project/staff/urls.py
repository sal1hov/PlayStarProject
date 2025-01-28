from django.urls import path
from .views import employee_dashboard, manager_dashboard, admin_dashboard

urlpatterns = [
    path('employee/', employee_dashboard, name='employee_dashboard'),
    path('manager/', manager_dashboard, name='manager_dashboard'),
    path('admin/', admin_dashboard, name='admin_dashboard'),
]