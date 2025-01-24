from django.contrib import admin
from django.urls import path, include
from main.views import index
from main.views import register

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('accounts/', include('django.contrib.auth.urls')),  # Маршруты для входа/выхода
    path('accounts/register/', register, name='register'),  # Регистрация
]
