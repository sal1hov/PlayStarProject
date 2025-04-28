# core/urls.py
from django.contrib import admin
from django.urls import path, include
from main.views import index, register, profile_view, logout_view
from staff.views import edit_user, delete_user, manage_booking
from bookings.views import edit_booking, delete_booking

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('register/', register, name='register'),
    path('accounts/', include('accounts.urls')),
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('bookings/', include('bookings.urls')),
    path('staff/', include('staff.urls')),
    path('profile/', profile_view, name='profile'),
    path('booking/<int:booking_id>/edit/', edit_booking, name='edit_booking'),
    path('booking/<int:booking_id>/delete/', delete_booking, name='delete_booking'),
    path('booking/<int:booking_id>/<str:action>/', manage_booking, name='manage_booking'),
    # Добавьте эту строку для включения URL-паттернов из main.urls
    path('', include('main.urls')),
]