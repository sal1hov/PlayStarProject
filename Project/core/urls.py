# main/urls.py или core/urls.py
from django.contrib import admin
from django.urls import path, include
from main.views import index, register, profile_view  # Импортируем profile_view
from staff.views import edit_user, delete_user  # Импортируем функции для редактирования и удаления пользователей

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('register/', register, name='register'),  # Маршрут для регистрации
    path('accounts/', include('accounts.urls')),  # Маршруты для приложения accounts
    path('accounts/', include('django.contrib.auth.urls')),  # Встроенные маршруты для входа/выхода
    path('bookings/', include('bookings.urls')),
    path('staff/', include('staff.urls')),  # Включаем маршруты из staff
    path('profile/', profile_view, name='profile'),  # Маршрут для профиля пользователя
    path('user/<int:user_id>/edit/', edit_user, name='edit_user'),  # Маршрут для редактирования пользователя
    path('user/<int:user_id>/delete/', delete_user, name='delete_user'),  # Маршрут для удаления пользователя
]