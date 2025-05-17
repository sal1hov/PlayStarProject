from django.urls import path
from . import views

app_name = 'bookings'  # Добавляем namespace для приложения

urlpatterns = [
    path('create/', views.create_booking, name='create_booking'),
    path('edit/<int:booking_id>/', views.edit_booking, name='edit_booking'),
    path('manage/<int:booking_id>/<str:action>/', views.manage_booking, name='manage_booking'),
    path('delete/<int:booking_id>/', views.delete_booking, name='delete_booking'),
    path('admin/edit/<int:booking_id>/', views.edit_booking_admin, name='edit_booking_admin'),
]