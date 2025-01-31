# core/urls.py
from django.contrib import admin
from django.urls import path, include
from main.views import index, register, profile_view, logout_view  # Импортируем logout_view
from staff.views import edit_user, delete_user  # Импортируем функции для редактирования и удаления пользователей
from bookings.views import edit_booking, delete_booking, manage_booking  # Импортируем функции для управления бронированиями

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('register/', register, name='register'),  # Маршрут для регистрации
    path('accounts/', include('accounts.urls')),  # Маршруты для приложения accounts
    path('accounts/logout/', logout_view, name='logout'),  # Маршрут для выхода
    path('accounts/', include('django.contrib.auth.urls')),  # Встроенные маршруты для входа/выхода
    path('bookings/', include('bookings.urls')),
    path('staff/', include('staff.urls')),  # Включаем маршруты из staff
    path('profile/', profile_view, name='profile'),  # Маршрут для профиля пользователя
    path('user/<int:user_id>/edit/', edit_user, name='edit_user'),  # Маршрут для редактирования пользователя
    path('user/<int:user_id>/delete/', delete_user, name='delete_user'),  # Маршрут для удаления пользователя
    path('booking/<int:booking_id>/edit/', edit_booking, name='edit_booking'),  # Маршрут для редактирования бронирования
    path('booking/<int:booking_id>/delete/', delete_booking, name='delete_booking'),  # Маршрут для удаления бронирования
    path('booking/<int:booking_id>/<str:action>/', manage_booking, name='manage_booking'),  # Маршрут для управления бронированием
]