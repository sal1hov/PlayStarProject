from django.contrib import admin
from django.urls import path, include
from main.views import index, register

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('accounts/', include('django.contrib.auth.urls')),  # Маршруты для входа/выхода
    path('accounts/register/', register, name='register'),  # Регистрация
    path('accounts/', include('accounts.urls')),
    path('bookings/', include('bookings.urls')),
    path('staff/', include('staff.urls')),
]