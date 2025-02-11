# staff/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),

    # Управление пользователями
    path('user/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('user/<int:user_id>/delete/', views.delete_user, name='delete_user'),

    # Управление бронированиями
    path('booking/<int:booking_id>/<str:action>/', views.manage_booking, name='manage_booking'),

    # Экспорт данных
    path('export/users/', views.export_users_csv, name='export_users_csv'),
    path('export/bookings/', views.export_bookings_csv, name='export_bookings_csv'),

    path('statistics/', views.statistics_view, name='statistics'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('events/', views.events_view, name='events'),
    path('filter-users/', views.filter_users, name='filter_users'),
]
