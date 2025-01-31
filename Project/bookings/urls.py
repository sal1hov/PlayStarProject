# bookings/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('edit/<int:booking_id>/', views.edit_booking, name='edit_booking'),
    path('manage/<int:booking_id>/<str:action>/', views.manage_booking, name='manage_booking'),  # Маршрут для управления бронированием
    path('delete/<int:booking_id>/', views.delete_booking, name='delete_booking'),  # Маршрут для удаления бронирования
]