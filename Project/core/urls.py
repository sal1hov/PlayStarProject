from django.contrib import admin
from django.urls import path, include
from main.views import index, register, admin_dashboard, manager_dashboard, employee_dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('accounts/', include('django.contrib.auth.urls')),  # Маршруты для входа/выхода
    path('accounts/register/', register, name='register'),  # Регистрация
    path('accounts/', include('accounts.urls')),
    path('bookings/', include('bookings.urls')),
    path('staff/', include('staff.urls')),

    # Новые маршруты для панелей пользователей
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('manager-dashboard/', manager_dashboard, name='manager_dashboard'),
    path('employee-dashboard/', employee_dashboard, name='employee_dashboard'),
]
