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
    path('events/', views.events_view, name='events'),
    # Новые маршруты для мероприятий
    path('events/create/', views.create_event, name='create_event'),
    path('events/import/', views.import_events, name='import_events'),
    path('events/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('events/<int:event_id>/approve/', views.approve_event, name='approve_event'),
    path('events/<int:event_id>/reject/', views.reject_event, name='reject_event'),
    path('export/events/', views.export_events_csv, name='export_events_csv'),
    path('events/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    # ... остальные пути
    path('events/<int:event_id>/view/', views.event_view, name='event_view'),
    path('events/<int:event_id>/view_booking/', views.view_booking, name='view_booking'),

]
