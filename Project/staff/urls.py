from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # -----------------------------
    # Основные маршруты
    # -----------------------------
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager-dashboard'),
    path('employee-dashboard/', views.employee_dashboard, name='employee-dashboard'),

    # Управление пользователями
    path('user/<int:user_id>/edit/', views.edit_user, name='edit-user'),
    path('user/<int:user_id>/delete/', views.delete_user, name='delete-user'),
    path('user/<int:user_id>/children/', views.manage_user_children, name='manage-user-children'),
    path('users/', views.users_view, name='users'),
    path('users/create/', views.create_user, name='create-user'),
    path('filter-users/', views.filter_users, name='filter_users'),

    # Управление бронированиями
    path('booking/<int:booking_id>/delete/', views.delete_booking_admin, name='delete-booking-admin'),
    path('booking/<int:booking_id>/<str:action>/', views.manage_booking, name='manage-booking'),

    # Финансы и аналитика
    path('statistics/', views.statistics_view, name='statistics'),
    path('income-management/', views.income_management, name='income-management'),
    path('income-management/data/', views.income_management_data, name='income-management-data'),
    path('income-management/edit/', views.edit_income, name='edit-income'),

    # Управление событиями
    path('events/', views.events_view, name='events'),
    path('events/create/', views.create_event, name='create-event'),
    path('events/edit/<int:event_id>/', views.edit_event, name='edit-event'),
    path('events/<int:event_id>/approve/', views.approve_event, name='approve-event'),
    path('events/<int:event_id>/reject/', views.reject_event, name='reject-event'),
    path('events/<int:event_id>/delete/', views.delete_event, name='delete-event'),
    path('events/<int:event_id>/view/', views.event_view, name='view-event'),
    path('events/<int:event_id>/view-booking/', views.view_booking, name='view-booking'),

    # Управление сменами
    path('shifts/', views.ShiftListView.as_view(), name='shift-list'),
    path('shifts/create/', views.CreateShiftView.as_view(), name='shift-create'),
    path('shifts/<int:pk>/update/', views.UpdateShiftView.as_view(), name='shift-update'),
    path('shifts/<int:pk>/delete/', views.delete_shift, name='shift-delete'),
    path('shifts/get_shift_types/', views.get_shift_types, name='get-shift-types'),
    path('shifts/get_staff/', views.get_staff, name='get-staff'),
    path('shift-management/', views.ShiftManagementView.as_view(), name='shift-management'),
    path('shifts/edit_day/', views.edit_day_shifts, name='edit-day-shifts'),
    path('shifts/<int:pk>/duplicate/', views.duplicate_shift, name='shift-duplicate'),
    path('shifts/edit_day_view/', views.edit_day_shifts_view, name='edit-day-shifts-view'),

    # Запросы на смены
    path('my-shifts/', views.MyShiftRequestsView.as_view(), name='my-shift-requests'),
    path('shift-request/create/', views.CreateShiftRequestView.as_view(), name='shift-request-create'),
    path('shift-request/<int:pk>/update/', views.UpdateShiftRequestView.as_view(), name='shift-request-update'),
    path('shift-request/<int:pk>/delete/', views.delete_shift_request, name='shift-request-delete'),
    path('shift-request/<int:pk>/details/', views.ShiftRequestDetailView.as_view(), name='shift-request-details'),
    path('admin/shift-approval/', views.AdminShiftApprovalView.as_view(), name='admin_shift_approval'),
    path('admin/shift-approval/<int:pk>/approve/', views.approve_shift_request, name='approve-shift-request'),
    path('admin/shift-approval/<int:pk>/reject/', views.reject_shift_request, name='reject-shift-request'),

    # =============================================
    # Управление ценами (Price Settings)
    # =============================================
    path('prices/', views.price_settings, name='price-settings'),

    # Сохранение цен
    path('prices/save-child-city/', views.save_child_city_prices, name='save_child_city_prices'),
    path('prices/save-arcade/', views.save_arcade_prices, name='save_arcade_prices'),
    path('prices/save-vr-arena/', views.save_vr_arena_prices, name='save_vr_arena_prices'),
    path('prices/save-birthday-packages/', views.save_birthday_packages, name='save_birthday_packages'),
    path('prices/save-vr-packages/', views.save_vr_packages, name='save_vr_packages'),
    path('prices/save-standard-packages/', views.save_standard_packages, name='save_standard_packages'),
    path('prices/save-playstation/', views.save_playstation_prices, name='save_playstation_prices'),
    path('prices/save-vr-rides/', views.save_vr_rides, name='save_vr_rides'),

    # Управление элементами
    path('prices/child-city/add/', views.add_child_city_item, name='add_child_city_item'),
    path('prices/child-city/delete/<int:pk>/', views.delete_child_city_item, name='delete_child_city_item'),
    path('prices/arcade/add/', views.add_arcade_machine_item, name='add_arcade_machine_item'),
    path('prices/arcade/delete/<int:pk>/', views.delete_arcade_machine_item, name='delete_arcade_machine_item'),
    path('prices/vr-arena/add/', views.add_vr_arena_item, name='add_vr_arena_item'),
    path('prices/vr-arena/delete/<int:pk>/', views.delete_vr_arena_item, name='delete_vr_arena_item'),
    path('prices/birthday-packages/add/', views.add_birthday_package, name='add_birthday_package'),
    path('prices/birthday-packages/delete/<int:pk>/', views.delete_birthday_package, name='delete_birthday_package'),
    path('prices/vr-packages/add/', views.add_vr_package, name='add_vr_package'),
    path('prices/vr-packages/delete/<int:pk>/', views.delete_vr_package, name='delete_vr_package'),
    path('prices/standard-packages/add/', views.add_standard_package, name='add_standard_package'),
    path('prices/standard-packages/delete/<int:pk>/', views.delete_standard_package, name='delete_standard_package'),
    path('prices/playstation/add/', views.add_playstation_slot, name='add_playstation_slot'),
    path('prices/playstation/delete/<int:pk>/', views.delete_playstation_slot, name='delete_playstation_slot'),
    path('prices/vr-rides/add/', views.add_vr_ride, name='add_vr_ride'),
    path('prices/vr-rides/delete/<int:pk>/', views.delete_vr_ride, name='delete_vr_ride'),
]